"""Serviço de publicação: orquestra a automação no portal."""
from __future__ import annotations

import logging

from config.settings import settings
from src.application.dtos.news_dto import NewsDTO, PublishRequestDTO
from src.domain.entities.news import NewsStatus
from src.domain.entities.publication import Publication

logger = logging.getLogger(__name__)


class PublicationService:
    """Coordena a publicação de notícias no portal de notícias.

    Delega a automação de browser ao SitePublisher (infraestrutura),
    mantendo a camada de aplicação desacoplada do Playwright.

    Padrão aplicado: Facade — expõe um único método ``publish()``
    que encapsula todo o fluxo de automação do browser.
    """

    def __init__(self, headless: bool = True) -> None:
        self._headless = headless

    def publish(self, request: PublishRequestDTO) -> Publication:
        """Publica a notícia no portal e retorna o registro resultante.

        Cria uma entidade Publication, executa a automação via SitePublisher
        e retorna a publicação com status SUCCESS ou FAILED.

        Args:
            request: DTO com os dados necessários para publicação.

        Returns:
            Entidade Publication com status SUCCESS ou FAILED.

        Raises:
            ValueError: Se PORTAL_URL não estiver configurada.
        """
        # Import lazy para evitar importação do Playwright na inicialização
        from src.infrastructure.automation.site_publisher import SitePublisher

        portal_url = settings.portal_url
        if not portal_url:
            raise ValueError(
                "PORTAL_URL não está configurada. "
                "Adicione PORTAL_URL, PORTAL_USERNAME e PORTAL_PASSWORD no arquivo .env."
            )

        publication = Publication(
            news_id=request.news_id,
            portal_url=portal_url,
        )
        publication.mark_in_progress()

        # Monta um NewsDTO mínimo para o SitePublisher
        news_dto = NewsDTO(
            id=request.news_id,
            titulo=request.titulo,
            conteudo=request.conteudo,
            source_file="",
            status=NewsStatus.REVIEWED,
            reviewed_content=request.reviewed_content,
            categoria=request.categoria,
            imagem=request.imagem,
        )

        try:
            with SitePublisher(headless=self._headless) as publisher:
                publisher.login()
                publisher.abrir_painel()
                publisher.criar_noticia()
                publisher.preencher_campos(news_dto)
                if request.imagem:
                    try:
                        publisher.enviar_imagem(request.imagem)
                    except FileNotFoundError:
                        logger.warning(
                            "Imagem '%s' não encontrada — publicando sem imagem.",
                            request.imagem,
                        )
                publisher.publicar()
            publication.mark_success()
            logger.info("Publicação concluída com sucesso: news_id=%s", request.news_id)
        except Exception as exc:
            logger.exception("Erro ao publicar notícia news_id=%s.", request.news_id)
            publication.mark_failed(str(exc))

        return publication

