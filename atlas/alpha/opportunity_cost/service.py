"""Orchestration for Decision Alternatives & Opportunity Cost. The
only part of this package that performs I/O.

**Reuses three already-computed engines, recomputes nothing.**
`InvestmentDecisionService.synthesize_for_case` (Sprint 1, unmodified
-- every alternative's own action/reason), `RecommendationConviction
Service.assess_for_case` (Sprint 2, unmodified -- every alternative's
own strength, and the pairwise comparison input), `DecisionPathService
.build_for_case` (Sprint 3, unmodified -- the current Case's own
grounding reason for `WAIT`/`KEEP_CASH`/`NO_ACTION`, and the pairwise
comparison input). See this package's own `__init__.py` for the full
audit this reuse is based on.

**Always computed live**, the same choice every sibling Decision Layer
service already makes. The one persisted table exists solely so the
*previous* computation can be read back for change detection.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.case_membership import known_cases, resolve_case_id_for_ticker
from atlas.alpha.decision_path.service import DecisionPathService
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.investment_decision.service import InvestmentDecisionService
from atlas.alpha.opportunity_cost.engine import (
    OtherCaseSummary,
    build_alternative_comparison,
    build_alternatives,
    build_opportunity_cost,
    build_portfolio_opportunity_cost_breakdown,
    detect_opportunity_cost_change,
    summarize_opportunity_cost,
)
from atlas.alpha.opportunity_cost.models import (
    AlternativeComparison,
    DecisionAlternativeSummary,
    DecisionTradeoff,
    OpportunityCost,
    OpportunityCostChange,
    PortfolioOpportunityCostBreakdown,
)
from atlas.alpha.opportunity_cost.repository import SqlAlchemyOpportunityCostResultRepository
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.recommendation_conviction.service import RecommendationConvictionService
from atlas.alpha.watchlist.store import AlphaWatchlistStore

__all__ = ["OpportunityCostService"]

_COMPETING_ACTIONS = frozenset({DecisionAction.BUY, DecisionAction.ADD})


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OpportunityCostService:
    def __init__(
        self,
        investment_decision_service: InvestmentDecisionService,
        recommendation_conviction_service: RecommendationConvictionService,
        decision_path_service: DecisionPathService,
        result_repository: SqlAlchemyOpportunityCostResultRepository,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
    ) -> None:
        self._investment_decision_service = investment_decision_service
        self._recommendation_conviction_service = recommendation_conviction_service
        self._decision_path_service = decision_path_service
        self._result_repository = result_repository
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store
        # Request-scoped memoization (Investment Case Decision Layer
        # Bundle sprint) -- same pattern and justification as the
        # Decision Layer Runtime Verification sprint's own fix, applied
        # here because the Bundle endpoint made real what that earlier
        # sprint had only that this method already had `count=1` in
        # every endpoint tested at the time: the Bundle calls this
        # method up to four times for the same `case_id` within one
        # request (directly, plus transitively via `decision_memory`,
        # `decision_explanation`, and `portfolio_decision`), each of
        # which would otherwise independently re-run
        # `_other_case_summaries` -- the full, expensive scan over
        # every other known Case -- from scratch. `ticker` is
        # deliberately excluded from the key -- see
        # `recommendation_conviction.service`'s own identical comment
        # for why; the repository upsert only runs on the one call that
        # actually computes a fresh result, not on a cache hit.
        self._assess_for_case_cache: dict[str, OpportunityCost | None] = {}

    def _ticker_for_case(self, case_id: str) -> str | None:
        for known_case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            if known_case_id == case_id:
                return ticker
        return None

    def _other_case_summaries(self, exclude_case_id: str) -> tuple[OtherCaseSummary, ...]:
        portfolio_state = self._portfolio_store.get()
        held_tickers = {h.ticker for h in portfolio_state.holdings} if portfolio_state is not None else set()

        summaries: list[OtherCaseSummary] = []
        for case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            if case_id == exclude_case_id or ticker is None:
                continue
            decision = self._investment_decision_service.synthesize_for_case(case_id, ticker=ticker)
            if decision is None or decision.action not in _COMPETING_ACTIONS:
                continue
            conviction = self._recommendation_conviction_service.assess_for_case(case_id, ticker=ticker)
            summaries.append(
                OtherCaseSummary(
                    case_id=case_id,
                    ticker=ticker,
                    is_holding=ticker in held_tickers,
                    action=decision.action,
                    top_reason=decision.supporting_reasons[0] if decision.supporting_reasons else None,
                    strength=conviction.strength if conviction is not None else None,
                )
            )
        return tuple(summaries)

    def assess_for_case(self, case_id: str, *, ticker: str | None = None) -> OpportunityCost | None:
        """`None` only when `case_id` does not resolve to a real Case
        or a real Investment Decision -- the same honest-absence
        contract every sibling Decision Layer service already uses."""
        resolved_ticker = ticker if ticker is not None else self._ticker_for_case(case_id)
        if case_id in self._assess_for_case_cache:
            return self._assess_for_case_cache[case_id]
        result = self._assess_for_case_uncached(case_id, ticker=resolved_ticker)
        self._assess_for_case_cache[case_id] = result
        if result is not None:
            self._result_repository.upsert(result, ticker=resolved_ticker)
        return result

    def _assess_for_case_uncached(self, case_id: str, *, ticker: str | None) -> OpportunityCost | None:
        decision = self._investment_decision_service.synthesize_for_case(case_id, ticker=ticker)
        if decision is None:
            return None
        conviction = self._recommendation_conviction_service.assess_for_case(case_id, ticker=ticker)
        if conviction is None:
            return None
        path = self._decision_path_service.build_for_case(case_id, ticker=ticker)
        if path is None:
            return None

        others = self._other_case_summaries(case_id)
        alternatives = build_alternatives(decision.action, decision.supporting_reasons, path, others)

        tradeoffs: list[DecisionTradeoff] = []
        for alternative in alternatives:
            comparison = None
            if alternative.case_id is not None:
                other_conviction = self._recommendation_conviction_service.assess_for_case(
                    alternative.case_id, ticker=alternative.ticker
                )
                other_path = self._decision_path_service.build_for_case(alternative.case_id, ticker=alternative.ticker)
                if other_conviction is not None and other_path is not None:
                    comparison = build_alternative_comparison(conviction, other_conviction, path, other_path)
            tradeoffs.append(DecisionTradeoff(alternative=alternative, comparison=comparison))

        return build_opportunity_cost(case_id, decision.action, tuple(tradeoffs), generated_at=_utc_now())

    def assess_for_ticker(self, ticker: str) -> OpportunityCost | None:
        case_id = resolve_case_id_for_ticker(ticker, self._portfolio_store, self._watchlist_store)
        if case_id is None:
            return None
        return self.assess_for_case(case_id, ticker=ticker)

    def summary_for_case(self, case_id: str, *, ticker: str | None = None) -> DecisionAlternativeSummary | None:
        opportunity_cost = self.assess_for_case(case_id, ticker=ticker)
        return summarize_opportunity_cost(opportunity_cost) if opportunity_cost is not None else None

    def change_for_case(self, case_id: str, *, ticker: str | None = None) -> OpportunityCostChange | None:
        """Reads the cache *before* this call's own fresh computation
        overwrites it."""
        previous = self._result_repository.get(case_id)
        current = self.assess_for_case(case_id, ticker=ticker)
        if current is None:
            return None
        return detect_opportunity_cost_change(previous, current, detected_at=current.generated_at)

    def current_and_change_for_case(
        self, case_id: str, *, ticker: str | None = None
    ) -> tuple[OpportunityCost | None, OpportunityCostChange | None]:
        """Investment Case Decision Layer Bundle -- returns both
        `current` and `change` from a single cross-case scan instead of
        the two independent ones `assess_for_case` and `change_for_case`
        would otherwise each trigger (this method's own body is exactly
        `change_for_case`'s, extended to also keep `current`). Preserves
        the identical read-before-write ordering: `previous` is read
        before `assess_for_case` runs and (on a cache miss) upserts."""
        previous = self._result_repository.get(case_id)
        current = self.assess_for_case(case_id, ticker=ticker)
        if current is None:
            return None, None
        change = detect_opportunity_cost_change(previous, current, detected_at=current.generated_at)
        return current, change

    def compare(self, ticker_a: str, ticker_b: str) -> AlternativeComparison | None:
        """Deliverable 9 -- the exact `AlternativeComparison` shape
        every alternative-with-a-real-Case already carries, exposed
        directly for two arbitrary tickers (never restricted to an
        actual alternative pair)."""
        case_id_a = resolve_case_id_for_ticker(ticker_a, self._portfolio_store, self._watchlist_store)
        case_id_b = resolve_case_id_for_ticker(ticker_b, self._portfolio_store, self._watchlist_store)
        if case_id_a is None or case_id_b is None:
            return None

        conviction_a = self._recommendation_conviction_service.assess_for_case(case_id_a, ticker=ticker_a)
        conviction_b = self._recommendation_conviction_service.assess_for_case(case_id_b, ticker=ticker_b)
        path_a = self._decision_path_service.build_for_case(case_id_a, ticker=ticker_a)
        path_b = self._decision_path_service.build_for_case(case_id_b, ticker=ticker_b)
        if conviction_a is None or conviction_b is None or path_a is None or path_b is None:
            return None

        return build_alternative_comparison(conviction_a, conviction_b, path_a, path_b)

    def portfolio_opportunity_cost_breakdown(self) -> PortfolioOpportunityCostBreakdown:
        """Deliverable 7 -- holdings-only scope for the primary
        breakdown, the same scope every sibling service already uses,
        plus one Watchlist-scoped fact (`watchlist_competing_with
        _holdings`) the brief explicitly asks Portfolio to surface.
        Never re-ranked, never turned into an allocation suggestion."""
        portfolio_state = self._portfolio_store.get()
        holdings = portfolio_state.holdings if portfolio_state is not None else ()
        held_tickers = {h.ticker for h in holdings}

        holding_items: list[tuple[str, OpportunityCost]] = []
        for holding in holdings:
            if holding.case_id is None:
                continue
            opportunity_cost = self.assess_for_case(holding.case_id, ticker=holding.ticker)
            if opportunity_cost is not None:
                holding_items.append((holding.ticker, opportunity_cost))

        watchlist_competing: list[str] = []
        for entry in self._watchlist_store.list_all():
            if entry.ticker in held_tickers:
                continue
            decision = self._investment_decision_service.synthesize_for_case(entry.case_id, ticker=entry.ticker)
            if decision is not None and decision.action is DecisionAction.BUY:
                watchlist_competing.append(entry.ticker)

        return build_portfolio_opportunity_cost_breakdown(tuple(holding_items), tuple(watchlist_competing))
