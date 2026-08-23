"""Daily Brief Agenda -- the real HTTP surface (`/daily-brief-agenda`),
powered by `atlas.alpha.daily_brief_agenda.service.DailyBriefAgendaService`.
Follows the exact fixture/helper pattern `test_portfolio_fit_v1_scenarios.py`
already established.
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


class TestEmptyAgenda:
    def test_no_portfolio_or_watchlist_returns_an_honest_empty_agenda(self, client):
        response = client.get("/daily-brief-agenda")
        assert response.status_code == 200
        body = response.json()
        assert body["items"] == []
        assert body["summary"]["holdingsCount"] == 0
        assert body["summary"]["criticalCount"] == 0
        assert "generatedAt" in body


class TestRealPortfolio:
    def test_a_real_holding_can_produce_a_portfolio_risk_item_from_concentration(self, client):
        _import_holding(client, "AAPL")
        response = client.get("/daily-brief-agenda")
        assert response.status_code == 200
        body = response.json()
        assert body["summary"]["holdingsCount"] == 1
        # The sole 100%-weight holding always trips HIGH_CONCENTRATION.
        assert any(item["ticker"] == "AAPL" for item in body["items"])

    def test_every_item_names_a_real_priority_never_a_number(self, client):
        _import_holding(client, "AAPL")
        response = client.get("/daily-brief-agenda")
        body = response.json()
        for item in body["items"]:
            assert item["priority"] in ("critical", "high", "normal", "low")
            assert "score" not in item
            assert "confidence" not in item

    def test_every_item_is_traceable_to_a_real_source(self, client):
        _import_holding(client, "AAPL")
        response = client.get("/daily-brief-agenda")
        body = response.json()
        for item in body["items"]:
            assert item["source"] in (
                "change_intelligence",
                "portfolio_fit",
                "case_condition",
                "assumption",
                "portfolio_status",
                "portfolio_intelligence",
            )
