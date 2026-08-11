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

from atlas.alpha.portfolio_cockpit.models import BusinessSummary

__all__ = ["business_summary", "valuation_finding", "risk_projection"]


def business_summary(business_analysis) -> BusinessSummary:
    """Growth and Capital Allocation only -- see `BusinessSummary`'s own
    docstring for why the other four categories are deliberately
    absent, not padded out."""
    growth = next(f for f in business_analysis.findings if f.kind is BusinessCategory.GROWTH)
    capital_allocation = next(
        f for f in business_analysis.findings if f.kind is BusinessCategory.CAPITAL_ALLOCATION
    )
    return BusinessSummary(growth=growth.status, capital_allocation=capital_allocation.status)


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
