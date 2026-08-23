"""Decision Path & Required Progress domain model (Atlas Decision
Layer Sprint 3). Alpha-only -- no Core change.

**Every step references an already-real object, never a synthetic
milestone.** A `DecisionStep` is a tagged pointer at exactly one of two
already-real vocabularies: a present `DecisionBlockerKind` (Sprint 11)
or a still-missing `DecisionReadinessReasonKind` (also Sprint 11, the
one positive reason `ALMOST_READY` names as not yet reached). Nothing
in this package invents a new fact -- see this package's own
`__init__.py` for the full audit.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.recommendation_conviction.models import ConvictionStrength

__all__ = [
    "RequiredProgressKind",
    "ReachabilityStatus",
    "DependencySource",
    "DependencyReference",
    "DecisionStep",
    "FinalReachableState",
    "DecisionPath",
    "DecisionPathSummary",
    "DecisionPathComparison",
    "DecisionPathChange",
    "PortfolioDecisionPathBreakdown",
]


class RequiredProgressKind(str, Enum):
    """The six categories Deliverable 4 names -- every present
    `DecisionBlockerKind` (Sprint 11) already belongs to exactly one
    of these; `READINESS` is the one category with no `DecisionBlockerKind`
    of its own (see `DependencySource.READINESS_PROGRESS` below)."""

    OPERATIONAL = "operational"
    EVIDENCE = "evidence"
    COVERAGE = "coverage"
    READINESS = "readiness"
    DEPENDENCY = "dependency"
    DECISION = "decision"


class ReachabilityStatus(str, Enum):
    """Deliverable 5's own three-way classification. `REACHABLE` --
    a real, already-existing pathway in this codebase can satisfy this
    today (Monitoring can run, an Observation/Evidence can be recorded).
    `BLOCKED` -- the pathway is real, but is currently gated behind
    another, `NOT_REACHABLE` blocker on the *same* Case (e.g. nothing
    can progress while no data source is connected at all). `NOT_REACHABLE`
    -- this codebase has no pathway at all today, an explicit,
    documented, permanent architectural boundary (no external data
    connector exists; semantic/NLP business-quality parsing and
    scenario-valuation fabrication are both permanently refused)."""

    REACHABLE = "reachable"
    BLOCKED = "blocked"
    NOT_REACHABLE = "not_reachable"


class DependencySource(str, Enum):
    """The same "tagged pointer, never a new vocabulary" discipline
    every prior Decision Layer sprint already established."""

    READINESS_BLOCKER = "readiness_blocker"
    """A code from `atlas.alpha.decision_readiness.models.DecisionBlockerKind`
    -- a real, currently-present blocker."""
    READINESS_PROGRESS = "readiness_progress"
    """A code from `atlas.alpha.decision_readiness.models
    .DecisionReadinessReasonKind` -- a real, positive reason that is
    *not yet* present among the Case's own supporting reasons
    (`ALMOST_READY`'s own documented meaning: "the same real conclusion
    exists, but confidence is not yet established")."""


@dataclass(frozen=True)
class DependencyReference:
    source: DependencySource
    code: str


@dataclass(frozen=True)
class DecisionStep:
    dependency: DependencyReference
    progress_kind: RequiredProgressKind
    reachability: ReachabilityStatus


class FinalReachableState(str, Enum):
    """Deliverable 3's own "final reachable state" -- a structural
    classification of the *dependency set itself*, never a prediction
    of what Atlas's recommendation will eventually become or when."""

    ALREADY_REACHED = "already_reached"
    """No real blocker remains -- nothing is holding today's
    recommendation back."""
    FULLY_REACHABLE = "fully_reachable"
    """Every present blocker has a real, already-existing pathway to
    resolution -- nothing structurally prevents this Case from
    eventually reflecting its strongest possible recommendation, once
    real evidence arrives through the normal channels."""
    PARTIALLY_REACHABLE = "partially_reachable"
    """At least one real, present blocker is permanently NOT_REACHABLE
    today -- some progress remains possible, but a stronger
    recommendation may never be fully reachable while it persists."""
    NOT_REACHABLE = "not_reachable"
    """Every real, present blocker is currently NOT_REACHABLE or
    BLOCKED -- no real path exists today."""


@dataclass(frozen=True)
class DecisionPath:
    case_id: str
    current_action: DecisionAction
    current_strength: ConvictionStrength
    steps: tuple[DecisionStep, ...]
    """Every real required-progress item, in the same fixed,
    deterministic order `DecisionReadiness.blockers` already comes in
    -- never re-sorted by this package."""
    immediate_blocker: DecisionStep | None
    next_achievable_improvement: DecisionStep | None
    """The first step, in order, whose `reachability` is `REACHABLE`
    -- may differ from `immediate_blocker` when the very first step is
    itself `BLOCKED`/`NOT_REACHABLE`."""
    final_reachable_state: FinalReachableState
    generated_at: datetime


@dataclass(frozen=True)
class DecisionPathSummary:
    case_id: str
    current_action: DecisionAction
    final_reachable_state: FinalReachableState
    immediate_blocker: DecisionStep | None
    next_achievable_improvement: DecisionStep | None
    remaining_step_count: int
    generated_at: datetime


@dataclass(frozen=True)
class DecisionPathComparison:
    """Deliverable 9 -- factual comparisons only, never a "better
    investment" verdict. `None` on a genuine tie, the same
    honest-absence discipline every prior comparison in this program
    already established."""

    a: DecisionPath
    b: DecisionPath
    shorter_path_case_id: str | None
    fewer_remaining_blockers_case_id: str | None
    more_operationally_dependent_case_id: str | None
    more_evidence_dependent_case_id: str | None


@dataclass(frozen=True)
class DecisionPathChange:
    case_id: str
    previous_final_reachable_state: FinalReachableState
    current_final_reachable_state: FinalReachableState
    resolved_steps: tuple[DecisionStep, ...]
    new_steps: tuple[DecisionStep, ...]
    detected_at: datetime


@dataclass(frozen=True)
class PortfolioDecisionPathBreakdown:
    """Deliverable 7 -- ticker groupings only, always in Portfolio's
    own existing holdings order. Never a re-ranking, never an
    allocation suggestion."""

    closest_to_investable: tuple[str, ...]
    operationally_blocked: tuple[str, ...]
    requiring_more_evidence: tuple[str, ...]
    requiring_dependency_resolution: tuple[str, ...]
