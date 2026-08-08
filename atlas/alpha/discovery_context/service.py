"""Builds the canonical Discovery Context (ATLAS-018).

`DiscoveryContextService.build()` is now the *only* place Discovery's
context is assembled -- `atlas/ai/api/router.py` calls this instead of
calling `PortfolioIntelligenceService`/`CaseIntelligenceService`
directly, so there is exactly one composition point rather than the
ad-hoc inline assembly ATLAS-016/017 left in the router (see this
package's own `__init__.py`).
"""
from __future__ import annotations

import uuid

from atlas.alpha.case_intelligence.service import CaseIntelligenceService
from atlas.alpha.discovery_context.models import (
    DiscoveryContext,
    IdentityResolutionStatus,
    ResolvedIdentity,
)
from atlas.alpha.portfolio_intelligence.service import PortfolioIntelligenceService


class DiscoveryContextService:
    def __init__(
        self,
        portfolio_intelligence_service: PortfolioIntelligenceService,
        case_intelligence_service: CaseIntelligenceService,
    ) -> None:
        self._portfolio_intelligence_service = portfolio_intelligence_service
        self._case_intelligence_service = case_intelligence_service

    def build(self, case_id: str | None) -> DiscoveryContext:
        """`case_id`, when given, is resolved deterministically (Phase
        3) before any Case Intelligence content is included. A
        malformed or nonexistent `case_id` never raises and never
        silently falls back to "no case was requested" -- it resolves
        to `UNRESOLVED`, an honest, explicit disclosure of failed
        resolution, distinct from `NOT_REQUESTED`."""
        portfolio = self._portfolio_intelligence_service.build_report()

        if case_id is None:
            return DiscoveryContext(
                identity=ResolvedIdentity(
                    status=IdentityResolutionStatus.NOT_REQUESTED, case_id=None, ticker=None
                ),
                portfolio=portfolio,
                case=None,
            )

        if not _is_well_formed_case_id(case_id):
            return DiscoveryContext(
                identity=ResolvedIdentity(
                    status=IdentityResolutionStatus.UNRESOLVED, case_id=case_id, ticker=None
                ),
                portfolio=portfolio,
                case=None,
            )

        case_report = self._case_intelligence_service.build_report(case_id)
        if case_report is None:
            return DiscoveryContext(
                identity=ResolvedIdentity(
                    status=IdentityResolutionStatus.UNRESOLVED, case_id=case_id, ticker=None
                ),
                portfolio=portfolio,
                case=None,
            )

        return DiscoveryContext(
            identity=ResolvedIdentity(
                status=IdentityResolutionStatus.RESOLVED,
                case_id=case_id,
                ticker=case_report.current_view.ticker,
            ),
            portfolio=portfolio,
            case=case_report,
        )


def _is_well_formed_case_id(case_id: str) -> bool:
    """A structural check only -- whether the string can even be a real
    Case identity (`CaseId` wraps a `uuid.UUID`, `atlas/core/domain
    /case/value_objects.py`). Existence is confirmed separately, by
    `CaseIntelligenceService.build_report()` itself returning `None`."""
    try:
        uuid.UUID(case_id)
    except ValueError:
        return False
    return True
