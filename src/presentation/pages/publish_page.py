"""Página 4 — Publicação da notícia no portal."""
from __future__ import annotations

import logging

import streamlit as st

from src.application.use_cases.publish_news_use_case import PublishNewsUseCase

logger = logging.getLogger(__name__)


def render(publish_news_use_case: PublishNewsUseCase) -> None:
    """Renderiza a confirmação e execução da publicação no portal.

    Responsabilidades:
        - Exibir resumo da notícia pronta para publicação.
        - Solicitar confirmação do usuário.
        - Acionar o PublishNewsUseCase ao confirmar.
        - Exibir feedback de sucesso ou falha com detalhes do erro.

    Args:
        publish_news_use_case: Use case de publicação injetado.
    """
    ...
