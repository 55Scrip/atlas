"""Composition wiring for `DiscoveryContextService` (ATLAS-018; migrated
to the canonical Investment Case composition path in ATLAS-030).

No dedicated `api/` subpackage: unlike its sibling services
(`portfolio_intelligence`, `investment_case`), `DiscoveryContextService`
has no REST endpoint of its own -- it is injected directly into
`atlas/ai/api/router.py`'s existing `/discovery/chat` route. Reuses
`portfolio_intelligence`'s own dependency provider, `investment_case`'s
own `InvestmentCaseCompositionService` wiring (mirroring the identical
pattern already established independently in
`atlas.alpha.portfolio_cockpit.api.dependencies` and
`atlas.alpha.investment_case.api.dependencies` -- see either module's
own docstring for why each Alpha package wires this service itself
rather than importing another package's provider), and
`portfolio_status`'s own provider -- no new repository implementation,
no new table.
"""
from __future__ import annotations

from fastapi import Depends

from atlas.alpha.discovery_context.service import DiscoveryContextService
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store, get_alpha_trade_log_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio_intelligence.api.dependencies import get_portfolio_intelligence_service
from atlas.alpha.portfolio_intelligence.service import PortfolioIntelligenceService
from atlas.alpha.portfolio_status.api.dependencies import get_portfolio_status_service
from atlas.alpha.portfolio_status.service import PortfolioStatusService
from atlas.core.domain.case.repository import CaseRepository
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.evidence.repository import EvidenceRepository
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.domain.outcome.repository import OutcomeRepository
from atlas.alpha.business_data_refresh.api.dependencies import get_business_record_repository
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
from atlas.core.infrastructure.api.evidence.dependencies import get_evidence_repository
from atlas.core.infrastructure.api.knowledge_reference.dependencies import get_outcome_repository
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository


def get_investment_case_composition_service(
    case_repository: CaseRepository = Depends(get_case_repository),
    decision_repository: DecisionRepository = Depends(get_decision_repository),
    observation_repository: ObservationRepository = Depends(get_observation_repository),
    evidence_repository: EvidenceRepository = Depends(get_evidence_repository),
    outcome_repository: OutcomeRepository = Depends(get_outcome_repository),
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    trade_log_store: AlphaTradeLogStore = Depends(get_alpha_trade_log_store),
    business_record_repository: SqlAlchemyBusinessRecordRepository = Depends(get_business_record_repository),
) -> InvestmentCaseCompositionService:
    return InvestmentCaseCompositionService(
        case_repository=case_repository,
        decision_repository=decision_repository,
        observation_repository=observation_repository,
        evidence_repository=evidence_repository,
        outcome_repository=outcome_repository,
        portfolio_store=portfolio_store,
        trade_log_store=trade_log_store,
        business_record_repository=business_record_repository,
    )


def get_discovery_context_service(
    portfolio_intelligence_service: PortfolioIntelligenceService = Depends(get_portfolio_intelligence_service),
    investment_case_composition_service: InvestmentCaseCompositionService = Depends(
        get_investment_case_composition_service
    ),
    portfolio_status_service: PortfolioStatusService = Depends(get_portfolio_status_service),
) -> DiscoveryContextService:
    return DiscoveryContextService(
        portfolio_intelligence_service=portfolio_intelligence_service,
        investment_case_composition_service=investment_case_composition_service,
        portfolio_status_service=portfolio_status_service,
    )
