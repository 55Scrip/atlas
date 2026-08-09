"""Data model for the canonical Discovery Context (ATLAS-018)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.alpha.discovery_context.case_projection import DiscoveryCaseContext
from atlas.alpha.portfolio_intelligence.models import PortfolioIntelligenceReport

__all__ = ["IdentityResolutionStatus", "ResolvedIdentity", "DiscoveryContext"]


class IdentityResolutionStatus(str, Enum):
    """Phase 3: "Discovery must never guess which company is being
    discussed... only after deterministic identity resolution may the
    request continue."

    `NOT_REQUESTED` is not a failure -- most Discovery conversations are
    genuinely portfolio-wide, with no single Case in question. Only
    `UNRESOLVED` represents an actual resolution failure (a `caseId`
    was given but does not correspond to any real, existing Case) --
    the two are kept distinct so the render layer can state plainly
    "Atlas could not confirm which Investment Case this is" only when
    resolution was actually attempted and failed, never for an ordinary
    portfolio-wide question.
    """

    NOT_REQUESTED = "not_requested"
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class ResolvedIdentity:
    """The deterministic identity result for one Discovery request.

    Deliberately two fields, not three: `ticker` and `case_id` are the
    only instrument-identity concepts that exist anywhere in this
    codebase's real domain model (`AlphaHolding.ticker`,
    `AlphaHolding.case_id` -- see `atlas/alpha/portfolio/models.py`).
    An "InstrumentId" is explicitly NOT included here, per the "never
    invent" principle: no instrument-identity aggregate, registry
    entity, or id type exists in this codebase today (confirmed by
    repository investigation before this sprint -- the closest thing,
    `frontend/src/portfolio-import/instrumentRegistry.ts`, is a
    client-side name-to-ticker lookup table with no id concept of its
    own). Adding a fabricated `instrument_id` field here would violate
    this sprint's own "do not hallucinate" instruction at the type
    level, not just in generated text.

    `ticker` is `None` whenever `case_id` resolves to a real Case that
    has no linked Alpha holding yet (a genuine, valid state -- see
    `DiscoveryCaseContext.held`) -- distinct from `UNRESOLVED`, where
    `case_id` itself could not be confirmed to exist at all.
    """

    status: IdentityResolutionStatus
    case_id: str | None
    ticker: str | None


@dataclass(frozen=True)
class DiscoveryContext:
    """The single canonical object Discovery consumes (Phase 2).

    `portfolio` is always present -- `PortfolioIntelligenceReport`
    itself already carries `exists: bool` for "no portfolio established
    yet," the same honest-disclosure shape this sprint reuses rather
    than wrapping in a second `Optional`. `case` is `None` whenever
    `identity.status is not IdentityResolutionStatus.RESOLVED`.

    ATLAS-030: `case` is now a `DiscoveryCaseContext`, built exclusively
    from `InvestmentCaseCompositionService.build()`'s
    `InvestmentCaseComposition` -- the same canonical composition
    Portfolio Cockpit and the Investment Case API already consume --
    rather than the legacy `case_intelligence.CaseIntelligenceReport`.
    """

    identity: ResolvedIdentity
    portfolio: PortfolioIntelligenceReport
    case: DiscoveryCaseContext | None
