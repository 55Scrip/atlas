"""End-to-end API tests for the Investment Case Engine v1 slice.

Exercises the real HTTP layer (Watchlist, Portfolio, Investment Case
analysis) against one shared in-memory engine, with the real provider
dependency overridden by a fake -- proves the full product loop this
sprint's Definition of Done requires: add a company -> Case resolved ->
automatic enrichment -> Investment Case API exposes real company data
-> moving Watchlist -> Portfolio keeps the same knowledge.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.api.dependencies import get_default_business_data_providers
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.decision.table import create_decision_table

_NOW = datetime(2026, 8, 9, tzinfo=timezone.utc)


class _FakeProvider:
    """A `BusinessDataProvider` returning canned documents for whatever
    ticker is requested -- no network call anywhere in this test file."""

    def __init__(self) -> None:
        self.call_count: list[str] = []

    def fetch(self, *, company_identifier: str, evaluated_at) -> tuple[RawBusinessDocument, ...]:
        self.call_count.append(company_identifier)
        return (
            RawBusinessDocument(
                identifier=f"{company_identifier}:profile",
                company=company_identifier,
                source_kind="company_profile",
                published_at=evaluated_at,
                provider_id="fake",
                raw_reference="https://example.test/profile",
                content_hash="profile-hash",
                language="en",
                metadata={"name": "Meta Platforms, Inc.", "sector": "Communication Services"},
            ),
            RawBusinessDocument(
                identifier=f"{company_identifier}:FY:2025",
                company=company_identifier,
                source_kind="financial_statement",
                published_at=evaluated_at,
                provider_id="fake",
                raw_reference="https://example.test/fs",
                content_hash="fs-hash",
                language="en",
                metadata={"revenue": 5000.0, "free_cash_flow": 1200.0},
            ),
        )


@pytest.fixture
def provider() -> _FakeProvider:
    return _FakeProvider()


@pytest.fixture
def client(provider):
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_decision_table(engine)
    app = create_app()
    app.dependency_overrides[get_decision_engine] = lambda: engine
    app.dependency_overrides[get_default_business_data_providers] = lambda: (provider,)
    return TestClient(app)


class TestAddToWatchlistCreatesCaseAndEnriches:
    def test_adding_a_ticker_returns_a_real_case_id(self, client):
        response = client.post("/alpha-watchlist", json={"ticker": "META"})
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["ticker"] == "META"
        assert body["caseId"]

    def test_the_investment_case_api_exposes_the_enriched_company_data(self, client):
        entry = client.post("/alpha-watchlist", json={"ticker": "META"}).json()
        analysis = client.get(f"/cases/{entry['caseId']}/analysis")
        assert analysis.status_code == 200, analysis.text
        body = analysis.json()
        assert body["companyProfile"] is not None
        assert body["companyProfile"]["name"] == "Meta Platforms, Inc."
        assert body["companyProfile"]["sector"] == "Communication Services"
        assert len(body["financialHistory"]) == 1
        assert body["financialHistory"][0]["revenue"] == 5000.0

    def test_repeated_addition_is_idempotent_and_never_re_enriches(self, client, provider):
        first = client.post("/alpha-watchlist", json={"ticker": "META"}).json()
        second = client.post("/alpha-watchlist", json={"ticker": "META"}).json()
        assert first["caseId"] == second["caseId"]
        assert provider.call_count == ["META"]

    def test_list_watchlist_shows_the_added_entry(self, client):
        client.post("/alpha-watchlist", json={"ticker": "META"})
        listing = client.get("/alpha-watchlist")
        assert listing.status_code == 200
        assert [e["ticker"] for e in listing.json()] == ["META"]

    def test_blank_ticker_is_rejected_with_400(self, client):
        response = client.post("/alpha-watchlist", json={"ticker": "   "})
        assert response.status_code == 400


class TestWatchlistToPortfolioPreservesKnowledge:
    """The Definition of Done's exact final scenario: META added to
    Watchlist, then later added to Portfolio -- no new Case, no
    rebuilt company knowledge."""

    def test_moving_to_portfolio_reuses_the_same_case_and_keeps_the_data(self, client, provider):
        watchlist_entry = client.post("/alpha-watchlist", json={"ticker": "META"}).json()
        watchlist_case_id = watchlist_entry["caseId"]

        import_response = client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "META", "weightPercent": 20.0}]},
        )
        assert import_response.status_code == 201, import_response.text
        holding = import_response.json()["holdings"][0]

        # Same Case, no new one created.
        assert holding["caseId"] == watchlist_case_id
        # No second round of enrichment for the same ticker.
        assert provider.call_count == ["META"]

        analysis = client.get(f"/cases/{watchlist_case_id}/analysis").json()
        assert analysis["companyProfile"]["name"] == "Meta Platforms, Inc."
        assert analysis["holdingContext"]["held"] is True
        assert analysis["holdingContext"]["ticker"] == "META"
