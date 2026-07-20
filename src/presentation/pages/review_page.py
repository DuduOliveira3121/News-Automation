"""Página 3 — Revisão de notícia com auxílio da IA."""
from __future__ import annotations

import logging
from typing import Optional

import streamlit as st
from sqlalchemy.orm import Session as SASession

from src.application.services.news_service import NewsService
from src.application.use_cases.review_news_use_case import ReviewNewsUseCase
from src.presentation.state.session_state import AppPage, SessionStateManager

logger = logging.getLogger(__name__)


def render(
    news_service: NewsService,
    review_uc: Optional[ReviewNewsUseCase],
    news_id: Optional[str],
    session: SASession,
) -> None:
    """Renderiza a interface de revisão de uma notícia selecionada.

    Permite edição manual dos campos, geração automática via IA e
    salvamento no banco. Ao salvar, habilita a navegação para publicação.

    Args:
        news_service: Serviço para busca e atualização da notícia.
        review_uc: Use case de revisão IA (None se API key não configurada).
        news_id: ID da notícia selecionada no SessionStateManager.
        session: Sessão SQLAlchemy para commit/rollback.
    """
    st.header("✏️ Revisar e Editar Notícia")

    # ── Navegação ─────────────────────────────────────────────────
    col_back, col_spacer = st.columns([1, 5])
    with col_back:
        if st.button("← Selecionar", use_container_width=True):
            SessionStateManager.set_current_page(AppPage.SELECT)
            st.rerun()

    if not news_id:
        st.warning("Nenhuma notícia selecionada. Volte à página de seleção.")
        return

    news = news_service.find_by_id(news_id)
    if news is None:
        st.error(f"Notícia '{news_id}' não encontrada.")
        return

    # ── Carrega dados no editor na primeira visita (ou mudança de seleção) ──
    if st.session_state.get("rev_loaded_id") != news_id:
        SessionStateManager.load_news_into_editor(
            titulo=news.titulo or "",
            conteudo=news.reviewed_content or news.conteudo or "",
            resumo=news.resumo or "",
            categoria=news.categoria or "",
            imagem=news.imagem or "",
            texto_alternativo=news.texto_alternativo or "",
            news_id=news_id,
        )

    # ── Status badge ─────────────────────────────────────────────
    _STATUS_ICON = {"pending": "⏳", "reviewed": "✅", "published": "🌐", "failed": "❌"}
    status_val = news.status.value if hasattr(news.status, "value") else str(news.status)
    st.caption(
        f"Status atual: {_STATUS_ICON.get(status_val, '⬜')} **{status_val.capitalize()}** "
        f"| Arquivo: `{news.source_file}`"
    )

    st.divider()

    # ── Campos editáveis ──────────────────────────────────────────
    st.text_input("Título *", key="rev_titulo")
    st.text_area("Conteúdo *", key="rev_conteudo", height=280)

    col_resumo, col_cat = st.columns(2)
    with col_resumo:
        st.text_area("Resumo", key="rev_resumo", height=100)
    with col_cat:
        st.text_input("Categoria", key="rev_categoria")

    col_img, col_alt = st.columns(2)
    with col_img:
        st.text_input("Imagem (caminho ou URL)", key="rev_imagem")
    with col_alt:
        st.text_input("Texto Alternativo", key="rev_texto_alternativo")

    st.divider()

    # ── Botões de ação ────────────────────────────────────────────
    col_ai, col_save, col_pub = st.columns(3)

    # Gerar com IA
    with col_ai:
        ai_disabled = review_uc is None
        ai_help = (
            "Configure OPENAI_API_KEY no .env para habilitar."
            if ai_disabled
            else "Gera título, resumo, conteúdo melhorado e alt-text via IA."
        )
        if st.button(
            "🤖 Gerar com IA",
            use_container_width=True,
            disabled=ai_disabled,
            help=ai_help,
        ):
            conteudo_atual = st.session_state.get("rev_conteudo", "").strip()
            if not conteudo_atual:
                st.warning("Preencha o campo **Conteúdo** antes de gerar com IA.")
            else:
                with st.spinner("Gerando conteúdo com IA…"):
                    try:
                        result = review_uc.execute(news_id)  # type: ignore[union-attr]
                        st.session_state["rev_titulo"] = result.titulo or st.session_state["rev_titulo"]
                        st.session_state["rev_resumo"] = result.resumo or st.session_state["rev_resumo"]
                        st.session_state["rev_conteudo"] = result.reviewed_content
                        st.session_state["rev_texto_alternativo"] = (
                            result.texto_alternativo or st.session_state["rev_texto_alternativo"]
                        )
                        st.success("Conteúdo gerado com sucesso!")
                        st.rerun()
                    except Exception as exc:
                        logger.exception("Erro ao gerar com IA.")
                        st.error(f"Erro ao gerar com IA: {exc}")

    # Salvar
    with col_save:
        if st.button("💾 Salvar", use_container_width=True):
            titulo = st.session_state.get("rev_titulo", "").strip()
            conteudo = st.session_state.get("rev_conteudo", "").strip()

            if not titulo or not conteudo:
                st.warning("**Título** e **Conteúdo** são obrigatórios.")
            else:
                try:
                    news_service.update_fields(
                        news_id=news_id,
                        titulo=titulo,
                        conteudo=conteudo,
                        resumo=st.session_state.get("rev_resumo") or None,
                        categoria=st.session_state.get("rev_categoria") or None,
                        imagem=st.session_state.get("rev_imagem") or None,
                        texto_alternativo=st.session_state.get("rev_texto_alternativo") or None,
                    )
                    session.commit()
                    st.success("✅ Notícia salva com sucesso.")
                    logger.info("Notícia salva via review_page: id=%s", news_id)
                    st.rerun()
                except Exception as exc:
                    session.rollback()
                    logger.exception("Erro ao salvar notícia.")
                    st.error(f"Erro ao salvar: {exc}")

    # Publicar
    with col_pub:
        if st.button("🚀 Publicar →", use_container_width=True, type="primary"):
            if not st.session_state.get("rev_titulo", "").strip():
                st.warning("Salve a notícia antes de publicar.")
            else:
                SessionStateManager.set_current_page(AppPage.PUBLISH)
                st.rerun()

