"""End-to-end proof that `POST /alpha-watchlist` now schedules an
automatic Monitoring run for the ticker it just added (Internal Alpha
Fix Sprint 1, Deliverable 5 -- Portfolio Change Integration), with no
manual `POST /monitoring/run` required.

Same pattern as `alpha_portfolio/test_bulk_enrichment_v1_scenarios.py`:
fake providers (no network), and the router's own module-level
`get_decision_engine` reference monkeypatched so the automatic
Monitoring background task resolves to the same isolated in-memory
engine as everything else in the test -- `TestClient` runs a
`BackgroundTasks` callable to completion before `.post()` returns
control to the test, so no polling or sleeping is needed.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

import atlas.alpha.watchlist.api.router as watchlist_router
from atlas.alpha.business_data_refresh.api.dependencies import get_default_business_data_providers
from atlas.alpha.monitoring.repository import SqlAlchemyMonitoringResultRepository
from atlas.alpha.monitoring.table import create_monitoring_result_table
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.decision.table import create_decision_table

_NOW = datetime(2026, 8, 9, tzinfo=timezone.utc)


class _FakeProvider:
    def __init__(self) -> None:
        self.call_count: list[str] = []

    def fetch(self, *, company_identifier: str, evaluated_at) -> tuple[RawBusinessDocument, ...]:
        self.call_count.append(company_identifier)
        return (
            RawBusinessDocument(
                identifier=f"{company_identifier}:FY:2025",
                company=company_identifier,
                source_kind="financial_statement",
                published_at=evaluated_at,
                provider_id="fake",
                raw_reference="https://example.test/fs",
                content_hash="fs-hash",
                language="en",
                metadata={"revenue": 5000.0, "free_cash_flow": 1200.0},
            ),
        )

    def fetch_company_profile(self, *, company_identifier: str, evaluated_at) -> tuple[RawBusinessDocument, ...]:
        return (
            RawBusinessDocument(
                identifier=f"{company_identifier}:profile",
                company=company_identifier,
                source_kind="company_profile",
                published_at=evaluated_at,
                provider_id="alpha_vantage",
                raw_reference="https://example.test/profile",
                content_hash="profile-hash",
                language="en",
                metadata={
                    "name": "Meta Platforms, Inc.",
                    "sector": "Communication Services",
                    "exchange": "NASDAQ",
                    "country": "USA",
                    "currency": "USD",
                    "security_type": "COMMON_STOCK",
                },
            ),
        )


@pytest.fixture
def provider() -> _FakeProvider:
    return _FakeProvider()


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_decision_table(engine)
    return engine


@pytest.fixture
def client(engine, provider, monkeypatch):
    # The request-scoped `Depends(get_decision_engine)` graph AND the
    # background task's own bare `get_decision_engine()` call both
    # resolve to this exact in-memory engine.
    monkeypatch.setattr(watchlist_router, "get_decision_engine", lambda: engine)
    app = create_app()
    app.dependency_overrides[get_decision_engine] = lambda: engine
    app.dependency_overrides[get_default_business_data_providers] = lambda: (provider,)
    return TestClient(app)


def _monitoring_result_repository(engine) -> SqlAlchemyMonitoringResultRepository:
    create_monitoring_result_table(engine)
    return SqlAlchemyMonitoringResultRepository(engine)


class TestAddingATickerAutomaticallyMonitorsIt:
    def test_a_freshly_added_ticker_has_a_monitoring_result_by_the_time_add_returns(self, client, engine):
        entry = client.post("/alpha-watchlist", json={"ticker": "META"}).json()

        result = _monitoring_result_repository(engine).get(entry["caseId"])
        assert result is not None
        assert result.ticker == "META"

    def test_no_manual_monitoring_run_endpoint_call_is_needed(self, client, engine):
        """The exact product claim this sprint exists to make true:
        Monitoring already has an opinion on a company the moment it is
        added, with nobody ever having called `POST /monitoring/run`."""
        entry = client.post("/alpha-watchlist", json={"ticker": "META"}).json()

        status_response = client.get("/monitoring/status")
        assert status_response.status_code == 200
        body = status_response.json()
        assert body["lastRunStartedAt"] is not None
        assert entry["caseId"] not in [case_id for case_id, _ in body["pendingCases"]]

    def test_re_adding_an_already_watchlisted_ticker_does_not_fail_even_though_it_reschedules_monitoring(
        self, client, engine
    ):
        first = client.post("/alpha-watchlist", json={"ticker": "META"})
        second = client.post("/alpha-watchlist", json={"ticker": "META"})
        assert first.status_code == 201
        assert second.status_code == 201
        assert first.json()["caseId"] == second.json()["caseId"]

    def test_a_validation_error_never_schedules_a_monitoring_run(self, client, engine):
        response = client.post("/alpha-watchlist", json={"ticker": "   "})
        assert response.status_code == 400
        status_response = client.get("/monitoring/status")
        assert status_response.json()["lastRunStartedAt"] is None
