"""Implementação SQLAlchemy do INewsRepository."""
from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from src.domain.entities.news import News, NewsStatus
from src.domain.interfaces.news_repository import INewsRepository
from src.infrastructure.database.models import NewsModel

logger = logging.getLogger(__name__)


class SQLAlchemyNewsRepository(INewsRepository):
    """Repositório de notícias usando SQLAlchemy + SQLite."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Mapeamento entre domínio ↔ ORM ──────────────────────────

    def _to_model(self, news: News) -> NewsModel:
        """Converte entidade de domínio para modelo ORM."""
        ...

    def _to_entity(self, model: NewsModel) -> News:
        """Converte modelo ORM para entidade de domínio."""
        ...

    # ── Implementação do contrato ────────────────────────────────

    def save(self, news: News) -> News:
        ...

    def find_by_id(self, news_id: str) -> Optional[News]:
        ...

    def find_all(self) -> List[News]:
        ...

    def find_by_status(self, status: NewsStatus) -> List[News]:
        ...

    def update(self, news: News) -> News:
        ...

    def delete(self, news_id: str) -> None:
        ...
