"""Serviço de gerenciamento de notícias — listagem e atualização de campos."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from src.application.dtos.news_dto import NewsDTO
from src.domain.entities.news import News
from src.domain.interfaces.news_repository import INewsRepository

logger = logging.getLogger(__name__)


class NewsService:
    """Fornece operações de leitura e atualização sobre notícias.

    Esta camada separa a interface gráfica do repositório, garantindo que
    nenhuma página do Streamlit acesse o repositório diretamente.
    """

    def __init__(self, news_repository: INewsRepository) -> None:
        self._repository = news_repository

    # ── Leitura ──────────────────────────────────────────────────

    def list_all(self) -> List[NewsDTO]:
        """Retorna todas as notícias armazenadas como DTOs."""
        return [self._to_dto(n) for n in self._repository.find_all()]

    def find_by_id(self, news_id: str) -> Optional[NewsDTO]:
        """Retorna uma notícia pelo ID, ou None se não encontrada."""
        news = self._repository.find_by_id(news_id)
        return self._to_dto(news) if news else None

    # ── Atualização ──────────────────────────────────────────────

    def update_fields(
        self,
        news_id: str,
        titulo: str,
        conteudo: str,
        resumo: Optional[str] = None,
        categoria: Optional[str] = None,
        imagem: Optional[str] = None,
        texto_alternativo: Optional[str] = None,
    ) -> NewsDTO:
        """Atualiza os campos editáveis de uma notícia e retorna o DTO atualizado.

        Args:
            news_id: Identificador único da notícia.
            titulo: Novo título.
            conteudo: Novo conteúdo.
            resumo: Novo resumo (opcional).
            categoria: Nova categoria (opcional).
            imagem: Caminho ou URL da imagem (opcional).
            texto_alternativo: Texto alternativo da imagem (opcional).

        Returns:
            NewsDTO atualizado.

        Raises:
            ValueError: Se a notícia não for encontrada.
        """
        news = self._repository.find_by_id(news_id)
        if news is None:
            raise ValueError(f"Notícia '{news_id}' não encontrada.")

        news.titulo = titulo
        news.conteudo = conteudo
        news.resumo = resumo
        news.categoria = categoria
        news.imagem = imagem
        news.texto_alternativo = texto_alternativo
        news.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        updated = self._repository.update(news)
        logger.info("Notícia atualizada via NewsService: id=%s", news_id)
        return self._to_dto(updated)

    # ── Conversão interna ─────────────────────────────────────────

    def _to_dto(self, news: News) -> NewsDTO:
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
