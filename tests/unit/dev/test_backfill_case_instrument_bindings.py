"""The production guard on the Case-instrument backfill command.

`atlas/dev/__init__.py` states that every command in this package
"refuses to run unless `ATLAS_ENV` is unset or `'development'`". This
command shipped without that call; these tests pin it so it cannot be
dropped again.
"""
from __future__ import annotations

import pytest

from atlas.dev.backfill_case_instrument_bindings import main
from atlas.dev.guard import NotDevelopmentEnvironmentError


class TestProductionGuard:
    def test_refuses_when_atlas_env_is_production(self, monkeypatch, tmp_path):
        monkeypatch.setenv("ATLAS_ENV", "production")
        monkeypatch.setattr("sys.argv", ["backfill", "--database", str(tmp_path / "atlas.db")])
        with pytest.raises(NotDevelopmentEnvironmentError):
            main()

    def test_refuses_before_touching_any_database(self, monkeypatch, tmp_path):
        """The guard runs first, so a refused invocation must not have
        created the database file it was pointed at."""
        database = tmp_path / "atlas.db"
        monkeypatch.setenv("ATLAS_ENV", "production")
        monkeypatch.setattr("sys.argv", ["backfill", "--database", str(database)])
        with pytest.raises(NotDevelopmentEnvironmentError):
            main()
        assert not database.exists()

    def test_runs_when_atlas_env_is_unset(self, monkeypatch, tmp_path):
        monkeypatch.delenv("ATLAS_ENV", raising=False)
        monkeypatch.setattr("sys.argv", ["backfill", "--database", str(tmp_path / "atlas.db")])
        assert main() == 0

    def test_runs_when_atlas_env_is_development(self, monkeypatch, tmp_path):
        monkeypatch.setenv("ATLAS_ENV", "development")
        monkeypatch.setattr("sys.argv", ["backfill", "--database", str(tmp_path / "atlas.db")])
        assert main() == 0
