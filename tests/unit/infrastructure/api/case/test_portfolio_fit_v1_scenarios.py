"""Portfolio Fit Engine -- the real HTTP surface (`/portfolio-fit/*`),
powered by `atlas.alpha.portfolio_fit.service.PortfolioFitService`.
Follows the exact fixture/helper pattern
`test_daily_brief_v1_scenarios.py` already established.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.decision.table import create_decision_table

_NOW = datetime.now(timezone.utc)


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


def _add_to_watchlist(client, ticker: str) -> str:
    response = client.post("/alpha-watchlist", json={"ticker": ticker})
    assert response.status_code == 201, response.text
    case_id = response.json()["caseId"]
    assert case_id is not None
    return case_id


class TestCaseAndTickerEndpoints:
    def test_fit_for_an_existing_holding_is_available_via_both_case_and_ticker(self, client):
        case_id = _import_holding(client, "AAPL")

        by_case = client.get(f"/portfolio-fit/case/{case_id}")
        by_ticker = client.get("/portfolio-fit/ticker/AAPL")

        assert by_case.status_code == 200
        assert by_ticker.status_code == 200
        assert by_case.json()["overall"] == by_ticker.json()["overall"]
        assert by_case.json()["dimensions"] == by_ticker.json()["dimensions"]
        assert by_case.json()["isExistingHolding"] is True
        assert by_case.json()["currentWeightPercent"] == pytest.approx(100.0)

    def test_response_names_every_dimension_qualitatively_never_numerically(self, client):
        case_id = _import_holding(client, "AAPL")
        response = client.get(f"/portfolio-fit/case/{case_id}")
        body = response.json()

        assert isinstance(body["overall"], str)
        assert body["overall"] in ("excellent", "good", "neutral", "weak", "poor", "unavailable")
        for dimension in body["dimensions"]:
            assert isinstance(dimension["rating"], str)
            assert "score" not in dimension
            assert "confidence" not in dimension or dimension.get("kind") != "score"

    def test_unknown_case_returns_404(self, client):
        response = client.get("/portfolio-fit/case/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_unknown_ticker_returns_404(self, client):
        response = client.get("/portfolio-fit/ticker/ZZZZ")
        assert response.status_code == 404


class TestCompareEndpoint:
    def test_comparing_two_holdings_names_a_preferred_ticker_or_none(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [
                {"ticker": "AAPL", "weightPercent": 50.0},
                {"ticker": "MSFT", "weightPercent": 50.0},
            ]},
        )
        response = client.get("/portfolio-fit/compare", params={"tickerA": "AAPL", "tickerB": "MSFT"})
        assert response.status_code == 200
        body = response.json()
        assert body["assessmentA"]["ticker"] == "AAPL"
        assert body["assessmentB"]["ticker"] == "MSFT"
        assert body["preferredTicker"] in (None, "AAPL", "MSFT")

    def test_comparing_against_an_unknown_ticker_returns_404(self, client):
        _import_holding(client, "AAPL")
        response = client.get("/portfolio-fit/compare", params={"tickerA": "AAPL", "tickerB": "ZZZZ"})
        assert response.status_code == 404


class TestHoldingsAndCandidatesEndpoints:
    def test_holdings_endpoint_lists_every_case_linked_holding(self, client):
        _import_holding(client, "AAPL")
        response = client.get("/portfolio-fit/holdings")
        assert response.status_code == 200
        tickers = [a["ticker"] for a in response.json()]
        assert "AAPL" in tickers

    def test_candidates_endpoint_excludes_existing_holdings(self, client):
        _import_holding(client, "AAPL")
        watchlist_case_id = _add_to_watchlist(client, "NVDA")

        holdings_response = client.get("/portfolio-fit/holdings")
        candidates_response = client.get("/portfolio-fit/candidates")

        holding_case_ids = {a["caseId"] for a in holdings_response.json()}
        candidate_case_ids = {a["caseId"] for a in candidates_response.json()}

        assert holding_case_ids.isdisjoint(candidate_case_ids)
        assert watchlist_case_id in candidate_case_ids

    def test_empty_portfolio_and_watchlist_returns_empty_lists_not_errors(self, client):
        assert client.get("/portfolio-fit/holdings").json() == []
        assert client.get("/portfolio-fit/candidates").json() == []
