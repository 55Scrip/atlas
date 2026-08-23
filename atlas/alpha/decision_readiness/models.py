"""Decision Readiness domain model (Atlas Intelligence Sprint 11,
Deliverable 2). Alpha-only -- no Core change.

This is a product-level judgement about *whether Atlas has gathered
enough to responsibly reach a decision*, not a new investment view. It
is deliberately distinct from Stance (`atlas.alpha.stance`): Stance
answers "what does Atlas currently believe" (a directional read);
Decision Readiness answers "has Atlas earned the right to state any
view at all" (a judgement about the process, not the conclusion). Both
draw on Coverage/Confidence/Monitoring, but they are never the same
question -- a Case can have a clear, confident Stance (`MAINTAIN`) while
still being newly-monitored-and-blocked, and a Case can be `WAIT`/
`NO_RECOMMENDATION` in Stance while genuinely `READY` in the Decision
Readiness sense (Atlas has looked hard enough to honestly say "there is
nothing to act on yet" -- which is itself a reached decision, not an
unreached one). See this package's own `__init__.py` for the full
audit this model is built from.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

__all__ = [
    "DecisionReadinessStatus",
    "DecisionBlockerKind",
    "DecisionBlocker",
    "DecisionReadinessReasonKind",
    "DecisionReadinessReason",
    "DecisionReadiness",
    "DecisionReadinessSummary",
    "DecisionReadinessComparison",
    "DecisionReadinessChange",
]


class DecisionReadinessStatus(str, Enum):
    """Deliverable 3's own six-member outcome vocabulary. A strict
    priority order decides which one member applies (`engine.py`'s own
    `derive_decision_readiness`) -- never a score, never an average."""

    READY = "ready"
    """Substantial coverage, a real decision-support conclusion, no
    conflicts, no pending monitoring, no critical dependency, and
    established confidence -- Atlas has genuinely earned a decision."""

    ALMOST_READY = "almost_ready"
    """The same real conclusion exists, but confidence is not yet
    established -- close, not there yet."""

    WAITING = "waiting"
    """Nothing is wrong; there simply isn't enough yet, or Monitoring
    is still checking for more (Deliverable 4's "insufficient
    evidence"/"coverage incomplete"/"operational freshness outdated"
    without anything actively conflicting)."""

    BLOCKED = "blocked"
    """A genuine content-level problem exists -- conflicting evidence,
    a real Stance red flag, or an unresolved critical dependency --
    that more waiting alone will not resolve."""

    UNAVAILABLE = "unavailable"
    """Atlas's own operational systems have not produced a trustworthy
    read yet -- never monitored, the last run failed for this Case, or
    no data source could be reached at all. Distinct from `WAITING`:
    this is Atlas's own machinery, not the underlying evidence."""

    UNKNOWN = "unknown"
    """Atlas has no real company data to reason from at all -- the
    floor state, before any of the above questions can even be asked."""


class DecisionBlockerKind(str, Enum):
    """Deliverable 4's own closed vocabulary -- constructed only when
    the real, already-computed signal it names is actually present."""

    NEVER_EVALUATED = "never_evaluated"
    MONITORING_FAILED = "monitoring_failed"
    NO_DATA_SOURCE = "no_data_source"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    CRITICAL_DEPENDENCY_UNRESOLVED = "critical_dependency_unresolved"
    MONITORING_PENDING = "monitoring_pending"
    OPERATIONAL_FRESHNESS_OUTDATED = "operational_freshness_outdated"
    COVERAGE_INCOMPLETE = "coverage_incomplete"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNKNOWN_VALUATION = "unknown_valuation"
    MISSING_OBSERVATION = "missing_observation"
    MISSING_THESIS_EVIDENCE = "missing_thesis_evidence"
    AVOID_DECISION_SIGNAL = "avoid_decision_signal"


@dataclass(frozen=True)
class DecisionBlocker:
    kind: DecisionBlockerKind
    detail: int | None = None
    """A real, structural count backing the blocker (e.g. how many
    Findings lack support) -- never a fabricated severity score."""


class DecisionReadinessReasonKind(str, Enum):
    """The positive counterpart to `DecisionBlockerKind` -- why
    readiness is what it is when things are going well, closed the
    same way."""

    SUBSTANTIAL_COVERAGE_REACHED = "substantial_coverage_reached"
    CONFIDENCE_ESTABLISHED = "confidence_established"
    NO_CONFLICTS_FOUND = "no_conflicts_found"
    MONITORING_CURRENT = "monitoring_current"
    DECISION_SUPPORT_REACHED = "decision_support_reached"
    NO_CRITICAL_DEPENDENCIES = "no_critical_dependencies"


@dataclass(frozen=True)
class DecisionReadinessReason:
    kind: DecisionReadinessReasonKind
    detail: int | None = None


@dataclass(frozen=True)
class DecisionReadiness:
    """The full, per-Case result -- every applicable blocker and
    supporting reason, not just the one that decided `status`
    (matching `ConvictionReasonCode`'s own "complete answer" discipline)."""

    case_id: str
    status: DecisionReadinessStatus
    blockers: tuple[DecisionBlocker, ...]
    supporting_reasons: tuple[DecisionReadinessReason, ...]
    generated_at: datetime


@dataclass(frozen=True)
class DecisionReadinessSummary:
    """Deliverable 6/7's own compact entry point -- status plus the one
    most important blocker/reason, never the full lists. `primary_*` is
    the first entry of the corresponding `DecisionReadiness` tuple
    (both are already built in a fixed, deterministic order -- see
    `engine.py`), never a separately invented "most important" score."""

    case_id: str
    status: DecisionReadinessStatus
    primary_blocker: DecisionBlocker | None
    primary_supporting_reason: DecisionReadinessReason | None
    generated_at: datetime


@dataclass(frozen=True)
class DecisionReadinessComparison:
    """Deliverable 9 -- two real sides, plus which blockers differ.
    Never a "more ready" verdict: `closer_case_id` is `None` whenever
    the two statuses tie in priority, an honest absence rather than an
    arbitrary tiebreak."""

    a: DecisionReadiness
    b: DecisionReadiness
    closer_case_id: str | None
    differing_blocker_kinds: tuple[DecisionBlockerKind, ...]


@dataclass(frozen=True)
class DecisionReadinessChange:
    """Deliverable 10/11 -- a real transition between two consecutive
    computations for the same Case, never a manufactured one (an
    unchanged status produces no `DecisionReadinessChange` at all, the
    same "no event, no timestamp" discipline every other change-
    detector in this codebase already follows)."""

    case_id: str
    previous_status: DecisionReadinessStatus
    current_status: DecisionReadinessStatus
    new_blockers: tuple[DecisionBlockerKind, ...]
    resolved_blockers: tuple[DecisionBlockerKind, ...]
    detected_at: datetime
