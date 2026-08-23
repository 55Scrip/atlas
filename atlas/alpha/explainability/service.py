"""Orchestration for the Explainability Engine -- the only part of this
package that performs I/O. Composes `atlas.alpha.investment_case
.InvestmentCaseCompositionService`, `atlas.alpha.portfolio_fit
.PortfolioFitService`, and `atlas.alpha.coverage.assess_coverage`/
`atlas.alpha.stance.determine_stance` (all unmodified), mirroring
`atlas.alpha.stance.service.StanceService`'s own exact shape one layer
up -- the same "each Alpha service independently composes for its own
purpose" cost tradeoff `atlas.alpha.daily_brief_agenda.service`'s own
module docstring already accepts and documents.
"""
from __future__ import annotations

from atlas.alpha.case_membership import resolve_case_id_for_ticker
from atlas.alpha.coverage import assess_coverage
from atlas.alpha.explainability.engine import compare_evidence, explain
from atlas.alpha.explainability.models import ComparisonEvidence, Explanation
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio_fit.service import PortfolioFitService
from atlas.alpha.stance.engine import determine_stance
from atlas.alpha.watchlist.store import AlphaWatchlistStore

__all__ = ["ExplainabilityService"]


class ExplainabilityService:
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

    def _explain(self, case_id: str) -> Explanation | None:
        composition = self._composition_service.build(case_id)
        if composition is None:
            return None
        fit = self._portfolio_fit_service.assess_for_case(case_id)
        coverage = assess_coverage(composition.canonical_analysis, is_thesis_stale=composition.is_thesis_stale)
        stance = determine_stance(
            composition.canonical_analysis,
            coverage=coverage,
            change_intelligence=composition.change_intelligence,
            portfolio_fit=fit,
        )
        return explain(stance, coverage)

    def explain_for_case(self, case_id: str) -> Explanation | None:
        return self._explain(case_id)

    def explain_for_ticker(self, ticker: str) -> Explanation | None:
        case_id = resolve_case_id_for_ticker(ticker, self._portfolio_store, self._watchlist_store)
        if case_id is None:
            return None
        return self._explain(case_id)

    def compare(self, ticker_a: str, ticker_b: str) -> ComparisonEvidence | None:
        """Deliverable 7 -- Compare Integration."""
        explanation_a = self.explain_for_ticker(ticker_a)
        explanation_b = self.explain_for_ticker(ticker_b)
        if explanation_a is None or explanation_b is None:
            return None
        return compare_evidence(explanation_a, explanation_b)
