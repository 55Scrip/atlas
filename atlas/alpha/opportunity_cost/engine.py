"""The Decision Alternatives & Opportunity Cost engine itself -- pure,
deterministic, no I/O. Given the exact same inputs, every function
here always returns the exact same result.

**Every alternative is grounded in an already-real fact, never
invented.** `build_alternatives` never fabricates a competing company:
an `INCREASE_EXISTING_HOLDING`/`OPEN_NEW_POSITION` alternative only
exists when another already-known Case's own Investment Decision
(Sprint 1, unmodified) is currently `BUY`/`ADD`; `WAIT`/`KEEP_CASH`/
`NO_ACTION` only exist when a real grounding reason -- the current
Case's own immediate Decision Path blocker (Sprint 3), or its own top
Investment Decision supporting reason (Sprint 1) -- is actually
present. No alternative is ever constructed with a fabricated reason.

**`build_alternative_comparison` reuses Sprint 2's and Sprint 3's own
`compare_convictions`/`compare_decision_paths` verbatim.** The one new
comparison this package adds (`more_dependency_blocked_case_id`) reads
directly from each side's own already-computed `DecisionPath.steps`,
never a second scoring algorithm.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.alpha.decision_path.engine import compare_decision_paths
from atlas.alpha.decision_path.models import DecisionPath, RequiredProgressKind
from atlas.alpha.investment_decision.models import DecisionAction, DecisionReason
from atlas.alpha.opportunity_cost.models import (
    AlternativeComparison,
    AlternativeKind,
    AlternativeReason,
    AlternativeReasonSource,
    DecisionAlternative,
    DecisionAlternativeSummary,
    DecisionTradeoff,
    OpportunityCost,
    OpportunityCostChange,
    PortfolioOpportunityCostBreakdown,
)
from atlas.alpha.recommendation_conviction.engine import compare_convictions
from atlas.alpha.recommendation_conviction.models import ConvictionStrength, RecommendationConviction

__all__ = [
    "OtherCaseSummary",
    "build_alternatives",
    "build_alternative_comparison",
    "build_opportunity_cost",
    "summarize_opportunity_cost",
    "detect_opportunity_cost_change",
    "build_portfolio_opportunity_cost_breakdown",
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

_COMPETING_ACTIONS = frozenset({DecisionAction.BUY, DecisionAction.ADD})
_NO_ACTION_CURRENT_ACTIONS = frozenset({DecisionAction.HOLD, DecisionAction.WAIT, DecisionAction.NO_DECISION})


@dataclass(frozen=True)
class OtherCaseSummary:
    """Everything about one other already-known Case this package
    needs to decide whether it is a real alternative -- every field a
    direct read of that Case's own already-computed Investment
    Decision/Recommendation Conviction, nothing recomputed."""

    case_id: str
    ticker: str
    is_holding: bool
    action: DecisionAction
    top_reason: DecisionReason | None
    strength: ConvictionStrength | None


def _reason_from_decision_reason(reason: DecisionReason) -> AlternativeReason:
    return AlternativeReason(source=AlternativeReasonSource(reason.source.value), code=reason.code)


def _grounding_reason(decision_supporting_reasons: tuple[DecisionReason, ...], path: DecisionPath) -> AlternativeReason | None:
    """The one real fact that grounds `WAIT`/`KEEP_CASH`/`NO_ACTION`:
    the current Case's own immediate Decision Path blocker when one is
    real and present, otherwise its own top Investment Decision
    supporting reason. `None` only when neither exists -- the genuinely
    empty case, where these alternatives are honestly not explainable
    today and are therefore never constructed."""
    if path.immediate_blocker is not None:
        dependency = path.immediate_blocker.dependency
        return AlternativeReason(source=AlternativeReasonSource(dependency.source.value), code=dependency.code)
    if decision_supporting_reasons:
        return _reason_from_decision_reason(decision_supporting_reasons[0])
    return None


def build_alternatives(
    current_action: DecisionAction,
    decision_supporting_reasons: tuple[DecisionReason, ...],
    path: DecisionPath,
    others: tuple[OtherCaseSummary, ...],
) -> tuple[DecisionAlternative, ...]:
    alternatives: list[DecisionAlternative] = []

    for other in others:
        if other.action not in _COMPETING_ACTIONS or other.top_reason is None:
            continue
        kind = AlternativeKind.INCREASE_EXISTING_HOLDING if other.is_holding else AlternativeKind.OPEN_NEW_POSITION
        alternatives.append(
            DecisionAlternative(
                kind=kind,
                case_id=other.case_id,
                ticker=other.ticker,
                action=other.action,
                strength=other.strength,
                reason=_reason_from_decision_reason(other.top_reason),
            )
        )

    grounding = _grounding_reason(decision_supporting_reasons, path)
    if grounding is not None:
        alternatives.append(DecisionAlternative(AlternativeKind.WAIT, None, None, None, None, grounding))
        alternatives.append(DecisionAlternative(AlternativeKind.KEEP_CASH, None, None, None, None, grounding))
        if current_action in _NO_ACTION_CURRENT_ACTIONS:
            alternatives.append(DecisionAlternative(AlternativeKind.NO_ACTION, None, None, None, None, grounding))

    return tuple(alternatives)


def _pick_more(a_value: int, b_value: int, a_id: str, b_id: str) -> str | None:
    if a_value > b_value:
        return a_id
    if b_value > a_value:
        return b_id
    return None


def build_alternative_comparison(
    current_conviction: RecommendationConviction,
    other_conviction: RecommendationConviction,
    current_path: DecisionPath,
    other_path: DecisionPath,
) -> AlternativeComparison:
    current_dependency_count = sum(1 for s in current_path.steps if s.progress_kind is RequiredProgressKind.DEPENDENCY)
    other_dependency_count = sum(1 for s in other_path.steps if s.progress_kind is RequiredProgressKind.DEPENDENCY)
    return AlternativeComparison(
        conviction=compare_convictions(current_conviction, other_conviction),
        path=compare_decision_paths(current_path, other_path),
        more_dependency_blocked_case_id=_pick_more(
            current_dependency_count, other_dependency_count, current_path.case_id, other_path.case_id
        ),
    )


def build_opportunity_cost(
    case_id: str,
    current_action: DecisionAction,
    tradeoffs: tuple[DecisionTradeoff, ...],
    *,
    generated_at: datetime,
) -> OpportunityCost:
    return OpportunityCost(case_id=case_id, current_action=current_action, tradeoffs=tradeoffs, generated_at=generated_at)


def summarize_opportunity_cost(opportunity_cost: OpportunityCost) -> DecisionAlternativeSummary:
    primary = opportunity_cost.tradeoffs[0].alternative if opportunity_cost.tradeoffs else None
    return DecisionAlternativeSummary(
        case_id=opportunity_cost.case_id,
        current_action=opportunity_cost.current_action,
        primary_alternative=primary,
        alternative_count=len(opportunity_cost.tradeoffs),
        generated_at=opportunity_cost.generated_at,
    )


def detect_opportunity_cost_change(
    previous: OpportunityCost | None, current: OpportunityCost, *, detected_at: datetime
) -> OpportunityCostChange | None:
    """"No event, no timestamp" -- `None` when this is the first-ever
    computation, or when nothing about the alternative set actually
    moved. Identity across the two snapshots is `(kind, case_id)`."""
    if previous is None:
        return None

    previous_by_key = {(t.alternative.kind, t.alternative.case_id): t.alternative for t in previous.tradeoffs}
    current_by_key = {(t.alternative.kind, t.alternative.case_id): t.alternative for t in current.tradeoffs}

    new_keys = set(current_by_key) - set(previous_by_key)
    disappeared_keys = set(previous_by_key) - set(current_by_key)
    shared_keys = set(current_by_key) & set(previous_by_key)

    strengthened: list[DecisionAlternative] = []
    weakened: list[DecisionAlternative] = []
    for key in shared_keys:
        previous_alternative = previous_by_key[key]
        current_alternative = current_by_key[key]
        if (
            previous_alternative.strength is not None
            and current_alternative.strength is not None
            and previous_alternative.strength != current_alternative.strength
        ):
            if _STRENGTH_RANK[current_alternative.strength] > _STRENGTH_RANK[previous_alternative.strength]:
                strengthened.append(current_alternative)
            else:
                weakened.append(current_alternative)

    previous_primary_key = (
        (previous.tradeoffs[0].alternative.kind, previous.tradeoffs[0].alternative.case_id) if previous.tradeoffs else None
    )
    current_primary_key = (
        (current.tradeoffs[0].alternative.kind, current.tradeoffs[0].alternative.case_id) if current.tradeoffs else None
    )
    primary_alternative_changed = previous_primary_key != current_primary_key

    new_alternatives = tuple(current_by_key[key] for key in current_by_key if key in new_keys)
    disappeared_alternatives = tuple(previous_by_key[key] for key in previous_by_key if key in disappeared_keys)

    if not new_alternatives and not disappeared_alternatives and not strengthened and not weakened and not primary_alternative_changed:
        return None

    return OpportunityCostChange(
        case_id=current.case_id,
        new_alternatives=new_alternatives,
        disappeared_alternatives=disappeared_alternatives,
        strengthened_alternatives=tuple(strengthened),
        weakened_alternatives=tuple(weakened),
        primary_alternative_changed=primary_alternative_changed,
        detected_at=detected_at,
    )


def build_portfolio_opportunity_cost_breakdown(
    holding_items: tuple[tuple[str, OpportunityCost], ...],
    watchlist_competing_tickers: tuple[str, ...],
) -> PortfolioOpportunityCostBreakdown:
    """Deliverable 7 -- ticker groupings only, in the caller's own
    existing order; never re-ranked, never turned into an allocation
    suggestion.

    **Membership, not primacy.** `waiting_preferable`/`no_action
    _appropriate` check whether that `AlternativeKind` is present
    *anywhere* among a holding's own tradeoffs, not only whether it
    happens to be `tradeoffs[0]`. `build_alternatives` always
    constructs `WAIT` before `NO_ACTION` when both are grounded (a
    fixed, deterministic order -- see that function's own docstring),
    so a primacy-only check would leave `no_action_appropriate`
    structurally near-empty in practice: any holding for which "no
    action needed" is genuinely true almost always has a real `WAIT`
    grounding too, and `WAIT` would always win the `[0]` slot. The two
    facts are not mutually exclusive in reality, so this check does
    not treat them as such."""
    competing = tuple(
        ticker for ticker, oc in holding_items if oc.current_action in _COMPETING_ACTIONS
    )
    waiting_preferable = tuple(
        ticker
        for ticker, oc in holding_items
        if any(t.alternative.kind is AlternativeKind.WAIT for t in oc.tradeoffs)
    )
    no_action_appropriate = tuple(
        ticker
        for ticker, oc in holding_items
        if any(t.alternative.kind is AlternativeKind.NO_ACTION for t in oc.tradeoffs)
    )
    return PortfolioOpportunityCostBreakdown(
        holdings_competing_for_capital=competing,
        watchlist_competing_with_holdings=watchlist_competing_tickers,
        waiting_preferable=waiting_preferable,
        no_action_appropriate=no_action_appropriate,
    )
