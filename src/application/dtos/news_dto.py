"""DTOs de notícia para comunicação entre camadas."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.domain.entities.news import NewsStatus


@dataclass(frozen=True)
class NewsDTO:
    """Transfere dados de uma notícia sem expor a entidade de domínio."""

    id: str
    titulo: str
    conteudo: str
    source_file: str
    status: NewsStatus
    resumo: Optional[str] = None
    categoria: Optional[str] = None
    imagem: Optional[str] = None
    texto_alternativo: Optional[str] = None
    reviewed_content: Optional[str] = None


@dataclass(frozen=True)
class ParsedNewsDTO:
    """Representa uma notícia extraída do .docx antes de ser salva."""

    titulo: str
    conteudo: str
    source_file: str
    resumo: Optional[str] = None
    categoria: Optional[str] = None
    imagem: Optional[str] = None
    texto_alternativo: Optional[str] = None


@dataclass(frozen=True)
class ReviewRequestDTO:
    """Dados enviados ao serviço de IA para revisão."""

    news_id: str
    titulo: str
    conteudo: str


@dataclass(frozen=True)
class ReviewResultDTO:
    """Resultado da revisão devolvida pelo serviço de IA."""

    news_id: str
    reviewed_content: str
    titulo: Optional[str] = None
    resumo: Optional[str] = None
    texto_alternativo: Optional[str] = None


@dataclass(frozen=True)
class PublishRequestDTO:
    """Dados necessários para disparar a publicação no portal."""

    news_id: str
    titulo: str
    conteudo: str
    reviewed_content: Optional[str] = None
    categoria: Optional[str] = None
    imagem: Optional[str] = None
