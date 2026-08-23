"""Orchestration for the Materiality Engine -- the only part of this
package that performs I/O. Composes `atlas.alpha.investment_case
.InvestmentCaseCompositionService`, `atlas.alpha.portfolio_fit
.PortfolioFitService`, `atlas.alpha.coverage.assess_coverage`, and
`atlas.alpha.stance.determine_stance` (all unmodified) -- mirrors
`atlas.alpha.explainability.service.ExplainabilityService`'s own exact
shape one layer up, the same "each Alpha service independently
composes for its own purpose" cost tradeoff `atlas.alpha
.daily_brief_agenda.service`'s own module docstring already accepts
and documents.
"""
from __future__ import annotations

from atlas.alpha.case_membership import resolve_case_id_for_ticker
from atlas.alpha.coverage import assess_coverage
from atlas.alpha.explainability import explain
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.materiality.engine import assess_materiality
from atlas.alpha.materiality.models import MaterialityAssessment
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio_fit.service import PortfolioFitService
from atlas.alpha.stance.engine import determine_stance
from atlas.alpha.watchlist.store import AlphaWatchlistStore

__all__ = ["MaterialityService"]


class MaterialityService:
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

    def _assess(self, case_id: str) -> MaterialityAssessment | None:
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
        explanation = explain(stance, coverage)
        return assess_materiality(explanation)

    def assess_for_case(self, case_id: str) -> MaterialityAssessment | None:
        return self._assess(case_id)

    def assess_for_ticker(self, ticker: str) -> MaterialityAssessment | None:
        case_id = resolve_case_id_for_ticker(ticker, self._portfolio_store, self._watchlist_store)
        if case_id is None:
            return None
        return self._assess(case_id)
