import os
from collections.abc import Generator

from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, create_engine

_database: Engine | None = None
_session_maker: sessionmaker[Session] | None = None


def init_db() -> None:
    """
    Initialize the database connection.

    Uses DATABASE_URL if set, otherwise constructs it from individual
    environment variables (POSTGRES_USER, POSTGRES_PASSWORD, etc.)
    """
    global _database
    global _session_maker

    url = os.getenv("DATABASE_URL")
    if url is None:
        # Fallback to constructing URL from individual env vars
        user = os.getenv("POSTGRES_USER", "chrono")
        password = os.getenv("POSTGRES_PASSWORD", "chrono")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "chrono")
        url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"

    _database = create_engine(url)
    _session_maker = sessionmaker(
        class_=Session, autocommit=False, autoflush=False, bind=_database
    )


def _ensure_db_initialized():
    """
    Lazy loader: If the session maker isn't there (like in a Celery worker),
    initialize it.
    """
    global _session_maker
    if _session_maker is None:
        init_db()


def _get_session() -> Generator[Session, None, None]:
    assert _session_maker
    session: Session = _session_maker()
    try:
        yield session
        if session.in_transaction():
            session.commit()
    except Exception:
        if session.in_transaction():
            try:
                session.rollback()
            except Exception:
                raise SystemError("Failed to rollback session")
        raise
    finally:
        try:
            session.close()
        except Exception:
            raise SystemError("Failed to close session")


def get_db() -> Generator[Session, None, None]:
    _ensure_db_initialized()
    yield from _get_session()
