"""Sprint 195: Config module audit guardrails.

atlas/config.py is a 6-line foundational infrastructure module.
It reads one environment variable (ATLAS_HOME), derives three path
constants (BASE_DIR, DATABASE_DIR, DATABASE_PATH), and exposes them
for use by the database layer. It imports nothing from Atlas packages.

These tests confirm:
  - DATABASE_PATH is importable and is a pathlib.Path
  - DATABASE_PATH filename is atlas.db
  - atlas/config.py imports only stdlib (pathlib, os)
  - atlas/config.py does not import providers
  - ATLAS_HOME env var is respected when set
"""

from __future__ import annotations

import ast
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "atlas" / "config.py"


# ── Basic import and type checks ─────────────────────────────────────────────

def test_config_database_path_importable() -> None:
    """DATABASE_PATH is importable from atlas.config."""
    from atlas.config import DATABASE_PATH  # noqa: F401

    assert DATABASE_PATH is not None


def test_config_database_path_is_path_object() -> None:
    """DATABASE_PATH is a pathlib.Path instance."""
    from atlas.config import DATABASE_PATH

    assert isinstance(DATABASE_PATH, Path), (
        f"DATABASE_PATH must be a pathlib.Path, got {type(DATABASE_PATH)}"
    )


def test_config_database_path_ends_with_atlas_db() -> None:
    """DATABASE_PATH filename is atlas.db."""
    from atlas.config import DATABASE_PATH

    assert DATABASE_PATH.name == "atlas.db", (
        f"DATABASE_PATH filename must be 'atlas.db', got {DATABASE_PATH.name!r}"
    )


# ── Boundary guards — imports ─────────────────────────────────────────────────

def _config_imports() -> list[str]:
    tree = ast.parse(CONFIG_PATH.read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(a.name for a in node.names)
    return modules


def test_config_does_not_import_atlas_packages() -> None:
    """atlas/config.py imports only stdlib (pathlib, os) — no Atlas packages.

    Config is the lowest-level infrastructure layer. It must not import
    from any Atlas package to avoid circular dependencies.
    """
    imports = _config_imports()
    atlas_imports = [m for m in imports if m.startswith("atlas")]
    assert not atlas_imports, (
        f"atlas/config.py must not import from Atlas packages: {atlas_imports}"
    )


def test_config_does_not_import_providers() -> None:
    """atlas/config.py does not import from atlas.providers."""
    imports = _config_imports()
    provider_imports = [m for m in imports if "provider" in m.lower()]
    assert not provider_imports, (
        f"atlas/config.py must not import providers: {provider_imports}"
    )


# ── Environment variable behavior ─────────────────────────────────────────────

def test_atlas_home_env_var_respected(tmp_path: Path, monkeypatch: object) -> None:
    """When ATLAS_HOME is set, DATABASE_PATH is derived from it.

    This verifies the single configuration knob in atlas/config.py works.
    Uses a temporary directory to avoid side effects.
    """
    import importlib
    import sys

    # Set ATLAS_HOME to a temp path and reload config
    monkeypatch.setenv("ATLAS_HOME", str(tmp_path))  # type: ignore[attr-defined]

    # Remove cached module so it re-evaluates env var
    sys.modules.pop("atlas.config", None)
    try:
        import atlas.config as cfg
        importlib.reload(cfg)
        assert cfg.DATABASE_PATH == tmp_path / "database" / "atlas.db", (
            f"DATABASE_PATH should be derived from ATLAS_HOME={tmp_path}, "
            f"got {cfg.DATABASE_PATH}"
        )
    finally:
        # Restore original module
        sys.modules.pop("atlas.config", None)
        import atlas.config  # noqa: F401 — re-import with original env
