"""Investment Decision Synthesis domain model (Atlas Decision Layer
Sprint 1, Deliverable 2). Alpha-only -- no Core change.

This is the final synthesis, not a fourth independent judgment: every
field here is either a direct re-expression of an already-existing
value (`DecisionAction` from `atlas.alpha.decision_support
.DecisionSupportLevel`) or a tagged pointer at one (`DecisionReason`
names a real `DecisionBlockerKind`/`DecisionReadinessReasonKind`/
`StanceReasonCode` value it was built from, never a new code of its
own). See this package's own `__init__.py` for the full audit this
model is built from.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

__all__ = [
    "DecisionAction",
    "DecisionReasonSource",
    "DecisionReason",
    "DecisionQualifierKind",
    "DecisionQualifier",
    "InvestmentDecision",
    "DecisionSummary",
    "DecisionComparison",
    "DecisionChange",
]


class DecisionAction(str, Enum):
    """Deliverable 3's own seven-member outcome vocabulary -- a direct,
    one-to-one re-expression of `atlas.alpha.decision_support
    .DecisionSupportLevel`, Atlas's own already-existing "what does
    current evidence support" signal (see `__init__.py`'s own audit for
    why that, and not Stance, is the synthesis engine's anchor)."""

    BUY = "buy"
    ADD = "add"
    HOLD = "hold"
    REDUCE = "reduce"
    EXIT = "exit"
    WAIT = "wait"
    NO_DECISION = "no_decision"


class DecisionReasonSource(str, Enum):
    """Which existing vocabulary a `DecisionReason.code` value belongs
    to -- so a caller can resolve/translate it correctly without this
    package inventing a fourth, unified reason-code enum of its own."""

    READINESS_BLOCKER = "readiness_blocker"
    READINESS_SUPPORT = "readiness_support"
    STANCE = "stance"


@dataclass(frozen=True)
class DecisionReason:
    """A tagged pointer at one real, already-computed reason -- never a
    new judgment. `code` is the `.value` of a real `DecisionBlockerKind`
    (`atlas.alpha.decision_readiness.models`), `DecisionReadinessReasonKind`,
    or `StanceReasonCode` (`atlas.alpha.stance.models`), disambiguated by
    `source`."""

    source: DecisionReasonSource
    code: str


class DecisionQualifierKind(str, Enum):
    """Deliverable 4's own closed vocabulary -- every member derived
    from an already-real Decision Readiness/Stance/thesis-staleness
    fact (see `engine.py`'s own docstring for exactly which)."""

    STRONG_DECISION = "strong_decision"
    CAREFUL_DECISION = "careful_decision"
    TEMPORARY_DECISION = "temporary_decision"
    OPERATIONALLY_DELAYED = "operationally_delayed"
    EVIDENCE_LIMITED = "evidence_limited"
    DECISION_BLOCKED = "decision_blocked"


@dataclass(frozen=True)
class DecisionQualifier:
    kind: DecisionQualifierKind


@dataclass(frozen=True)
class InvestmentDecision:
    """The full, per-Case result -- every applicable qualifier/reason/
    blocker, not just the primary ones (matches `DecisionReadiness`'s
    own "complete answer" discipline, Sprint 11)."""

    case_id: str
    action: DecisionAction
    qualifiers: tuple[DecisionQualifier, ...]
    supporting_reasons: tuple[DecisionReason, ...]
    blockers: tuple[DecisionReason, ...]
    change_trigger: DecisionReason | None
    """Deliverable 5's own "what would most likely change the
    decision" -- the same real fact as `blockers[0]` when one exists
    (resolving it is what would change the decision), `None`
    otherwise -- never a separately invented prediction.

    Reasoning Domain Closure: this remains a READINESS blocker, kept
    only for backward compatibility. It is no longer the authoritative
    "what would change the recommendation" -- that is
    `reasoning_payload["whatWouldChange"]`, produced by the
    recommendation gate from the same statuses that chose the
    direction. A readiness blocker describes Atlas's workflow; it was
    never an investment condition, and presenting it as one is what the
    Calibration Phase 9 benchmark measured."""
    generated_at: datetime

    #: The canonical analytical rationale, projected from
    #: `RecommendationReasoning` and never re-derived here. `None` means
    #: either no directional recommendation existed, or the row predates
    #: reasoning persistence -- see `LEGACY_RESULT_WITHOUT_REASONING`.
    reasoning_payload: dict | None = None


@dataclass(frozen=True)
class DecisionSummary:
    """Deliverable 6/7's own compact entry point -- action plus the one
    most important qualifier/reason/blocker, never the full lists."""

    case_id: str
    action: DecisionAction
    primary_qualifier: DecisionQualifierKind | None
    primary_supporting_reason: DecisionReason | None
    primary_blocker: DecisionReason | None
    change_trigger: DecisionReason | None
    generated_at: datetime


@dataclass(frozen=True)
class DecisionComparison:
    """Deliverable 9 -- two real sides, plus what differs/what's
    shared. Never a preferred side: no field here ever names a
    "winner.\""""

    a: InvestmentDecision
    b: InvestmentDecision
    differing_qualifier_kinds: tuple[DecisionQualifierKind, ...]
    shared_blocker_codes: tuple[str, ...]
    shared_supporting_reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class DecisionChange:
    """Deliverable 10/11 -- a real transition between two consecutive
    computations for the same Case, never a manufactured one (an
    unchanged decision produces no `DecisionChange` at all)."""

    case_id: str
    previous_action: DecisionAction
    current_action: DecisionAction
    previous_qualifier_kinds: tuple[DecisionQualifierKind, ...]
    current_qualifier_kinds: tuple[DecisionQualifierKind, ...]
    detected_at: datetime
