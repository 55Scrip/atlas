"""Deliverable 11 (Cross-layer Audit) -- explicit invariant checks that
Investment Decision, Decision Readiness, and Recommendation Conviction
can never disagree. These are property-style tests over the *whole*
enum cross-product, not a handful of examples, because the entire
point of Deliverable 11 is that no combination of real inputs can ever
produce an incoherent result -- the same discipline that caught Sprint
11's own READY-with-blockers bug, applied here as a standing
regression guard rather than something found live.
"""
from __future__ import annotations

from datetime import datetime, timezone
from itertools import product

from atlas.alpha.decision_readiness.models import DecisionBlocker, DecisionBlockerKind, DecisionReadinessStatus
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.recommendation_conviction.engine import ConvictionInputs, build_conviction
from atlas.alpha.recommendation_conviction.models import ConvictionReasonSource, ConvictionStrength, RecommendationStability
from atlas.analysis_engine.conviction import ConvictionAssessment, ConvictionLevel, ConvictionReasonCode
from atlas.alpha.evidence_graph.models import WeaknessKind

NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)

_STRENGTH_RANK = {
    ConvictionStrength.UNAVAILABLE: -1,
    ConvictionStrength.VERY_WEAK: 0,
    ConvictionStrength.WEAK: 1,
    ConvictionStrength.MODERATE: 2,
    ConvictionStrength.STRONG: 3,
    ConvictionStrength.VERY_STRONG: 4,
}

_READINESS_CEILING_RANK = {
    DecisionReadinessStatus.READY: 4,
    DecisionReadinessStatus.ALMOST_READY: 2,
    DecisionReadinessStatus.WAITING: 1,
    DecisionReadinessStatus.BLOCKED: 0,
    DecisionReadinessStatus.UNAVAILABLE: 0,
    DecisionReadinessStatus.UNKNOWN: 0,
}


def _inputs(action, readiness_status, level) -> ConvictionInputs:
    return ConvictionInputs(
        action=action,
        readiness_status=readiness_status,
        readiness_blockers=(),
        readiness_supporting_reasons=(),
        analysis_conviction=ConvictionAssessment(level=level, reasons=(ConvictionReasonCode.EVIDENCE_COVERAGE_FULL,)),
        weak_dependency_kinds=(),
        is_thesis_stale=False,
    )


class TestConvictionNeverExceedsReadinessCeiling:
    def test_across_every_action_readiness_and_analysis_level_combination(self):
        """No combination of real `DecisionAction`/`DecisionReadinessStatus`/
        `ConvictionLevel` can ever produce a `ConvictionStrength` that
        reads stronger than what the readiness process itself has
        earned -- Decision Readiness and Recommendation Conviction can
        never disagree about "how solid is this," by construction."""
        for action, readiness_status, level in product(DecisionAction, DecisionReadinessStatus, ConvictionLevel):
            conviction = build_conviction("c1", _inputs(action, readiness_status, level), generated_at=NOW)

            if action is DecisionAction.NO_DECISION:
                assert conviction.strength is ConvictionStrength.UNAVAILABLE
                continue

            assert _STRENGTH_RANK[conviction.strength] <= _READINESS_CEILING_RANK[readiness_status]


class TestNoDecisionAlwaysMeansUnavailable:
    def test_no_decision_is_unavailable_regardless_of_every_other_signal(self):
        """Investment Decision's own `NO_DECISION` gate always wins --
        Recommendation Conviction never states a strength for an
        action Atlas has not actually recommended."""
        for readiness_status, level in product(DecisionReadinessStatus, ConvictionLevel):
            conviction = build_conviction(
                "c1", _inputs(DecisionAction.NO_DECISION, readiness_status, level), generated_at=NOW
            )
            assert conviction.strength is ConvictionStrength.UNAVAILABLE


class TestStabilityNeverFabricatesABlocker:
    def test_operationally_blocked_always_traces_to_a_real_operational_blocker(self):
        inputs = ConvictionInputs(
            action=DecisionAction.HOLD,
            readiness_status=DecisionReadinessStatus.WAITING,
            readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_FAILED),),
            readiness_supporting_reasons=(),
            analysis_conviction=ConvictionAssessment(
                level=ConvictionLevel.LOW, reasons=(ConvictionReasonCode.EVIDENCE_COVERAGE_PARTIAL,)
            ),
            weak_dependency_kinds=(),
            is_thesis_stale=False,
        )
        conviction = build_conviction("c1", inputs, generated_at=NOW)
        assert conviction.stability is RecommendationStability.OPERATIONALLY_BLOCKED
        real_blocker_codes = {b.kind.value for b in inputs.readiness_blockers}
        limiting_readiness_blocker_codes = {
            r.code for r in conviction.limiting_reasons if r.source is ConvictionReasonSource.READINESS_BLOCKER
        }
        assert limiting_readiness_blocker_codes <= real_blocker_codes

    def test_stable_never_coexists_with_a_real_blocker(self):
        inputs = ConvictionInputs(
            action=DecisionAction.HOLD,
            readiness_status=DecisionReadinessStatus.READY,
            readiness_blockers=(),
            readiness_supporting_reasons=(),
            analysis_conviction=ConvictionAssessment(
                level=ConvictionLevel.HIGH, reasons=(ConvictionReasonCode.EVIDENCE_COVERAGE_FULL,)
            ),
            weak_dependency_kinds=(),
            is_thesis_stale=False,
        )
        conviction = build_conviction("c1", inputs, generated_at=NOW)
        assert conviction.stability is RecommendationStability.STABLE
        assert conviction.limiting_reasons == ()


class TestEveryReasonCodeBelongsToItsDeclaredVocabulary:
    """A wire-level integrity check: a `ConvictionReason` tagged
    `readiness_blocker` must always carry a real `DecisionBlockerKind`
    value, `analysis_conviction` a real `ConvictionReasonCode` value,
    and `evidence_graph` a real `WeaknessKind` value -- never a code
    from the wrong vocabulary, never an invented one."""

    def test_every_reason_across_a_rich_input_resolves_to_a_real_enum_member(self):
        inputs = ConvictionInputs(
            action=DecisionAction.HOLD,
            readiness_status=DecisionReadinessStatus.WAITING,
            readiness_blockers=(DecisionBlocker(DecisionBlockerKind.COVERAGE_INCOMPLETE),),
            readiness_supporting_reasons=(),
            analysis_conviction=ConvictionAssessment(
                level=ConvictionLevel.MODERATE,
                reasons=(ConvictionReasonCode.THESIS_STALE, ConvictionReasonCode.OPEN_QUESTIONS_REMAIN),
            ),
            weak_dependency_kinds=(WeaknessKind.NO_SUPPORT,),
            is_thesis_stale=True,
        )
        conviction = build_conviction("c1", inputs, generated_at=NOW)
        for reason in conviction.limiting_reasons + conviction.supporting_reasons:
            if reason.source is ConvictionReasonSource.READINESS_BLOCKER:
                DecisionBlockerKind(reason.code)
            elif reason.source is ConvictionReasonSource.READINESS_SUPPORT:
                pass
            elif reason.source is ConvictionReasonSource.ANALYSIS_CONVICTION:
                ConvictionReasonCode(reason.code)
            elif reason.source is ConvictionReasonSource.EVIDENCE_GRAPH:
                WeaknessKind(reason.code)
            else:
                raise AssertionError(f"Unexpected ConvictionReasonSource: {reason.source}")
