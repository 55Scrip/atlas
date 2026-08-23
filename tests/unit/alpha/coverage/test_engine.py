"""Tests for `atlas.alpha.coverage.engine.assess_coverage` -- exercised
through the real, top-level `assemble_analysis` entry point with real
`BusinessRecord`s, the same convention
`tests/unit/analysis_engine/test_investment_case_synthesis.py` already
establishes -- never a hand-built fake `CanonicalAnalysis`.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.coverage import ConfidenceLevel, DimensionCoverageLevel, assess_coverage
from atlas.alpha.coverage.models import ConfidenceReasonCode
from atlas.analysis_engine.analysis_coverage import AnalysisCoverageLevel
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.pipeline import assemble_analysis
from tests.unit.analysis_engine._fixtures import GENERATED_AT, run_minimal


def _make_record(source_kind, period_end, identifier, *, published_at=GENERATED_AT, **metadata):
    document = RawBusinessDocument(
        identifier=identifier,
        company="ASML",
        source_kind=source_kind,
        published_at=published_at,
        provider_id="structured_test",
        raw_reference=f"ref://{identifier}",
        content_hash=f"hash-{identifier}",
        language="en",
        period_end=period_end,
        metadata=metadata,
    )
    result = ingest(document, evaluated_at=GENERATED_AT)
    assert isinstance(result, IngestedRecord)
    return result.record


def _strong_growth_records():
    return (
        _make_record("annual_report", date(2022, 12, 31), "fy22", revenue=1000.0, free_cash_flow=200.0),
        _make_record("annual_report", date(2023, 12, 31), "fy23", revenue=1100.0, free_cash_flow=240.0),
        _make_record("annual_report", date(2024, 12, 31), "fy24", revenue=1250.0, free_cash_flow=300.0),
    )


def _strong_capital_allocation_records():
    """Real conclusion (STRONG) but no dividend/capex/share-count facts
    at all -- a naturally-occurring "conclusive status with non-empty
    missing_evidence" case, i.e. Partially Available."""
    return (
        _make_record(
            "annual_report", date(2023, 12, 31), "ca23",
            share_buybacks=100.0, share_issuance=10.0, debt_repayment=50.0, debt_issuance=5.0,
        ),
        _make_record(
            "annual_report", date(2024, 12, 31), "ca24",
            share_buybacks=120.0, share_issuance=10.0, debt_repayment=60.0, debt_issuance=5.0,
        ),
    )


def _undervalued_valuation_records():
    return (
        _make_record(
            "annual_report", date(2022, 12, 31), "vfy22",
            published_at=datetime(2023, 2, 15, tzinfo=timezone.utc), free_cash_flow=100.0,
        ),
        _make_record(
            "annual_report", date(2023, 12, 31), "vfy23",
            published_at=datetime(2024, 2, 15, tzinfo=timezone.utc), free_cash_flow=110.0,
        ),
        _make_record(
            "annual_report", date(2024, 12, 31), "vfy24",
            published_at=datetime(2025, 2, 15, tzinfo=timezone.utc), free_cash_flow=200.0,
        ),
        _make_record("market_data_snapshot", date(2023, 3, 1), "vm22", share_price=50.0, shares_outstanding=100.0),
        _make_record("market_data_snapshot", date(2024, 3, 1), "vm23", share_price=52.0, shares_outstanding=100.0),
        _make_record("market_data_snapshot", date(2025, 3, 1), "vm24", share_price=53.0, shares_outstanding=100.0),
    )


def _assemble(records=(), *, is_thesis_stale=False):
    engine_input, output = run_minimal()
    return assemble_analysis(
        engine_input, output, is_thesis_stale=is_thesis_stale, business_records=records, generated_at=GENERATED_AT
    )


class TestNoDataIsHonestlyUnavailable:
    def test_growth_is_unavailable_with_no_records(self):
        assessment = assess_coverage(_assemble(), is_thesis_stale=False)
        growth = next(d for d in assessment.dimensions if d.dimension == "growth")
        assert growth.level is DimensionCoverageLevel.UNAVAILABLE
        assert growth.reasoning

    def test_confidence_is_very_limited_with_no_data_at_all(self):
        assessment = assess_coverage(_assemble(), is_thesis_stale=False)
        assert assessment.overall_confidence is ConfidenceLevel.VERY_LIMITED

    def test_overall_coverage_is_reused_verbatim_from_analysis_coverage(self):
        analysis = _assemble()
        assessment = assess_coverage(analysis, is_thesis_stale=False)
        assert assessment.overall_coverage == analysis.analysis_coverage.level
        assert assessment.overall_coverage is AnalysisCoverageLevel.NO_COVERAGE


class TestStructurallyLockedDimensionsAreNotApplicable:
    def test_business_model_is_not_applicable_not_unavailable(self):
        """Business Model has no evaluator wired in today (no external
        data source connected) -- this is a permanent capability gap,
        never a per-company data gap, so it must read as Not Applicable,
        never Unavailable."""
        assessment = assess_coverage(_assemble(_strong_growth_records()), is_thesis_stale=False)
        business_model = next(d for d in assessment.dimensions if d.dimension == "business_model")
        assert business_model.level is DimensionCoverageLevel.NOT_APPLICABLE
        assert "business_model" in assessment.not_applicable_dimensions
        assert "business_model" not in assessment.missing_dimensions

    def test_durability_is_not_applicable(self):
        assessment = assess_coverage(_assemble(_strong_growth_records()), is_thesis_stale=False)
        durability = next(d for d in assessment.dimensions if d.dimension == "durability")
        assert durability.level is DimensionCoverageLevel.NOT_APPLICABLE


class TestRealConclusionsAreAvailable:
    def test_strong_growth_is_available(self):
        assessment = assess_coverage(_assemble(_strong_growth_records()), is_thesis_stale=False)
        growth = next(d for d in assessment.dimensions if d.dimension == "growth")
        assert growth.level is DimensionCoverageLevel.AVAILABLE
        assert growth.reasoning == ()

    def test_undervalued_valuation_is_available(self):
        assessment = assess_coverage(_assemble(_undervalued_valuation_records()), is_thesis_stale=False)
        fcf = next(d for d in assessment.dimensions if d.dimension == "fcf_yield_relative")
        assert fcf.level is DimensionCoverageLevel.AVAILABLE

    def test_conclusive_status_with_a_real_gap_is_partially_available(self):
        """Capital Allocation reaches STRONG from buyback/debt facts
        alone, but dividend/capex/share-count facts are entirely
        absent -- a real conclusion built from incomplete evidence."""
        assessment = assess_coverage(_assemble(_strong_capital_allocation_records()), is_thesis_stale=False)
        capital_allocation = next(d for d in assessment.dimensions if d.dimension == "capital_allocation")
        assert capital_allocation.level is DimensionCoverageLevel.PARTIALLY_AVAILABLE
        assert capital_allocation.reasoning


class TestThesisRiskIsInsufficientEvidenceNotUnavailable:
    def test_thesis_risk_with_no_investor_evidence_is_insufficient_evidence(self):
        """Thesis Risk's gap is about the investor's own recorded
        evidence, not company data -- it must read as Insufficient
        Evidence, the one dimension reserved for that distinction."""
        assessment = assess_coverage(_assemble(), is_thesis_stale=False)
        thesis_risk = next(d for d in assessment.dimensions if d.dimension == "thesis_risk")
        assert thesis_risk.level is DimensionCoverageLevel.INSUFFICIENT_EVIDENCE
        assert "thesis_risk" in assessment.missing_dimensions


class TestConfidenceDerivation:
    def test_thesis_staleness_is_disclosed_in_reasoning(self):
        records = _strong_growth_records() + _undervalued_valuation_records()
        stale = assess_coverage(_assemble(records, is_thesis_stale=True), is_thesis_stale=True)
        assert any(r.code is ConfidenceReasonCode.THESIS_STALE for r in stale.reasoning)

    def test_thesis_staleness_never_improves_confidence(self):
        """Staleness can only ever cap confidence downward (real signal
        that something might be outdated) -- it must never, on its own,
        push a case toward a higher confidence than an otherwise-
        identical fresh case would get."""
        records = _strong_growth_records() + _undervalued_valuation_records()
        stale = assess_coverage(_assemble(records, is_thesis_stale=True), is_thesis_stale=True)
        fresh = assess_coverage(_assemble(records, is_thesis_stale=False), is_thesis_stale=False)
        rank = {
            ConfidenceLevel.VERY_LIMITED: 0,
            ConfidenceLevel.LIMITED: 1,
            ConfidenceLevel.MODERATE: 2,
            ConfidenceLevel.HIGH: 3,
        }
        assert rank[stale.overall_confidence] <= rank[fresh.overall_confidence]

    def test_reasoning_is_never_empty(self):
        assessment = assess_coverage(_assemble(), is_thesis_stale=False)
        assert assessment.reasoning

    def test_dimensions_unavailable_reason_carries_the_real_count_with_no_data(self):
        """Every one of the 7 live (non-permanently-locked) dimensions
        reads Unavailable/Insufficient Evidence with zero records --
        `NO_COMPANY_DATA` itself is reserved for a stricter, currently
        unreachable case (zero live dimensions at all); this is the
        real "no data" state a fresh Case actually produces."""
        assessment = assess_coverage(_assemble(), is_thesis_stale=False)
        gaps = next(r for r in assessment.reasoning if r.code is ConfidenceReasonCode.DIMENSIONS_UNAVAILABLE)
        conclusive = next(r for r in assessment.reasoning if r.code is ConfidenceReasonCode.DIMENSIONS_CONCLUSIVE)
        assert gaps.count == 7
        assert conclusive.count == 0
        assert conclusive.total == 7

    def test_dimensions_conclusive_reason_carries_real_counts(self):
        """7 live dimensions total for any case with real data (Growth,
        Capital Allocation, FCF Yield, Business/Financial/Valuation/
        Thesis Risk) -- Growth+Capital Allocation+FCF Yield+Business
        Risk+Valuation Risk reach a real conclusion here; Financial Risk
        and Thesis Risk remain gaps (no debt facts, no investor
        evidence)."""
        records = _strong_growth_records() + _strong_capital_allocation_records() + _undervalued_valuation_records()
        assessment = assess_coverage(_assemble(records), is_thesis_stale=False)
        conclusive = next(r for r in assessment.reasoning if r.code is ConfidenceReasonCode.DIMENSIONS_CONCLUSIVE)
        assert conclusive.total == 7
        assert conclusive.count is not None and 0 < conclusive.count <= conclusive.total


class TestDeterminism:
    def test_identical_inputs_produce_deeply_equal_assessments(self):
        records = _strong_growth_records()
        a = assess_coverage(_assemble(records), is_thesis_stale=False)
        b = assess_coverage(_assemble(records), is_thesis_stale=False)
        assert a == b
