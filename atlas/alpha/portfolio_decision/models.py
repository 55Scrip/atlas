"""Portfolio Decision Synthesis domain model (Atlas Decision Layer
Sprint 8). Alpha-only -- no Core change.

Answers "what does this decision actually mean for my portfolio" -- a
pure composition of five already-real, already-computed judgments
(`PortfolioFitAssessment` [ALLOCATION dimension], the Portfolio
Domain's own `Concentration`, `PortfolioIntelligenceReport.key_findings`,
`OpportunityCost.tradeoffs`, `DecisionReliability.level`), never a new
portfolio-optimization computation. See this package's own `__init__.py`
for the full audit.

`PortfolioDecisionReference` is deliberately `atlas.alpha
.decision_explanation.models.ExplanationReference`, reused verbatim
rather than re-declared -- the same "one traceable-reference shape,
reused across every Decision Layer sprint" discipline Sprint 7 already
established for its own `ReliabilityReference`.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.alpha.decision_explanation.models import ExplanationReference
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.opportunity_cost.models import DecisionAlternative
from atlas.domains.portfolio.models import ConcentrationLevel

__all__ = [
    "PortfolioDecisionCategory",
    "PortfolioDecisionReasonSource",
    "PortfolioDecisionReference",
    "PortfolioDecisionReason",
    "PortfolioDecisionImpact",
    "CapitalCompetition",
    "PortfolioDecision",
    "PortfolioDecisionSummary",
    "PortfolioDecisionComparison",
    "PortfolioDecisionChange",
    "PortfolioSynthesisBreakdown",
]

#: `PortfolioDecisionReference` is `ExplanationReference` under a name
#: that reads correctly in this package's own vocabulary -- the exact
#: same type, never a parallel redeclaration (see module docstring).
PortfolioDecisionReference = ExplanationReference


class PortfolioDecisionCategory(str, Enum):
    """Deliverable 6's own closed, six-member classification -- derived
    by a fixed, documented priority cascade over already-real facts
    (`engine.py::classify_portfolio_decision`), never a score, never a
    probability, never a target-allocation computation."""

    SUPPORTS_PORTFOLIO = "supports_portfolio"
    """This decision reduces a real, already-flagged concentration
    concern (a capital-decreasing action on an already-overweight
    holding), or names no real portfolio tension at all."""

    NEUTRAL = "neutral"
    """No capital-allocating action is being recommended (`HOLD`/
    `WAIT`/`NO_DECISION`), or a capital-allocating action exists with
    no real portfolio tension found."""

    REQUIRES_REVIEW = "requires_review"
    """A capital-increasing action exists alongside a real, already-
    computed competing alternative (`atlas.alpha.opportunity_cost`'s
    own `INCREASE_EXISTING_HOLDING`/`OPEN_NEW_POSITION` tradeoffs) --
    worth a look, not yet a hard conflict."""

    CONFLICTS_WITH_PORTFOLIO = "conflicts_with_portfolio"
    """A capital-increasing action exists on a holding Portfolio Fit's
    own ALLOCATION dimension already rates `WEAK`/`POOR`, or the
    portfolio is already at `HIGH` concentration on this same ticker --
    a real, already-flagged tension, not an invented one."""

    OPERATIONALLY_LIMITED = "operationally_limited"
    """Atlas's own operational systems have not produced a trustworthy
    reliability read yet (`ReliabilityLevel.UNAVAILABLE`) -- distinct
    from a portfolio-level conflict."""

    UNKNOWN = "unknown"
    """Atlas has no real company data to reason from at all
    (`ReliabilityLevel.UNKNOWN`) -- the floor state, before any
    portfolio question can even be asked."""


class PortfolioDecisionReasonSource(str, Enum):
    """Deliverable 1's own audited portfolio-decision-source list --
    which already-real service produced a given `PortfolioDecisionReason`.
    Never a new vocabulary of its own: every code a reason carries is a
    real `FitRating`/`KeyFindingKind`/`AlternativeKind`/`ReliabilityLevel`
    value, disambiguated by this tag."""

    PORTFOLIO_FIT = "portfolio_fit"
    """A code from `atlas.alpha.portfolio_fit.models.FitRating` -- this
    holding's own ALLOCATION dimension rating."""
    PORTFOLIO_INTELLIGENCE = "portfolio_intelligence"
    """A code from `atlas.alpha.portfolio_intelligence.models
    .KeyFindingKind` -- a real, portfolio-wide concentration or
    unallocated-capital finding."""
    OPPORTUNITY_COST = "opportunity_cost"
    """A code from `atlas.alpha.opportunity_cost.models.AlternativeKind`
    -- a real capital-competing alternative."""
    DECISION_RELIABILITY = "decision_reliability"
    """A code from `atlas.alpha.decision_reliability.models
    .ReliabilityLevel` -- how trustworthy the underlying decision
    currently is."""


@dataclass(frozen=True)
class PortfolioDecisionReason:
    source: PortfolioDecisionReasonSource
    reference: PortfolioDecisionReference


@dataclass(frozen=True)
class PortfolioDecisionImpact:
    """Deliverable 5 -- Portfolio Context: how the current portfolio
    already bears on this decision, every field a direct read of an
    already-real fact. `already_diversified`/`duplicated_exposure`
    (both named as brief examples) are deliberately absent -- audited
    and found to have no real, already-computed data source in this
    codebase (see `__init__.py`'s own audit); never fabricated here."""

    is_existing_holding: bool
    current_weight_percent: float | None
    """The holding's real weight -- `None` for a Watchlist-only Case,
    the same honest-absence discipline `PortfolioFitAssessment
    .current_weight_percent` already established."""
    is_largest_position: bool
    """Whether this ticker is the portfolio's own real
    `PortfolioSummary.largest_holding` -- `atlas.alpha.portfolio
    .projection.derive_portfolio_view`'s own already-computed fact,
    never re-derived."""
    allocation_rating: str | None
    """This holding's own `FitDimensionKind.ALLOCATION` rating
    (`FitRating` `.value`) from `PortfolioFitAssessment.dimensions` --
    `None` only when no Fit assessment exists for this Case at all."""
    portfolio_concentration_level: ConcentrationLevel
    """The portfolio's own overall `Concentration.level` -- real,
    already-computed, portfolio-wide (not holding-specific)."""


@dataclass(frozen=True)
class CapitalCompetition:
    """Deliverable 4 -- reuses `atlas.alpha.opportunity_cost
    .OpportunityCost.tradeoffs` verbatim, reclassified into "real
    capital competitors" (another Case whose own Investment Decision
    also wants capital -- `INCREASE_EXISTING_HOLDING`/
    `OPEN_NEW_POSITION`) versus "non-competing alternatives"
    (`WAIT`/`KEEP_CASH`/`NO_ACTION`, which draw on no other Case's own
    capital claim). Computes nothing new -- a pure reclassification of
    Sprint 4's own already-real alternative list."""

    case_id: str
    competing_alternatives: tuple[DecisionAlternative, ...]
    non_competing_alternatives: tuple[DecisionAlternative, ...]


@dataclass(frozen=True)
class PortfolioDecision:
    """The full, per-Case result -- every applicable supporting/
    limiting reason, not just the one that decided `category`
    (matching `DecisionReliability`'s own "complete answer"
    discipline)."""

    case_id: str
    action: DecisionAction
    category: PortfolioDecisionCategory
    impact: PortfolioDecisionImpact
    capital_competition: CapitalCompetition
    supporting_reasons: tuple[PortfolioDecisionReason, ...]
    limiting_reasons: tuple[PortfolioDecisionReason, ...]
    primary_limiting_reason: PortfolioDecisionReason | None
    generated_at: datetime


@dataclass(frozen=True)
class PortfolioDecisionSummary:
    """Deliverable 9's own compact entry point -- category plus the
    one most important limiting reason, never the full lists."""

    case_id: str
    action: DecisionAction
    category: PortfolioDecisionCategory
    primary_limiting_reason: PortfolioDecisionReason | None
    generated_at: datetime


@dataclass(frozen=True)
class PortfolioDecisionComparison:
    """Deliverable 10 -- which side's own decision currently fits the
    portfolio better (by the same fixed category rank `engine.py`
    already uses, `None` on a genuine tie), shared strengths/
    weaknesses, and shared capital competitors. Never declares an
    overall winner: `better_portfolio_fit_case_id` speaks only to
    portfolio fit, never to "the better investment.\""""

    a: PortfolioDecision
    b: PortfolioDecision
    better_portfolio_fit_case_id: str | None
    shared_strengths: tuple[PortfolioDecisionReference, ...]
    shared_weaknesses: tuple[PortfolioDecisionReference, ...]
    shared_competitor_case_ids: tuple[str, ...]
    """Real Case ids appearing in both sides' own `capital_competition
    .competing_alternatives` -- a third Case both decisions are
    currently competing against for the same capital."""


@dataclass(frozen=True)
class PortfolioDecisionChange:
    """Deliverable 11 -- a real transition between two consecutive
    computations for the same Case, never a manufactured one (an
    unchanged portfolio decision produces no `PortfolioDecisionChange`
    at all, the same "no event, no timestamp" discipline every other
    change-detector in this program already follows)."""

    case_id: str
    previous_category: PortfolioDecisionCategory
    current_category: PortfolioDecisionCategory
    competition_changed: bool
    """Whether the real set of competing-alternative Case ids differs
    from the previous computation -- a real, structural set comparison,
    never a judgment about which competitor matters more."""
    new_limiting: tuple[PortfolioDecisionReason, ...]
    resolved_limiting: tuple[PortfolioDecisionReason, ...]
    detected_at: datetime


@dataclass(frozen=True)
class PortfolioSynthesisBreakdown:
    """Deliverable 8 -- ticker groupings only, always in Portfolio's
    own existing holdings order. Never a re-ranking, never an
    allocation suggestion, never a re-ordering of holdings themselves."""

    supports_portfolio: tuple[str, ...]
    highest_capital_competition: tuple[str, ...]
    conflicts_with_portfolio: tuple[str, ...]
    neutral: tuple[str, ...]
