"""Growth evaluator v1 (ATLAS-023, Phase 5) -- Atlas's first Business
Analysis category evaluator that can genuinely reach `WEAK`/`MODERATE`/
`STRONG`, from real `BusinessFact`s only.

**The rule table, documented before it was implemented (Phase 5's own
requirement):**

For each of the two supported metrics (`REVENUE`, `FREE_CASH_FLOW`),
sort that metric's facts by `period` and compute every consecutive-period
delta's sign -- `POSITIVE` (`current > previous`), `NEGATIVE`
(`current < previous`), or `FLAT` (`current == previous`). A metric with
fewer than two periods has no delta at all and is excluded from
everything below. Per metric, classify:

- `STRONG_METRIC` -- every delta is `POSITIVE`.
- `WEAK_METRIC` -- every delta is `NEGATIVE`.
- `MIXED_METRIC` -- anything else (any `FLAT`, or a mix of signs).

Let `supported` be the set of metrics with two or more periods. Then,
in this fixed order, first match wins:

1. `supported` is empty -> `INSUFFICIENT_INPUT`.
2. Every metric in `supported` is `STRONG_METRIC`, and both Revenue and
   Free Cash Flow are in `supported` -> `STRONG`. Requiring *both*
   metrics, not one, is a deliberate choice: "broad-based" growth
   (Doctrine's own framing) means more than one independent metric
   corroborating the same direction -- a single strong metric, however
   consistent, stays at `MODERATE` below rather than reaching the top
   tier alone.
3. Every metric in `supported` is `WEAK_METRIC` -> `WEAK`, whether one
   or two metrics are supported -- contraction is contraction regardless
   of how many metrics happened to be reported.
4. Anything else (a single strong metric alone, or the supported
   metrics disagreeing, or any metric itself `MIXED_METRIC`) ->
   `MODERATE`.

The only comparisons anywhere in this table are `>`, `<`, and `==` on
real extracted values -- no threshold, no percentage cutoff, no weight,
nothing invented.

`confidence` reuses `EvidenceCoverageLevel` at the Finding level, where
its "how much of the expected input is covered" semantics genuinely
fit: `FULL` (both metrics supported), `PARTIAL` (one metric supported),
`NONE` (some facts exist but no metric reaches two periods),
`NOT_APPLICABLE` (no Growth-relevant facts exist at all).
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from enum import Enum

from atlas.analysis_engine.business_contracts import (
    BusinessCategory,
    BusinessDataGapKind,
    BusinessFinding,
    severity_for_status,
)
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus as Status
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.growth_primitives import rolling_growth_observations
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
from atlas.decision_engine.contracts import EvidenceCoverageLevel

__all__ = ["evaluate_growth", "MetricTrend", "classify_metric_trend"]

_SUPPORTED_KINDS = (BusinessFactKind.REVENUE, BusinessFactKind.FREE_CASH_FLOW)

_MISSING_HISTORY_REASON = {
    BusinessFactKind.REVENUE: BusinessDataGapKind.MISSING_REVENUE_HISTORY,
    BusinessFactKind.FREE_CASH_FLOW: BusinessDataGapKind.MISSING_CASH_FLOW_HISTORY,
}

_ALL_CONSUMERS = (
    Consumer.PORTFOLIO_PAGE,
    Consumer.INVESTMENT_CASE_PAGE,
    Consumer.DISCOVERY,
    Consumer.HISTORY,
)


class MetricTrend(str, Enum):
    STRONG_METRIC = "strong_metric"
    WEAK_METRIC = "weak_metric"
    MIXED_METRIC = "mixed_metric"


def _facts_by_kind(facts: tuple[BusinessFact, ...]) -> dict[BusinessFactKind, list[BusinessFact]]:
    grouped: dict[BusinessFactKind, list[BusinessFact]] = defaultdict(list)
    for fact in facts:
        if fact.kind in _SUPPORTED_KINDS:
            grouped[fact.kind].append(fact)
    for kind_facts in grouped.values():
        kind_facts.sort(key=lambda f: f.period)
    return grouped


def classify_metric_trend(kind_facts: list[BusinessFact]) -> tuple[MetricTrend, tuple[str, ...], tuple[str, ...]]:
    """Returns the metric's trend plus the fact ids that supported it
    (participated in a `POSITIVE` delta) and contradicted it
    (participated in a `NEGATIVE` delta) -- a fact can appear in both
    if it is the shared endpoint of two oppositely-signed deltas.

    Public (Investment Case Engine v1 slice) so
    `atlas.analysis_engine.investment_case_synthesis` can apply the
    identical, already-documented trend rule to a shorter, "most
    recent periods" window for narrative purposes, without a second,
    competing trend algorithm. `kind_facts` must already be sorted by
    `period` ascending -- this function does not sort, matching
    `evaluate_growth`'s own pre-sorted call site."""
    supporting: set[str] = set()
    contradicting: set[str] = set()
    signs: list[int] = []
    for previous, current in zip(kind_facts, kind_facts[1:]):
        if current.value > previous.value:
            signs.append(1)
            supporting.update((previous.id, current.id))
        elif current.value < previous.value:
            signs.append(-1)
            contradicting.update((previous.id, current.id))
        else:
            signs.append(0)

    if all(sign > 0 for sign in signs):
        trend = MetricTrend.STRONG_METRIC
    elif all(sign < 0 for sign in signs):
        trend = MetricTrend.WEAK_METRIC
    else:
        trend = MetricTrend.MIXED_METRIC

    return trend, tuple(sorted(supporting)), tuple(sorted(contradicting))


def _full_span_cagr(kind_facts: list[BusinessFact]) -> float | None:
    """First-to-last compound annual growth rate, or `None` where no
    principled rate exists.

    Delegates the arithmetic and every edge case to
    `growth_primitives.rolling_growth_observations`, the primitive
    Outlook already uses -- called with `years = len - 1` so it yields
    exactly one observation spanning the whole series. Reusing it
    rather than repeating the formula means the positivity guard is
    shared: an observation is emitted only when both endpoints are
    strictly positive, so a zero or negative start or end produces
    `None` instead of a fabricated rate. Free Cash Flow legitimately
    crosses zero for real companies, and a compound rate across a sign
    change is not a small error -- it is meaningless.

    `kind_facts` arrives sorted ascending by period from
    `_facts_by_kind`, which sorts explicitly; this function does not
    re-sort, matching `classify_metric_trend`'s own contract.

    Periods are treated as one step apart, exactly as
    `rolling_growth_observations` already treats them everywhere else
    in this codebase. `BusinessFact.period` is a string, so no calendar
    arithmetic is available here and none is invented.
    """
    if len(kind_facts) < 2:
        return None
    observations = rolling_growth_observations(kind_facts, years=len(kind_facts) - 1)
    return observations[0].rate if observations else None


def _confidence(supported_count: int, any_facts_at_all: bool) -> EvidenceCoverageLevel:
    if supported_count == len(_SUPPORTED_KINDS):
        return EvidenceCoverageLevel.FULL
    if supported_count == 1:
        return EvidenceCoverageLevel.PARTIAL
    if any_facts_at_all:
        return EvidenceCoverageLevel.NONE
    return EvidenceCoverageLevel.NOT_APPLICABLE


def evaluate_growth(facts: tuple[BusinessFact, ...], *, evaluated_at: datetime) -> BusinessFinding:
    """Deterministic: identical `facts` always produce a deeply equal
    `BusinessFinding`. Reads only `BusinessFact` -- no
    `BusinessRecord`, no provider object, no document content anywhere
    in this function.
    """
    grouped = _facts_by_kind(facts)
    any_facts_at_all = any(grouped.values())

    trends: dict[BusinessFactKind, MetricTrend] = {}
    supporting_ids: set[str] = set()
    contradicting_ids: set[str] = set()
    missing: list[BusinessDataGapKind] = []

    for kind in _SUPPORTED_KINDS:
        kind_facts = grouped.get(kind, [])
        if len(kind_facts) < 2:
            missing.append(_MISSING_HISTORY_REASON[kind])
            continue
        trend, supports, contradicts = classify_metric_trend(kind_facts)
        trends[kind] = trend
        supporting_ids.update(supports)
        contradicting_ids.update(contradicts)

    if not trends:
        status = Status.INSUFFICIENT_INPUT
        missing = [BusinessDataGapKind.INSUFFICIENT_HISTORICAL_PERIODS, *missing]
    elif all(t is MetricTrend.STRONG_METRIC for t in trends.values()) and set(trends) == set(_SUPPORTED_KINDS):
        status = Status.STRONG
    elif all(t is MetricTrend.WEAK_METRIC for t in trends.values()):
        status = Status.WEAK
    else:
        status = Status.MODERATE

    confidence = _confidence(len(trends), any_facts_at_all)

    # Computed from the same `grouped` series the classifier already
    # read. Purely additive: neither value can reach `status` above,
    # which is decided before this line runs.
    revenue_cagr = _full_span_cagr(grouped.get(BusinessFactKind.REVENUE, []))
    free_cash_flow_cagr = _full_span_cagr(grouped.get(BusinessFactKind.FREE_CASH_FLOW, []))

    return BusinessFinding(
        id="business_finding:growth",
        kind=BusinessCategory.GROWTH,
        status=status,
        severity=severity_for_status(status),
        supporting_evidence=tuple(sorted(supporting_ids)),
        contradicting_evidence=tuple(sorted(contradicting_ids)),
        missing_evidence=tuple(missing),
        confidence=confidence,
        provenance=Provenance(
            source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
            source_references=tuple(sorted(supporting_ids | contradicting_ids)),
            dependencies=tuple(sorted({fact.id for kind_facts in grouped.values() for fact in kind_facts})),
            update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
            consumers=_ALL_CONSUMERS,
            computed_at=evaluated_at,
        ),
        updated_at=evaluated_at,
        revenue_cagr=revenue_cagr,
        free_cash_flow_cagr=free_cash_flow_cagr,
    )
