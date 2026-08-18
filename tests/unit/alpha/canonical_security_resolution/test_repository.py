"""Resolution shadow persistence repository tests -- Sprint N Phase 9/10/14."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.canonical_security.value_objects import MicCode, TradingCurrency
from atlas.alpha.canonical_security_resolution.candidates import ProviderCandidate
from atlas.alpha.canonical_security_resolution.repository import SqlAlchemyResolutionRepository
from atlas.alpha.canonical_security_resolution.service import CanonicalSecurityResolutionService, ResolutionRequest
from atlas.alpha.canonical_security_resolution.table import create_resolution_tables

_FIXED_CLOCK = lambda: datetime(2026, 8, 18, tzinfo=timezone.utc)  # noqa: E731


def _make_repository() -> SqlAlchemyResolutionRepository:
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_resolution_tables(engine)
    return SqlAlchemyResolutionRepository(engine)


def test_save_persists_every_candidate_not_only_the_winner() -> None:
    repository = _make_repository()
    a = ProviderCandidate(provider_name="SEC_EDGAR", symbol="MC", company_name="Moelis & Company")
    b = ProviderCandidate(provider_name="TWELVE_DATA", symbol="MC", company_name="LVMH")
    result = CanonicalSecurityResolutionService().resolve(
        ResolutionRequest(investor_ticker="MC", candidates=(a, b)), clock=_FIXED_CLOCK
    )
    record_id = repository.save(
        result, investor_ticker="MC", investor_company_text=None, existing_canonical_security_id=None
    )
    loaded = repository.load(record_id)
    assert loaded is not None
    assert loaded.outcome == "AMBIGUOUS"
    assert len(loaded.evidence) == 2
    providers = {item.candidate.provider_name for item in loaded.evidence}
    assert providers == {"SEC_EDGAR", "TWELVE_DATA"}


def test_load_preserves_candidate_order() -> None:
    repository = _make_repository()
    a = ProviderCandidate(provider_name="SEC_EDGAR", symbol="MC")
    b = ProviderCandidate(provider_name="TWELVE_DATA", symbol="MC")
    c = ProviderCandidate(provider_name="ALPHA_VANTAGE", symbol="MC")
    result = CanonicalSecurityResolutionService().resolve(
        ResolutionRequest(investor_ticker="MC", candidates=(a, b, c)), clock=_FIXED_CLOCK
    )
    record_id = repository.save(
        result, investor_ticker="MC", investor_company_text=None, existing_canonical_security_id=None
    )
    loaded = repository.load(record_id)
    assert [item.candidate.provider_name for item in loaded.evidence] == ["SEC_EDGAR", "TWELVE_DATA", "ALPHA_VANTAGE"]


def test_load_returns_none_for_unknown_id() -> None:
    repository = _make_repository()
    assert repository.load("00000000-0000-0000-0000-000000000000") is None


def test_find_latest_resolution_returns_most_recent() -> None:
    repository = _make_repository()
    candidate = ProviderCandidate(
        provider_name="TWELVE_DATA", symbol="AAPL", company_name="Apple Inc.",
        exchange_mic=MicCode("XNGS"), country="United States", currency=TradingCurrency("USD"), security_type="COMMON_STOCK",
    )
    first_clock = lambda: datetime(2026, 1, 1, tzinfo=timezone.utc)  # noqa: E731
    second_clock = lambda: datetime(2026, 6, 1, tzinfo=timezone.utc)  # noqa: E731

    first_result = CanonicalSecurityResolutionService().resolve(
        ResolutionRequest(investor_ticker="AAPL", candidates=(candidate,)), clock=first_clock
    )
    repository.save(first_result, investor_ticker="AAPL", investor_company_text=None, existing_canonical_security_id=None)

    second_result = CanonicalSecurityResolutionService().resolve(
        ResolutionRequest(investor_ticker="AAPL", candidates=(candidate,)), clock=second_clock
    )
    second_id = repository.save(
        second_result, investor_ticker="AAPL", investor_company_text=None, existing_canonical_security_id=None
    )

    latest = repository.find_latest_resolution("AAPL")
    assert latest is not None
    assert latest.id == second_id
    assert latest.resolved_at == datetime(2026, 6, 1, tzinfo=timezone.utc)


def test_find_latest_resolution_returns_none_when_absent() -> None:
    repository = _make_repository()
    assert repository.find_latest_resolution("NONEXISTENT") is None


def test_shadow_persistence_carries_resulting_canonical_security_id() -> None:
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
    loaded = repository.load(record_id)
    assert loaded.resulting_canonical_security_id == str(result.canonical_security.id)
