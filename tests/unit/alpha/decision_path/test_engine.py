"""Tests for `atlas.alpha.decision_path.engine` -- the progress-kind
classification, the reachability waterfall (including the `NO_DATA
_SOURCE` cascade and the "permanent dependency gap" check), and the
summary/compare/change-detection helpers."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.decision_path.engine import (
    DecisionPathInputs,
    build_decision_path,
    build_portfolio_decision_path_breakdown,
    compare_decision_paths,
    detect_decision_path_change,
    summarize_decision_path,
)
from atlas.alpha.decision_path.models import (
    DependencyReference,
    DependencySource,
    FinalReachableState,
    ReachabilityStatus,
    RequiredProgressKind,
)
from atlas.alpha.decision_readiness.models import (
    DecisionBlocker,
    DecisionBlockerKind,
    DecisionReadinessReason,
    DecisionReadinessReasonKind,
    DecisionReadinessStatus,
)
from atlas.alpha.evidence_graph.models import WeakDependency, WeaknessKind
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.recommendation_conviction.models import ConvictionStrength

NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)


def _inputs(**overrides) -> DecisionPathInputs:
    """A fully "healthy, no blockers" baseline -- every test overrides
    only the field(s) it actually cares about."""
    base = dict(
        action=DecisionAction.HOLD,
        strength=ConvictionStrength.STRONG,
        readiness_status=DecisionReadinessStatus.READY,
        readiness_blockers=(),
        readiness_supporting_reasons=(DecisionReadinessReason(DecisionReadinessReasonKind.CONFIDENCE_ESTABLISHED),),
        weak_dependencies=(),
        graph_node_details_by_id={},
    )
    base.update(overrides)
    return DecisionPathInputs(**base)


class TestProgressKindMapping:
    def test_every_blocker_kind_is_classified(self):
        from atlas.alpha.decision_path.engine import _PROGRESS_KIND_BY_BLOCKER

        assert set(_PROGRESS_KIND_BY_BLOCKER.keys()) == set(DecisionBlockerKind)

    def test_operational_blockers(self):
        path = build_decision_path(
            "c1",
            _inputs(
                readiness_status=DecisionReadinessStatus.WAITING,
                readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),),
            ),
            generated_at=NOW,
        )
        assert path.steps[0].progress_kind is RequiredProgressKind.OPERATIONAL

    def test_evidence_blockers(self):
        path = build_decision_path(
            "c1",
            _inputs(
                readiness_status=DecisionReadinessStatus.WAITING,
                readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MISSING_THESIS_EVIDENCE),),
            ),
            generated_at=NOW,
        )
        assert path.steps[0].progress_kind is RequiredProgressKind.EVIDENCE

    def test_coverage_blocker(self):
        path = build_decision_path(
            "c1",
            _inputs(
                readiness_status=DecisionReadinessStatus.WAITING,
                readiness_blockers=(DecisionBlocker(DecisionBlockerKind.COVERAGE_INCOMPLETE),),
            ),
            generated_at=NOW,
        )
        assert path.steps[0].progress_kind is RequiredProgressKind.COVERAGE

    def test_dependency_blocker(self):
        path = build_decision_path(
            "c1",
            _inputs(
                readiness_status=DecisionReadinessStatus.WAITING,
                readiness_blockers=(DecisionBlocker(DecisionBlockerKind.CRITICAL_DEPENDENCY_UNRESOLVED),),
            ),
            generated_at=NOW,
        )
        assert path.steps[0].progress_kind is RequiredProgressKind.DEPENDENCY

    def test_decision_blocker(self):
        path = build_decision_path(
            "c1",
            _inputs(
                readiness_status=DecisionReadinessStatus.BLOCKED,
                readiness_blockers=(DecisionBlocker(DecisionBlockerKind.AVOID_DECISION_SIGNAL),),
            ),
            generated_at=NOW,
        )
        assert path.steps[0].progress_kind is RequiredProgressKind.DECISION


class TestReachability:
    def test_operational_blockers_are_reachable(self):
        for kind in (
            DecisionBlockerKind.NEVER_EVALUATED,
            DecisionBlockerKind.MONITORING_FAILED,
            DecisionBlockerKind.MONITORING_PENDING,
            DecisionBlockerKind.OPERATIONAL_FRESHNESS_OUTDATED,
        ):
            path = build_decision_path(
                "c1", _inputs(readiness_status=DecisionReadinessStatus.WAITING, readiness_blockers=(DecisionBlocker(kind),)), generated_at=NOW
            )
            assert path.steps[0].reachability is ReachabilityStatus.REACHABLE

    def test_no_data_source_is_not_reachable(self):
        path = build_decision_path(
            "c1",
            _inputs(readiness_status=DecisionReadinessStatus.UNAVAILABLE, readiness_blockers=(DecisionBlocker(DecisionBlockerKind.NO_DATA_SOURCE),)),
            generated_at=NOW,
        )
        assert path.steps[0].reachability is ReachabilityStatus.NOT_REACHABLE

    def test_no_data_source_downgrades_every_other_step_to_blocked(self):
        path = build_decision_path(
            "c1",
            _inputs(
                readiness_status=DecisionReadinessStatus.UNAVAILABLE,
                readiness_blockers=(
                    DecisionBlocker(DecisionBlockerKind.NO_DATA_SOURCE),
                    DecisionBlocker(DecisionBlockerKind.COVERAGE_INCOMPLETE),
                    DecisionBlocker(DecisionBlockerKind.MISSING_THESIS_EVIDENCE),
                ),
            ),
            generated_at=NOW,
        )
        by_code = {s.dependency.code: s for s in path.steps}
        assert by_code["no_data_source"].reachability is ReachabilityStatus.NOT_REACHABLE
        assert by_code["coverage_incomplete"].reachability is ReachabilityStatus.BLOCKED
        assert by_code["missing_thesis_evidence"].reachability is ReachabilityStatus.BLOCKED

    def test_evidence_blockers_are_reachable_without_no_data_source(self):
        path = build_decision_path(
            "c1",
            _inputs(readiness_status=DecisionReadinessStatus.WAITING, readiness_blockers=(DecisionBlocker(DecisionBlockerKind.INSUFFICIENT_EVIDENCE),)),
            generated_at=NOW,
        )
        assert path.steps[0].reachability is ReachabilityStatus.REACHABLE

    def test_critical_dependency_is_reachable_by_default(self):
        path = build_decision_path(
            "c1",
            _inputs(
                readiness_status=DecisionReadinessStatus.WAITING,
                readiness_blockers=(DecisionBlocker(DecisionBlockerKind.CRITICAL_DEPENDENCY_UNRESOLVED),),
            ),
            generated_at=NOW,
        )
        assert path.steps[0].reachability is ReachabilityStatus.REACHABLE

    def test_critical_dependency_on_a_permanently_locked_business_category_is_not_reachable(self):
        path = build_decision_path(
            "c1",
            _inputs(
                readiness_status=DecisionReadinessStatus.WAITING,
                readiness_blockers=(DecisionBlocker(DecisionBlockerKind.CRITICAL_DEPENDENCY_UNRESOLVED),),
                weak_dependencies=(WeakDependency(node_id="n1", kind=WeaknessKind.CRITICAL_DEPENDENCY, detail=3),),
                graph_node_details_by_id={"n1": {"kind": "business_category_assessed", "category": "business_model", "status": "insufficient_input"}},
            ),
            generated_at=NOW,
        )
        assert path.steps[0].reachability is ReachabilityStatus.NOT_REACHABLE

    def test_critical_dependency_on_a_permanently_locked_valuation_method_is_not_reachable(self):
        path = build_decision_path(
            "c1",
            _inputs(
                readiness_status=DecisionReadinessStatus.WAITING,
                readiness_blockers=(DecisionBlocker(DecisionBlockerKind.CRITICAL_DEPENDENCY_UNRESOLVED),),
                weak_dependencies=(WeakDependency(node_id="n1", kind=WeaknessKind.CRITICAL_DEPENDENCY, detail=3),),
                graph_node_details_by_id={"n1": {"kind": "valuation_method_assessed", "method": "scenario_base", "status": "insufficient_input"}},
            ),
            generated_at=NOW,
        )
        assert path.steps[0].reachability is ReachabilityStatus.NOT_REACHABLE

    def test_critical_dependency_on_a_real_evaluator_stays_reachable(self):
        path = build_decision_path(
            "c1",
            _inputs(
                readiness_status=DecisionReadinessStatus.WAITING,
                readiness_blockers=(DecisionBlocker(DecisionBlockerKind.CRITICAL_DEPENDENCY_UNRESOLVED),),
                weak_dependencies=(WeakDependency(node_id="n1", kind=WeaknessKind.CRITICAL_DEPENDENCY, detail=3),),
                graph_node_details_by_id={"n1": {"kind": "business_category_assessed", "category": "capital_allocation", "status": "weak"}},
            ),
            generated_at=NOW,
        )
        assert path.steps[0].reachability is ReachabilityStatus.REACHABLE

    def test_critical_dependency_with_no_matching_weak_dependency_stays_reachable(self):
        """A `CRITICAL_DEPENDENCY_UNRESOLVED` blocker with no
        corresponding Evidence Graph entry (an honest data gap between
        the two sibling services) never crashes and never fabricates
        a permanent-lock finding."""
        path = build_decision_path(
            "c1",
            _inputs(readiness_status=DecisionReadinessStatus.WAITING, readiness_blockers=(DecisionBlocker(DecisionBlockerKind.CRITICAL_DEPENDENCY_UNRESOLVED),)),
            generated_at=NOW,
        )
        assert path.steps[0].reachability is ReachabilityStatus.REACHABLE


class TestReadinessProgressStep:
    def test_almost_ready_without_confidence_established_adds_a_readiness_step(self):
        path = build_decision_path(
            "c1", _inputs(readiness_status=DecisionReadinessStatus.ALMOST_READY, readiness_supporting_reasons=()), generated_at=NOW
        )
        assert len(path.steps) == 1
        assert path.steps[0].progress_kind is RequiredProgressKind.READINESS
        assert path.steps[0].dependency == DependencyReference(DependencySource.READINESS_PROGRESS, "confidence_established")
        assert path.steps[0].reachability is ReachabilityStatus.REACHABLE

    def test_almost_ready_with_confidence_established_already_present_adds_no_step(self):
        path = build_decision_path(
            "c1",
            _inputs(
                readiness_status=DecisionReadinessStatus.ALMOST_READY,
                readiness_supporting_reasons=(DecisionReadinessReason(DecisionReadinessReasonKind.CONFIDENCE_ESTABLISHED),),
            ),
            generated_at=NOW,
        )
        assert path.steps == ()

    def test_ready_status_never_adds_a_readiness_step(self):
        path = build_decision_path("c1", _inputs(readiness_status=DecisionReadinessStatus.READY), generated_at=NOW)
        assert path.steps == ()

    def test_readiness_step_follows_the_no_data_source_cascade(self):
        path = build_decision_path(
            "c1",
            _inputs(
                readiness_status=DecisionReadinessStatus.ALMOST_READY,
                readiness_supporting_reasons=(),
                readiness_blockers=(DecisionBlocker(DecisionBlockerKind.NO_DATA_SOURCE),),
            ),
            generated_at=NOW,
        )
        readiness_step = next(s for s in path.steps if s.progress_kind is RequiredProgressKind.READINESS)
        assert readiness_step.reachability is ReachabilityStatus.BLOCKED


class TestImmediateBlockerAndNextAchievable:
    def test_immediate_blocker_is_the_first_step(self):
        path = build_decision_path(
            "c1",
            _inputs(
                readiness_status=DecisionReadinessStatus.WAITING,
                readiness_blockers=(
                    DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),
                    DecisionBlocker(DecisionBlockerKind.COVERAGE_INCOMPLETE),
                ),
            ),
            generated_at=NOW,
        )
        assert path.immediate_blocker == path.steps[0]

    def test_next_achievable_improvement_skips_a_leading_not_reachable_step(self):
        path = build_decision_path(
            "c1",
            _inputs(
                readiness_status=DecisionReadinessStatus.UNAVAILABLE,
                readiness_blockers=(
                    DecisionBlocker(DecisionBlockerKind.NO_DATA_SOURCE),
                    DecisionBlocker(DecisionBlockerKind.COVERAGE_INCOMPLETE),
                ),
            ),
            generated_at=NOW,
        )
        assert path.immediate_blocker.dependency.code == "no_data_source"
        assert path.next_achievable_improvement is None  # everything else is BLOCKED, not REACHABLE

    def test_no_steps_means_both_are_none(self):
        path = build_decision_path("c1", _inputs(readiness_status=DecisionReadinessStatus.READY), generated_at=NOW)
        assert path.immediate_blocker is None
        assert path.next_achievable_improvement is None


class TestFinalReachableState:
    def test_no_steps_is_already_reached(self):
        path = build_decision_path("c1", _inputs(readiness_status=DecisionReadinessStatus.READY), generated_at=NOW)
        assert path.final_reachable_state is FinalReachableState.ALREADY_REACHED

    def test_all_reachable_steps_is_fully_reachable(self):
        path = build_decision_path(
            "c1", _inputs(readiness_status=DecisionReadinessStatus.WAITING, readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),)), generated_at=NOW
        )
        assert path.final_reachable_state is FinalReachableState.FULLY_REACHABLE

    def test_a_permanent_not_reachable_step_alongside_a_reachable_one_is_partially_reachable(self):
        path = build_decision_path(
            "c1",
            _inputs(
                readiness_status=DecisionReadinessStatus.WAITING,
                readiness_blockers=(
                    DecisionBlocker(DecisionBlockerKind.CRITICAL_DEPENDENCY_UNRESOLVED),
                    DecisionBlocker(DecisionBlockerKind.MISSING_OBSERVATION),
                ),
                weak_dependencies=(WeakDependency(node_id="n1", kind=WeaknessKind.CRITICAL_DEPENDENCY, detail=3),),
                graph_node_details_by_id={"n1": {"kind": "business_category_assessed", "category": "durability", "status": "insufficient_input"}},
            ),
            generated_at=NOW,
        )
        assert path.final_reachable_state is FinalReachableState.PARTIALLY_REACHABLE

    def test_only_no_data_source_present_is_not_reachable(self):
        path = build_decision_path(
            "c1", _inputs(readiness_status=DecisionReadinessStatus.UNAVAILABLE, readiness_blockers=(DecisionBlocker(DecisionBlockerKind.NO_DATA_SOURCE),)), generated_at=NOW
        )
        assert path.final_reachable_state is FinalReachableState.NOT_REACHABLE


class TestSummarizeDecisionPath:
    def test_fields_mirror_the_path(self):
        path = build_decision_path(
            "c1", _inputs(readiness_status=DecisionReadinessStatus.WAITING, readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),)), generated_at=NOW
        )
        summary = summarize_decision_path(path)
        assert summary.immediate_blocker == path.immediate_blocker
        assert summary.next_achievable_improvement == path.next_achievable_improvement
        assert summary.remaining_step_count == len(path.steps)


class TestCompareDecisionPaths:
    def test_shorter_path_counts_only_non_permanent_steps(self):
        a = build_decision_path("a", _inputs(readiness_status=DecisionReadinessStatus.READY), generated_at=NOW)
        b = build_decision_path(
            "b", _inputs(readiness_status=DecisionReadinessStatus.WAITING, readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),)), generated_at=NOW
        )
        comparison = compare_decision_paths(a, b)
        assert comparison.shorter_path_case_id == "a"

    def test_tie_is_none(self):
        a = build_decision_path("a", _inputs(readiness_status=DecisionReadinessStatus.READY), generated_at=NOW)
        b = build_decision_path("b", _inputs(readiness_status=DecisionReadinessStatus.READY), generated_at=NOW)
        comparison = compare_decision_paths(a, b)
        assert comparison.shorter_path_case_id is None
        assert comparison.fewer_remaining_blockers_case_id is None

    def test_more_operationally_dependent(self):
        a = build_decision_path("a", _inputs(readiness_status=DecisionReadinessStatus.READY), generated_at=NOW)
        b = build_decision_path(
            "b", _inputs(readiness_status=DecisionReadinessStatus.WAITING, readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),)), generated_at=NOW
        )
        comparison = compare_decision_paths(a, b)
        assert comparison.more_operationally_dependent_case_id == "b"

    def test_more_evidence_dependent(self):
        a = build_decision_path("a", _inputs(readiness_status=DecisionReadinessStatus.READY), generated_at=NOW)
        b = build_decision_path(
            "b", _inputs(readiness_status=DecisionReadinessStatus.WAITING, readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MISSING_THESIS_EVIDENCE),)), generated_at=NOW
        )
        comparison = compare_decision_paths(a, b)
        assert comparison.more_evidence_dependent_case_id == "b"

    def test_comparison_never_names_an_overall_winner(self):
        a = build_decision_path("a", _inputs(readiness_status=DecisionReadinessStatus.READY), generated_at=NOW)
        b = build_decision_path(
            "b", _inputs(readiness_status=DecisionReadinessStatus.UNAVAILABLE, readiness_blockers=(DecisionBlocker(DecisionBlockerKind.NO_DATA_SOURCE),)), generated_at=NOW
        )
        comparison = compare_decision_paths(a, b)
        field_names = set(comparison.__dataclass_fields__.keys())
        assert field_names == {
            "a",
            "b",
            "shorter_path_case_id",
            "fewer_remaining_blockers_case_id",
            "more_operationally_dependent_case_id",
            "more_evidence_dependent_case_id",
        }


class TestDetectDecisionPathChange:
    def test_no_previous_computation_produces_no_change(self):
        current = build_decision_path("c1", _inputs(readiness_status=DecisionReadinessStatus.READY), generated_at=NOW)
        assert detect_decision_path_change(None, current, detected_at=NOW) is None

    def test_identical_state_and_steps_produce_no_change(self):
        previous = build_decision_path(
            "c1", _inputs(readiness_status=DecisionReadinessStatus.WAITING, readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),)), generated_at=NOW
        )
        current = build_decision_path(
            "c1", _inputs(readiness_status=DecisionReadinessStatus.WAITING, readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),)), generated_at=NOW
        )
        assert detect_decision_path_change(previous, current, detected_at=NOW) is None

    def test_a_resolved_blocker_is_reported(self):
        previous = build_decision_path(
            "c1", _inputs(readiness_status=DecisionReadinessStatus.WAITING, readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),)), generated_at=NOW
        )
        current = build_decision_path("c1", _inputs(readiness_status=DecisionReadinessStatus.READY), generated_at=NOW)
        change = detect_decision_path_change(previous, current, detected_at=NOW)
        assert change is not None
        assert change.previous_final_reachable_state is FinalReachableState.FULLY_REACHABLE
        assert change.current_final_reachable_state is FinalReachableState.ALREADY_REACHED
        assert len(change.resolved_steps) == 1
        assert change.resolved_steps[0].dependency.code == "monitoring_pending"
        assert change.new_steps == ()


class TestPortfolioDecisionPathBreakdown:
    def test_buckets_by_progress_kind_and_final_state(self):
        close = build_decision_path("a", _inputs(readiness_status=DecisionReadinessStatus.READY), generated_at=NOW)
        operational = build_decision_path(
            "b",
            _inputs(
                readiness_status=DecisionReadinessStatus.WAITING,
                readiness_blockers=(
                    DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),
                    DecisionBlocker(DecisionBlockerKind.MONITORING_FAILED),
                ),
            ),
            generated_at=NOW,
        )
        evidence = build_decision_path(
            "c",
            _inputs(
                readiness_status=DecisionReadinessStatus.WAITING,
                readiness_blockers=(
                    DecisionBlocker(DecisionBlockerKind.MISSING_THESIS_EVIDENCE),
                    DecisionBlocker(DecisionBlockerKind.INSUFFICIENT_EVIDENCE),
                ),
            ),
            generated_at=NOW,
        )
        dependency = build_decision_path(
            "d",
            _inputs(
                readiness_status=DecisionReadinessStatus.BLOCKED,
                readiness_blockers=(
                    DecisionBlocker(DecisionBlockerKind.CRITICAL_DEPENDENCY_UNRESOLVED),
                    DecisionBlocker(DecisionBlockerKind.AVOID_DECISION_SIGNAL),
                ),
            ),
            generated_at=NOW,
        )
        items = (("AAPL", close), ("MSFT", operational), ("NVDA", evidence), ("GOOGL", dependency))
        breakdown = build_portfolio_decision_path_breakdown(items)
        assert breakdown.closest_to_investable == ("AAPL",)
        assert breakdown.operationally_blocked == ("MSFT",)
        assert breakdown.requiring_more_evidence == ("NVDA",)
        assert breakdown.requiring_dependency_resolution == ("GOOGL",)
