"""Composition wiring for the Evidence Quality API. Same "each Alpha
package wires its own dependencies" convention `atlas.alpha.stance.api
.dependencies`'s own module docstring documents.
"""
from __future__ import annotations

from fastapi import Depends

from atlas.alpha.business_data_refresh.api.dependencies import get_business_record_repository
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.evidence_quality.service import EvidenceQualityService
from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore

__all__ = ["get_evidence_quality_service"]


def get_evidence_quality_service(
    composition_service: InvestmentCaseCompositionService = Depends(get_investment_case_composition_service),
    business_record_repository: SqlAlchemyBusinessRecordRepository = Depends(get_business_record_repository),
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
) -> EvidenceQualityService:
    return EvidenceQualityService(
        composition_service=composition_service,
        business_record_repository=business_record_repository,
        portfolio_store=portfolio_store,
        watchlist_store=watchlist_store,
    )
