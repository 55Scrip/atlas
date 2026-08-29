"""Real-data-shaped scenarios (ATLAS-031, Phases 34-38).

Not a provider test -- these construct `RawBusinessDocument`s shaped
exactly like what `SecEdgarFundamentalsProvider`/
`AlphaVantageMarketDataProvider` actually produce (confirmed live
against real AAPL data during this sprint's audit), run them through
the real, unmodified `business_data.pipeline.ingest` and
`assemble_analysis`, and assert on the real Growth/Capital
Allocation/Valuation/Risk/Conviction conclusions that result. Proves
the full canonical chain behaves correctly on realistic external data,
without any live network call (Phase 32).
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.analysis_engine.business_contracts import BusinessCategory
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.business_data.versioning import latest_versions
from atlas.analysis_engine.pipeline import assemble_analysis
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.risk.contracts import RiskStatus
from atlas.analysis_engine.valuation.contracts import ValuationMethodKind, ValuationStatus
from tests.unit.analysis_engine._fixtures import run_minimal

_EVALUATED_AT = datetime(2026, 8, 9, tzinfo=timezone.utc)


def _dt(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


def _fundamentals_doc(*, period_end: str, revenue: float, fcf: float | None = None, buybacks: float | None = None, issuance: float | None = None, debt_issuance: float | None = None, debt_repayment: float | None = None, total_debt: float | None = None, content_hash: str | None = None, published_at: datetime | None = None) -> RawBusinessDocument:
    metadata: dict = {"revenue": revenue, "currency": "USD"}
    if fcf is not None:
        metadata["free_cash_flow"] = fcf
    if buybacks is not None:
        metadata["share_buybacks"] = buybacks
    if issuance is not None:
        metadata["share_issuance"] = issuance
    if debt_issuance is not None:
        metadata["debt_issuance"] = debt_issuance
    if debt_repayment is not None:
        metadata["debt_repayment"] = debt_repayment
    if total_debt is not None:
        metadata["total_debt"] = total_debt
    return RawBusinessDocument(
        identifier=f"TEST:FY:{period_end}",
        company="TEST",
        source_kind="financial_statement",
        # ATLAS-032: a real SEC filing date, ~6 weeks after period end
        # by default -- callers pairing this with a market observation
        # override this to keep the no-look-ahead eligibility rule
        # (published_at <= observation date) satisfied.
        published_at=published_at if published_at is not None else _EVALUATED_AT,
        provider_id="sec_edgar",
        raw_reference="https://example.test/filing",
        content_hash=content_hash or f"hash-{period_end}-{revenue}",
        language="en",
        period_start=date(int(period_end[:4]) - 1, 1, 1),
        period_end=date.fromisoformat(period_end),
        metadata=metadata,
    )


def _market_doc(*, snapshot: str, price: float, shares: float | None = None, content_hash: str | None = None) -> RawBusinessDocument:
    metadata: dict = {"share_price": price, "currency": "USD"}
    if shares is not None:
        metadata["shares_outstanding"] = shares
    return RawBusinessDocument(
        identifier=f"TEST:snapshot:{snapshot}",
        company="TEST",
        source_kind="market_data_snapshot",
        published_at=_EVALUATED_AT,
        provider_id="alpha_vantage",
        raw_reference="https://example.test/quote",
        content_hash=content_hash or f"hash-{snapshot}-{price}",
        language="en",
        period_start=date.fromisoformat(snapshot),
        period_end=date.fromisoformat(snapshot),
        metadata=metadata,
    )


def _ingest_all(*documents: RawBusinessDocument) -> tuple:
    records: list = []
    for document in documents:
        result = ingest(document, existing_records=tuple(records), evaluated_at=_EVALUATED_AT)
        assert isinstance(result, IngestedRecord), result
        records.append(result.record)
    return latest_versions(tuple(records))


def _assemble(records: tuple):
    engine_input, decision_output = run_minimal()
    return assemble_analysis(
        engine_input, decision_output, is_thesis_stale=False, business_records=records, generated_at=_EVALUATED_AT
    )


def _finding(analysis, category: BusinessCategory):
    return next(f for f in analysis.business_analysis.findings if f.kind is category)


class TestGrowthRealDataShapes:
    def test_consistently_growing_revenue_and_fcf_is_strong(self):
        records = _ingest_all(
            _fundamentals_doc(period_end="2021-12-31", revenue=100, fcf=20),
            _fundamentals_doc(period_end="2022-12-31", revenue=110, fcf=25),
            _fundamentals_doc(period_end="2023-12-31", revenue=125, fcf=30),
        )
        analysis = _assemble(records)
        growth = _finding(analysis, BusinessCategory.GROWTH)
        assert growth.status.value == "strong"

    def test_declining_revenue_and_fcf_is_weak(self):
        records = _ingest_all(
            _fundamentals_doc(period_end="2021-12-31", revenue=125, fcf=30),
            _fundamentals_doc(period_end="2022-12-31", revenue=110, fcf=25),
            _fundamentals_doc(period_end="2023-12-31", revenue=100, fcf=20),
        )
        analysis = _assemble(records)
        growth = _finding(analysis, BusinessCategory.GROWTH)
        assert growth.status.value == "weak"

    def test_mixed_revenue_and_fcf_is_moderate(self):
        records = _ingest_all(
            _fundamentals_doc(period_end="2021-12-31", revenue=100, fcf=30),
            _fundamentals_doc(period_end="2022-12-31", revenue=110, fcf=25),
            _fundamentals_doc(period_end="2023-12-31", revenue=125, fcf=20),
        )
        analysis = _assemble(records)
        growth = _finding(analysis, BusinessCategory.GROWTH)
        assert growth.status.value == "moderate"

    def test_one_metric_missing_still_produces_partial_confidence_growth(self):
        """STRONG requires both Revenue and FCF present and increasing
        (`set(trends) == set(_SUPPORTED_KINDS)`) -- Revenue-only still
        reaches a real MODERATE conclusion with PARTIAL confidence,
        never fabricating FCF's own missing side."""
        records = _ingest_all(
            _fundamentals_doc(period_end="2022-12-31", revenue=100),
            _fundamentals_doc(period_end="2023-12-31", revenue=110),
        )
        analysis = _assemble(records)
        growth = _finding(analysis, BusinessCategory.GROWTH)
        assert growth.status.value == "moderate"
        assert growth.confidence.value == "partial"

    def test_insufficient_historical_periods_is_insufficient_input(self):
        records = _ingest_all(_fundamentals_doc(period_end="2023-12-31", revenue=100))
        analysis = _assemble(records)
        growth = _finding(analysis, BusinessCategory.GROWTH)
        assert growth.status.value == "insufficient_input"

    def test_negative_fcf_trend_still_evaluated_growth_reads_direction_not_sign(self):
        records = _ingest_all(
            _fundamentals_doc(period_end="2022-12-31", revenue=100, fcf=-50),
            _fundamentals_doc(period_end="2023-12-31", revenue=110, fcf=-20),
        )
        analysis = _assemble(records)
        growth = _finding(analysis, BusinessCategory.GROWTH)
        assert growth.status.value == "strong"  # both metrics increased, even though FCF is still negative


class TestCapitalAllocationRealDataShapes:
    def test_buybacks_exceed_issuance_and_debt_is_falling_is_strong(self):
        records = _ingest_all(
            _fundamentals_doc(period_end="2022-12-31", revenue=100, total_debt=150),
            _fundamentals_doc(period_end="2023-12-31", revenue=100, buybacks=100, issuance=10, total_debt=50),
        )
        analysis = _assemble(records)
        capital_allocation = _finding(analysis, BusinessCategory.CAPITAL_ALLOCATION)
        assert capital_allocation.status.value == "strong"

    def test_issuance_exceeds_buybacks_is_weak(self):
        records = _ingest_all(
            _fundamentals_doc(period_end="2023-12-31", revenue=100, buybacks=10, issuance=100, debt_issuance=5, debt_repayment=50)
        )
        analysis = _assemble(records)
        capital_allocation = _finding(analysis, BusinessCategory.CAPITAL_ALLOCATION)
        assert capital_allocation.status.value == "weak"

    def test_rising_debt_alongside_dilution_is_weak(self):
        records = _ingest_all(
            _fundamentals_doc(period_end="2022-12-31", revenue=100, buybacks=10, issuance=100, total_debt=50),
            _fundamentals_doc(period_end="2023-12-31", revenue=100, buybacks=10, issuance=100, total_debt=150),
        )
        analysis = _assemble(records)
        capital_allocation = _finding(analysis, BusinessCategory.CAPITAL_ALLOCATION)
        assert capital_allocation.status.value == "weak"

    def test_only_buybacks_reported_neither_signal_is_computable(self):
        """Buybacks alone cannot make the capital_return signal
        computable (that needs the issuance side too) -- neither
        signal computes, but a real fact exists, so confidence is NONE
        (not NOT_APPLICABLE, and not fabricated as PARTIAL)."""
        records = _ingest_all(_fundamentals_doc(period_end="2023-12-31", revenue=100, buybacks=50))
        analysis = _assemble(records)
        capital_allocation = _finding(analysis, BusinessCategory.CAPITAL_ALLOCATION)
        assert capital_allocation.status.value == "insufficient_input"
        assert capital_allocation.confidence.value == "none"

    def test_no_capital_allocation_signal_coverage_at_all(self):
        records = _ingest_all(_fundamentals_doc(period_end="2023-12-31", revenue=100))
        analysis = _assemble(records)
        capital_allocation = _finding(analysis, BusinessCategory.CAPITAL_ALLOCATION)
        assert capital_allocation.status.value == "insufficient_input"
        assert capital_allocation.confidence.value == "not_applicable"


class TestValuationRealDataShapes:
    def _fcf_finding(self, analysis):
        return next(f for f in analysis.valuation_engine.findings if f.kind is ValuationMethodKind.FCF_YIELD_RELATIVE)

    def test_current_yield_above_historical_range_is_undervalued(self):
        records = _ingest_all(
            _fundamentals_doc(period_end="2021-12-31", revenue=100, fcf=10, published_at=_dt(2022, 2, 15)),
            _fundamentals_doc(period_end="2022-12-31", revenue=100, fcf=10, published_at=_dt(2023, 2, 15)),
            _market_doc(snapshot="2022-06-01", price=200, shares=100),
            _market_doc(snapshot="2023-06-01", price=50, shares=100),
        )
        analysis = _assemble(records)
        assert self._fcf_finding(analysis).status is ValuationStatus.UNDERVALUED

    def test_current_yield_below_historical_range_is_expensive(self):
        records = _ingest_all(
            _fundamentals_doc(period_end="2021-12-31", revenue=100, fcf=10, published_at=_dt(2022, 2, 15)),
            _fundamentals_doc(period_end="2022-12-31", revenue=100, fcf=10, published_at=_dt(2023, 2, 15)),
            _market_doc(snapshot="2022-06-01", price=50, shares=100),
            _market_doc(snapshot="2023-06-01", price=200, shares=100),
        )
        analysis = _assemble(records)
        assert self._fcf_finding(analysis).status is ValuationStatus.EXPENSIVE

    def test_negative_fcf_period_is_insufficient_input(self):
        records = _ingest_all(
            _fundamentals_doc(period_end="2023-12-31", revenue=100, fcf=-10),
            _market_doc(snapshot="2023-12-31", price=50, shares=100),
        )
        analysis = _assemble(records)
        assert self._fcf_finding(analysis).status is ValuationStatus.INSUFFICIENT_INPUT

    def test_missing_shares_outstanding_is_insufficient_input(self):
        """Alpha Vantage OVERVIEW momentarily unavailable -- price alone
        cannot compute a market cap."""
        records = _ingest_all(
            _fundamentals_doc(period_end="2022-12-31", revenue=100, fcf=10),
            _fundamentals_doc(period_end="2023-12-31", revenue=100, fcf=10),
            _market_doc(snapshot="2023-12-31", price=50),
        )
        analysis = _assemble(records)
        assert self._fcf_finding(analysis).status is ValuationStatus.INSUFFICIENT_INPUT

    def test_insufficient_historical_periods_is_insufficient_input(self):
        records = _ingest_all(
            _fundamentals_doc(period_end="2023-12-31", revenue=100, fcf=10),
            _market_doc(snapshot="2023-12-31", price=50, shares=100),
        )
        analysis = _assemble(records)
        assert self._fcf_finding(analysis).status is ValuationStatus.INSUFFICIENT_INPUT

    def test_no_market_data_at_all_is_insufficient_input(self):
        records = _ingest_all(
            _fundamentals_doc(period_end="2022-12-31", revenue=100, fcf=10),
            _fundamentals_doc(period_end="2023-12-31", revenue=100, fcf=10),
        )
        analysis = _assemble(records)
        assert self._fcf_finding(analysis).status is ValuationStatus.INSUFFICIENT_INPUT


class TestRiskDerivesOnlyFromUpstreamConclusions:
    def test_weak_growth_produces_high_business_risk(self):
        records = _ingest_all(
            _fundamentals_doc(period_end="2022-12-31", revenue=125, fcf=30),
            _fundamentals_doc(period_end="2023-12-31", revenue=100, fcf=20),
        )
        analysis = _assemble(records)
        business_risk = next(f for f in analysis.risk_analysis.findings if f.category is RiskCategory.BUSINESS_RISK)
        assert business_risk.status is RiskStatus.HIGH

    def test_strong_growth_produces_low_business_risk(self):
        records = _ingest_all(
            _fundamentals_doc(period_end="2022-12-31", revenue=100, fcf=20),
            _fundamentals_doc(period_end="2023-12-31", revenue=125, fcf=30),
        )
        analysis = _assemble(records)
        business_risk = next(f for f in analysis.risk_analysis.findings if f.category is RiskCategory.BUSINESS_RISK)
        assert business_risk.status is RiskStatus.LOW

    def test_expensive_valuation_produces_high_valuation_risk(self):
        records = _ingest_all(
            _fundamentals_doc(period_end="2021-12-31", revenue=100, fcf=10, published_at=_dt(2022, 2, 15)),
            _fundamentals_doc(period_end="2022-12-31", revenue=100, fcf=10, published_at=_dt(2023, 2, 15)),
            _market_doc(snapshot="2022-06-01", price=50, shares=100),
            _market_doc(snapshot="2023-06-01", price=200, shares=100),
        )
        analysis = _assemble(records)
        valuation_risk = next(f for f in analysis.risk_analysis.findings if f.category is RiskCategory.VALUATION_RISK)
        assert valuation_risk.status is RiskStatus.HIGH


class TestConvictionImpactOfRealData:
    def test_real_conclusive_business_and_valuation_data_does_not_exceed_moderate_ceiling(self):
        """ATLAS-026's structural MODERATE ceiling (unresolved
        portfolio-factor/durability open questions) is untouched by
        real data becoming available -- Conviction still cannot exceed
        MODERATE through the real pipeline, exactly as ATLAS-027/030
        already found."""
        records = _ingest_all(
            _fundamentals_doc(period_end="2021-12-31", revenue=100, fcf=10),
            _fundamentals_doc(period_end="2022-12-31", revenue=110, fcf=15),
            _fundamentals_doc(period_end="2023-12-31", revenue=125, fcf=20),
            _market_doc(snapshot="2021-12-31", price=200, shares=100),
            _market_doc(snapshot="2023-12-31", price=50, shares=100),
        )
        analysis = _assemble(records)
        assert analysis.conviction.level.value in ("moderate", "insufficient_evidence", "low")
        assert analysis.conviction.level.value not in ("high", "very_high")


class TestRestatementFlowsThroughToAnalysis:
    def test_latest_version_of_a_restated_period_is_what_analysis_sees(self):
        original = _fundamentals_doc(period_end="2023-12-31", revenue=100, fcf=10, content_hash="original")
        restated = _fundamentals_doc(period_end="2023-12-31", revenue=95, fcf=8, content_hash="restated")

        first_pass = _ingest_all(_fundamentals_doc(period_end="2022-12-31", revenue=90, fcf=5), original)
        # Simulate a second refresh where the same period is restated --
        # existing_records includes the first pass's persisted history.
        result = ingest(restated, existing_records=first_pass, evaluated_at=_EVALUATED_AT)
        assert isinstance(result, IngestedRecord)
        assert result.record.version.version_number == 2

        all_records = latest_versions(first_pass + (result.record,))
        analysis = _assemble(all_records)
        growth = _finding(analysis, BusinessCategory.GROWTH)
        # 90 -> 95 is still growth (restated 100 -> 95 would have been a
        # smaller increase but still an increase over 90)
        assert growth.status.value in ("strong", "moderate")
