"""The Decision Path engine itself -- pure, deterministic, no I/O.
Given the exact same `DecisionPathInputs`, every function here always
returns the exact same result.

**Every step is built directly from `DecisionReadiness.blockers`
(Sprint 11), never re-derived.** This engine classifies each already-
real blocker along two axes this codebase has never named before:
`RequiredProgressKind` (which category of progress would resolve it)
and `ReachabilityStatus` (whether a real pathway to resolve it exists
in this codebase today). Neither axis invents a new fact -- see this
package's own `__init__.py` for the full audit each classification is
based on.

**The `NO_DATA_SOURCE` cascade.** When no external data source is
connected for a Case, *nothing* else about that Case can genuinely
progress -- Coverage cannot expand, Evidence cannot be recorded,
Monitoring has nothing new to check. This is a real, structural fact,
not a judgment call: every other present step's `ReachabilityStatus`
is downgraded from its own intrinsic classification to `BLOCKED`
while `NO_DATA_SOURCE` itself persists (`_effective_reachability`
below) -- the one genuine dependency-ordering fact Deliverable 1's own
audit found among the 13 `DecisionBlockerKind` members.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.alpha.decision_readiness.models import (
    DecisionBlocker,
    DecisionBlockerKind,
    DecisionReadinessReason,
    DecisionReadinessReasonKind,
    DecisionReadinessStatus,
)
from atlas.alpha.decision_path.models import (
    DecisionPath,
    DecisionPathChange,
    DecisionPathComparison,
    DecisionPathSummary,
    DecisionStep,
    DependencyReference,
    DependencySource,
    FinalReachableState,
    PortfolioDecisionPathBreakdown,
    ReachabilityStatus,
    RequiredProgressKind,
)
from atlas.alpha.evidence_graph.models import WeakDependency, WeaknessKind
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.recommendation_conviction.models import ConvictionStrength

__all__ = [
    "DecisionPathInputs",
    "build_decision_path",
    "summarize_decision_path",
    "compare_decision_paths",
    "detect_decision_path_change",
    "build_portfolio_decision_path_breakdown",
]


@dataclass(frozen=True)
class DecisionPathInputs:
    action: DecisionAction
    strength: ConvictionStrength
    readiness_status: DecisionReadinessStatus
    readiness_blockers: tuple[DecisionBlocker, ...]
    readiness_supporting_reasons: tuple[DecisionReadinessReason, ...]
    weak_dependencies: tuple[WeakDependency, ...]
    graph_node_details_by_id: dict[str, dict]
    """Deliverable 1's own "permanent dependency gap" check needs the
    Evidence Graph node a `CRITICAL_DEPENDENCY` weak link points at --
    built by the caller from `CaseEvidenceGraph.graph.nodes`, never
    recomputed here."""


_PROGRESS_KIND_BY_BLOCKER: dict[DecisionBlockerKind, RequiredProgressKind] = {
    DecisionBlockerKind.NEVER_EVALUATED: RequiredProgressKind.OPERATIONAL,
    DecisionBlockerKind.MONITORING_FAILED: RequiredProgressKind.OPERATIONAL,
    DecisionBlockerKind.MONITORING_PENDING: RequiredProgressKind.OPERATIONAL,
    DecisionBlockerKind.OPERATIONAL_FRESHNESS_OUTDATED: RequiredProgressKind.OPERATIONAL,
    DecisionBlockerKind.NO_DATA_SOURCE: RequiredProgressKind.OPERATIONAL,
    DecisionBlockerKind.CONFLICTING_EVIDENCE: RequiredProgressKind.EVIDENCE,
    DecisionBlockerKind.INSUFFICIENT_EVIDENCE: RequiredProgressKind.EVIDENCE,
    DecisionBlockerKind.MISSING_OBSERVATION: RequiredProgressKind.EVIDENCE,
    DecisionBlockerKind.MISSING_THESIS_EVIDENCE: RequiredProgressKind.EVIDENCE,
    DecisionBlockerKind.UNKNOWN_VALUATION: RequiredProgressKind.EVIDENCE,
    DecisionBlockerKind.COVERAGE_INCOMPLETE: RequiredProgressKind.COVERAGE,
    DecisionBlockerKind.CRITICAL_DEPENDENCY_UNRESOLVED: RequiredProgressKind.DEPENDENCY,
    DecisionBlockerKind.AVOID_DECISION_SIGNAL: RequiredProgressKind.DECISION,
}
"""Deliverable 4's own exhaustive classification -- every one of the
13 `DecisionBlockerKind` members belongs to exactly one of the six
`RequiredProgressKind` categories. `READINESS` has no
`DecisionBlockerKind` of its own -- see `DependencySource
.READINESS_PROGRESS` in `models.py`."""

_INTRINSICALLY_NOT_REACHABLE_BLOCKER_KINDS = frozenset({DecisionBlockerKind.NO_DATA_SOURCE})
"""Deliverable 1's audit: of the 13 blockers, only `NO_DATA_SOURCE`
names an unconditional architectural absence -- no external data
connector exists in this codebase today, and none of the other 12
blockers name a permanently-unfillable gap on their own (each has a
real, already-existing recording/operational pathway). `CRITICAL
_DEPENDENCY_UNRESOLVED` is the one *conditional* case -- see
`_critical_dependency_is_permanently_locked` below."""

_PERMANENTLY_LOCKED_BUSINESS_CATEGORIES = frozenset({"business_model", "competitive_position", "management", "durability"})
"""Atlas Intelligence Sprint 12's own finding, reused verbatim: these
four of `BusinessCategory`'s six members are permanently
`INSUFFICIENT_INPUT` -- no Core domain object carries category-
attributed qualitative evidence, and semantic/NLP parsing of filing
text is explicitly, permanently forbidden (`atlas.analysis_engine
.business`'s own module docstring)."""

_PERMANENTLY_LOCKED_VALUATION_METHODS = frozenset({"scenario_bear", "scenario_base", "scenario_bull"})
"""`ValuationMethodKind`'s own docstring: always `INSUFFICIENT_INPUT`
this sprint, permanently -- fabricating forward assumptions is
refused."""


def _is_permanently_locked_node(details: dict) -> bool:
    node_kind = details.get("kind")
    if node_kind == "business_category_assessed":
        return details.get("category") in _PERMANENTLY_LOCKED_BUSINESS_CATEGORIES
    if node_kind == "valuation_method_assessed":
        return details.get("method") in _PERMANENTLY_LOCKED_VALUATION_METHODS
    return False


def _critical_dependency_is_permanently_locked(inputs: DecisionPathInputs) -> bool:
    """The one real "permanent dependency gap" instance this codebase
    can honestly name: a `CRITICAL_DEPENDENCY` weak link (Sprint 10)
    whose own underlying node is a business-quality category or
    valuation method this codebase has permanently refused to
    evaluate (Sprint 12's own finding)."""
    for dependency in inputs.weak_dependencies:
        if dependency.kind is not WeaknessKind.CRITICAL_DEPENDENCY:
            continue
        details = inputs.graph_node_details_by_id.get(dependency.node_id)
        if details is not None and _is_permanently_locked_node(details):
            return True
    return False


def _intrinsic_reachability(blocker_kind: DecisionBlockerKind, inputs: DecisionPathInputs) -> ReachabilityStatus:
    if blocker_kind in _INTRINSICALLY_NOT_REACHABLE_BLOCKER_KINDS:
        return ReachabilityStatus.NOT_REACHABLE
    if blocker_kind is DecisionBlockerKind.CRITICAL_DEPENDENCY_UNRESOLVED and _critical_dependency_is_permanently_locked(inputs):
        return ReachabilityStatus.NOT_REACHABLE
    return ReachabilityStatus.REACHABLE


def _effective_reachability(
    intrinsic: ReachabilityStatus, blocker_kind: DecisionBlockerKind | None, no_data_source_present: bool
) -> ReachabilityStatus:
    if intrinsic is ReachabilityStatus.NOT_REACHABLE:
        return ReachabilityStatus.NOT_REACHABLE
    if no_data_source_present and blocker_kind is not DecisionBlockerKind.NO_DATA_SOURCE:
        return ReachabilityStatus.BLOCKED
    return intrinsic


def _derive_final_reachable_state(steps: tuple[DecisionStep, ...]) -> FinalReachableState:
    if not steps:
        return FinalReachableState.ALREADY_REACHED
    if not any(s.reachability is ReachabilityStatus.REACHABLE for s in steps):
        return FinalReachableState.NOT_REACHABLE
    if any(s.reachability is ReachabilityStatus.NOT_REACHABLE for s in steps):
        return FinalReachableState.PARTIALLY_REACHABLE
    return FinalReachableState.FULLY_REACHABLE


def build_decision_path(case_id: str, inputs: DecisionPathInputs, *, generated_at: datetime) -> DecisionPath:
    no_data_source_present = any(b.kind is DecisionBlockerKind.NO_DATA_SOURCE for b in inputs.readiness_blockers)

    steps: list[DecisionStep] = []
    for blocker in inputs.readiness_blockers:
        intrinsic = _intrinsic_reachability(blocker.kind, inputs)
        steps.append(
            DecisionStep(
                dependency=DependencyReference(DependencySource.READINESS_BLOCKER, blocker.kind.value),
                progress_kind=_PROGRESS_KIND_BY_BLOCKER[blocker.kind],
                reachability=_effective_reachability(intrinsic, blocker.kind, no_data_source_present),
            )
        )

    confidence_established = any(
        r.kind is DecisionReadinessReasonKind.CONFIDENCE_ESTABLISHED for r in inputs.readiness_supporting_reasons
    )
    if inputs.readiness_status is DecisionReadinessStatus.ALMOST_READY and not confidence_established:
        steps.append(
            DecisionStep(
                dependency=DependencyReference(
                    DependencySource.READINESS_PROGRESS, DecisionReadinessReasonKind.CONFIDENCE_ESTABLISHED.value
                ),
                progress_kind=RequiredProgressKind.READINESS,
                reachability=ReachabilityStatus.BLOCKED if no_data_source_present else ReachabilityStatus.REACHABLE,
            )
        )

    steps_tuple = tuple(steps)
    return DecisionPath(
        case_id=case_id,
        current_action=inputs.action,
        current_strength=inputs.strength,
        steps=steps_tuple,
        immediate_blocker=steps_tuple[0] if steps_tuple else None,
        next_achievable_improvement=next((s for s in steps_tuple if s.reachability is ReachabilityStatus.REACHABLE), None),
        final_reachable_state=_derive_final_reachable_state(steps_tuple),
        generated_at=generated_at,
    )


def summarize_decision_path(path: DecisionPath) -> DecisionPathSummary:
    return DecisionPathSummary(
        case_id=path.case_id,
        current_action=path.current_action,
        final_reachable_state=path.final_reachable_state,
        immediate_blocker=path.immediate_blocker,
        next_achievable_improvement=path.next_achievable_improvement,
        remaining_step_count=len(path.steps),
        generated_at=path.generated_at,
    )


def _pick_fewer(a_value: int, b_value: int, a_id: str, b_id: str) -> str | None:
    if a_value < b_value:
        return a_id
    if b_value < a_value:
        return b_id
    return None


def _pick_more(a_value: int, b_value: int, a_id: str, b_id: str) -> str | None:
    if a_value > b_value:
        return a_id
    if b_value > a_value:
        return b_id
    return None


def compare_decision_paths(a: DecisionPath, b: DecisionPath) -> DecisionPathComparison:
    """Deliverable 9 -- four independent factual comparisons, each
    `None` on a genuine tie. "Shorter path" counts only the steps that
    are not permanently `NOT_REACHABLE` (the ones a real path can
    actually walk); "fewer remaining blockers" counts every real step,
    including permanent ones -- two genuinely different questions,
    never collapsed into a single "better" verdict."""
    a_walkable = sum(1 for s in a.steps if s.reachability is not ReachabilityStatus.NOT_REACHABLE)
    b_walkable = sum(1 for s in b.steps if s.reachability is not ReachabilityStatus.NOT_REACHABLE)
    a_operational = sum(1 for s in a.steps if s.progress_kind is RequiredProgressKind.OPERATIONAL)
    b_operational = sum(1 for s in b.steps if s.progress_kind is RequiredProgressKind.OPERATIONAL)
    a_evidence = sum(1 for s in a.steps if s.progress_kind is RequiredProgressKind.EVIDENCE)
    b_evidence = sum(1 for s in b.steps if s.progress_kind is RequiredProgressKind.EVIDENCE)

    return DecisionPathComparison(
        a=a,
        b=b,
        shorter_path_case_id=_pick_fewer(a_walkable, b_walkable, a.case_id, b.case_id),
        fewer_remaining_blockers_case_id=_pick_fewer(len(a.steps), len(b.steps), a.case_id, b.case_id),
        more_operationally_dependent_case_id=_pick_more(a_operational, b_operational, a.case_id, b.case_id),
        more_evidence_dependent_case_id=_pick_more(a_evidence, b_evidence, a.case_id, b.case_id),
    )


def detect_decision_path_change(
    previous: DecisionPath | None, current: DecisionPath, *, detected_at: datetime
) -> DecisionPathChange | None:
    """"No event, no timestamp" -- `None` when this is the first-ever
    computation, or when neither the final reachable state nor the
    real step set actually moved."""
    if previous is None:
        return None
    previous_set = set(previous.steps)
    current_set = set(current.steps)
    if previous.final_reachable_state == current.final_reachable_state and previous_set == current_set:
        return None

    return DecisionPathChange(
        case_id=current.case_id,
        previous_final_reachable_state=previous.final_reachable_state,
        current_final_reachable_state=current.final_reachable_state,
        resolved_steps=tuple(s for s in previous.steps if s in previous_set - current_set),
        new_steps=tuple(s for s in current.steps if s in current_set - previous_set),
        detected_at=detected_at,
    )


_CLOSEST_TO_INVESTABLE_STATES = frozenset({FinalReachableState.ALREADY_REACHED, FinalReachableState.FULLY_REACHABLE})


def build_portfolio_decision_path_breakdown(
    items: tuple[tuple[str, DecisionPath], ...],
) -> PortfolioDecisionPathBreakdown:
    """Deliverable 7 -- ticker groupings only, in the caller's own
    existing order (Portfolio's own holdings order); never re-ranked,
    never turned into an allocation suggestion. "Closest to investable"
    is a fixed, disclosed threshold (a fully-reachable path with at
    most one remaining step), never a ranking."""
    closest = tuple(
        ticker
        for ticker, path in items
        if path.final_reachable_state in _CLOSEST_TO_INVESTABLE_STATES and len(path.steps) <= 1
    )
    operationally_blocked = tuple(
        ticker for ticker, path in items if any(s.progress_kind is RequiredProgressKind.OPERATIONAL for s in path.steps)
    )
    requiring_more_evidence = tuple(
        ticker
        for ticker, path in items
        if any(s.progress_kind in (RequiredProgressKind.EVIDENCE, RequiredProgressKind.COVERAGE) for s in path.steps)
    )
    requiring_dependency_resolution = tuple(
        ticker for ticker, path in items if any(s.progress_kind is RequiredProgressKind.DEPENDENCY for s in path.steps)
    )
    return PortfolioDecisionPathBreakdown(
        closest_to_investable=closest,
        operationally_blocked=operationally_blocked,
        requiring_more_evidence=requiring_more_evidence,
        requiring_dependency_resolution=requiring_dependency_resolution,
    )
