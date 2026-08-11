"""Pure projection from a full `RiskAnalysisResult` onto a single,
compact `RiskProjection` -- for consumers that need one representative
risk category/status (a table cell, a scorecard dot), never the
complete four-category vector.

Originally `atlas.alpha.portfolio_cockpit.projection.risk_projection`
(ATLAS-028 Phase 8); relocated to `analysis_engine.risk` alongside
`RiskProjection` itself so both `atlas.alpha.portfolio_cockpit` and
`atlas.alpha.investment_case` can reuse the identical function -- see
`RiskProjection`'s own docstring for why the two Alpha packages can't
import from each other. Logic is unchanged from the original.
"""
from __future__ import annotations

from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.risk.contracts import RiskStatus
from atlas.analysis_engine.risk.models import EVALUATED_RISK_CATEGORIES, RiskAnalysisResult, RiskProjection

__all__ = ["risk_projection"]

#: Fixed, deterministic tie-break order -- the canonical `RiskCategory`
#: enum's own declared order, filtered to the categories a real
#: evaluator exists for. Not invented for this module: this is simply
#: "the order the taxonomy itself was written in," the same non-
#: arbitrary-ordering discipline every other first-match-wins rule
#: table in this codebase already follows.
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


def risk_projection(risk_analysis: RiskAnalysisResult) -> RiskProjection:
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
