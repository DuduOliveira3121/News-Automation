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
        return PublicationModel(
            id=publication.id,
            news_id=publication.news_id,
            portal_url=publication.portal_url,
            status=publication.status,
            error_message=publication.error_message,
            published_at=publication.published_at,
            created_at=publication.created_at,
        )

    def _to_entity(self, model: PublicationModel) -> Publication:
        """Converte modelo ORM para entidade de domínio."""
        return Publication(
            id=model.id,
            news_id=model.news_id,
            portal_url=model.portal_url,
            status=model.status,
            error_message=model.error_message,
            published_at=model.published_at,
            created_at=model.created_at,
        )

    # ── Implementação do contrato ────────────────────────────────

    def save(self, publication: Publication) -> Publication:
        model = self._to_model(publication)
        self._session.add(model)
        self._session.flush()
        logger.debug("Publication salva: id=%s", publication.id)
        return self._to_entity(model)

    def find_by_id(self, publication_id: str) -> Optional[Publication]:
        model = self._session.get(PublicationModel, publication_id)
        return self._to_entity(model) if model else None

    def find_by_news_id(self, news_id: str) -> List[Publication]:
        models = (
            self._session.query(PublicationModel)
            .filter(PublicationModel.news_id == news_id)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def find_by_status(self, status: PublicationStatus) -> List[Publication]:
        models = (
            self._session.query(PublicationModel)
            .filter(PublicationModel.status == status)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def update(self, publication: Publication) -> Publication:
        model = self._session.get(PublicationModel, publication.id)
        if model is None:
            raise ValueError(f"Publication '{publication.id}' não encontrada.")
        model.portal_url = publication.portal_url
        model.status = publication.status
        model.error_message = publication.error_message
        model.published_at = publication.published_at
        self._session.flush()
        logger.debug("Publication atualizada: id=%s", publication.id)
        return self._to_entity(model)

