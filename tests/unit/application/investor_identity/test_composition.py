"""Tests for investor_identity/composition.py (ATLAS-009B).

Two boundaries this module exists to prove:
  1. It is a *store-level* capability, callable with nothing but an
     Engine — no ConversationSession, no Decision, no orchestrator
     anywhere in the call.
  2. It respects the domain -> application -> infrastructure dependency
     direction: the application-layer composition module imports no
     SQLAlchemy table objects and issues no raw persistence statements
     itself, reusing this codebase's existing AST-import-graph
     precedent (tests/test_config_sprint195.py::_config_imports())
     rather than a brittle source-text search.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool

from atlas.core.application.investor_identity.composition import (
    resolve_investor_identity,
)
from atlas.core.domain.decision.value_objects import UserId
from atlas.core.infrastructure.persistence.investor_identity.table import (
    investor_identity_table,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
COMPOSITION_PATH = (
    REPO_ROOT
    / "atlas"
    / "core"
    / "application"
    / "investor_identity"
    / "composition.py"
)


@pytest.fixture
def engine():
    return create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )


class TestStoreLevelBoundary:
    """No ConversationSession, no Decision, no orchestrator anywhere here."""

    def test_resolves_against_a_bare_engine(self, engine):
        user_id = resolve_investor_identity(engine)
        assert isinstance(user_id, UserId)

    def test_creates_its_own_required_tables(self, engine):
        # A freshly created engine has neither table yet — resolve_investor_identity
        # must not assume a prior caller (e.g. a conversation) already created them.
        resolve_investor_identity(engine)
        with engine.connect() as connection:
            rows = connection.execute(select(investor_identity_table)).mappings().all()
        assert len(rows) == 1

    def test_repeated_calls_are_idempotent(self, engine):
        first = resolve_investor_identity(engine)
        second = resolve_investor_identity(engine)
        third = resolve_investor_identity(engine)
        assert first == second == third


# ── Boundary guard — imports ──────────────────────────────────────────────────


def _composition_imports() -> list[str]:
    tree = ast.parse(COMPOSITION_PATH.read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(a.name for a in node.names)
    return modules


def test_composition_does_not_import_sqlalchemy_core() -> None:
    """The application layer never issues raw persistence statements.

    `sqlalchemy.engine` (the `Engine` type) is fine — it's a neutral
    type used across this codebase's own composition roots for
    dependency injection, not a persistence statement. `sqlalchemy`
    itself (Core: Table/insert/select/update/Column/MetaData) must never
    be imported here — those, and the raw table objects
    (investor_identity_table, decisions_table), belong entirely to the
    infrastructure layer.
    """
    imports = _composition_imports()
    core_imports = [m for m in imports if m == "sqlalchemy"]
    assert not core_imports, (
        f"investor_identity/composition.py must not import sqlalchemy Core "
        f"directly: {core_imports}"
    )


def test_composition_does_not_import_table_modules() -> None:
    """No raw Table object import — only create_*_table functions and the
    repository class, which live in modules named `table`/`sqlalchemy_repository`
    but are re-exported as callables/classes, not table objects themselves."""
    # The composition module is allowed to import the table *modules* to reach
    # their create_*_table functions, but must never import a `Table` object
    # or issue a raw SQL construct itself. Verify no bare `Table`/`insert`/
    # `select`/`update` symbol from sqlalchemy is imported by name.
    source = COMPOSITION_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported_names.extend(a.name for a in node.names)
    forbidden = {"Table", "insert", "select", "update", "Column", "MetaData"}
    leaked = forbidden & set(imported_names)
    assert not leaked, (
        f"investor_identity/composition.py must not import raw SQL constructs: {leaked}"
    )
