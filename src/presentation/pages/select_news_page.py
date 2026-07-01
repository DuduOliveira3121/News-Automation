"""Página 2 — Seleção de notícia para revisão."""
from __future__ import annotations

import logging
from typing import List

import streamlit as st

from src.application.dtos.news_dto import NewsDTO
from src.application.use_cases.select_news_use_case import SelectNewsUseCase
from src.domain.interfaces.news_repository import INewsRepository

logger = logging.getLogger(__name__)


def render(
    news_repository: INewsRepository,
    select_news_use_case: SelectNewsUseCase,
) -> None:
    """Renderiza a lista de notícias extraídas e permite ao usuário escolher uma.

    Responsabilidades:
        - Listar todas as notícias disponíveis via repositório.
        - Permitir seleção por meio de cards clicáveis.
        - Armazenar a notícia selecionada no session state.
        - Redirecionar para a página de revisão.

    Args:
        news_repository: Repositório para listagem de notícias.
        select_news_use_case: Use case para busca da notícia selecionada.
    """
    ...
