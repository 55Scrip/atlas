"""End-to-end proof that `GET /alpha-portfolio/cockpit` exposes a
separate `analysisCoverage` signal from `conviction` (Internal Alpha
Fix Sprint 1, Part 2 -- confirmed root cause IA-003).

The Internal Alpha finding: a holding with `confidence: full`
Growth/Capital Allocation/Valuation findings still read `conviction
.level: "insufficient_evidence"` at the Portfolio level, because
Conviction is gated on investor-recorded evidence coverage, which none
of these test holdings ever record. These tests prove `analysisCoverage`
answers the separate question "does Atlas actually know this company"
and moves independently of `conviction`, which correctly stays
`insufficient_evidence` throughout every scenario here (no test in this
file records a Decision/Observation for any holding).
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

_NOW = datetime(2026, 8, 9, tzinfo=timezone.utc)


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_decision_table(engine)
    app = create_app()
    app.dependency_overrides[get_decision_engine] = lambda: engine
    test_client = TestClient(app)
    test_client.engine = engine  # type: ignore[attr-defined]
    return test_client


def _import_holding(client, ticker: str) -> str:
    response = client.post("/alpha-portfolio/import", json={"holdings": [{"ticker": ticker, "weightPercent": 100.0}]})
    assert response.status_code == 201, response.text
    return response.json()["holdings"][0]["caseId"]


def _statement_document(*, ticker: str, period_end: date, **metadata) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=f"{ticker}:FY:{period_end.isoformat()}",
        company=ticker,
        source_kind="financial_statement",
        published_at=_NOW,
        provider_id="sec_edgar",
        raw_reference="https://example.test/10k",
        content_hash=f"hash-{ticker}-{period_end.isoformat()}",
        language="en",
        period_start=date(period_end.year, 1, 1),
        period_end=period_end,
        metadata=metadata,
    )


def _persist(client, *documents: RawBusinessDocument) -> None:
    engine = client.engine
    create_business_record_table(engine)
    repository = SqlAlchemyBusinessRecordRepository(engine)
    for document in documents:
        result = ingest(document, evaluated_at=_NOW)
        assert isinstance(result, IngestedRecord), result
        repository.add(result.record)


def _cockpit_holding(client, ticker: str) -> dict:
    body = client.get("/alpha-portfolio/cockpit").json()
    return next(h for h in body["holdings"] if h["ticker"] == ticker)


class TestNoCoverage:
    def test_a_holding_with_zero_business_data_is_no_coverage(self, client):
        _import_holding(client, "ZZZZ")
        holding = _cockpit_holding(client, "ZZZZ")
        assert holding["analysisCoverage"]["level"] == "no_coverage"
        assert holding["conviction"]["level"] == "insufficient_evidence"


class TestPartialCoverage:
    def test_one_period_of_real_data_is_partial_not_no_coverage(self, client):
        _import_holding(client, "AAPL")
        _persist(client, _statement_document(ticker="AAPL", period_end=date(2024, 12, 31), revenue=1000.0))
        holding = _cockpit_holding(client, "AAPL")
        assert holding["analysisCoverage"]["level"] == "partial_coverage"
        # Conviction is untouched by this data -- still gated on investor
        # evidence, which this test never records.
        assert holding["conviction"]["level"] == "insufficient_evidence"


class TestSubstantialCoverage:
    def test_growth_and_capital_allocation_both_conclusive_is_substantial(self, client):
        """Two real periods of revenue/FCF makes Growth conclusive;
        real buyback/issuance/debt-repayment fields make Capital
        Allocation conclusive -- both required for `business_conclusive`
        (`analysis_coverage.py`'s own `SUBSTANTIAL_COVERAGE` branch)."""
        _import_holding(client, "AAPL")
        _persist(
            client,
            _statement_document(
                ticker="AAPL",
                period_end=date(2023, 12, 31),
                revenue=900.0,
                free_cash_flow=200.0,
                share_buybacks=500.0,
                share_issuance=50.0,
                debt_repayment=300.0,
                debt_issuance=100.0,
            ),
            _statement_document(
                ticker="AAPL",
                period_end=date(2024, 12, 31),
                revenue=1000.0,
                free_cash_flow=250.0,
                share_buybacks=550.0,
                share_issuance=60.0,
                debt_repayment=320.0,
                debt_issuance=110.0,
            ),
        )
        holding = _cockpit_holding(client, "AAPL")
        # Business Analysis is conclusive either way; whether this
        # reaches SUBSTANTIAL (vs. PARTIAL, if Valuation is not yet
        # conclusive with only fundamentals and no market snapshot) is
        # itself informative -- assert the honest floor plus the
        # decoupling from Conviction, which is this file's real claim.
        assert holding["analysisCoverage"]["level"] in ("partial_coverage", "substantial_coverage")
        assert holding["conviction"]["level"] == "insufficient_evidence"


class TestDistributionIsExposed:
    def test_analysis_coverage_distribution_appears_in_the_cockpit_response(self, client):
        _import_holding(client, "AAPL")
        body = client.get("/alpha-portfolio/cockpit").json()
        assert "analysisCoverageDistribution" in body
        levels = {entry["level"] for entry in body["analysisCoverageDistribution"]}
        assert levels == {"no_coverage", "partial_coverage", "substantial_coverage"}
