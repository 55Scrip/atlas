"""Opening an Investment Case must not mean joining the Watchlist.

Before Sprint 4A a Case had no instrument of its own, so Discovery
could only reach an analysable Case by adding the company to the
Watchlist first -- conflating "I want to look at this" with "monitor
this for me". These tests pin the replacement.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.api.dependencies import get_default_business_data_providers
from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.decision.table import create_decision_table
from tests.unit.infrastructure.api.alpha_watchlist.test_router import _FakeProvider


@pytest.fixture
def provider():
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


def ensure(client, ticker: str):
    return client.post("/case-identity/ensure", json={"ticker": ticker})


class TestEnsureCase:
    def test_it_returns_a_case_bound_to_the_ticker(self, client):
        response = ensure(client, "ASML")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["ticker"] == "ASML"
        assert body["caseId"]

    def test_repeated_ensure_reuses_the_same_case(self, client):
        first = ensure(client, "ASML").json()["caseId"]
        second = ensure(client, "ASML").json()["caseId"]
        assert first == second

    def test_it_creates_no_watchlist_membership(self, client):
        ensure(client, "ASML")
        assert client.get("/alpha-watchlist").json() == []

    def test_it_creates_no_portfolio_holding(self, client):
        ensure(client, "ASML")
        cockpit = client.get("/alpha-portfolio/cockpit").json()
        assert cockpit["holdings"] == []

    def test_it_records_no_decision(self, client):
        case_id = ensure(client, "ASML").json()["caseId"]
        memory = client.get(f"/decision-memory/{case_id}")
        # Either no memory resource at all, or one with no decisions --
        # never a fabricated decision event from merely opening a Case.
        if memory.status_code == 200:
            assert not memory.json().get("decisions")

    def test_the_case_it_returns_is_a_real_analysable_case(self, client):
        case_id = ensure(client, "ASML").json()["caseId"]
        analysis = client.get(f"/cases/{case_id}/analysis")
        assert analysis.status_code == 200, analysis.text

    def test_a_watchlisted_ticker_reuses_its_existing_case(self, client):
        added = client.post("/alpha-watchlist", json={"ticker": "META"}).json()
        assert ensure(client, "META").json()["caseId"] == added["caseId"]

    def test_watchlist_membership_is_unchanged_by_ensuring(self, client):
        client.post("/alpha-watchlist", json={"ticker": "META"})
        before = client.get("/alpha-watchlist").json()
        ensure(client, "META")
        assert client.get("/alpha-watchlist").json() == before

    def test_a_blank_ticker_is_refused(self, client):
        assert ensure(client, "   ").status_code == 400

    def test_the_ticker_is_upper_cased_but_not_otherwise_normalized(self, client):
        assert ensure(client, "  asml ").json()["ticker"] == "ASML"

    def test_su_pa_and_su_get_distinct_cases(self, client):
        """Both are in the real database and are unrelated companies:
        Schneider Electric on Euronext Paris, and Suncor Energy on the
        NYSE. No normalization here may collapse them."""
        assert ensure(client, "SU.PA").json()["caseId"] != ensure(client, "SU").json()["caseId"]

    def test_share_classes_get_distinct_cases(self, client):
        assert ensure(client, "GOOG").json()["caseId"] != ensure(client, "GOOGL").json()["caseId"]


class TestDiscoveryCandidates:
    def test_an_empty_atlas_surfaces_no_candidates(self, client):
        assert client.get("/discovery-candidates").json() == []

    def test_a_portfolio_holding_is_never_a_new_idea(self, client):
        client.post("/alpha-portfolio/import", json={"holdings": [{"ticker": "META", "weightPercent": 100.0}]})
        tickers = [c["ticker"] for c in client.get("/discovery-candidates").json()]
        assert "META" not in tickers

    def test_an_actively_watched_prospect_is_never_a_new_idea(self, client):
        client.post("/alpha-watchlist", json={"ticker": "META"})
        tickers = [c["ticker"] for c in client.get("/discovery-candidates").json()]
        assert "META" not in tickers

    def test_a_bound_case_the_investor_does_not_follow_is_a_candidate(self, client):
        client.post("/alpha-watchlist", json={"ticker": "META"})
        client.delete("/alpha-watchlist/META")
        tickers = [c["ticker"] for c in client.get("/discovery-candidates").json()]
        # Removal ended the monitoring relationship; Atlas may
        # legitimately surface the company again as an idea.
        assert "META" in tickers

    def test_candidates_carry_canonical_enum_values_never_rendered_text(self, client):
        client.post("/alpha-watchlist", json={"ticker": "META"})
        client.delete("/alpha-watchlist/META")
        [candidate] = client.get("/discovery-candidates").json()
        from atlas.alpha.decision_support import DecisionSupportLevel
        from atlas.analysis_engine.analysis_coverage import AnalysisCoverageLevel

        assert candidate["decisionSupportLevel"] in {level.value for level in DecisionSupportLevel}
        assert candidate["analysisCoverageLevel"] in {level.value for level in AnalysisCoverageLevel}

    def test_candidates_carry_no_invented_investment_metric(self, client):
        client.post("/alpha-watchlist", json={"ticker": "META"})
        client.delete("/alpha-watchlist/META")
        [candidate] = client.get("/discovery-candidates").json()
        for invented in ("conviction", "expectedReturn", "upside", "downside", "score", "risk"):
            assert invented not in candidate

    def test_rendering_candidates_calls_no_provider(self, client, provider):
        client.post("/alpha-watchlist", json={"ticker": "META"})
        client.delete("/alpha-watchlist/META")
        after_add = list(provider.call_count)
        for _ in range(3):
            assert client.get("/discovery-candidates").status_code == 200
        assert provider.call_count == after_add

    def test_rendering_candidates_creates_no_case(self, client):
        """Opening Discovery is a read. Cases for analysed securities
        are adopted deliberately, by an operator."""
        client.post("/alpha-watchlist", json={"ticker": "META"})
        client.delete("/alpha-watchlist/META")
        before = client.get("/discovery-candidates").json()
        for _ in range(3):
            client.get("/discovery-candidates")
        assert client.get("/discovery-candidates").json() == before
