"""Composition wiring for the Discovery candidate universe.

Every collaborator is resolved through the canonical provider its own
package already exposes, so this endpoint shares the request-scoped
composition service with everything else in the request -- and, more
importantly, inherits their provider-free character rather than
re-deriving it.
"""
from __future__ import annotations

from fastapi import Depends

from atlas.alpha.case_instrument.dependencies import get_case_instrument_binding_repository
from atlas.alpha.case_instrument.repository import CaseInstrumentBindingRepository
from atlas.alpha.discovery_candidates.service import DiscoveryCandidateService
from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio_fit.api.dependencies import get_portfolio_fit_service
from atlas.alpha.portfolio_fit.service import PortfolioFitService
from atlas.alpha.stance.api.dependencies import get_stance_service
from atlas.alpha.stance.service import StanceService
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore


def get_discovery_candidate_service(
    binding_repository: CaseInstrumentBindingRepository = Depends(get_case_instrument_binding_repository),
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
    composition_service: InvestmentCaseCompositionService = Depends(get_investment_case_composition_service),
    portfolio_fit_service: PortfolioFitService = Depends(get_portfolio_fit_service),
    stance_service: StanceService = Depends(get_stance_service),
) -> DiscoveryCandidateService:
    return DiscoveryCandidateService(
        binding_repository,
        portfolio_store,
        watchlist_store,
        composition_service,
        portfolio_fit_service,
        stance_service,
    )
