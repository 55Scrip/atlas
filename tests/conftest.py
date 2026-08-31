"""Global test isolation guarantees (Calibration Phase 8).

This file exists because of a real incident, not as a precaution. Until
Phase 8, `tests/` had **no `conftest.py` at all**: several API tests build
`create_app()` with the *real* default `BusinessDataProvider` tuple and
the *real* `database/atlas.db`. Those tests were silently inert only
because `ALPHA_VANTAGE_API_KEY` was unreadable -- with no key, the
Alpha Vantage profile leg raised `MissingRequiredField`,
`CanonicalSecurityIdentityGate` returned `NO_MATCH`, and
`refresh_company_data` short-circuited before fetching anything. An
unloadable `.env` was acting as an undocumented safety net.

The moment `atlas.config.load_local_env` made that key readable, a
single full-suite run performed genuine live enrichment: 48 real Alpha
Vantage calls (the free tier allows 25/day) and 161 real
`BusinessRecord`s written into the development database, alongside
synthetic fixture tickers (`ZZZZ`, `ODD TICKER`).

Three permanent engineering guarantees are established here, in order
of how they are enforced:

1. **Unit tests cannot modify the development database.** `ATLAS_HOME`
   and `ATLAS_CORE_DB_PATH` -- both already-existing overrides, no new
   configuration concept -- are redirected to a per-run temporary
   directory *before* `atlas.config` is ever imported, because
   `atlas.config.BASE_DIR` (and therefore `DATABASE_PATH`) is resolved
   at import time. Redirecting `ATLAS_HOME` also points
   `atlas.config.LOCAL_ENV_PATH` at a directory with no `.env`, so no
   real provider credential is visible to a unit test either.

2. **Unit tests consume zero provider quota.** Outbound TCP is blocked
   at the `socket` layer rather than by patching `httpx`, so it holds
   for every client any provider might use now or later. Loopback is
   still permitted: `TestClient` speaks ASGI in-process and needs no
   socket, but some local fixtures do.

3. **Live-provider verification is an explicit, separate workflow.** A
   test that genuinely needs the network must be marked
   `@pytest.mark.integration`; such tests are *deselected by default*
   and run only with `--run-integration`. Marking a test is therefore a
   deliberate, visible act, never something a test can drift into.

Together these make unit tests deterministic: identical inputs, no
network, no shared mutable database.
"""
from __future__ import annotations

import os
import socket
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Guarantee 1 -- redirect every filesystem/database root BEFORE atlas imports.
# `atlas.config` resolves BASE_DIR at import time, so this must run first and
# must not be moved below any `atlas.*` import.
# ---------------------------------------------------------------------------
_TEST_HOME = Path(tempfile.mkdtemp(prefix="atlas-test-home-"))
(_TEST_HOME / "database").mkdir(parents=True, exist_ok=True)
os.environ["ATLAS_HOME"] = str(_TEST_HOME)
os.environ["ATLAS_CORE_DB_PATH"] = str(_TEST_HOME / "database" / "atlas.db")

import pytest  # noqa: E402  -- deliberately after the env redirection above


#: The real development database. Never a legitimate test target.
_PROTECTED_DB = Path(__file__).resolve().parent.parent / "database" / "atlas.db"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: test performs real outbound network I/O against a live "
        "provider. Deselected unless --run-integration is passed.",
    )


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run tests marked @pytest.mark.integration, which make real "
        "network calls and consume real provider quota.",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-integration"):
        return
    skip = pytest.mark.skip(reason="needs --run-integration (makes real provider calls)")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)


class OutboundNetworkBlocked(RuntimeError):
    """Raised instead of opening a real connection from a unit test."""


_LOOPBACK = frozenset({"127.0.0.1", "::1", "localhost", ""})


def _is_loopback(address: object) -> bool:
    if isinstance(address, (str, bytes, Path)):
        return True  # AF_UNIX path -- local IPC, never a provider call.
    if isinstance(address, tuple) and address:
        return str(address[0]) in _LOOPBACK
    return False


@pytest.fixture(autouse=True)
def _block_outbound_network(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Guarantee 2. Autouse, so a test cannot forget it; opt out only by
    marking the test `integration`."""
    if request.node.get_closest_marker("integration"):
        return

    real_connect = socket.socket.connect
    real_create_connection = socket.create_connection

    def guarded_connect(self, address, *args, **kwargs):  # type: ignore[no-untyped-def]
        if _is_loopback(address):
            return real_connect(self, address, *args, **kwargs)
        raise OutboundNetworkBlocked(
            f"Unit test attempted outbound network I/O to {address!r}. Unit tests "
            "consume zero provider quota by design. Inject a fake fetcher (every "
            "provider in atlas.business_data_providers takes one), or mark the test "
            "@pytest.mark.integration and run with --run-integration."
        )

    def guarded_create_connection(address, *args, **kwargs):  # type: ignore[no-untyped-def]
        if _is_loopback(address):
            return real_create_connection(address, *args, **kwargs)
        raise OutboundNetworkBlocked(
            f"Unit test attempted outbound network I/O to {address!r}. See "
            "tests/conftest.py for the opt-in integration workflow."
        )

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket, "create_connection", guarded_create_connection)


@pytest.fixture(autouse=True)
def _assert_development_database_untouched() -> None:
    """Guarantee 1, verified rather than assumed. A test that resolves the
    real `database/atlas.db` despite the redirection above would otherwise
    fail silently and invisibly; this turns that into a hard error at the
    end of the offending test."""
    before = _PROTECTED_DB.stat().st_mtime_ns if _PROTECTED_DB.exists() else None
    yield
    after = _PROTECTED_DB.stat().st_mtime_ns if _PROTECTED_DB.exists() else None
    if before != after:
        raise AssertionError(
            f"Test modified the development database at {_PROTECTED_DB}. Unit tests "
            "must never read or write it -- see tests/conftest.py."
        )
