"""Replay Engine tests -- Sprint N Phase 12."""
from __future__ import annotations

from dataclasses import replace as dataclass_replace
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.canonical_security.value_objects import MicCode, TradingCurrency
from atlas.alpha.canonical_security_resolution.candidates import ProviderCandidate
from atlas.alpha.canonical_security_resolution.exceptions import ReplayMismatchError, ReplayVersionMismatchError
from atlas.alpha.canonical_security_resolution.repository import SqlAlchemyResolutionRepository
from atlas.alpha.canonical_security_resolution.replay import replay, verify_replay
from atlas.alpha.canonical_security_resolution.service import CanonicalSecurityResolutionService, ResolutionRequest
from atlas.alpha.canonical_security_resolution.table import create_resolution_tables

_FIXED_CLOCK = lambda: datetime(2026, 8, 18, tzinfo=timezone.utc)  # noqa: E731


def _make_repository() -> SqlAlchemyResolutionRepository:
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_resolution_tables(engine)
    return SqlAlchemyResolutionRepository(engine)


def test_replay_ambiguous_mc_collision_reproduces_identical_outcome() -> None:
    repository = _make_repository()
    a = ProviderCandidate(provider_name="SEC_EDGAR", symbol="MC", company_name="Moelis & Company")
    b = ProviderCandidate(provider_name="TWELVE_DATA", symbol="MC", company_name="LVMH")
    result = CanonicalSecurityResolutionService().resolve(
        ResolutionRequest(investor_ticker="MC", candidates=(a, b)), clock=_FIXED_CLOCK
    )
    record_id = repository.save(
        result, investor_ticker="MC", investor_company_text=None, existing_canonical_security_id=None
    )
    stored = repository.load(record_id)
    verified = verify_replay(stored)
    assert verified.outcome == "AMBIGUOUS"


def test_replay_auto_accept_reproduces_identical_confidence() -> None:
    repository = _make_repository()
    candidate = ProviderCandidate(
        provider_name="TWELVE_DATA", symbol="AAPL", company_name="Apple Inc.",
        exchange_mic=MicCode("XNGS"), country="United States", currency=TradingCurrency("USD"), security_type="COMMON_STOCK",
    )
    result = CanonicalSecurityResolutionService().resolve(
        ResolutionRequest(investor_ticker="AAPL", candidates=(candidate,)), clock=_FIXED_CLOCK
    )
    record_id = repository.save(
        result, investor_ticker="AAPL", investor_company_text=None, existing_canonical_security_id=None
    )
    stored = repository.load(record_id)
    verified = verify_replay(stored)
    assert verified.outcome == "AUTO_ACCEPT"
    assert [item.confidence for item in verified.evidence] == [item.confidence for item in stored.evidence]


def test_replay_rejects_mismatched_algorithm_version() -> None:
    repository = _make_repository()
    candidate = ProviderCandidate(provider_name="SEC_EDGAR", symbol="AAPL")
    result = CanonicalSecurityResolutionService().resolve(
        ResolutionRequest(investor_ticker="AAPL", candidates=(candidate,)), clock=_FIXED_CLOCK
    )
    record_id = repository.save(
        result, investor_ticker="AAPL", investor_company_text=None, existing_canonical_security_id=None
    )
    stored = repository.load(record_id)
    tampered = dataclass_replace(stored, resolution_version="0.0.1")
    with pytest.raises(ReplayVersionMismatchError):
        replay(tampered)


def test_verify_replay_raises_on_genuine_mismatch() -> None:
    """Constructs a StoredResolution whose recorded outcome disagrees
    with what re-running the algorithm actually produces -- proving
    verify_replay actually checks, rather than trusting the stored
    outcome blindly."""
    repository = _make_repository()
    candidate = ProviderCandidate(
        provider_name="TWELVE_DATA", symbol="AAPL", company_name="Apple Inc.",
        exchange_mic=MicCode("XNGS"), country="United States", currency=TradingCurrency("USD"), security_type="COMMON_STOCK",
    )
    result = CanonicalSecurityResolutionService().resolve(
        ResolutionRequest(investor_ticker="AAPL", candidates=(candidate,)), clock=_FIXED_CLOCK
    )
    record_id = repository.save(
        result, investor_ticker="AAPL", investor_company_text=None, existing_canonical_security_id=None
    )
    stored = repository.load(record_id)
    tampered = dataclass_replace(stored, outcome="NO_MATCH")
    with pytest.raises(ReplayMismatchError):
        verify_replay(tampered)
