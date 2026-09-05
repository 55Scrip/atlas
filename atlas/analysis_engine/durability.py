"""Durability evaluator -- `Doctrine` §4 dimension 1, from real
`BusinessFact`s only.

Built to the Growth evaluator's architecture (`growth.py`, ATLAS-023
Phase 5): reads only `BusinessFact`, never a `BusinessRecord`, a
provider, or document content; produces one `BusinessFinding`; introduces
no enum, no schema, and no threshold. Every comparison below is `>=`,
`<`, or `==` against a value the series itself supplies -- its own
median, its own starting level, or zero.

**Deliberately does not read gross profit.** Gross margin is the better
moat proxy, and `gross_profit` genuinely exists in ingested records --
for 9 of 30 companies. Depending on it would make Durability
`INSUFFICIENT_INPUT` for the other 21 while every fact this module does
read is present for 26-30 of 30. A finding that works everywhere from
weaker signals beats a better signal that is almost never available.

**The three sub-assessments answer `Doctrine` §4 dimension 1's three
clauses, one each** ("durable demand, a defensible position relative to
competitors or substitutes, and a balance sheet that can survive a bad
year without forced, thesis-breaking action"):

*Demand durability* and *margin durability* share one rule, stated once
in `_classify_level_persistence`: the latest observation is compared
against the series' own median and its own starting level. `STRONG` when
it is at or above both -- `Doctrine`'s "on comparable or better terms",
read literally. `WEAK` when it is below both, which is structural
erosion on every reference the series offers. `MODERATE` when the two
references disagree.

**Why not monotonicity.** The previous rule asked that no period be
worse than the one before it. Measured across the real corpus that is
unreachable: 0 of 28 companies have zero adverse margin deltas (minimum
1, mean 5.4), so `STRONG` could never occur, and demand carried a 47-point
history-length bias (55% `STRONG` on short histories against 8% on long)
because more periods mean more chances to dip. Doctrine asks about
*resilience through adversity*, never about smoothness -- it says a bad
year is survivable, not that it must not happen. A rule that punishes the
dip answers the wrong question. Under the rule above, the 15 companies
that dipped more than 25% below their starting margin and recovered stay
`STRONG`, and the one company with genuine structural erosion (revenue at
67% of peak, margin down 103%) is `WEAK`.

**Why the median and the start, and not the peak.** A peak-relative rule
was measured and rejected: `Doctrine` says "comparable or better terms",
not "at its best ever", and a peak comparison is knife-edge -- a company
at 99% of its peak revenue would read the same as one at 40%. The median
and the starting level are order statistics the series itself supplies,
so neither invents a threshold and neither grows more demanding as
history lengthens.

*Balance-sheet resilience* -- free cash flow only. `STRONG` when every
known period is positive, `WEAK` when every period is zero or negative,
`MODERATE` otherwise.

**Why net debt was removed.** An earlier version also asked whether net
debt fell monotonically. That answers the wrong question twice over:
`Doctrine` asks whether the business can *survive a bad year*, which is
a question about capacity, not about trajectory -- and a growing company
that funds expansion with debt is not thereby fragile. Measured, the
trend rule marked 15 of 25 companies `WEAK` and carried its own 33-point
history-length bias, then destroyed the free-cash-flow signal by
combination (19 `STRONG` standing alone, 4 once combined). No replacement
debt metric is introduced: every coverage measure available here would
need a ratio compared against unity, which is exactly the threshold this
module refuses to invent.

**Overall status** (veto), first match wins:

1. No sub-assessment is supported -> `INSUFFICIENT_INPUT`.
2. Any supported sub-assessment is `WEAK` -> `WEAK`. `Doctrine` states
   the three clauses conjunctively -- "durable demand, a defensible
   position ... *and* a balance sheet that can survive a bad year" -- so
   failing one clause is failing durability. The previous rule required
   all three to be `WEAK` at once, which left the one genuinely
   deteriorating company in the corpus reading `MODERATE` despite weak
   demand *and* weak margins.
3. All three are supported and all three are `STRONG` -> `STRONG`. All
   three, not merely all *supported* ones: durability is a three-clause
   concept, and a company whose margin clause cannot be answered has not
   demonstrated durability, it has demonstrated two thirds of it.
4. Anything else -> `MODERATE`.

A sub-assessment is *supported* only with two or more comparable
periods; one observation has nothing to be compared against.

**Duplicate facts.** Two records may report the same metric for the same
period (an original filing and a later restatement). Only one can be
used, and the choice is deterministic: the greatest
`(published_at, id)` wins, so a later-published figure supersedes the
earlier one, and ties fall back to the fact id rather than to input
order.

`confidence` reuses `EvidenceCoverageLevel` at the Finding level exactly
as Growth does: `FULL` (all three supported), `PARTIAL` (one or two),
`NONE` (durability-relevant facts exist but none reaches two periods),
`NOT_APPLICABLE` (no durability-relevant facts at all).
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import median

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
#: (operating margin is computed only where it is present); the rest each
#: gate one sub-assessment. `CASH`/`TOTAL_DEBT` are deliberately absent --
#: see the net-debt note in this module's docstring.
_SUPPORTED_KINDS = (
    BusinessFactKind.REVENUE,
    BusinessFactKind.NET_INCOME,
    BusinessFactKind.OPERATING_INCOME,
    BusinessFactKind.FREE_CASH_FLOW,
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

    __slots__ = ("values", "ids")

    def __init__(self, values: list[float], ids: list[str]) -> None:
        self.values, self.ids = values, ids

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
    return _Series([f.value for f in ordered], [f.id for f in ordered])


def _margin_series(numerator: dict[str, BusinessFact], revenue: dict[str, BusinessFact]) -> _Series:
    """Margin per period, for periods carrying both facts and strictly
    positive revenue. A margin on zero or negative revenue is not a small
    error, it is meaningless, so those periods are skipped entirely."""
    values, ids = [], []
    for period in sorted(set(numerator) & set(revenue)):
        denominator = revenue[period]
        if denominator.value <= 0:
            continue
        values.append(numerator[period].value / denominator.value)
        ids.append(f"{numerator[period].id}|{denominator.id}")
    return _Series(values, ids)


def _split_ids(compound: str) -> set[str]:
    return set(compound.split("|"))


def _classify_level_persistence(series: _Series) -> tuple[Status, set[str], set[str]]:
    """The shared demand/margin rule: where the latest observation sits
    against the series' own median and its own starting level.

    Evidence is attributed to the observations the judgment actually
    rests on -- the latest and the first -- never to every historical
    fact and never to every adverse delta. A `MODERATE` result genuinely
    populates both sides, because a split verdict is what it reports.
    """
    latest_ids, first_ids = _split_ids(series.ids[-1]), _split_ids(series.ids[0])
    latest = series.values[-1]
    meets_median = latest >= median(series.values)
    meets_start = latest >= series.values[0]

    supporting: set[str] = set()
    contradicting: set[str] = set()
    (supporting if meets_median else contradicting).update(latest_ids)
    (supporting if meets_start else contradicting).update(latest_ids | first_ids)

    if meets_median and meets_start:
        return Status.STRONG, supporting, contradicting
    if not meets_median and not meets_start:
        return Status.WEAK, supporting, contradicting
    return Status.MODERATE, supporting, contradicting


def _classify_positivity(series: _Series) -> tuple[Status, set[str], set[str]]:
    """Free cash flow's own rule. Unlike the persistence rule this reads
    each value on its own: a company that funded itself in every known
    period can survive a bad year whether or not the amount rose."""
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
    `BusinessFinding`, regardless of the order they arrive in. Reads only
    `BusinessFact` -- no `BusinessRecord`, no provider object, no
    document content, and no wall clock.
    """
    grouped = _facts_by_kind(facts)
    any_facts_at_all = any(grouped.values())

    revenue = grouped.get(BusinessFactKind.REVENUE, {})
    net_income = grouped.get(BusinessFactKind.NET_INCOME, {})
    operating_income = grouped.get(BusinessFactKind.OPERATING_INCOME, {})
    free_cash_flow = grouped.get(BusinessFactKind.FREE_CASH_FLOW, {})

    supporting: set[str] = set()
    contradicting: set[str] = set()
    missing: list[BusinessDataGapKind] = []
    supported: list[Status] = []

    # -- Demand durability -------------------------------------------
    demand = _series(revenue)
    if len(demand) >= _MINIMUM_PERIODS:
        status, plus, minus = _classify_level_persistence(demand)
        supported.append(status)
        supporting |= plus
        contradicting |= minus
    else:
        missing.append(BusinessDataGapKind.MISSING_REVENUE_HISTORY)

    # -- Margin durability -------------------------------------------
    margin_parts: list[Status] = []
    for numerator in (net_income, operating_income):
        margins = _margin_series(numerator, revenue)
        if len(margins) >= _MINIMUM_PERIODS:
            status, plus, minus = _classify_level_persistence(margins)
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
    cash_flow = _series(free_cash_flow)
    if len(cash_flow) >= _MINIMUM_PERIODS:
        status, plus, minus = _classify_positivity(cash_flow)
        supported.append(status)
        supporting |= plus
        contradicting |= minus
    else:
        missing.append(BusinessDataGapKind.MISSING_CASH_FLOW_HISTORY)

    # -- Overall (veto) -----------------------------------------------
    if not supported:
        status = Status.INSUFFICIENT_INPUT
        if any_facts_at_all:
            missing.append(BusinessDataGapKind.INSUFFICIENT_HISTORICAL_PERIODS)
    elif any(part is Status.WEAK for part in supported):
        status = Status.WEAK
    elif len(supported) == 3 and all(part is Status.STRONG for part in supported):
        status = Status.STRONG
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
