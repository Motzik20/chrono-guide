import os
from collections.abc import Generator

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
    _session_maker = sessionmaker(
        class_=Session, autocommit=False, autoflush=False, bind=_database
    )


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
    yield from _get_session()
