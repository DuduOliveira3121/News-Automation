"""Entidade de domínio: Publicação."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class PublicationStatus(str, Enum):
    """Status de uma tentativa de publicação no portal."""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class Publication:
    """Registra cada tentativa de publicação de uma notícia no portal.

    Atributos:
        id: Identificador único (UUID v4).
        news_id: Referência à notícia publicada.
        portal_url: URL do portal alvo.
        status: Estado da publicação.
        error_message: Mensagem de erro (quando falhou).
        published_at: Timestamp de publicação bem-sucedida.
        created_at: Timestamp de criação do registro.
    """

    news_id: str
    portal_url: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: PublicationStatus = field(default=PublicationStatus.QUEUED)
    error_message: Optional[str] = field(default=None)
    published_at: Optional[datetime] = field(default=None)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def mark_in_progress(self) -> None:
        """Transiciona para IN_PROGRESS."""
        self.status = PublicationStatus.IN_PROGRESS

    def mark_success(self) -> None:
        """Transiciona para SUCCESS registrando o timestamp."""
        self.status = PublicationStatus.SUCCESS
        self.published_at = datetime.utcnow()

    def mark_failed(self, reason: str) -> None:
        """Transiciona para FAILED com a mensagem de erro."""
        self.status = PublicationStatus.FAILED
        self.error_message = reason
