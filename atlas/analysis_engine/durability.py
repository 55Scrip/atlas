"""Durability evaluator v1 -- `Doctrine` §4 dimension 1, from real
`BusinessFact`s only.

Built to the Growth evaluator's architecture (`growth.py`, ATLAS-023
Phase 5): reads only `BusinessFact`, never a `BusinessRecord`, a
provider, or document content; produces one `BusinessFinding`; introduces
no enum, no schema, and no threshold. Every comparison below is `>`,
`<`, or `==` on real extracted values.

**Deliberately does not read gross profit.** Gross margin is the better
moat proxy, and `gross_profit` genuinely exists in ingested records --
for 9 of 30 companies. Depending on it would make Durability
`INSUFFICIENT_INPUT` for the other 21 while every fact this module does
read is present for 26-30 of 30. A finding that works everywhere from
weaker signals beats a better signal that is almost never available.

**The three sub-assessments answer `Doctrine` §4 dimension 1's three
clauses, one each** ("durable demand, a defensible position relative to
competitors or substitutes, and a balance sheet that can survive a bad
year"):

*Demand durability* -- `REVENUE` sorted by period. `STRONG` when no
consecutive-period delta is negative (demand never fell); `WEAK` when
the last value is below the first (net erosion across the whole span);
`MODERATE` otherwise (it fell somewhere but recovered to at least where
it started). The three are exhaustive and ordered: "no negative delta"
implies "last >= first", so `STRONG` is tested first and the cases
cannot overlap.

*Margin durability* -- net margin (`NET_INCOME`/`REVENUE`) and, where
both are present in the same period, operating margin
(`OPERATING_INCOME`/`REVENUE`). A period contributes a margin only when
its revenue is strictly positive; a margin on zero or negative revenue
is not a small error, it is meaningless. Each margin series is
classified by the identical three-way rule as demand, then combined:
`STRONG` only when every supported series is `STRONG`, `WEAK` only when
every one is `WEAK`, `MODERATE` otherwise.

**This is a within-company proxy, not a competitive comparison.** True
"defensible relative to competitors or substitutes" needs peer data
this engine does not have and does not pretend to have; margin
persistence is what a single company's own history can honestly
support, and Industry Intelligence is where the comparative question
belongs.

*Balance-sheet resilience* -- two components. Free cash flow:
`STRONG` when every known value is positive, `WEAK` when every value is
zero or negative, `MODERATE` otherwise. Net debt (`TOTAL_DEBT` minus
`CASH`, both required in the same period): `STRONG` when no delta is
positive (leverage never rose), `WEAK` when the last value exceeds the
first, `MODERATE` otherwise. Combined by the same all-`STRONG` /
all-`WEAK` rule as margins.

**Overall status**, first match wins:

1. No sub-assessment is supported -> `INSUFFICIENT_INPUT`.
2. All three are supported and all three are `STRONG` -> `STRONG`.
   Requiring all three, not merely all *supported* ones, mirrors
   Growth's own "broad-based means more than one independent metric"
   choice: durability is a three-clause doctrinal concept, so the top
   tier requires all three clauses answered, not one answered well.
3. Every supported sub-assessment is `WEAK` -> `WEAK`.
4. Anything else -> `MODERATE`.

A sub-assessment is *supported* only with two or more comparable
periods; one period has no delta and grades nothing.

**Duplicate facts.** Two records may report the same metric for the same
period (an original filing and a later restatement). Only one can be
used, and the choice is made deterministically: the greatest
`(published_at, id)` wins, so a later-published figure supersedes the
earlier one for that period, and ties fall back to the deterministic
fact id rather than to input order.

**Measured limitation, recorded before wiring (do not skip at Stage 3).**
Run against every company's real extracted facts, this rule table
returns `MODERATE` for 32 of 32 -- no discriminating power at all. The
per-metric rule is sound (revenue demand alone grades 9 `STRONG`, 20
`MODERATE`, 1 `WEAK`); the collapse is in the combination. Margin
durability reaches `STRONG` for 0 of 26 companies, because "no adverse
delta in any period" is effectively unreachable for a *ratio* over the
14-19 periods Atlas actually holds, and rule 2 then requires all three
sub-assessments `STRONG` at once. A finding that says the same thing
about every company is not yet worth dispatching, so the combination
rule must be revisited -- with evidence, and without inventing a
threshold -- before Stage 3 connects this evaluator to
`BusinessAnalysis`. Candidates measured so far: a drawdown-relative
rule ("never fell below where it started"), which lifts revenue to 19
`STRONG`, and order-statistic comparisons of the latest value against
the series' own median, the pattern the valuation engine already uses.
Neither is adopted here.

`confidence` reuses `EvidenceCoverageLevel` at the Finding level exactly
as Growth does: `FULL` (all three supported), `PARTIAL` (one or two),
`NONE` (durability-relevant facts exist but none reaches two periods),
`NOT_APPLICABLE` (no durability-relevant facts at all).
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from atlas.analysis_engine.business_contracts import (
    BusinessCategory,
    BusinessDataGapKind,
    BusinessFinding,
    severity_for_status,
)
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus as Status
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
from atlas.decision_engine.contracts import EvidenceCoverageLevel

__all__ = ["evaluate_durability"]

#: Every fact kind this evaluator reads. `OPERATING_INCOME` is optional
#: (operating margin is computed only where it is present); the rest
#: each gate one sub-assessment.
_SUPPORTED_KINDS = (
    BusinessFactKind.REVENUE,
    BusinessFactKind.NET_INCOME,
    BusinessFactKind.OPERATING_INCOME,
    BusinessFactKind.FREE_CASH_FLOW,
    BusinessFactKind.CASH,
    BusinessFactKind.TOTAL_DEBT,
)

_MINIMUM_PERIODS = 2

_ALL_CONSUMERS = (
    Consumer.PORTFOLIO_PAGE,
    Consumer.INVESTMENT_CASE_PAGE,
    Consumer.DISCOVERY,
    Consumer.HISTORY,
)


class _Series:
    """One metric's deduplicated, period-ordered values, carrying the
    fact id behind each so evidence can be attributed."""

    __slots__ = ("periods", "values", "ids")

    def __init__(self, periods: list[str], values: list[float], ids: list[str]) -> None:
        self.periods, self.values, self.ids = periods, values, ids

    def __len__(self) -> int:
        return len(self.values)


def _facts_by_kind(facts: tuple[BusinessFact, ...]) -> dict[BusinessFactKind, dict[str, BusinessFact]]:
    """Group by kind, then collapse each period to a single fact.

    A later-published figure supersedes an earlier one for the same
    period; `id` breaks exact ties so the result never depends on the
    order `facts` arrived in.
    """
    grouped: dict[BusinessFactKind, dict[str, BusinessFact]] = defaultdict(dict)
    for fact in facts:
        if fact.kind not in _SUPPORTED_KINDS:
            continue
        by_period = grouped[fact.kind]
        existing = by_period.get(fact.period)
        if existing is None or (fact.published_at, fact.id) > (existing.published_at, existing.id):
            by_period[fact.period] = fact
    return grouped


def _series(by_period: dict[str, BusinessFact]) -> _Series:
    ordered = sorted(by_period.values(), key=lambda f: f.period)
    return _Series(
        [f.period for f in ordered], [f.value for f in ordered], [f.id for f in ordered]
    )


def _ratio_series(numerator: dict[str, BusinessFact], revenue: dict[str, BusinessFact]) -> _Series:
    """Margin per period, for periods carrying both facts and strictly
    positive revenue. Both fact ids are attributed to the period."""
    periods, values, ids = [], [], []
    for period in sorted(set(numerator) & set(revenue)):
        denominator = revenue[period]
        if denominator.value <= 0:
            continue
        periods.append(period)
        values.append(numerator[period].value / denominator.value)
        ids.append(f"{numerator[period].id}|{denominator.id}")
    return _Series(periods, values, ids)


def _ratio_free_net_debt(total_debt: dict[str, BusinessFact], cash: dict[str, BusinessFact]) -> _Series:
    """Net debt per period, for periods carrying both facts. Negative
    values are net cash and are a good thing -- the sign is preserved
    and the caller reads it with `adverse_when_rising`."""
    periods, values, ids = [], [], []
    for period in sorted(set(total_debt) & set(cash)):
        periods.append(period)
        values.append(total_debt[period].value - cash[period].value)
        ids.append(f"{total_debt[period].id}|{cash[period].id}")
    return _Series(periods, values, ids)


def _classify_persistence(
    series: _Series, *, adverse_when_rising: bool = False
) -> tuple[Status, set[str], set[str]]:
    """The three-way rule every sub-assessment shares.

    `STRONG` when no delta moves adversely, `WEAK` when the last value
    is worse than the first, `MODERATE` otherwise. `adverse_when_rising`
    flips the direction for net debt, where an increase is the bad
    outcome -- the rule itself is identical, only which sign counts as
    deterioration changes.
    """
    supporting: set[str] = set()
    contradicting: set[str] = set()
    any_adverse = False
    for index in range(1, len(series)):
        previous, current = series.values[index - 1], series.values[index]
        delta = current - previous
        if adverse_when_rising:
            delta = -delta
        pair = _split_ids(series.ids[index - 1]) | _split_ids(series.ids[index])
        if delta < 0:
            any_adverse = True
            contradicting |= pair
        elif delta > 0:
            supporting |= pair

    if not any_adverse:
        return Status.STRONG, supporting, contradicting

    first, last = series.values[0], series.values[-1]
    eroded = last > first if adverse_when_rising else last < first
    return (Status.WEAK if eroded else Status.MODERATE), supporting, contradicting


def _split_ids(compound: str) -> set[str]:
    return set(compound.split("|"))


def _classify_positivity(series: _Series) -> tuple[Status, set[str], set[str]]:
    """Free cash flow's own rule: every period positive, every period
    non-positive, or a mix. Unlike the persistence rule this reads each
    value on its own -- a company that funded itself in every known
    period is resilient whether or not the amount rose."""
    supporting = {i for value, ids in zip(series.values, series.ids) if value > 0 for i in _split_ids(ids)}
    contradicting = {i for value, ids in zip(series.values, series.ids) if value <= 0 for i in _split_ids(ids)}
    if not contradicting:
        return Status.STRONG, supporting, contradicting
    if not supporting:
        return Status.WEAK, supporting, contradicting
    return Status.MODERATE, supporting, contradicting


def _combine(parts: list[Status]) -> Status:
    if all(part is Status.STRONG for part in parts):
        return Status.STRONG
    if all(part is Status.WEAK for part in parts):
        return Status.WEAK
    return Status.MODERATE


def _confidence(supported_count: int, any_facts_at_all: bool) -> EvidenceCoverageLevel:
    if supported_count == 3:
        return EvidenceCoverageLevel.FULL
    if supported_count > 0:
        return EvidenceCoverageLevel.PARTIAL
    if any_facts_at_all:
        return EvidenceCoverageLevel.NONE
    return EvidenceCoverageLevel.NOT_APPLICABLE


def evaluate_durability(facts: tuple[BusinessFact, ...], *, evaluated_at: datetime) -> BusinessFinding:
    """Deterministic: identical `facts` always produce a deeply equal
    `BusinessFinding`, regardless of the order they arrive in. Reads
    only `BusinessFact` -- no `BusinessRecord`, no provider object, no
    document content, and no wall clock.
    """
    grouped = _facts_by_kind(facts)
    any_facts_at_all = any(grouped.values())

    revenue = grouped.get(BusinessFactKind.REVENUE, {})
    net_income = grouped.get(BusinessFactKind.NET_INCOME, {})
    operating_income = grouped.get(BusinessFactKind.OPERATING_INCOME, {})
    free_cash_flow = grouped.get(BusinessFactKind.FREE_CASH_FLOW, {})
    cash = grouped.get(BusinessFactKind.CASH, {})
    total_debt = grouped.get(BusinessFactKind.TOTAL_DEBT, {})

    supporting: set[str] = set()
    contradicting: set[str] = set()
    missing: list[BusinessDataGapKind] = []
    supported: list[Status] = []

    # -- Demand durability -------------------------------------------
    demand = _series(revenue)
    if len(demand) >= _MINIMUM_PERIODS:
        status, plus, minus = _classify_persistence(demand)
        supported.append(status)
        supporting |= plus
        contradicting |= minus
    else:
        missing.append(BusinessDataGapKind.MISSING_REVENUE_HISTORY)

    # -- Margin durability -------------------------------------------
    margin_parts: list[Status] = []
    for numerator in (net_income, operating_income):
        margins = _ratio_series(numerator, revenue)
        if len(margins) >= _MINIMUM_PERIODS:
            status, plus, minus = _classify_persistence(margins)
            margin_parts.append(status)
            supporting |= plus
            contradicting |= minus
    if margin_parts:
        supported.append(_combine(margin_parts))
    else:
        # No "missing earnings history" member exists, and inventing one
        # is out of scope. A margin needs two periods carrying both a
        # numerator and positive revenue, so the generic periods gap is
        # the honest existing label.
        missing.append(BusinessDataGapKind.INSUFFICIENT_HISTORICAL_PERIODS)

    # -- Balance-sheet resilience ------------------------------------
    resilience_parts: list[Status] = []
    cash_flow = _series(free_cash_flow)
    if len(cash_flow) >= _MINIMUM_PERIODS:
        status, plus, minus = _classify_positivity(cash_flow)
        resilience_parts.append(status)
        supporting |= plus
        contradicting |= minus
    else:
        missing.append(BusinessDataGapKind.MISSING_CASH_FLOW_HISTORY)

    net_debt = _ratio_free_net_debt(total_debt, cash)
    if len(net_debt) >= _MINIMUM_PERIODS:
        status, plus, minus = _classify_persistence(net_debt, adverse_when_rising=True)
        resilience_parts.append(status)
        supporting |= plus
        contradicting |= minus
    else:
        missing.append(BusinessDataGapKind.MISSING_DEBT_DATA)

    if resilience_parts:
        supported.append(_combine(resilience_parts))

    # -- Overall ------------------------------------------------------
    if not supported:
        status = Status.INSUFFICIENT_INPUT
        if any_facts_at_all:
            missing.append(BusinessDataGapKind.INSUFFICIENT_HISTORICAL_PERIODS)
    elif len(supported) == 3 and all(part is Status.STRONG for part in supported):
        status = Status.STRONG
    elif all(part is Status.WEAK for part in supported):
        status = Status.WEAK
    else:
        status = Status.MODERATE

    confidence = _confidence(len(supported), any_facts_at_all)
    dependencies = tuple(sorted(fact.id for by_period in grouped.values() for fact in by_period.values()))

    return BusinessFinding(
        id="business_finding:durability",
        kind=BusinessCategory.DURABILITY,
        status=status,
        severity=severity_for_status(status),
        supporting_evidence=tuple(sorted(supporting)),
        contradicting_evidence=tuple(sorted(contradicting)),
        missing_evidence=tuple(dict.fromkeys(missing)),
        confidence=confidence,
        provenance=Provenance(
            source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
            source_references=tuple(sorted(supporting | contradicting)),
            dependencies=dependencies,
            update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
            consumers=_ALL_CONSUMERS,
            computed_at=evaluated_at,
        ),
        updated_at=evaluated_at,
    )
