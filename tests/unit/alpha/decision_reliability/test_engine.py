"""Pure unit tests for `atlas.alpha.decision_reliability.engine` --
classification, reason construction, comparison, and change detection.
No I/O; every input is a hand-built domain object."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.coverage.models import ConfidenceLevel, ConfidenceReason, ConfidenceReasonCode, CoverageAssessment
from atlas.alpha.decision_explanation.models import ChangeDirection, ExplanationReferenceKind
from atlas.alpha.decision_readiness.models import (
    DecisionBlocker,
    DecisionBlockerKind,
    DecisionReadiness,
    DecisionReadinessReason,
    DecisionReadinessReasonKind,
    DecisionReadinessStatus,
)
from atlas.alpha.decision_reliability.engine import (
    build_decision_reliability,
    build_portfolio_reliability_breakdown,
    classify_reliability,
    compare_decision_reliability,
    detect_reliability_change,
    summarize_decision_reliability,
)
from atlas.alpha.decision_reliability.models import ReliabilityLevel, ReliabilitySource
from atlas.alpha.evidence_quality.models import (
    EvidenceConflictStatus,
    EvidenceDominance,
    EvidenceFreshness,
    EvidenceQualityLevel,
    EvidenceQualityReport,
    EvidenceWarningCode,
)
from atlas.analysis_engine.analysis_coverage import AnalysisCoverageLevel

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
_CASE_ID = "case-1"


def _coverage(
    *, confidence: ConfidenceLevel = ConfidenceLevel.HIGH, reasoning: tuple[ConfidenceReason, ...] = ()
) -> CoverageAssessment:
    return CoverageAssessment(
        dimensions=(),
        overall_coverage=AnalysisCoverageLevel.SUBSTANTIAL_COVERAGE,
        overall_confidence=confidence,
        missing_dimensions=(),
        not_applicable_dimensions=(),
        reasoning=reasoning,
    )


def _evidence_quality(
    *, quality: EvidenceQualityLevel = EvidenceQualityLevel.FRESH, warnings: tuple[EvidenceWarningCode, ...] = ()
) -> EvidenceQualityReport:
    return EvidenceQualityReport(
        quality=quality,
        conflict_status=EvidenceConflictStatus.CONSISTENT,
        freshness=EvidenceFreshness.FRESH,
        dominance=EvidenceDominance.CORROBORATED,
        warnings=warnings,
        facts=(),
        conflicts=(),
        unsupported_findings=(),
    )


def _readiness(
    *,
    status: DecisionReadinessStatus = DecisionReadinessStatus.READY,
    blockers: tuple[DecisionBlocker, ...] = (),
    supporting: tuple[DecisionReadinessReason, ...] = (),
) -> DecisionReadiness:
    return DecisionReadiness(case_id=_CASE_ID, status=status, blockers=blockers, supporting_reasons=supporting, generated_at=_NOW)


def _build(
    *,
    coverage: CoverageAssessment | None = None,
    evidence_quality: EvidenceQualityReport | None = None,
    readiness: DecisionReadiness | None = None,
):
    return build_decision_reliability(
        _CASE_ID,
        coverage=coverage if coverage is not None else _coverage(),
        evidence_quality=evidence_quality if evidence_quality is not None else _evidence_quality(),
        readiness=readiness if readiness is not None else _readiness(),
        generated_at=_NOW,
    )


class TestClassifyReliability:
    def test_unknown_readiness_status_is_always_unknown_regardless_of_other_inputs(self):
        level = classify_reliability(DecisionReadinessStatus.UNKNOWN, ConfidenceLevel.HIGH, EvidenceQualityLevel.FRESH)
        assert level is ReliabilityLevel.UNKNOWN

    def test_unavailable_readiness_status_is_always_unavailable(self):
        level = classify_reliability(DecisionReadinessStatus.UNAVAILABLE, ConfidenceLevel.HIGH, EvidenceQualityLevel.FRESH)
        assert level is ReliabilityLevel.UNAVAILABLE

    def test_blocked_readiness_status_is_always_limited(self):
        level = classify_reliability(DecisionReadinessStatus.BLOCKED, ConfidenceLevel.HIGH, EvidenceQualityLevel.FRESH)
        assert level is ReliabilityLevel.LIMITED

    def test_very_limited_confidence_is_limited(self):
        level = classify_reliability(DecisionReadinessStatus.READY, ConfidenceLevel.VERY_LIMITED, EvidenceQualityLevel.FRESH)
        assert level is ReliabilityLevel.LIMITED

    def test_conflicting_evidence_quality_is_limited(self):
        level = classify_reliability(DecisionReadinessStatus.READY, ConfidenceLevel.HIGH, EvidenceQualityLevel.CONFLICTING)
        assert level is ReliabilityLevel.LIMITED

    def test_moderate_confidence_is_moderate(self):
        level = classify_reliability(DecisionReadinessStatus.READY, ConfidenceLevel.MODERATE, EvidenceQualityLevel.FRESH)
        assert level is ReliabilityLevel.MODERATE

    def test_stale_evidence_quality_is_moderate(self):
        level = classify_reliability(DecisionReadinessStatus.READY, ConfidenceLevel.HIGH, EvidenceQualityLevel.STALE)
        assert level is ReliabilityLevel.MODERATE

    def test_waiting_readiness_status_is_moderate(self):
        level = classify_reliability(DecisionReadinessStatus.WAITING, ConfidenceLevel.HIGH, EvidenceQualityLevel.FRESH)
        assert level is ReliabilityLevel.MODERATE

    def test_everything_good_is_high(self):
        level = classify_reliability(DecisionReadinessStatus.READY, ConfidenceLevel.HIGH, EvidenceQualityLevel.FRESH)
        assert level is ReliabilityLevel.HIGH

    def test_not_applicable_evidence_quality_does_not_block_high(self):
        """A Case with no timestamped evidence to grade at all must
        never be penalized as if its evidence were stale."""
        level = classify_reliability(DecisionReadinessStatus.READY, ConfidenceLevel.HIGH, EvidenceQualityLevel.NOT_APPLICABLE)
        assert level is ReliabilityLevel.HIGH


class TestBuildDecisionReliability:
    def test_level_matches_classify_reliability(self):
        reliability = _build(
            coverage=_coverage(confidence=ConfidenceLevel.MODERATE), readiness=_readiness(status=DecisionReadinessStatus.READY)
        )
        assert reliability.level is ReliabilityLevel.MODERATE

    def test_positive_confidence_reason_becomes_supporting(self):
        reasoning = (ConfidenceReason(ConfidenceReasonCode.DIMENSIONS_CONCLUSIVE, count=5, total=5),)
        reliability = _build(coverage=_coverage(reasoning=reasoning))
        codes = [r.reference.id for r in reliability.supporting_reasons]
        assert "dimensions_conclusive" in codes

    def test_negative_confidence_reason_becomes_limiting(self):
        reasoning = (ConfidenceReason(ConfidenceReasonCode.THESIS_STALE),)
        reliability = _build(coverage=_coverage(reasoning=reasoning))
        codes = [r.reference.id for r in reliability.limiting_reasons]
        assert "thesis_stale" in codes

    def test_fresh_evidence_quality_becomes_supporting(self):
        reliability = _build(evidence_quality=_evidence_quality(quality=EvidenceQualityLevel.FRESH))
        codes = [r.reference.id for r in reliability.supporting_reasons]
        assert "fresh" in codes

    def test_evidence_warning_becomes_limiting(self):
        reliability = _build(
            evidence_quality=_evidence_quality(
                quality=EvidenceQualityLevel.CONFLICTING, warnings=(EvidenceWarningCode.CONFLICTING_SOURCE_VALUES,)
            )
        )
        matching = [r for r in reliability.limiting_reasons if r.reference.id == "conflicting_source_values"]
        assert len(matching) == 1
        assert matching[0].source is ReliabilitySource.EVIDENCE_QUALITY

    def test_readiness_blocker_becomes_limiting(self):
        reliability = _build(
            readiness=_readiness(
                status=DecisionReadinessStatus.BLOCKED, blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),)
            )
        )
        matching = [r for r in reliability.limiting_reasons if r.reference.id == "monitoring_pending"]
        assert len(matching) == 1
        assert matching[0].source is ReliabilitySource.READINESS_BLOCKER

    def test_readiness_support_becomes_supporting(self):
        reliability = _build(
            readiness=_readiness(supporting=(DecisionReadinessReason(DecisionReadinessReasonKind.MONITORING_CURRENT),))
        )
        matching = [r for r in reliability.supporting_reasons if r.reference.id == "monitoring_current"]
        assert len(matching) == 1
        assert matching[0].source is ReliabilitySource.READINESS_SUPPORT

    def test_every_reference_uses_the_reason_code_kind(self):
        reliability = _build(
            readiness=_readiness(blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),)),
        )
        for reason in reliability.limiting_reasons:
            assert reason.reference.kind is ExplanationReferenceKind.REASON_CODE

    def test_primary_limiting_reason_is_the_first_entry(self):
        reliability = _build(
            readiness=_readiness(
                blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING), DecisionBlocker(DecisionBlockerKind.NO_DATA_SOURCE))
            )
        )
        assert reliability.primary_limiting_reason == reliability.limiting_reasons[0]

    def test_no_limiting_reasons_produces_no_primary(self):
        reliability = _build()
        assert reliability.primary_limiting_reason is None

    def test_two_calls_with_identical_inputs_produce_identical_output(self):
        coverage = _coverage()
        first = _build(coverage=coverage)
        second = _build(coverage=coverage)
        assert first == second


class TestSummarize:
    def test_summary_carries_the_same_primary_fact(self):
        reliability = _build(readiness=_readiness(blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),)))
        summary = summarize_decision_reliability(reliability)
        assert summary.primary_limiting_reason == reliability.primary_limiting_reason
        assert summary.level == reliability.level


class TestCompareDecisionReliability:
    def test_never_declares_a_winner_field(self):
        a = _build()
        b = _build()
        comparison = compare_decision_reliability(a, b)
        field_names = set(comparison.__dataclass_fields__.keys())
        assert not any("winner" in f or "better" in f for f in field_names)

    def test_more_reliable_case_id_is_none_on_a_genuine_tie(self):
        a = _build()
        b = _build()
        comparison = compare_decision_reliability(a, b)
        assert comparison.more_reliable_case_id is None

    def test_more_reliable_case_id_names_the_higher_ranked_side(self):
        a = _build(readiness=_readiness(status=DecisionReadinessStatus.WAITING))
        b = _build()
        comparison = compare_decision_reliability(a, b)
        assert comparison.more_reliable_case_id == b.case_id

    def test_shared_limiting_is_the_real_intersection(self):
        blocker = DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING)
        a = _build(readiness=_readiness(status=DecisionReadinessStatus.BLOCKED, blockers=(blocker,)))
        b = _build(readiness=_readiness(status=DecisionReadinessStatus.BLOCKED, blockers=(blocker,)))
        comparison = compare_decision_reliability(a, b)
        assert [r.id for r in comparison.shared_limiting] == ["monitoring_pending"]


class TestDetectReliabilityChange:
    def test_first_ever_computation_produces_no_change(self):
        current = _build()
        assert detect_reliability_change(None, current, detected_at=_NOW) is None

    def test_an_unchanged_reliability_produces_no_change(self):
        previous = _build()
        current = _build()
        assert detect_reliability_change(previous, current, detected_at=_NOW) is None

    def test_level_improvement_is_detected_as_stronger(self):
        previous = _build(readiness=_readiness(status=DecisionReadinessStatus.WAITING))
        current = _build(readiness=_readiness(status=DecisionReadinessStatus.READY))
        change = detect_reliability_change(previous, current, detected_at=_NOW)
        assert change is not None
        assert change.direction is ChangeDirection.STRONGER

    def test_level_weakening_is_detected_as_weaker(self):
        previous = _build(readiness=_readiness(status=DecisionReadinessStatus.READY))
        current = _build(readiness=_readiness(status=DecisionReadinessStatus.WAITING))
        change = detect_reliability_change(previous, current, detected_at=_NOW)
        assert change is not None
        assert change.direction is ChangeDirection.WEAKER

    def test_a_resolved_limiting_reason_is_detected(self):
        previous = _build(readiness=_readiness(status=DecisionReadinessStatus.BLOCKED, blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),)))
        current = _build(readiness=_readiness(status=DecisionReadinessStatus.READY))
        change = detect_reliability_change(previous, current, detected_at=_NOW)
        assert change is not None
        assert [r.reference.id for r in change.resolved_limiting] == ["monitoring_pending"]


class TestPortfolioReliabilityBreakdown:
    def test_high_level_ticker_lands_in_most_reliable(self):
        reliability = _build()
        items = (("AAPL", reliability),)
        breakdown = build_portfolio_reliability_breakdown(items, ())
        assert breakdown.most_reliable == ("AAPL",)
        assert breakdown.least_reliable == ()

    def test_limited_level_ticker_lands_in_least_reliable(self):
        reliability = _build(readiness=_readiness(status=DecisionReadinessStatus.BLOCKED))
        items = (("AAPL", reliability),)
        breakdown = build_portfolio_reliability_breakdown(items, ())
        assert breakdown.least_reliable == ("AAPL",)
        assert breakdown.most_reliable == ()

    def test_moderate_level_ticker_lands_in_neither_bucket(self):
        reliability = _build(readiness=_readiness(status=DecisionReadinessStatus.WAITING))
        items = (("AAPL", reliability),)
        breakdown = build_portfolio_reliability_breakdown(items, ())
        assert breakdown.most_reliable == ()
        assert breakdown.least_reliable == ()
