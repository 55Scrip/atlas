"""Portfolio Cockpit domain models (ATLAS-028 Phase 4). See this
package's own `__init__.py` for the projection/reuse rationale.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.alpha.portfolio.models import ReconciliationStatus
from atlas.alpha.portfolio_status.models import PortfolioSummaryMetrics
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.conviction import ConvictionAssessment, ConvictionLevel
from atlas.analysis_engine.risk.contracts import RiskStatus
from atlas.analysis_engine.risk.models import RiskFinding
from atlas.analysis_engine.valuation.contracts import ValuationStatus
from atlas.analysis_engine.valuation.models import ValuationFinding
from atlas.decision_engine.contracts import EvidenceCoverageLevel

from atlas.alpha.portfolio_cockpit.contracts import AttentionReasonKind, ReviewPriority

__all__ = [
    "RiskProjection",
    "BusinessSummary",
    "HoldingAttention",
    "PortfolioHoldingAnalysis",
    "UnresolvedHolding",
    "ConvictionLevelCount",
    "ValuationStatusCount",
    "PortfolioCockpitReport",
]


@dataclass(frozen=True)
class RiskProjection:
    """The single highest-severity `RiskCategory` among
    `EVALUATED_RISK_CATEGORIES`, for compact display only -- a
    projection, explicitly never an aggregate score (Phase 8). Severity
    order: `HIGH > MODERATE > LOW > INSUFFICIENT_INPUT`. Ties are broken
    by `RiskCategory`'s own declared enum order (never an invented
    priority) -- deterministic, not arbitrary."""

    category: RiskCategory
    status: RiskStatus


@dataclass(frozen=True)
class BusinessSummary:
    """Growth and Capital Allocation only -- the two `BusinessCategory`
    members this codebase can currently evaluate for real (ATLAS-023).
    Deliberately not a synthesized six-category aggregate; the other
    four categories are honestly omitted rather than padded out with a
    constant `INSUFFICIENT_INPUT` that would imply four more real
    checks ran (Phase 7)."""

    growth: BusinessCategoryStatus
    capital_allocation: BusinessCategoryStatus


@dataclass(frozen=True)
class HoldingAttention:
    """`reasons` names every rule that fired, not only the one deciding
    `priority` -- the same "always name every applicable code" style
    `ConvictionAssessment.reasons` already established."""

    priority: ReviewPriority
    reasons: tuple[AttentionReasonKind, ...]


@dataclass(frozen=True)
class PortfolioHoldingAnalysis:
    """One holding's canonical, portfolio-scoped summary -- a
    projection of `CanonicalAnalysis`, never a duplicate of it. The
    full object remains reachable through `case_id`'s own Investment
    Case, one click away."""

    ticker: str
    case_id: str
    weight_percent: float
    value_absolute: float | None
    reconciliation_status: ReconciliationStatus
    conviction: ConvictionAssessment
    valuation: ValuationFinding
    """The real `FCF_YIELD_RELATIVE` finding, reused verbatim -- not a
    bare status string. The other three `ValuationMethodKind` members
    are always structurally `INSUFFICIENT_INPUT` this sprint (see
    `atlas.analysis_engine.valuation.scenarios`), so this one method
    already *is* the honest Portfolio-level projection."""
    business: BusinessSummary
    risk_projection: RiskProjection
    risk_findings: tuple[RiskFinding, ...]
    """The complete, untouched Risk vector (all `EVALUATED_RISK_CATEGORIES`
    members) -- reused verbatim from `risk_analysis.findings`, exposed
    for a detail/expand view alongside `risk_projection`'s compact badge."""
    confidence: EvidenceCoverageLevel
    is_thesis_stale: bool
    attention: HoldingAttention


@dataclass(frozen=True)
class UnresolvedHolding:
    """A holding whose canonical analysis could not be composed --
    either it has no `case_id` at all, or that `case_id` did not
    resolve to a real Case. An honest, explicit operational state
    (Phase 22/33), never silently dropped and never filled with
    fabricated analytical values."""

    ticker: str
    case_id: str | None


@dataclass(frozen=True)
class ConvictionLevelCount:
    level: ConvictionLevel
    count: int


@dataclass(frozen=True)
class ValuationStatusCount:
    status: ValuationStatus
    count: int


@dataclass(frozen=True)
class PortfolioCockpitReport:
    """The canonical Portfolio Cockpit view. `holdings` covers every
    holding whose analysis composed successfully; `unresolved_holdings`
    honestly names the rest. `summary` is `PortfolioStatusService`'s
    own `PortfolioSummaryMetrics`, reused by reference -- concentration,
    unallocated capital, and holdings count are never recomputed here.

    `conviction_distribution`/`valuation_distribution` are purely
    descriptive counts (Phase 17/18) -- "N holdings at MODERATE
    conviction," never a single averaged "portfolio conviction" or
    "portfolio valuation." No field on this object is a numeric score.
    """

    exists: bool
    holdings: tuple[PortfolioHoldingAnalysis, ...]
    unresolved_holdings: tuple[UnresolvedHolding, ...]
    summary: PortfolioSummaryMetrics | None
    conviction_distribution: tuple[ConvictionLevelCount, ...]
    valuation_distribution: tuple[ValuationStatusCount, ...]
    priority_review_count: int
    generated_at: datetime
