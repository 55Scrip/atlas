"""History v1 -- `GET /history/analysis`, powered by
`atlas.alpha.investment_case_history.service.InvestmentCaseHistoryService`.
Exercises the real HTTP surface end-to-end: real Portfolio/Watchlist
imports, real Investment Case analysis builds (via `GET /cases/{case_id}
/analysis`, which is the only endpoint in this whole test file that may
create a snapshot), and a read-only `GET /history/analysis` that must
never itself create one. Follows the exact fixture/helper pattern
`test_daily_brief_v1_scenarios.py` already established.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
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


def _weaken_growth(client, ticker: str) -> None:
    _add_records(
        client,
        ticker,
        [
            _growth_record(company=ticker, identifier=f"{ticker}-fy22", period_end=date(2022, 12, 31), revenue=1250.0, free_cash_flow=300.0),
            _growth_record(company=ticker, identifier=f"{ticker}-fy23", period_end=date(2023, 12, 31), revenue=1100.0, free_cash_flow=240.0),
            _growth_record(company=ticker, identifier=f"{ticker}-fy24", period_end=date(2024, 12, 31), revenue=1000.0, free_cash_flow=200.0),
        ],
    )


def _strengthen_growth(client, ticker: str) -> None:
    _add_records(
        client,
        ticker,
        [
            _growth_record(company=ticker, identifier=f"{ticker}-fy25", period_end=date(2025, 12, 31), revenue=2000.0, free_cash_flow=600.0),
            _growth_record(company=ticker, identifier=f"{ticker}-fy26", period_end=date(2026, 12, 31), revenue=3000.0, free_cash_flow=900.0),
        ],
    )


class TestEmptyHistory:
    """Scenario 1."""

    def test_no_portfolio_or_watchlist_returns_an_empty_history(self, client):
        response = client.get("/history/analysis")
        assert response.status_code == 200
        body = response.json()
        assert body["entries"] == []
        assert "generatedAt" in body


class TestBaselineOnly:
    """Scenario 2."""

    def test_one_analysis_produces_a_single_baseline_entry(self, client):
        case_id = _import_holding(client, "AAPL")
        analysis_response = client.get(f"/cases/{case_id}/analysis")
        assert analysis_response.status_code == 200

        response = client.get("/history/analysis")
        body = response.json()
        assert len(body["entries"]) == 1
        entry = body["entries"][0]
        assert entry["caseId"] == case_id
        assert entry["ticker"] == "AAPL"
        assert entry["isBaseline"] is True
        assert entry["changes"] == []


class TestBaselinePlusTransition:
    """Scenarios 3/9: a growth transition after the baseline produces a
    second, non-baseline timeline entry with the full structured shape."""

    def test_a_growth_transition_appears_as_a_second_entry(self, client):
        case_id = _import_holding(client, "NVDA")
        _weaken_growth(client, "NVDA")
        client.get(f"/cases/{case_id}/analysis")  # establish baseline

        _strengthen_growth(client, "NVDA")
        client.get(f"/cases/{case_id}/analysis")  # review the new data
        response = client.get("/history/analysis")
        body = response.json()
        assert len(body["entries"]) == 2
        # Newest first.
        newest, oldest = body["entries"]
        assert newest["isBaseline"] is False
        assert newest["caseId"] == case_id
        assert newest["thesisImpact"] in ("strengthened", "weakened", "mixed", "unchanged")
        assert len(newest["changes"]) >= 1
        for change in newest["changes"]:
            assert {"id", "category", "direction", "previousState", "currentState"} <= set(change.keys())
        assert oldest["isBaseline"] is True


class TestReadOnly:
    """Scenarios 5/6/27: repeated `GET /history/analysis` calls never
    create a new snapshot or a new ChangeFinding row."""

    def test_repeated_reads_never_change_the_response(self, client):
        case_id = _import_holding(client, "AAPL")
        _weaken_growth(client, "AAPL")
        client.get(f"/cases/{case_id}/analysis")
        _strengthen_growth(client, "AAPL")
        client.get(f"/cases/{case_id}/analysis")

        first = client.get("/history/analysis").json()
        for _ in range(5):
            client.get("/history/analysis")
        second = client.get("/history/analysis").json()
        assert first["entries"] == second["entries"]
        assert len(second["entries"]) == 2


class TestHistoricalStateIsNotRecomputed:
    """Scenario 7/8: opening History after new, unreviewed data has
    arrived must not show that new state as if it were already part of
    the timeline -- only an explicit `/cases/{case_id}/analysis` call
    (an Investment Case build, never History itself) advances it."""

    def test_new_unreviewed_data_does_not_appear_until_analysis_is_rebuilt(self, client):
        case_id = _import_holding(client, "AAPL")
        _weaken_growth(client, "AAPL")
        client.get(f"/cases/{case_id}/analysis")  # baseline

        _strengthen_growth(client, "AAPL")  # new data, not yet reviewed
        response = client.get("/history/analysis")
        assert len(response.json()["entries"]) == 1  # still just the baseline

        client.get(f"/cases/{case_id}/analysis")  # now review it
        response = client.get("/history/analysis")
        assert len(response.json()["entries"]) == 2


class TestPortfolioAndWatchlistMix:
    """Scenarios 18/19/20."""

    def test_a_watchlist_only_case_appears(self, client):
        case_id = _add_to_watchlist(client, "META")
        client.get(f"/cases/{case_id}/analysis")
        response = client.get("/history/analysis")
        tickers = [e["ticker"] for e in response.json()["entries"]]
        assert tickers == ["META"]

    def test_portfolio_and_watchlist_cases_are_combined(self, client):
        held_case_id = _import_holding(client, "AAPL")
        watched_case_id = _add_to_watchlist(client, "META")
        client.get(f"/cases/{held_case_id}/analysis")
        client.get(f"/cases/{watched_case_id}/analysis")
        response = client.get("/history/analysis")
        case_ids = {e["caseId"] for e in response.json()["entries"]}
        assert case_ids == {held_case_id, watched_case_id}


class TestProvenance:
    """Scenario 21: each change carries traceable identifiers even
    though the UI never has to show them by default."""

    def test_each_change_carries_a_stable_id_and_category(self, client):
        case_id = _import_holding(client, "NVDA")
        _weaken_growth(client, "NVDA")
        client.get(f"/cases/{case_id}/analysis")
        _strengthen_growth(client, "NVDA")
        client.get(f"/cases/{case_id}/analysis")

        response = client.get("/history/analysis")
        newest = response.json()["entries"][0]
        assert newest["changes"]
        for change in newest["changes"]:
            assert change["id"]
            assert change["category"]


class TestSnapshotDetailReflectsCapturedState:
    """Scenarios 22/23/24: the detail payload for a historical entry
    reflects strengths/risks/open questions/business-category states as
    they were at that point -- structural fields directly off the
    persisted snapshot, present on every entry."""

    def test_baseline_entry_exposes_structural_snapshot_fields(self, client):
        case_id = _import_holding(client, "AAPL")
        client.get(f"/cases/{case_id}/analysis")
        response = client.get("/history/analysis")
        entry = response.json()["entries"][0]
        for field in (
            "strengths",
            "risks",
            "openQuestions",
            "businessCategoryStates",
            "riskCategoryStates",
            "valuationStatus",
            "atlasThesisNarrative",
            "atlasThesisPosture",
        ):
            assert field in entry


class TestOrdering:
    """Scenario 4: multiple entries across Cases are ordered
    newest-first, deterministically."""

    def test_entries_are_ordered_newest_first(self, client):
        aapl_case_id = _import_holding(client, "AAPL")
        client.get(f"/cases/{aapl_case_id}/analysis")

        response = client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [
                    {"ticker": "AAPL", "weightPercent": 50.0},
                    {"ticker": "MSFT", "weightPercent": 50.0},
                ]
            },
        )
        assert response.status_code == 201, response.text
        msft_case_id = next(h["caseId"] for h in response.json()["holdings"] if h["ticker"] == "MSFT")
        client.get(f"/cases/{msft_case_id}/analysis")

        entries = client.get("/history/analysis").json()["entries"]
        captured_at = [e["capturedAt"] for e in entries]
        assert captured_at == sorted(captured_at, reverse=True)


class TestExistingInvestorHistoryUnaffected:
    """Scenario 28: existing Decision/Outcome/Observation endpoints are
    untouched by this sprint -- History v1 is additive."""

    def test_decisions_and_outcomes_endpoints_still_respond(self, client):
        assert client.get("/decisions").status_code == 200
        assert client.get("/outcomes").status_code == 200
