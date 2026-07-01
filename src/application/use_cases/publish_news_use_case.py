"""Use case: publicação de uma notícia no portal via Playwright."""
from __future__ import annotations

import logging

from src.application.services.publication_service import PublicationService
from src.domain.entities.publication import Publication
from src.domain.interfaces.news_repository import INewsRepository
from src.domain.interfaces.publication_repository import IPublicationRepository

logger = logging.getLogger(__name__)


class PublishNewsUseCase:
    """Orquestra a publicação de uma notícia revisada no portal.

    Responsabilidades:
        1. Validar que a notícia existe e está com status REVIEWED.
        2. Criar um registro de Publication (status QUEUED).
        3. Delegar ao PublicationService a automação via Playwright.
        4. Atualizar os status de News e Publication conforme resultado.
    """

    def __init__(
        self,
        publication_service: PublicationService,
        news_repository: INewsRepository,
        publication_repository: IPublicationRepository,
    ) -> None:
        self._publication_service = publication_service
        self._news_repository = news_repository
        self._publication_repository = publication_repository

    def execute(self, news_id: str) -> Publication:
        """Publica a notícia no portal e retorna o registro de publicação.

        Args:
            news_id: Identificador único da notícia a publicar.

        Returns:
            Entidade Publication com o resultado da operação.

        Raises:
            ValueError: Se a notícia não for encontrada ou não estiver revisada.
        """
        ...
