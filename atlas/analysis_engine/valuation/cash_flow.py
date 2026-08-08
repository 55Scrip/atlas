"""FCF Yield evaluator v1 (ATLAS-024, Phase 6/7) -- Atlas's first real
Valuation method: current Free Cash Flow yield vs. this company's own
historical FCF-yield range. Chosen over P/E, EV/EBITDA, or a full DCF
precisely because it needs the fewest unsupported assumptions: `FCF`
already exists as a real `business_facts.BusinessFact` (ATLAS-023,
reused verbatim, never duplicated), and `SHARE_PRICE`/
`SHARES_OUTSTANDING` (this sprint's own `ValuationFact`s) are the
minimum needed to derive a market capitalization ourselves.

**The rule table, documented before it was implemented (Phase 6's own
requirement):**

`market_cap = share_price × shares_outstanding`, `fcf_yield = FCF /
market_cap`, computed independently for every period where a Free Cash
Flow fact and a matching-period market snapshot both exist. A period is
excluded from consideration entirely (not just flagged) when its FCF is
zero or negative -- a yield computed from it would invert into a sign
that means nothing in this method, the same "do not force the formula
into a misleading result" instruction Phase 17 states for negative
earnings.

In this fixed order, first match wins:

1. Zero valid (FCF > 0, matched-period) yields exist -> `INSUFFICIENT_INPUT`,
   with every applicable reason named (`MISSING_FREE_CASH_FLOW_HISTORY`,
   `MISSING_MARKET_PRICE`, `MISSING_SHARE_COUNT`, `CASH_FLOW_NOT_POSITIVE`
   -- whichever genuinely apply).
2. A Free Cash Flow fact exists for a period *newer* than the most
   recent valid market snapshot -> `INSUFFICIENT_INPUT`,
   `STALE_MARKET_DATA` -- comparing a price against fundamentals it
   predates is a real methodological problem, not a generic freshness
   opinion (see `_is_stale`).
3. Fewer than two valid periods exist (only the current one, no
   history) -> `INSUFFICIENT_INPUT`, `INSUFFICIENT_HISTORICAL_VALUATION_PERIODS`
   -- there is nothing to be "relative to."
4. Current yield exceeds every historical yield -> `UNDERVALUED`.
5. Current yield is below every historical yield -> `EXPENSIVE`.
6. Otherwise (within the historical range) -> `FAIRLY_VALUED`.

**No universal constant appears anywhere in this table.** "Cheap" and
"expensive" are always relative to the same company's own recorded
history -- never a fixed yield percentage, never a P/E cutoff.
"""
from __future__ import annotations

from datetime import datetime

from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.valuation.contracts import (
    ValuationDataGapKind,
    ValuationMethodKind,
    ValuationStatus,
    severity_for_valuation_status,
)
from atlas.analysis_engine.valuation.facts import ValuationFact, ValuationFactKind
from atlas.analysis_engine.valuation.models import ValuationFinding
from atlas.decision_engine.contracts import EvidenceCoverageLevel

__all__ = ["evaluate_fcf_yield_relative"]

_ALL_CONSUMERS = (
    Consumer.PORTFOLIO_PAGE,
    Consumer.INVESTMENT_CASE_PAGE,
    Consumer.DISCOVERY,
    Consumer.HISTORY,
)


def _by_period(facts: list, kind) -> dict[str, object]:
    return {fact.period: fact for fact in facts if fact.kind is kind}


def evaluate_fcf_yield_relative(
    business_facts: tuple[BusinessFact, ...],
    valuation_facts: tuple[ValuationFact, ...],
    *,
    evaluated_at: datetime,
) -> ValuationFinding:
    """Deterministic: identical `business_facts`/`valuation_facts`
    always produce a deeply equal `ValuationFinding`. Reads only
    `BusinessFact`/`ValuationFact` -- no `BusinessRecord`, no provider
    object, no document content anywhere in this function.
    """
    fcf_by_period = _by_period(list(business_facts), BusinessFactKind.FREE_CASH_FLOW)
    price_by_period = _by_period(list(valuation_facts), ValuationFactKind.SHARE_PRICE)
    shares_by_period = _by_period(list(valuation_facts), ValuationFactKind.SHARES_OUTSTANDING)

    missing: list[ValuationDataGapKind] = []
    if not fcf_by_period:
        missing.append(ValuationDataGapKind.MISSING_FREE_CASH_FLOW_HISTORY)
    if not price_by_period:
        missing.append(ValuationDataGapKind.MISSING_MARKET_PRICE)
    if not shares_by_period:
        missing.append(ValuationDataGapKind.MISSING_SHARE_COUNT)

    # A period is "valid" only when FCF, price, and share count all
    # exist for it AND the resulting FCF is positive -- a negative or
    # zero yield is excluded outright, per this module's own rule table.
    valid_periods: dict[str, tuple[float, tuple[str, str, str]]] = {}
    any_cash_flow_excluded_as_non_positive = False
    for period, fcf_fact in fcf_by_period.items():
        price_fact = price_by_period.get(period)
        shares_fact = shares_by_period.get(period)
        if price_fact is None or shares_fact is None:
            continue
        if fcf_fact.value <= 0:
            any_cash_flow_excluded_as_non_positive = True
            continue
        market_cap = price_fact.value * shares_fact.value
        if market_cap <= 0:
            continue
        yield_value = fcf_fact.value / market_cap
        valid_periods[period] = (yield_value, (fcf_fact.id, price_fact.id, shares_fact.id))

    if not valid_periods:
        if any_cash_flow_excluded_as_non_positive and not missing:
            missing.append(ValuationDataGapKind.CASH_FLOW_NOT_POSITIVE)
        return _insufficient(missing, business_facts, valuation_facts, evaluated_at)

    most_recent_valid_period = max(valid_periods)

    # Staleness: does a Free Cash Flow fact exist for a period newer
    # than the most recent valid (price-matched) period? If so, the
    # market snapshot predates fundamentals Atlas already knows about.
    if any(period > most_recent_valid_period for period in fcf_by_period):
        return _insufficient(
            [ValuationDataGapKind.STALE_MARKET_DATA], business_facts, valuation_facts, evaluated_at
        )

    if len(valid_periods) < 2:
        return _insufficient(
            [ValuationDataGapKind.INSUFFICIENT_HISTORICAL_VALUATION_PERIODS],
            business_facts,
            valuation_facts,
            evaluated_at,
        )

    current_yield, current_fact_ids = valid_periods[most_recent_valid_period]
    historical = {period: v for period, v in valid_periods.items() if period != most_recent_valid_period}
    historical_yields = [yield_value for yield_value, _ in historical.values()]

    if current_yield > max(historical_yields):
        status = ValuationStatus.UNDERVALUED
    elif current_yield < min(historical_yields):
        status = ValuationStatus.EXPENSIVE
    else:
        status = ValuationStatus.FAIRLY_VALUED

    all_fact_ids = tuple(
        sorted({fid for _, ids in valid_periods.values() for fid in ids})
    )

    return ValuationFinding(
        id=f"valuation_finding:{ValuationMethodKind.FCF_YIELD_RELATIVE.value}",
        kind=ValuationMethodKind.FCF_YIELD_RELATIVE,
        status=status,
        severity=severity_for_valuation_status(status),
        supporting_facts=all_fact_ids,
        contradicting_facts=(),
        assumptions=(),
        missing_evidence=tuple(missing),
        confidence=EvidenceCoverageLevel.FULL,
        provenance=Provenance(
            source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
            source_references=all_fact_ids,
            dependencies=tuple(sorted({fid for fid in current_fact_ids})),
            update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
            consumers=_ALL_CONSUMERS,
            computed_at=evaluated_at,
        ),
        evaluated_at=evaluated_at,
    )


def _insufficient(
    missing: list[ValuationDataGapKind],
    business_facts: tuple[BusinessFact, ...],
    valuation_facts: tuple[ValuationFact, ...],
    evaluated_at: datetime,
) -> ValuationFinding:
    present_kinds = 0
    if any(f.kind is BusinessFactKind.FREE_CASH_FLOW for f in business_facts):
        present_kinds += 1
    if any(f.kind is ValuationFactKind.SHARE_PRICE for f in valuation_facts):
        present_kinds += 1
    if any(f.kind is ValuationFactKind.SHARES_OUTSTANDING for f in valuation_facts):
        present_kinds += 1

    if present_kinds == 0:
        confidence = EvidenceCoverageLevel.NOT_APPLICABLE
    elif present_kinds == 3:
        confidence = EvidenceCoverageLevel.NONE
    else:
        confidence = EvidenceCoverageLevel.PARTIAL

    status = ValuationStatus.INSUFFICIENT_INPUT
    return ValuationFinding(
        id=f"valuation_finding:{ValuationMethodKind.FCF_YIELD_RELATIVE.value}",
        kind=ValuationMethodKind.FCF_YIELD_RELATIVE,
        status=status,
        severity=severity_for_valuation_status(status),
        supporting_facts=(),
        contradicting_facts=(),
        assumptions=(),
        missing_evidence=tuple(missing),
        confidence=confidence,
        provenance=Provenance(
            source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
            source_references=(),
            dependencies=(),
            update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
            consumers=_ALL_CONSUMERS,
            computed_at=evaluated_at,
        ),
        evaluated_at=evaluated_at,
    )
