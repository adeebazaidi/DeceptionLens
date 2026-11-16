"""
DeceptionLens — Database Connection
===================================
Configures the SQLAlchemy engine and session factory.

The database location is configurable via the DATABASE_URL environment
variable. By default a local SQLite file (backend/deceptionlens.db) is used.
"""

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
DEFAULT_DATABASE_URL = f"sqlite:///{(BASE_DIR / 'deceptionlens.db').as_posix()}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

# SQLite connections must be shareable across FastAPI's threadpool workers.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def init_db() -> None:
    """Create all tables if they do not already exist (idempotent)."""
    # Import models so they are registered on Base.metadata before create_all.
    from database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a request-scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
