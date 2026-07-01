"""Serviço de revisão de conteúdo via OpenAI."""
from __future__ import annotations

import logging

from src.application.dtos.news_dto import ReviewRequestDTO, ReviewResultDTO

logger = logging.getLogger(__name__)


class AIReviewService:
    """Coordena a revisão de notícias usando a API da OpenAI.

    Responsabilidades:
        - Montar o prompt adequado para revisão jornalística.
        - Chamar o cliente OpenAI (injetado via infraestrutura).
        - Retornar o conteúdo revisado encapsulado em ReviewResultDTO.
    """

    def review(self, request: ReviewRequestDTO) -> ReviewResultDTO:
        """Envia a notícia para revisão e retorna o conteúdo corrigido.

        Args:
            request: DTO com id, título e conteúdo original.

        Returns:
            ReviewResultDTO com o conteúdo revisado pela IA.

        Raises:
            RuntimeError: Em caso de falha na comunicação com a API.
        """
        ...
