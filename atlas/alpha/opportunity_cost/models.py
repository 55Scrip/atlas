"""Decision Alternatives & Opportunity Cost domain model (Atlas
Decision Layer Sprint 4). Alpha-only -- no Core change.

**Every alternative references an already-real object, never a
synthetic one.** A `DecisionAlternative` either points at another real,
already-known Case (`case_id`/`ticker` set) or is one of the three
always-real non-Case alternatives (`WAIT`/`NO_ACTION`/`KEEP_CASH`,
`case_id`/`ticker` both `None`) -- there is no fourth shape. See this
package's own `__init__.py` for the full audit.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.alpha.decision_path.models import DecisionPathComparison
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.recommendation_conviction.models import ConvictionComparison, ConvictionStrength

__all__ = [
    "AlternativeKind",
    "AlternativeReasonSource",
    "AlternativeReason",
    "DecisionAlternative",
    "AlternativeComparison",
    "DecisionTradeoff",
    "OpportunityCost",
    "DecisionAlternativeSummary",
    "PortfolioOpportunityCostBreakdown",
    "OpportunityCostChange",
]


class AlternativeKind(str, Enum):
    """Deliverable 3's own closed vocabulary -- the five real
    categories the brief itself names. Every instance is grounded in
    an already-real fact (another Case's own current action, or the
    current Case's own decision path/decision); none is a synthetic
    milestone."""

    INCREASE_EXISTING_HOLDING = "increase_existing_holding"
    """Another known Case, already a Portfolio holding, whose own
    Investment Decision is currently `BUY`/`ADD` -- real capital
    competition from inside the portfolio."""
    OPEN_NEW_POSITION = "open_new_position"
    """Another known Case, Watchlist-only, whose own Investment
    Decision is currently `BUY` -- real capital competition from
    outside the portfolio."""
    WAIT = "wait"
    NO_ACTION = "no_action"
    KEEP_CASH = "keep_cash"


class AlternativeReasonSource(str, Enum):
    """The same "tagged pointer, never a new vocabulary" discipline
    every prior Decision Layer sprint already established -- a strict
    superset of Sprint 1's own `DecisionReasonSource` (`READINESS_BLOCKER`/
    `READINESS_SUPPORT`/`STANCE`) and Sprint 3's own `DependencySource`
    (`READINESS_BLOCKER`/`READINESS_PROGRESS`), since an alternative's
    own reason is always literally one of those two sprints' own
    already-real reason objects, converted 1:1, never re-coded."""

    READINESS_BLOCKER = "readiness_blocker"
    READINESS_SUPPORT = "readiness_support"
    READINESS_PROGRESS = "readiness_progress"
    STANCE = "stance"


@dataclass(frozen=True)
class AlternativeReason:
    source: AlternativeReasonSource
    code: str


@dataclass(frozen=True)
class DecisionAlternative:
    kind: AlternativeKind
    case_id: str | None
    """The other real Case this alternative points to -- `None` for
    `WAIT`/`NO_ACTION`/`KEEP_CASH`, which never reference a second
    Case."""
    ticker: str | None
    action: DecisionAction | None
    """That other Case's own current Investment Decision -- `None` for
    the three non-Case alternatives."""
    strength: ConvictionStrength | None
    """That other Case's own current Recommendation Conviction -- read
    verbatim, never recomputed. `None` for the three non-Case
    alternatives."""
    reason: AlternativeReason


@dataclass(frozen=True)
class AlternativeComparison:
    """Deliverable 5 -- reuses Sprint 2's and Sprint 3's own
    `compare_convictions`/`compare_decision_paths` results verbatim,
    plus one small, honest addition (`more_dependency_blocked_case_id`,
    read directly from each side's own already-computed `DecisionPath
    .steps`, never a new comparison algorithm). Every field is `None`
    on a genuine tie; never a combined "winner.\""""

    conviction: ConvictionComparison
    path: DecisionPathComparison
    more_dependency_blocked_case_id: str | None


@dataclass(frozen=True)
class DecisionTradeoff:
    """One real alternative, plus the factual comparison against it --
    `None` only for the three non-Case alternatives, which have no
    second Case to compare against."""

    alternative: DecisionAlternative
    comparison: AlternativeComparison | None


@dataclass(frozen=True)
class OpportunityCost:
    case_id: str
    current_action: DecisionAction
    tradeoffs: tuple[DecisionTradeoff, ...]
    """Every real alternative, in a fixed, deterministic order
    (competing Cases first, in `known_cases`'s own order, then
    `WAIT`/`KEEP_CASH`/`NO_ACTION`) -- never re-ranked, never reduced
    to a single "best" choice."""
    generated_at: datetime


@dataclass(frozen=True)
class DecisionAlternativeSummary:
    case_id: str
    current_action: DecisionAction
    primary_alternative: DecisionAlternative | None
    alternative_count: int
    generated_at: datetime


@dataclass(frozen=True)
class PortfolioOpportunityCostBreakdown:
    """Deliverable 7 -- ticker groupings only, always in Portfolio's
    own existing holdings order. Never a re-ranking, never an
    allocation suggestion."""

    holdings_competing_for_capital: tuple[str, ...]
    watchlist_competing_with_holdings: tuple[str, ...]
    waiting_preferable: tuple[str, ...]
    no_action_appropriate: tuple[str, ...]


@dataclass(frozen=True)
class OpportunityCostChange:
    """Deliverable 10 -- identity across two snapshots is `(kind,
    case_id)`: the same real alternative (the same other Case, or the
    same non-Case category) persisting, appearing, or disappearing."""

    case_id: str
    new_alternatives: tuple[DecisionAlternative, ...]
    disappeared_alternatives: tuple[DecisionAlternative, ...]
    strengthened_alternatives: tuple[DecisionAlternative, ...]
    weakened_alternatives: tuple[DecisionAlternative, ...]
    primary_alternative_changed: bool
    detected_at: datetime
