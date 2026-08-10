"""Company Data Foundation v1 -- `GET /cases/{case_id}/analysis` end to
end with the richer financial fields this sprint adds: real SEC EDGAR-
shaped `FINANCIAL_STATEMENT` records (operating income, net income,
EPS, cash, total debt, shares outstanding) flow all the way through to
`FinancialPeriodView`/`MarketSnapshotView`, and Growth/Capital
Allocation/Financial Risk/Valuation consume the richer facts. Follows
the exact fixture/helper pattern `test_investment_case_analysis_v1_scenarios.py`
already established.
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


def _snapshot_document(*, ticker: str, **metadata) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=f"{ticker}:snapshot:2026-08-09",
        company=ticker,
        source_kind="market_data_snapshot",
        published_at=_NOW,
        provider_id="alpha_vantage",
        raw_reference="https://example.test/quote",
        content_hash=f"hash-snapshot-{ticker}",
        language="en",
        period_start=_NOW.date(),
        period_end=_NOW.date(),
        metadata=metadata,
    )


def _profile_document(*, ticker: str, **metadata) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=f"{ticker}:profile",
        company=ticker,
        source_kind="company_profile",
        published_at=_NOW,
        provider_id="alpha_vantage",
        raw_reference="https://example.test/overview",
        content_hash=f"hash-profile-{ticker}",
        language="en",
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


class TestRicherFinancialHistoryExposedByTheApi:
    def test_new_fields_appear_in_the_financial_history_response(self, client):
        case_id = _import_holding(client, "AAPL")
        _persist(
            client,
            _statement_document(
                ticker="AAPL",
                period_end=date(2024, 12, 31),
                revenue=1000.0,
                operating_income=250.0,
                net_income=200.0,
                eps=2.5,
                free_cash_flow=300.0,
                cash=900.0,
                total_debt=550.0,
                shares_outstanding=1_000_000.0,
                currency="USD",
            ),
        )
        body = client.get(f"/cases/{case_id}/analysis").json()
        (period,) = body["financialHistory"]
        assert period["operatingIncome"] == 250.0
        assert period["netIncome"] == 200.0
        assert period["eps"] == 2.5
        assert period["cash"] == 900.0
        assert period["totalDebt"] == 550.0
        assert period["sharesOutstanding"] == 1_000_000.0

    def test_missing_new_fields_are_null_never_zero(self, client):
        case_id = _import_holding(client, "AAPL")
        _persist(client, _statement_document(ticker="AAPL", period_end=date(2024, 12, 31), revenue=1000.0))
        body = client.get(f"/cases/{case_id}/analysis").json()
        (period,) = body["financialHistory"]
        assert period["revenue"] == 1000.0
        for field_name in ("operatingIncome", "netIncome", "eps", "cash", "totalDebt", "sharesOutstanding"):
            assert period[field_name] is None

    def test_market_cap_is_derived_in_the_market_snapshot_response(self, client):
        case_id = _import_holding(client, "AAPL")
        _persist(client, _snapshot_document(ticker="AAPL", share_price=500.0, shares_outstanding=7_000_000.0, currency="USD"))
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert body["marketSnapshot"]["marketCap"] == 3_500_000_000.0

    def test_company_profile_exposes_currency_and_fiscal_year_end(self, client):
        case_id = _import_holding(client, "AAPL")
        _persist(client, _profile_document(ticker="AAPL", name="Apple Inc.", currency="USD", fiscal_year_end="September"))
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert body["companyProfile"]["currency"] == "USD"
        assert body["companyProfile"]["fiscalYearEnd"] == "September"


class TestRicherDataFlowsIntoEvaluators:
    def test_growth_becomes_evaluable_with_two_real_periods(self, client):
        case_id = _import_holding(client, "AAPL")
        _persist(
            client,
            _statement_document(ticker="AAPL", period_end=date(2023, 12, 31), revenue=900.0, free_cash_flow=200.0),
            _statement_document(ticker="AAPL", period_end=date(2024, 12, 31), revenue=1000.0, free_cash_flow=250.0),
        )
        body = client.get(f"/cases/{case_id}/analysis").json()
        growth = next(f for f in body["businessAnalysis"]["findings"] if f["kind"] == "growth")
        assert growth["status"] == "strong"

    def test_capital_allocation_surfaces_share_count_history_as_informational(self, client):
        case_id = _import_holding(client, "AAPL")
        _persist(
            client,
            _statement_document(
                ticker="AAPL",
                period_end=date(2024, 12, 31),
                share_buybacks=500.0,
                share_issuance=50.0,
                debt_repayment=300.0,
                debt_issuance=100.0,
                shares_outstanding=1_000_000.0,
            ),
        )
        body = client.get(f"/cases/{case_id}/analysis").json()
        capital_allocation = next(f for f in body["businessAnalysis"]["findings"] if f["kind"] == "capital_allocation")
        assert capital_allocation["status"] == "strong"
        assert "missing_share_count_history" not in capital_allocation["missingEvidence"]

    def test_financial_risk_escalates_to_high_on_a_real_rising_debt_trend(self, client):
        case_id = _import_holding(client, "AAPL")
        _persist(
            client,
            _statement_document(ticker="AAPL", period_end=date(2022, 12, 31), total_debt=100.0),
            _statement_document(ticker="AAPL", period_end=date(2023, 12, 31), total_debt=200.0),
            _statement_document(ticker="AAPL", period_end=date(2024, 12, 31), total_debt=300.0),
        )
        body = client.get(f"/cases/{case_id}/analysis").json()
        financial_risk = next(f for f in body["risk"]["findings"] if f["category"] == "financial_risk")
        assert financial_risk["status"] == "high"

    def test_current_fcf_yield_is_computable_with_one_period_of_richer_data(self, client):
        """A single fundamentals period plus a market snapshot is not
        enough for a real UNDERVALUED/FAIRLY_VALUED/EXPENSIVE
        classification (no history to be relative *to* -- doctrine,
        unchanged by this sprint), but `currentYield` itself is real
        and populated the moment FCF, share price, and share count all
        exist -- exactly ATLAS-032's own "Current FCF Yield does not
        require a historical range" rule."""
        case_id = _import_holding(client, "AAPL")
        _persist(
            client,
            _statement_document(ticker="AAPL", period_end=date(2024, 12, 31), free_cash_flow=300.0),
            _snapshot_document(ticker="AAPL", share_price=100.0, shares_outstanding=1_000_000.0, currency="USD"),
        )
        body = client.get(f"/cases/{case_id}/analysis").json()
        fcf_yield = next(f for f in body["valuation"]["findings"] if f["kind"] == "fcf_yield_relative")
        assert fcf_yield["status"] == "insufficient_input"
        assert fcf_yield["currentYield"] is not None


class TestUnsupportedQualitativeDimensionsStayHonest:
    """Richer financial data must never bleed into the four categories
    that genuinely require qualitative information Atlas does not
    have."""

    def test_business_model_competitive_position_management_durability_stay_insufficient(self, client):
        case_id = _import_holding(client, "AAPL")
        _persist(
            client,
            _statement_document(
                ticker="AAPL",
                period_end=date(2024, 12, 31),
                revenue=1000.0,
                operating_income=250.0,
                net_income=200.0,
                eps=2.5,
                free_cash_flow=300.0,
                cash=900.0,
                total_debt=550.0,
                shares_outstanding=1_000_000.0,
            ),
        )
        body = client.get(f"/cases/{case_id}/analysis").json()
        for category in ("business_model", "competitive_position", "management", "durability"):
            finding = next(f for f in body["businessAnalysis"]["findings"] if f["kind"] == category)
            assert finding["status"] == "insufficient_input"


class TestChangeIntelligenceStaysHonestAboutBackfilledData:
    """Repeated analysis over unchanged, richer data must remain
    deterministic and idempotent -- opening/re-reading the Investment
    Case never fabricates a change."""

    def test_repeated_reads_over_identical_richer_data_report_no_change(self, client):
        case_id = _import_holding(client, "AAPL")
        _persist(
            client,
            _statement_document(
                ticker="AAPL", period_end=date(2024, 12, 31), revenue=1000.0, total_debt=550.0, cash=900.0
            ),
        )
        client.get(f"/cases/{case_id}/analysis")  # establish baseline
        second = client.get(f"/cases/{case_id}/analysis").json()
        assert second["isBaselineCase"] is False
        assert second["latestChanges"] == []
        assert second["thesisChange"] == "unchanged"
