"""Financial Risk evaluator v1 (ATLAS-025, Phase 6; extended Company
Data Foundation v1).

**The rule table, documented before it was implemented:**

Two independent signals, deliberately never blended into one number,
plus one narrower, escalation-only third signal added this sprint:

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
- **`debt_trend_signal`** (Company Data Foundation v1) -- reuses
  `growth.classify_metric_trend` verbatim (never a second trend
  algorithm) over consecutive-period `TOTAL_DEBT` facts: `HIGH` when
  total debt increased in every consecutive period (a clean, real
  worsening trend), `LOW` when it decreased in every consecutive
  period, `INSUFFICIENT_INPUT` for fewer than two periods or a mixed
  trend. **Deliberately excluded from `confidence` and from the `LOW`/
  `INSUFFICIENT_INPUT` branches below** -- see "Escalation-only,"
  below.

**Combined, in this fixed order, first match wins:**

1. `capital_allocation_signal` and `cash_generation_signal` both
   `INSUFFICIENT_INPUT`, and `debt_trend_signal` is not `HIGH` ->
   `RiskStatus.INSUFFICIENT_INPUT`.
2. Any of the three signals is `HIGH` -> `RiskStatus.HIGH` -- an
   adverse signal on even one computable side is disqualifying, never
   offset by another side being positive (the same "no hidden
   weighting" discipline `capital_allocation.py`'s own rule table
   already applies).
3. `capital_allocation_signal` and `cash_generation_signal` both
   computable and `LOW` -> `RiskStatus.LOW` -- `debt_trend_signal`
   being `LOW` or `INSUFFICIENT_INPUT` never blocks this; it only ever
   adds real confirming evidence when it fires, never a precondition.
4. Anything else -> `RiskStatus.MODERATE`.

**Escalation-only, by design.** `debt_trend_signal` can turn a would-be
`LOW`/`MODERATE`/`INSUFFICIENT_INPUT` result into `HIGH`, and its
supporting `TOTAL_DEBT` fact ids are always added to `supporting_facts`/
`dependencies` when it fires -- but it is deliberately **excluded from
`confidence`'s own computation**, which still counts only the original
two signals exactly as ATLAS-025 defined it. Folding a brand-new fact
kind into that denominator would silently downgrade every company's
`confidence` from `FULL` to `PARTIAL` the moment `TOTAL_DEBT` exists as
a fact kind but is not yet populated for that company -- a real
regression, not a genuine confidence loss, since the two original
signals are exactly as knowable as before. A future sprint that wants
`TOTAL_DEBT` fully weighted into `confidence` needs to make that
tradeoff deliberately, not inherit it from an additive extension.

**Never invents a leverage ratio.** No debt-to-EBITDA, debt-to-equity,
or any other ratio exists anywhere in this evaluator -- `debt_trend_signal`
is a pure sign-of-consecutive-deltas comparison (the same discipline
`growth.py` already established for Revenue/FCF), never a threshold
against an invented "safe" level. Missing `TOTAL_DEBT` facts are never
treated as "zero debt," and a mixed or single-period debt trend is
`INSUFFICIENT_INPUT`, never `MODERATE` -- an unclear trend is honestly
unclear, not a soft warning.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from atlas.analysis_engine.business_contracts import BusinessCategoryStatus, BusinessFinding
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.growth import MetricTrend, classify_metric_trend
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


def _debt_trend_signal(facts: tuple[BusinessFact, ...]) -> tuple[_Signal, tuple[str, ...]]:
    """(Company Data Foundation v1) Reuses `growth.classify_metric_trend`
    verbatim over consecutive-period `TOTAL_DEBT` facts -- never a
    second trend algorithm. Rising debt in every consecutive period
    (`MetricTrend.STRONG_METRIC` in that function's own, growth-neutral
    vocabulary) is a real worsening signal here (`HIGH`); falling debt
    in every period (`WEAK_METRIC`) is a real improving signal (`LOW`);
    fewer than two periods or a mixed trend is honestly
    `INSUFFICIENT`, never guessed as `MODERATE`."""
    debt_facts = sorted(
        (fact for fact in facts if fact.kind is BusinessFactKind.TOTAL_DEBT), key=lambda fact: fact.period
    )
    if len(debt_facts) < 2:
        return _Signal.INSUFFICIENT, ()
    trend, supporting, contradicting = classify_metric_trend(debt_facts)
    fact_ids = tuple(sorted({*supporting, *contradicting}))
    if trend is MetricTrend.STRONG_METRIC:  # consistently rising debt
        return _Signal.HIGH, fact_ids
    if trend is MetricTrend.WEAK_METRIC:  # consistently falling debt
        return _Signal.LOW, fact_ids
    return _Signal.INSUFFICIENT, ()  # mixed trend: no clean signal either way


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
    debt_signal, debt_fact_ids = _debt_trend_signal(business_facts)

    # `confidence` is computed from exactly these two signals, unchanged
    # from ATLAS-025 -- see module docstring's "Escalation-only" section
    # for why `debt_signal` is deliberately excluded from this count.
    signals = (ca_signal, cash_signal)
    computable_count = sum(1 for signal in signals if signal is not _Signal.INSUFFICIENT)

    missing: list[RiskDataGapKind] = []
    if ca_signal is _Signal.INSUFFICIENT:
        missing.append(RiskDataGapKind.CAPITAL_ALLOCATION_ASSESSMENT_UNAVAILABLE)
    if cash_signal is _Signal.INSUFFICIENT:
        missing.append(RiskDataGapKind.MISSING_CASH_FLOW_LEVEL)
    if debt_signal is _Signal.INSUFFICIENT:
        missing.append(RiskDataGapKind.MISSING_DEBT_HISTORY)

    if _Signal.HIGH in (ca_signal, cash_signal, debt_signal):
        status = RiskStatus.HIGH
    elif computable_count == 0:
        status = RiskStatus.INSUFFICIENT_INPUT
    elif computable_count == 2 and ca_signal is _Signal.LOW and cash_signal is _Signal.LOW:
        status = RiskStatus.LOW
    else:
        status = RiskStatus.MODERATE

    supporting_ids = tuple(
        sorted({*(x for x in (ca_id, cash_fact.id if cash_fact else None) if x is not None), *debt_fact_ids})
    )
    relevant_fcf_ids = (fact.id for fact in business_facts if fact.kind is BusinessFactKind.FREE_CASH_FLOW)
    relevant_debt_ids = (fact.id for fact in business_facts if fact.kind is BusinessFactKind.TOTAL_DEBT)
    dependencies = tuple(sorted({capital_allocation_finding.id, *relevant_fcf_ids, *relevant_debt_ids}))

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
