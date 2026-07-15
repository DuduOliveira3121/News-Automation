"""
News Automation — ponto de entrada Streamlit.

Interface única com:
  - Upload do Word
  - Lista das notícias
  - Editor dos campos
  - Botões: Gerar IA / Salvar / Publicar

A camada de apresentação consome apenas Services e Use Cases,
nunca acessa repositórios diretamente.
"""
from __future__ import annotations

import logging
from typing import List, Optional

import streamlit as st
from sqlalchemy.orm import Session as SASession

from config.logging_config import setup_logging
from config.settings import settings
from src.application.dtos.news_dto import NewsDTO
from src.application.services.docx_service import DocxService
from src.application.services.ia_service import IAService
from src.application.services.news_service import NewsService
from src.application.services.publication_service import PublicationService
from src.application.use_cases.parse_docx_use_case import ParseDocxUseCase
from src.application.use_cases.publish_news_use_case import PublishNewsUseCase
from src.domain.entities.news import NewsStatus
from src.infrastructure.ai.openai_client import OpenAIClient
from src.infrastructure.database.session import get_engine, init_db
from src.infrastructure.repositories.news_repository import NewsRepository
from src.infrastructure.repositories.publication_repository import (
    SQLAlchemyPublicationRepository,
)

setup_logging()
logger = logging.getLogger(__name__)

# ── Status icons ─────────────────────────────────────────────────────────────

_STATUS_ICON: dict[NewsStatus, str] = {
    NewsStatus.PENDING: "⏳",
    NewsStatus.REVIEWED: "✅",
    NewsStatus.PUBLISHED: "🌐",
    NewsStatus.FAILED: "❌",
}

_STATUS_LABEL: dict[NewsStatus, str] = {
    NewsStatus.PENDING: "Pendente",
    NewsStatus.REVIEWED: "Revisado",
    NewsStatus.PUBLISHED: "Publicado",
    NewsStatus.FAILED: "Falhou",
}


# ── Dependency injection (engine singleton) ──────────────────────────────────

@st.cache_resource
def _init_engine():
    """Inicializa e retorna o engine SQLAlchemy (singleton por processo)."""
    init_db()
    return get_engine()


def _build_services(session: SASession) -> tuple[
    NewsService, ParseDocxUseCase, PublishNewsUseCase
]:
    """Constrói todos os serviços injetando a sessão fornecida.

    O IAService é criado de forma lazy (somente quando 'Gerar IA' é acionado)
    para evitar erro de credencial na inicialização da aplicação.
    """
    news_repo = NewsRepository(session)
    pub_repo = SQLAlchemyPublicationRepository(session)

    news_service = NewsService(news_repo)
    docx_service = DocxService()
    pub_service = PublicationService()

    parse_uc = ParseDocxUseCase(docx_service, news_repo)
    publish_uc = PublishNewsUseCase(pub_service, news_repo, pub_repo)

    return news_service, parse_uc, publish_uc


def _get_ia_service() -> IAService:
    """Cria o IAService sob demanda, validando a chave da API antes."""
    if not settings.openai_api_key:
        raise ValueError(
            "A chave OPENAI_API_KEY não está configurada. "
            "Adicione-a no arquivo .env ou nas variáveis de ambiente."
        )
    return IAService(OpenAIClient())


# ── Session state ─────────────────────────────────────────────────────────────

def _init_state() -> None:
    """Garante que todas as chaves necessárias existam no session_state."""
    defaults: dict[str, object] = {
        "selected_news_id": None,
        "_last_selected_id": None,
        "_last_uploaded_name": None,
        "editor_titulo": "",
        "editor_conteudo": "",
        "editor_resumo": "",
        "editor_categoria": "",
        "editor_imagem": "",
        "editor_texto_alternativo": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _load_news_into_editor(news: NewsDTO) -> None:
    """Preenche o session_state do editor com os dados da notícia selecionada."""
    st.session_state.editor_titulo = news.titulo or ""
    st.session_state.editor_conteudo = news.conteudo or ""
    st.session_state.editor_resumo = news.resumo or ""
    st.session_state.editor_categoria = news.categoria or ""
    st.session_state.editor_imagem = news.imagem or ""
    st.session_state.editor_texto_alternativo = news.texto_alternativo or ""
    st.session_state._last_selected_id = news.id


# ── Upload section ────────────────────────────────────────────────────────────

def _render_upload(parse_uc: ParseDocxUseCase, session: SASession) -> bool:
    """Renderiza o widget de upload. Retorna True se um novo arquivo foi processado."""
    st.subheader("📂 Upload")
    uploaded = st.file_uploader(
        "Selecione o arquivo .docx",
        type=["docx"],
        key="file_uploader",
        label_visibility="collapsed",
    )

    if uploaded is None:
        return False

    # Evita reprocessar o mesmo arquivo na mesma sessão
    if st.session_state._last_uploaded_name == uploaded.name:
        st.caption(f"Arquivo carregado: **{uploaded.name}**")
        return False

    with st.spinner(f"Processando **{uploaded.name}**…"):
        upload_dir = settings.upload_dir
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest = upload_dir / uploaded.name
        dest.write_bytes(uploaded.getvalue())

        try:
            saved = parse_uc.execute(dest)
            session.commit()
            st.session_state._last_uploaded_name = uploaded.name
            st.session_state.selected_news_id = None
            st.session_state._last_selected_id = None
            st.success(f"{len(saved)} notícia(s) extraída(s) de **{uploaded.name}**.")
            return True
        except (FileNotFoundError, ValueError) as exc:
            session.rollback()
            st.error(str(exc))
            return False


# ── News list ─────────────────────────────────────────────────────────────────

def _render_news_list(news_list: List[NewsDTO]) -> None:
    """Renderiza a lista de notícias. Clicar em um item o seleciona para edição."""
    st.subheader("📋 Notícias")

    if not news_list:
        st.caption("Nenhuma notícia carregada. Faça o upload de um arquivo .docx.")
        return

    for news in news_list:
        icon = _STATUS_ICON.get(news.status, "⬜")
        label_text = news.titulo if len(news.titulo) <= 48 else news.titulo[:46] + "…"
        label = f"{icon} {label_text}"
        is_selected = st.session_state.selected_news_id == news.id

        if st.button(
            label,
            key=f"news_btn_{news.id}",
            use_container_width=True,
            type="primary" if is_selected else "secondary",
            help=f"Status: {_STATUS_LABEL.get(news.status, news.status.value)}",
        ):
            st.session_state.selected_news_id = news.id
            st.rerun()


# ── Editor ────────────────────────────────────────────────────────────────────

def _render_editor(
    news_list: List[NewsDTO],
    news_service: NewsService,
    publish_uc: PublishNewsUseCase,
    session: SASession,
) -> None:
    """Renderiza o painel de edição da notícia selecionada."""
    selected_id: Optional[str] = st.session_state.selected_news_id
    selected_news = next((n for n in news_list if n.id == selected_id), None)

    if selected_news is None:
        st.info("Selecione uma notícia na lista ao lado para editar.")
        return

    # Carrega os dados no editor quando a seleção muda
    if st.session_state._last_selected_id != selected_id:
        _load_news_into_editor(selected_news)

    status_icon = _STATUS_ICON.get(selected_news.status, "")
    status_label = _STATUS_LABEL.get(selected_news.status, selected_news.status.value)
    st.subheader(f"✏️ Editor  —  {status_icon} {status_label}")

    # ── Campos editáveis ──────────────────────────────────────────────────────

    st.text_input("Título", key="editor_titulo")

    st.text_area("Conteúdo", key="editor_conteudo", height=240)

    st.text_area("Resumo", key="editor_resumo", height=90)

    col_cat, col_img = st.columns(2)
    with col_cat:
        st.text_input("Categoria", key="editor_categoria")
    with col_img:
        st.text_input("Imagem (URL / caminho)", key="editor_imagem")

    st.text_input("Texto Alternativo", key="editor_texto_alternativo")

    st.divider()

    # ── Botões de ação ────────────────────────────────────────────────────────

    col_ai, col_save, col_pub = st.columns(3)

    # Gerar IA
    with col_ai:
        if st.button("🤖 Gerar IA", use_container_width=True):
            conteudo = st.session_state.editor_conteudo.strip()
            if not conteudo:
                st.warning("Preencha o campo **Conteúdo** antes de gerar com IA.")
            else:
                with st.spinner("Gerando conteúdo com IA…"):
                    try:
                        ia_service = _get_ia_service()
                        st.session_state.editor_titulo = ia_service.gerar_titulo(conteudo)
                        st.session_state.editor_resumo = ia_service.gerar_resumo(conteudo)
                        st.session_state.editor_conteudo = ia_service.melhorar_conteudo(conteudo)
                        st.session_state.editor_texto_alternativo = (
                            ia_service.gerar_texto_alternativo(conteudo)
                        )
                        st.rerun()
                    except Exception as exc:  # noqa: BLE001
                        logger.exception("Erro ao gerar com IA.")
                        st.error(f"Erro ao gerar com IA: {exc}")

    # Salvar
    with col_save:
        if st.button("💾 Salvar", use_container_width=True):
            try:
                news_service.update_fields(
                    news_id=selected_id,
                    titulo=st.session_state.editor_titulo,
                    conteudo=st.session_state.editor_conteudo,
                    resumo=st.session_state.editor_resumo or None,
                    categoria=st.session_state.editor_categoria or None,
                    imagem=st.session_state.editor_imagem or None,
                    texto_alternativo=st.session_state.editor_texto_alternativo or None,
                )
                session.commit()
                st.success("Notícia salva com sucesso.")
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                session.rollback()
                logger.exception("Erro ao salvar notícia.")
                st.error(f"Erro ao salvar: {exc}")

    # Publicar
    with col_pub:
        if st.button("🚀 Publicar", use_container_width=True, type="primary"):
            try:
                result = publish_uc.execute(selected_id)
                if result is None:
                    st.warning("O serviço de publicação ainda não está implementado.")
                else:
                    session.commit()
                    st.success(f"Notícia publicada com sucesso! (ID: {result.id})")
                    st.rerun()
            except Exception as exc:  # noqa: BLE001
                session.rollback()
                logger.exception("Erro ao publicar notícia.")
                st.error(f"Erro ao publicar: {exc}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title=settings.app_name,
        page_icon="📰",
        layout="wide",
    )

    st.title(f"📰 {settings.app_name}")
    _init_state()

    engine = _init_engine()
    session = SASession(engine)

    try:
        news_service, parse_uc, publish_uc = _build_services(session)

        news_list = news_service.list_all()

        col_left, col_right = st.columns([1, 2], gap="large")

        with col_left:
            new_upload = _render_upload(parse_uc, session)
            if new_upload:
                st.rerun()

            st.divider()
            _render_news_list(news_list)

        with col_right:
            _render_editor(news_list, news_service, publish_uc, session)

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()

