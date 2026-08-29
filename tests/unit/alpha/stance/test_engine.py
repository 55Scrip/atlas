"""Tests for `atlas.alpha.stance.engine` -- `CanonicalAnalysis`/
`CoverageAssessment` are built through the real, top-level
`assemble_analysis`/`assess_coverage` entry points with real
`BusinessRecord`s (the same convention `tests/unit/alpha/coverage
/test_engine.py` already establishes); `ChangeIntelligence`/
`PortfolioFitAssessment` are hand-built minimal, controlled stand-ins
for an already-tested-elsewhere upstream engine's real output shape --
the same "controlled input to the thing under test" convention
`tests/unit/alpha/portfolio_fit/test_engine.py`'s own `_EMPTY_COVERAGE`
fixture already establishes for `CoverageAssessment`.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.coverage import assess_coverage
from atlas.alpha.portfolio_fit.models import FitDimension, FitDimensionKind, FitRating, FitTrend, PortfolioFitAssessment
from atlas.alpha.stance import StanceLevel, StanceReasonCode, compare_stance, determine_stance
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.investment_case_change import ChangeIntelligence, ThesisImpact
from atlas.analysis_engine.pipeline import assemble_analysis
from tests.unit.analysis_engine._fixtures import GENERATED_AT, run_minimal, run_populated


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
        _make_record("financial_statement", date(2022, 12, 31), "fy22", revenue=1000.0, free_cash_flow=200.0),
        _make_record("financial_statement", date(2023, 12, 31), "fy23", revenue=1100.0, free_cash_flow=240.0),
        _make_record("financial_statement", date(2024, 12, 31), "fy24", revenue=1250.0, free_cash_flow=300.0),
    )


def _strong_capital_allocation_records():
    return (
        _make_record(
            "financial_statement", date(2023, 12, 31), "ca23",
            share_buybacks=100.0, share_issuance=10.0, debt_repayment=50.0, debt_issuance=5.0,
        ),
        _make_record(
            "financial_statement", date(2024, 12, 31), "ca24",
            share_buybacks=120.0, share_issuance=10.0, debt_repayment=60.0, debt_issuance=5.0,
        ),
    )


def _undervalued_valuation_records():
    return (
        _make_record(
            "financial_statement", date(2022, 12, 31), "vfy22",
            published_at=datetime(2023, 2, 15, tzinfo=timezone.utc), free_cash_flow=100.0,
        ),
        _make_record(
            "financial_statement", date(2023, 12, 31), "vfy23",
            published_at=datetime(2024, 2, 15, tzinfo=timezone.utc), free_cash_flow=110.0,
        ),
        _make_record(
            "financial_statement", date(2024, 12, 31), "vfy24",
            published_at=datetime(2025, 2, 15, tzinfo=timezone.utc), free_cash_flow=200.0,
        ),
        _make_record("market_data_snapshot", date(2023, 3, 1), "vm22", share_price=50.0, shares_outstanding=100.0),
        _make_record("market_data_snapshot", date(2024, 3, 1), "vm23", share_price=52.0, shares_outstanding=100.0),
        _make_record("market_data_snapshot", date(2025, 3, 1), "vm24", share_price=53.0, shares_outstanding=100.0),
    )


_RICH_RECORDS = _strong_growth_records() + _strong_capital_allocation_records() + _undervalued_valuation_records()


def _assemble(records=(), *, is_thesis_stale=False, populated=False):
    engine_input, output = run_populated() if populated else run_minimal()
    return assemble_analysis(
        engine_input, output, is_thesis_stale=is_thesis_stale, business_records=records, generated_at=GENERATED_AT
    )


def _coverage(analysis, *, is_thesis_stale=False):
    return assess_coverage(analysis, is_thesis_stale=is_thesis_stale)


def _change_intelligence(*, is_baseline=False, thesis_impact=ThesisImpact.UNCHANGED):
    return ChangeIntelligence(
        is_baseline=is_baseline,
        changes=(),
        thesis_impact=thesis_impact,
        summary_narrative="",
        previous_captured_at=None,
        current_captured_at=GENERATED_AT,
    )


def _fit(rating: FitRating) -> PortfolioFitAssessment:
    dims = tuple(
        FitDimension(kind=kind, rating=rating, reasoning=(), unavailable_reason=None) for kind in FitDimensionKind
    )
    return PortfolioFitAssessment(
        case_id="case-1",
        ticker="TEST",
        is_existing_holding=False,
        current_weight_percent=None,
        overall=rating,
        overall_reasoning=(),
        overall_reasoning_code=None,
        overall_reasoning_count=None,
        dimensions=dims,
        trend=FitTrend.UNAVAILABLE,
        data_gaps=(),
        coverage=_coverage(_assemble()),
        generated_at=GENERATED_AT,
    )


class TestNoCompanyDataFloor:
    def test_zero_records_and_zero_investor_evidence_is_no_recommendation(self):
        """Trust Hardening Sprint: `ConfidenceReasonCode.NO_COMPANY_DATA`
        previously only fired when every dimension was `NOT_APPLICABLE`
        (`coverage.engine._derive_confidence`'s own `if not live` gate),
        but a genuinely zero-data company (confirmed live: BTC, INVE-B)
        classifies its dimensions as `UNAVAILABLE`, not `NOT_APPLICABLE`
        -- so that gate never fired, Conviction's `INSUFFICIENT_EVIDENCE`
        fell through to `AVOID_DECISION` instead, and a company Atlas has
        never analyzed rendered identically to one with a real,
        evidence-backed contradiction. `_derive_confidence` now names
        `NO_COMPANY_DATA` whenever zero dimensions are `AVAILABLE`/
        `PARTIALLY_AVAILABLE` regardless of which non-conclusive level
        the rest carry, so this engine's own step-1 gate now correctly
        intercepts this case before it can ever reach the red-flag
        branch."""
        analysis = _assemble()
        stance = determine_stance(
            analysis, coverage=_coverage(analysis), change_intelligence=None, portfolio_fit=None
        )
        assert stance.level is StanceLevel.NO_RECOMMENDATION
        assert any(r.code is StanceReasonCode.NO_COMPANY_DATA for r in stance.reasoning)


class TestConfidenceGating:
    """Deliverable 4's own doctrine: the engine must become less
    decisive as confidence drops, never the opposite."""

    def test_very_limited_confidence_is_wait_never_a_direction(self):
        """`WAIT` even when the underlying analysis (via `analysis`,
        real and populated) would otherwise support a real conviction --
        `coverage` alone gates this, exactly Deliverable 4's own "never
        more decisive than Atlas's actual confidence" doctrine."""
        from atlas.alpha.coverage import ConfidenceLevel, ConfidenceReason, ConfidenceReasonCode, CoverageAssessment
        from atlas.analysis_engine.analysis_coverage import AnalysisCoverageLevel

        analysis = _assemble(_RICH_RECORDS, populated=True)
        coverage = CoverageAssessment(
            dimensions=(),
            overall_coverage=AnalysisCoverageLevel.PARTIAL_COVERAGE,
            overall_confidence=ConfidenceLevel.VERY_LIMITED,
            missing_dimensions=("growth", "capital_allocation"),
            not_applicable_dimensions=(),
            reasoning=(ConfidenceReason(ConfidenceReasonCode.DIMENSIONS_UNAVAILABLE, count=5),),
        )
        stance = determine_stance(
            analysis,
            coverage=coverage,
            change_intelligence=_change_intelligence(thesis_impact=ThesisImpact.STRENGTHENED),
            portfolio_fit=_fit(FitRating.EXCELLENT),
        )
        assert stance.level is StanceLevel.WAIT
        assert stance.reasoning[0].code is StanceReasonCode.CONFIDENCE_VERY_LIMITED

    def test_moderate_confidence_caps_at_review_never_a_direction(self):
        """Deliverable 4's own worked example: Strong Investment Case +
        Weak Coverage must produce Review, never a directional claim --
        even when a real thesis-strengthened signal is fed in. `_RICH
        _RECORDS` genuinely reaches `MODERATE` confidence (partial
        capital-allocation/growth data, no debt history) -- a real,
        unmodified fixture, not a hand-built stand-in, deliberately used
        here since this is the one test checking the gate against real
        data end to end."""
        analysis = _assemble(_RICH_RECORDS, populated=True)
        coverage = _coverage(analysis)
        assert coverage.overall_confidence.value == "moderate"
        stance = determine_stance(
            analysis,
            coverage=coverage,
            change_intelligence=_change_intelligence(thesis_impact=ThesisImpact.STRENGTHENED),
            portfolio_fit=_fit(FitRating.EXCELLENT),
        )
        assert stance.level is StanceLevel.REVIEW
        assert stance.reasoning[0].code is StanceReasonCode.CONFIDENCE_MODERATE


def _high_confidence_coverage():
    """A hand-built, controlled `CoverageAssessment` reporting `HIGH`
    confidence -- `coverage` is an external, already-computed parameter
    to `determine_stance` (never recomputed internally), so this
    isolates "does the directional logic behave correctly given high
    confidence" from "does a synthetic fixture's real financial data
    happen to reach exactly HIGH" (fragile and not the point of these
    tests -- `TestConfidenceGating` above already covers the gate
    itself against real data). Same "controlled input to the thing
    under test" convention this file's own module docstring documents
    for `ChangeIntelligence`/`PortfolioFitAssessment`."""
    from atlas.alpha.coverage import ConfidenceLevel, ConfidenceReason, ConfidenceReasonCode, CoverageAssessment
    from atlas.analysis_engine.analysis_coverage import AnalysisCoverageLevel

    return CoverageAssessment(
        dimensions=(),
        overall_coverage=AnalysisCoverageLevel.SUBSTANTIAL_COVERAGE,
        overall_confidence=ConfidenceLevel.HIGH,
        missing_dimensions=(),
        not_applicable_dimensions=(),
        reasoning=(ConfidenceReason(ConfidenceReasonCode.DIMENSIONS_CONCLUSIVE, count=7, total=7),),
    )


class TestDirectionalGating:
    def test_thesis_strengthened_with_favorable_fit_and_no_risk_is_increase(self):
        analysis = _assemble(_RICH_RECORDS, populated=True)
        stance = determine_stance(
            analysis,
            coverage=_high_confidence_coverage(),
            change_intelligence=_change_intelligence(thesis_impact=ThesisImpact.STRENGTHENED),
            portfolio_fit=_fit(FitRating.EXCELLENT),
        )
        assert stance.level is StanceLevel.INCREASE
        assert any(r.code is StanceReasonCode.THESIS_STRENGTHENED for r in stance.supporting_signals)

    def test_thesis_strengthened_with_weak_fit_downgrades_to_review(self):
        """Deliverable 7's own worked example: an otherwise-favorable
        direction alongside a weak Portfolio Fit must never state a
        confident Increase."""
        analysis = _assemble(_RICH_RECORDS, populated=True)
        stance = determine_stance(
            analysis,
            coverage=_high_confidence_coverage(),
            change_intelligence=_change_intelligence(thesis_impact=ThesisImpact.STRENGTHENED),
            portfolio_fit=_fit(FitRating.WEAK),
        )
        assert stance.level is StanceLevel.REVIEW
        assert any(r.code is StanceReasonCode.PORTFOLIO_FIT_WEAK for r in stance.limiting_signals)

    def test_thesis_weakened_is_reduce_never_review(self):
        analysis = _assemble(_RICH_RECORDS, populated=True)
        stance = determine_stance(
            analysis,
            coverage=_high_confidence_coverage(),
            change_intelligence=_change_intelligence(thesis_impact=ThesisImpact.WEAKENED),
            portfolio_fit=None,
        )
        assert stance.level is StanceLevel.REDUCE
        assert any(r.code is StanceReasonCode.THESIS_WEAKENED for r in stance.limiting_signals)

    def test_thesis_mixed_is_review(self):
        analysis = _assemble(_RICH_RECORDS, populated=True)
        stance = determine_stance(
            analysis,
            coverage=_high_confidence_coverage(),
            change_intelligence=_change_intelligence(thesis_impact=ThesisImpact.MIXED),
            portfolio_fit=None,
        )
        assert stance.level is StanceLevel.REVIEW

    def test_thesis_unchanged_is_maintain(self):
        analysis = _assemble(_RICH_RECORDS, populated=True)
        stance = determine_stance(
            analysis,
            coverage=_high_confidence_coverage(),
            change_intelligence=_change_intelligence(thesis_impact=ThesisImpact.UNCHANGED),
            portfolio_fit=None,
        )
        assert stance.level is StanceLevel.MAINTAIN


class TestReasoningAndDisclosure:
    def test_reasoning_is_never_empty(self):
        analysis = _assemble()
        stance = determine_stance(
            analysis, coverage=_coverage(analysis), change_intelligence=None, portfolio_fit=None
        )
        assert stance.reasoning

    def test_missing_information_is_reused_verbatim_from_coverage(self):
        analysis = _assemble()
        coverage = _coverage(analysis)
        stance = determine_stance(analysis, coverage=coverage, change_intelligence=None, portfolio_fit=None)
        assert stance.missing_information == coverage.missing_dimensions

    def test_confidence_is_reused_verbatim_from_coverage(self):
        analysis = _assemble(_RICH_RECORDS, populated=True)
        coverage = _coverage(analysis)
        stance = determine_stance(analysis, coverage=coverage, change_intelligence=None, portfolio_fit=None)
        assert stance.confidence == coverage.overall_confidence


class TestCompareStance:
    def _stance(self, level: StanceLevel):
        from atlas.alpha.coverage import ConfidenceLevel
        from atlas.alpha.stance.models import Stance

        return Stance(
            level=level,
            reasoning=(),
            supporting_signals=(),
            limiting_signals=(),
            confidence=ConfidenceLevel.HIGH,
            missing_information=(),
        )

    def test_tied_levels_produce_no_preference(self):
        comparison = compare_stance("AAA", self._stance(StanceLevel.MAINTAIN), "BBB", self._stance(StanceLevel.MAINTAIN))
        assert comparison.preferred_ticker is None

    def test_wait_never_gets_a_preference_even_against_increase(self):
        comparison = compare_stance("AAA", self._stance(StanceLevel.INCREASE), "BBB", self._stance(StanceLevel.WAIT))
        assert comparison.preferred_ticker is None

    def test_increase_beats_reduce(self):
        comparison = compare_stance("AAA", self._stance(StanceLevel.INCREASE), "BBB", self._stance(StanceLevel.REDUCE))
        assert comparison.preferred_ticker == "AAA"

    def test_preference_is_symmetric_regardless_of_argument_order(self):
        a = compare_stance("AAA", self._stance(StanceLevel.INCREASE), "BBB", self._stance(StanceLevel.REDUCE))
        b = compare_stance("BBB", self._stance(StanceLevel.REDUCE), "AAA", self._stance(StanceLevel.INCREASE))
        assert a.preferred_ticker == b.preferred_ticker == "AAA"


class TestDeterminism:
    def test_identical_inputs_produce_deeply_equal_stances(self):
        analysis = _assemble(_RICH_RECORDS, populated=True)
        coverage = _coverage(analysis)
        ci = _change_intelligence(thesis_impact=ThesisImpact.STRENGTHENED)
        a = determine_stance(analysis, coverage=coverage, change_intelligence=ci, portfolio_fit=None)
        b = determine_stance(analysis, coverage=coverage, change_intelligence=ci, portfolio_fit=None)
        assert a == b
