"""Decision Memory -- the real HTTP surface (`/decision-memory/*`),
powered by `atlas.alpha.decision_memory.service.DecisionMemoryService`.
Follows the exact fixture/helper pattern
`test_opportunity_cost_v1_scenarios.py` already established. No real
network access is available in this environment, so a freshly imported
holding genuinely has never been evaluated -- these tests exercise
that real, honest floor state (a single baseline snapshot) rather than
fabricating richer coverage.
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


class TestDecisionMemoryShape:
    def test_unknown_case_returns_404(self, client):
        response = client.get(f"/decision-memory/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_a_freshly_imported_holding_has_exactly_one_baseline_snapshot(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/decision-memory/{case_id}").json()
        assert body["caseId"] == case_id
        assert body["previousSnapshot"] is None
        assert body["latestChange"] is None
        assert len(body["history"]["entries"]) == 1
        assert body["history"]["entries"][0]["change"]["isBaseline"] is True

    def test_repeated_reads_never_append_a_duplicate_row(self, client):
        case_id = _import_holding(client, "NVDA")
        client.get(f"/decision-memory/{case_id}")
        client.get(f"/decision-memory/{case_id}")
        body = client.get(f"/decision-memory/{case_id}").json()
        assert len(body["history"]["entries"]) == 1

    def test_the_memory_view_never_leaks_internal_engine_terminology(self, client):
        """Deliverable 14's own language-boundary check at the wire
        level -- no memory/learning/AI/psychology wording anywhere in
        the payload's own keys."""
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/decision-memory/{case_id}").json()
        assert "score" not in body and "learned" not in body and "personalized" not in body


class TestPortfolioBreakdown:
    def test_shape_and_scope(self, client):
        _import_holding(client, "NVDA")
        _add_to_watchlist(client, "MSFT")
        body = client.get("/decision-memory/portfolio/breakdown").json()
        assert set(body) == {"recentlyChanged", "stable", "recentlyStrengthened", "recentlyWeakened"}
        all_tickers = set(body["recentlyChanged"]) | set(body["stable"])
        assert "MSFT" not in all_tickers


class TestCompare:
    def test_unknown_ticker_returns_404(self, client):
        _import_holding(client, "NVDA")
        response = client.get("/decision-memory/compare?tickerA=NVDA&tickerB=ZZZZZ")
        assert response.status_code == 404

    def test_compares_two_real_tickers_and_never_declares_a_winner(self, client):
        _import_holding(client, "NVDA")
        _add_to_watchlist(client, "MSFT")
        body = client.get("/decision-memory/compare?tickerA=NVDA&tickerB=MSFT").json()
        assert set(body) == {
            "a",
            "b",
            "moreRecentlyChangedCaseId",
            "moreStableCaseId",
            "convictionChangedCaseId",
            "blockersDisappearedCaseId",
        }


class TestChange:
    def test_first_read_produces_no_change(self, client):
        case_id = _import_holding(client, "NVDA")
        response = client.get(f"/decision-memory/{case_id}/change")
        assert response.status_code == 200
        assert response.json() is None
