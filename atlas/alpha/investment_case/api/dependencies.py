"""Composition wiring for the canonical Investment Case API (ATLAS-029).

Same shared-engine pattern every Alpha API dependencies module uses: one
physical `atlas.db` file, read-only providers reused directly from
Case's, Decision's, Observation's, Evidence's, and Outcome's own
established composition modules -- no new repository implementation, no
new table.

Deliberately independent of `atlas.alpha.portfolio_cockpit.api
.dependencies`'s own `get_investment_case_composition_service` (which
wires the identical service): `portfolio_cockpit` already depends on
`investment_case` at the service layer, so importing back from here
would create a package-level cycle. Both providers wire the same
`InvestmentCaseCompositionService` constructor the same way -- this is
the same "each Alpha package's own composition module, even when
providers coincide" convention `case_intelligence`/`portfolio_status`
already established independently of each other.
"""
from __future__ import annotations

from fastapi import Depends

from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store, get_alpha_trade_log_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.core.domain.case.repository import CaseRepository
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.evidence.repository import EvidenceRepository
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.domain.outcome.repository import OutcomeRepository
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
) -> InvestmentCaseCompositionService:
    return InvestmentCaseCompositionService(
        case_repository=case_repository,
        decision_repository=decision_repository,
        observation_repository=observation_repository,
        evidence_repository=evidence_repository,
        outcome_repository=outcome_repository,
        portfolio_store=portfolio_store,
        trade_log_store=trade_log_store,
    )
