"""Serviço de revisão de conteúdo via OpenAI."""
from __future__ import annotations

import logging

from src.application.dtos.news_dto import ReviewRequestDTO, ReviewResultDTO
from src.application.services.ia_service import IAService
from src.domain.interfaces.ai_client import IAIClient

logger = logging.getLogger(__name__)


class AIReviewService:
    """Coordena a revisão de notícias usando a API da OpenAI.

    Responsabilidades:
        - Montar o prompt adequado para revisão jornalística.
        - Chamar o IAService (Strategy: IAIClient injetado).
        - Retornar o conteúdo revisado encapsulado em ReviewResultDTO.

    Padrão aplicado: Facade — esconde a complexidade de múltiplas
    chamadas ao IAService em um único método ``review()``.
    """

    def __init__(self, ai_client: IAIClient) -> None:
        # Strategy: qualquer implementação de IAIClient é aceita
        self._ia_service = IAService(ai_client)

    def review(self, request: ReviewRequestDTO) -> ReviewResultDTO:
        """Envia a notícia para revisão e retorna o conteúdo corrigido.

        Gera título, resumo, conteúdo melhorado e texto alternativo
        em sequência. Todas as chamadas usam o mesmo conteúdo original.

        Args:
            request: DTO com id, título e conteúdo original.

        Returns:
            ReviewResultDTO com todos os campos gerados pela IA.

        Raises:
            RuntimeError: Em caso de falha na comunicação com a API.
        """
        logger.info("Iniciando revisão via IA para notícia id=%s", request.news_id)

        reviewed_content = self._ia_service.melhorar_conteudo(request.conteudo)
        titulo = self._ia_service.gerar_titulo(request.conteudo)
        resumo = self._ia_service.gerar_resumo(request.conteudo)
        texto_alternativo = self._ia_service.gerar_texto_alternativo(request.conteudo)

        logger.info("Revisão concluída para notícia id=%s", request.news_id)
        return ReviewResultDTO(
            news_id=request.news_id,
            reviewed_content=reviewed_content,
            titulo=titulo,
            resumo=resumo,
            texto_alternativo=texto_alternativo,
        )

