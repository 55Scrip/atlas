"""Composition wiring for `DiscoveryContextService` (ATLAS-018).

No dedicated `api/` subpackage: unlike its sibling services
(`portfolio_intelligence`, `case_intelligence`), `DiscoveryContextService`
has no REST endpoint of its own -- it is injected directly into
`atlas/ai/api/router.py`'s existing `/discovery/chat` route. Reuses both
sibling services' own dependency providers rather than re-composing
their repositories/stores here.
"""
from __future__ import annotations

from fastapi import Depends

from atlas.alpha.case_intelligence.api.dependencies import get_case_intelligence_service
from atlas.alpha.case_intelligence.service import CaseIntelligenceService
from atlas.alpha.discovery_context.service import DiscoveryContextService
from atlas.alpha.portfolio_intelligence.api.dependencies import get_portfolio_intelligence_service
from atlas.alpha.portfolio_intelligence.service import PortfolioIntelligenceService


def get_discovery_context_service(
    portfolio_intelligence_service: PortfolioIntelligenceService = Depends(get_portfolio_intelligence_service),
    case_intelligence_service: CaseIntelligenceService = Depends(get_case_intelligence_service),
) -> DiscoveryContextService:
    return DiscoveryContextService(
        portfolio_intelligence_service=portfolio_intelligence_service,
        case_intelligence_service=case_intelligence_service,
    )
