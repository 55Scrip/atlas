"""Orchestration for the Portfolio Fit Engine -- the only part of this
package that performs I/O. Composes `atlas.alpha.investment_case
.InvestmentCaseCompositionService`, `atlas.alpha.portfolio.AlphaPortfolioStore`,
`atlas.alpha.watchlist.AlphaWatchlistStore`, and `atlas.alpha.case_membership
.known_cases` -- every one of them unmodified -- and hands their output to
the pure `engine.py`. No new repository, no new table, no new persistence
(Deliverable 9).

**This package leaves `atlas.alpha.portfolio_intelligence.PortfolioFitStatus`
untouched.** That placeholder's own docstring ties its future availability
specifically to the canonical pipeline's `PortfolioDoctrineFactor`
evaluation (`atlas.decision_engine.contracts.PortfolioFinding`) becoming
real -- a different, Core-side capability this sprint does not build.
`PortfolioFitAssessment` here is a separate, disclosed Alpha-layer
interpretation; the two are not the same claim and this service does not
conflate them. See this package's own `__init__.py`.

**Deliberately per-Case `InvestmentCaseCompositionService.build`, not
`.build_many`** -- `build_many` does not resolve a Watchlist-only Case's
ticker (it was built for Portfolio Cockpit, a Portfolio-only surface; see
its own docstring). `atlas.alpha.daily_brief` already solved this exact
"must cover Portfolio + Watchlist" problem the same way, for the same
documented reason -- reused here rather than re-solved.
"""
from __future__ import annotations

from atlas.alpha.case_membership import known_cases, resolve_case_id_for_ticker
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.models import AlphaHolding, AlphaPortfolioState, EntryMode
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio_fit.engine import assess_portfolio_fit, compare_fit
from atlas.alpha.portfolio_fit.models import FitComparison, FitRating, PortfolioFitAssessment
from atlas.alpha.watchlist.store import AlphaWatchlistStore

__all__ = ["PortfolioFitService"]

_RANK_ORDER = {
    FitRating.EXCELLENT: 0,
    FitRating.GOOD: 1,
    FitRating.NEUTRAL: 2,
    FitRating.WEAK: 3,
    FitRating.POOR: 4,
    FitRating.UNAVAILABLE: 5,
}


class PortfolioFitService:
    def __init__(
        self,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
        composition_service: InvestmentCaseCompositionService,
    ) -> None:
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store
        self._composition_service = composition_service

    def _ticker_for_case(self, case_id: str, composition, portfolio_state: AlphaPortfolioState | None) -> str:
        """Resolves the real ticker for a Case whose caller only has a
        `case_id` in hand (`assess_for_case`, the Investment Case page's
        own path). `composition.holding_context` only ever resolves a
        *Portfolio* holding, so a Watchlist-only Case falls through to
        `AlphaWatchlistStore.get_by_case_id` -- the same store
        `resolve_case_id_for_ticker` already reads, reused rather than
        re-queried differently. Only a bare Case linked to neither (an
        edge case with no ticker anywhere in Atlas for it) falls back to
        the `case_id` itself, honestly, as a last resort."""
        if composition.holding_context is not None:
            return composition.holding_context.ticker
        watchlist_entry = self._watchlist_store.get_by_case_id(case_id)
        if watchlist_entry is not None:
            return watchlist_entry.ticker
        return case_id

    def _holding_for_ticker(self, ticker: str, portfolio_state: AlphaPortfolioState | None) -> AlphaHolding | None:
        if portfolio_state is None:
            return None
        return next((h for h in portfolio_state.holdings if h.ticker == ticker), None)

    def _assess(
        self,
        case_id: str,
        portfolio_state: AlphaPortfolioState | None,
        ticker: str | None = None,
    ) -> PortfolioFitAssessment | None:
        composition = self._composition_service.build(case_id)
        if composition is None:
            return None
        # No portfolio has been established at all yet -- a real, honest
        # state (every field absent/empty), never a fabricated one; the
        # Allocation Fit and Cash Impact dimensions below both already
        # degrade to `UNAVAILABLE` correctly on empty holdings/no cash.
        state = portfolio_state if portfolio_state is not None else AlphaPortfolioState(
            established_at=composition.generated_at,
            updated_at=composition.generated_at,
            entry_mode=EntryMode.FROM_SCRATCH,
        )
        holding = composition.holding_context
        resolved_ticker = ticker if ticker is not None else self._ticker_for_case(case_id, composition, state)
        return assess_portfolio_fit(composition=composition, portfolio_state=state, holding=holding, ticker=resolved_ticker)

    def assess_for_case(self, case_id: str) -> PortfolioFitAssessment | None:
        """Deliverable 8 -- Investment Case's own "Portfolio Fit" section
        already has a `case_id` in hand; this is the direct path."""
        return self._assess(case_id, self._portfolio_store.get())

    def assess_for_ticker(self, ticker: str) -> PortfolioFitAssessment | None:
        case_id = resolve_case_id_for_ticker(ticker, self._portfolio_store, self._watchlist_store)
        if case_id is None:
            return None
        return self._assess(case_id, self._portfolio_store.get(), ticker=ticker)

    def compare(self, ticker_a: str, ticker_b: str) -> FitComparison | None:
        """Deliverable 4 -- Company Comparison."""
        assessment_a = self.assess_for_ticker(ticker_a)
        assessment_b = self.assess_for_ticker(ticker_b)
        if assessment_a is None or assessment_b is None:
            return None
        return compare_fit(assessment_a, assessment_b)

    def assess_all_holdings(self) -> tuple[PortfolioFitAssessment, ...]:
        """Deliverable 7 -- Portfolio's own "best/worst fit today" and
        (via `.trend`) "improved/worsened" sections. Only holdings with a
        linked Case can be assessed at all -- a holding awaiting a Case
        has no `CanonicalAnalysis` to read (disclosed by simply not
        appearing, the same honest-absence contract every other Alpha
        capability in this codebase already uses)."""
        portfolio_state = self._portfolio_store.get()
        if portfolio_state is None:
            return ()
        assessments = []
        for holding in portfolio_state.holdings:
            if holding.case_id is None:
                continue
            assessment = self._assess(holding.case_id, portfolio_state, ticker=holding.ticker)
            if assessment is not None:
                assessments.append(assessment)
        return tuple(sorted(assessments, key=lambda a: (_RANK_ORDER[a.overall], a.ticker)))

    def rank_candidates(self) -> tuple[PortfolioFitAssessment, ...]:
        """Deliverable 6 -- Discovery's own candidate sort. "Candidates"
        here means Watchlist Cases not already held (an existing holding
        is not a candidate to consider buying, it already is one) --
        exactly the set `atlas.alpha.daily_brief`'s own "Watchlist
        Updates" slice already means by the same phrase. A raw
        `atlas.alpha.security_discovery` ticker-search result with no
        Case yet cannot be ranked at all (no `CanonicalAnalysis` exists
        for it) -- disclosed by omission, never a fabricated rating."""
        portfolio_state = self._portfolio_store.get()
        held_tickers = {h.ticker for h in portfolio_state.holdings} if portfolio_state is not None else set()
        assessments = []
        for case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            if ticker is not None and ticker in held_tickers:
                continue
            assessment = self._assess(case_id, portfolio_state, ticker=ticker)
            if assessment is not None:
                assessments.append(assessment)
        return tuple(sorted(assessments, key=lambda a: (_RANK_ORDER[a.overall], a.ticker)))
