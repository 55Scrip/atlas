from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from atlas.config import DATABASE_PATH

class Base(DeclarativeBase):
    pass

def get_engine(db_path: Path | None = None):
    path = db_path or DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{path}", future=True)

def get_session(db_path: Path | None = None):
    engine = get_engine(db_path)
    Session = sessionmaker(bind=engine, future=True)
    return Session()
