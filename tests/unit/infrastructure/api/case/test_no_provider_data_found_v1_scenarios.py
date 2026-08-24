"""`noProviderDataFound` on `GET /cases/{case_id}/analysis` (Import
Robustness, Internal Alpha Stabilization 1) -- end to end through the
real HTTP surface, following the exact fixture/helper pattern
`test_price_freshness_v1_scenarios.py` already established.

Writes real resolution outcomes directly against the same test engine
the app itself reads from (`get_decision_engine` override), via the
real `CanonicalSecurityIdentityGate` -- never a fake/stub of the gate
itself, since the whole point of this field is that it reflects a real,
persisted resolution outcome. Built via
`canonical_security_gate.factory.build_identity_gate`, the one
sanctioned integration point -- this file (outside the
`canonical_security`/`canonical_security_resolution`/
`canonical_security_gate` packages and their own test directories)
must never import those two shadow-mode packages directly, per
`test_integration_safety.py`'s own guard in each of them.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.canonical_security_gate.factory import build_identity_gate
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.decision.table import create_decision_table

_NOW = datetime(2026, 8, 24, 12, tzinfo=timezone.utc)


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(engine)
    app = create_app()
    app.dependency_overrides[get_decision_engine] = lambda: engine
    test_client = TestClient(app)
    test_client.engine = engine  # type: ignore[attr-defined]
    return test_client


def _import_holding(client, ticker: str, weight_percent: float = 100.0) -> str:
    response = client.post(
        "/alpha-portfolio/import",
        json={"holdings": [{"ticker": ticker, "weightPercent": weight_percent}]},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    case_id = next(h["caseId"] for h in body["holdings"] if h["ticker"] == ticker)
    assert case_id is not None
    return case_id


def _gate(engine) -> CanonicalSecurityIdentityGate:
    return build_identity_gate(engine)


def _profile_document(*, ticker: str, **metadata) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=f"{ticker}:profile",
        company=ticker,
        source_kind="company_profile",
        published_at=_NOW,
        provider_id="alpha_vantage",
        raw_reference="https://example.test/overview",
        content_hash=f"hash-profile-{ticker}",
        language="en",
        metadata=metadata,
    )


def _persist_company_profile(client, ticker: str) -> None:
    engine = client.engine
    create_business_record_table(engine)
    repository = SqlAlchemyBusinessRecordRepository(engine)
    document = _profile_document(
        ticker=ticker, name=f"{ticker} Inc.", exchange="NASDAQ", country="USA", currency="USD", security_type="COMMON_STOCK",
    )
    result = ingest(document, evaluated_at=_NOW)
    assert isinstance(result, IngestedRecord), result
    repository.add(result.record)


class TestNoProviderDataFound:
    def test_true_after_a_real_persisted_no_match_and_no_business_data(self, client):
        case_id = _import_holding(client, "BTC")
        _gate(client.engine).evaluate(ticker="BTC", documents=(), clock=lambda: _NOW)

        body = client.get(f"/cases/{case_id}/analysis").json()

        assert body["noProviderDataFound"] is True
        assert body["companyProfile"] is None
        assert body["marketSnapshot"] is None

    def test_false_when_no_resolution_attempt_has_ever_been_made(self, client):
        """A brand-new ticker Atlas simply hasn't looked at yet must not
        be conflated with one that was looked at and found nothing --
        the ordinary, unmodified insufficient-evidence framing applies."""
        case_id = _import_holding(client, "NEWCO")

        body = client.get(f"/cases/{case_id}/analysis").json()

        assert body["noProviderDataFound"] is False

    def test_false_when_a_resolution_attempt_found_candidates_but_needed_confirmation(self, client):
        """MANUAL_CONFIRMATION means real candidates were found -- a
        meaningfully different fact from NO_MATCH, must never be
        conflated with it."""
        case_id = _import_holding(client, "MANUALCO")
        doc = _profile_document(ticker="MANUALCO", name="Manual Co", exchange="NASDAQ", country="USA", currency="USD")
        _gate(client.engine).evaluate(ticker="MANUALCO", documents=(doc,), clock=lambda: _NOW)

        body = client.get(f"/cases/{case_id}/analysis").json()

        assert body["noProviderDataFound"] is False

    def test_false_for_an_ordinary_fully_enriched_case_unchanged_behavior(self, client):
        """A normal, fully enriched case (company profile present)
        behaves exactly as before this sprint -- this field is never
        True when real data exists, regardless of resolution history."""
        case_id = _import_holding(client, "MSFT")
        _persist_company_profile(client, "MSFT")

        body = client.get(f"/cases/{case_id}/analysis").json()

        assert body["noProviderDataFound"] is False
        assert body["companyProfile"] is not None

    def test_becomes_false_again_after_a_later_successful_resolution(self, client):
        """Reflects only the most recent attempt -- a ticker that first
        came back NO_MATCH but later resolves successfully (e.g. a
        provider outage clears, or a typo gets corrected via a fresh
        import) must stop being reported as no-provider-data."""
        case_id = _import_holding(client, "RETRY")
        gate = _gate(client.engine)
        gate.evaluate(ticker="RETRY", documents=(), clock=lambda: _NOW)
        first = client.get(f"/cases/{case_id}/analysis").json()
        assert first["noProviderDataFound"] is True

        doc = _profile_document(
            ticker="RETRY", name="Retry Inc.", exchange="NASDAQ", country="USA", currency="USD", security_type="COMMON_STOCK",
        )
        later = datetime(2026, 8, 25, tzinfo=timezone.utc)
        gate.evaluate(ticker="RETRY", documents=(doc,), clock=lambda: later)

        second = client.get(f"/cases/{case_id}/analysis").json()
        assert second["noProviderDataFound"] is False
