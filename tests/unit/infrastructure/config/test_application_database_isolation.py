"""The running application must open the database it was told to open.

`resolve_database_path` has always taken an explicit argument, then
`ATLAS_CORE_DB_PATH`, then the project default, and every CLI and
`atlas/dev` command has always gone through it. The backend did not. Its
one engine read `atlas.config.DATABASE_PATH` directly, so the override was
honoured everywhere except in the application itself -- the single place
where an operator points a test instance away from live data.

That is not a theoretical gap. A product audit copied the live database,
started the backend with `ATLAS_CORE_DB_PATH` pointing at the copy,
confirmed the variable was set inside the process, and browsed the app.
`lsof` later showed the backend holding `database/atlas.db` open the whole
time. One Alpha Vantage call, one new business record and twenty-two
snapshot rows were written to live data that was supposed to be untouched.
The variable was not partly effective; it was inert, and nothing said so.

The engine here is the only one the backend builds -- every repository in
`atlas.core` and `atlas.alpha` resolves through `get_decision_engine`, and
so does every `BackgroundTasks` job they hand work to -- so this one
function decides where the whole application reads and writes. These tests
pin that, and the guard below keeps a future leaf module from quietly
reintroducing its own default underneath it.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from atlas.core.infrastructure.api.decision import dependencies
from atlas.core.infrastructure.config.database import resolve_database_path


@pytest.fixture(autouse=True)
def _fresh_engine():
    """`get_decision_engine` is `@lru_cache`'d for the process lifetime, which
    is right in production and would otherwise make these tests observe each
    other's engines."""
    dependencies.get_decision_engine.cache_clear()
    yield
    dependencies.get_decision_engine.cache_clear()


def test_the_application_opens_the_database_the_override_names(monkeypatch, tmp_path):
    """The behaviour whose absence cost live data."""
    isolated = tmp_path / "isolated.db"
    monkeypatch.setenv("ATLAS_CORE_DB_PATH", str(isolated))

    assert Path(dependencies.get_decision_engine().url.database) == isolated


def test_the_application_never_opens_the_project_database_under_an_override(monkeypatch, tmp_path):
    """Stated as its own test because "opens the copy" and "does not open
    live" are different claims, and only the second one is the safety
    property. The audit satisfied the first in configuration and failed the
    second in reality."""
    from atlas.config import DATABASE_PATH

    monkeypatch.setenv("ATLAS_CORE_DB_PATH", str(tmp_path / "isolated.db"))
    opened = Path(dependencies.get_decision_engine().url.database)

    assert opened == tmp_path / "isolated.db"
    assert opened != DATABASE_PATH


def test_without_an_override_the_application_still_opens_the_project_database(monkeypatch):
    """The fix must not quietly relocate normal startup."""
    monkeypatch.delenv("ATLAS_CORE_DB_PATH", raising=False)

    assert Path(dependencies.get_decision_engine().url.database) == resolve_database_path()


def test_the_engine_is_still_one_per_process(monkeypatch, tmp_path):
    """The pool sizing that fixed a wave of `QueuePool limit` 500s depends on
    there being exactly one engine, not one per request."""
    monkeypatch.setenv("ATLAS_CORE_DB_PATH", str(tmp_path / "isolated.db"))

    assert dependencies.get_decision_engine() is dependencies.get_decision_engine()


def test_the_connection_pool_is_still_sized_for_a_real_page_load(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_CORE_DB_PATH", str(tmp_path / "isolated.db"))
    pool = dependencies.get_decision_engine().pool

    assert pool.size() == 10
    assert pool._max_overflow == 20


# --- The guard that keeps the resolver authoritative -------------------


def test_the_application_engine_does_not_read_the_default_path_directly():
    """The exact shape of the original defect: a module below the
    configuration layer importing `DATABASE_PATH` and building its own
    engine from it. Everything the backend serves hangs off this one
    factory, so reintroducing that here silently re-breaks every override at
    once -- which is why it is pinned by name rather than left to review.
    """
    source = inspect.getsource(dependencies)
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }

    assert "DATABASE_PATH" not in imported, (
        "atlas.core.infrastructure.api.decision.dependencies imports DATABASE_PATH "
        "again. The application's only engine must resolve its path through "
        "resolve_database_path, or ATLAS_CORE_DB_PATH stops isolating the app."
    )
    assert "resolve_database_path" in imported
