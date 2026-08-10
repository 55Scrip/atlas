"""Daily Brief v1 -- `GET /daily-brief`, powered by
`atlas.alpha.daily_brief.service.DailyBriefService`. Exercises the real
HTTP surface end-to-end through the real Alpha Portfolio/Watchlist/
Investment-Case APIs, following the exact fixture/helper pattern
`test_investment_case_analysis_v1_scenarios.py` already established.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
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


def _growth_record(*, company: str, identifier: str, period_end, revenue: float, free_cash_flow: float):
    document = RawBusinessDocument(
        identifier=identifier,
        company=company,
        source_kind="annual_report",
        published_at=_NOW,
        provider_id="structured_test",
        raw_reference=f"ref://{identifier}",
        content_hash=f"hash-{identifier}",
        language="en",
        period_end=period_end,
        metadata={"revenue": revenue, "free_cash_flow": free_cash_flow},
    )
    result = ingest(document, evaluated_at=_NOW)
    assert isinstance(result, IngestedRecord)
    return result.record


def _add_records(client, ticker: str, records) -> None:
    engine = client.engine
    create_business_record_table(engine)
    repository = SqlAlchemyBusinessRecordRepository(engine)
    for record in records:
        repository.add(record)


class TestEmptyBrief:
    def test_no_portfolio_or_watchlist_returns_the_exact_no_change_summary(self, client):
        response = client.get("/daily-brief")
        assert response.status_code == 200
        body = response.json()
        assert body["entries"] == []
        assert body["summary"] == "No material analytical changes since your previous review."
        assert "generatedAt" in body


class TestBaselineIsExcludedFromTheBrief:
    def test_a_freshly_imported_holding_with_no_prior_review_is_not_in_the_brief(self, client):
        _import_holding(client, "AAPL")
        # No explicit "review" GET yet -- the very first Daily Brief
        # request is itself what triggers the first-ever build, so this
        # already IS the baseline read; nothing to compare against yet.
        response = client.get("/daily-brief")
        assert response.status_code == 200
        assert response.json()["entries"] == []


class TestOneCompanyChanged:
    def test_a_real_growth_transition_appears_with_the_full_structured_shape(self, client):
        case_id = _import_holding(client, "NVDA")
        _add_records(
            client,
            "NVDA",
            [
                _growth_record(company="NVDA", identifier="fy22", period_end=date(2022, 12, 31), revenue=1250.0, free_cash_flow=300.0),
                _growth_record(company="NVDA", identifier="fy23", period_end=date(2023, 12, 31), revenue=1100.0, free_cash_flow=240.0),
                _growth_record(company="NVDA", identifier="fy24", period_end=date(2024, 12, 31), revenue=1000.0, free_cash_flow=200.0),
            ],
        )
        client.get("/daily-brief")  # establish baseline for this Case

        _add_records(
            client,
            "NVDA",
            [
                _growth_record(company="NVDA", identifier="fy25", period_end=date(2025, 12, 31), revenue=2000.0, free_cash_flow=600.0),
                _growth_record(company="NVDA", identifier="fy26", period_end=date(2026, 12, 31), revenue=3000.0, free_cash_flow=900.0),
            ],
        )
        response = client.get("/daily-brief")
        body = response.json()
        assert len(body["entries"]) == 1
        entry = body["entries"][0]
        assert entry["caseId"] == case_id
        assert entry["ticker"] == "NVDA"
        assert entry["headline"]
        assert entry["changeSummary"]
        assert entry["whyItMatters"]
        assert entry["thesisImpact"] in ("strengthened", "weakened", "mixed", "unchanged")
        assert isinstance(entry["changes"], list)
        assert len(entry["changes"]) >= 1
        for change in entry["changes"]:
            assert {"id", "category", "direction", "previousState", "currentState"} <= set(change.keys())


class TestUnchangedCompanyIsExcluded:
    def test_repeated_reads_with_no_new_data_never_populate_the_brief(self, client):
        _import_holding(client, "AAPL")
        client.get("/daily-brief")
        response = client.get("/daily-brief")
        assert response.json()["entries"] == []
        response_again = client.get("/daily-brief")
        assert response_again.json()["entries"] == []


class TestOrdering:
    def test_multiple_changed_companies_are_alphabetically_ordered(self, client):
        # `/alpha-portfolio/import` replaces the whole portfolio state --
        # all three holdings must be imported in one call.
        response = client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [
                    {"ticker": "MSFT", "weightPercent": 34.0},
                    {"ticker": "AAPL", "weightPercent": 33.0},
                    {"ticker": "META", "weightPercent": 33.0},
                ]
            },
        )
        assert response.status_code == 201, response.text

        for ticker in ("MSFT", "AAPL", "META"):
            _add_records(
                client,
                ticker,
                [
                    _growth_record(company=ticker, identifier=f"{ticker}-fy22", period_end=date(2022, 12, 31), revenue=1250.0, free_cash_flow=300.0),
                    _growth_record(company=ticker, identifier=f"{ticker}-fy23", period_end=date(2023, 12, 31), revenue=1100.0, free_cash_flow=240.0),
                    _growth_record(company=ticker, identifier=f"{ticker}-fy24", period_end=date(2024, 12, 31), revenue=1000.0, free_cash_flow=200.0),
                ],
            )
        client.get("/daily-brief")  # baseline for all three

        for ticker in ("MSFT", "AAPL", "META"):
            _add_records(
                client,
                ticker,
                [
                    _growth_record(company=ticker, identifier=f"{ticker}-fy25", period_end=date(2025, 12, 31), revenue=2000.0, free_cash_flow=600.0),
                    _growth_record(company=ticker, identifier=f"{ticker}-fy26", period_end=date(2026, 12, 31), revenue=3000.0, free_cash_flow=900.0),
                ],
            )
        response = client.get("/daily-brief")
        tickers = [e["ticker"] for e in response.json()["entries"]]
        assert tickers == ["AAPL", "META", "MSFT"]
