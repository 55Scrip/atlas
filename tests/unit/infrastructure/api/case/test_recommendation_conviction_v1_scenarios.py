"""Recommendation Conviction & Strength -- the real HTTP surface
(`/recommendation-conviction/*`), powered by `atlas.alpha
.recommendation_conviction.service.RecommendationConvictionService`.
Follows the exact fixture/helper pattern
`test_investment_decision_v1_scenarios.py` already established. No
real network access is available in this environment, so a freshly
imported holding genuinely has `NO_COVERAGE` -- these tests exercise
that real, honest floor state (`unavailable`) rather than fabricating
richer coverage.
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


class TestRecommendationConvictionShape:
    def test_unknown_case_returns_404(self, client):
        response = client.get(f"/recommendation-conviction/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_a_freshly_imported_holding_with_no_ingested_data_is_unavailable(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/recommendation-conviction/{case_id}").json()
        assert body["caseId"] == case_id
        assert body["strength"] == "unavailable"
        assert set(body) == {
            "caseId",
            "action",
            "strength",
            "stability",
            "supportingReasons",
            "limitingReasons",
            "strengtheningTrigger",
            "generatedAt",
        }

    def test_the_conviction_view_never_leaks_internal_engine_terminology(self, client):
        """Deliverable 13's own language-boundary check at the wire
        level -- no probability/score/prediction wording anywhere in
        the payload's own keys."""
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/recommendation-conviction/{case_id}").json()
        assert "score" not in body and "probability" not in body and "prediction" not in body


class TestPortfolioBreakdown:
    def test_shape_and_scope(self, client):
        _import_holding(client, "NVDA")
        _add_to_watchlist(client, "MSFT")
        body = client.get("/recommendation-conviction/portfolio/breakdown").json()
        assert set(body) == {"highestConviction", "lowestConviction", "evidenceLimited", "operationallyBlocked"}
        all_tickers = {t for tickers in body.values() for t in tickers}
        assert "MSFT" not in all_tickers


class TestCompare:
    def test_unknown_ticker_returns_404(self, client):
        _import_holding(client, "NVDA")
        response = client.get("/recommendation-conviction/compare?tickerA=NVDA&tickerB=ZZZZZ")
        assert response.status_code == 404

    def test_compares_two_real_tickers_and_never_names_an_overall_winner(self, client):
        _import_holding(client, "NVDA")
        _add_to_watchlist(client, "MSFT")
        body = client.get("/recommendation-conviction/compare?tickerA=NVDA&tickerB=MSFT").json()
        assert body["a"]["strength"] == "unavailable"
        assert body["b"]["strength"] == "unavailable"
        assert set(body) == {
            "a",
            "b",
            "strongerCaseId",
            "moreEvidenceLimitedCaseId",
            "moreOperationallyBlockedCaseId",
            "moreStableCaseId",
        }


class TestChange:
    def test_first_read_produces_no_change(self, client):
        case_id = _import_holding(client, "NVDA")
        response = client.get(f"/recommendation-conviction/{case_id}/change")
        assert response.status_code == 200
        assert response.json() is None
