"""Tests for `atlas.alpha.materiality.engine` -- `Explanation` is a
hand-built, controlled stand-in for the already-tested-elsewhere
`atlas.alpha.explainability.explain()`, the same convention
`tests/unit/alpha/explainability/test_engine.py`'s own module docstring
establishes, since this module's whole job is classifying/ranking its
already-real buckets, never recomputing them.
"""
from __future__ import annotations

from atlas.alpha.coverage import DimensionCoverage, DimensionCoverageLevel
from atlas.alpha.explainability import Explanation
from atlas.alpha.materiality import MaterialityLevel, assess_materiality
from atlas.alpha.materiality.engine import _STANCE_REASON_MATERIALITY
from atlas.alpha.stance import StanceReason, StanceReasonCode


def _explanation(
    supporting=(),
    contradicting=(),
    limiting=(),
    missing=(),
    most_valuable=None,
) -> Explanation:
    return Explanation(
        supporting_evidence=supporting,
        contradicting_evidence=contradicting,
        limiting_factors=limiting,
        missing_evidence=missing,
        confidence_drivers=(),
        most_valuable_missing_information=most_valuable,
    )


class TestCompleteness:
    def test_every_stance_reason_code_is_classified(self):
        assert set(_STANCE_REASON_MATERIALITY) == set(StanceReasonCode)

    def test_no_code_is_classified_as_unknown(self):
        """UNKNOWN is reserved for a future, unclassified code -- never
        one this engine's own fixed map should assign today."""
        assert MaterialityLevel.UNKNOWN not in _STANCE_REASON_MATERIALITY.values()


class TestClassification:
    def test_a_fundamental_blocker_is_classified_critical(self):
        explanation = _explanation(limiting=(StanceReason(StanceReasonCode.NO_COMPANY_DATA),))
        assessment = assess_materiality(explanation)
        assert assessment.limiting_factors[0].materiality is MaterialityLevel.CRITICAL

    def test_a_routine_unchanged_fact_is_classified_background(self):
        explanation = _explanation(supporting=(StanceReason(StanceReasonCode.DECISION_SUPPORT_NEUTRAL),))
        assessment = assess_materiality(explanation)
        assert assessment.supporting_evidence[0].materiality is MaterialityLevel.BACKGROUND

    def test_high_risk_present_is_critical_never_merely_high(self):
        explanation = _explanation(contradicting=(StanceReason(StanceReasonCode.HIGH_RISK_PRESENT),))
        assessment = assess_materiality(explanation)
        assert assessment.contradicting_evidence[0].materiality is MaterialityLevel.CRITICAL


class TestOrdering:
    def test_critical_evidence_is_ordered_before_high_evidence(self):
        explanation = _explanation(
            limiting=(
                StanceReason(StanceReasonCode.CONFIDENCE_VERY_LIMITED),  # HIGH
                StanceReason(StanceReasonCode.CONVICTION_INSUFFICIENT),  # CRITICAL
            )
        )
        assessment = assess_materiality(explanation)
        assert assessment.limiting_factors[0].reason.code is StanceReasonCode.CONVICTION_INSUFFICIENT
        assert assessment.limiting_factors[1].reason.code is StanceReasonCode.CONFIDENCE_VERY_LIMITED

    def test_never_reorders_by_input_position_alone(self):
        """Input order must never win over the real materiality
        classification -- confirmed by reversing the input tuple and
        checking the output order is identical either way."""
        reasons_a = (StanceReason(StanceReasonCode.CONFIDENCE_MODERATE), StanceReason(StanceReasonCode.HIGH_RISK_PRESENT))
        reasons_b = tuple(reversed(reasons_a))
        result_a = assess_materiality(_explanation(limiting=reasons_a))
        result_b = assess_materiality(_explanation(limiting=reasons_b))
        assert [m.reason.code for m in result_a.limiting_factors] == [m.reason.code for m in result_b.limiting_factors]

    def test_a_deterministic_tie_break_applies_within_the_same_level(self):
        """Two CRITICAL codes must still resolve to one fixed, stable
        order -- `StanceReasonCode`'s own declared member order, never
        arbitrary."""
        reasons = (StanceReason(StanceReasonCode.HIGH_RISK_PRESENT), StanceReason(StanceReasonCode.NO_COMPANY_DATA))
        first = assess_materiality(_explanation(limiting=reasons))
        second = assess_materiality(_explanation(limiting=tuple(reversed(reasons))))
        assert [m.reason.code for m in first.limiting_factors] == [m.reason.code for m in second.limiting_factors]


class TestTopPicks:
    def test_top_supporting_evidence_is_the_most_material_one(self):
        explanation = _explanation(
            supporting=(
                StanceReason(StanceReasonCode.PORTFOLIO_FIT_FAVORABLE),  # MEDIUM
                StanceReason(StanceReasonCode.THESIS_STRENGTHENED),  # HIGH
            )
        )
        assessment = assess_materiality(explanation)
        assert assessment.top_supporting_evidence is not None
        assert assessment.top_supporting_evidence.reason.code is StanceReasonCode.THESIS_STRENGTHENED

    def test_top_pick_is_none_when_the_bucket_is_empty_never_fabricated(self):
        assessment = assess_materiality(_explanation())
        assert assessment.top_supporting_evidence is None
        assert assessment.top_contradicting_evidence is None
        assert assessment.top_limiting_factor is None

    def test_top_missing_evidence_is_reused_verbatim_never_recomputed(self):
        dimension = DimensionCoverage(dimension="growth", level=DimensionCoverageLevel.UNAVAILABLE, reasoning=())
        explanation = _explanation(missing=(dimension,), most_valuable=dimension)
        assessment = assess_materiality(explanation)
        assert assessment.top_missing_evidence is dimension


class TestDeterminism:
    def test_identical_inputs_produce_deeply_equal_assessments(self):
        explanation = _explanation(
            supporting=(StanceReason(StanceReasonCode.THESIS_STRENGTHENED),),
            limiting=(StanceReason(StanceReasonCode.CONFIDENCE_LIMITED),),
        )
        assert assess_materiality(explanation) == assess_materiality(explanation)
