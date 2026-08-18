"""Resolution Expiration tests -- Sprint N Phase 13."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from atlas.alpha.canonical_security_resolution.expiration import (
    DEFAULT_MAX_AGE,
    age_confidence,
    is_resolution_expired,
    requires_revalidation,
)

_RESOLVED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_not_expired_within_window() -> None:
    now = _RESOLVED_AT + timedelta(days=1)
    assert is_resolution_expired(_RESOLVED_AT, now=now) is False


def test_expired_past_window() -> None:
    now = _RESOLVED_AT + DEFAULT_MAX_AGE + timedelta(days=1)
    assert is_resolution_expired(_RESOLVED_AT, now=now) is True


def test_requires_revalidation_matches_expiration_today() -> None:
    now = _RESOLVED_AT + DEFAULT_MAX_AGE + timedelta(days=1)
    assert requires_revalidation(_RESOLVED_AT, now=now) == is_resolution_expired(_RESOLVED_AT, now=now)


def test_age_confidence_downgrades_high_to_medium_when_expired() -> None:
    now = _RESOLVED_AT + DEFAULT_MAX_AGE + timedelta(days=1)
    assert age_confidence("HIGH", resolved_at=_RESOLVED_AT, now=now) == "MEDIUM"


def test_age_confidence_downgrades_medium_to_low_when_expired() -> None:
    now = _RESOLVED_AT + DEFAULT_MAX_AGE + timedelta(days=1)
    assert age_confidence("MEDIUM", resolved_at=_RESOLVED_AT, now=now) == "LOW"


def test_age_confidence_leaves_low_unchanged() -> None:
    now = _RESOLVED_AT + DEFAULT_MAX_AGE + timedelta(days=1)
    assert age_confidence("LOW", resolved_at=_RESOLVED_AT, now=now) == "LOW"


def test_age_confidence_leaves_rejected_unchanged() -> None:
    now = _RESOLVED_AT + DEFAULT_MAX_AGE + timedelta(days=1)
    assert age_confidence("REJECTED", resolved_at=_RESOLVED_AT, now=now) == "REJECTED"


def test_age_confidence_never_upgrades() -> None:
    now = _RESOLVED_AT + timedelta(days=1)  # not expired
    assert age_confidence("HIGH", resolved_at=_RESOLVED_AT, now=now) == "HIGH"


def test_age_confidence_is_pure_no_side_effects() -> None:
    now = _RESOLVED_AT + DEFAULT_MAX_AGE + timedelta(days=1)
    first = age_confidence("HIGH", resolved_at=_RESOLVED_AT, now=now)
    second = age_confidence("HIGH", resolved_at=_RESOLVED_AT, now=now)
    assert first == second
