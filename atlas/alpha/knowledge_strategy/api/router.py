"""REST controller for the Knowledge Strategy Engine.

`GET /research-strategy/{ticker}` is a new, additive, read-only
operation: reports what Atlas would research next and why, without
running any provider -- the "Evaluate Decision Impact -> Prioritize
Research" steps of the sprint's own Expected User Experience, visible
independent of actually triggering `POST /orchestration/{ticker}`.
Computes the Case's own **current** Knowledge Coverage the identical
way `atlas.alpha.knowledge_orchestration.api.router.orchestrate_
acquisition` already does (`composition_service.build()` ->
`assess_evidence_quality()` -> `assess_knowledge_coverage()`, all three
reused verbatim) -- no second coverage computation path.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from atlas.alpha.case_membership import resolve_case_id_for_ticker
from atlas.alpha.evidence_quality import assess_evidence_quality
from atlas.alpha.knowledge_coverage import assess_knowledge_coverage
from atlas.alpha.knowledge_strategy.api.schemas import ResearchStrategyView
from atlas.alpha.knowledge_strategy.completion import assess_research_completion
from atlas.alpha.knowledge_strategy.evaluation import assess_knowledge_gaps
from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.analysis_engine.business_data.versioning import latest_versions
from atlas.alpha.business_data_refresh.api.dependencies import get_business_record_repository
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository

router = APIRouter(prefix="/research-strategy", tags=["knowledge-strategy"])


@router.get("/{ticker}", response_model=ResearchStrategyView)
def get_research_strategy(
    ticker: str,
    composition_service: InvestmentCaseCompositionService = Depends(get_investment_case_composition_service),
    business_record_repository: SqlAlchemyBusinessRecordRepository = Depends(get_business_record_repository),
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
) -> ResearchStrategyView:
    normalized = ticker.strip().upper()
    case_id = resolve_case_id_for_ticker(normalized, portfolio_store, watchlist_store)
    if case_id is None:
        raise HTTPException(
            status_code=404,
            detail=f"No Case exists for {normalized!r} yet -- add it to a Portfolio or Watchlist first",
        )

    composition = composition_service.build(case_id)
    if composition is None:
        raise HTTPException(status_code=404, detail="Case not found")

    records = latest_versions(business_record_repository.get_by_company(normalized))
    evidence_quality = assess_evidence_quality(
        records, composition.business_facts, composition.market_facts, composition.canonical_analysis,
        evaluated_at=composition.generated_at,
    )
    coverage = assess_knowledge_coverage(composition, evidence_quality, records, evaluated_at=composition.generated_at)

    gaps = assess_knowledge_gaps(coverage)
    completion = assess_research_completion(gaps, research_was_performed=False, any_decision_critical_step_blocked=False)
    return ResearchStrategyView.from_domain(normalized, case_id, gaps, completion)
