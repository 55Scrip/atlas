"""Where the FCF-yield method applies (Valuation Observation Integrity).

Free cash flow is operating cash flow less capital expenditure. For a bank,
a dealer or an insurer, operating cash flow is not the cash the business
earns: it moves with deposits, trading inventories and policyholder flows,
and GS's swung by tens of billions in a single year. A yield on that figure
would be a confident, meaningless valuation.

That is the same reason Financial Risk v2 keeps its debt-to-operating-cash-
flow measure away from these businesses, so the line is drawn once, from the
company-profile industry, in `risk.applicability` -- reused here, never
restated, so the two measures cannot drift apart. Payment networks and data
providers ("CREDIT SERVICES", "FINANCIAL DATA & STOCK EXCHANGES") are
operating businesses and stay applicable; the rule follows the industry
label and never names a company.

`None` when no industry is recorded: applicability cannot be established,
and the evaluator reports that rather than assuming either way.
"""
from __future__ import annotations

from atlas.analysis_engine.risk.applicability import debt_burden_measure_applies

__all__ = ["fcf_yield_applies"]


def fcf_yield_applies(industry: str | None) -> bool | None:
    """`True`/`False` for a known industry; `None` when none is recorded."""
    return debt_burden_measure_applies(industry)
