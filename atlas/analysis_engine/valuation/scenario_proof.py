"""Scenario proof path (`DE-015` §11, §12) -- the valuation-owned,
forward-looking proof path.

**Envelope construction, per `DE-015` §11's own resolved question.**
Growth and terminal valuation are each independently ranged (never a
fabricated point, never probability-weighted), and combined as the full,
independent envelope -- never a matched-narrative pairing (`DE-015` §20
rejected alternative 6). Bull = the most favorable growth observation
compounded and re-priced at the most favorable (lowest, richest) real
historical yield; Bear = the least favorable growth observation compounded
and re-priced at the least favorable (highest, cheapest) real historical
yield. This is deliberately wider than a matched-extreme construction
would be -- accepted per `DE-015` §11's own instruction, not corrected
for.

**Proof semantics, per `DE-015` §12.** The full envelope's low end above
zero -> `ESTABLISHES_SUPPORT` (even the adverse case avoids a nominal
loss). The full envelope's high end below zero -> `ESTABLISHES_NON_SUPPORT`
(even the optimistic case remains a loss). Any straddle, or ineligibility,
or missing yield data -> `DOES_NOT_ESTABLISH`. No numeric threshold, no
probability, no required return anywhere in this module.

**No Outlook import.** This module never imports
`atlas.analysis_engine.outlook` or any of its types
(`ExpectedReturnRange`/`OutlookScenario`/`HorizonOutlook`) -- it computes
its own envelope, independently, from the shared primitive
(`business_facts.growth_primitives`) and the valuation-native eligibility
gate (`eligibility.py`) alone.
"""
from __future__ import annotations

from datetime import datetime

from atlas.analysis_engine.business_facts.growth_primitives import compound_and_reprice_return, distribution_summary
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.valuation.eligibility import SCENARIO_HORIZON_YEARS, evaluate_scenario_eligibility
from atlas.analysis_engine.valuation.proof import PathProof, ProofVerdict

__all__ = ["PATH_NAME", "evaluate_scenario_proof"]

PATH_NAME = "scenario"


def evaluate_scenario_proof(
    business_facts: tuple[BusinessFact, ...],
    *,
    current_yield: float | None,
    historical_yields: tuple[float, ...],
    generated_at: datetime,
) -> PathProof:
    """Deterministic: identical inputs always produce an identical
    `PathProof`. `current_yield`/`historical_yields` are read verbatim
    from the already-computed `FCF_YIELD_RELATIVE` `ValuationFinding` --
    real facts already exposed there, never recomputed."""
    eligibility = evaluate_scenario_eligibility(business_facts, generated_at=generated_at)
    if not eligibility.eligible:
        return PathProof(
            path_name=PATH_NAME,
            verdict=ProofVerdict.DOES_NOT_ESTABLISH,
            evidence_summary=f"ineligible:{eligibility.ineligibility_reason.value}",
        )

    if current_yield is None:
        return PathProof(
            path_name=PATH_NAME, verdict=ProofVerdict.DOES_NOT_ESTABLISH, evidence_summary="no_current_yield"
        )

    yield_summary = distribution_summary(historical_yields)
    if yield_summary is None:
        return PathProof(
            path_name=PATH_NAME, verdict=ProofVerdict.DOES_NOT_ESTABLISH, evidence_summary="no_historical_yield_range"
        )

    growth_rates = tuple(obs.rate for obs in eligibility.corroborated_growth_observations)
    growth_summary = distribution_summary(growth_rates)
    assert growth_summary is not None  # eligibility already guarantees >=2 observations

    # Lower terminal yield <-> richer valuation <-> higher implied return,
    # so the most favorable growth paired with the lowest historical
    # yield is Bull; the least favorable growth paired with the highest
    # historical yield is Bear -- see this module's own docstring.
    bull_return = compound_and_reprice_return(
        current_value=current_yield,
        growth_rate=growth_summary.maximum,
        years=SCENARIO_HORIZON_YEARS,
        terminal_value=yield_summary.minimum,
    )
    bear_return = compound_and_reprice_return(
        current_value=current_yield,
        growth_rate=growth_summary.minimum,
        years=SCENARIO_HORIZON_YEARS,
        terminal_value=yield_summary.maximum,
    )
    low = min(bear_return, bull_return)
    high = max(bear_return, bull_return)

    if low > 0:
        verdict = ProofVerdict.ESTABLISHES_SUPPORT
    elif high < 0:
        verdict = ProofVerdict.ESTABLISHES_NON_SUPPORT
    else:
        verdict = ProofVerdict.DOES_NOT_ESTABLISH

    return PathProof(
        path_name=PATH_NAME,
        verdict=verdict,
        evidence_summary=f"envelope_low={low:.6f};envelope_high={high:.6f}",
    )
