"""Fixtures compartilhadas entre todos os testes (pytest conftest)."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.infrastructure.database.models import Base


@pytest.fixture(scope="function")
def in_memory_session() -> Session:
    """Cria uma sessão SQLAlchemy em banco SQLite em memória para testes.

    Cada teste recebe um banco limpo — tabelas criadas e destruídas
    automaticamente ao final do teste.
    """
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
