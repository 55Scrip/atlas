"""Recommendation Conviction & Strength domain model (Atlas Decision
Layer Sprint 2). Alpha-only -- no Core change.

**Deliberately not named `ConvictionLevel`/`ConvictionAssessment`.**
Two other, real, already-shipped scales already use those names:
`atlas.analysis_engine.conviction.ConvictionLevel` (five levels, "how
strongly does available analysis support an investment conclusion,"
already read directly here as the primary input -- see `engine.py`) and
`atlas.analysis_engine.recommendation_conviction.RecommendationConvictionLevel`
(three levels, DE-004 §3, never wired into any pipeline). That second
module's own docstring establishes the governing discipline this
package follows too: "the two scales are independently computed, never
merged, never presented under the same label, and never interchangeable."
This is a *third*, genuinely distinct thing -- not a rescoring of
either, but the Decision Layer's own question: "how strongly does
Atlas stand behind the specific action it just recommended" (Sprint 1's
`InvestmentDecision.action`), which neither existing scale answers on
its own. See this package's own `__init__.py` for the full audit.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.alpha.investment_decision.models import DecisionAction

__all__ = [
    "ConvictionStrength",
    "RecommendationStability",
    "ConvictionReasonSource",
    "ConvictionReason",
    "RecommendationConviction",
    "ConvictionSummary",
    "ConvictionComparison",
    "ConvictionChange",
    "PortfolioConvictionBreakdown",
]


class ConvictionStrength(str, Enum):
    """How strongly Atlas stands behind the specific action it already
    recommended (Sprint 1's `DecisionAction`) -- never a probability,
    never a prediction, never a rescoring of `ConvictionLevel`."""

    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    VERY_WEAK = "very_weak"
    UNAVAILABLE = "unavailable"
    """No real recommendation exists yet (`DecisionAction.NO_DECISION`)
    -- there is nothing to hold a conviction about, the same "precedes
    the scale entirely" idea `atlas.analysis_engine.recommendation
    _conviction`'s own `DE-004 §4` already establishes for a withheld
    recommendation."""


class RecommendationStability(str, Enum):
    """A second, independent dimension from `ConvictionStrength` --
    how robust *today's* recommendation is, not how strong it is. A
    recommendation can be genuinely `STRONG` and still `FRAGILE` (a
    stale thesis or an unsupported dependency underneath it); this is
    never predictive, only a description of today's own footing."""

    STABLE = "stable"
    FRAGILE = "fragile"
    WAITING_FOR_EVIDENCE = "waiting_for_evidence"
    OPERATIONALLY_BLOCKED = "operationally_blocked"
    EVIDENCE_LIMITED = "evidence_limited"


class ConvictionReasonSource(str, Enum):
    """The same "tagged pointer, never a new vocabulary" discipline
    Sprint 1's own `DecisionReasonSource` established -- every code
    here is a real `.value` string from an already-real, already-
    computed upstream enum, disambiguated by source."""

    READINESS_BLOCKER = "readiness_blocker"
    READINESS_SUPPORT = "readiness_support"
    ANALYSIS_CONVICTION = "analysis_conviction"
    """A code from `atlas.analysis_engine.conviction.ConvictionReasonCode`
    -- the primary, already-computed "how strong is the analysis"
    signal this package reads, never recomputes."""
    EVIDENCE_GRAPH = "evidence_graph"
    """A code from `atlas.alpha.evidence_graph.models.WeaknessKind` --
    a real structural fact about the Case's own dependency graph."""


@dataclass(frozen=True)
class ConvictionReason:
    source: ConvictionReasonSource
    code: str


@dataclass(frozen=True)
class RecommendationConviction:
    case_id: str
    action: DecisionAction
    strength: ConvictionStrength
    stability: RecommendationStability
    supporting_reasons: tuple[ConvictionReason, ...]
    limiting_reasons: tuple[ConvictionReason, ...]
    strengthening_trigger: ConvictionReason | None
    """The one real fact that would most likely strengthen conviction if
    resolved -- always the same as `limiting_reasons[0]` when one
    exists, the identical "resolving it IS what would change this,
    not a prediction" discipline Sprint 1's own `change_trigger` uses."""
    generated_at: datetime


@dataclass(frozen=True)
class ConvictionSummary:
    case_id: str
    action: DecisionAction
    strength: ConvictionStrength
    stability: RecommendationStability
    primary_supporting_reason: ConvictionReason | None
    primary_limiting_reason: ConvictionReason | None
    strengthening_trigger: ConvictionReason | None
    generated_at: datetime


@dataclass(frozen=True)
class ConvictionComparison:
    """Deliverable 9 -- four independent factual comparisons, never an
    overall "winner." Each field is `None` on a genuine tie, the same
    honest-absence discipline `DecisionReadinessComparison.closer_case_id`
    already established."""

    a: RecommendationConviction
    b: RecommendationConviction
    stronger_case_id: str | None
    more_evidence_limited_case_id: str | None
    more_operationally_blocked_case_id: str | None
    more_stable_case_id: str | None


@dataclass(frozen=True)
class ConvictionChange:
    case_id: str
    previous_strength: ConvictionStrength
    current_strength: ConvictionStrength
    previous_stability: RecommendationStability
    current_stability: RecommendationStability
    new_limiting_reasons: tuple[ConvictionReason, ...]
    resolved_limiting_reasons: tuple[ConvictionReason, ...]
    detected_at: datetime


@dataclass(frozen=True)
class PortfolioConvictionBreakdown:
    """Deliverable 7 -- ticker groupings only, always in Portfolio's
    own existing holdings order. Never a re-ranking, never an
    allocation suggestion."""

    highest_conviction: tuple[str, ...]
    lowest_conviction: tuple[str, ...]
    evidence_limited: tuple[str, ...]
    operationally_blocked: tuple[str, ...]
