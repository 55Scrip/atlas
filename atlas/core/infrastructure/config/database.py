"""Neutral infrastructure configuration boundary for the persistent Atlas
core database (ATLAS-003).

Contains no conversation or review behavior whatsoever — purely path and
engine resolution, consumed by both the First Decision Conversation CLI
and the Decision Review CLI so they reconnect through the same physical
database.

Precedence for the resolved path:
1. An explicit path argument, if given.
2. The ATLAS_CORE_DB_PATH environment variable, if set.
3. atlas.config.DATABASE_PATH — the same location already used by the
   existing REST API layer (atlas/core/infrastructure/api/*/dependencies.py)
   for Decision, DecisionContext, Observation, Hypothesis, and Evidence.
   Itself already neutral and portable: computed from the ATLAS_HOME
   environment variable (defaulting to the current working directory),
   not a literal machine-specific path.
"""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from atlas.config import DATABASE_PATH


def resolve_database_path(explicit_path: str | Path | None = None) -> Path:
    """Resolve the persistent Atlas core database path, creating its
    parent directory if it doesn't exist yet.
    """
    if explicit_path is not None:
        path = Path(explicit_path)
    else:
        override = os.environ.get("ATLAS_CORE_DB_PATH")
        path = Path(override) if override else DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def create_database_engine(explicit_path: str | Path | None = None) -> Engine:
    """Build a SQLAlchemy engine for the resolved database path."""
    path = resolve_database_path(explicit_path)
    return create_engine(f"sqlite:///{path}", future=True)
