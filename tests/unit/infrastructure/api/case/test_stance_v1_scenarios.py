"""Stance Engine -- the real HTTP surface (`/stance/*`), powered by
`atlas.alpha.stance.service.StanceService`. Follows the exact fixture/
helper pattern `test_portfolio_fit_v1_scenarios.py` already established.
"""
from __future__ import annotations

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
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(engine)
    app = create_app()
    app.dependency_overrides[get_decision_engine] = lambda: engine
    return TestClient(app)


def _import_holding(client, ticker: str, weight_percent: float = 100.0) -> str:
    return _import_holdings(client, [(ticker, weight_percent)])[ticker]


def _import_holdings(client, tickers_and_weights: list[tuple[str, float]]) -> dict[str, str]:
    """`/alpha-portfolio/import` replaces the whole portfolio on every
    call -- multiple holdings must be imported together in one call, or
    each subsequent call silently discards the previous one."""
    response = client.post(
        "/alpha-portfolio/import",
        json={"holdings": [{"ticker": ticker, "weightPercent": weight} for ticker, weight in tickers_and_weights]},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    return {h["ticker"]: h["caseId"] for h in body["holdings"]}


def _add_to_watchlist(client, ticker: str) -> str:
    response = client.post("/alpha-watchlist", json={"ticker": ticker})
    assert response.status_code == 201, response.text
    return response.json()["caseId"]


_STANCE_LEVELS = {"increase", "maintain", "reduce", "review", "wait", "avoid_decision", "no_recommendation"}


class TestCaseAndTickerEndpoints:
    def test_stance_for_a_fresh_holding_is_available_via_both_case_and_ticker(self, client):
        case_id = _import_holding(client, "AAPL")
        by_case = client.get(f"/stance/case/{case_id}")
        by_ticker = client.get("/stance/ticker/AAPL")
        assert by_case.status_code == 200
        assert by_ticker.status_code == 200
        assert by_case.json() == by_ticker.json()

    def test_returns_404_for_an_unknown_case_id(self, client):
        response = client.get("/stance/case/00000000-0000-0000-0000-000000000099")
        assert response.status_code == 404

    def test_returns_404_for_a_ticker_with_no_case(self, client):
        response = client.get("/stance/ticker/ZZZZZ")
        assert response.status_code == 404


class TestStanceShape:
    def test_a_fresh_holding_with_no_data_and_no_evidence_is_conservative(self, client):
        """No BusinessRecords, no investor evidence -- Conviction's own
        real gate fires and this engine honestly propagates it, never a
        confident directional claim."""
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/stance/case/{case_id}").json()
        assert body["level"] in _STANCE_LEVELS
        assert body["level"] not in ("increase", "reduce")
        assert body["reasoning"]
        assert all("code" in r for r in body["reasoning"])

    def test_never_leaks_a_raw_share_count_or_trade_verb(self, client):
        """This engine never recommends buying or selling shares --
        only every response field name/shape is checked here since the
        wire format is entirely closed enum codes, never free text."""
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/stance/case/{case_id}").json()
        assert set(body) == {"level", "reasoning", "supportingSignals", "limitingSignals", "confidence", "missingInformation"}
        for reason in body["reasoning"] + body["supportingSignals"] + body["limitingSignals"]:
            assert set(reason) == {"code"}


class TestPortfolioSurface:
    def test_holdings_endpoint_returns_one_entry_per_holding_with_a_case(self, client):
        _import_holdings(client, [("NVDA", 60), ("AMD", 40)])
        body = client.get("/stance/holdings").json()
        assert {entry["ticker"] for entry in body} == {"NVDA", "AMD"}
        for entry in body:
            assert entry["stance"]["level"] in _STANCE_LEVELS


class TestDiscoverySurface:
    def test_candidates_endpoint_excludes_existing_holdings(self, client):
        _import_holdings(client, [("NVDA", 100)])
        _add_to_watchlist(client, "AMD")
        body = client.get("/stance/candidates").json()
        tickers = {entry["ticker"] for entry in body}
        assert "AMD" in tickers
        assert "NVDA" not in tickers


class TestCompareIntegration:
    def test_compare_two_uncertain_companies_never_forces_a_preference(self, client):
        """Deliverable 9's own worked example: when Atlas cannot
        honestly choose, it must say so, never force a winner."""
        _import_holdings(client, [("NVDA", 50), ("AMD", 50)])
        body = client.get("/stance/compare?tickerA=NVDA&tickerB=AMD").json()
        assert body["preferredTicker"] is None
        assert body["reasoning"]

    def test_returns_404_when_either_ticker_has_no_case(self, client):
        _import_holding(client, "NVDA")
        response = client.get("/stance/compare?tickerA=NVDA&tickerB=ZZZZZ")
        assert response.status_code == 404

    def test_compare_is_symmetric(self, client):
        _import_holdings(client, [("NVDA", 50), ("AMD", 50)])
        a = client.get("/stance/compare?tickerA=NVDA&tickerB=AMD").json()
        b = client.get("/stance/compare?tickerA=AMD&tickerB=NVDA").json()
        assert a["preferredTicker"] == b["preferredTicker"]
