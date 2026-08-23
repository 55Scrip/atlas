"""The Decision Memory engine itself -- pure, deterministic, no I/O.
Given the exact same inputs, every function here always returns the
exact same result.

**Snapshots are append-only by construction, not by convention.**
`build_snapshot` never reads or references any prior snapshot -- it
builds one immutable record from the current, live-computed state
Sprints 1-4 already produced. Whether that record is actually written
anywhere is entirely the repository's own decision (`atlas.alpha
.decision_memory.repository`'s own idempotent-by-`content_hash` `add`,
mirroring `atlas.alpha.investment_case_change`'s own established
discipline exactly); this module never mutates, never overwrites,
never re-derives history.

**`detect_decision_change` only ever compares two already-real,
already-persisted snapshots' own structured fields** -- never free
text, the same discipline every field on `DecisionSnapshot` already
enforces by being a closed enum, a sorted tuple of codes, or a count.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime

from atlas.alpha.decision_path.models import FinalReachableState
from atlas.alpha.decision_readiness.engine import READINESS_PROXIMITY_RANK
from atlas.alpha.decision_readiness.models import DecisionReadinessStatus
from atlas.alpha.decision_memory.models import (
    ChangeDirection,
    DecisionMemoryChange,
    DecisionMemory,
    DecisionMemoryComparison,
    DecisionSnapshot,
    DecisionTimeline,
    PortfolioDecisionMemoryBreakdown,
)
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.opportunity_cost.models import AlternativeKind
from atlas.alpha.recommendation_conviction.models import ConvictionStrength, RecommendationStability

__all__ = [
    "DecisionSnapshotInputs",
    "build_snapshot",
    "detect_decision_change",
    "build_decision_memory",
    "compare_decision_memories",
    "build_portfolio_decision_memory_breakdown",
]

_STRENGTH_RANK: dict[ConvictionStrength, int] = {
    ConvictionStrength.UNAVAILABLE: -1,
    ConvictionStrength.VERY_WEAK: 0,
    ConvictionStrength.WEAK: 1,
    ConvictionStrength.MODERATE: 2,
    ConvictionStrength.STRONG: 3,
    ConvictionStrength.VERY_STRONG: 4,
}
"""The same rank order `atlas.alpha.recommendation_conviction.engine`
already uses -- referencing the enum's own real ordering, not a second
scoring algorithm."""


@dataclass(frozen=True)
class DecisionSnapshotInputs:
    action: DecisionAction
    readiness_status: DecisionReadinessStatus
    blocker_codes: tuple[str, ...]
    conviction_strength: ConvictionStrength
    conviction_stability: RecommendationStability
    decision_path_step_count: int
    decision_path_final_state: FinalReachableState
    primary_alternative_kind: AlternativeKind | None
    alternative_count: int


def build_snapshot(case_id: str, inputs: DecisionSnapshotInputs, *, recorded_at: datetime) -> DecisionSnapshot:
    sorted_blockers = tuple(sorted(inputs.blocker_codes))
    hashed_content = {
        "action": inputs.action.value,
        "readinessStatus": inputs.readiness_status.value,
        "blockerCodes": list(sorted_blockers),
        "convictionStrength": inputs.conviction_strength.value,
        "convictionStability": inputs.conviction_stability.value,
        "decisionPathStepCount": inputs.decision_path_step_count,
        "decisionPathFinalState": inputs.decision_path_final_state.value,
        "primaryAlternativeKind": inputs.primary_alternative_kind.value if inputs.primary_alternative_kind is not None else None,
        "alternativeCount": inputs.alternative_count,
    }
    content_hash = hashlib.sha256(json.dumps(hashed_content, sort_keys=True).encode("utf-8")).hexdigest()
    return DecisionSnapshot(
        case_id=case_id,
        action=inputs.action,
        readiness_status=inputs.readiness_status,
        blocker_codes=sorted_blockers,
        conviction_strength=inputs.conviction_strength,
        conviction_stability=inputs.conviction_stability,
        decision_path_step_count=inputs.decision_path_step_count,
        decision_path_final_state=inputs.decision_path_final_state,
        primary_alternative_kind=inputs.primary_alternative_kind,
        alternative_count=inputs.alternative_count,
        content_hash=content_hash,
        recorded_at=recorded_at,
    )


def _direction(previous_rank: int, current_rank: int) -> ChangeDirection:
    """A shared "higher rank is stronger" convention. `READINESS
    _PROXIMITY_RANK`'s own real values run the opposite way (`READY`
    is `0`, the *lowest* number) -- callers passing that rank negate it
    first so this one helper's own convention stays consistent for
    every direction field, never a second, inverted comparator."""
    if current_rank > previous_rank:
        return ChangeDirection.STRONGER
    if current_rank < previous_rank:
        return ChangeDirection.WEAKER
    return ChangeDirection.UNCHANGED


_PATH_STEP_RANK_CEILING = 1_000_000
"""Fewer steps is "stronger" (closer to a fully-settled decision) --
ranked by the negative step count so the shared `_direction` helper's
own ">/<" comparison reads correctly without a second, inverted
helper."""


def detect_decision_change(
    previous: DecisionSnapshot | None, current: DecisionSnapshot, *, detected_at: datetime
) -> DecisionMemoryChange:
    """Always returns a real `DecisionMemoryChange` -- `is_baseline=True`
    for a Case's first-ever snapshot (mirrors `atlas.analysis_engine
    .investment_case_change.compare_snapshots(None, snapshot)`'s own
    constant-baseline convention), never `None`. This function is only
    ever called by the repository's own `add()` at the moment a new,
    genuinely-different snapshot is about to be persisted -- there is
    no "no change" case to represent here."""
    if previous is None:
        return DecisionMemoryChange(
            case_id=current.case_id,
            is_baseline=True,
            previous_action=None,
            current_action=current.action,
            recommendation_changed=False,
            conviction_direction=None,
            readiness_direction=None,
            decision_path_direction=None,
            blockers_resolved=(),
            blockers_added=(),
            alternative_changed=False,
            detected_at=detected_at,
        )

    previous_blockers = set(previous.blocker_codes)
    current_blockers = set(current.blocker_codes)

    return DecisionMemoryChange(
        case_id=current.case_id,
        is_baseline=False,
        previous_action=previous.action,
        current_action=current.action,
        recommendation_changed=previous.action != current.action,
        conviction_direction=_direction(_STRENGTH_RANK[previous.conviction_strength], _STRENGTH_RANK[current.conviction_strength]),
        readiness_direction=_direction(
            -READINESS_PROXIMITY_RANK[previous.readiness_status], -READINESS_PROXIMITY_RANK[current.readiness_status]
        ),
        decision_path_direction=_direction(
            _PATH_STEP_RANK_CEILING - previous.decision_path_step_count, _PATH_STEP_RANK_CEILING - current.decision_path_step_count
        ),
        blockers_resolved=tuple(sorted(previous_blockers - current_blockers)),
        blockers_added=tuple(sorted(current_blockers - previous_blockers)),
        alternative_changed=(
            previous.primary_alternative_kind != current.primary_alternative_kind
            or previous.alternative_count != current.alternative_count
        ),
        detected_at=detected_at,
    )


def build_decision_memory(
    case_id: str,
    current_snapshot: DecisionSnapshot,
    previous_snapshot: DecisionSnapshot | None,
    latest_change: DecisionMemoryChange | None,
    history: DecisionTimeline,
) -> DecisionMemory:
    return DecisionMemory(
        case_id=case_id,
        current_snapshot=current_snapshot,
        previous_snapshot=previous_snapshot,
        latest_change=latest_change,
        history=history,
    )


def _pick_newer(a_time: datetime, b_time: datetime, a_id: str, b_id: str) -> str | None:
    if a_time > b_time:
        return a_id
    if b_time > a_time:
        return b_id
    return None


def _pick_older(a_time: datetime, b_time: datetime, a_id: str, b_id: str) -> str | None:
    if a_time < b_time:
        return a_id
    if b_time < a_time:
        return b_id
    return None


def compare_decision_memories(a: DecisionMemory, b: DecisionMemory) -> DecisionMemoryComparison:
    """Deliverable 9 -- four independent factual comparisons, each
    `None` on a genuine tie. `more_recently_changed`/`more_stable` are
    opposite readings of the same real `current_snapshot.recorded_at`
    -- neither framed as better, both real."""
    more_recently_changed = _pick_newer(a.current_snapshot.recorded_at, b.current_snapshot.recorded_at, a.case_id, b.case_id)
    more_stable = _pick_older(a.current_snapshot.recorded_at, b.current_snapshot.recorded_at, a.case_id, b.case_id)

    a_conviction_changed = a.latest_change is not None and not a.latest_change.is_baseline and a.latest_change.conviction_direction is not ChangeDirection.UNCHANGED
    b_conviction_changed = b.latest_change is not None and not b.latest_change.is_baseline and b.latest_change.conviction_direction is not ChangeDirection.UNCHANGED
    conviction_changed_case_id = None
    if a_conviction_changed and not b_conviction_changed:
        conviction_changed_case_id = a.case_id
    elif b_conviction_changed and not a_conviction_changed:
        conviction_changed_case_id = b.case_id

    a_blockers_resolved = a.latest_change is not None and bool(a.latest_change.blockers_resolved)
    b_blockers_resolved = b.latest_change is not None and bool(b.latest_change.blockers_resolved)
    blockers_disappeared_case_id = None
    if a_blockers_resolved and not b_blockers_resolved:
        blockers_disappeared_case_id = a.case_id
    elif b_blockers_resolved and not a_blockers_resolved:
        blockers_disappeared_case_id = b.case_id

    return DecisionMemoryComparison(
        a=a,
        b=b,
        more_recently_changed_case_id=more_recently_changed,
        more_stable_case_id=more_stable,
        conviction_changed_case_id=conviction_changed_case_id,
        blockers_disappeared_case_id=blockers_disappeared_case_id,
    )


def build_portfolio_decision_memory_breakdown(
    items: tuple[tuple[str, DecisionMemory], ...],
) -> PortfolioDecisionMemoryBreakdown:
    """Deliverable 7 -- ticker groupings only, in the caller's own
    existing order; never re-ranked. "Recently changed" means the
    latest recorded transition is real (not a first-ever baseline);
    "stable" is every other holding, including one that has never
    changed at all -- an honest, disclosed reading of "recent" as "the
    most recent recorded transition," this codebase's own established
    meaning throughout the Decision Layer (no calendar-time window
    exists anywhere in this program)."""
    recently_changed = tuple(
        ticker for ticker, memory in items if memory.latest_change is not None and not memory.latest_change.is_baseline
    )
    stable = tuple(ticker for ticker, memory in items if ticker not in recently_changed)
    recently_strengthened = tuple(
        ticker
        for ticker, memory in items
        if memory.latest_change is not None
        and not memory.latest_change.is_baseline
        and memory.latest_change.conviction_direction is ChangeDirection.STRONGER
    )
    recently_weakened = tuple(
        ticker
        for ticker, memory in items
        if memory.latest_change is not None
        and not memory.latest_change.is_baseline
        and memory.latest_change.conviction_direction is ChangeDirection.WEAKER
    )
    return PortfolioDecisionMemoryBreakdown(
        recently_changed=recently_changed,
        stable=stable,
        recently_strengthened=recently_strengthened,
        recently_weakened=recently_weakened,
    )
