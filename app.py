"""
News Automation — ponto de entrada Streamlit.
"""
import logging

import streamlit as st

from config.logging_config import setup_logging
from config.settings import settings

setup_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    st.set_page_config(
        page_title=settings.app_name,
        page_icon="📰",
        layout="wide",
    )
    # TODO: inicializar roteamento de páginas
    pass


if __name__ == "__main__":
    main()
