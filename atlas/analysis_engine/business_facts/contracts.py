"""The Business Fact taxonomy (ATLAS-023, Phase 3).

Eight members, not the full speculative list either Growth or Capital
Allocation could theoretically use -- only what the Phase 1 audit
confirmed this sprint's two evaluators genuinely need. No `_GROWTH`
suffixed members exist here (no `REVENUE_GROWTH`, no
`FREE_CASH_FLOW_GROWTH`): a growth rate is a real computation over two
consecutive-period `REVENUE`/`FREE_CASH_FLOW` facts, performed once,
inside `atlas.analysis_engine.growth` itself -- persisting it as a
second fact kind would just be redundant derived data with its own
staleness problem, not a new atomic fact. `REVENUE`/`FREE_CASH_FLOW`
are deliberately generic enough that a future Valuation stage can read
them too, without this package or its taxonomy needing to know that
consumer exists.
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
