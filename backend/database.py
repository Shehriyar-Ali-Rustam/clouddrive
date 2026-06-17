"""
SQLAlchemy engine + session setup.

Swapping SQLite (local) for PostgreSQL/RDS (cloud) is just a change of
DATABASE_URL in the environment — no code changes needed.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

# check_same_thread is a SQLite-only quirk; harmless to compute, ignored by Postgres.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
