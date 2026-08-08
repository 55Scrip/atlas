"""The Portfolio Cockpit composition layer (ATLAS-028).

**Not a second reasoning engine — a portfolio-wide projection over
canonical per-holding analysis.** `PortfolioCockpitService.build_report`
never computes a Business, Valuation, Risk, or Conviction conclusion of
its own. It reuses `atlas.alpha.investment_case.InvestmentCaseComposition
Service.build_many` (batched, ATLAS-028's own fix for that service's
real N+1) to get one real `CanonicalAnalysis` per holding, then narrows
each into a compact `PortfolioHoldingAnalysis` -- a projection, never a
duplicate of the full object (the full `CanonicalAnalysis` remains
reachable through the Investment Case, one click away).

**Portfolio is overview, not depth.** Every projection function in this
package narrows an existing canonical value down for scanability; none
of them reinterprets, rescales, or averages one. `RiskProjection` is
explicitly documented as a display convenience (the single highest-
severity category) sitting alongside the complete, untouched 4-category
vector -- never a replacement for it. `BusinessSummary` exposes exactly
the two `BusinessCategory` members this codebase can currently evaluate
for real (Growth, Capital Allocation) -- never a synthesized six-
category aggregate, per this sprint's own explicit "prefer honesty over
visual simplicity" rule.

**Attention is prioritization, never recommendation.** `ReviewPriority`
and `AttentionReasonKind` (`attention.py`) describe where a review is
warranted and why, in fixed, deterministic, first-match-wins rules
combining position size (reusing `portfolio_intelligence.thresholds`'s
own concentration cutoffs, never inventing a new number) with real
analytical signals already computed elsewhere. Nothing here ever
produces or implies BUY/SELL/TRIM/ADD.

**Reuses the existing portfolio-wide summary, never recomputes it.**
Concentration, unallocated capital, holdings count, and every other
portfolio-wide fact in `PortfolioCockpitReport.summary` is the exact
`PortfolioSummaryMetrics` object `atlas.alpha.portfolio_status
.PortfolioStatusService` already computes -- reused by reference, not
re-derived.

**Architectural boundary**, identical to every other Alpha module: no
`atlas.core.infrastructure`, no external API calls, no LLM, no NLP. May
read `atlas.core.domain`, `atlas.decision_engine`, `atlas.analysis_engine`,
and sibling Alpha packages (`portfolio`, `portfolio_status`,
`portfolio_intelligence`, `investment_case`) freely, the same boundary
every prior Alpha package in this codebase already established.
"""
