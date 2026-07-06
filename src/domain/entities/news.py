"""Entidade principal de domínio: Notícia."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class NewsStatus(str, Enum):
    """Ciclo de vida de uma notícia dentro do sistema."""

    PENDING = "pending"
    REVIEWED = "reviewed"
    PUBLISHED = "published"
    FAILED = "failed"


@dataclass
class News:
    """Representa uma notícia extraída de um arquivo .docx.

    Atributos:
        id: Identificador único (UUID v4).
        titulo: Título da notícia.
        conteudo: Conteúdo original extraído do .docx.
        source_file: Nome do arquivo de origem.
        resumo: Resumo da notícia (opcional).
        categoria: Categoria da notícia (opcional).
        imagem: Caminho ou URL da imagem de capa (opcional).
        texto_alternativo: Texto alternativo da imagem (opcional).
        status: Estado atual no ciclo de vida.
        reviewed_content: Conteúdo após revisão pela IA (opcional).
        created_at: Data/hora de criação.
        updated_at: Data/hora da última atualização.
    """

    titulo: str
    conteudo: str
    source_file: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    resumo: Optional[str] = field(default=None)
    categoria: Optional[str] = field(default=None)
    imagem: Optional[str] = field(default=None)
    texto_alternativo: Optional[str] = field(default=None)
    status: NewsStatus = field(default=NewsStatus.PENDING)
    reviewed_content: Optional[str] = field(default=None)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def mark_as_reviewed(self, reviewed_content: str) -> None:
        """Transiciona para o estado REVIEWED com o conteúdo revisado."""
        self.reviewed_content = reviewed_content
        self.status = NewsStatus.REVIEWED
        self.updated_at = datetime.utcnow()

    def mark_as_published(self) -> None:
        """Transiciona para o estado PUBLISHED."""
        self.status = NewsStatus.PUBLISHED
        self.updated_at = datetime.utcnow()

    def mark_as_failed(self) -> None:
        """Transiciona para o estado FAILED."""
        self.status = NewsStatus.FAILED
        self.updated_at = datetime.utcnow()
