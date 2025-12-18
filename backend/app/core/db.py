import os
from collections.abc import Generator
from typing import cast

from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, create_engine

_database: Engine | None = None
_session_maker: sessionmaker[Session] | None = None


def init_db(local: bool) -> None:
    global _database
    global _session_maker
    if local:
        _database = create_local_db_engine()
    else:
        _database = create_db_engine()
    _session_maker = cast(sessionmaker[Session], sessionmaker(autocommit=False, autoflush=False, bind=_database))


def create_local_db_engine() -> Engine:
    # Default to local Dockerized Postgres; override via env if provided
    user = os.getenv("POSTGRES_USER", "chrono")
    password = os.getenv("POSTGRES_PASSWORD", "chrono")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "chrono")
    url = os.getenv(
        "DATABASE_URL",
        f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}",
    )
    return create_engine(url)


def create_db_engine() -> Engine:
    url = os.getenv("DATABASE_URL")
    if url is None:
        raise ValueError("DATABASE_URL is not set")
    return create_engine(url)


def get_session() -> Session:
    if _session_maker is None:
        raise ValueError("Database not initialized properly")
    return _session_maker()


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
                pass
        raise
    finally:
        try:
            session.close()
        except Exception:
            pass


def get_db() -> Generator[Session, None, None]:
    yield from _get_session()
