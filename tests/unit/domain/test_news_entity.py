"""Testes unitários da entidade News."""
from __future__ import annotations

import re
from datetime import datetime
from unittest.mock import patch

import pytest

from src.domain.entities.news import News, NewsStatus


def _make_news(**kwargs) -> News:
    """Cria uma instância de News com valores padrão substituíveis."""
    defaults = {"titulo": "Título de Teste", "conteudo": "Conteúdo.", "source_file": "boletim.docx"}
    return News(**{**defaults, **kwargs})


class TestNewsDefaults:
    """Testes dos valores padrão da entidade News."""

    def test_default_status_is_pending(self) -> None:
        news = _make_news()

        assert news.status == NewsStatus.PENDING

    def test_default_id_is_uuid_v4_format(self) -> None:
        news = _make_news()
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        )

        assert uuid_pattern.match(news.id)

    def test_each_instance_gets_unique_id(self) -> None:
        news_a = _make_news()
        news_b = _make_news()

        assert news_a.id != news_b.id

    def test_default_reviewed_content_is_none(self) -> None:
        news = _make_news()

        assert news.reviewed_content is None

    def test_title_content_source_file_are_set(self) -> None:
        news = _make_news(titulo="T", conteudo="C", source_file="f.docx")

        assert news.titulo == "T"
        assert news.conteudo == "C"
        assert news.source_file == "f.docx"

    def test_created_at_is_datetime(self) -> None:
        news = _make_news()

        assert isinstance(news.created_at, datetime)

    def test_updated_at_is_datetime(self) -> None:
        news = _make_news()

        assert isinstance(news.updated_at, datetime)


class TestMarkAsReviewed:
    """Testes da transição para o estado REVIEWED."""

    def test_status_changes_to_reviewed(self) -> None:
        news = _make_news()

        news.mark_as_reviewed("Conteúdo revisado.")

        assert news.status == NewsStatus.REVIEWED

    def test_reviewed_content_is_stored(self) -> None:
        news = _make_news()

        news.mark_as_reviewed("Novo texto revisado.")

        assert news.reviewed_content == "Novo texto revisado."

    def test_updated_at_is_refreshed(self) -> None:
        news = _make_news()
        frozen = datetime(2025, 6, 1, 12, 0, 0)

        with patch("src.domain.entities.news.datetime") as mock_dt:
            mock_dt.utcnow.return_value = frozen
            news.mark_as_reviewed("revisado")

        assert news.updated_at == frozen

    def test_previous_reviewed_content_is_overwritten(self) -> None:
        news = _make_news()
        news.mark_as_reviewed("Versão 1")

        news.mark_as_reviewed("Versão 2")

        assert news.reviewed_content == "Versão 2"


class TestMarkAsPublished:
    """Testes da transição para o estado PUBLISHED."""

    def test_status_changes_to_published(self) -> None:
        news = _make_news()

        news.mark_as_published()

        assert news.status == NewsStatus.PUBLISHED

    def test_updated_at_is_refreshed(self) -> None:
        news = _make_news()
        frozen = datetime(2025, 6, 1, 15, 0, 0)

        with patch("src.domain.entities.news.datetime") as mock_dt:
            mock_dt.utcnow.return_value = frozen
            news.mark_as_published()

        assert news.updated_at == frozen

    def test_reviewed_content_is_not_affected(self) -> None:
        news = _make_news()
        news.mark_as_reviewed("conteúdo revisado")

        news.mark_as_published()

        assert news.reviewed_content == "conteúdo revisado"


class TestMarkAsFailed:
    """Testes da transição para o estado FAILED."""

    def test_status_changes_to_failed(self) -> None:
        news = _make_news()

        news.mark_as_failed()

        assert news.status == NewsStatus.FAILED

    def test_updated_at_is_refreshed(self) -> None:
        news = _make_news()
        frozen = datetime(2025, 6, 1, 18, 0, 0)

        with patch("src.domain.entities.news.datetime") as mock_dt:
            mock_dt.utcnow.return_value = frozen
            news.mark_as_failed()

        assert news.updated_at == frozen

    def test_reviewed_content_is_not_affected(self) -> None:
        news = _make_news()

        news.mark_as_failed()

        assert news.reviewed_content is None


class TestNewsStatusEnum:
    """Testes do enum NewsStatus."""

    def test_status_values_are_strings(self) -> None:
        assert NewsStatus.PENDING == "pending"
        assert NewsStatus.REVIEWED == "reviewed"
        assert NewsStatus.PUBLISHED == "published"
        assert NewsStatus.FAILED == "failed"

