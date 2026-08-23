"""Decision Reliability -- the real HTTP surface
(`/decision-reliability/*`), powered by `atlas.alpha.decision_reliability
.service.DecisionReliabilityService`. Follows the exact fixture/helper
pattern `test_decision_explanation_v1_scenarios.py` already established.
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


class TestDecisionReliabilityShape:
    def test_unknown_case_returns_404(self, client):
        response = client.get(f"/decision-reliability/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_a_freshly_imported_holding_returns_a_real_reliability(self, client):
        case_id = _import_holding(client, "NVDA")
        response = client.get(f"/decision-reliability/{case_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["caseId"] == case_id
        assert body["level"] in {"high", "moderate", "limited", "unavailable", "unknown"}

    def test_no_reference_is_ever_anonymous(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/decision-reliability/{case_id}").json()
        for reason in body["supportingReasons"] + body["limitingReasons"]:
            assert reason["reference"]["id"]
            assert reason["source"] in {"confidence", "evidence_quality", "readiness_blocker", "readiness_support"}


class TestDecisionReliabilityChangeShape:
    def test_first_call_returns_null_change(self, client):
        case_id = _import_holding(client, "NVDA")
        response = client.get(f"/decision-reliability/{case_id}/change")
        assert response.status_code == 200
        assert response.json() is None

    def test_no_change_on_repeated_calls_when_nothing_changed(self, client):
        case_id = _import_holding(client, "NVDA")
        client.get(f"/decision-reliability/{case_id}")
        response = client.get(f"/decision-reliability/{case_id}/change")
        assert response.json() is None


class TestDecisionReliabilityCompare:
    def test_unknown_ticker_returns_404(self, client):
        _import_holding(client, "AAPL")
        response = client.get("/decision-reliability/compare", params={"tickerA": "AAPL", "tickerB": "UNKNOWN"})
        assert response.status_code == 404

    def test_compares_two_real_tickers(self, client):
        _import_holdings(client, {"AAPL": 50.0, "MSFT": 50.0})
        response = client.get("/decision-reliability/compare", params={"tickerA": "AAPL", "tickerB": "MSFT"})
        assert response.status_code == 200
        body = response.json()
        assert body["a"]["caseId"] != body["b"]["caseId"]
        assert "winner" not in body


class TestDecisionReliabilityPortfolioBreakdown:
    def test_empty_portfolio_returns_empty_buckets(self, client):
        response = client.get("/decision-reliability/portfolio/breakdown")
        assert response.status_code == 200
        body = response.json()
        assert body["mostReliable"] == []

    def test_a_fresh_holding_never_lands_in_both_buckets(self, client):
        _import_holding(client, "NVDA")
        response = client.get("/decision-reliability/portfolio/breakdown")
        body = response.json()
        assert not ("NVDA" in body["mostReliable"] and "NVDA" in body["leastReliable"])
