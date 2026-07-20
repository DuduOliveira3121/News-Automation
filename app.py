"""
News Automation — ponto de entrada Streamlit.

Fluxo principal:
    Upload do Word → Selecionar notícia → Revisar / Gerar com IA
    → Salvar no banco → Publicar no painel administrativo

Arquitetura:
    - Cada etapa é uma página independente em src/presentation/pages/.
    - O roteamento usa SessionStateManager (session_state centralizado).
    - Serviços e use cases são construídos aqui e injetados nas páginas
      (Dependency Injection explícita — sem globals).
    - IAService / ReviewNewsUseCase são criados de forma lazy (apenas se
      OPENAI_API_KEY estiver configurada).

Design Patterns aplicados:
    - Repository   : INewsRepository / IPublicationRepository
    - Strategy     : IAIClient (OpenAI pode ser trocado por outro provedor)
    - Facade       : PublicationService esconde a complexidade do Playwright
    - Template Method: NewsParser._validate / _open_document / _extract
    - DTO          : NewsDTO / PublishRequestDTO / ReviewResultDTO / …
    - Factory Method: DocxService(parser=None) cria o parser automaticamente
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import streamlit as st
from sqlalchemy.orm import Session as SASession

from config.logging_config import setup_logging
from config.settings import settings
from src.application.services.docx_service import DocxService
from src.application.services.news_service import NewsService
from src.application.services.publication_service import PublicationService
from src.application.use_cases.parse_docx_use_case import ParseDocxUseCase
from src.application.use_cases.publish_news_use_case import PublishNewsUseCase
from src.application.use_cases.review_news_use_case import ReviewNewsUseCase
from src.infrastructure.database.session import get_engine, init_db
from src.infrastructure.repositories.news_repository import NewsRepository
from src.infrastructure.repositories.publication_repository import (
    SQLAlchemyPublicationRepository,
)
from src.presentation.pages import publish_page, review_page, select_news_page, upload_page
from src.presentation.state.session_state import AppPage, SessionStateManager

setup_logging()
logger = logging.getLogger(__name__)


# ── Dataclass de serviços (agrupa dependências injetadas) ─────────────────────

@dataclass
class AppServices:
    """Contém todos os serviços e use cases da aplicação."""

    news_service: NewsService
    parse_uc: ParseDocxUseCase
    publish_uc: PublishNewsUseCase
    review_uc: Optional[ReviewNewsUseCase]  # None se OPENAI_API_KEY não configurada


# ── Inicialização ─────────────────────────────────────────────────────────────

@st.cache_resource
def _init_engine():
    """Inicializa e retorna o engine SQLAlchemy (singleton por processo)."""
    init_db()
    return get_engine()


def _build_services(session: SASession) -> AppServices:
    """Constrói todos os serviços injetando a sessão fornecida.

    O ReviewNewsUseCase (e sua cadeia OpenAI) é criado de forma lazy:
    somente se OPENAI_API_KEY estiver configurada, evitando erros de
    credencial na inicialização da aplicação.
    """
    news_repo = NewsRepository(session)
    pub_repo = SQLAlchemyPublicationRepository(session)

    news_service = NewsService(news_repo)
    docx_service = DocxService()          # Factory Method: cria NewsParser internamente
    pub_service = PublicationService()    # Facade sobre SitePublisher / Playwright

    parse_uc = ParseDocxUseCase(docx_service, news_repo)
    publish_uc = PublishNewsUseCase(pub_service, news_repo, pub_repo)

    review_uc: Optional[ReviewNewsUseCase] = None
    if settings.openai_api_key:
        from src.application.services.ai_review_service import AIReviewService
        from src.infrastructure.ai.openai_client import OpenAIClient

        # Strategy: OpenAIClient implementa IAIClient — pode ser trocado
        ai_review_service = AIReviewService(OpenAIClient())
        review_uc = ReviewNewsUseCase(ai_review_service, news_repo)

    return AppServices(
        news_service=news_service,
        parse_uc=parse_uc,
        publish_uc=publish_uc,
        review_uc=review_uc,
    )


# ── Sidebar com progresso ─────────────────────────────────────────────────────

_STEPS: list[tuple[AppPage, str]] = [
    (AppPage.UPLOAD, "📂 Upload"),
    (AppPage.SELECT, "📋 Selecionar"),
    (AppPage.REVIEW, "✏️ Revisar"),
    (AppPage.PUBLISH, "🚀 Publicar"),
]


def _render_sidebar(current_page: AppPage) -> None:
    """Renderiza o progresso e controles globais no sidebar."""
    with st.sidebar:
        st.title("📰 Fluxo")
        for page, label in _STEPS:
            if page == current_page:
                st.markdown(f"**→ {label}**")
            else:
                st.markdown(f"&nbsp;&nbsp;&nbsp;{label}")

        st.divider()

        source_file = SessionStateManager.get_source_file()
        if source_file:
            st.caption(f"Arquivo: **{source_file}**")

        if st.button("🔄 Novo Upload", use_container_width=True):
            SessionStateManager.set_current_page(AppPage.UPLOAD)
            st.session_state["_last_uploaded"] = None
            st.session_state["selected_news_id"] = None
            st.rerun()

        st.divider()
        st.caption("**Configurações**")
        ai_ok = bool(settings.openai_api_key)
        portal_ok = bool(settings.portal_url)
        st.caption(f"{'✅' if ai_ok else '❌'} OpenAI API Key")
        st.caption(f"{'✅' if portal_ok else '❌'} Portal URL")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title=settings.app_name,
        page_icon="📰",
        layout="wide",
    )

    st.title(f"📰 {settings.app_name}")

    SessionStateManager.init()
    engine = _init_engine()

    current_page = SessionStateManager.get_current_page()
    _render_sidebar(current_page)

    session = SASession(engine)
    try:
        svc = _build_services(session)
        news_id = SessionStateManager.get_selected_news_id()

        if current_page == AppPage.UPLOAD:
            upload_page.render(svc.parse_uc, session)

        elif current_page == AppPage.SELECT:
            select_news_page.render(svc.news_service)

        elif current_page == AppPage.REVIEW:
            review_page.render(
                news_service=svc.news_service,
                review_uc=svc.review_uc,
                news_id=news_id,
                session=session,
            )

        elif current_page == AppPage.PUBLISH:
            publish_page.render(
                news_service=svc.news_service,
                publish_uc=svc.publish_uc,
                news_id=news_id,
                session=session,
            )

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()


