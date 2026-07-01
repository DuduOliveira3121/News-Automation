"""DTOs de notícia para comunicação entre camadas."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.domain.entities.news import NewsStatus


@dataclass(frozen=True)
class NewsDTO:
    """Transfere dados de uma notícia sem expor a entidade de domínio."""

    id: str
    title: str
    content: str
    source_file: str
    status: NewsStatus
    reviewed_content: Optional[str] = None


@dataclass(frozen=True)
class ParsedNewsDTO:
    """Representa uma notícia extraída do .docx antes de ser salva."""

    title: str
    content: str
    source_file: str


@dataclass(frozen=True)
class ReviewRequestDTO:
    """Dados enviados ao serviço de IA para revisão."""

    news_id: str
    title: str
    content: str


@dataclass(frozen=True)
class ReviewResultDTO:
    """Resultado da revisão devolvida pelo serviço de IA."""

    news_id: str
    reviewed_content: str


@dataclass(frozen=True)
class PublishRequestDTO:
    """Dados necessários para disparar a publicação no portal."""

    news_id: str
    title: str
    content: str
