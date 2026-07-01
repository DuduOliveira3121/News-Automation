"""Testes unitários do SQLAlchemyNewsRepository."""
import pytest
from sqlalchemy.orm import Session

from src.domain.entities.news import News, NewsStatus
from src.infrastructure.repositories.news_repository import SQLAlchemyNewsRepository


class TestSQLAlchemyNewsRepository:
    """Testes de integração leve usando banco SQLite em memória."""

    def test_save_and_find_by_id(self, in_memory_session: Session) -> None:
        # TODO: implementar após o repositório ser desenvolvido
        pass

    def test_find_all_returns_empty_list_initially(self, in_memory_session: Session) -> None:
        pass

    def test_update_changes_status(self, in_memory_session: Session) -> None:
        pass

    def test_delete_removes_news(self, in_memory_session: Session) -> None:
        pass
