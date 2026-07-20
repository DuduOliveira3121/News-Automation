"""Página 2 — Seleção de notícia para revisão."""
from __future__ import annotations

import logging

import streamlit as st

from src.application.services.news_service import NewsService
from src.presentation.components.news_card import news_card
from src.presentation.state.session_state import AppPage, SessionStateManager

logger = logging.getLogger(__name__)


def render(news_service: NewsService) -> None:
    """Renderiza a lista de notícias extraídas e permite ao usuário escolher uma.

    Exibe todas as notícias como cards clicáveis. Ao selecionar, armazena
    o ID no SessionStateManager e navega para a página de revisão.

    Args:
        news_service: Serviço para listagem de notícias.
    """
    st.header("📋 Selecionar Notícia")

    col_header, col_btn = st.columns([4, 1])
    with col_btn:
        if st.button("← Upload", use_container_width=True):
            SessionStateManager.set_current_page(AppPage.UPLOAD)
            st.rerun()

    news_list = news_service.list_all()

    if not news_list:
        st.info(
            "Nenhuma notícia disponível. "
            "Faça o upload de um arquivo .docx para começar."
        )
        return

    source_file = SessionStateManager.get_source_file()
    if source_file:
        st.caption(f"Arquivo de origem: **{source_file}**")

    st.write(f"**{len(news_list)} notícia(s) disponível(is)** — clique em *Selecionar* para editar.")
    st.divider()

    for news in news_list:
        selected = news_card(news, on_select=True)
        if selected:
            SessionStateManager.set_selected_news_id(news.id)
            SessionStateManager.set_current_page(AppPage.REVIEW)
            logger.info("Notícia selecionada: id=%s", news.id)
            st.rerun()

