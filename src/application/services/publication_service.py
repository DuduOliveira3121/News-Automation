"""Serviço de publicação: orquestra a automação no portal."""
from __future__ import annotations

import logging

from src.application.dtos.news_dto import PublishRequestDTO
from src.domain.entities.publication import Publication

logger = logging.getLogger(__name__)


class PublicationService:
    """Coordena a publicação de notícias no portal de notícias.

    Delega a automação de browser ao PortalAutomation (infraestrutura),
    mantendo a camada de aplicação desacoplada do Playwright.
    """

    def publish(self, request: PublishRequestDTO) -> Publication:
        """Publica a notícia no portal e retorna o registro resultante.

        Args:
            request: DTO com os dados necessários para publicação.

        Returns:
            Entidade Publication com status SUCCESS ou FAILED.
        """
        ...
