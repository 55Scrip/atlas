"""Deliverable 11 (Cross-layer Audit) -- explicit invariant checks that
Investment Decision, Recommendation Conviction, Decision Path, and
Opportunity Cost can never disagree. Property-style tests over the
whole action/blocker space, the same discipline Sprint 2's and Sprint
3's own `test_cross_layer_consistency.py` already established.
"""
from __future__ import annotations

from datetime import datetime, timezone
from itertools import product

from atlas.alpha.decision_path.models import (
    DecisionPath,
    DecisionStep,
    DependencyReference,
    DependencySource,
    FinalReachableState,
    ReachabilityStatus,
    RequiredProgressKind,
)
from atlas.alpha.investment_decision.models import DecisionAction, DecisionReason, DecisionReasonSource
from atlas.alpha.opportunity_cost.engine import OtherCaseSummary, build_alternatives
from atlas.alpha.opportunity_cost.models import AlternativeKind
from atlas.alpha.recommendation_conviction.models import ConvictionStrength

NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)

_ALL_ACTIONS = tuple(DecisionAction)
_NO_ACTION_CURRENT_ACTIONS = frozenset({DecisionAction.HOLD, DecisionAction.WAIT, DecisionAction.NO_DECISION})


def _path(steps: tuple[DecisionStep, ...] = ()) -> DecisionPath:
    return DecisionPath(
        case_id="current",
        current_action=DecisionAction.HOLD,
        current_strength=ConvictionStrength.MODERATE,
        steps=steps,
        immediate_blocker=steps[0] if steps else None,
        next_achievable_improvement=None,
        final_reachable_state=FinalReachableState.FULLY_REACHABLE if steps else FinalReachableState.ALREADY_REACHED,
        generated_at=NOW,
    )


_STEP = DecisionStep(DependencyReference(DependencySource.READINESS_BLOCKER, "missing_thesis_evidence"), RequiredProgressKind.EVIDENCE, ReachabilityStatus.REACHABLE)
_REASON = DecisionReason(DecisionReasonSource.STANCE, "decision_support_favorable")


class TestNoActionOnlyForSettledActions:
    def test_across_every_current_action_with_and_without_a_blocker(self):
        for current_action, has_step in product(_ALL_ACTIONS, (True, False)):
            path = _path((_STEP,) if has_step else ())
            alternatives = build_alternatives(current_action, (_REASON,), path, ())
            has_no_action = any(a.kind is AlternativeKind.NO_ACTION for a in alternatives)
            assert has_no_action == (current_action in _NO_ACTION_CURRENT_ACTIONS)


class TestNonCaseAlternativesNeverCarryCaseFields:
    def test_wait_keep_cash_no_action_are_always_case_free(self):
        for current_action in _ALL_ACTIONS:
            alternatives = build_alternatives(current_action, (_REASON,), _path((_STEP,)), ())
            for alternative in alternatives:
                if alternative.kind in (AlternativeKind.WAIT, AlternativeKind.KEEP_CASH, AlternativeKind.NO_ACTION):
                    assert alternative.case_id is None
                    assert alternative.ticker is None
                    assert alternative.action is None
                    assert alternative.strength is None


class TestCompetingCaseAlternativesAlwaysHaveARealBuyOrAddAction:
    def test_across_every_other_action(self):
        for other_action in _ALL_ACTIONS:
            other = OtherCaseSummary("o1", "MSFT", is_holding=True, action=other_action, top_reason=_REASON, strength=ConvictionStrength.STRONG)
            alternatives = build_alternatives(DecisionAction.HOLD, (), _path(), (other,))
            case_alternatives = [a for a in alternatives if a.case_id == "o1"]
            if other_action in (DecisionAction.BUY, DecisionAction.ADD):
                assert len(case_alternatives) == 1
                assert case_alternatives[0].action in (DecisionAction.BUY, DecisionAction.ADD)
            else:
                assert case_alternatives == []


class TestOrderingIsStableAcrossEveryCombination:
    def test_competing_cases_always_precede_wait_keep_cash_no_action(self):
        other = OtherCaseSummary("o1", "MSFT", is_holding=True, action=DecisionAction.ADD, top_reason=_REASON, strength=None)
        for current_action, has_step in product(_ALL_ACTIONS, (True, False)):
            path = _path((_STEP,) if has_step else ())
            alternatives = build_alternatives(current_action, (_REASON,), path, (other,))
            kinds = [a.kind for a in alternatives]
            case_kind_indices = [i for i, k in enumerate(kinds) if k in (AlternativeKind.INCREASE_EXISTING_HOLDING, AlternativeKind.OPEN_NEW_POSITION)]
            non_case_kind_indices = [i for i, k in enumerate(kinds) if k in (AlternativeKind.WAIT, AlternativeKind.KEEP_CASH, AlternativeKind.NO_ACTION)]
            if case_kind_indices and non_case_kind_indices:
                assert max(case_kind_indices) < min(non_case_kind_indices)
