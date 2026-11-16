"""
DeceptionLens — Database Connection & Session Factory
=====================================================
Configures the SQLAlchemy 2.0 engine and session factory.

The database location is configurable via the DATABASE_URL environment
variable (the Docker setup and the test suite rely on this). By default a
local SQLite file at backend/database/deceptionlens.db is used.

SQLite foreign-key constraints are enforced for forensic referential
integrity. WAL journaling is intentionally not enabled: it relies on shared
memory files that are unreliable on Docker Desktop bind mounts and synced
folders such as OneDrive.
"""

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
DB_PATH = BASE_DIR / "database" / "deceptionlens.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")

_IS_SQLITE = DATABASE_URL.startswith("sqlite")

# SQLite connections must be shareable across FastAPI's threadpool workers.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if _IS_SQLITE else {},
    echo=False,
)

if _IS_SQLITE:
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def init_db() -> None:
    """Create all tables if they do not already exist (never drops data)."""
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
