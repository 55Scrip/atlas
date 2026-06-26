from pathlib import Path
import os

BASE_DIR = Path(os.environ.get("ATLAS_HOME", Path.cwd())).resolve()
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "atlas.db"
