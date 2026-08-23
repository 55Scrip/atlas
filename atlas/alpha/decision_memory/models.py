"""Decision Memory domain model (Atlas Decision Layer Sprint 5).
Alpha-only -- no Core change.

**Every snapshot references already-real structured fields, never a
duplicated analysis.** A `DecisionSnapshot` carries only the compact,
comparable summary of what Sprints 1-4 already computed for a Case at
one moment -- never the full nested objects, never free text. See this
package's own `__init__.py` for the full audit.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.alpha.decision_path.models import FinalReachableState
from atlas.alpha.decision_readiness.models import DecisionReadinessStatus
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.opportunity_cost.models import AlternativeKind
from atlas.alpha.recommendation_conviction.models import ConvictionStrength, RecommendationStability

__all__ = [
    "DecisionSnapshot",
    "ChangeDirection",
    "DecisionMemoryChange",
    "DecisionTimelineEntry",
    "DecisionTimeline",
    "DecisionMemory",
    "DecisionMemoryComparison",
    "PortfolioDecisionMemoryBreakdown",
]


@dataclass(frozen=True)
class DecisionSnapshot:
    """One immutable, append-only record of a Case's own structured
    decision state at one moment. Never mutated after it is written --
    a later real change always produces a *new* snapshot, never an
    edit to this one (Deliverable 12's own "new snapshot appended,
    previous snapshot preserved")."""

    case_id: str
    action: DecisionAction
    readiness_status: DecisionReadinessStatus
    blocker_codes: tuple[str, ...]
    """Every current `DecisionBlockerKind` value, sorted -- a
    structured field, never free text (Deliverable 4's own
    instruction)."""
    conviction_strength: ConvictionStrength
    conviction_stability: RecommendationStability
    decision_path_step_count: int
    decision_path_final_state: FinalReachableState
    primary_alternative_kind: AlternativeKind | None
    alternative_count: int
    content_hash: str
    """Computed over every field above, never over `recorded_at` --
    the same "idempotent by content" discipline `atlas.alpha
    .investment_case_change`'s own `AnalyticalSnapshot.content_hash`
    already established, reused here rather than invented fresh."""
    recorded_at: datetime


class ChangeDirection(str, Enum):
    """One shared, reused ranking-direction vocabulary -- `atlas.alpha
    .recommendation_conviction`'s own strength rank and `atlas.alpha
    .decision_readiness`'s own `READINESS_PROXIMITY_RANK` are both
    already real, ordered scales; this package reads their existing
    order rather than inventing a category-specific verb for each."""

    STRONGER = "stronger"
    WEAKER = "weaker"
    UNCHANGED = "unchanged"


@dataclass(frozen=True)
class DecisionMemoryChange:
    """The structured transition between two consecutive
    `DecisionSnapshot`s -- every field a direct structured comparison,
    never free text. `is_baseline` is `True` only for a Case's
    first-ever snapshot (mirrors `atlas.analysis_engine
    .investment_case_change.compare_snapshots(None, snapshot)`'s own
    constant-baseline convention) -- every direction field is `None`
    for a baseline, an honest absence rather than a fabricated "no
    change.\""""

    case_id: str
    is_baseline: bool
    previous_action: DecisionAction | None
    current_action: DecisionAction
    recommendation_changed: bool
    conviction_direction: ChangeDirection | None
    readiness_direction: ChangeDirection | None
    decision_path_direction: ChangeDirection | None
    blockers_resolved: tuple[str, ...]
    blockers_added: tuple[str, ...]
    alternative_changed: bool
    detected_at: datetime


@dataclass(frozen=True)
class DecisionTimelineEntry:
    snapshot: DecisionSnapshot
    change: DecisionMemoryChange
    """The transition that produced `snapshot` -- always present
    (every snapshot, including the first, has a real `DecisionMemoryChange`;
    the first's is simply `is_baseline=True`)."""


@dataclass(frozen=True)
class DecisionTimeline:
    case_id: str
    entries: tuple[DecisionTimelineEntry, ...]
    """Every persisted snapshot for this Case, oldest first -- never
    re-sorted, never pruned, never rewritten."""


@dataclass(frozen=True)
class DecisionMemory:
    """Deliverable 6's own compact entry point -- current snapshot,
    previous snapshot, the latest real change, and the full history,
    all in one read."""

    case_id: str
    current_snapshot: DecisionSnapshot
    previous_snapshot: DecisionSnapshot | None
    latest_change: DecisionMemoryChange | None
    """`None` only when the current snapshot is this Case's first-ever
    (no real predecessor to describe a transition from)."""
    history: DecisionTimeline


@dataclass(frozen=True)
class DecisionMemoryComparison:
    """Deliverable 9 -- four independent factual comparisons, each
    `None` on a genuine tie. Never infers superiority: "changed more
    recently" and "stable longer" are opposite readings of the same
    real timestamp, neither framed as better."""

    a: DecisionMemory
    b: DecisionMemory
    more_recently_changed_case_id: str | None
    more_stable_case_id: str | None
    conviction_changed_case_id: str | None
    blockers_disappeared_case_id: str | None


@dataclass(frozen=True)
class PortfolioDecisionMemoryBreakdown:
    """Deliverable 7 -- ticker groupings only, always in Portfolio's
    own existing holdings order. Never a re-ranking."""

    recently_changed: tuple[str, ...]
    stable: tuple[str, ...]
    recently_strengthened: tuple[str, ...]
    recently_weakened: tuple[str, ...]
