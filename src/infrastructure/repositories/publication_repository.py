"""Implementação SQLAlchemy do IPublicationRepository."""
from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from src.domain.entities.publication import Publication, PublicationStatus
from src.domain.interfaces.publication_repository import IPublicationRepository
from src.infrastructure.database.models import PublicationModel

logger = logging.getLogger(__name__)


class SQLAlchemyPublicationRepository(IPublicationRepository):
    """Repositório de publicações usando SQLAlchemy + SQLite."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Mapeamento entre domínio ↔ ORM ──────────────────────────

    def _to_model(self, publication: Publication) -> PublicationModel:
        """Converte entidade de domínio para modelo ORM."""
        ...

    def _to_entity(self, model: PublicationModel) -> Publication:
        """Converte modelo ORM para entidade de domínio."""
        ...

    # ── Implementação do contrato ────────────────────────────────

    def save(self, publication: Publication) -> Publication:
        ...

    def find_by_id(self, publication_id: str) -> Optional[Publication]:
        ...

    def find_by_news_id(self, news_id: str) -> List[Publication]:
        ...

    def find_by_status(self, status: PublicationStatus) -> List[Publication]:
        ...

    def update(self, publication: Publication) -> Publication:
        ...
