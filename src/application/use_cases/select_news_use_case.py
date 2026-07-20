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
        news = self._news_repository.find_by_id(news_id)
        if news is None:
            logger.debug("Notícia não encontrada: id=%s", news_id)
            return None
        return NewsDTO(
            id=news.id,
            titulo=news.titulo,
            conteudo=news.conteudo,
            source_file=news.source_file,
            status=news.status,
            resumo=news.resumo,
            categoria=news.categoria,
            imagem=news.imagem,
            texto_alternativo=news.texto_alternativo,
            reviewed_content=news.reviewed_content,
        )
