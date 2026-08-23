"""Portfolio Decision Synthesis engine (Atlas Decision Layer Sprint 8).
Pure, deterministic functions only -- no I/O, matching every sibling
Decision Layer engine in this program.

**Computes nothing new.** Every function below reclassifies and
composes already-real, already-computed facts -- `PortfolioFitAssessment`
.dimensions[ALLOCATION]` (Atlas Alpha Portfolio Fit), `PortfolioSummary
.concentration`/`.largest_holding` (`atlas.alpha.portfolio.projection
.derive_portfolio_view`), `PortfolioIntelligenceReport.key_findings`
(Atlas Intelligence Sprint 16), and `OpportunityCost.tradeoffs` (Atlas
Decision Layer Sprint 4) -- into one closed `PortfolioDecisionCategory`.
See this package's own `__init__.py` for the full audit these
functions are built from.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.decision_explanation.models import ExplanationReferenceKind
from atlas.alpha.decision_reliability.models import ReliabilityLevel
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.opportunity_cost.models import AlternativeKind, DecisionAlternative
from atlas.alpha.portfolio_fit.models import FitRating
from atlas.alpha.portfolio_intelligence.models import KeyFindingKind
from atlas.domains.portfolio.models import ConcentrationLevel

from .models import (
    CapitalCompetition,
    PortfolioDecision,
    PortfolioDecisionCategory,
    PortfolioDecisionChange,
    PortfolioDecisionComparison,
    PortfolioDecisionImpact,
    PortfolioDecisionReason,
    PortfolioDecisionReasonSource,
    PortfolioDecisionReference,
    PortfolioDecisionSummary,
    PortfolioSynthesisBreakdown,
)

__all__ = [
    "classify_portfolio_decision",
    "build_capital_competition",
    "build_portfolio_decision",
    "summarize_portfolio_decision",
    "compare_portfolio_decisions",
    "detect_portfolio_decision_change",
    "build_portfolio_synthesis_breakdown",
]

#: Deliverable 4 -- the same two-bucket split `atlas.alpha
#: .opportunity_cost.service.OpportunityCostService`'s own
#: `_COMPETING_ACTIONS` already establishes for which actions draw on
#: capital versus which free it. Declared here too (not imported)
#: since this package reasons about the *current* Case's own action,
#: while `opportunity_cost`'s constant reasons about *other* Cases'.
_CAPITAL_INCREASING_ACTIONS = frozenset({DecisionAction.BUY, DecisionAction.ADD})
_CAPITAL_DECREASING_ACTIONS = frozenset({DecisionAction.REDUCE, DecisionAction.EXIT})

#: Deliverable 6 -- a holding whose own `FitDimensionKind.ALLOCATION`
#: rating is `WEAK`/`POOR` is already, honestly overweight per
#: `atlas.alpha.portfolio_fit.engine`'s own already-computed threshold
#: check -- never re-derived here.
_OVERWEIGHT_FIT_RATINGS = frozenset({FitRating.WEAK, FitRating.POOR})
_SUPPORTING_FIT_RATINGS = frozenset({FitRating.EXCELLENT, FitRating.GOOD, FitRating.NEUTRAL})

#: Deliverable 6 -- worst-to-best, used for `PortfolioDecisionComparison`'s
#: own "better portfolio fit" reading. Declared once, locally, the same
#: "each package owns its own rank table" discipline Sprint 5/6/7
#: already established.
_CATEGORY_RANK: dict[PortfolioDecisionCategory, int] = {
    PortfolioDecisionCategory.UNKNOWN: 0,
    PortfolioDecisionCategory.OPERATIONALLY_LIMITED: 1,
    PortfolioDecisionCategory.CONFLICTS_WITH_PORTFOLIO: 2,
    PortfolioDecisionCategory.REQUIRES_REVIEW: 3,
    PortfolioDecisionCategory.NEUTRAL: 4,
    PortfolioDecisionCategory.SUPPORTS_PORTFOLIO: 5,
}


def _reason_ref(code: str) -> PortfolioDecisionReference:
    return PortfolioDecisionReference(kind=ExplanationReferenceKind.REASON_CODE, id=code)


def _is_overweight(
    allocation_rating: FitRating | None, is_largest_position: bool, portfolio_concentration_level: ConcentrationLevel
) -> bool:
    """Deliverable 6 -- prefers the holding-specific, already-computed
    Portfolio Fit ALLOCATION rating when one exists; falls back to the
    portfolio-wide concentration level only for a Case Portfolio Fit
    has not assessed at all (e.g. a Watchlist-only candidate)."""
    if allocation_rating is not None:
        return allocation_rating in _OVERWEIGHT_FIT_RATINGS
    return is_largest_position and portfolio_concentration_level in (ConcentrationLevel.HIGH, ConcentrationLevel.ELEVATED)


def classify_portfolio_decision(
    action: DecisionAction,
    reliability_level: ReliabilityLevel,
    is_overweight: bool,
    has_capital_competition: bool,
) -> PortfolioDecisionCategory:
    """Deliverable 6 -- a fixed priority cascade, never a score. Each
    step below is a real, disclosed rule; the first one that matches
    decides the category, the same "declared order, never invented"
    discipline every prior classification in this program already
    established."""
    if reliability_level is ReliabilityLevel.UNKNOWN:
        return PortfolioDecisionCategory.UNKNOWN
    if reliability_level is ReliabilityLevel.UNAVAILABLE:
        return PortfolioDecisionCategory.OPERATIONALLY_LIMITED
    if action in _CAPITAL_INCREASING_ACTIONS and is_overweight:
        return PortfolioDecisionCategory.CONFLICTS_WITH_PORTFOLIO
    if action in _CAPITAL_DECREASING_ACTIONS and is_overweight:
        return PortfolioDecisionCategory.SUPPORTS_PORTFOLIO
    if action in _CAPITAL_INCREASING_ACTIONS and has_capital_competition:
        return PortfolioDecisionCategory.REQUIRES_REVIEW
    return PortfolioDecisionCategory.NEUTRAL


def build_capital_competition(
    case_id: str, alternatives: tuple[DecisionAlternative, ...]
) -> CapitalCompetition:
    """Deliverable 4 -- reclassifies `OpportunityCost.tradeoffs`'
    already-real alternatives, never recomputes them."""
    competing_kinds = (AlternativeKind.INCREASE_EXISTING_HOLDING, AlternativeKind.OPEN_NEW_POSITION)
    competing = tuple(a for a in alternatives if a.kind in competing_kinds)
    non_competing = tuple(a for a in alternatives if a.kind not in competing_kinds)
    return CapitalCompetition(case_id=case_id, competing_alternatives=competing, non_competing_alternatives=non_competing)


def build_portfolio_decision(
    case_id: str,
    *,
    action: DecisionAction,
    reliability_level: ReliabilityLevel,
    is_existing_holding: bool,
    current_weight_percent: float | None,
    is_largest_position: bool,
    allocation_rating: FitRating | None,
    portfolio_concentration_level: ConcentrationLevel,
    concentration_findings_for_ticker: tuple[KeyFindingKind, ...],
    large_unallocated: bool,
    alternatives: tuple[DecisionAlternative, ...],
    generated_at: datetime,
) -> PortfolioDecision:
    """Deliverable 3 -- one deterministic builder, every input already
    computed elsewhere, nothing recomputed."""
    overweight = _is_overweight(allocation_rating, is_largest_position, portfolio_concentration_level)
    capital_competition = build_capital_competition(case_id, alternatives)
    has_competition = len(capital_competition.competing_alternatives) > 0
    category = classify_portfolio_decision(action, reliability_level, overweight, has_competition)

    supporting: list[PortfolioDecisionReason] = []
    limiting: list[PortfolioDecisionReason] = []

    if allocation_rating is not None:
        target = supporting if allocation_rating in _SUPPORTING_FIT_RATINGS else limiting
        if allocation_rating in _SUPPORTING_FIT_RATINGS or allocation_rating in _OVERWEIGHT_FIT_RATINGS:
            target.append(PortfolioDecisionReason(PortfolioDecisionReasonSource.PORTFOLIO_FIT, _reason_ref(allocation_rating.value)))

    for finding_kind in concentration_findings_for_ticker:
        limiting.append(PortfolioDecisionReason(PortfolioDecisionReasonSource.PORTFOLIO_INTELLIGENCE, _reason_ref(finding_kind.value)))

    if large_unallocated and action in _CAPITAL_INCREASING_ACTIONS:
        supporting.append(
            PortfolioDecisionReason(PortfolioDecisionReasonSource.PORTFOLIO_INTELLIGENCE, _reason_ref(KeyFindingKind.LARGE_UNALLOCATED.value))
        )

    for alternative in capital_competition.competing_alternatives:
        limiting.append(PortfolioDecisionReason(PortfolioDecisionReasonSource.OPPORTUNITY_COST, _reason_ref(alternative.kind.value)))

    if reliability_level in (ReliabilityLevel.HIGH, ReliabilityLevel.MODERATE):
        supporting.append(PortfolioDecisionReason(PortfolioDecisionReasonSource.DECISION_RELIABILITY, _reason_ref(reliability_level.value)))
    else:
        limiting.append(PortfolioDecisionReason(PortfolioDecisionReasonSource.DECISION_RELIABILITY, _reason_ref(reliability_level.value)))

    impact = PortfolioDecisionImpact(
        is_existing_holding=is_existing_holding,
        current_weight_percent=current_weight_percent,
        is_largest_position=is_largest_position,
        allocation_rating=allocation_rating.value if allocation_rating is not None else None,
        portfolio_concentration_level=portfolio_concentration_level,
    )

    return PortfolioDecision(
        case_id=case_id,
        action=action,
        category=category,
        impact=impact,
        capital_competition=capital_competition,
        supporting_reasons=tuple(supporting),
        limiting_reasons=tuple(limiting),
        primary_limiting_reason=limiting[0] if limiting else None,
        generated_at=generated_at,
    )


def summarize_portfolio_decision(decision: PortfolioDecision) -> PortfolioDecisionSummary:
    return PortfolioDecisionSummary(
        case_id=decision.case_id,
        action=decision.action,
        category=decision.category,
        primary_limiting_reason=decision.primary_limiting_reason,
        generated_at=decision.generated_at,
    )


def compare_portfolio_decisions(a: PortfolioDecision, b: PortfolioDecision) -> PortfolioDecisionComparison:
    """Deliverable 10 -- better portfolio fit (by the same fixed
    category rank, `None` on a genuine tie), shared strengths/
    weaknesses, shared capital competitors. Never an overall winner."""
    better_case_id: str | None
    if _CATEGORY_RANK[a.category] == _CATEGORY_RANK[b.category]:
        better_case_id = None
    elif _CATEGORY_RANK[a.category] > _CATEGORY_RANK[b.category]:
        better_case_id = a.case_id
    else:
        better_case_id = b.case_id

    a_limiting_by_id = {r.reference.id: r.reference for r in a.limiting_reasons}
    b_limiting_by_id = {r.reference.id: r.reference for r in b.limiting_reasons}
    shared_weaknesses = tuple(a_limiting_by_id[i] for i in sorted(set(a_limiting_by_id) & set(b_limiting_by_id)))

    a_supporting_by_id = {r.reference.id: r.reference for r in a.supporting_reasons}
    b_supporting_by_id = {r.reference.id: r.reference for r in b.supporting_reasons}
    shared_strengths = tuple(a_supporting_by_id[i] for i in sorted(set(a_supporting_by_id) & set(b_supporting_by_id)))

    a_competitor_ids = {alt.case_id for alt in a.capital_competition.competing_alternatives if alt.case_id is not None}
    b_competitor_ids = {alt.case_id for alt in b.capital_competition.competing_alternatives if alt.case_id is not None}
    shared_competitors = tuple(sorted(a_competitor_ids & b_competitor_ids))

    return PortfolioDecisionComparison(
        a=a,
        b=b,
        better_portfolio_fit_case_id=better_case_id,
        shared_strengths=shared_strengths,
        shared_weaknesses=shared_weaknesses,
        shared_competitor_case_ids=shared_competitors,
    )


def detect_portfolio_decision_change(
    previous: PortfolioDecision | None, current: PortfolioDecision, *, detected_at: datetime
) -> PortfolioDecisionChange | None:
    """"No event, no timestamp" -- `None` on the first-ever computation
    or when nothing about the portfolio decision actually moved."""
    if previous is None:
        return None

    previous_limiting = {r.reference.id: r for r in previous.limiting_reasons}
    current_limiting = {r.reference.id: r for r in current.limiting_reasons}
    new_limiting = tuple(current_limiting[i] for i in current_limiting if i not in previous_limiting)
    resolved_limiting = tuple(previous_limiting[i] for i in previous_limiting if i not in current_limiting)

    previous_competitor_ids = {a.case_id for a in previous.capital_competition.competing_alternatives if a.case_id is not None}
    current_competitor_ids = {a.case_id for a in current.capital_competition.competing_alternatives if a.case_id is not None}
    competition_changed = previous_competitor_ids != current_competitor_ids

    if previous.category == current.category and not new_limiting and not resolved_limiting and not competition_changed:
        return None

    return PortfolioDecisionChange(
        case_id=current.case_id,
        previous_category=previous.category,
        current_category=current.category,
        competition_changed=competition_changed,
        new_limiting=new_limiting,
        resolved_limiting=resolved_limiting,
        detected_at=detected_at,
    )


def build_portfolio_synthesis_breakdown(
    items: tuple[tuple[str, PortfolioDecision], ...],
) -> PortfolioSynthesisBreakdown:
    """Deliverable 8 -- ticker groupings only, in the caller's own
    existing order; never re-ranked, never a re-ordering of holdings."""
    supports = tuple(ticker for ticker, d in items if d.category is PortfolioDecisionCategory.SUPPORTS_PORTFOLIO)
    highest_competition = tuple(ticker for ticker, d in items if len(d.capital_competition.competing_alternatives) > 0)
    conflicts = tuple(ticker for ticker, d in items if d.category is PortfolioDecisionCategory.CONFLICTS_WITH_PORTFOLIO)
    neutral = tuple(ticker for ticker, d in items if d.category is PortfolioDecisionCategory.NEUTRAL)
    return PortfolioSynthesisBreakdown(
        supports_portfolio=supports,
        highest_capital_competition=highest_competition,
        conflicts_with_portfolio=conflicts,
        neutral=neutral,
    )
