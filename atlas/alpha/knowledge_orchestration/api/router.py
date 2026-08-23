"""REST controller for the Knowledge Orchestration Engine.

`POST /orchestration/{ticker}` is a new, additive, explicit operation
-- mirrors `atlas.alpha.ingestion.api.router`'s own `POST /ingestion
/refresh/{ticker}` precedent exactly (a real, explicit, human- or
integration-triggered operation, never invoked automatically by any
existing trigger). Plans against the Case's own **current** Knowledge
Coverage (computed the identical way `atlas.alpha.investment_case.api
.router.get_investment_case_analysis` already does -- `composition
_service.build()` -> `assess_evidence_quality()` -> `assess_knowledge
_coverage()`, all three reused verbatim), executes the plan, and
returns what happened. Never touches `MonitoringService`,
`InvestmentCaseComposition`, `atlas.alpha.coverage`, or the Decision
Layer -- see `orchestrator.py`'s own module docstring for why
`should_reanalyze` is a recommendation only, not an action taken here.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.alpha.case_membership import resolve_case_id_for_ticker
from atlas.alpha.evidence_quality import assess_evidence_quality
from atlas.alpha.knowledge_coverage import assess_knowledge_coverage
from atlas.alpha.knowledge_orchestration.api.dependencies import (
    get_business_record_repository,
    get_canonical_security_identity_gate,
    get_default_business_data_providers_by_id,
)
from atlas.alpha.knowledge_orchestration.api.schemas import OrchestrationOutcomeView
from atlas.alpha.knowledge_orchestration.orchestrator import run_orchestrated_acquisition
from atlas.alpha.knowledge_orchestration.planner import plan_acquisition
from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.analysis_engine.business_data.providers import BusinessDataProvider
from atlas.analysis_engine.business_data.versioning import latest_versions

router = APIRouter(prefix="/orchestration", tags=["knowledge-orchestration"])


@router.post("/{ticker}", response_model=OrchestrationOutcomeView)
def orchestrate_acquisition(
    ticker: str,
    composition_service: InvestmentCaseCompositionService = Depends(get_investment_case_composition_service),
    providers_by_id: dict[str, BusinessDataProvider] = Depends(get_default_business_data_providers_by_id),
    business_record_repository: SqlAlchemyBusinessRecordRepository = Depends(get_business_record_repository),
    identity_gate: CanonicalSecurityIdentityGate = Depends(get_canonical_security_identity_gate),
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
) -> OrchestrationOutcomeView:
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

    plan = plan_acquisition(coverage)
    outcome = run_orchestrated_acquisition(
        normalized, plan, coverage, providers_by_id, business_record_repository, identity_gate=identity_gate
    )
    return OrchestrationOutcomeView.from_domain(normalized, case_id, outcome)
