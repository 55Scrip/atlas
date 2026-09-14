"""The analysis methodology identity: which measuring rules produced a
result, so that Atlas changing how it measures is never presented as the
company changing.

`investment_case_change` already compares two snapshots on Financial Risk
or valuation only when both were taken under the same method. The Decision
Layer (readiness, decision, conviction, path, opportunity cost,
explanation, reliability, portfolio decision, decision memory) persists
each Case's previous result and diffs the fresh one against it -- which,
across Financial Risk v2 and the fiscal-epoch valuation history, turned
the method changes into "Recommendation changed from hold to reduce" in
the Daily Brief. Each persisted result is therefore stamped with this
identity, and a result stamped with another one (or none: written before
the stamp existed) is not a previous result to diff against. The fresh
result is still computed and stored, so the current state always reflects
the new method; only the "what changed" narration is re-baselined, once
per method change. A real company change landing in the same computation
as a method change is re-baselined with it -- the price of never
narrating a method change as news.

A new method joins `_COMPONENTS` with its own named constant.
"""
from __future__ import annotations

import json

from atlas.analysis_engine.business_facts.growth_primitives import ROLLING_GROWTH_METHODOLOGY
from atlas.analysis_engine.outlook import OUTLOOK_METHODOLOGY
from atlas.analysis_engine.risk.financial_risk import FINANCIAL_RISK_METHODOLOGY
from atlas.analysis_engine.valuation.cash_flow import VALUATION_METHODOLOGY

__all__ = ["ANALYSIS_METHODOLOGY", "METHODOLOGY_KEY", "stamp_methodology", "comparable_payload"]

_COMPONENTS = {
    "financial_risk": FINANCIAL_RISK_METHODOLOGY,
    # fiscal_epoch_v3 over the issuer common-equity denominator and the
    # common-attributable numerator: one identity, so a change to any of
    # the three re-baselines once rather than narrating a new ruler as news.
    "valuation": VALUATION_METHODOLOGY,
    "rolling_growth": ROLLING_GROWTH_METHODOLOGY,
    # Outlook became a sensitivity and left Portfolio Fit, which the
    # Decision Layer reads through Stance.
    "outlook": OUTLOOK_METHODOLOGY,
}

ANALYSIS_METHODOLOGY = ";".join(f"{name}={method}" for name, method in sorted(_COMPONENTS.items()))

#: The key a persisted result's JSON payload carries the identity under.
METHODOLOGY_KEY = "analysisMethodology"


def stamp_methodology(payload: dict) -> dict:
    """`payload`, stamped with the methodology that produced it."""
    return {**payload, METHODOLOGY_KEY: ANALYSIS_METHODOLOGY}


def comparable_payload(result_json: str) -> dict | None:
    """A stored result's payload, or `None` when it was written under
    another methodology (or before results were stamped) and so is no
    baseline for a change today."""
    payload = json.loads(result_json)
    return payload if payload.get(METHODOLOGY_KEY) == ANALYSIS_METHODOLOGY else None
