"""Valuation-native Scenario eligibility (`DE-015` §9).

Implements the adopted Historical Persistence Doctrine's three conditions
using raw `BusinessFact`s only:

1. At least two real, revenue-corroborated rolling growth observations
   must exist (`growth_primitives.rolling_growth_observations` +
   `.corroborated_by` -- a statistical floor, not a threshold: a range
   cannot exist from fewer than two points).
2. Revenue corroboration itself (the same call, exact-membership).
3. The valuation domain, reading raw facts only, refuses extrapolation
   when full-history evidence shows no legitimate growth basis.

**Condition 3's exact rule, and why this is not an invented alternative.**
`DE-015` §9 condition 3 mirrors Outlook's own, already-adopted
`growth_status is not WEAK` floor -- but `DE-015` §10 forbids reading
`BusinessCategoryStatus` (Business Analysis's own interpreted conclusion)
to get it. `atlas.analysis_engine.growth`'s own WEAK rule is itself
precisely defined and already exported for exactly this kind of reuse:
"every metric in `supported` [Revenue or Free Cash Flow with >=2 real
periods] is `WEAK_METRIC`" (`growth.py`'s own module docstring, rule 3).
This module recomputes that identical rule directly from raw facts, via
the same mechanical `classify_metric_trend` `outlook.py` already reuses
across domain lines -- never by calling `evaluate_growth` or reading its
`BusinessFinding.status`. No other candidate rule was considered
plausible enough to create genuine doctrine ambiguity: any rule *other*
than growth.py's own already-adopted WEAK definition would itself be a
new, uninvestigated growth-quality judgment, exactly what `DE-015` §9's
own closing sentence rules out ("No other condition is adopted").
Mirroring the one rule this codebase has already tested and adopted,
computed independently, is not a choice between competing plausible
rules -- it is the only rule with any real precedent behind it.

**Horizon.** `SCENARIO_HORIZON_YEARS` is independently affirmed here as a
Valuation-domain choice, not inherited from `outlook.py`'s own
`LONG_TERM_COMPOUNDING_YEARS` constant, per `DE-015` §17's "domains may
legitimately diverge" -- it happens to use the identical value (4) because
no other value has any better claim to it, not because this module reads
Outlook's constant.

Returns an internal, non-exported `EligibilityResult` -- see this
package's own `support.py` for the public contract this feeds into. No
`BusinessCategoryStatus`, `BusinessFinding`, or any other Business
Analysis conclusion is imported anywhere in this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.growth_primitives import (
    GrowthObservation,
    corroborated_by,
    exclude_future_dated,
    real_periods,
    rolling_growth_observations,
    sorted_facts_of_kind,
)
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.growth import MetricTrend, classify_metric_trend

__all__ = ["SCENARIO_HORIZON_YEARS", "IneligibilityReason", "EligibilityResult", "evaluate_scenario_eligibility"]

#: Independently affirmed Valuation-domain horizon -- see module docstring.
SCENARIO_HORIZON_YEARS = 4

#: The statistical floor a range needs to exist at all -- not a threshold.
_MINIMUM_CORROBORATED_OBSERVATIONS = 2


class IneligibilityReason(str, Enum):
    """Internal only -- mapped to a public `ValuationSupportGapKind` by
    the orchestrator in `support.py`, never exposed directly."""

    NO_LEGITIMATE_GROWTH_BASIS = "no_legitimate_growth_basis"
    INSUFFICIENT_CORROBORATED_OBSERVATIONS = "insufficient_corroborated_observations"


@dataclass(frozen=True)
class EligibilityResult:
    eligible: bool
    corroborated_growth_observations: tuple[GrowthObservation, ...]
    ineligibility_reason: IneligibilityReason | None

    def __post_init__(self) -> None:
        if self.eligible and self.ineligibility_reason is not None:
            raise ValueError("EligibilityResult cannot be eligible and carry an ineligibility_reason.")
        if not self.eligible and self.ineligibility_reason is None:
            raise ValueError("EligibilityResult must carry an ineligibility_reason when not eligible.")


def _no_legitimate_growth_basis(business_facts: tuple[BusinessFact, ...], *, generated_at: datetime) -> bool:
    """Mirrors `growth.py`'s own `WEAK` rule -- see this module's own
    docstring for why this is the one, already-adopted rule, not an
    invented alternative. Returns `False` (not refused) whenever no
    metric has enough real periods to classify at all -- absence of data
    is a separate, `INSUFFICIENT_INPUT`-shaped fact, never itself treated
    as evidence of decline."""
    supported_trends: list[MetricTrend] = []
    for kind in (BusinessFactKind.REVENUE, BusinessFactKind.FREE_CASH_FLOW):
        facts = exclude_future_dated(sorted_facts_of_kind(business_facts, kind), as_of=generated_at)
        if len(facts) < 2:
            continue
        trend, _supporting, _contradicting = classify_metric_trend(facts)
        supported_trends.append(trend)
    if not supported_trends:
        return False
    return all(trend is MetricTrend.WEAK_METRIC for trend in supported_trends)


def evaluate_scenario_eligibility(
    business_facts: tuple[BusinessFact, ...], *, years: int = SCENARIO_HORIZON_YEARS, generated_at: datetime
) -> EligibilityResult:
    """Deterministic: identical `business_facts`/`generated_at` always
    produce an identical result. Reads only raw `BusinessFact`s."""
    if _no_legitimate_growth_basis(business_facts, generated_at=generated_at):
        return EligibilityResult(
            eligible=False,
            corroborated_growth_observations=(),
            ineligibility_reason=IneligibilityReason.NO_LEGITIMATE_GROWTH_BASIS,
        )

    fcf_facts = exclude_future_dated(
        sorted_facts_of_kind(business_facts, BusinessFactKind.FREE_CASH_FLOW), as_of=generated_at
    )
    revenue_facts = exclude_future_dated(
        sorted_facts_of_kind(business_facts, BusinessFactKind.REVENUE), as_of=generated_at
    )
    fcf_growth_observations = rolling_growth_observations(fcf_facts, years=years)
    revenue_periods = real_periods(revenue_facts)
    corroborated = corroborated_by(fcf_growth_observations, revenue_periods)

    if len(corroborated) < _MINIMUM_CORROBORATED_OBSERVATIONS:
        return EligibilityResult(
            eligible=False,
            corroborated_growth_observations=corroborated,
            ineligibility_reason=IneligibilityReason.INSUFFICIENT_CORROBORATED_OBSERVATIONS,
        )

    return EligibilityResult(eligible=True, corroborated_growth_observations=corroborated, ineligibility_reason=None)
