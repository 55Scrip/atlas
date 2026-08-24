"""HTTP response schema for the Investment Case page's Decision Layer
Bundle (Opportunity Cost Cross-Case Computation Review, follow-up
implementation sprint).

Purely additive and purely compositional: every field reuses the
existing, unmodified `*View.from_domain` classmethods from
`opportunity_cost`/`decision_memory`/`decision_explanation`/
`portfolio_decision`'s own `api/schemas.py` modules -- nothing is
recomputed or reworded here, and none of those four packages' own
existing endpoints are changed.

Each of the five fields is independently nullable, matching the exact
failure-isolation behavior the four separate endpoints already have
today (each "renders nothing" on a genuine absence or an unexpected
error, never blocking the others) -- see this schema's own `from_parts`
docstring for why the router builds each field independently rather
than failing the whole response if one part raises.
"""
from __future__ import annotations

from atlas.alpha.decision_explanation.api.schemas import DecisionExplanationView
from atlas.alpha.decision_memory.api.schemas import DecisionMemoryView
from atlas.alpha.opportunity_cost.api.schemas import OpportunityCostChangeView, OpportunityCostView
from atlas.alpha.portfolio_decision.api.schemas import PortfolioDecisionView
from atlas.core.infrastructure.api.serialization import CamelModel


class InvestmentCaseDecisionLayerBundleView(CamelModel):
    opportunity_cost: OpportunityCostView | None
    opportunity_cost_change: OpportunityCostChangeView | None
    decision_memory: DecisionMemoryView | None
    decision_explanation: DecisionExplanationView | None
    portfolio_decision: PortfolioDecisionView | None
