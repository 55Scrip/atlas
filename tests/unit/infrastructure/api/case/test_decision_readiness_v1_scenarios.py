"""Decision Readiness & Decision Eligibility -- the real HTTP surface
(`/decision-readiness/*`), powered by `atlas.alpha.decision_readiness
.service.DecisionReadinessService`. Follows the exact fixture/helper
pattern `test_evidence_graph_v1_scenarios.py` already established. No
real network access is available in this environment, so a freshly
imported holding genuinely has `NO_COVERAGE` (no ingested
`BusinessRecord`s) -- these tests exercise that real, honest floor
state rather than fabricating richer coverage.
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


class TestDecisionReadinessShape:
    def test_unknown_case_returns_404(self, client):
        response = client.get(f"/decision-readiness/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_a_freshly_imported_holding_with_no_ingested_data_is_unknown(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/decision-readiness/{case_id}").json()
        assert body["caseId"] == case_id
        assert body["status"] == "unknown"
        assert set(body) == {"caseId", "status", "blockers", "supportingReasons", "generatedAt"}

    def test_the_readiness_view_never_leaks_investment_status_fields(self, client):
        """Deliverable 12's own language-boundary check at the wire
        level -- Decision Readiness must never be confused with Stance
        or Decision Support at the API shape level."""
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/decision-readiness/{case_id}").json()
        assert "stanceLevel" not in body and "decisionSupportLevel" not in body


class TestPortfolioBreakdown:
    def test_shape_and_scope(self, client):
        case_id = _import_holding(client, "NVDA")
        _add_to_watchlist(client, "MSFT")
        body = client.get("/decision-readiness/portfolio/breakdown").json()
        assert set(body) == {"ready", "almostReady", "waiting", "blocked", "unavailable", "unknown"}
        assert "NVDA" in body["unknown"]
        all_tickers = {t for tickers in body.values() for t in tickers}
        assert "MSFT" not in all_tickers


class TestCompare:
    def test_unknown_ticker_returns_404(self, client):
        _import_holding(client, "NVDA")
        response = client.get("/decision-readiness/compare?tickerA=NVDA&tickerB=ZZZZZ")
        assert response.status_code == 404

    def test_compares_two_real_tickers(self, client):
        _import_holding(client, "NVDA")
        _add_to_watchlist(client, "MSFT")
        body = client.get("/decision-readiness/compare?tickerA=NVDA&tickerB=MSFT").json()
        assert body["a"]["status"] == "unknown"
        assert body["b"]["status"] == "unknown"
        assert body["closerCaseId"] is None


class TestChange:
    def test_first_read_produces_no_change(self, client):
        case_id = _import_holding(client, "NVDA")
        response = client.get(f"/decision-readiness/{case_id}/change")
        assert response.status_code == 200
        assert response.json() is None
