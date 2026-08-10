"""Daily Brief v1 -- the Alpha-layer orchestration half of
`atlas.analysis_engine.daily_brief`.

**Not a second analysis engine.** This package never computes a
Business/Valuation/Risk/Change conclusion of its own -- it gathers
"which Cases exist" (every Portfolio holding plus every Watchlist entry,
deduplicated by `case_id`), reads each one's already-computed
`ChangeIntelligence` via the exact same
`InvestmentCaseCompositionService.build` the Investment Case page itself
calls, and hands the result to the pure `atlas.analysis_engine
.daily_brief.build_daily_brief`. No repository read here recomputes
anything `assemble_analysis`/`compare_snapshots` did not already
compute.

**Deliberately per-Case `build`, not `build_many`.** `build_many`
(ATLAS-028) does not resolve a Watchlist-only Case's ticker -- by its
own documented design, it was built for Portfolio Cockpit, a
Portfolio-only surface. Daily Brief must cover Watchlist too (the
sprint's own explicit "Portfolio + Watchlist" requirement), so this
package calls `build` once per Case -- the same, already-correct
Watchlist-fallback-aware path -- accepting the small, bounded cost of
one assembly per Case rather than extending `build_many`'s own,
unrelated, proven batch path for a capability this sprint does not
otherwise need to touch.

**Architectural boundary**, identical to every other Alpha module: no
LLM, no NLP, no direct provider/network calls. May read `atlas.core.domain`,
`atlas.decision_engine`, `atlas.analysis_engine`, and other `atlas.alpha`
packages for their own repository/service types -- the same pattern
`atlas.alpha.portfolio_cockpit` already follows for
`InvestmentCaseCompositionService` itself.
"""
