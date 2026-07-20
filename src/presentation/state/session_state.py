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
    Padrão aplicado: encapsula o dicionário global de estado como
    um objeto com interface bem definida.
    """

    # ── Chaves ──────────────────────────────────────────────────
    _KEY_CURRENT_PAGE = "current_page"
    _KEY_SELECTED_NEWS_ID = "selected_news_id"
    _KEY_SOURCE_FILE = "source_file"
    _KEY_LAST_UPLOADED = "_last_uploaded"

    # ── Prefixo dos campos do editor ────────────────────────────
    EDITOR_PREFIX = "rev_"

    @staticmethod
    def init() -> None:
        """Inicializa as chaves do session_state com valores padrão."""
        defaults: dict[str, object] = {
            SessionStateManager._KEY_CURRENT_PAGE: AppPage.UPLOAD,
            SessionStateManager._KEY_SELECTED_NEWS_ID: None,
            SessionStateManager._KEY_SOURCE_FILE: None,
            SessionStateManager._KEY_LAST_UPLOADED: None,
            # Campos do editor de revisão
            "rev_loaded_id": None,
            "rev_titulo": "",
            "rev_conteudo": "",
            "rev_resumo": "",
            "rev_categoria": "",
            "rev_imagem": "",
            "rev_texto_alternativo": "",
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    def get_current_page() -> AppPage:
        """Retorna a página atualmente ativa."""
        return st.session_state.get(
            SessionStateManager._KEY_CURRENT_PAGE, AppPage.UPLOAD
        )

    @staticmethod
    def set_current_page(page: AppPage) -> None:
        """Define a página ativa."""
        st.session_state[SessionStateManager._KEY_CURRENT_PAGE] = page

    @staticmethod
    def get_selected_news_id() -> Optional[str]:
        """Retorna o ID da notícia selecionada pelo usuário."""
        return st.session_state.get(SessionStateManager._KEY_SELECTED_NEWS_ID)

    @staticmethod
    def set_selected_news_id(news_id: str) -> None:
        """Armazena o ID da notícia selecionada e limpa o cache do editor."""
        st.session_state[SessionStateManager._KEY_SELECTED_NEWS_ID] = news_id
        st.session_state["rev_loaded_id"] = None  # força recarga no editor

    @staticmethod
    def get_source_file() -> Optional[str]:
        """Retorna o nome do arquivo .docx carregado."""
        return st.session_state.get(SessionStateManager._KEY_SOURCE_FILE)

    @staticmethod
    def set_source_file(filename: str) -> None:
        """Armazena o nome do arquivo .docx carregado."""
        st.session_state[SessionStateManager._KEY_SOURCE_FILE] = filename

    @staticmethod
    def get_last_uploaded() -> Optional[str]:
        """Retorna o nome do último arquivo carregado (evita reprocessamento)."""
        return st.session_state.get(SessionStateManager._KEY_LAST_UPLOADED)

    @staticmethod
    def set_last_uploaded(filename: str) -> None:
        """Armazena o nome do último arquivo processado."""
        st.session_state[SessionStateManager._KEY_LAST_UPLOADED] = filename

    @staticmethod
    def load_news_into_editor(
        titulo: str,
        conteudo: str,
        resumo: str,
        categoria: str,
        imagem: str,
        texto_alternativo: str,
        news_id: str,
    ) -> None:
        """Carrega os dados de uma notícia nos campos do editor."""
        st.session_state["rev_titulo"] = titulo
        st.session_state["rev_conteudo"] = conteudo
        st.session_state["rev_resumo"] = resumo
        st.session_state["rev_categoria"] = categoria
        st.session_state["rev_imagem"] = imagem
        st.session_state["rev_texto_alternativo"] = texto_alternativo
        st.session_state["rev_loaded_id"] = news_id

