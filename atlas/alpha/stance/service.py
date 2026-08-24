"""Orchestration for the Stance Engine -- the only part of this package
that performs I/O. Composes `atlas.alpha.investment_case
.InvestmentCaseCompositionService` and `atlas.alpha.portfolio_fit
.PortfolioFitService` (both unmodified) and `atlas.alpha.coverage
.assess_coverage` (Atlas Intelligence Sprint 1), and hands their output
to the pure `engine.py`. No new repository, no new table, no new
persistence -- mirrors `atlas.alpha.portfolio_fit.service
.PortfolioFitService`'s own shape and reuse discipline exactly, one
layer higher (this package is the one thing in the whole Alpha layer
that legitimately depends on Portfolio Fit's own output, since a Stance
needs to know whether an otherwise-favorable direction still fits the
portfolio -- see this package's own `__init__.py`).
"""
from __future__ import annotations

from atlas.alpha.case_membership import known_cases, resolve_case_id_for_ticker
from atlas.alpha.coverage import assess_coverage
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio_fit.service import PortfolioFitService
from atlas.alpha.stance.engine import compare_stance, determine_stance
from atlas.alpha.stance.models import Stance, StanceComparison
from atlas.alpha.watchlist.store import AlphaWatchlistStore

__all__ = ["StanceService"]


class StanceService:
    def __init__(
        self,
        composition_service: InvestmentCaseCompositionService,
        portfolio_fit_service: PortfolioFitService,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
    ) -> None:
        self._composition_service = composition_service
        self._portfolio_fit_service = portfolio_fit_service
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store
        # Request-scoped memoization (Decision Layer Runtime
        # Verification sprint) -- same pattern and justification as
        # `InvestmentCaseCompositionService._build_cache`: this dict is
        # as request-scoped as the instance itself, so caching by
        # `case_id` changes no observable behavior, only how many times
        # an identical assessment is repeated within one request.
        # Measured: `assess_for_case` was called up to 111 times for
        # one Case within a single `/decision-explanation/{id}` request.
        self._assess_for_case_cache: dict[str, Stance | None] = {}

    def _assess(self, case_id: str) -> Stance | None:
        composition = self._composition_service.build(case_id)
        if composition is None:
            return None
        fit = self._portfolio_fit_service.assess_for_case(case_id)
        coverage = assess_coverage(composition.canonical_analysis, is_thesis_stale=composition.is_thesis_stale)
        return determine_stance(
            composition.canonical_analysis,
            coverage=coverage,
            change_intelligence=composition.change_intelligence,
            portfolio_fit=fit,
        )

    def assess_for_case(self, case_id: str) -> Stance | None:
        """Investment Case's own Executive Summary area has a `case_id`
        in hand; this is the direct path (Deliverable 5)."""
        if case_id in self._assess_for_case_cache:
            return self._assess_for_case_cache[case_id]
        result = self._assess(case_id)
        self._assess_for_case_cache[case_id] = result
        return result

    def assess_for_ticker(self, ticker: str) -> Stance | None:
        case_id = resolve_case_id_for_ticker(ticker, self._portfolio_store, self._watchlist_store)
        if case_id is None:
            return None
        return self._assess(case_id)

    def compare(self, ticker_a: str, ticker_b: str) -> StanceComparison | None:
        """Deliverable 9 -- Compare Integration."""
        stance_a = self.assess_for_ticker(ticker_a)
        stance_b = self.assess_for_ticker(ticker_b)
        if stance_a is None or stance_b is None:
            return None
        return compare_stance(ticker_a, stance_a, ticker_b, stance_b)

    def assess_all_holdings(self) -> tuple[tuple[str, Stance], ...]:
        """Deliverable 6 -- Portfolio's own recommendation surface.
        Ticker paired with `Stance` (unlike `PortfolioFitService`'s own
        `PortfolioFitAssessment`, `Stance` carries no `ticker` field of
        its own -- see `models.py`'s own docstring for why: it is a
        pure judgment about one Case, agnostic of how a caller looked
        it up)."""
        portfolio_state = self._portfolio_store.get()
        if portfolio_state is None:
            return ()
        results = []
        for holding in portfolio_state.holdings:
            if holding.case_id is None:
                continue
            stance = self._assess(holding.case_id)
            if stance is not None:
                results.append((holding.ticker, stance))
        return tuple(results)

    def assess_for_candidates(self) -> tuple[tuple[str, Stance], ...]:
        """Deliverable 7 -- Discovery's own recommendation-aware
        candidate cards. Same "Watchlist Cases not already held" scope
        `PortfolioFitService.rank_candidates` already established."""
        portfolio_state = self._portfolio_store.get()
        held_tickers = {h.ticker for h in portfolio_state.holdings} if portfolio_state is not None else set()
        results = []
        for case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            if ticker is not None and ticker in held_tickers:
                continue
            stance = self._assess(case_id)
            if stance is not None and ticker is not None:
                results.append((ticker, stance))
        return tuple(results)
