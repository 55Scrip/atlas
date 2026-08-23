"""Decision Alternatives & Opportunity Cost -- the real HTTP surface
(`/opportunity-cost/*`), powered by `atlas.alpha.opportunity_cost
.service.OpportunityCostService`. Follows the exact fixture/helper
pattern `test_decision_path_v1_scenarios.py` already established. No
real network access is available in this environment, so a freshly
imported holding genuinely has never been evaluated -- these tests
exercise that real, honest floor state (no competing-Case alternatives
constructible yet) rather than fabricating richer coverage.
"""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.decision.table import create_decision_table


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_decision_table(engine)
    app = create_app()
    app.dependency_overrides[get_decision_engine] = lambda: engine
    return TestClient(app)


def _import_holding(client, ticker: str, weight_percent: float = 100.0) -> str:
    response = client.post("/alpha-portfolio/import", json={"holdings": [{"ticker": ticker, "weightPercent": weight_percent}]})
    assert response.status_code == 201, response.text
    return response.json()["holdings"][0]["caseId"]


def _add_to_watchlist(client, ticker: str) -> str:
    response = client.post("/alpha-watchlist", json={"ticker": ticker})
    assert response.status_code == 201, response.text
    return response.json()["caseId"]


class TestOpportunityCostShape:
    def test_unknown_case_returns_404(self, client):
        response = client.get(f"/opportunity-cost/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_a_freshly_imported_holding_returns_a_real_shape(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/opportunity-cost/{case_id}").json()
        assert body["caseId"] == case_id
        assert set(body) == {"caseId", "currentAction", "tradeoffs", "generatedAt"}

    def test_every_tradeoff_names_a_real_kind_and_reason(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/opportunity-cost/{case_id}").json()
        for tradeoff in body["tradeoffs"]:
            alternative = tradeoff["alternative"]
            assert alternative["kind"] in {
                "increase_existing_holding",
                "open_new_position",
                "wait",
                "no_action",
                "keep_cash",
            }
            assert alternative["reason"]["code"]

    def test_the_opportunity_cost_view_never_leaks_internal_engine_terminology(self, client):
        """Deliverable 14's own language-boundary check at the wire
        level -- no ranking/winner/optimization wording anywhere in
        the payload's own keys."""
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/opportunity-cost/{case_id}").json()
        assert "score" not in body and "winner" not in body and "rank" not in body


class TestPortfolioBreakdown:
    def test_shape_and_scope(self, client):
        _import_holding(client, "NVDA")
        _add_to_watchlist(client, "MSFT")
        body = client.get("/opportunity-cost/portfolio/breakdown").json()
        assert set(body) == {
            "holdingsCompetingForCapital",
            "watchlistCompetingWithHoldings",
            "waitingPreferable",
            "noActionAppropriate",
        }


class TestCompare:
    def test_unknown_ticker_returns_404(self, client):
        _import_holding(client, "NVDA")
        response = client.get("/opportunity-cost/compare?tickerA=NVDA&tickerB=ZZZZZ")
        assert response.status_code == 404

    def test_compares_two_real_tickers_and_never_declares_a_winner(self, client):
        _import_holding(client, "NVDA")
        _add_to_watchlist(client, "MSFT")
        body = client.get("/opportunity-cost/compare?tickerA=NVDA&tickerB=MSFT").json()
        assert set(body) == {"conviction", "path", "moreDependencyBlockedCaseId"}
        assert "winner" not in body


class TestChange:
    def test_first_read_produces_no_change(self, client):
        case_id = _import_holding(client, "NVDA")
        response = client.get(f"/opportunity-cost/{case_id}/change")
        assert response.status_code == 200
        assert response.json() is None
