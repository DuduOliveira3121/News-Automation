"""Página 4 — Publicação da notícia no portal."""
from __future__ import annotations

import logging
from typing import Optional

import streamlit as st
from sqlalchemy.orm import Session as SASession

from src.application.services.news_service import NewsService
from src.application.use_cases.publish_news_use_case import PublishNewsUseCase
from src.presentation.state.session_state import AppPage, SessionStateManager

logger = logging.getLogger(__name__)


def render(
    news_service: NewsService,
    publish_uc: PublishNewsUseCase,
    news_id: Optional[str],
    session: SASession,
) -> None:
    """Renderiza a confirmação e execução da publicação no portal.

    Exibe o preview da notícia, solicita confirmação e aciona o
    PublishNewsUseCase ao confirmar. Exibe feedback de sucesso ou falha.

    Args:
        news_service: Serviço para busca da notícia.
        publish_uc: Use case de publicação injetado.
        news_id: ID da notícia selecionada.
        session: Sessão SQLAlchemy para commit/rollback.
    """
    st.header("🚀 Publicar no Portal")

    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("← Revisar", use_container_width=True):
            SessionStateManager.set_current_page(AppPage.REVIEW)
            st.rerun()

    if not news_id:
        st.warning("Nenhuma notícia selecionada. Volte à etapa de seleção.")
        return

    news = news_service.find_by_id(news_id)
    if news is None:
        st.error(f"Notícia '{news_id}' não encontrada.")
        return

    # ── Preview ──────────────────────────────────────────────────
    st.subheader("Preview da notícia")

    with st.container():
        st.markdown(f"### {news.titulo}")

        if news.resumo:
            st.info(news.resumo)

        conteudo_exibido = news.reviewed_content or news.conteudo
        st.write(conteudo_exibido[:800] + "…" if len(conteudo_exibido) > 800 else conteudo_exibido)

        meta_cols = st.columns(3)
        with meta_cols[0]:
            st.caption(f"📁 Categoria: **{news.categoria or '—'}**")
        with meta_cols[1]:
            st.caption(f"🖼️ Imagem: **{news.imagem or '—'}**")
        with meta_cols[2]:
            status_val = news.status.value if hasattr(news.status, "value") else str(news.status)
            st.caption(f"📊 Status: **{status_val.capitalize()}**")

    st.divider()

    # ── Verificação de pré-requisitos ─────────────────────────────
    from config.settings import settings

    if not settings.portal_url:
        st.warning(
            "⚠️ **PORTAL_URL** não está configurada. "
            "Adicione `PORTAL_URL`, `PORTAL_USERNAME` e `PORTAL_PASSWORD` no arquivo `.env` "
            "para habilitar a publicação automática."
        )
        return

    if news.status.value == "published":
        st.success("✅ Esta notícia já foi publicada com sucesso.")
        if st.button("🔄 Publicar novamente", use_container_width=True):
            _execute_publish(publish_uc, news_id, session)
        return

    # ── Confirmação ───────────────────────────────────────────────
    st.write("Ao confirmar, a notícia será publicada automaticamente no portal.")
    st.write(f"**Portal:** `{settings.portal_url}`")

    if st.button(
        "✅ Confirmar Publicação",
        type="primary",
        use_container_width=True,
    ):
        _execute_publish(publish_uc, news_id, session)


def _execute_publish(
    publish_uc: PublishNewsUseCase,
    news_id: str,
    session: SASession,
) -> None:
    """Executa o use case de publicação e exibe o resultado."""
    with st.spinner("Publicando no portal… Aguarde."):
        try:
            result = publish_uc.execute(news_id)
            session.commit()

            if result.status.value == "success":
                st.success(
                    f"🎉 Notícia publicada com sucesso! "
                    f"(Publication ID: `{result.id}`)"
                )
                logger.info("Publicação concluída: news_id=%s pub_id=%s", news_id, result.id)
                # Redireciona para seleção para processar próxima notícia
                if st.button("📋 Selecionar próxima notícia", type="primary"):
                    SessionStateManager.set_current_page(AppPage.SELECT)
                    st.rerun()
            else:
                st.error(
                    f"❌ Falha na publicação: {result.error_message or 'Erro desconhecido.'}"
                )
                logger.error(
                    "Publicação falhou: news_id=%s erro=%s",
                    news_id,
                    result.error_message,
                )
        except ValueError as exc:
            session.rollback()
            st.error(str(exc))
        except Exception as exc:
            session.rollback()
            logger.exception("Erro inesperado ao publicar notícia.")
            st.error(f"Erro inesperado ao publicar: {exc}")

