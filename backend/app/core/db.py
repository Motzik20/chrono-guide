import os

from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, create_engine

_DATABASE: Engine | None = None
_SESSION_MAKER: sessionmaker | None = None


def init_db(local: bool):
    global _DATABASE
    global _SESSION_MAKER
    if local:
        _DATABASE = create_local_db_engine()

    else:
        _DATABASE = create_db_engine()
    _SESSION_MAKER = sessionmaker(autocommit=False, autoflush=False, bind=_DATABASE)


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
    if _SESSION_MAKER is None:
        raise ValueError("Database not initialized properly")
    return _SESSION_MAKER()


def _get_session():
    assert _SESSION_MAKER
    session = _SESSION_MAKER()
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


def get_db():
    yield from _get_session()
