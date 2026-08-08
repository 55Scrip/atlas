"""Financial Risk evaluator v1 (ATLAS-025, Phase 6).

**The rule table, documented before it was implemented:**

Two independent signals, deliberately never blended into one number:

- **`capital_allocation_signal`** -- reused verbatim from
  `atlas.analysis_engine.capital_allocation.evaluate_capital_allocation`'s
  own `BusinessFinding.status`, never a second re-derivation of the
  buyback/issuance or debt-repayment/issuance comparison. Mapped
  `WEAK -> HIGH`, `MODERATE -> MODERATE`, `STRONG -> LOW`,
  `INSUFFICIENT_INPUT -> INSUFFICIENT_INPUT`.
- **`cash_generation_signal`** -- a direct, non-duplicating check
  Capital Allocation's own rule table does not perform: is the most
  recent known `FREE_CASH_FLOW` fact's *value* negative. `HIGH` if
  negative, `LOW` if positive-or-zero, `INSUFFICIENT_INPUT` if no
  `FREE_CASH_FLOW` fact exists at all. This checks a fact's sign, not a
  trend -- `growth.py`'s own Growth evaluator only ever compares
  consecutive periods to each other, never a level against zero, so
  "persistent negative free cash flow" (Phase 6's own named signal) is
  genuinely new information, not a duplicate of Growth's own
  contraction check.

Combined, in this fixed order, first match wins:

1. Both signals `INSUFFICIENT_INPUT` -> `RiskStatus.INSUFFICIENT_INPUT`.
2. Either signal `HIGH` -> `RiskStatus.HIGH` -- an adverse signal on
   even one computable side is disqualifying, never offset by the
   other side being positive (the same "no hidden weighting"
   discipline `capital_allocation.py`'s own rule table already
   applies).
3. Both signals computable and `LOW` -> `RiskStatus.LOW`.
4. Anything else (one signal computable and `LOW` while the other is
   `INSUFFICIENT_INPUT`, or either signal `MODERATE`) ->
   `RiskStatus.MODERATE`.

**Never invents a leverage ratio.** No total-debt or balance-sheet data
exists anywhere in this codebase; `capital_allocation_signal` already
reasons only from the debt *flows* (`DEBT_ISSUANCE`/`DEBT_REPAYMENT`)
Atlas genuinely has, and this evaluator adds nothing beyond that.
Missing `SHARE_ISSUANCE`/`DEBT_ISSUANCE` facts are never treated as
"zero issuance" -- that inference already does not happen inside
`capital_allocation.py`, and this evaluator does not reopen it.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from atlas.analysis_engine.business_contracts import BusinessCategoryStatus, BusinessFinding
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.risk.contracts import RiskDataGapKind, RiskStatus, severity_for_risk_status
from atlas.analysis_engine.risk.models import RiskFinding
from atlas.decision_engine.contracts import EvidenceCoverageLevel

__all__ = ["evaluate_financial_risk"]

_ALL_CONSUMERS = (
    Consumer.PORTFOLIO_PAGE,
    Consumer.INVESTMENT_CASE_PAGE,
    Consumer.DISCOVERY,
    Consumer.HISTORY,
)

_CAPITAL_ALLOCATION_MAP = {
    BusinessCategoryStatus.WEAK: RiskStatus.HIGH,
    BusinessCategoryStatus.MODERATE: RiskStatus.MODERATE,
    BusinessCategoryStatus.STRONG: RiskStatus.LOW,
}


class _Signal(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    INSUFFICIENT = "insufficient"


def _capital_allocation_signal(finding: BusinessFinding) -> tuple[_Signal, str | None]:
    if finding.status is BusinessCategoryStatus.INSUFFICIENT_INPUT:
        return _Signal.INSUFFICIENT, None
    mapped = _CAPITAL_ALLOCATION_MAP[finding.status]
    return _Signal(mapped.value), finding.id


def _cash_generation_signal(facts: tuple[BusinessFact, ...]) -> tuple[_Signal, BusinessFact | None]:
    fcf_facts = [fact for fact in facts if fact.kind is BusinessFactKind.FREE_CASH_FLOW]
    if not fcf_facts:
        return _Signal.INSUFFICIENT, None
    most_recent = max(fcf_facts, key=lambda fact: fact.period)
    if most_recent.value < 0:
        return _Signal.HIGH, most_recent
    return _Signal.LOW, most_recent


def _confidence(computable_count: int, capital_allocation_finding: BusinessFinding) -> EvidenceCoverageLevel:
    if computable_count == 2:
        return EvidenceCoverageLevel.FULL
    if computable_count == 1:
        return EvidenceCoverageLevel.PARTIAL
    # Both signals insufficient: cash-generation is insufficient only
    # when zero FREE_CASH_FLOW facts exist, so the Capital Allocation
    # Finding's own confidence -- which already distinguishes "some
    # relevant facts, none computable" (NONE) from "no relevant facts
    # at all" (NOT_APPLICABLE) -- is the most informative signal left.
    return capital_allocation_finding.confidence


def evaluate_financial_risk(
    capital_allocation_finding: BusinessFinding,
    business_facts: tuple[BusinessFact, ...],
    *,
    evaluated_at: datetime,
) -> RiskFinding:
    """Deterministic: identical inputs always produce a deeply equal
    `RiskFinding`. Reads the already-computed Capital Allocation
    `BusinessFinding` plus raw `BusinessFact`s -- never a
    `BusinessRecord`, never document content."""
    ca_signal, ca_id = _capital_allocation_signal(capital_allocation_finding)
    cash_signal, cash_fact = _cash_generation_signal(business_facts)

    signals = (ca_signal, cash_signal)
    computable_count = sum(1 for signal in signals if signal is not _Signal.INSUFFICIENT)

    missing: list[RiskDataGapKind] = []
    if ca_signal is _Signal.INSUFFICIENT:
        missing.append(RiskDataGapKind.CAPITAL_ALLOCATION_ASSESSMENT_UNAVAILABLE)
    if cash_signal is _Signal.INSUFFICIENT:
        missing.append(RiskDataGapKind.MISSING_CASH_FLOW_LEVEL)

    if computable_count == 0:
        status = RiskStatus.INSUFFICIENT_INPUT
    elif _Signal.HIGH in signals:
        status = RiskStatus.HIGH
    elif computable_count == 2 and ca_signal is _Signal.LOW and cash_signal is _Signal.LOW:
        status = RiskStatus.LOW
    else:
        status = RiskStatus.MODERATE

    supporting_ids = tuple(sorted(x for x in (ca_id, cash_fact.id if cash_fact else None) if x is not None))
    relevant_fcf_ids = (fact.id for fact in business_facts if fact.kind is BusinessFactKind.FREE_CASH_FLOW)
    dependencies = tuple(sorted({capital_allocation_finding.id, *relevant_fcf_ids}))

    return RiskFinding(
        id=f"risk_finding:{RiskCategory.FINANCIAL_RISK.value}",
        category=RiskCategory.FINANCIAL_RISK,
        status=status,
        severity=severity_for_risk_status(status),
        supporting_facts=supporting_ids,
        contradicting_facts=(),
        missing_evidence=tuple(missing),
        confidence=_confidence(computable_count, capital_allocation_finding),
        provenance=Provenance(
            source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
            source_references=supporting_ids,
            dependencies=dependencies,
            update_trigger=UpdateTrigger.UPSTREAM_STAGE_CHANGED,
            consumers=_ALL_CONSUMERS,
            computed_at=evaluated_at,
        ),
        evaluated_at=evaluated_at,
    )
