"""Valuation Risk evaluator v1 (ATLAS-025, Phase 8).

**The rule table, documented before it was implemented:**

Reuses `atlas.analysis_engine.valuation.cash_flow
.evaluate_fcf_yield_relative`'s own `ValuationFinding.status` verbatim --
this evaluator must never recompute FCF yield or a historical valuation
range itself; one source of valuation truth (Phase 8's own explicit
rule). In this fixed order, first match wins:

1. `status in (NOT_EVALUATED, INSUFFICIENT_INPUT)` -> `RiskStatus
   .INSUFFICIENT_INPUT`. Atlas not having a real valuation conclusion is
   uncertainty about price, not a risk finding.
2. `status is EXPENSIVE` -> `RiskStatus.HIGH` -- paying a price above
   this company's own supported historical range is the one dimension
   this method can honestly call a real overpaying risk.
3. `status is FAIRLY_VALUED` -> `RiskStatus.MODERATE`.
4. `status is UNDERVALUED` -> `RiskStatus.LOW`, confirmed via explicit
   sprint direction: "map UNDERVALUED -> LOW... this is a clean
   one-to-one interpretation of the existing canonical Valuation
   result... the specific risk of overpaying is low."

**Architectural caveat, stated once here and never assumed away
elsewhere:** `LOW` Valuation Risk describes only this one narrow,
price-relative-to-history dimension. It is never a claim about overall
investment risk, and it must never override, feed, or be read by
Business Risk, Financial Risk, Thesis Risk, or Recommendation --
preserving Phase 17's independence-of-dimensions principle. A company
can honestly be `UNDERVALUED` (`Valuation Risk: LOW`) while its
`Business Risk` is independently `HIGH` -- detecting that combination
(a potential "value trap") is not this evaluator's job; it requires a
future consumer reading both categories together, which this module
deliberately does not attempt.

Confidence reuses `ValuationFinding.confidence` directly -- it already
answers "how well-supported is this specific conclusion."
"""
from __future__ import annotations

from datetime import datetime

from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.risk.contracts import RiskDataGapKind, RiskStatus, severity_for_risk_status
from atlas.analysis_engine.risk.models import RiskFinding
from atlas.analysis_engine.valuation.contracts import ValuationStatus
from atlas.analysis_engine.valuation.models import ValuationFinding

__all__ = ["evaluate_valuation_risk"]

_ALL_CONSUMERS = (
    Consumer.PORTFOLIO_PAGE,
    Consumer.INVESTMENT_CASE_PAGE,
    Consumer.DISCOVERY,
    Consumer.HISTORY,
)

_STATUS_MAP = {
    ValuationStatus.EXPENSIVE: RiskStatus.HIGH,
    ValuationStatus.FAIRLY_VALUED: RiskStatus.MODERATE,
    ValuationStatus.UNDERVALUED: RiskStatus.LOW,
}


def evaluate_valuation_risk(fcf_yield_finding: ValuationFinding, *, evaluated_at: datetime) -> RiskFinding:
    """Deterministic: identical `fcf_yield_finding` always produces a
    deeply equal `RiskFinding`. Reads only the already-computed
    `ValuationFinding` for `ValuationMethodKind.FCF_YIELD_RELATIVE` --
    never a `ValuationFact`/`BusinessFact`, never market data directly.
    """
    if fcf_yield_finding.status in (ValuationStatus.NOT_EVALUATED, ValuationStatus.INSUFFICIENT_INPUT):
        status = RiskStatus.INSUFFICIENT_INPUT
        missing = (RiskDataGapKind.VALUATION_ASSESSMENT_UNAVAILABLE,)
    else:
        status = _STATUS_MAP[fcf_yield_finding.status]
        missing = ()

    return RiskFinding(
        id=f"risk_finding:{RiskCategory.VALUATION_RISK.value}",
        category=RiskCategory.VALUATION_RISK,
        status=status,
        severity=severity_for_risk_status(status),
        supporting_facts=(fcf_yield_finding.id,),
        contradicting_facts=(),
        missing_evidence=missing,
        confidence=fcf_yield_finding.confidence,
        provenance=Provenance(
            source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
            source_references=(fcf_yield_finding.id,),
            dependencies=(fcf_yield_finding.id,),
            update_trigger=UpdateTrigger.UPSTREAM_STAGE_CHANGED,
            consumers=_ALL_CONSUMERS,
            computed_at=evaluated_at,
        ),
        evaluated_at=evaluated_at,
    )
