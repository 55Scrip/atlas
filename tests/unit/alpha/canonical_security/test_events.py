"""Domain event construction -- Sprint M Phase 8. These events are not
published anywhere yet (see `events.py`'s own docstring); this suite
only proves each shape is constructible and carries the fields Sprint L
Phase 12 specified."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.canonical_security.events import (
    CanonicalSecurityCreated,
    ProviderMappingAdded,
    ProviderMappingVerified,
    ResolutionStatusChanged,
    SecurityMerged,
    SecurityRevoked,
    SecuritySuperseded,
)

_AT = datetime(2026, 8, 18, tzinfo=timezone.utc)


def test_canonical_security_created() -> None:
    event = CanonicalSecurityCreated(
        canonical_security_id="abc", canonical_company_name="LVMH", native_ticker="MC", created_at=_AT
    )
    assert event.canonical_security_id == "abc"
    assert event.created_at == _AT


def test_provider_mapping_added() -> None:
    event = ProviderMappingAdded(
        canonical_security_id="abc",
        provider_name="TWELVE_DATA",
        provider_ticker="MC",
        confidence="HIGH",
        mapped_at=_AT,
    )
    assert event.provider_name == "TWELVE_DATA"


def test_provider_mapping_verified() -> None:
    event = ProviderMappingVerified(
        canonical_security_id="abc",
        provider_name="SEC_EDGAR",
        provider_ticker="MC",
        verification_status="REJECTED",
        verified_at=_AT,
    )
    assert event.verification_status == "REJECTED"


def test_resolution_status_changed() -> None:
    event = ResolutionStatusChanged(
        canonical_security_id="abc", previous_status="CONFIRMED", new_status="CANONICAL", changed_at=_AT
    )
    assert event.previous_status == "CONFIRMED"
    assert event.new_status == "CANONICAL"


def test_security_merged() -> None:
    event = SecurityMerged(
        losing_canonical_security_id="a", winning_canonical_security_id="b", merged_at=_AT, reason="duplicate resolution"
    )
    assert event.losing_canonical_security_id == "a"


def test_security_superseded() -> None:
    event = SecuritySuperseded(
        old_canonical_security_id="a", new_canonical_security_id="b", superseded_at=_AT, reason="ticker_change"
    )
    assert event.reason == "ticker_change"


def test_security_revoked() -> None:
    event = SecurityRevoked(canonical_security_id="abc", revoked_at=_AT, reason="wrong company identified after activation")
    assert event.canonical_security_id == "abc"
