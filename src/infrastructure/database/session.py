"""Configuração da sessão SQLAlchemy e inicialização do banco."""
from __future__ import annotations

import logging
from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import settings
from src.infrastructure.database.models import Base

logger = logging.getLogger(__name__)

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Retorna (ou cria) o engine SQLAlchemy singleton."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},  # necessário para SQLite
            echo=settings.debug,
        )
    return _engine


def init_db() -> None:
    """Cria todas as tabelas no banco de dados (idempotente)."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Banco de dados inicializado: %s", settings.database_url)


def get_session() -> Generator[Session, None, None]:
    """Gerador de sessão para uso com injeção de dependência.

    Uso:
        with get_session() as session:
            ...
    """
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)

    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
