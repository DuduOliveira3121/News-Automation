"""Página 1 — Upload do arquivo .docx."""
from __future__ import annotations

import logging

import streamlit as st

from src.application.use_cases.parse_docx_use_case import ParseDocxUseCase

logger = logging.getLogger(__name__)


def render(parse_docx_use_case: ParseDocxUseCase) -> None:
    """Renderiza a página de upload de arquivo .docx.

    Responsabilidades:
        - Exibir widget de upload de arquivo.
        - Salvar o arquivo no diretório de uploads.
        - Acionar o ParseDocxUseCase ao confirmar o upload.
        - Redirecionar para a página de seleção de notícias.

    Args:
        parse_docx_use_case: Use case injetado para processamento do arquivo.
    """
    ...
