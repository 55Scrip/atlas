"""The Business Fact taxonomy (ATLAS-023, Phase 3; extended Company
Data Foundation v1).

Not the full speculative list either Growth or Capital Allocation could
theoretically use -- only what a real evaluator genuinely needs, or (for
the six Company Data Foundation v1 additions below) what the Investment
Case's own Financials view needs to render as real, traceable structured
facts even before a future evaluator reads them. No `_GROWTH` suffixed
members exist here (no `REVENUE_GROWTH`, no `FREE_CASH_FLOW_GROWTH`): a
growth rate is a real computation over two consecutive-period
`REVENUE`/`FREE_CASH_FLOW` facts, performed once, inside
`atlas.analysis_engine.growth` itself -- persisting it as a second fact
kind would just be redundant derived data with its own staleness
problem, not a new atomic fact. `REVENUE`/`FREE_CASH_FLOW` are
deliberately generic enough that a future Valuation stage can read them
too, without this package or its taxonomy needing to know that consumer
exists.

**Company Data Foundation v1: `OPERATING_INCOME`/`NET_INCOME`/`EPS`/
`CASH`/`TOTAL_DEBT`/`SHARES_OUTSTANDING` added.** `SHARES_OUTSTANDING`
is deliberately informational-only in Capital Allocation v1 (share-count
movement, alongside `CAPITAL_EXPENDITURE`/`DIVIDENDS`) and `TOTAL_DEBT`
drives only a narrow, escalation-only signal in Financial Risk (see
`atlas.analysis_engine.risk.financial_risk`'s own module docstring for
why) -- neither reopens Growth's own two-metric `STRONG` rule, which
still requires exactly `REVENUE`+`FREE_CASH_FLOW` (see `growth.py`'s own
docstring for why a third metric is not folded into that rule this
sprint: doing so would silently downgrade every company's confidence
from `FULL` to `PARTIAL` the moment `EPS` exists as a fact kind but is
not yet populated for that company, a real regression this sprint
deliberately avoids). `OPERATING_INCOME`/`NET_INCOME`/`EPS` are not
consumed by any evaluator yet -- they exist so the Investment Case's own
Financials view can show real income-statement data, and so a future
sprint building a P/E-style Valuation method has the raw input already
flowing through the pipeline rather than needing a second data-foundation
sprint first.
"""
from __future__ import annotations

from enum import Enum

__all__ = ["BusinessFactKind"]


class BusinessFactKind(str, Enum):
    """A closed, growing set -- a future evaluator that needs a new
    atomic fact adds a member here, the same discipline every other
    closed taxonomy in this codebase already follows
    (`atlas.analysis_engine.business_data.sources.SourceKind`,
    `atlas.decision_engine.contracts.EvidenceGapKind`)."""

    # -- Growth v1 -------------------------------------------------------
    REVENUE = "revenue"
    FREE_CASH_FLOW = "free_cash_flow"

    # -- Capital Allocation v1 --------------------------------------------
    CAPITAL_EXPENDITURE = "capital_expenditure"
    SHARE_BUYBACKS = "share_buybacks"
    SHARE_ISSUANCE = "share_issuance"
    DIVIDENDS = "dividends"
    DEBT_ISSUANCE = "debt_issuance"
    DEBT_REPAYMENT = "debt_repayment"

    # -- Company Data Foundation v1 ---------------------------------------
    OPERATING_INCOME = "operating_income"
    """Not yet consumed by any evaluator -- real income-statement data
    for the Investment Case's own Financials view, and raw input for a
    future Valuation/Business Analysis method."""
    NET_INCOME = "net_income"
    """Not yet consumed by any evaluator -- same status as
    `OPERATING_INCOME` above."""
    EPS = "eps"
    """Not yet consumed by any evaluator; see `growth.py`'s own
    docstring for why a third Growth metric is not wired this sprint."""
    CASH = "cash"
    """Not yet a Financial Risk signal on its own (see
    `financial_risk.py`'s own module docstring) -- real balance-sheet
    data for the Financials view, and the numerator a future
    principled net-cash-position rule would need."""
    TOTAL_DEBT = "total_debt"
    """Drives Financial Risk's own escalation-only debt-trend signal
    (see `financial_risk.py`) -- never a leverage ratio, never a
    fabricated threshold."""
    SHARES_OUTSTANDING = "shares_outstanding"
    """Capital Allocation v1: informational only, alongside
    `CAPITAL_EXPENDITURE`/`DIVIDENDS` -- presence/absence is recorded,
    never drives `status`. A real per-fiscal-period historical count
    from SEC EDGAR, deliberately distinct from `atlas.analysis_engine
    .valuation.facts.ValuationFactKind.SHARES_OUTSTANDING` (Alpha
    Vantage's current, today-only figure)."""
