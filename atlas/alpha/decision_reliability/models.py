"""Decision Reliability domain model (Atlas Decision Layer Sprint 7).
Alpha-only -- no Core change.

Answers "how trustworthy is this decision, and why" -- a pure
reclassification and composition of three already-real, already-
computed judgments (`CoverageAssessment.overall_confidence`,
`EvidenceQualityReport.quality`, `DecisionReadiness.status`), never a
new score. See this package's own `__init__.py` for the full audit.

`ReliabilityReference` is deliberately `atlas.alpha.decision_explanation
.models.ExplanationReference`, reused verbatim rather than re-declared
-- the same four traceable kinds (`FINDING`/`OBSERVATION`/`REASON_CODE`
/`DECISION_SNAPSHOT`) already cover every fact Reliability can point
at; declaring a fifth, structurally identical shape here would be
exactly the "nothing duplicated" the brief forbids.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.alpha.decision_explanation.models import ChangeDirection, ExplanationReference

__all__ = [
    "ReliabilityLevel",
    "ReliabilitySource",
    "ReliabilityReference",
    "ReliabilityReason",
    "DecisionReliability",
    "DecisionReliabilitySummary",
    "ReliabilityComparison",
    "ReliabilityChange",
    "PortfolioReliabilityBreakdown",
]

#: `ReliabilityReference` is `ExplanationReference` under a name that
#: reads correctly in this package's own vocabulary -- the exact same
#: type, never a parallel redeclaration (see module docstring).
ReliabilityReference = ExplanationReference


class ReliabilityLevel(str, Enum):
    """Deliverable 4's own closed, five-member classification --
    derived by a fixed, documented priority cascade over three
    already-real inputs (`engine.py::classify_reliability`), never a
    score, never an average, never a probability."""

    HIGH = "high"
    """Confidence is `HIGH`, evidence is `FRESH`/`RECENT` (or has
    nothing timestamped to grade), and Decision Readiness is `READY`
    -- every real signal Atlas already has agrees this decision rests
    on a complete, current, unblocked picture."""

    MODERATE = "moderate"
    """A real signal is genuinely still developing -- confidence is
    `MODERATE`, evidence has aged (`OLD`/`STALE`), or readiness is
    still `WAITING`/`ALMOST_READY` -- never a content-level problem,
    only more time or more data needed."""

    LIMITED = "limited"
    """A real, content-level problem exists: confidence is `LIMITED`/
    `VERY_LIMITED`, evidence is `CONFLICTING`/`UNSUPPORTED`/
    `INCOMPLETE`/`SUPERSEDED`, or Decision Readiness is genuinely
    `BLOCKED` -- more waiting alone will not resolve this."""

    UNAVAILABLE = "unavailable"
    """Atlas's own operational systems have not produced a trustworthy
    read yet (`DecisionReadinessStatus.UNAVAILABLE` -- never
    monitored, the last run failed, or no data source could be
    reached) -- distinct from `LIMITED`: this is Atlas's own
    machinery, not the underlying evidence."""

    UNKNOWN = "unknown"
    """Atlas has no real company data to reason from at all -- the
    floor state, before any reliability question can even be asked
    (`DecisionReadinessStatus.UNKNOWN`)."""


class ReliabilitySource(str, Enum):
    """Deliverable 1's own audited reliability-source list -- which
    already-real service produced a given `ReliabilityReason`. Never a
    new vocabulary of its own: every code a reason carries is a real
    `ConfidenceReasonCode`/`EvidenceWarningCode`/`DecisionBlockerKind`/
    `DecisionReadinessReasonKind` value, disambiguated by this tag."""

    CONFIDENCE = "confidence"
    """A code from `atlas.alpha.coverage.models.ConfidenceReasonCode`
    -- Atlas's own understanding of the Case, from Coverage &
    Confidence (Atlas Intelligence Sprint 1)."""
    EVIDENCE_QUALITY = "evidence_quality"
    """A code from `atlas.alpha.evidence_quality.models
    .EvidenceWarningCode` -- freshness, dominance, and conflict facts
    about the investor's own recorded evidence (Atlas Intelligence
    Sprint 4)."""
    READINESS_BLOCKER = "readiness_blocker"
    """A code from `atlas.alpha.decision_readiness.models
    .DecisionBlockerKind` -- including Monitoring's own operational
    facts (`MONITORING_PENDING`/`MONITORING_FAILED`/
    `OPERATIONAL_FRESHNESS_OUTDATED`), already folded into Decision
    Readiness (Atlas Intelligence Sprint 11) rather than composed
    separately here -- see `__init__.py`'s own audit for why."""
    READINESS_SUPPORT = "readiness_support"
    """A code from `atlas.alpha.decision_readiness.models
    .DecisionReadinessReasonKind`."""


@dataclass(frozen=True)
class ReliabilityReason:
    source: ReliabilitySource
    reference: ReliabilityReference
    count: int | None = None
    total: int | None = None
    """Reused verbatim from the real, already-counted upstream fact
    this reason points at (`ConfidenceReason.count`/`.total` when
    `source` is `CONFIDENCE`; `DecisionBlocker.detail`/
    `DecisionReadinessReason.detail` as `count`, `total` always `None`,
    when `source` is a readiness reason) -- never invented here, and
    never dropped: a presentation layer that needs a real number to
    fill its own sentence (e.g. "3 of 7 dimensions...") must never be
    left with nothing to interpolate."""


@dataclass(frozen=True)
class DecisionReliability:
    """The full, per-Case result -- every applicable supporting/
    limiting reason, not just the one that decided `level` (matching
    `DecisionReadiness`'s own "complete answer" discipline)."""

    case_id: str
    level: ReliabilityLevel
    supporting_reasons: tuple[ReliabilityReason, ...]
    limiting_reasons: tuple[ReliabilityReason, ...]
    primary_limiting_reason: ReliabilityReason | None
    """The first entry of `limiting_reasons` -- the same "primary is
    the first, already-ordered entry, never a separately invented
    importance score" discipline every prior Decision Layer summary
    in this program already uses."""
    generated_at: datetime


@dataclass(frozen=True)
class DecisionReliabilitySummary:
    """Deliverable 9's own compact entry point -- level plus the one
    most important limiting reason, never the full lists."""

    case_id: str
    level: ReliabilityLevel
    primary_limiting_reason: ReliabilityReason | None
    generated_at: datetime


@dataclass(frozen=True)
class ReliabilityComparison:
    """Deliverable 10 -- which side is more reliable (by the same
    fixed level ranking `engine.py` already uses for classification,
    `None` on a genuine tie), shared/differing limitations, and shared
    strengths. Never a "better investment" verdict -- only a
    reliability-of-explanation reading."""

    a: DecisionReliability
    b: DecisionReliability
    more_reliable_case_id: str | None
    shared_limiting: tuple[ReliabilityReference, ...]
    differing_limiting_a: tuple[ReliabilityReference, ...]
    differing_limiting_b: tuple[ReliabilityReference, ...]
    shared_supporting: tuple[ReliabilityReference, ...]


@dataclass(frozen=True)
class ReliabilityChange:
    """Deliverable 11 -- a real transition between two consecutive
    computations for the same Case, never a manufactured one (an
    unchanged reliability produces no `ReliabilityChange` at all, the
    same "no event, no timestamp" discipline every other change-
    detector in this program already follows)."""

    case_id: str
    previous_level: ReliabilityLevel
    current_level: ReliabilityLevel
    direction: ChangeDirection | None
    """Reuses `atlas.alpha.decision_explanation.models.ChangeDirection`
    verbatim (itself reused from Decision Memory) -- never a new
    vocabulary. `None` only when `previous_level == current_level`."""
    new_limiting: tuple[ReliabilityReason, ...]
    resolved_limiting: tuple[ReliabilityReason, ...]
    detected_at: datetime


@dataclass(frozen=True)
class PortfolioReliabilityBreakdown:
    """Deliverable 8 -- ticker groupings only, always in Portfolio's
    own existing holdings order. Never a re-ranking, never an
    allocation suggestion."""

    most_reliable: tuple[str, ...]
    least_reliable: tuple[str, ...]
    recently_improved: tuple[str, ...]
    recently_weakened: tuple[str, ...]
