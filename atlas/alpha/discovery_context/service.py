"""Builds the canonical Discovery Context (ATLAS-018; migrated to the
canonical Investment Case composition path in ATLAS-030).

`DiscoveryContextService.build()` is now the *only* place Discovery's
context is assembled -- `atlas/ai/api/router.py` calls this instead of
calling `PortfolioIntelligenceService`/`InvestmentCaseCompositionService`
directly, so there is exactly one composition point rather than the
ad-hoc inline assembly ATLAS-016/017 left in the router (see this
package's own `__init__.py`).

ATLAS-030: the per-Case half of this context is now built from
`InvestmentCaseCompositionService.build()` -- the same canonical
composition Portfolio Cockpit and the Investment Case API already
consume -- via `case_projection.build_discovery_case_context`, never a
second `decision_engine.run_pipeline` call. `case_intelligence` is no
longer a dependency of this service.
"""
from __future__ import annotations

import uuid

from atlas.alpha.discovery_context.case_projection import build_discovery_case_context
from atlas.alpha.discovery_context.models import (
    DiscoveryContext,
    IdentityResolutionStatus,
    ResolvedIdentity,
)
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.monitoring.service import MonitoringService
from atlas.alpha.portfolio_intelligence.service import PortfolioIntelligenceService
from atlas.alpha.portfolio_status.service import PortfolioStatusService


class DiscoveryContextService:
    def __init__(
        self,
        portfolio_intelligence_service: PortfolioIntelligenceService,
        investment_case_composition_service: InvestmentCaseCompositionService,
        portfolio_status_service: PortfolioStatusService,
        monitoring_service: MonitoringService,
    ) -> None:
        self._portfolio_intelligence_service = portfolio_intelligence_service
        self._investment_case_composition_service = investment_case_composition_service
        self._portfolio_status_service = portfolio_status_service
        self._monitoring_service = monitoring_service

    def build(self, case_id: str | None) -> DiscoveryContext:
        """`case_id`, when given, is resolved deterministically (Phase
        3) before any per-Case content is included. A malformed or
        nonexistent `case_id` never raises and never silently falls
        back to "no case was requested" -- it resolves to `UNRESOLVED`,
        an honest, explicit disclosure of failed resolution, distinct
        from `NOT_REQUESTED`."""
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

        composition = self._investment_case_composition_service.build(case_id)
        if composition is None:
            return DiscoveryContext(
                identity=ResolvedIdentity(
                    status=IdentityResolutionStatus.UNRESOLVED, case_id=case_id, ticker=None
                ),
                portfolio=portfolio,
                case=None,
            )

        status_report = self._portfolio_status_service.build_report()
        # Sprint 8, Deliverable 17 -- Companion's own honest freshness
        # disclosure, computed via the same cheap pre-pass `run()`
        # itself uses (see `MonitoringService._signal_maps`), never a
        # second monitoring run triggered by a chat message.
        monitoring_pending = self._monitoring_service.freshness_for_case(case_id).is_pending
        case_context = build_discovery_case_context(composition, status_report, monitoring_pending=monitoring_pending)

        return DiscoveryContext(
            identity=ResolvedIdentity(
                status=IdentityResolutionStatus.RESOLVED,
                case_id=case_id,
                ticker=case_context.ticker,
            ),
            portfolio=portfolio,
            case=case_context,
        )


def _is_well_formed_case_id(case_id: str) -> bool:
    """A structural check only -- whether the string can even be a real
    Case identity (`CaseId` wraps a `uuid.UUID`, `atlas/core/domain
    /case/value_objects.py`). Existence is confirmed separately, by
    `InvestmentCaseCompositionService.build()` itself returning `None`."""
    try:
        uuid.UUID(case_id)
    except ValueError:
        return False
    return True
