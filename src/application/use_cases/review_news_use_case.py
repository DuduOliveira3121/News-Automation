"""Use case: revisão de uma notícia com auxílio da IA."""
from __future__ import annotations

import logging

from src.application.dtos.news_dto import ReviewResultDTO
from src.application.services.ai_review_service import AIReviewService
from src.domain.interfaces.news_repository import INewsRepository

logger = logging.getLogger(__name__)


class ReviewNewsUseCase:
    """Envia uma notícia para revisão pela IA e persiste o resultado.

    Responsabilidades:
        1. Recuperar a notícia pelo ID.
        2. Enviar o conteúdo ao AIReviewService.
        3. Persistir o conteúdo revisado na entidade News.
        4. Retornar o ReviewResultDTO para a apresentação.
    """

    def __init__(
        self,
        ai_review_service: AIReviewService,
        news_repository: INewsRepository,
    ) -> None:
        self._ai_review_service = ai_review_service
        self._news_repository = news_repository

    def execute(self, news_id: str) -> ReviewResultDTO:
        """Solicita revisão da notícia e persiste o resultado.

        Args:
            news_id: Identificador único da notícia a revisar.

        Returns:
            ReviewResultDTO com o conteúdo revisado.

        Raises:
            ValueError: Se a notícia não for encontrada.
        """
        ...
