"""Modelos ORM (SQLAlchemy) mapeados às entidades de domínio."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.domain.entities.news import NewsStatus
from src.domain.entities.publication import PublicationStatus


class Base(DeclarativeBase):
    """Base declarativa compartilhada por todos os modelos."""


class NewsModel(Base):
    """Tabela `news` — armazena as notícias extraídas dos arquivos .docx."""

    __tablename__ = "news"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_file: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[NewsStatus] = mapped_column(
        Enum(NewsStatus), nullable=False, default=NewsStatus.PENDING
    )
    reviewed_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class PublicationModel(Base):
    """Tabela `publications` — registra cada tentativa de publicação."""

    __tablename__ = "publications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    news_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    portal_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    status: Mapped[PublicationStatus] = mapped_column(
        Enum(PublicationStatus), nullable=False, default=PublicationStatus.QUEUED
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
