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
    ticker is requested -- no network call anywhere in this test file.

    Sprint O: the company-profile document now comes from
    `fetch_company_profile` (the identity-supplying capability, with
    the additional exchange/country/currency/security_type fields the
    Identity Gate's candidate mapper reads) rather than the main
    `fetch()` -- `metadata["name"]`/`metadata["sector"]` are unchanged,
    since the API surfaces those directly. `call_count` still tracks
    only `.fetch()` calls, preserving every existing "no second round
    of enrichment" assertion in this file exactly."""

    def __init__(self) -> None:
        self.call_count: list[str] = []

    def fetch(self, *, company_identifier: str, evaluated_at) -> tuple[RawBusinessDocument, ...]:
        self.call_count.append(company_identifier)
        return (
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

    def fetch_company_profile(self, *, company_identifier: str, evaluated_at) -> tuple[RawBusinessDocument, ...]:
        return (
            RawBusinessDocument(
                identifier=f"{company_identifier}:profile",
                company=company_identifier,
                source_kind="company_profile",
                published_at=evaluated_at,
                provider_id="alpha_vantage",
                raw_reference="https://example.test/profile",
                content_hash="profile-hash",
                language="en",
                metadata={
                    "name": "Meta Platforms, Inc.",
                    "sector": "Communication Services",
                    "exchange": "NASDAQ",
                    "country": "USA",
                    "currency": "USD",
                    "security_type": "COMMON_STOCK",
                },
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


class TestRemoveFromWatchlist:
    def test_removing_an_existing_entry_returns_204(self, client):
        client.post("/alpha-watchlist", json={"ticker": "META"})
        response = client.delete("/alpha-watchlist/META")
        assert response.status_code == 204

    def test_removed_entry_no_longer_appears_in_list(self, client):
        client.post("/alpha-watchlist", json={"ticker": "META"})
        client.delete("/alpha-watchlist/META")
        listing = client.get("/alpha-watchlist")
        assert [e["ticker"] for e in listing.json()] == []

    def test_other_entries_remain_unchanged_after_removal(self, client):
        client.post("/alpha-watchlist", json={"ticker": "META"})
        client.post("/alpha-watchlist", json={"ticker": "NVDA"})
        client.delete("/alpha-watchlist/META")
        listing = client.get("/alpha-watchlist")
        assert [e["ticker"] for e in listing.json()] == ["NVDA"]

    def test_the_case_entity_itself_remains_intact_after_removal(self, client):
        entry = client.post("/alpha-watchlist", json={"ticker": "META"}).json()
        client.delete("/alpha-watchlist/META")
        case_response = client.get(f"/cases/{entry['caseId']}")
        assert case_response.status_code == 200, case_response.text
        assert case_response.json()["caseId"] == entry["caseId"]

    def test_company_profile_display_remains_available_after_removal(self, client):
        """Ticker -> Existing Case Resolution Sprint: previously,
        `InvestmentCaseCompositionService._assemble`'s
        `watchlist_store.get_by_case_id(case_id)` ticker-recovery
        fallback (see `atlas/alpha/investment_case/service.py`) went
        blind the moment the Watchlist row was deleted, so
        `companyProfile` disappeared from `/cases/{id}/analysis` even
        though the underlying `BusinessRecord`s were untouched. Removal
        is now a soft delete (`AlphaWatchlistStore.remove`), so
        `get_by_case_id` keeps finding the ticker and `companyProfile`
        stays visible across removal, with no re-add required."""
        entry = client.post("/alpha-watchlist", json={"ticker": "META"}).json()
        analysis_before = client.get(f"/cases/{entry['caseId']}/analysis").json()
        assert analysis_before["companyProfile"]["name"] == "Meta Platforms, Inc."

        client.delete("/alpha-watchlist/META")
        analysis_after = client.get(f"/cases/{entry['caseId']}/analysis")
        assert analysis_after.status_code == 200, analysis_after.text
        assert analysis_after.json()["companyProfile"]["name"] == "Meta Platforms, Inc."

    def test_the_portfolio_holding_is_untouched_when_the_same_ticker_is_removed_from_watchlist(
        self, client
    ):
        watchlist_entry = client.post("/alpha-watchlist", json={"ticker": "META"}).json()
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "META", "weightPercent": 20.0}]},
        )
        client.delete("/alpha-watchlist/META")

        portfolio = client.get("/alpha-portfolio").json()
        holding = next(h for h in portfolio["holdings"] if h["ticker"] == "META")
        assert holding["caseId"] == watchlist_entry["caseId"]

        analysis = client.get(f"/cases/{watchlist_entry['caseId']}/analysis").json()
        assert analysis["holdingContext"]["held"] is True

    def test_removing_a_ticker_not_on_the_watchlist_returns_404(self, client):
        response = client.delete("/alpha-watchlist/NOPE")
        assert response.status_code == 404

    def test_existing_add_and_list_behavior_is_unaffected(self, client):
        first = client.post("/alpha-watchlist", json={"ticker": "META"}).json()
        second = client.post("/alpha-watchlist", json={"ticker": "META"}).json()
        assert first["caseId"] == second["caseId"]
        assert [e["ticker"] for e in client.get("/alpha-watchlist").json()] == ["META"]

    def test_add_remove_add_again_relists_the_ticker(self, client):
        client.post("/alpha-watchlist", json={"ticker": "META"})
        client.delete("/alpha-watchlist/META")
        readded = client.post("/alpha-watchlist", json={"ticker": "META"})
        assert readded.status_code == 201, readded.text
        assert [e["ticker"] for e in client.get("/alpha-watchlist").json()] == ["META"]

    def test_re_adding_a_watchlist_only_ticker_reuses_the_same_case(self, client):
        """Ticker -> Existing Case Resolution Sprint: previously,
        `CaseGenerationService.ensure_case_id` only reused a Case via a
        current Portfolio-holding cross-reference, so a ticker that was
        only ever on the Watchlist got a brand-new Case on re-add,
        orphaning its original one. `add_ticker` now resolves via
        `case_membership.resolve_case_id_for_ticker` first, which also
        checks this exact ticker's own prior (since-removed) Watchlist
        entry -- so re-add restores the original `case_id`, not a new
        one."""
        first = client.post("/alpha-watchlist", json={"ticker": "META"}).json()
        client.delete("/alpha-watchlist/META")
        second = client.post("/alpha-watchlist", json={"ticker": "META"}).json()
        assert second["caseId"] == first["caseId"]

    def test_decision_history_remains_linked_after_remove_and_re_add(self, client):
        entry = client.post("/alpha-watchlist", json={"ticker": "META"}).json()
        case_id = entry["caseId"]
        decision = client.post(
            "/decisions",
            json={
                "caseId": case_id,
                "userId": "00000000-0000-0000-0000-000000000001",
                "decisionType": "HOLD",
                "subject": "META",
                "reason": "Steady compounder.",
                "confidence": 70,
            },
        )
        assert decision.status_code == 201, decision.text

        client.delete("/alpha-watchlist/META")
        readded = client.post("/alpha-watchlist", json={"ticker": "META"}).json()
        assert readded["caseId"] == case_id

        analysis = client.get(f"/cases/{case_id}/analysis").json()
        assert any(d["decisionId"] == decision.json()["id"] for d in analysis["decisionHistory"])


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
