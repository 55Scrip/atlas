import sqlite3
from importlib.resources import files
from pathlib import Path

from atlas.config import DATABASE_PATH
from atlas.database.connection import get_engine, Base
from atlas.models import Company, FinancialHistory  # noqa: F401

def init_database(db_path: Path | None = None) -> Path:
    path = db_path or DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = get_engine(path)
    Base.metadata.create_all(engine)

    schema_sql = files("atlas.database").joinpath("schema.sql").read_text(encoding="utf-8")
    with sqlite3.connect(path) as conn:
        conn.executescript(schema_sql)

    return path
