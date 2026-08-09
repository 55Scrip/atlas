"""FCF Yield evaluator v1 (ATLAS-024, Phase 6/7; temporal alignment
rewritten ATLAS-032) -- Atlas's first real Valuation method: current
Free Cash Flow yield vs. this company's own historical FCF-yield range.
Chosen over P/E, EV/EBITDA, or a full DCF precisely because it needs
the fewest unsupported assumptions: `FCF` already exists as a real
`business_facts.BusinessFact` (ATLAS-023, reused verbatim, never
duplicated), and `SHARE_PRICE`/`SHARES_OUTSTANDING` (this sprint's own
`ValuationFact`s) are the minimum needed to derive a market
capitalization ourselves.

**ATLAS-032: period is no longer used to match a Free Cash Flow fact
to a market observation.** ATLAS-024's original rule required an exact
`fact.period` string match between FCF and market snapshot -- for real
providers this never fires, because SEC fundamentals key `period` by
fiscal-year-end date and Alpha Vantage market snapshots key `period` by
trading date. Those are different questions by construction, not a
coincidence to be patched around.

**The corrected rule, documented before it was implemented:** a
"market observation" is a period where a `SHARE_PRICE` and a
`SHARES_OUTSTANDING` fact both exist (unchanged -- both always arrive
together in one `MARKET_DATA_SNAPSHOT` document today). For each market
observation, the *eligible* Free Cash Flow fact is the one with the
most recent `period` among all FCF facts whose `published_at` is on or
before that observation's own date -- i.e. the most recent fundamental
Atlas could actually have known about at that point in time. A market
observation with no eligible FCF fact at all (every known FCF fact was
published after that snapshot was taken) contributes nothing, exactly
like a period missing FCF entirely.

**This is the no-look-ahead guarantee, expressed as code, not a
comment.** It compares `published_at` (a real, disclosed timestamp)
against a market observation's own date -- never `period` against
`period`, since a fact's period never says when the fact became public.

`market_cap = share_price × shares_outstanding`, `fcf_yield = FCF /
market_cap`, computed independently for every market observation with
an eligible, positive FCF fact. An observation is excluded entirely
(not just flagged) when its eligible FCF is zero or negative -- a yield
computed from it would invert into a sign that means nothing in this
method, the same "do not force the formula into a misleading result"
instruction Phase 17 states for negative earnings.

In this fixed order, first match wins:

1. Zero valid observations (eligible FCF > 0, market cap > 0) exist ->
   `INSUFFICIENT_INPUT`, with every applicable reason named
   (`MISSING_FREE_CASH_FLOW_HISTORY`, `MISSING_MARKET_PRICE`,
   `MISSING_SHARE_COUNT`, `CASH_FLOW_NOT_POSITIVE` -- whichever
   genuinely apply).
2. Exactly one valid observation exists (the current one, no history)
   -> `INSUFFICIENT_INPUT`, `INSUFFICIENT_HISTORICAL_VALUATION_PERIODS`
   -- there is nothing to be "relative to." `current_yield` is still
   populated on the returned finding: Current FCF Yield does not
   require a historical range to be real (ATLAS-032, Phase 5).
3. Current yield (the most recent valid observation) exceeds every
   historical yield -> `UNDERVALUED`.
4. Current yield is below every historical yield -> `EXPENSIVE`.
5. Otherwise (within the historical range) -> `FAIRLY_VALUED`.

**No universal constant appears anywhere in this table.** "Cheap" and
"expensive" are always relative to the same company's own recorded
history -- never a fixed yield percentage, never a P/E cutoff.

**Staleness (ATLAS-032, retired, not redefined with a new magic
number).** ATLAS-024's original `STALE_MARKET_DATA` check compared a
market snapshot's `period` against the most recent FCF fact's
`period` -- exactly the same period-vs-period confusion this rewrite
removes everywhere else, and it is retired for the same reason, not
replaced by an equivalent bug. A genuinely useful "the market snapshot
we have is old" signal would need a real, owned wall-clock threshold
(how many days old is too old to call "current"), and no such threshold
is owned anywhere in this codebase today -- inventing one here would be
exactly the kind of arbitrary constant this method's rule table already
refuses to have. `ValuationDataGapKind.STALE_MARKET_DATA` remains
defined for a future sprint that defines and owns that threshold; this
evaluator never constructs it.
"""
from __future__ import annotations

from datetime import date, datetime

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


def _parse_period_date(period: str) -> date | None:
    """Market observation periods always originate from a provider's
    own snapshot date (`RawBusinessDocument.period_end.isoformat()`),
    so this always succeeds for real data. `business_facts.models`'s
    own docstring is explicit that `period` is "not guaranteed" to be a
    date in general -- this function fails closed (returns `None`,
    excluding the observation) rather than assuming a format a future
    non-market fact source might not honor."""
    try:
        return date.fromisoformat(period)
    except ValueError:
        return None


def _eligible_fcf_as_of(fcf_facts: list[BusinessFact], as_of: date) -> BusinessFact | None:
    """The most recent Free Cash Flow fact (by `period`) among those
    whose `published_at` is on or before `as_of` -- the no-look-ahead
    rule. Ties (same `period`, different `published_at` -- e.g. a
    restatement) break by `published_at` then `id` for determinism."""
    eligible = [fact for fact in fcf_facts if fact.published_at.date() <= as_of]
    if not eligible:
        return None
    return max(eligible, key=lambda fact: (fact.period, fact.published_at, fact.id))


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
    fcf_facts = [fact for fact in business_facts if fact.kind is BusinessFactKind.FREE_CASH_FLOW]
    price_by_period = _by_period(list(valuation_facts), ValuationFactKind.SHARE_PRICE)
    shares_by_period = _by_period(list(valuation_facts), ValuationFactKind.SHARES_OUTSTANDING)

    missing: list[ValuationDataGapKind] = []
    if not fcf_facts:
        missing.append(ValuationDataGapKind.MISSING_FREE_CASH_FLOW_HISTORY)
    if not price_by_period:
        missing.append(ValuationDataGapKind.MISSING_MARKET_PRICE)
    if not shares_by_period:
        missing.append(ValuationDataGapKind.MISSING_SHARE_COUNT)

    # A market observation is a period where both a price and a share
    # count exist -- unchanged from ATLAS-024, since both always arrive
    # together in one MARKET_DATA_SNAPSHOT document.
    market_periods = sorted(set(price_by_period) & set(shares_by_period))

    valid_observations: dict[str, tuple[float, tuple[str, str, str]]] = {}
    any_cash_flow_excluded_as_non_positive = False
    any_observation_without_eligible_fcf = False
    for period in market_periods:
        observation_date = _parse_period_date(period)
        if observation_date is None:
            continue
        eligible_fcf = _eligible_fcf_as_of(fcf_facts, observation_date)
        if eligible_fcf is None:
            any_observation_without_eligible_fcf = True
            continue
        if eligible_fcf.value <= 0:
            any_cash_flow_excluded_as_non_positive = True
            continue
        price_fact = price_by_period[period]
        shares_fact = shares_by_period[period]
        market_cap = price_fact.value * shares_fact.value
        if market_cap <= 0:
            continue
        yield_value = eligible_fcf.value / market_cap
        valid_observations[period] = (yield_value, (eligible_fcf.id, price_fact.id, shares_fact.id))

    if not valid_observations:
        if any_cash_flow_excluded_as_non_positive and ValuationDataGapKind.CASH_FLOW_NOT_POSITIVE not in missing:
            missing.append(ValuationDataGapKind.CASH_FLOW_NOT_POSITIVE)
        if (
            any_observation_without_eligible_fcf
            and ValuationDataGapKind.NO_ELIGIBLE_FUNDAMENTALS_AS_OF_OBSERVATION not in missing
        ):
            missing.append(ValuationDataGapKind.NO_ELIGIBLE_FUNDAMENTALS_AS_OF_OBSERVATION)
        return _insufficient(missing, business_facts, valuation_facts, evaluated_at)

    most_recent_period = max(valid_observations)
    current_yield, current_fact_ids = valid_observations[most_recent_period]

    if len(valid_observations) < 2:
        # Current FCF Yield is real and traceable even with no history
        # to classify it against (ATLAS-032, Phase 5) -- only the
        # relative UNDERVALUED/FAIRLY_VALUED/EXPENSIVE classification
        # is genuinely unreachable here.
        return _insufficient(
            [ValuationDataGapKind.INSUFFICIENT_HISTORICAL_VALUATION_PERIODS],
            business_facts,
            valuation_facts,
            evaluated_at,
            current_yield=current_yield,
            current_fact_ids=current_fact_ids,
        )

    historical = {period: v for period, v in valid_observations.items() if period != most_recent_period}
    historical_yields = [yield_value for yield_value, _ in historical.values()]

    if current_yield > max(historical_yields):
        status = ValuationStatus.UNDERVALUED
    elif current_yield < min(historical_yields):
        status = ValuationStatus.EXPENSIVE
    else:
        status = ValuationStatus.FAIRLY_VALUED

    all_fact_ids = tuple(
        sorted({fid for _, ids in valid_observations.values() for fid in ids})
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
        current_yield=current_yield,
    )


def _insufficient(
    missing: list[ValuationDataGapKind],
    business_facts: tuple[BusinessFact, ...],
    valuation_facts: tuple[ValuationFact, ...],
    evaluated_at: datetime,
    *,
    current_yield: float | None = None,
    current_fact_ids: tuple[str, str, str] | None = None,
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

    supporting_facts = current_fact_ids if current_fact_ids is not None else ()

    status = ValuationStatus.INSUFFICIENT_INPUT
    return ValuationFinding(
        id=f"valuation_finding:{ValuationMethodKind.FCF_YIELD_RELATIVE.value}",
        kind=ValuationMethodKind.FCF_YIELD_RELATIVE,
        status=status,
        severity=severity_for_valuation_status(status),
        supporting_facts=supporting_facts,
        contradicting_facts=(),
        assumptions=(),
        missing_evidence=tuple(missing),
        confidence=confidence,
        provenance=Provenance(
            source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
            source_references=supporting_facts,
            dependencies=supporting_facts,
            update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
            consumers=_ALL_CONSUMERS,
            computed_at=evaluated_at,
        ),
        evaluated_at=evaluated_at,
        current_yield=current_yield,
    )
