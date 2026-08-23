"""Decision Explanation & Traceability domain model (Atlas Decision
Layer Sprint 6). Alpha-only -- no Core change.

**Deliberately not named `Explanation`.** `atlas.alpha.explainability
.models.Explanation` already exists (Atlas Intelligence Sprint 3) and
answers a different question: "why does Atlas currently believe X,"
built entirely from `Stance`/`CoverageAssessment` -- it predates the
Decision Layer program (Sprints 1-5 of this program) and has no
knowledge of `InvestmentDecision`/`RecommendationConviction`/
`DecisionPath`/`DecisionMemory` at all. This package answers a later,
narrower question: "why is Atlas recommending this specific *action*,"
built from those five newer objects. Both are real, both stay, neither
is redesigned -- see this package's own `__init__.py` for the full
audit. Every model class here uses `Explanation`-prefixed or
`Decision`-prefixed names distinct from that package's own two classes
(`Explanation`, `ComparisonEvidence`) to keep the two permanently
unambiguous.

**Every field is a tagged pointer at an already-real object, never a
new judgment.** `ExplanationReference` names one of the five
traceable object kinds Deliverable 4 asks for (`Finding`,
`Observation`, a Decision Readiness blocker/reason code, a Decision
Path dependency code, a Decision Memory snapshot) by that object's own
real, already-existing identifier -- never an anonymous string, never
"because AI thinks so."
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.alpha.decision_memory.models import ChangeDirection
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.recommendation_conviction.models import ConvictionStrength

__all__ = [
    "ExplanationReferenceKind",
    "ExplanationReference",
    "ExplanationLayer",
    "SupportingFinding",
    "BlockingFinding",
    "ExplanationSectionKind",
    "ExplanationSection",
    "ExplanationChain",
    "DecisionExplanation",
    "DecisionExplanationSummary",
    "DecisionExplanationComparison",
    "DecisionExplanationChange",
    "PortfolioDecisionExplanationBreakdown",
]


class ExplanationReferenceKind(str, Enum):
    """The four traceable object kinds Deliverable 4 names, classified
    by what real thing `id` identifies -- never by which upstream
    layer produced it (`ExplanationLayer`/`named_by` already carries
    that). `FINDING`/`OBSERVATION` are real Evidence Graph node ids
    (`GraphNode.id`, itself a real `Finding.id`/`Observation.id`).
    `REASON_CODE` is a real, closed-vocabulary code string from
    Decision Readiness/Recommendation Conviction/Decision Path/Stance
    (a `DecisionBlockerKind`/`DecisionReadinessReasonKind`/
    `StanceReasonCode`/`DependencyReference.code`/`WeaknessKind`
    value) that does not resolve to one specific object instance.
    `DECISION_SNAPSHOT` is a real `DecisionSnapshot.content_hash`.
    Nothing here is invented."""

    FINDING = "finding"
    OBSERVATION = "observation"
    REASON_CODE = "reason_code"
    DECISION_SNAPSHOT = "decision_snapshot"


@dataclass(frozen=True)
class ExplanationReference:
    """A tagged pointer at exactly one real object -- resolvable back
    to its source by any caller holding the same Case's own Evidence
    Graph / Decision Readiness / Decision Path / Decision Memory
    result. Never anonymous: `id` is always that object's own real,
    already-existing identifier, `kind` says exactly which of the five
    traceable vocabularies it belongs to."""

    kind: ExplanationReferenceKind
    id: str


class ExplanationLayer(str, Enum):
    """Deliverable 1's own audited explanation-source list -- which
    already-real Decision Layer service actually surfaced a given
    `SupportingFinding`/`BlockingFinding`. A single real fact (e.g. a
    `DecisionBlockerKind` code) is very often named by more than one
    layer at once (Investment Decision's own blockers already include
    every Decision Readiness blocker verbatim) -- `named_by` below
    carries every layer that named it, so the same fact is counted
    once, never once per layer."""

    INVESTMENT_DECISION = "investment_decision"
    RECOMMENDATION_CONVICTION = "recommendation_conviction"
    DECISION_READINESS = "decision_readiness"
    DECISION_PATH = "decision_path"
    EVIDENCE_GRAPH = "evidence_graph"


@dataclass(frozen=True)
class SupportingFinding:
    reference: ExplanationReference
    named_by: tuple[ExplanationLayer, ...]


@dataclass(frozen=True)
class BlockingFinding:
    reference: ExplanationReference
    named_by: tuple[ExplanationLayer, ...]
    is_change_trigger: bool
    """Whether resolving this specific blocker is the one real fact
    that would most likely change this decision -- the same already-
    computed `InvestmentDecision.change_trigger`/`RecommendationConviction
    .strengthening_trigger` fact, re-exposed here, never recomputed."""


class ExplanationSectionKind(str, Enum):
    """Deliverable 5's own fixed ordering categories -- Supporting,
    Blocking, Dependency, Historical, always in this order, never
    randomized, never reordered by content."""

    SUPPORTING = "supporting"
    BLOCKING = "blocking"
    DEPENDENCY = "dependency"
    HISTORICAL = "historical"


@dataclass(frozen=True)
class ExplanationSection:
    """One entry per section kind, always present in `ExplanationChain
    .order` even when `item_count` is `0` -- an honest "this section
    has nothing to say" is itself real information, never omitted."""

    kind: ExplanationSectionKind
    item_count: int


@dataclass(frozen=True)
class ExplanationChain:
    """Deliverable 5's own deterministically ordered explanation --
    `order` states which of the four sections is present, in the
    fixed sequence; the four typed tuples below carry each section's
    own real content."""

    case_id: str
    order: tuple[ExplanationSection, ...]
    supporting: tuple[SupportingFinding, ...]
    blocking: tuple[BlockingFinding, ...]
    dependency_steps: tuple[ExplanationReference, ...]
    """Every remaining `DecisionPath` step, in that package's own
    already-fixed order -- never re-sorted here."""
    historical_reference: ExplanationReference | None
    """The Case's own most recent real `DecisionMemory` snapshot, when
    one exists beyond the baseline -- `None` when nothing has changed
    since the first recorded decision."""


@dataclass(frozen=True)
class DecisionExplanation:
    """The full, per-Case result -- one coherent explanation, built
    the same way regardless of wording (Deliverable 3): a pure,
    deterministic function of five already-computed upstream results."""

    case_id: str
    action: DecisionAction
    conviction_strength: ConvictionStrength
    chain: ExplanationChain
    primary_supporting: SupportingFinding | None
    primary_blocking: BlockingFinding | None
    generated_at: datetime


@dataclass(frozen=True)
class DecisionExplanationSummary:
    """Deliverable 8's own compact entry point -- action plus the one
    most important supporting/blocking fact, never the full chain."""

    case_id: str
    action: DecisionAction
    primary_supporting: SupportingFinding | None
    primary_blocking: BlockingFinding | None
    generated_at: datetime


@dataclass(frozen=True)
class DecisionExplanationComparison:
    """Deliverable 9 -- shared supporting findings, each side's own
    differing blockers, and shared dependencies. Never a "better
    explained" verdict: no field here ever names a winner. Historical
    differences are deliberately not duplicated here -- `atlas.alpha
    .decision_memory.service.DecisionMemoryService.compare` already
    answers "whose decision changed more recently"/"whose has been
    stable longer" and is reused verbatim by Compare Integration."""

    a: DecisionExplanation
    b: DecisionExplanation
    shared_supporting: tuple[ExplanationReference, ...]
    differing_blocking_a: tuple[ExplanationReference, ...]
    differing_blocking_b: tuple[ExplanationReference, ...]
    shared_dependencies: tuple[ExplanationReference, ...]


@dataclass(frozen=True)
class DecisionExplanationChange:
    """Deliverable 10/11 -- a real transition between two consecutive
    computations for the same Case, never a manufactured one (an
    unchanged explanation produces no `DecisionExplanationChange` at
    all, the same "no event, no timestamp" discipline every other
    change-detector in this program already follows)."""

    case_id: str
    new_supporting: tuple[SupportingFinding, ...]
    resolved_blocking: tuple[BlockingFinding, ...]
    new_blocking: tuple[BlockingFinding, ...]
    evidence_expanded: bool
    """Whether the current chain names strictly more supporting
    findings than the previous one -- a real, structural count
    comparison, never a judgment about evidence quality."""
    conviction_direction: ChangeDirection | None
    """Reuses `atlas.alpha.decision_memory.models.ChangeDirection`
    verbatim (never a new vocabulary). `None` only when
    `previous.conviction_strength == current.conviction_strength`."""
    detected_at: datetime


@dataclass(frozen=True)
class PortfolioDecisionExplanationBreakdown:
    """Deliverable 7 -- ticker groupings only, always in Portfolio's
    own existing holdings order. Never a re-ranking, never an
    allocation suggestion."""

    recently_changed: tuple[str, ...]
    new_supporting_findings: tuple[str, ...]
    resolved_blockers: tuple[str, ...]
    recently_strengthened: tuple[str, ...]
