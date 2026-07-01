"""Gerenciamento centralizado e tipado do Streamlit session_state."""
from __future__ import annotations

from enum import Enum
from typing import Optional

import streamlit as st


class AppPage(str, Enum):
    """Representa as páginas do fluxo principal da aplicação."""

    UPLOAD = "upload"
    SELECT = "select"
    REVIEW = "review"
    PUBLISH = "publish"


class SessionStateManager:
    """Centraliza o acesso e a mutação do st.session_state.

    Evita chaves espalhadas pelo código e garante tipagem nos valores.
    """

    # ── Chaves ──────────────────────────────────────────────────
    _KEY_CURRENT_PAGE = "current_page"
    _KEY_SELECTED_NEWS_ID = "selected_news_id"
    _KEY_SOURCE_FILE = "source_file"

    @staticmethod
    def init() -> None:
        """Inicializa as chaves do session_state com valores padrão."""
        defaults: dict[str, object] = {
            SessionStateManager._KEY_CURRENT_PAGE: AppPage.UPLOAD,
            SessionStateManager._KEY_SELECTED_NEWS_ID: None,
            SessionStateManager._KEY_SOURCE_FILE: None,
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    def get_current_page() -> AppPage:
        """Retorna a página atualmente ativa."""
        ...

    @staticmethod
    def set_current_page(page: AppPage) -> None:
        """Define a página ativa."""
        ...

    @staticmethod
    def get_selected_news_id() -> Optional[str]:
        """Retorna o ID da notícia selecionada pelo usuário."""
        ...

    @staticmethod
    def set_selected_news_id(news_id: str) -> None:
        """Armazena o ID da notícia selecionada."""
        ...

    @staticmethod
    def get_source_file() -> Optional[str]:
        """Retorna o nome do arquivo .docx carregado."""
        ...

    @staticmethod
    def set_source_file(filename: str) -> None:
        """Armazena o nome do arquivo .docx carregado."""
        ...
