"""Portfolio Intelligence integration layer (ATLAS-016).

Naming note, read this before reusing the term "Portfolio Intelligence"
anywhere near this module: this codebase already has **two other**
things sharing that name, and this is deliberately a **third, distinct**
one:

1. `atlas.capabilities.portfolio_intelligence.PortfolioIntelligenceCapability`
   -- a legacy, CLI-only, scored 7-dimension fit engine (`fit_score`,
   sector/country/market-cap concentration scores). Not reachable from
   the live FastAPI app. This module never imports it and never
   reproduces its scoring.
2. `atlas.decision_engine.stages.portfolio_intelligence` -- one internal
   stage of the canonical Decision Engine pipeline (`DE-003`), producing
   `PortfolioIntelligenceResult` for a single Case. This module is a
   *consumer* of that pipeline's output, not a replacement for it.
3. **This module** -- the ATLAS-016 integration layer that runs the
   canonical `atlas.decision_engine.pipeline.run_pipeline` once per held
   Investment Case, composes its output with the existing
   `atlas.alpha.portfolio_status.PortfolioStatusService` report (ATLAS-015,
   reused verbatim, never recomputed), and derives the Portfolio page's
   Key Findings / Consider / Risk Signals / Missing Evidence sections --
   plain, deterministic reshaping of already-computed facts. No scoring,
   no ranking, no AI, no new reasoning system, no trade recommendation.

Architecture: Portfolio -> this module -> Decision Engine pipeline ->
existing reasoning -> structured findings -> Portfolio UI. This module
never computes a finding the pipeline or `PortfolioStatusService`
couldn't already support; it only reshapes their output for display.
"""
