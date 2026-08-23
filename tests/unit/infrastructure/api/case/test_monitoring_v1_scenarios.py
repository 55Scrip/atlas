"""Monitoring & Change Detection -- the real HTTP surface
(`/monitoring/*`), powered by `atlas.alpha.monitoring.service
.MonitoringService`. Follows the exact fixture/helper pattern
`test_evidence_timeline_v1_scenarios.py` already established.
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
    response = client.post("/alpha-portfolio/import", json={"holdings": [{"ticker": ticker, "weightPercent": weight_percent}]})
    assert response.status_code == 201, response.text
    return response.json()["holdings"][0]["caseId"]


class TestMonitoringRun:
    def test_running_with_no_portfolio_or_watchlist_produces_an_empty_run(self, client):
        body = client.post("/monitoring/run").json()
        assert body["results"] == []

    def test_a_portfolio_holding_is_evaluated_and_scoped_as_portfolio(self, client):
        _import_holding(client, "NVDA")
        body = client.post("/monitoring/run").json()
        assert len(body["results"]) == 1
        assert body["results"][0]["ticker"] == "NVDA"
        assert body["results"][0]["scope"] == "portfolio"

    def test_a_watchlist_only_company_is_scoped_as_watchlist(self, client):
        response = client.post("/alpha-watchlist", json={"ticker": "AMD"})
        assert response.status_code in (200, 201), response.text
        body = client.post("/monitoring/run").json()
        tickers = {r["ticker"]: r["scope"] for r in body["results"]}
        assert tickers.get("AMD") == "watchlist"

    def test_the_first_ever_run_for_a_case_never_reports_a_change(self, client):
        _import_holding(client, "NVDA")
        body = client.post("/monitoring/run").json()
        assert body["results"][0]["changes"] == []

    def test_running_twice_with_no_underlying_change_produces_no_new_changes(self, client):
        """Critical requirement (Deliverable 11/25/26): unchanged
        recomputation must never fabricate a monitoring event."""
        _import_holding(client, "NVDA")
        client.post("/monitoring/run")
        second = client.post("/monitoring/run").json()
        assert second["results"][0]["changes"] == []

    def test_every_result_has_the_full_expected_shape(self, client):
        _import_holding(client, "NVDA")
        body = client.post("/monitoring/run").json()
        result = body["results"][0]
        assert set(result) == {
            "caseId", "ticker", "scope", "status", "changes", "stanceLevel", "confidenceLevel",
            "coverageLevel", "latestMeaningfulEvidenceAt", "recommendedAction", "generatedAt",
        }
        assert result["status"] in {
            "up_to_date", "changed_review_suggested", "changed_high_importance", "waiting_for_better_evidence", "unavailable",
        }


class TestMonitoringReadModel:
    def test_the_read_model_is_empty_before_any_run_has_happened(self, client):
        _import_holding(client, "NVDA")
        body = client.get("/monitoring/results").json()
        assert body["results"] == []

    def test_the_read_model_reflects_the_last_run_without_recomputing(self, client):
        _import_holding(client, "NVDA")
        run_body = client.post("/monitoring/run").json()
        read_body = client.get("/monitoring/results").json()
        assert {r["caseId"] for r in read_body["results"]} == {r["caseId"] for r in run_body["results"]}


class TestMonitoringIncremental:
    """Atlas Intelligence Sprint 8 -- Automated Monitoring Operations."""

    def test_a_second_run_with_no_new_signal_carries_the_same_checkpoint_forward(self, client):
        _import_holding(client, "NVDA")
        run1 = client.post("/monitoring/run").json()
        run2 = client.post("/monitoring/run").json()
        assert run1["results"][0]["generatedAt"] == run2["results"][0]["generatedAt"]

    def test_recording_a_decision_makes_the_next_run_reevaluate(self, client):
        case_id = _import_holding(client, "NVDA")
        run1 = client.post("/monitoring/run").json()
        client.post(
            "/decisions",
            json={
                "caseId": case_id,
                "userId": "00000000-0000-0000-0000-000000000001",
                "decisionType": "HOLD",
                "subject": "NVDA",
                "reason": "Sprint 8 incremental monitoring live check.",
                "confidence": 65,
            },
        )
        run2 = client.post("/monitoring/run").json()
        assert run1["results"][0]["generatedAt"] != run2["results"][0]["generatedAt"]

    def test_force_true_reevaluates_even_with_nothing_dirty(self, client):
        _import_holding(client, "NVDA")
        client.post("/monitoring/run")
        forced = client.post("/monitoring/run", params={"force": "true"}).json()
        # A forced re-evaluation still produces exactly one result and never crashes.
        assert len(forced["results"]) == 1


class TestMonitoringStatus:
    def test_status_is_unknown_before_any_run(self, client):
        _import_holding(client, "NVDA")
        body = client.get("/monitoring/status").json()
        assert body["status"] == "unknown"

    def test_status_is_up_to_date_after_a_clean_run(self, client):
        _import_holding(client, "NVDA")
        client.post("/monitoring/run")
        body = client.get("/monitoring/status").json()
        assert body["status"] == "up_to_date"
        assert body["pendingCases"] == []
        assert body["failedCases"] == []

    def test_status_becomes_pending_after_a_new_watchlist_addition(self, client):
        _import_holding(client, "NVDA")
        client.post("/monitoring/run")
        client.post("/alpha-watchlist", json={"ticker": "AMD"})
        body = client.get("/monitoring/status").json()
        assert body["status"] == "pending"
        assert any(c["ticker"] == "AMD" for c in body["pendingCases"])

    def test_the_status_shape_never_leaks_investment_fields(self, client):
        """Deliverable 7 -- operational status must stay structurally
        distinct from `MonitoringResultView` (investment status)."""
        _import_holding(client, "NVDA")
        client.post("/monitoring/run")
        body = client.get("/monitoring/status").json()
        assert set(body) == {
            "status",
            "lastRunStartedAt",
            "lastRunCompletedAt",
            "pendingCases",
            "failedCases",
            "portfolioFreshness",
            "watchlistFreshness",
        }
        assert "stanceLevel" not in body and "changes" not in body
