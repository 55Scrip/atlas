"""Portfolio Decision Synthesis -- the real HTTP surface
(`/portfolio-decision/*`), powered by `atlas.alpha.portfolio_decision
.service.PortfolioDecisionService`. Follows the exact fixture/helper
pattern `test_decision_reliability_v1_scenarios.py` already
established.
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


def _import_holdings(client, weights_by_ticker: dict[str, float]) -> dict[str, str]:
    response = client.post(
        "/alpha-portfolio/import",
        json={"holdings": [{"ticker": ticker, "weightPercent": weight} for ticker, weight in weights_by_ticker.items()]},
    )
    assert response.status_code == 201, response.text
    return {h["ticker"]: h["caseId"] for h in response.json()["holdings"]}


class TestPortfolioDecisionShape:
    def test_unknown_case_returns_404(self, client):
        response = client.get(f"/portfolio-decision/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_a_freshly_imported_holding_returns_a_real_decision(self, client):
        case_id = _import_holding(client, "NVDA")
        response = client.get(f"/portfolio-decision/{case_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["caseId"] == case_id
        assert body["category"] in {"supports_portfolio", "neutral", "requires_review", "conflicts_with_portfolio", "operationally_limited", "unknown"}

    def test_no_reference_is_ever_anonymous(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/portfolio-decision/{case_id}").json()
        for reason in body["supportingReasons"] + body["limitingReasons"]:
            assert reason["reference"]["id"]
            assert reason["source"] in {"portfolio_fit", "portfolio_intelligence", "opportunity_cost", "decision_reliability"}

    def test_a_single_full_weight_holding_is_the_largest_position(self, client):
        case_id = _import_holding(client, "NVDA", 100.0)
        body = client.get(f"/portfolio-decision/{case_id}").json()
        assert body["impact"]["isLargestPosition"] is True
        assert body["impact"]["currentWeightPercent"] == 100.0


class TestPortfolioDecisionChangeShape:
    def test_first_call_returns_null_change(self, client):
        case_id = _import_holding(client, "NVDA")
        response = client.get(f"/portfolio-decision/{case_id}/change")
        assert response.status_code == 200
        assert response.json() is None

    def test_no_change_on_repeated_calls_when_nothing_changed(self, client):
        case_id = _import_holding(client, "NVDA")
        client.get(f"/portfolio-decision/{case_id}")
        response = client.get(f"/portfolio-decision/{case_id}/change")
        assert response.json() is None


class TestPortfolioDecisionCompare:
    def test_unknown_ticker_returns_404(self, client):
        _import_holding(client, "AAPL")
        response = client.get("/portfolio-decision/compare", params={"tickerA": "AAPL", "tickerB": "UNKNOWN"})
        assert response.status_code == 404

    def test_compares_two_real_tickers(self, client):
        _import_holdings(client, {"AAPL": 50.0, "MSFT": 50.0})
        response = client.get("/portfolio-decision/compare", params={"tickerA": "AAPL", "tickerB": "MSFT"})
        assert response.status_code == 200
        body = response.json()
        assert body["a"]["caseId"] != body["b"]["caseId"]
        assert "winner" not in body


class TestPortfolioSynthesisBreakdown:
    def test_empty_portfolio_returns_empty_buckets(self, client):
        response = client.get("/portfolio-decision/portfolio/breakdown")
        assert response.status_code == 200
        body = response.json()
        assert body["supportsPortfolio"] == []

    def test_a_fresh_holding_never_lands_in_both_conflict_and_support_buckets(self, client):
        _import_holding(client, "NVDA")
        response = client.get("/portfolio-decision/portfolio/breakdown")
        body = response.json()
        assert not ("NVDA" in body["supportsPortfolio"] and "NVDA" in body["conflictsWithPortfolio"])
