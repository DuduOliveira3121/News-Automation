"""Testes unitários da entidade News."""
import pytest

from src.domain.entities.news import News, NewsStatus


class TestNewsEntity:
    """Testes das transições de estado da entidade News."""

    def test_default_status_is_pending(self) -> None:
        # TODO: implementar após a entidade ser desenvolvida
        pass

    def test_mark_as_reviewed_changes_status(self) -> None:
        pass

    def test_mark_as_published_changes_status(self) -> None:
        pass

    def test_mark_as_failed_changes_status(self) -> None:
        pass
