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

**The basis is the decision, retained.** Each signal returns a
`FinancialRiskSignalBasis` -- its level, the branch of its rule that
matched, and the facts (or upstream finding) it read -- and `_combine`
decides the level from those three bases and nothing else, returning the
line of the table that matched and the signals it rests on. `status` is
read from that result, so the disclosed basis and the level cannot
disagree. Disclosure changes no rule: every branch above is unchanged.
"""
from __future__ import annotations

from datetime import datetime

from atlas.analysis_engine.business_contracts import BusinessCategoryStatus, BusinessFinding
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.growth import MetricTrend, classify_metric_trend
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.risk.contracts import (
    FinancialRiskCondition,
    FinancialRiskMetric,
    FinancialRiskRule,
    FinancialRiskSignal,
    RiskDataGapKind,
    RiskStatus,
    severity_for_risk_status,
)
from atlas.analysis_engine.risk.models import (
    FinancialRiskBasis,
    FinancialRiskObservation,
    FinancialRiskSignalBasis,
    RiskFinding,
)
from atlas.decision_engine.contracts import EvidenceCoverageLevel

__all__ = ["evaluate_financial_risk"]

_ALL_CONSUMERS = (
    Consumer.PORTFOLIO_PAGE,
    Consumer.INVESTMENT_CASE_PAGE,
    Consumer.DISCOVERY,
    Consumer.HISTORY,
)

_CAPITAL_ALLOCATION_CONDITIONS = {
    BusinessCategoryStatus.WEAK: (RiskStatus.HIGH, FinancialRiskCondition.CAPITAL_ALLOCATION_WEAK),
    BusinessCategoryStatus.MODERATE: (RiskStatus.MODERATE, FinancialRiskCondition.CAPITAL_ALLOCATION_MODERATE),
    BusinessCategoryStatus.STRONG: (RiskStatus.LOW, FinancialRiskCondition.CAPITAL_ALLOCATION_STRONG),
}

_METRICS = {
    BusinessFactKind.FREE_CASH_FLOW: FinancialRiskMetric.FREE_CASH_FLOW,
    BusinessFactKind.TOTAL_DEBT: FinancialRiskMetric.TOTAL_DEBT,
}


def _observation(fact: BusinessFact) -> FinancialRiskObservation:
    return FinancialRiskObservation(
        metric=_METRICS[fact.kind],
        period=fact.period,
        value=fact.value,
        unit=fact.unit,
        fact_id=fact.id,
        source_record_id=fact.source_record_id,
    )


def _capital_allocation_signal(finding: BusinessFinding) -> FinancialRiskSignalBasis:
    if finding.status is BusinessCategoryStatus.INSUFFICIENT_INPUT:
        level, condition = RiskStatus.INSUFFICIENT_INPUT, FinancialRiskCondition.CAPITAL_ALLOCATION_UNAVAILABLE
    else:
        level, condition = _CAPITAL_ALLOCATION_CONDITIONS[finding.status]
    return FinancialRiskSignalBasis(
        signal=FinancialRiskSignal.CAPITAL_ALLOCATION,
        level=level,
        condition=condition,
        source_finding_id=finding.id,
    )


def _cash_generation_signal(facts: tuple[BusinessFact, ...]) -> FinancialRiskSignalBasis:
    fcf_facts = [fact for fact in facts if fact.kind is BusinessFactKind.FREE_CASH_FLOW]
    if not fcf_facts:
        return FinancialRiskSignalBasis(
            signal=FinancialRiskSignal.CASH_GENERATION,
            level=RiskStatus.INSUFFICIENT_INPUT,
            condition=FinancialRiskCondition.NO_FREE_CASH_FLOW,
        )
    most_recent = max(fcf_facts, key=lambda fact: fact.period)
    if most_recent.value < 0:
        level, condition = RiskStatus.HIGH, FinancialRiskCondition.LATEST_FREE_CASH_FLOW_NEGATIVE
    else:
        level, condition = RiskStatus.LOW, FinancialRiskCondition.LATEST_FREE_CASH_FLOW_NOT_NEGATIVE
    return FinancialRiskSignalBasis(
        signal=FinancialRiskSignal.CASH_GENERATION,
        level=level,
        condition=condition,
        observations=(_observation(most_recent),),
    )


def _debt_trend_signal(facts: tuple[BusinessFact, ...]) -> FinancialRiskSignalBasis:
    """(Company Data Foundation v1) Reuses `growth.classify_metric_trend`
    verbatim over consecutive-period `TOTAL_DEBT` facts -- never a
    second trend algorithm. Rising debt in every consecutive period
    (`MetricTrend.STRONG_METRIC` in that function's own, growth-neutral
    vocabulary) is a real worsening signal here (`HIGH`); falling debt
    in every period (`WEAK_METRIC`) is a real improving signal (`LOW`);
    fewer than two periods or a mixed trend is honestly
    `INSUFFICIENT`, never guessed as `MODERATE`.

    The basis carries every `TOTAL_DEBT` fact this signal evaluated, in
    period order -- the figures the trend was read from, whatever it
    concluded."""
    debt_facts = sorted(
        (fact for fact in facts if fact.kind is BusinessFactKind.TOTAL_DEBT), key=lambda fact: fact.period
    )
    observations = tuple(_observation(fact) for fact in debt_facts)
    if len(debt_facts) < 2:
        level, condition = RiskStatus.INSUFFICIENT_INPUT, FinancialRiskCondition.TOTAL_DEBT_FEWER_THAN_TWO_PERIODS
    else:
        trend, _, _ = classify_metric_trend(debt_facts)
        if trend is MetricTrend.STRONG_METRIC:  # consistently rising debt
            level, condition = RiskStatus.HIGH, FinancialRiskCondition.TOTAL_DEBT_INCREASED_EVERY_PERIOD
        elif trend is MetricTrend.WEAK_METRIC:  # consistently falling debt
            level, condition = RiskStatus.LOW, FinancialRiskCondition.TOTAL_DEBT_DECREASED_EVERY_PERIOD
        else:  # mixed trend: no clean signal either way
            level, condition = RiskStatus.INSUFFICIENT_INPUT, FinancialRiskCondition.TOTAL_DEBT_NO_CONSISTENT_DIRECTION
    return FinancialRiskSignalBasis(
        signal=FinancialRiskSignal.DEBT_TREND,
        level=level,
        condition=condition,
        observations=observations,
    )


def _combine(
    ca: FinancialRiskSignalBasis, cash: FinancialRiskSignalBasis, debt: FinancialRiskSignalBasis
) -> FinancialRiskBasis:
    """The combination table from this module's docstring, first match
    wins -- the one place the level is decided. It returns the level
    together with the line of the table that decided it and the signals
    that line rests on, so the basis is the decision itself rather than
    an account written after it."""
    signals = (ca, cash, debt)
    core = (ca, cash)
    high = tuple(s.signal for s in signals if s.level is RiskStatus.HIGH)
    if high:
        level, rule, determining = RiskStatus.HIGH, FinancialRiskRule.ANY_SIGNAL_HIGH, high
    elif all(s.level is RiskStatus.INSUFFICIENT_INPUT for s in core):
        level, rule = RiskStatus.INSUFFICIENT_INPUT, FinancialRiskRule.NO_CORE_SIGNAL_ASSESSED
        determining = tuple(s.signal for s in core)
    elif all(s.level is RiskStatus.LOW for s in core):
        level, rule = RiskStatus.LOW, FinancialRiskRule.CORE_SIGNALS_BOTH_LOW
        determining = tuple(s.signal for s in core)
    else:
        level, rule = RiskStatus.MODERATE, FinancialRiskRule.CORE_SIGNAL_NOT_LOW
        determining = tuple(s.signal for s in core if s.level is not RiskStatus.LOW)
    return FinancialRiskBasis(level=level, rule=rule, signals=signals, determining=determining)


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
    ca_signal = _capital_allocation_signal(capital_allocation_finding)
    cash_signal = _cash_generation_signal(business_facts)
    debt_signal = _debt_trend_signal(business_facts)
    basis = _combine(ca_signal, cash_signal, debt_signal)
    status = basis.level

    # `confidence` is computed from exactly these two signals, unchanged
    # from ATLAS-025 -- see module docstring's "Escalation-only" section
    # for why `debt_signal` is deliberately excluded from this count.
    signals = (ca_signal, cash_signal)
    computable_count = sum(1 for signal in signals if signal.level is not RiskStatus.INSUFFICIENT_INPUT)

    missing: list[RiskDataGapKind] = []
    if ca_signal.level is RiskStatus.INSUFFICIENT_INPUT:
        missing.append(RiskDataGapKind.CAPITAL_ALLOCATION_ASSESSMENT_UNAVAILABLE)
    if cash_signal.level is RiskStatus.INSUFFICIENT_INPUT:
        missing.append(RiskDataGapKind.MISSING_CASH_FLOW_LEVEL)
    if debt_signal.level is RiskStatus.INSUFFICIENT_INPUT:
        missing.append(RiskDataGapKind.MISSING_DEBT_HISTORY)

    # Supporting ids name only what a computable signal rested on: the
    # Capital Allocation finding when it reached a status, the latest FCF
    # fact when one exists, and the debt facts only when their trend was
    # clean. A mixed debt history stays in the basis as evaluated, not
    # here as support.
    supporting_ids = tuple(
        sorted({
            *((capital_allocation_finding.id,) if ca_signal.level is not RiskStatus.INSUFFICIENT_INPUT else ()),
            *(o.fact_id for o in cash_signal.observations),
            *(o.fact_id for o in debt_signal.observations if debt_signal.level is not RiskStatus.INSUFFICIENT_INPUT),
        })
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
        financial_risk_basis=basis,
    )
