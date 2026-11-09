from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def create_sync_session_maker(url: str) -> sessionmaker:
    engine = create_engine(url, pool_pre_ping=True)
    return sessionmaker(bind=engine, expire_on_commit=False)
