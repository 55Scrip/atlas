"""Pure unit tests for `atlas.alpha.decision_explanation.engine` --
deduplication, traceability resolution, ordering, and change detection.
No I/O; every input is a hand-built domain object."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.decision_explanation.engine import (
    build_decision_explanation,
    build_portfolio_decision_explanation_breakdown,
    compare_decision_explanations,
    detect_decision_explanation_change,
    summarize_decision_explanation,
)
from atlas.alpha.decision_explanation.models import (
    ChangeDirection,
    DecisionExplanation,
    ExplanationLayer,
    ExplanationReference,
    ExplanationReferenceKind,
    ExplanationSectionKind,
)
from atlas.alpha.decision_path.models import (
    DecisionPath,
    DecisionStep,
    DependencyReference,
    DependencySource,
    FinalReachableState,
    ReachabilityStatus,
    RequiredProgressKind,
)
from atlas.alpha.decision_readiness.models import (
    DecisionBlocker,
    DecisionBlockerKind,
    DecisionReadiness,
    DecisionReadinessReason,
    DecisionReadinessReasonKind,
    DecisionReadinessStatus,
)
from atlas.alpha.evidence_graph.models import GraphNode, GraphNodeKind, WeakDependency, WeaknessKind
from atlas.alpha.investment_decision.models import DecisionAction, DecisionReason, DecisionReasonSource, InvestmentDecision
from atlas.alpha.recommendation_conviction.models import (
    ConvictionReason,
    ConvictionReasonSource,
    ConvictionStrength,
    RecommendationConviction,
    RecommendationStability,
)

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
_CASE_ID = "case-1"


def _decision(
    *,
    action: DecisionAction = DecisionAction.HOLD,
    supporting: tuple[DecisionReason, ...] = (),
    blockers: tuple[DecisionReason, ...] = (),
    change_trigger: DecisionReason | None = None,
) -> InvestmentDecision:
    return InvestmentDecision(
        case_id=_CASE_ID,
        action=action,
        qualifiers=(),
        supporting_reasons=supporting,
        blockers=blockers,
        change_trigger=change_trigger,
        generated_at=_NOW,
    )


def _conviction(
    *,
    strength: ConvictionStrength = ConvictionStrength.MODERATE,
    supporting: tuple[ConvictionReason, ...] = (),
    limiting: tuple[ConvictionReason, ...] = (),
    strengthening_trigger: ConvictionReason | None = None,
) -> RecommendationConviction:
    return RecommendationConviction(
        case_id=_CASE_ID,
        action=DecisionAction.HOLD,
        strength=strength,
        stability=RecommendationStability.STABLE,
        supporting_reasons=supporting,
        limiting_reasons=limiting,
        strengthening_trigger=strengthening_trigger,
        generated_at=_NOW,
    )


def _readiness(
    *,
    blockers: tuple[DecisionBlocker, ...] = (),
    supporting: tuple[DecisionReadinessReason, ...] = (),
) -> DecisionReadiness:
    return DecisionReadiness(
        case_id=_CASE_ID,
        status=DecisionReadinessStatus.WAITING,
        blockers=blockers,
        supporting_reasons=supporting,
        generated_at=_NOW,
    )


def _path(*, steps: tuple[DecisionStep, ...] = ()) -> DecisionPath:
    return DecisionPath(
        case_id=_CASE_ID,
        current_action=DecisionAction.HOLD,
        current_strength=ConvictionStrength.MODERATE,
        steps=steps,
        immediate_blocker=steps[0] if steps else None,
        next_achievable_improvement=None,
        final_reachable_state=FinalReachableState.FULLY_REACHABLE,
        generated_at=_NOW,
    )


def _build(
    *,
    decision: InvestmentDecision | None = None,
    conviction: RecommendationConviction | None = None,
    readiness: DecisionReadiness | None = None,
    path: DecisionPath | None = None,
    latest_snapshot_hash: str | None = None,
    weak_dependencies: tuple[WeakDependency, ...] = (),
    finding_nodes: tuple[GraphNode, ...] = (),
) -> DecisionExplanation:
    return build_decision_explanation(
        _CASE_ID,
        decision=decision if decision is not None else _decision(),
        conviction=conviction if conviction is not None else _conviction(),
        readiness=readiness if readiness is not None else _readiness(),
        path=path if path is not None else _path(),
        latest_snapshot_hash=latest_snapshot_hash,
        weak_dependencies=weak_dependencies,
        finding_nodes=finding_nodes,
        generated_at=_NOW,
    )


class TestBuildDecisionExplanation:
    def test_action_and_strength_are_re_expressed_verbatim(self):
        explanation = _build(
            decision=_decision(action=DecisionAction.REDUCE), conviction=_conviction(strength=ConvictionStrength.WEAK)
        )
        assert explanation.action is DecisionAction.REDUCE
        assert explanation.conviction_strength is ConvictionStrength.WEAK

    def test_supporting_reasons_are_carried_through_as_reason_code_references(self):
        decision = _decision(
            supporting=(DecisionReason(DecisionReasonSource.STANCE, "some_positive_signal"),)
        )
        explanation = _build(decision=decision)
        codes = [sf.reference.id for sf in explanation.chain.supporting]
        assert "some_positive_signal" in codes
        matching = next(sf for sf in explanation.chain.supporting if sf.reference.id == "some_positive_signal")
        assert matching.reference.kind is ExplanationReferenceKind.REASON_CODE

    def test_the_same_code_named_by_two_layers_is_counted_once(self):
        decision = _decision(blockers=(DecisionReason(DecisionReasonSource.READINESS_BLOCKER, "missing_thesis_evidence"),))
        conviction = _conviction(
            limiting=(ConvictionReason(ConvictionReasonSource.READINESS_BLOCKER, "missing_thesis_evidence"),)
        )
        readiness = _readiness(blockers=(DecisionBlocker(DecisionBlockerKind.MISSING_THESIS_EVIDENCE),))
        explanation = _build(decision=decision, conviction=conviction, readiness=readiness)
        matching = [bf for bf in explanation.chain.blocking if bf.reference.id == "missing_thesis_evidence"]
        assert len(matching) == 1
        assert set(matching[0].named_by) == {
            ExplanationLayer.INVESTMENT_DECISION,
            ExplanationLayer.RECOMMENDATION_CONVICTION,
            ExplanationLayer.DECISION_READINESS,
        }

    def test_change_trigger_is_flagged_on_the_matching_blocking_finding(self):
        trigger = DecisionReason(DecisionReasonSource.READINESS_BLOCKER, "missing_thesis_evidence")
        decision = _decision(blockers=(trigger,), change_trigger=trigger)
        explanation = _build(decision=decision)
        matching = next(bf for bf in explanation.chain.blocking if bf.reference.id == "missing_thesis_evidence")
        assert matching.is_change_trigger is True

    def test_a_blocker_that_is_not_the_change_trigger_is_not_flagged(self):
        decision = _decision(
            blockers=(
                DecisionReason(DecisionReasonSource.READINESS_BLOCKER, "missing_thesis_evidence"),
                DecisionReason(DecisionReasonSource.READINESS_BLOCKER, "coverage_incomplete"),
            ),
            change_trigger=DecisionReason(DecisionReasonSource.READINESS_BLOCKER, "missing_thesis_evidence"),
        )
        explanation = _build(decision=decision)
        other = next(bf for bf in explanation.chain.blocking if bf.reference.id == "coverage_incomplete")
        assert other.is_change_trigger is False

    def test_evidence_graph_weakness_resolves_to_real_finding_node_ids(self):
        conviction = _conviction(limiting=(ConvictionReason(ConvictionReasonSource.EVIDENCE_GRAPH, "no_support"),))
        weak_deps = (WeakDependency(node_id="finding-1", kind=WeaknessKind.NO_SUPPORT, detail=0),)
        finding_nodes = (GraphNode(id="finding-1", kind=GraphNodeKind.FINDING, case_id=_CASE_ID, recorded_at=_NOW),)
        explanation = _build(conviction=conviction, weak_dependencies=weak_deps, finding_nodes=finding_nodes)
        finding_refs = [bf for bf in explanation.chain.blocking if bf.reference.kind is ExplanationReferenceKind.FINDING]
        assert len(finding_refs) == 1
        assert finding_refs[0].reference.id == "finding-1"
        assert finding_refs[0].named_by == (ExplanationLayer.EVIDENCE_GRAPH,)

    def test_a_weak_dependency_node_id_not_present_as_a_finding_node_is_never_resolved(self):
        """Traceability never fabricates a node -- a `WeakDependency`
        pointing at a node id this graph snapshot doesn't actually
        carry as a `FINDING` (e.g. an `OBSERVATION`-kind weak node)
        must never surface as a `FINDING` reference."""
        conviction = _conviction(limiting=(ConvictionReason(ConvictionReasonSource.EVIDENCE_GRAPH, "isolated_chain"),))
        weak_deps = (WeakDependency(node_id="obs-1", kind=WeaknessKind.ISOLATED_CHAIN, detail=0),)
        explanation = _build(conviction=conviction, weak_dependencies=weak_deps, finding_nodes=())
        finding_refs = [bf for bf in explanation.chain.blocking if bf.reference.kind is ExplanationReferenceKind.FINDING]
        assert finding_refs == []

    def test_dependency_steps_are_carried_through_in_the_paths_own_order(self):
        steps = (
            DecisionStep(DependencyReference(DependencySource.READINESS_BLOCKER, "a"), RequiredProgressKind.EVIDENCE, ReachabilityStatus.REACHABLE),
            DecisionStep(DependencyReference(DependencySource.READINESS_BLOCKER, "b"), RequiredProgressKind.COVERAGE, ReachabilityStatus.BLOCKED),
        )
        explanation = _build(path=_path(steps=steps))
        assert [r.id for r in explanation.chain.dependency_steps] == ["a", "b"]

    def test_historical_reference_is_none_when_no_snapshot_hash_given(self):
        explanation = _build(latest_snapshot_hash=None)
        assert explanation.chain.historical_reference is None

    def test_historical_reference_points_at_the_real_snapshot_hash_when_given(self):
        explanation = _build(latest_snapshot_hash="abc123")
        assert explanation.chain.historical_reference == ExplanationReference(ExplanationReferenceKind.DECISION_SNAPSHOT, "abc123")

    def test_order_lists_all_four_sections_even_when_some_are_empty(self):
        explanation = _build()
        kinds = [s.kind for s in explanation.chain.order]
        assert kinds == [
            ExplanationSectionKind.SUPPORTING,
            ExplanationSectionKind.BLOCKING,
            ExplanationSectionKind.DEPENDENCY,
            ExplanationSectionKind.HISTORICAL,
        ]

    def test_primary_supporting_and_blocking_are_the_first_entries(self):
        decision = _decision(
            supporting=(DecisionReason(DecisionReasonSource.STANCE, "first"), DecisionReason(DecisionReasonSource.STANCE, "second")),
            blockers=(DecisionReason(DecisionReasonSource.READINESS_BLOCKER, "block-1"),),
        )
        explanation = _build(decision=decision)
        assert explanation.primary_supporting.reference.id == "first"
        assert explanation.primary_blocking.reference.id == "block-1"

    def test_no_supporting_reasons_produces_no_primary_supporting(self):
        explanation = _build(decision=_decision(supporting=()))
        assert explanation.primary_supporting is None

    def test_two_calls_with_identical_inputs_produce_identical_output(self):
        decision = _decision(supporting=(DecisionReason(DecisionReasonSource.STANCE, "x"),))
        first = _build(decision=decision)
        second = _build(decision=decision)
        assert first == second


class TestSummarize:
    def test_summary_carries_the_same_primary_facts(self):
        decision = _decision(supporting=(DecisionReason(DecisionReasonSource.STANCE, "x"),))
        explanation = _build(decision=decision)
        summary = summarize_decision_explanation(explanation)
        assert summary.primary_supporting == explanation.primary_supporting
        assert summary.case_id == explanation.case_id


class TestCompareDecisionExplanations:
    def test_never_declares_an_overall_winner(self):
        """Structural check -- no field on the comparison object names
        a preferred/winning side."""
        a = _build(decision=_decision())
        b = _build(decision=_decision())
        comparison = compare_decision_explanations(a, b)
        field_names = set(comparison.__dataclass_fields__.keys())
        assert not any("winner" in f or "preferred" in f or "better" in f for f in field_names)

    def test_shared_supporting_is_the_real_intersection_and_keeps_its_reference_kind(self):
        a = _build(decision=_decision(supporting=(DecisionReason(DecisionReasonSource.STANCE, "shared"), DecisionReason(DecisionReasonSource.STANCE, "only_a"))))
        b = _build(decision=_decision(supporting=(DecisionReason(DecisionReasonSource.STANCE, "shared"), DecisionReason(DecisionReasonSource.STANCE, "only_b"))))
        comparison = compare_decision_explanations(a, b)
        assert [r.id for r in comparison.shared_supporting] == ["shared"]
        assert comparison.shared_supporting[0].kind is ExplanationReferenceKind.REASON_CODE

    def test_differing_blocking_is_each_sides_own_unique_set(self):
        a = _build(decision=_decision(blockers=(DecisionReason(DecisionReasonSource.READINESS_BLOCKER, "a_only"),)))
        b = _build(decision=_decision(blockers=(DecisionReason(DecisionReasonSource.READINESS_BLOCKER, "b_only"),)))
        comparison = compare_decision_explanations(a, b)
        assert [r.id for r in comparison.differing_blocking_a] == ["a_only"]
        assert [r.id for r in comparison.differing_blocking_b] == ["b_only"]

    def test_shared_dependencies_is_the_real_intersection(self):
        step = DecisionStep(DependencyReference(DependencySource.READINESS_BLOCKER, "shared_step"), RequiredProgressKind.EVIDENCE, ReachabilityStatus.REACHABLE)
        a = _build(path=_path(steps=(step,)))
        b = _build(path=_path(steps=(step,)))
        comparison = compare_decision_explanations(a, b)
        assert [r.id for r in comparison.shared_dependencies] == ["shared_step"]

    def test_a_finding_kind_reference_keeps_its_kind_through_comparison(self):
        """The bug this test guards: a comparison result must never
        collapse a `FINDING`-kind reference down to a bare id string --
        doing so would make the frontend unable to distinguish it from
        a `REASON_CODE`, rendering a raw technical Finding id as if it
        were prose (found and fixed during Sprint 6 Live Verification)."""
        conviction = _conviction(limiting=(ConvictionReason(ConvictionReasonSource.EVIDENCE_GRAPH, "no_support"),))
        weak_deps = (WeakDependency(node_id="finding-1", kind=WeaknessKind.NO_SUPPORT, detail=0),)
        finding_nodes = (GraphNode(id="finding-1", kind=GraphNodeKind.FINDING, case_id=_CASE_ID, recorded_at=_NOW),)
        a = _build(conviction=conviction, weak_dependencies=weak_deps, finding_nodes=finding_nodes)
        b = _build(decision=_decision())
        comparison = compare_decision_explanations(a, b)
        finding_ref = next(r for r in comparison.differing_blocking_a if r.id == "finding-1")
        assert finding_ref.kind is ExplanationReferenceKind.FINDING


class TestDetectDecisionExplanationChange:
    def test_first_ever_computation_produces_no_change(self):
        current = _build()
        assert detect_decision_explanation_change(None, current, detected_at=_NOW) is None

    def test_an_unchanged_explanation_produces_no_change(self):
        decision = _decision(supporting=(DecisionReason(DecisionReasonSource.STANCE, "x"),))
        previous = _build(decision=decision)
        current = _build(decision=decision)
        assert detect_decision_explanation_change(previous, current, detected_at=_NOW) is None

    def test_a_new_supporting_finding_is_detected(self):
        previous = _build(decision=_decision(supporting=()))
        current = _build(decision=_decision(supporting=(DecisionReason(DecisionReasonSource.STANCE, "new_one"),)))
        change = detect_decision_explanation_change(previous, current, detected_at=_NOW)
        assert change is not None
        assert [sf.reference.id for sf in change.new_supporting] == ["new_one"]
        assert change.evidence_expanded is True

    def test_a_resolved_blocker_is_detected(self):
        previous = _build(decision=_decision(blockers=(DecisionReason(DecisionReasonSource.READINESS_BLOCKER, "gone"),)))
        current = _build(decision=_decision(blockers=()))
        change = detect_decision_explanation_change(previous, current, detected_at=_NOW)
        assert change is not None
        assert [bf.reference.id for bf in change.resolved_blocking] == ["gone"]

    def test_a_new_blocker_is_detected(self):
        previous = _build(decision=_decision(blockers=()))
        current = _build(decision=_decision(blockers=(DecisionReason(DecisionReasonSource.READINESS_BLOCKER, "new_block"),)))
        change = detect_decision_explanation_change(previous, current, detected_at=_NOW)
        assert change is not None
        assert [bf.reference.id for bf in change.new_blocking] == ["new_block"]

    def test_conviction_strengthening_is_detected(self):
        previous = _build(conviction=_conviction(strength=ConvictionStrength.WEAK))
        current = _build(conviction=_conviction(strength=ConvictionStrength.STRONG))
        change = detect_decision_explanation_change(previous, current, detected_at=_NOW)
        assert change is not None
        assert change.conviction_direction is ChangeDirection.STRONGER

    def test_conviction_weakening_is_detected(self):
        previous = _build(conviction=_conviction(strength=ConvictionStrength.STRONG))
        current = _build(conviction=_conviction(strength=ConvictionStrength.WEAK))
        change = detect_decision_explanation_change(previous, current, detected_at=_NOW)
        assert change is not None
        assert change.conviction_direction is ChangeDirection.WEAKER

    def test_evidence_expanded_is_false_when_supporting_count_did_not_grow(self):
        previous = _build(decision=_decision(supporting=(DecisionReason(DecisionReasonSource.STANCE, "x"),)))
        current = _build(
            decision=_decision(supporting=(DecisionReason(DecisionReasonSource.STANCE, "x"),)),
            conviction=_conviction(strength=ConvictionStrength.STRONG),
        )
        change = detect_decision_explanation_change(previous, current, detected_at=_NOW)
        assert change is not None
        assert change.evidence_expanded is False


class TestPortfolioDecisionExplanationBreakdown:
    def test_buckets_are_built_from_real_per_ticker_changes(self):
        strengthened_change = detect_decision_explanation_change(
            _build(conviction=_conviction(strength=ConvictionStrength.WEAK)),
            _build(conviction=_conviction(strength=ConvictionStrength.STRONG)),
            detected_at=_NOW,
        )
        items = (
            ("AAPL", None),
            ("MSFT", strengthened_change),
        )
        breakdown = build_portfolio_decision_explanation_breakdown(items)
        assert breakdown.recently_changed == ("MSFT",)
        assert breakdown.recently_strengthened == ("MSFT",)
        assert "AAPL" not in breakdown.recently_changed
