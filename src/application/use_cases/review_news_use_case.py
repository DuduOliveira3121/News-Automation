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
        """Solicita revisão da notícia e retorna o resultado para o editor.

        O resultado NÃO é persistido automaticamente — o usuário pode
        editar os campos antes de clicar em 'Salvar'.

        Args:
            news_id: Identificador único da notícia a revisar.

        Returns:
            ReviewResultDTO com todos os campos gerados pela IA.

        Raises:
            ValueError: Se a notícia não for encontrada.
        """
        from src.application.dtos.news_dto import ReviewRequestDTO

        news = self._news_repository.find_by_id(news_id)
        if news is None:
            raise ValueError(f"Notícia '{news_id}' não encontrada.")

        request = ReviewRequestDTO(
            news_id=news.id,
            titulo=news.titulo,
            conteudo=news.conteudo,
        )
        result = self._ai_review_service.review(request)
        logger.info("Revisão IA concluída para notícia id=%s", news_id)
        return result
