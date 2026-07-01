"""Componente de card para exibição de notícias na lista de seleção."""
from __future__ import annotations

import streamlit as st

from src.application.dtos.news_dto import NewsDTO


def news_card(news: NewsDTO, on_select: bool = False) -> bool:
    """Renderiza um card com resumo de uma notícia.

    Args:
        news: DTO com os dados da notícia a exibir.
        on_select: Exibe botão de seleção quando True.

    Returns:
        True se o botão de seleção foi clicado, False caso contrário.
    """
    ...
