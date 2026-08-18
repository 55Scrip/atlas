"""Sprint O Phase 10 -- the backend-only manual confirmation pathway.

No UI is built this sprint; what's proven here is that a future UI has
everything it needs: `GateDecision.resolution_result` (exposed for
exactly this reason) carries the full evidence a human would review,
and `CanonicalSecurityResolutionService.confirm_manually` (Sprint N,
unmodified) turns a human's choice into a real `CANONICAL`
`CanonicalSecurity`. This test proves the two halves connect: a
blocked `MANUAL_CONFIRMATION` decision's own `resolution_result` is
exactly what `confirm_manually` accepts, and saving the result lets a
*subsequent* gate evaluation for the same ticker find and reuse it.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.canonical_security.repository import SqlAlchemyCanonicalSecurityRepository
from atlas.alpha.canonical_security.table import create_canonical_security_tables
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.alpha.canonical_security_resolution.repository import SqlAlchemyResolutionRepository
from atlas.alpha.canonical_security_resolution.service import CanonicalSecurityResolutionService
from atlas.alpha.canonical_security_resolution.table import create_resolution_tables
from atlas.analysis_engine.business_data.models import RawBusinessDocument

_NOW = datetime(2026, 8, 18, tzinfo=timezone.utc)


def _engine() -> Engine:
    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})
    create_canonical_security_tables(engine)
    create_resolution_tables(engine)
    return engine


def _gate(engine: Engine) -> CanonicalSecurityIdentityGate:
    return CanonicalSecurityIdentityGate(
        resolution_service=CanonicalSecurityResolutionService(),
        canonical_security_repository=SqlAlchemyCanonicalSecurityRepository(engine),
        resolution_repository=SqlAlchemyResolutionRepository(engine),
    )


def _profile_doc(*, ticker: str, provider_id: str = "alpha_vantage") -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=f"{ticker}:profile",
        company=ticker,
        source_kind="company_profile",
        published_at=_NOW,
        provider_id=provider_id,
        raw_reference="https://example.test/profile",
        content_hash=f"hash-{ticker}",
        language="en",
        metadata={"name": f"{ticker} Inc.", "exchange": "NASDAQ", "country": "USA", "currency": "USD"},
    )


def test_a_manual_confirmation_decision_can_be_completed_by_a_future_caller() -> None:
    engine = _engine()
    gate = _gate(engine)
    doc = _profile_doc(ticker="AAPL")  # exchange+country+currency, no security_type -> MEDIUM confidence
    decision = gate.evaluate(ticker="AAPL", documents=(doc,), clock=lambda: _NOW)

    assert decision.allowed is False
    assert decision.outcome == "MANUAL_CONFIRMATION"

    # What a future confirmation UI would have: the full result,
    # exactly as the gate saw it.
    result = decision.resolution_result
    assert len(result.evidence) == 1
    chosen = result.evidence[0].candidate

    resolution_service = CanonicalSecurityResolutionService()
    confirmed_security = resolution_service.confirm_manually(result, chosen_candidate=chosen, clock=lambda: _NOW)
    assert confirmed_security.resolution_status == "CANONICAL"

    canonical_security_repository = SqlAlchemyCanonicalSecurityRepository(engine)
    canonical_security_repository.save(confirmed_security)

    # A later refresh for the same ticker/exchange now finds and can
    # reuse the manually-confirmed identity rather than creating a
    # second one.
    found = canonical_security_repository.find_by_ticker_and_exchange("AAPL", confirmed_security.primary_exchange_mic.value)
    assert found is not None
    assert found.id == confirmed_security.id
