"""Página 1 — Upload do arquivo .docx."""
from __future__ import annotations

import logging

import streamlit as st
from sqlalchemy.orm import Session as SASession

from config.settings import settings
from src.application.use_cases.parse_docx_use_case import ParseDocxUseCase
from src.presentation.state.session_state import AppPage, SessionStateManager

logger = logging.getLogger(__name__)


def render(parse_docx_use_case: ParseDocxUseCase, session: SASession) -> None:
    """Renderiza a página de upload de arquivo .docx.

    Ao detectar um novo arquivo, extrai as notícias automaticamente,
    persiste no banco e navega para a página de seleção.

    Args:
        parse_docx_use_case: Use case injetado para processamento do arquivo.
        session: Sessão SQLAlchemy para commit/rollback.
    """
    st.header("📂 Upload do Documento Word")
    st.write(
        "Selecione um arquivo **.docx** com as notícias. "
        "Cada notícia deve começar com um parágrafo no estilo **Heading 1**."
    )

    uploaded = st.file_uploader(
        "Selecione o arquivo .docx",
        type=["docx"],
        key="file_uploader",
        label_visibility="collapsed",
    )

    if uploaded is None:
        st.info("Aguardando upload de arquivo…")
        return

    last_uploaded = SessionStateManager.get_last_uploaded()
    if last_uploaded == uploaded.name:
        st.success(f"Arquivo **{uploaded.name}** já foi processado.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Ver notícias", type="primary", use_container_width=True):
                SessionStateManager.set_current_page(AppPage.SELECT)
                st.rerun()
        with col2:
            if st.button("🔄 Reprocessar arquivo", use_container_width=True):
                SessionStateManager.set_last_uploaded("")
                st.rerun()
        return

    with st.spinner(f"Processando **{uploaded.name}**…"):
        upload_dir = settings.upload_dir
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest = upload_dir / uploaded.name
        dest.write_bytes(uploaded.getvalue())

        try:
            saved = parse_docx_use_case.execute(dest)
            session.commit()
            SessionStateManager.set_last_uploaded(uploaded.name)
            SessionStateManager.set_source_file(uploaded.name)

            st.success(
                f"✅ **{len(saved)} notícia(s)** extraída(s) de **{uploaded.name}**."
            )
            logger.info(
                "%d notícias extraídas de '%s'.", len(saved), uploaded.name
            )

            if st.button(
                "📋 Selecionar notícia →",
                type="primary",
                use_container_width=True,
            ):
                SessionStateManager.set_current_page(AppPage.SELECT)
                st.rerun()

        except (FileNotFoundError, ValueError) as exc:
            session.rollback()
            st.error(str(exc))
            logger.warning("Erro ao processar '%s': %s", uploaded.name, exc)
        except Exception as exc:
            session.rollback()
            st.error(f"Erro inesperado ao processar o arquivo: {exc}")
            logger.exception("Erro inesperado no upload de '%s'.", uploaded.name)

