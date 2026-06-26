from pathlib import Path
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from atlas.config import DATABASE_PATH


class Base(DeclarativeBase):
    pass


def get_engine(db_path: Path | None = None) -> Engine:
    path = db_path or DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{path}", future=True)


def get_session(db_path: Path | None = None) -> Session:
    engine = get_engine(db_path)
    session_factory = sessionmaker(bind=engine, future=True)
    return session_factory()
