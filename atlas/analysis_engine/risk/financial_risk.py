"""Financial Risk evaluator v2 -- scale-aware debt burden.

**What "elevated financial risk" means in Atlas:** reported debt is large
relative to the cash the company's operations generate, in its latest
eligible fiscal year -- or operations consumed cash. It does not mean debt
merely rose, capital allocation is weak, the latest free cash flow was
negative, or the price is high, and it is never a credit rating: Atlas
holds no ratings, maturities, interest cost or liquidity facilities.

**Why v2 replaced v1.** v1 read three signals -- the Capital Allocation
status, the sign of the latest free cash flow, and whether total debt rose
in every period of its whole history -- and any one of them made the level
`HIGH`. The Financial Risk Model Audit found all three unfit as level
signals: debt direction ignores scale (VST and META were both `HIGH`, at
about 4.2x and 0.5x debt to operating cash flow) and, compared across a
full history, only ever fired for companies with short histories; the
debt trend and the free-cash-flow sign were both counted a second time
through Capital Allocation, which contains the identical checks; and a
negative free cash flow is capex-driven as often as it is a warning.

**The rule, documented before it was implemented.** For each company, in
this fixed order, first match wins:

1. **Applicability.** `applicability.debt_burden_measure_applies` on the
   company-profile industry: `False` -> `NOT_APPLICABLE` (banks, dealers,
   insurers -- the measure does not describe them); `None` (no industry
   recorded) -> `INSUFFICIENT_INPUT`, gap `INDUSTRY_UNKNOWN`.
2. **Eligibility.** Only `TOTAL_DEBT`, `FREE_CASH_FLOW` and
   `CAPITAL_EXPENDITURE` facts that (a) come from a structured financial
   statement record and (b) end on or before the evaluation date are
   read; the rest are listed in the basis as excluded, with the reason.
3. **Alignment.** An observation needs all three facts for the same period
   end and in the same unit -- never one year's debt over another year's
   cash flow. No aligned period -> `INSUFFICIENT_INPUT` with the gap that
   explains it (`MISSING_DEBT`, `MISSING_OPERATING_CASH_FLOW` or
   `NO_ALIGNED_PERIOD`).
4. **Staleness.** The latest aligned period must end no more than
   `FINANCIAL_STATEMENT_MAX_AGE_DAYS` before the evaluation date, else
   `INSUFFICIENT_INPUT` / `STALE_FINANCIAL_STATEMENTS`.
5. **Level.** On that latest observation: operating cash flow (free cash
   flow plus capital expenditure) below zero -> `HIGH`, operations
   consumed cash; exactly zero -> `HIGH`, no ratio computed; otherwise
   gross debt / operating cash flow against `DEBT_BURDEN_BANDS`.

Up to two earlier aligned observations travel with the latest as trend
context. They never change the level: a burden drifting 0.99x -> 1.04x ->
1.09x is exactly as low or moderate as its latest figure says.

**Atlas policy bands, not credit-rating thresholds.** `DEBT_BURDEN_BANDS`
(below 1.25x low, 3.0x and above high) were chosen from the 23-company
distribution Atlas holds (median about 0.8x) as the round cuts with the
widest margins for the companies whose recommendation depends on them.
They say where Atlas draws its own line; they say nothing about what a
lender or rating agency would call safe.

**Staleness, owned here.** Atlas has no fundamentals-freshness policy to
reuse (`valuation/cash_flow.py` records that none is owned), so this
evaluator owns one: two years. It tolerates one pending annual filing for
an annual reporter and excludes nothing in the current data except
histories that stopped years ago.

Never reads Capital Allocation, never reads a `BusinessRecord` -- the
caller supplies which source records are financial statements and the
company's profile industry -- and never reads a clock: `evaluated_at` is
the only notion of now.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.risk.applicability import debt_burden_measure_applies
from atlas.analysis_engine.risk.contracts import (
    FinancialRiskCondition,
    FinancialRiskExclusionReason,
    FinancialRiskMeasure,
    RiskDataGapKind,
    RiskStatus,
    severity_for_risk_status,
)
from atlas.analysis_engine.risk.models import (
    DebtBurdenBands,
    DebtBurdenObservation,
    FinancialRiskBasis,
    FinancialRiskExclusion,
    RiskFinding,
)
from atlas.decision_engine.contracts import EvidenceCoverageLevel

__all__ = [
    "DEBT_BURDEN_BANDS",
    "FINANCIAL_RISK_METHODOLOGY",
    "FINANCIAL_STATEMENT_MAX_AGE_DAYS",
    "assess_financial_risk_basis",
    "evaluate_financial_risk",
]

#: Names how Financial Risk is measured, so a change of method is never
#: read as a change in the company (`investment_case_change` compares
#: Financial Risk only between snapshots taken under the same method).
FINANCIAL_RISK_METHODOLOGY = "debt_burden_v2"

#: Atlas policy bands for gross debt / operating cash flow. Not
#: credit-rating thresholds -- see the module docstring.
DEBT_BURDEN_BANDS = DebtBurdenBands(low_below=1.25, high_from=3.0)

#: The oldest a latest aligned period may be, in days before the
#: evaluation date -- two years. See the module docstring.
FINANCIAL_STATEMENT_MAX_AGE_DAYS = 730

#: Earlier aligned observations carried as trend context, besides the latest.
_TREND_CONTEXT_PERIODS = 2

_LEVEL = {
    FinancialRiskCondition.DEBT_BURDEN_LOW: RiskStatus.LOW,
    FinancialRiskCondition.DEBT_BURDEN_MODERATE: RiskStatus.MODERATE,
    FinancialRiskCondition.DEBT_BURDEN_HIGH: RiskStatus.HIGH,
    FinancialRiskCondition.OPERATING_CASH_FLOW_NEGATIVE: RiskStatus.HIGH,
    FinancialRiskCondition.OPERATING_CASH_FLOW_ZERO: RiskStatus.HIGH,
}

_BURDEN_KINDS = (BusinessFactKind.TOTAL_DEBT, BusinessFactKind.FREE_CASH_FLOW, BusinessFactKind.CAPITAL_EXPENDITURE)

_ALL_CONSUMERS = (
    Consumer.PORTFOLIO_PAGE,
    Consumer.INVESTMENT_CASE_PAGE,
    Consumer.DISCOVERY,
    Consumer.HISTORY,
)


def _eligible(
    facts: tuple[BusinessFact, ...], *, statement_record_ids: frozenset[str], evaluated_at: datetime
) -> tuple[list[BusinessFact], tuple[FinancialRiskExclusion, ...]]:
    cutoff = evaluated_at.date().isoformat()
    eligible: list[BusinessFact] = []
    excluded: list[FinancialRiskExclusion] = []
    for fact in sorted(facts, key=lambda f: (f.period, f.kind.value, f.id)):
        if fact.kind not in _BURDEN_KINDS:
            continue
        if fact.period > cutoff:
            excluded.append(FinancialRiskExclusion(fact.id, FinancialRiskExclusionReason.FUTURE_PERIOD))
        elif fact.source_record_id not in statement_record_ids:
            excluded.append(FinancialRiskExclusion(fact.id, FinancialRiskExclusionReason.NOT_A_FINANCIAL_STATEMENT))
        else:
            eligible.append(fact)
    return eligible, tuple(excluded)


def _aligned(eligible: list[BusinessFact]) -> tuple[DebtBurdenObservation, ...]:
    """One observation per period end where all three kinds exist exactly
    once in one shared unit; any ambiguity at a period drops that period."""
    by_period: dict[str, dict[BusinessFactKind, list[BusinessFact]]] = {}
    for fact in eligible:
        by_period.setdefault(fact.period, {}).setdefault(fact.kind, []).append(fact)
    observations = []
    for period in sorted(by_period):
        kinds = by_period[period]
        if any(len(kinds.get(kind, ())) != 1 for kind in _BURDEN_KINDS):
            continue
        debt, fcf, capex = (kinds[kind][0] for kind in _BURDEN_KINDS)
        if len({debt.unit, fcf.unit, capex.unit}) != 1:
            continue
        observations.append(DebtBurdenObservation(
            period=period,
            unit=debt.unit,
            total_debt=debt.value,
            free_cash_flow=fcf.value,
            capital_expenditure=capex.value,
            total_debt_fact_id=debt.id,
            free_cash_flow_fact_id=fcf.id,
            capital_expenditure_fact_id=capex.id,
            source_record_ids=tuple(sorted({debt.source_record_id, fcf.source_record_id, capex.source_record_id})),
        ))
    return tuple(observations)


def _gaps_without_alignment(eligible: list[BusinessFact]) -> tuple[RiskDataGapKind, ...]:
    kinds = {fact.kind for fact in eligible}
    gaps = []
    if BusinessFactKind.TOTAL_DEBT not in kinds:
        gaps.append(RiskDataGapKind.MISSING_DEBT)
    if not {BusinessFactKind.FREE_CASH_FLOW, BusinessFactKind.CAPITAL_EXPENDITURE} <= kinds:
        gaps.append(RiskDataGapKind.MISSING_OPERATING_CASH_FLOW)
    return tuple(gaps) or (RiskDataGapKind.NO_ALIGNED_PERIOD,)


def _level(latest: DebtBurdenObservation) -> FinancialRiskCondition:
    ocf = latest.operating_cash_flow
    if ocf < 0:
        return FinancialRiskCondition.OPERATING_CASH_FLOW_NEGATIVE
    if ocf == 0:
        return FinancialRiskCondition.OPERATING_CASH_FLOW_ZERO
    return DEBT_BURDEN_BANDS.condition_for(latest.total_debt / ocf)


def assess_financial_risk_basis(
    business_facts: tuple[BusinessFact, ...],
    *,
    statement_record_ids: frozenset[str],
    industry: str | None,
    evaluated_at: datetime,
) -> FinancialRiskBasis:
    """The rule table above, first match wins. Pure and deterministic."""
    applies = debt_burden_measure_applies(industry)
    eligible, excluded = _eligible(business_facts, statement_record_ids=statement_record_ids, evaluated_at=evaluated_at)
    common = dict(bands=DEBT_BURDEN_BANDS, industry=industry, excluded=excluded)
    if applies is False:
        return FinancialRiskBasis(
            level=RiskStatus.NOT_APPLICABLE, condition=FinancialRiskCondition.MEASURE_NOT_APPLICABLE, **common)
    insufficient = dict(level=RiskStatus.INSUFFICIENT_INPUT, condition=FinancialRiskCondition.NO_ELIGIBLE_EVIDENCE)
    if applies is None:
        return FinancialRiskBasis(**insufficient, gaps=(RiskDataGapKind.INDUSTRY_UNKNOWN,), **common)
    observations = _aligned(eligible)
    if not observations:
        return FinancialRiskBasis(**insufficient, gaps=_gaps_without_alignment(eligible), **common)
    latest = observations[-1]
    oldest_allowed = (evaluated_at - timedelta(days=FINANCIAL_STATEMENT_MAX_AGE_DAYS)).date().isoformat()
    if latest.period < oldest_allowed:
        return FinancialRiskBasis(**insufficient, gaps=(RiskDataGapKind.STALE_FINANCIAL_STATEMENTS,), **common)
    condition = _level(latest)
    return FinancialRiskBasis(
        level=_LEVEL[condition],
        condition=condition,
        measure=FinancialRiskMeasure.GROSS_DEBT_TO_OPERATING_CASH_FLOW,
        latest=latest,
        history=observations[-(_TREND_CONTEXT_PERIODS + 1):],
        **common,
    )


def _confidence(basis: FinancialRiskBasis, business_facts: tuple[BusinessFact, ...]) -> EvidenceCoverageLevel:
    if basis.level is RiskStatus.NOT_APPLICABLE:
        return EvidenceCoverageLevel.NOT_APPLICABLE
    if basis.latest is not None:
        return EvidenceCoverageLevel.FULL
    # Same distinction Capital Allocation draws: relevant facts exist but
    # none are usable (NONE) versus no relevant facts at all.
    if any(fact.kind in _BURDEN_KINDS for fact in business_facts):
        return EvidenceCoverageLevel.NONE
    return EvidenceCoverageLevel.NOT_APPLICABLE


def evaluate_financial_risk(
    business_facts: tuple[BusinessFact, ...],
    *,
    statement_record_ids: frozenset[str],
    industry: str | None,
    evaluated_at: datetime,
) -> RiskFinding:
    """Deterministic: identical facts, statement-record ids, industry and
    evaluation date always produce a deeply equal `RiskFinding`."""
    basis = assess_financial_risk_basis(
        business_facts, statement_record_ids=statement_record_ids, industry=industry, evaluated_at=evaluated_at)
    supporting_ids = tuple(sorted(basis.latest.fact_ids)) if basis.latest is not None else ()
    dependencies = tuple(sorted(fact.id for fact in business_facts if fact.kind in _BURDEN_KINDS))
    return RiskFinding(
        id=f"risk_finding:{RiskCategory.FINANCIAL_RISK.value}",
        category=RiskCategory.FINANCIAL_RISK,
        status=basis.level,
        severity=severity_for_risk_status(basis.level),
        supporting_facts=supporting_ids,
        contradicting_facts=(),
        missing_evidence=basis.gaps,
        confidence=_confidence(basis, business_facts),
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
