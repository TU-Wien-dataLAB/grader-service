from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker


_engine: Engine | None = None


def get_engine(database_url: str) -> Engine:
    """Create the engine on first use and cache it at module level."""
    global _engine
    if _engine is None:
        _engine = create_engine(database_url, pool_pre_ping=True)
    return _engine


def dispose_engine():
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None


def session_maker(url: str) -> sessionmaker:
    """Create session maker"""
    return sessionmaker(bind=get_engine(url), expire_on_commit=False)
