"""Use case: seleção de uma notícia pelo usuário."""
from __future__ import annotations

import logging
from typing import Optional

from src.application.dtos.news_dto import NewsDTO
from src.domain.interfaces.news_repository import INewsRepository

logger = logging.getLogger(__name__)


class SelectNewsUseCase:
    """Recupera uma notícia específica para exibição/edição.

    Responsabilidades:
        1. Buscar a notícia pelo ID fornecido pelo usuário.
        2. Converter para NewsDTO e retornar para a camada de apresentação.
    """

    def __init__(self, news_repository: INewsRepository) -> None:
        self._news_repository = news_repository

    def execute(self, news_id: str) -> Optional[NewsDTO]:
        """Busca e retorna os dados de uma notícia.

        Args:
            news_id: Identificador único da notícia.

        Returns:
            NewsDTO com os dados da notícia, ou None se não encontrada.
        """
        ...
