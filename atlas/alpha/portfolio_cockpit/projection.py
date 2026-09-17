"""Pure projection functions from `CanonicalAnalysis` onto Portfolio
Cockpit's own compact per-holding types (ATLAS-028 Phase 4/6/7/8).
Every function here narrows an existing canonical value; none
recomputes, reinterprets, or rescales one.

`risk_projection` itself now lives in `atlas.analysis_engine.risk
.projection` (re-exported below so every existing import site in this
package stays unchanged) -- relocated so `atlas.alpha.investment_case`
can reuse the identical function for its own Atlas View scorecard
without a package cycle; see that module's own docstring.
"""
from __future__ import annotations

from atlas.analysis_engine.business_contracts import BusinessCategory
from atlas.analysis_engine.models import CanonicalAnalysis
from atlas.analysis_engine.risk.models import RiskFinding
from atlas.analysis_engine.risk.projection import risk_projection
from atlas.analysis_engine.valuation.contracts import ValuationMethodKind
from atlas.analysis_engine.valuation.models import ValuationFinding

from atlas.alpha.portfolio_cockpit.models import (
    BusinessCategoryFinding,
    BusinessSummary,
    ForwardEvidenceSummary,
)

__all__ = [
    "business_summary",
    "business_categories",
    "forward_evidence",
    "valuation_finding",
    "risk_projection",
]


def business_summary(business_analysis) -> BusinessSummary:
    """Growth and Capital Allocation only -- see `BusinessSummary`'s own
    docstring for why the other four categories are deliberately
    absent, not padded out."""
    growth = next(f for f in business_analysis.findings if f.kind is BusinessCategory.GROWTH)
    capital_allocation = next(
        f for f in business_analysis.findings if f.kind is BusinessCategory.CAPITAL_ALLOCATION
    )
    return BusinessSummary(growth=growth.status, capital_allocation=capital_allocation.status)


def business_categories(business_analysis) -> tuple[BusinessCategoryFinding, ...]:
    """The whole already-computed category vector, in the engine's own
    order -- see `BusinessCategoryFinding`'s own docstring for why
    Portfolio needs the full vector and not just the two categories
    `business_summary` above narrows to.

    A pure narrowing of findings already in hand: each finding's own
    `kind` and `status`, nothing averaged, scored or reordered. Which
    categories count toward a Company rating, and which are excluded for
    having no real verdict, stays where it already is -- one shared
    presentation rule, applied identically by Portfolio and by the
    Investment Case."""
    return tuple(
        BusinessCategoryFinding(kind=f.kind.value, status=f.status) for f in business_analysis.findings
    )


def forward_evidence(recommendation) -> ForwardEvidenceSummary | None:
    """Counts of the verified forward evidence this holding's own
    recommendation reasoning already carries -- see
    `ForwardEvidenceSummary`'s docstring.

    `recommendation` is the `RecommendationGateResult` the canonical
    analysis already holds. Both of its outcomes may carry reasoning (a
    directional one always does; a withheld one does when it is a
    `RecommendationWithheldWithReasoning`), and either may legitimately
    carry none -- read defensively rather than asserting a shape, the
    same way the frontend's own reasoning contract reads every optional
    collection with `.get(...)`.

    Nothing about the forward-evidence pipeline is invoked here. This
    counts a result that `atlas.analysis_engine.forward_context` already
    produced and placed on the reasoning, after the direction was
    already chosen -- so reading it can no more influence a
    recommendation here than it can there."""
    outcome = getattr(recommendation, "recommendation", None)
    reasoning = getattr(outcome, "reasoning", None)
    context = getattr(reasoning, "forward_context", None)
    if context is None:
        return None
    return ForwardEvidenceSummary(
        guidance_count=len(context.guidance),
        contracted_volume_count=len(context.contracted_volume),
    )


def valuation_finding(valuation_engine) -> ValuationFinding:
    """The real `FCF_YIELD_RELATIVE` finding, reused verbatim -- see
    `PortfolioHoldingAnalysis.valuation`'s own docstring for why this
    one method already is the honest Portfolio-level projection."""
    return next(f for f in valuation_engine.findings if f.kind is ValuationMethodKind.FCF_YIELD_RELATIVE)


def full_risk_vector(risk_analysis) -> tuple[RiskFinding, ...]:
    """The complete, untouched Risk vector -- reused verbatim, never
    reshaped. A thin passthrough named for symmetry with the other
    projection functions in this module."""
    return risk_analysis.findings
