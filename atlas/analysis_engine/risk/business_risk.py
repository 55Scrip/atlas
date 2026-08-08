"""Business Risk evaluator v1 (ATLAS-025, Phase 7).

**The rule table, documented before it was implemented:**

Reuses `atlas.analysis_engine.growth.evaluate_growth`'s own
`BusinessFinding.status` verbatim -- never a second, independent
re-derivation of contraction/expansion. In this fixed order, first
match wins:

1. `GrowthFinding.status is INSUFFICIENT_INPUT` -> `RiskStatus
   .INSUFFICIENT_INPUT`. This is the sprint's own critical rule made
   concrete: Atlas not knowing enough about growth is uncertainty, not
   a negative business-risk signal -- it must never be silently
   converted into `HIGH`.
2. `GrowthFinding.status is WEAK` -> `RiskStatus.HIGH` -- sustained
   contraction across every supported metric is a real, observed
   negative signal.
3. `GrowthFinding.status is MODERATE` -> `RiskStatus.MODERATE`.
4. `GrowthFinding.status is STRONG` -> `RiskStatus.LOW`.

**Deliberately does not also read contradicting evidence.** Growth's own
status already captures "the business itself becoming less durable" per
`RiskCategory.BUSINESS_RISK`'s own docstring; contradicting evidence
against the investor's *thesis* is a distinct fact, owned exclusively by
`RiskCategory.THESIS_RISK` (`thesis_risk.py`). Reading it here too would
let two Risk categories silently claim the same underlying signal --
exactly the kind of hidden double-counting this sprint's "no weighted
aggregation" rule exists to prevent.

**Deliberately does not read Durability.** `atlas.decision_engine`'s own
Durability finding is permanently, structurally `INSUFFICIENT_INPUT`
for every Case today (Sprint 2's own lock) -- if Business Risk read it
at all, every company would show an identical Durability-driven
component, which is not a real signal, just a constant. Confidence
reuses `GrowthFinding.confidence` directly: it already answers "how
well-supported is this specific conclusion," the exact question Risk
confidence needs (Phase 11).
"""
from __future__ import annotations

from datetime import datetime

from atlas.analysis_engine.business_contracts import BusinessCategoryStatus, BusinessFinding
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.risk.contracts import RiskDataGapKind, RiskStatus, severity_for_risk_status
from atlas.analysis_engine.risk.models import RiskFinding

__all__ = ["evaluate_business_risk"]

_ALL_CONSUMERS = (
    Consumer.PORTFOLIO_PAGE,
    Consumer.INVESTMENT_CASE_PAGE,
    Consumer.DISCOVERY,
    Consumer.HISTORY,
)

_STATUS_MAP = {
    BusinessCategoryStatus.WEAK: RiskStatus.HIGH,
    BusinessCategoryStatus.MODERATE: RiskStatus.MODERATE,
    BusinessCategoryStatus.STRONG: RiskStatus.LOW,
}


def evaluate_business_risk(growth_finding: BusinessFinding, *, evaluated_at: datetime) -> RiskFinding:
    """Deterministic: identical `growth_finding` always produces a
    deeply equal `RiskFinding`. Reads only the already-computed
    `BusinessFinding` for `BusinessCategory.GROWTH` -- never raw
    `BusinessFact`s, never a `BusinessRecord`."""
    if growth_finding.status is BusinessCategoryStatus.INSUFFICIENT_INPUT:
        status = RiskStatus.INSUFFICIENT_INPUT
        missing = (RiskDataGapKind.GROWTH_ASSESSMENT_UNAVAILABLE,)
    else:
        status = _STATUS_MAP[growth_finding.status]
        missing = ()

    return RiskFinding(
        id=f"risk_finding:{RiskCategory.BUSINESS_RISK.value}",
        category=RiskCategory.BUSINESS_RISK,
        status=status,
        severity=severity_for_risk_status(status),
        supporting_facts=(growth_finding.id,),
        contradicting_facts=(),
        missing_evidence=missing,
        confidence=growth_finding.confidence,
        provenance=Provenance(
            source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
            source_references=(growth_finding.id,),
            dependencies=(growth_finding.id,),
            update_trigger=UpdateTrigger.UPSTREAM_STAGE_CHANGED,
            consumers=_ALL_CONSUMERS,
            computed_at=evaluated_at,
        ),
        evaluated_at=evaluated_at,
    )
