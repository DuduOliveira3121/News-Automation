"""Repositório SQLAlchemy para persistência de notícias."""
from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from src.domain.entities.news import News, NewsStatus
from src.infrastructure.database.models import NewsModel

logger = logging.getLogger(__name__)


class NewsRepository:
    """Responsável por toda comunicação com o banco para a entidade News."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Mapeamento domínio ↔ ORM ─────────────────────────────────

    def _to_model(self, news: News) -> NewsModel:
        return NewsModel(
            id=news.id,
            titulo=news.titulo,
            resumo=news.resumo,
            conteudo=news.conteudo,
            categoria=news.categoria,
            imagem=news.imagem,
            texto_alternativo=news.texto_alternativo,
            source_file=news.source_file,
            status=news.status,
            reviewed_content=news.reviewed_content,
            created_at=news.created_at,
            updated_at=news.updated_at,
        )

    def _to_entity(self, model: NewsModel) -> News:
        return News(
            id=model.id,
            titulo=model.titulo,
            resumo=model.resumo,
            conteudo=model.conteudo,
            categoria=model.categoria,
            imagem=model.imagem,
            texto_alternativo=model.texto_alternativo,
            source_file=model.source_file,
            status=model.status,
            reviewed_content=model.reviewed_content,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    # ── Operações de persistência ────────────────────────────────

    def save(self, news: News) -> News:
        model = self._to_model(news)
        self._session.add(model)
        self._session.flush()
        logger.debug("Notícia salva: id=%s", news.id)
        return self._to_entity(model)

    def find_by_id(self, news_id: str) -> Optional[News]:
        model = self._session.get(NewsModel, news_id)
        return self._to_entity(model) if model else None

    def find_all(self) -> List[News]:
        models = self._session.query(NewsModel).all()
        return [self._to_entity(m) for m in models]

    def find_by_status(self, status: NewsStatus) -> List[News]:
        models = (
            self._session.query(NewsModel)
            .filter(NewsModel.status == status)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def update(self, news: News) -> News:
        model = self._session.get(NewsModel, news.id)
        if model is None:
            raise ValueError(f"Notícia com id '{news.id}' não encontrada.")
        model.titulo = news.titulo
        model.resumo = news.resumo
        model.conteudo = news.conteudo
        model.categoria = news.categoria
        model.imagem = news.imagem
        model.texto_alternativo = news.texto_alternativo
        model.status = news.status
        model.reviewed_content = news.reviewed_content
        model.updated_at = news.updated_at
        self._session.flush()
        logger.debug("Notícia atualizada: id=%s", news.id)
        return self._to_entity(model)

    def delete(self, news_id: str) -> None:
        model = self._session.get(NewsModel, news_id)
        if model:
            self._session.delete(model)
            self._session.flush()
            logger.debug("Notícia removida: id=%s", news_id)

