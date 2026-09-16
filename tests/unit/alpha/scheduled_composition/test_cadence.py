"""The cadence is configuration, so its failure modes are configuration
failure modes: a typo in an environment variable must not stop Atlas, and
must never be read as "run continuously".
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from atlas.alpha.scheduled_composition.cadence import (
    DEFAULT_INTERVAL_SECONDS,
    INTERVAL_ENV_VAR,
    configured_interval,
    is_due,
)

_NOW = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)


def test_the_default_cadence_is_daily() -> None:
    """Daily matches the fastest thing that can actually move a conclusion;
    see `cadence.py` for why hourly and weekly were both rejected."""
    assert DEFAULT_INTERVAL_SECONDS == 24 * 60 * 60


def test_the_interval_is_configurable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(INTERVAL_ENV_VAR, "3600")
    assert configured_interval() == timedelta(hours=1)


def test_an_unset_interval_is_the_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(INTERVAL_ENV_VAR, raising=False)
    assert configured_interval() == timedelta(seconds=DEFAULT_INTERVAL_SECONDS)


@pytest.mark.parametrize("value", ["", "   ", "abc", "1.5", "not-a-number"])
def test_a_malformed_interval_falls_back_rather_than_raising(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv(INTERVAL_ENV_VAR, value)
    assert configured_interval() == timedelta(seconds=DEFAULT_INTERVAL_SECONDS)


@pytest.mark.parametrize("value", ["0", "-1", "-86400"])
def test_a_non_positive_interval_is_refused(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    """Zero would mean "continuously", which is never a cadence anyone
    intends and would compose the whole scope in a loop."""
    monkeypatch.setenv(INTERVAL_ENV_VAR, value)
    assert configured_interval() == timedelta(seconds=DEFAULT_INTERVAL_SECONDS)


def test_never_having_run_is_due() -> None:
    assert is_due(None, _NOW) is True


def test_a_batch_is_not_due_before_the_interval_elapses() -> None:
    assert is_due(_NOW - timedelta(hours=23), _NOW) is False


def test_a_batch_is_due_once_the_interval_has_elapsed() -> None:
    assert is_due(_NOW - timedelta(hours=24), _NOW) is True
    assert is_due(_NOW - timedelta(days=3), _NOW) is True


def test_an_explicit_interval_overrides_the_configured_one(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(INTERVAL_ENV_VAR, "86400")
    assert is_due(_NOW - timedelta(minutes=5), _NOW, timedelta(minutes=1)) is True


def test_cadence_reads_no_database_and_stores_nothing() -> None:
    """Scheduling introduces no table and no state to keep in sync: the
    caller owns when it last ran, and this is a function of two clocks."""
    import inspect

    from atlas.alpha.scheduled_composition import cadence

    source = inspect.getsource(cadence)
    for forbidden in ("engine", "sqlalchemy", "session", "select(", "insert("):
        assert forbidden not in source
