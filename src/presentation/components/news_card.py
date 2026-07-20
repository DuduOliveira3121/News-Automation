"""Componente de card para exibição de notícias na lista de seleção."""
from __future__ import annotations

import streamlit as st

from src.application.dtos.news_dto import NewsDTO

_STATUS_ICON: dict[str, str] = {
    "pending": "⏳",
    "reviewed": "✅",
    "published": "🌐",
    "failed": "❌",
}

_STATUS_LABEL: dict[str, str] = {
    "pending": "Pendente",
    "reviewed": "Revisado",
    "published": "Publicado",
    "failed": "Falhou",
}


def news_card(news: NewsDTO, on_select: bool = False) -> bool:
    """Renderiza um card com resumo de uma notícia.

    Args:
        news: DTO com os dados da notícia a exibir.
        on_select: Exibe botão de seleção quando True.

    Returns:
        True se o botão de seleção foi clicado, False caso contrário.
    """
    status_val = news.status.value if hasattr(news.status, "value") else str(news.status)
    icon = _STATUS_ICON.get(status_val, "⬜")
    label = _STATUS_LABEL.get(status_val, status_val.capitalize())

    with st.container():
        if on_select:
            col_info, col_btn = st.columns([5, 1])
        else:
            col_info = st.container()
            col_btn = None

        with col_info:
            titulo_display = (
                news.titulo if len(news.titulo) <= 80 else news.titulo[:78] + "…"
            )
            st.markdown(f"**{icon} {titulo_display}**")
            if news.resumo:
                preview = (
                    news.resumo if len(news.resumo) <= 120 else news.resumo[:118] + "…"
                )
                st.caption(preview)
            st.caption(
                f"Status: **{label}** · Arquivo: `{news.source_file}`"
            )

        if on_select and col_btn is not None:
            with col_btn:
                clicked = st.button(
                    "Selecionar",
                    key=f"card_select_{news.id}",
                    type="primary",
                    use_container_width=True,
                )
                return clicked

    st.divider()
    return False

