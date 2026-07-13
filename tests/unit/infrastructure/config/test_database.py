"""Tests for the neutral database configuration boundary (ATLAS-003)."""
from __future__ import annotations

from pathlib import Path

from atlas.core.infrastructure.config import database as database_module
from atlas.core.infrastructure.config.database import (
    create_database_engine,
    resolve_database_path,
)


class TestResolveDatabasePath:
    def test_explicit_path_argument_takes_precedence(self, monkeypatch, tmp_path):
        monkeypatch.setenv("ATLAS_CORE_DB_PATH", str(tmp_path / "env_path.db"))
        explicit = tmp_path / "explicit" / "explicit.db"

        result = resolve_database_path(explicit)

        assert result == explicit
        assert explicit.parent.is_dir()

    def test_environment_variable_is_used_when_no_explicit_path(self, monkeypatch, tmp_path):
        env_path = tmp_path / "from_env" / "atlas.db"
        monkeypatch.setenv("ATLAS_CORE_DB_PATH", str(env_path))

        result = resolve_database_path()

        assert result == env_path
        assert env_path.parent.is_dir()

    def test_falls_back_to_atlas_config_database_path(self, monkeypatch):
        monkeypatch.delenv("ATLAS_CORE_DB_PATH", raising=False)

        result = resolve_database_path()

        # Compare against the same reference resolve_database_path() itself
        # holds (bound once, at this module's own first import) rather than
        # a fresh `from atlas.config import DATABASE_PATH` — an unrelated
        # legacy test (tests/test_config_sprint195.py) reloads atlas.config
        # via importlib.reload with a monkeypatched ATLAS_HOME, and its
        # "restore" step runs before monkeypatch reverts the env var,
        # leaving that live module attribute unreliable for the rest of
        # the test session. This module's own frozen import isn't affected
        # by that reload.
        assert result == database_module.DATABASE_PATH

    def test_creates_parent_directory_when_missing(self, monkeypatch, tmp_path):
        nested = tmp_path / "does" / "not" / "exist" / "atlas.db"
        monkeypatch.setenv("ATLAS_CORE_DB_PATH", str(nested))

        resolve_database_path()

        assert nested.parent.is_dir()


class TestCreateDatabaseEngine:
    def test_builds_a_working_sqlite_engine(self, tmp_path):
        db_path = tmp_path / "engine_test.db"
        engine = create_database_engine(db_path)

        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")

        assert Path(db_path).parent.is_dir()
