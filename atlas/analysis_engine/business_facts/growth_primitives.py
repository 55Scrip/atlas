"""Shared, opinion-free analytical primitives (`DE-015` §17) -- the
"shared descriptive analytical primitive" layer `DE-015` requires to sit
between raw `BusinessFact`s and any domain (Valuation, Outlook) that wants
to reason about realized, multi-period growth without owning a second copy
of the same rolling-window/corroboration arithmetic.

**This module computes facts about facts. It never interprets them.**
Every function here answers a question of the form "what does the data
literally say," never "is that enough," "which extreme is favorable," or
"what should Atlas conclude." Concretely, this module contains, and will
never contain:

- eligibility (a `≥2 observations` floor, a "no legitimate growth basis"
  refusal, or any other sufficiency judgment) -- each domain applies its
  own;
- scenario labels (`Bull`/`Base`/`Bear`, `SUPPORTED`/`NOT_SUPPORTED`) --
  domain-owned;
- `ValuationSupport`/Outlook/Business status of any kind;
- proof logic of any kind;
- a numeric hurdle, threshold, or fabricated assumption of any kind.

**Why this lives in `business_facts`, not `valuation/` or as a new
top-level package.** This package's own module docstring already states
its purpose precisely: "produces no findings, no conclusions... Reusable
by design... a future Valuation stage can read the identical facts Growth
already extracts, without this package or its taxonomy needing to
change." That is exactly this module's role, one layer up (rolling
statistics over facts, not the facts themselves) -- not a new home, the
natural extension of an already-adopted one.

**Provenance.** Every function here is extracted, not reinvented, from
`atlas.analysis_engine.outlook`'s own already-real, already-tested
rolling-CAGR/revenue-corroboration/future-date-exclusion/annualized-return
math (Calibration Sprint). `outlook.py` is **not** refactored to call this
module in this sprint -- its own private implementations are left
untouched, per the explicit instruction to prefer additive extraction over
unrelated churn. A future sprint may migrate `outlook.py` onto this module
without changing its observable behavior; that migration is out of this
sprint's scope.

**Not exported here:** metric-trend classification
(`atlas.analysis_engine.growth.classify_metric_trend`/`MetricTrend`).
That function is already a neutral, mechanical, raw-fact-only classifier
(consecutive-period delta signs -> `STRONG_METRIC`/`WEAK_METRIC`/
`MIXED_METRIC` -- never `BusinessCategoryStatus`), and is already reused
directly across domain lines by `outlook.py` today. Re-extracting it here
would duplicate, not clarify, an already-established, already-neutral
utility; the valuation-native eligibility rule (`valuation/eligibility.py`)
imports it the same way `outlook.py` already does.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime

from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact

__all__ = [
    "GrowthObservation",
    "DistributionSummary",
    "sorted_facts_of_kind",
    "exclude_future_dated",
    "real_periods",
    "rolling_growth_observations",
    "corroborated_by",
    "distribution_summary",
    "compound_and_reprice_return",
]


def sorted_facts_of_kind(facts: tuple[BusinessFact, ...], kind: BusinessFactKind) -> list[BusinessFact]:
    """Every real fact of one kind, sorted by `period` ascending --
    the same one-line filter+sort every caller of this module needs
    before doing anything else, written once."""
    return sorted((f for f in facts if f.kind is kind), key=lambda f: f.period)


def exclude_future_dated(facts_sorted_asc: list[BusinessFact], *, as_of: datetime) -> list[BusinessFact]:
    """A `period` ending after `as_of` cannot be a *realized* historical
    observation by definition. Extracted verbatim from
    `outlook.py::_exclude_future_dated` -- see that function's own
    docstring for the real data-integrity bug this guard was written to
    make structurally unreachable, independent of whether the
    contaminating record itself is ever cleaned up."""
    cutoff = as_of.date().isoformat()
    return [f for f in facts_sorted_asc if f.period <= cutoff]


def real_periods(facts_sorted_asc: list[BusinessFact]) -> frozenset[str]:
    """The exact set of periods a real fact series actually covers --
    used for exact-membership corroboration (`corroborated_by`), never a
    bounds check (earliest-to-latest), since a bounds check would wrongly
    treat a genuine multi-year ingestion gap as covered."""
    return frozenset(f.period for f in facts_sorted_asc)


@dataclass(frozen=True)
class GrowthObservation:
    """One rolling-window growth-rate observation -- a fact about the
    data, not a conclusion. `rate` is a plain compound annual growth
    rate between two real, positive-valued facts exactly `years` apart."""

    start_period: str
    end_period: str
    rate: float


def rolling_growth_observations(
    facts_sorted_asc: list[BusinessFact], *, years: int
) -> tuple[GrowthObservation, ...]:
    """Every `(start, end, rate)` triple for facts exactly `years` apart
    in the sorted sequence where both endpoints are positive -- extracted
    verbatim from `outlook.py::_rolling_cagr_observations`. A single
    noisy period can no longer swing the whole distribution the way a raw
    year-over-year delta could; each observation already smooths `years`
    worth of timing noise."""
    observations: list[GrowthObservation] = []
    for i in range(len(facts_sorted_asc) - years):
        start, end = facts_sorted_asc[i], facts_sorted_asc[i + years]
        if start.value > 0 and end.value > 0:
            rate = (end.value / start.value) ** (1.0 / years) - 1.0
            observations.append(GrowthObservation(start.period, end.period, rate))
    return tuple(observations)


def corroborated_by(
    observations: tuple[GrowthObservation, ...], corroborating_periods: frozenset[str]
) -> tuple[GrowthObservation, ...]:
    """The subset of `observations` whose both endpoints are present in
    an independent fact series's own real period set -- exact per-period
    membership, never a bounds check (see `real_periods`). Extracted
    verbatim from `outlook.py::_revenue_corroborated_growth_rates`'s own
    filtering logic, generalized beyond Revenue-specifically: this
    function does not know or care which metric supplied the
    corroborating periods, only that they are real."""
    return tuple(
        obs for obs in observations if obs.start_period in corroborating_periods and obs.end_period in corroborating_periods
    )


@dataclass(frozen=True)
class DistributionSummary:
    """Plain descriptive statistics over a real, non-empty number
    sequence -- no label, no meaning, no Bull/Bear assignment. Assigning
    economic meaning to `minimum`/`maximum` (e.g. "Bull means the
    maximum") is each domain's own, separately-owned decision."""

    minimum: float
    median: float
    maximum: float


def distribution_summary(values: tuple[float, ...]) -> DistributionSummary | None:
    """`None` when `values` is empty -- there is no distribution to
    describe, and this module never invents one."""
    if not values:
        return None
    return DistributionSummary(minimum=min(values), median=statistics.median(values), maximum=max(values))


def compound_and_reprice_return(
    *, current_value: float, growth_rate: float, years: int, terminal_value: float
) -> float:
    """`((1+g)**years) * (current_value/terminal_value)` is the total
    -return multiple; its own `years`-th root minus one annualizes it.
    Extracted and generalized from `outlook.py::_annualized_return` --
    `terminal_value` is a real parameter here (not fixed), so a caller
    may vary it exactly as freely as `growth_rate`. Pure arithmetic: no
    eligibility, no scenario labeling, no sign judgment beyond the
    defensive `<= 0` guard already present in the source this was
    extracted from."""
    total_multiple = ((1.0 + growth_rate) ** years) * (current_value / terminal_value)
    if total_multiple <= 0:
        return -1.0
    return total_multiple ** (1.0 / years) - 1.0
