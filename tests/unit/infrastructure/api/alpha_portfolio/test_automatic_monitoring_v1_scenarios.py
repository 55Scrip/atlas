"""End-to-end proof that Portfolio's real data-mutation events schedule
an automatic Monitoring run (Internal Alpha Fix Sprint 1, Deliverable
4/5): `POST /alpha-portfolio/import` (chained onto the same background
enrichment task that already existed), and `POST /alpha-portfolio/
apply-trade` opening a genuinely new position. No manual `POST
/monitoring/run` is called anywhere in this file.

Same fixture pattern as `test_bulk_enrichment_v1_scenarios.py` and
`test_execution_v1_scenarios.py` -- reused, not reinvented.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

import atlas.alpha.portfolio.api.router as portfolio_router
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.monitoring.repository import SqlAlchemyMonitoringResultRepository
from atlas.alpha.monitoring.table import create_monitoring_result_table
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.decision.table import create_decision_table

_EVALUATED_AT = datetime(2026, 8, 9, tzinfo=timezone.utc)


@dataclass(frozen=True)
class _FakeProvider:
    documents: tuple[RawBusinessDocument, ...] = ()

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        return tuple(d for d in self.documents if d.company == company_identifier)


def _doc(*, identifier: str, company: str) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=identifier,
        company=company,
        source_kind="financial_statement",
        published_at=_EVALUATED_AT,
        provider_id="fake_provider",
        raw_reference="https://example.test/doc",
        content_hash=f"hash-{identifier}",
        language="en",
        metadata={"revenue": 100.0, "currency": "USD"},
    )


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_decision_table(engine)
    create_business_record_table(engine)
    return engine


@pytest.fixture
def client(engine, monkeypatch):
    monkeypatch.setattr(portfolio_router, "get_decision_engine", lambda: engine)
    app = create_app()
    app.dependency_overrides[get_decision_engine] = lambda: engine
    return TestClient(app)


def _set_fake_providers(monkeypatch, *providers) -> None:
    monkeypatch.setattr(portfolio_router, "get_default_business_data_providers", lambda: providers)


def _monitoring_result_repository(engine) -> SqlAlchemyMonitoringResultRepository:
    create_monitoring_result_table(engine)
    return SqlAlchemyMonitoringResultRepository(engine)


class TestImportAutomaticallyMonitorsEveryHolding:
    def test_a_freshly_imported_holding_has_a_monitoring_result_by_the_time_import_returns(
        self, client, engine, monkeypatch
    ):
        _set_fake_providers(monkeypatch, _FakeProvider(documents=(_doc(identifier="AAPL:FY:2024", company="AAPL"),)))

        response = client.post("/alpha-portfolio/import", json={"holdings": [{"ticker": "AAPL", "weightPercent": 100.0}]})
        assert response.status_code == 201
        case_id = response.json()["holdings"][0]["caseId"]

        result = _monitoring_result_repository(engine).get(case_id)
        assert result is not None
        assert result.ticker == "AAPL"

    def test_reimporting_the_same_holding_still_succeeds_once_it_is_already_monitored(
        self, client, engine, monkeypatch
    ):
        """The automatic Monitoring trigger firing twice for the same,
        already-monitored holding (nothing new to evaluate the second
        time) must never turn a valid re-import into a failure."""
        _set_fake_providers(monkeypatch, _FakeProvider(documents=(_doc(identifier="AAPL:FY:2024", company="AAPL"),)))
        first = client.post("/alpha-portfolio/import", json={"holdings": [{"ticker": "AAPL", "weightPercent": 100.0}]})
        assert first.status_code == 201
        second = client.post("/alpha-portfolio/import", json={"holdings": [{"ticker": "AAPL", "weightPercent": 100.0}]})
        assert second.status_code == 201


class TestApplyTradeAutomaticallyMonitorsANewPosition:
    def _record_decision_and_outcome(self, client, *, subject: str) -> tuple[dict, dict]:
        case_id = client.post("/cases").json()["caseId"]
        decision = client.post(
            "/decisions",
            json={
                "caseId": case_id,
                "userId": "00000000-0000-0000-0000-000000000001",
                "decisionType": "BUY",
                "subject": subject,
                "reason": "Testing automatic monitoring.",
                "confidence": 70,
            },
        ).json()
        outcome = client.post(
            "/outcomes",
            json={
                "decisionId": decision["id"],
                "statement": "Executed.",
                "occurredAt": datetime.now(timezone.utc).isoformat(),
            },
        ).json()
        return decision, outcome

    def test_a_buy_on_a_new_ticker_has_a_monitoring_result_by_the_time_the_trade_returns(self, client, engine):
        assert client.post("/alpha-portfolio/from-scratch", json={"objective": "Growth", "horizon": "5-10 years"}).status_code == 201
        decision, outcome = self._record_decision_and_outcome(client, subject="NVDA")
        response = client.post(
            "/alpha-portfolio/apply-trade",
            json={
                "outcomeId": outcome["id"],
                "decisionId": decision["id"],
                "security": "NVDA",
                "transactionType": "BUY",
                "quantity": 1,
                "executionPrice": 100,
                "executedAt": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 200, response.text
        new_case_id = next(h["caseId"] for h in response.json()["holdings"] if h["ticker"] == "NVDA")

        result = _monitoring_result_repository(engine).get(new_case_id)
        assert result is not None
        assert result.ticker == "NVDA"
