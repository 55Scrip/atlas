"""Tests for `atlas.alpha.recommendation_conviction.engine` -- the
strength derivation (base-from-analysis-conviction, capped by
readiness), the stability waterfall, reason tagging, and the summary/
compare/change-detection helpers."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.decision_readiness.models import (
    DecisionBlocker,
    DecisionBlockerKind,
    DecisionReadinessReason,
    DecisionReadinessReasonKind,
    DecisionReadinessStatus,
)
from atlas.alpha.evidence_graph.models import WeaknessKind
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.recommendation_conviction.engine import (
    ConvictionInputs,
    build_conviction,
    build_portfolio_conviction_breakdown,
    compare_convictions,
    detect_conviction_change,
    summarize_conviction,
)
from atlas.alpha.recommendation_conviction.models import (
    ConvictionReason,
    ConvictionReasonSource,
    ConvictionStrength,
    RecommendationConviction,
    RecommendationStability,
)
from atlas.analysis_engine.conviction import ConvictionAssessment, ConvictionLevel, ConvictionReasonCode

NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)


def _analysis_conviction(level=ConvictionLevel.VERY_HIGH, reasons=None) -> ConvictionAssessment:
    if reasons is None:
        reasons = (
            ConvictionReasonCode.EVIDENCE_COVERAGE_FULL,
            ConvictionReasonCode.NO_CONTRADICTING_EVIDENCE,
            ConvictionReasonCode.NO_HIGH_FINANCIAL_OR_VALUATION_RISK,
            ConvictionReasonCode.THESIS_NOT_STALE,
            ConvictionReasonCode.NO_OPEN_QUESTIONS,
            ConvictionReasonCode.BUSINESS_AND_VALUATION_CONCLUSIVE,
        )
    return ConvictionAssessment(level=level, reasons=reasons)


def _inputs(**overrides) -> ConvictionInputs:
    """A fully "healthy, strong" baseline -- every test overrides only
    the field(s) it actually cares about."""
    base = dict(
        action=DecisionAction.HOLD,
        readiness_status=DecisionReadinessStatus.READY,
        readiness_blockers=(),
        readiness_supporting_reasons=(DecisionReadinessReason(DecisionReadinessReasonKind.SUBSTANTIAL_COVERAGE_REACHED),),
        analysis_conviction=_analysis_conviction(),
        weak_dependency_kinds=(),
        is_thesis_stale=False,
    )
    base.update(overrides)
    return ConvictionInputs(**base)


class TestStrengthDerivation:
    def test_no_decision_action_is_unavailable(self):
        conviction = build_conviction("c1", _inputs(action=DecisionAction.NO_DECISION), generated_at=NOW)
        assert conviction.strength is ConvictionStrength.UNAVAILABLE

    def test_no_decision_is_unavailable_even_with_very_high_analysis_conviction(self):
        conviction = build_conviction(
            "c1", _inputs(action=DecisionAction.NO_DECISION, analysis_conviction=_analysis_conviction(ConvictionLevel.VERY_HIGH)), generated_at=NOW
        )
        assert conviction.strength is ConvictionStrength.UNAVAILABLE

    def test_very_high_analysis_conviction_with_ready_readiness_is_very_strong(self):
        conviction = build_conviction("c1", _inputs(analysis_conviction=_analysis_conviction(ConvictionLevel.VERY_HIGH)), generated_at=NOW)
        assert conviction.strength is ConvictionStrength.VERY_STRONG

    def test_high_analysis_conviction_with_ready_readiness_is_strong(self):
        conviction = build_conviction("c1", _inputs(analysis_conviction=_analysis_conviction(ConvictionLevel.HIGH)), generated_at=NOW)
        assert conviction.strength is ConvictionStrength.STRONG

    def test_moderate_analysis_conviction_is_moderate(self):
        conviction = build_conviction("c1", _inputs(analysis_conviction=_analysis_conviction(ConvictionLevel.MODERATE)), generated_at=NOW)
        assert conviction.strength is ConvictionStrength.MODERATE

    def test_low_analysis_conviction_is_weak(self):
        conviction = build_conviction("c1", _inputs(analysis_conviction=_analysis_conviction(ConvictionLevel.LOW)), generated_at=NOW)
        assert conviction.strength is ConvictionStrength.WEAK

    def test_insufficient_evidence_analysis_conviction_is_very_weak(self):
        conviction = build_conviction(
            "c1", _inputs(analysis_conviction=_analysis_conviction(ConvictionLevel.INSUFFICIENT_EVIDENCE)), generated_at=NOW
        )
        assert conviction.strength is ConvictionStrength.VERY_WEAK

    def test_blocked_readiness_caps_a_very_high_analysis_conviction_down_to_very_weak(self):
        conviction = build_conviction(
            "c1",
            _inputs(
                readiness_status=DecisionReadinessStatus.BLOCKED,
                analysis_conviction=_analysis_conviction(ConvictionLevel.VERY_HIGH),
            ),
            generated_at=NOW,
        )
        assert conviction.strength is ConvictionStrength.VERY_WEAK

    def test_unavailable_readiness_also_caps_at_very_weak(self):
        conviction = build_conviction(
            "c1",
            _inputs(
                readiness_status=DecisionReadinessStatus.UNAVAILABLE,
                analysis_conviction=_analysis_conviction(ConvictionLevel.VERY_HIGH),
            ),
            generated_at=NOW,
        )
        assert conviction.strength is ConvictionStrength.VERY_WEAK

    def test_waiting_readiness_caps_strength_at_weak(self):
        conviction = build_conviction(
            "c1",
            _inputs(readiness_status=DecisionReadinessStatus.WAITING, analysis_conviction=_analysis_conviction(ConvictionLevel.VERY_HIGH)),
            generated_at=NOW,
        )
        assert conviction.strength is ConvictionStrength.WEAK

    def test_almost_ready_readiness_caps_strength_at_moderate(self):
        conviction = build_conviction(
            "c1",
            _inputs(
                readiness_status=DecisionReadinessStatus.ALMOST_READY, analysis_conviction=_analysis_conviction(ConvictionLevel.VERY_HIGH)
            ),
            generated_at=NOW,
        )
        assert conviction.strength is ConvictionStrength.MODERATE

    def test_a_cap_never_upgrades_an_already_weaker_base(self):
        """`WAITING` caps at `WEAK`, but a `LOW` analysis conviction is
        already `WEAK` -- the cap must never push it *up* to `WEAK`
        from something lower, and here it should simply stay put."""
        conviction = build_conviction(
            "c1",
            _inputs(readiness_status=DecisionReadinessStatus.WAITING, analysis_conviction=_analysis_conviction(ConvictionLevel.INSUFFICIENT_EVIDENCE)),
            generated_at=NOW,
        )
        assert conviction.strength is ConvictionStrength.VERY_WEAK

    def test_unknown_readiness_caps_at_very_weak(self):
        conviction = build_conviction(
            "c1",
            _inputs(readiness_status=DecisionReadinessStatus.UNKNOWN, analysis_conviction=_analysis_conviction(ConvictionLevel.VERY_HIGH)),
            generated_at=NOW,
        )
        assert conviction.strength is ConvictionStrength.VERY_WEAK


class TestStabilityDerivation:
    def test_healthy_baseline_is_stable(self):
        conviction = build_conviction("c1", _inputs(), generated_at=NOW)
        assert conviction.stability is RecommendationStability.STABLE

    def test_operational_blocker_is_operationally_blocked(self):
        conviction = build_conviction(
            "c1", _inputs(readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),)), generated_at=NOW
        )
        assert conviction.stability is RecommendationStability.OPERATIONALLY_BLOCKED

    def test_evidence_limiting_blocker_is_evidence_limited(self):
        conviction = build_conviction(
            "c1", _inputs(readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MISSING_THESIS_EVIDENCE),)), generated_at=NOW
        )
        assert conviction.stability is RecommendationStability.EVIDENCE_LIMITED

    def test_operational_takes_priority_over_evidence_limited(self):
        conviction = build_conviction(
            "c1",
            _inputs(
                readiness_blockers=(
                    DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),
                    DecisionBlocker(DecisionBlockerKind.MISSING_THESIS_EVIDENCE),
                )
            ),
            generated_at=NOW,
        )
        assert conviction.stability is RecommendationStability.OPERATIONALLY_BLOCKED

    def test_waiting_status_with_no_blockers_is_waiting_for_evidence(self):
        conviction = build_conviction("c1", _inputs(readiness_status=DecisionReadinessStatus.WAITING), generated_at=NOW)
        assert conviction.stability is RecommendationStability.WAITING_FOR_EVIDENCE

    def test_stale_thesis_alone_is_fragile(self):
        conviction = build_conviction("c1", _inputs(is_thesis_stale=True), generated_at=NOW)
        assert conviction.stability is RecommendationStability.FRAGILE

    def test_weak_dependency_alone_is_fragile(self):
        conviction = build_conviction("c1", _inputs(weak_dependency_kinds=(WeaknessKind.CRITICAL_DEPENDENCY,)), generated_at=NOW)
        assert conviction.stability is RecommendationStability.FRAGILE


class TestReasonsAndTriggers:
    def test_readiness_blockers_are_reused_verbatim(self):
        conviction = build_conviction(
            "c1", _inputs(readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),)), generated_at=NOW
        )
        assert ConvictionReason(ConvictionReasonSource.READINESS_BLOCKER, "monitoring_pending") in conviction.limiting_reasons

    def test_readiness_supporting_reasons_are_reused_verbatim(self):
        conviction = build_conviction("c1", _inputs(), generated_at=NOW)
        assert (
            ConvictionReason(ConvictionReasonSource.READINESS_SUPPORT, "substantial_coverage_reached")
            in conviction.supporting_reasons
        )

    def test_positive_analysis_reasons_become_supporting(self):
        conviction = build_conviction("c1", _inputs(), generated_at=NOW)
        assert ConvictionReason(ConvictionReasonSource.ANALYSIS_CONVICTION, "evidence_coverage_full") in conviction.supporting_reasons

    def test_negative_analysis_reasons_become_limiting(self):
        conviction = build_conviction(
            "c1",
            _inputs(analysis_conviction=_analysis_conviction(ConvictionLevel.MODERATE, reasons=(ConvictionReasonCode.THESIS_STALE,))),
            generated_at=NOW,
        )
        assert ConvictionReason(ConvictionReasonSource.ANALYSIS_CONVICTION, "thesis_stale") in conviction.limiting_reasons

    def test_weak_dependency_kinds_become_limiting_reasons(self):
        conviction = build_conviction("c1", _inputs(weak_dependency_kinds=(WeaknessKind.NO_SUPPORT,)), generated_at=NOW)
        assert ConvictionReason(ConvictionReasonSource.EVIDENCE_GRAPH, "no_support") in conviction.limiting_reasons

    def test_strengthening_trigger_is_the_first_limiting_reason(self):
        conviction = build_conviction(
            "c1",
            _inputs(
                readiness_blockers=(
                    DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),
                    DecisionBlocker(DecisionBlockerKind.COVERAGE_INCOMPLETE),
                )
            ),
            generated_at=NOW,
        )
        assert conviction.strengthening_trigger == conviction.limiting_reasons[0]

    def test_no_limiting_reasons_means_no_strengthening_trigger(self):
        conviction = build_conviction(
            "c1", _inputs(analysis_conviction=_analysis_conviction(ConvictionLevel.VERY_HIGH)), generated_at=NOW
        )
        assert conviction.limiting_reasons == ()
        assert conviction.strengthening_trigger is None


class TestSummarizeConviction:
    def test_primary_fields_are_the_first_entries(self):
        conviction = build_conviction(
            "c1", _inputs(readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),)), generated_at=NOW
        )
        summary = summarize_conviction(conviction)
        assert summary.primary_limiting_reason == conviction.limiting_reasons[0]
        assert summary.primary_supporting_reason == conviction.supporting_reasons[0]
        assert summary.strengthening_trigger == conviction.strengthening_trigger


class TestCompareConvictions:
    def test_stronger_case_id_by_rank(self):
        a = build_conviction("a", _inputs(analysis_conviction=_analysis_conviction(ConvictionLevel.VERY_HIGH)), generated_at=NOW)
        b = build_conviction("b", _inputs(analysis_conviction=_analysis_conviction(ConvictionLevel.LOW)), generated_at=NOW)
        comparison = compare_convictions(a, b)
        assert comparison.stronger_case_id == "a"

    def test_tie_in_strength_is_none(self):
        a = build_conviction("a", _inputs(), generated_at=NOW)
        b = build_conviction("b", _inputs(), generated_at=NOW)
        comparison = compare_convictions(a, b)
        assert comparison.stronger_case_id is None

    def test_more_evidence_limited_case_id(self):
        a = build_conviction(
            "a", _inputs(readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MISSING_THESIS_EVIDENCE),)), generated_at=NOW
        )
        b = build_conviction("b", _inputs(), generated_at=NOW)
        comparison = compare_convictions(a, b)
        assert comparison.more_evidence_limited_case_id == "a"

    def test_more_operationally_blocked_case_id(self):
        a = build_conviction("a", _inputs(), generated_at=NOW)
        b = build_conviction(
            "b", _inputs(readiness_blockers=(DecisionBlocker(DecisionBlockerKind.NO_DATA_SOURCE),)), generated_at=NOW
        )
        comparison = compare_convictions(a, b)
        assert comparison.more_operationally_blocked_case_id == "b"

    def test_more_stable_case_id(self):
        a = build_conviction("a", _inputs(), generated_at=NOW)
        b = build_conviction("b", _inputs(is_thesis_stale=True), generated_at=NOW)
        comparison = compare_convictions(a, b)
        assert comparison.more_stable_case_id == "a"

    def test_comparison_never_names_an_overall_winner(self):
        """Structural check: only `a`/`b` and four independent,
        honest-on-tie factual comparison fields exist -- no combined
        verdict field of any kind."""
        a = build_conviction("a", _inputs(), generated_at=NOW)
        b = build_conviction("b", _inputs(readiness_status=DecisionReadinessStatus.BLOCKED), generated_at=NOW)
        comparison = compare_convictions(a, b)
        field_names = set(comparison.__dataclass_fields__.keys())
        assert field_names == {
            "a",
            "b",
            "stronger_case_id",
            "more_evidence_limited_case_id",
            "more_operationally_blocked_case_id",
            "more_stable_case_id",
        }


class TestDetectConvictionChange:
    def test_no_previous_computation_produces_no_change(self):
        current = build_conviction("c1", _inputs(), generated_at=NOW)
        assert detect_conviction_change(None, current, detected_at=NOW) is None

    def test_identical_strength_and_stability_produce_no_change(self):
        previous = build_conviction("c1", _inputs(), generated_at=NOW)
        current = build_conviction("c1", _inputs(), generated_at=NOW)
        assert detect_conviction_change(previous, current, detected_at=NOW) is None

    def test_a_real_strength_transition_is_reported(self):
        previous = build_conviction("c1", _inputs(analysis_conviction=_analysis_conviction(ConvictionLevel.LOW)), generated_at=NOW)
        current = build_conviction("c1", _inputs(analysis_conviction=_analysis_conviction(ConvictionLevel.VERY_HIGH)), generated_at=NOW)
        change = detect_conviction_change(previous, current, detected_at=NOW)
        assert change is not None
        assert change.previous_strength is ConvictionStrength.WEAK
        assert change.current_strength is ConvictionStrength.VERY_STRONG

    def test_a_stability_only_change_is_reported_even_with_the_same_strength(self):
        previous = build_conviction("c1", _inputs(), generated_at=NOW)
        current = build_conviction("c1", _inputs(is_thesis_stale=True), generated_at=NOW)
        change = detect_conviction_change(previous, current, detected_at=NOW)
        assert change is not None
        assert change.previous_strength == change.current_strength
        assert change.previous_stability is RecommendationStability.STABLE
        assert change.current_stability is RecommendationStability.FRAGILE

    def test_new_and_resolved_limiting_reasons_are_computed_correctly(self):
        previous = build_conviction(
            "c1", _inputs(readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),)), generated_at=NOW
        )
        current = build_conviction(
            "c1", _inputs(readiness_blockers=(DecisionBlocker(DecisionBlockerKind.COVERAGE_INCOMPLETE),)), generated_at=NOW
        )
        change = detect_conviction_change(previous, current, detected_at=NOW)
        assert change is not None
        assert ConvictionReason(ConvictionReasonSource.READINESS_BLOCKER, "coverage_incomplete") in change.new_limiting_reasons
        assert ConvictionReason(ConvictionReasonSource.READINESS_BLOCKER, "monitoring_pending") in change.resolved_limiting_reasons


class TestPortfolioConvictionBreakdown:
    def test_buckets_by_strength_and_stability(self):
        strong = build_conviction("a", _inputs(analysis_conviction=_analysis_conviction(ConvictionLevel.VERY_HIGH)), generated_at=NOW)
        weak = build_conviction("b", _inputs(analysis_conviction=_analysis_conviction(ConvictionLevel.LOW)), generated_at=NOW)
        blocked = build_conviction(
            "c",
            _inputs(
                readiness_blockers=(DecisionBlocker(DecisionBlockerKind.NO_DATA_SOURCE),),
                analysis_conviction=_analysis_conviction(ConvictionLevel.MODERATE),
            ),
            generated_at=NOW,
        )
        evidence_limited = build_conviction(
            "d",
            _inputs(
                readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MISSING_THESIS_EVIDENCE),),
                analysis_conviction=_analysis_conviction(ConvictionLevel.MODERATE),
            ),
            generated_at=NOW,
        )
        items = (("AAPL", strong), ("MSFT", weak), ("NVDA", blocked), ("GOOGL", evidence_limited))
        breakdown = build_portfolio_conviction_breakdown(items)
        assert breakdown.highest_conviction == ("AAPL",)
        assert breakdown.lowest_conviction == ("MSFT",)
        assert breakdown.operationally_blocked == ("NVDA",)
        assert breakdown.evidence_limited == ("GOOGL",)

    def test_holdings_order_is_preserved_never_re_ranked(self):
        weak = build_conviction("a", _inputs(analysis_conviction=_analysis_conviction(ConvictionLevel.LOW)), generated_at=NOW)
        strong = build_conviction("b", _inputs(analysis_conviction=_analysis_conviction(ConvictionLevel.VERY_HIGH)), generated_at=NOW)
        items = (("ZZZ", weak), ("AAA", strong))
        breakdown = build_portfolio_conviction_breakdown(items)
        assert breakdown.lowest_conviction == ("ZZZ",)
        assert breakdown.highest_conviction == ("AAA",)
