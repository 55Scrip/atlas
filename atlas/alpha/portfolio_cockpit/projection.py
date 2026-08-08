"""Pure projection functions from `CanonicalAnalysis` onto Portfolio
Cockpit's own compact per-holding types (ATLAS-028 Phase 4/6/7/8).
Every function here narrows an existing canonical value; none
recomputes, reinterprets, or rescales one.
"""
from __future__ import annotations

from atlas.analysis_engine.business_contracts import BusinessCategory
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.models import CanonicalAnalysis
from atlas.analysis_engine.risk.contracts import RiskStatus
from atlas.analysis_engine.risk.models import EVALUATED_RISK_CATEGORIES, RiskFinding
from atlas.analysis_engine.valuation.contracts import ValuationMethodKind
from atlas.analysis_engine.valuation.models import ValuationFinding

from atlas.alpha.portfolio_cockpit.models import BusinessSummary, RiskProjection

__all__ = ["business_summary", "valuation_finding", "risk_projection"]

#: Fixed, deterministic tie-break order for `risk_projection` -- the
#: canonical `RiskCategory` enum's own declared order, filtered to the
#: categories this sprint actually evaluates. Not invented for this
#: package: this is simply "the order the taxonomy itself was written
#: in," the same non-arbitrary-ordering discipline every other
#: first-match-wins rule table in this codebase already follows.
_TIE_BREAK_ORDER = tuple(category for category in RiskCategory if category in EVALUATED_RISK_CATEGORIES)

#: Higher index = higher severity. `NOT_EVALUATED` never appears
#: (reserved, never constructed by any real evaluator) but is included
#: so this mapping is total over the whole `RiskStatus` enum, never a
#: `KeyError` waiting to happen.
_SEVERITY_ORDER = (
    RiskStatus.NOT_EVALUATED,
    RiskStatus.INSUFFICIENT_INPUT,
    RiskStatus.LOW,
    RiskStatus.MODERATE,
    RiskStatus.HIGH,
)


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


def risk_projection(risk_analysis) -> RiskProjection:
    """The single highest-severity category among
    `EVALUATED_RISK_CATEGORIES`, deterministic ties broken by
    `_TIE_BREAK_ORDER`. Never an average, never a weighted combination
    -- exactly one category's own real status, chosen by a fixed rule.

    Walks `_TIE_BREAK_ORDER` (the canonical taxonomy's own declared
    order) and keeps the running highest-severity category seen so far,
    strictly greater-than only -- so the *first* category in declared
    order among any tied-severity group is the one kept, exactly the
    "ties broken by declared order" rule this function documents.
    """
    findings_by_category = {f.category: f for f in risk_analysis.findings}
    highest = findings_by_category[_TIE_BREAK_ORDER[0]]
    for category in _TIE_BREAK_ORDER[1:]:
        candidate = findings_by_category[category]
        if _SEVERITY_ORDER.index(candidate.status) > _SEVERITY_ORDER.index(highest.status):
            highest = candidate
    return RiskProjection(category=highest.category, status=highest.status)


def full_risk_vector(risk_analysis) -> tuple[RiskFinding, ...]:
    """The complete, untouched Risk vector -- reused verbatim, never
    reshaped. A thin passthrough named for symmetry with the other
    projection functions in this module."""
    return risk_analysis.findings
