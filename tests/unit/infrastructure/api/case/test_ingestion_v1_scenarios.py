"""Data Ingestion & Automatic Refresh -- the real HTTP surface
(`/ingestion/*`), powered by `atlas.alpha.ingestion.service
.IngestionService`. Follows the exact fixture/helper pattern
`test_monitoring_v1_scenarios.py` already established. No real network
access is available in this environment, so these tests exercise the
real, honest "no provider could be reached" path -- the same path a
real deployment with an unconfigured/rate-limited provider would take
-- rather than genuinely new data (which `tests/unit/alpha/ingestion
/test_service.py` already covers with fake, deterministic providers).
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


class TestIngestionRefresh:
    def test_refreshing_a_real_ticker_returns_an_honest_result_shape(self, client):
        _import_holding(client, "NVDA")
        body = client.post("/ingestion/refresh/NVDA").json()
        assert set(body) == {
            "ticker", "caseId", "ranAt", "changes", "hasNewData", "fetchedDocuments",
            "duplicatesSkipped", "rejectedDocuments", "providerErrors", "identityGateOutcome",
        }
        assert body["ticker"] == "NVDA"

    def test_the_case_id_is_resolved_from_real_portfolio_membership(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.post("/ingestion/refresh/NVDA").json()
        assert body["caseId"] == case_id

    def test_a_ticker_with_no_known_case_still_returns_a_result_with_no_case_id(self, client):
        body = client.post("/ingestion/refresh/ZZZZZ").json()
        assert body["caseId"] is None

    def test_running_twice_in_a_row_never_crashes_and_stays_honest(self, client):
        _import_holding(client, "NVDA")
        first = client.post("/ingestion/refresh/NVDA").json()
        second = client.post("/ingestion/refresh/NVDA").json()
        assert first["hasNewData"] == second["hasNewData"]


class TestIngestionResults:
    def test_no_result_recorded_yet_is_a_404_not_a_fabricated_empty_result(self, client):
        case_id = _import_holding(client, "NVDA")
        response = client.get(f"/ingestion/results/{case_id}")
        assert response.status_code == 404

    def test_after_a_refresh_the_result_is_readable_without_recomputing(self, client):
        case_id = _import_holding(client, "NVDA")
        run_body = client.post("/ingestion/refresh/NVDA").json()
        read_body = client.get(f"/ingestion/results/{case_id}").json()
        assert read_body["ranAt"] == run_body["ranAt"]


class TestMonitoringIntegration:
    """Deliverable 5 -- Monitoring reads Ingestion's own read model,
    never re-detects data changes itself."""

    def test_operational_freshness_reflects_a_case_with_no_ingestion_history_yet(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/cases/{case_id}/analysis").json()
        # No `/ingestion/refresh` has been called for this Case yet, and
        # no `/monitoring/run` either -- genuinely unknown.
        assert body["operationalFreshness"]["dataFreshnessStatus"] == "unknown"

    def test_a_recorded_ingestion_result_with_no_new_data_is_reflected_honestly(self, client):
        case_id = _import_holding(client, "NVDA")
        client.post("/ingestion/refresh/NVDA")  # real network unavailable -> fetchedDocuments == 0
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert body["operationalFreshness"]["dataFreshnessStatus"] == "no_data_source"
