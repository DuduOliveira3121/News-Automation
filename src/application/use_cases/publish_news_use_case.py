"""Use case: publicação de uma notícia no portal via Playwright."""
from __future__ import annotations

import logging

from config.settings import settings
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

        Fluxo:
            1. Valida que a notícia existe.
            2. Cria e persiste um Publication com status QUEUED.
            3. Delega ao PublicationService a automação via Playwright.
            4. Atualiza Publication e marca News como PUBLISHED ou FAILED.

        Args:
            news_id: Identificador único da notícia a publicar.

        Returns:
            Entidade Publication com o resultado da operação.

        Raises:
            ValueError: Se a notícia não for encontrada.
        """
        from src.application.dtos.news_dto import PublishRequestDTO

        news = self._news_repository.find_by_id(news_id)
        if news is None:
            raise ValueError(f"Notícia '{news_id}' não encontrada.")

        request = PublishRequestDTO(
            news_id=news.id,
            titulo=news.titulo,
            conteudo=news.conteudo,
            reviewed_content=news.reviewed_content,
            categoria=news.categoria,
            imagem=news.imagem,
        )

        # Persiste registro inicial (QUEUED → IN_PROGRESS via service)
        placeholder = Publication(
            news_id=news.id,
            portal_url=settings.portal_url or "not-configured",
        )
        saved_pub = self._publication_repository.save(placeholder)

        # Executa a publicação
        result = self._publication_service.publish(request)
        result.id = saved_pub.id  # mantém o ID persistido

        # Atualiza o registro de publicação
        updated_pub = self._publication_repository.update(result)

        # Atualiza status da notícia
        if result.status.value == "success":
            news.mark_as_published()
        else:
            news.mark_as_failed()
        self._news_repository.update(news)

        logger.info(
            "PublishNewsUseCase concluído: news_id=%s status=%s",
            news_id,
            result.status.value,
        )
        return updated_pub
