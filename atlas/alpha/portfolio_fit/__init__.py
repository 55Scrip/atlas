"""Portfolio Fit Engine (Product Sprint 4) -- an Alpha-layer
**interpretation**, not a new source of truth.

Answers one question: "How well does this company fit *my* portfolio?" --
never "is this company good?" (that question is already answered by
`CanonicalAnalysis.recommendation`/`conviction`, unmodified, elsewhere).

**Owns no data, stores nothing, computes deterministically.** Every
dimension is a direct, disclosed read of an already-computed signal:

- Business Fit <- `CanonicalAnalysis.business_analysis` (unmodified)
- Valuation Fit <- `CanonicalAnalysis.valuation_engine` +
  `.valuation_support` (unmodified)
- Risk Fit <- `CanonicalAnalysis.risk_analysis` (unmodified)
- Allocation Fit <- `AlphaHolding.weight_percent` + the exact same
  concentration thresholds `atlas.domains.portfolio.calculations
  .concentration_level` already uses (reused, not re-derived)
- Expected Contribution <- `CanonicalAnalysis.outlook` (unmodified)
- Cash Impact <- `AlphaPortfolioState.cash_weight_percent` (unmodified)

No new Core domain type, no new ADR, no new persistence, no new
aggregate. `engine.py` is pure (no I/O, fully deterministic given its
inputs); `service.py` is the only part that reads a repository, mirroring
every other Alpha package's own `service.py`/pure-module split (e.g.
`atlas.alpha.daily_brief`).

**Why this package, not `atlas.analysis_engine`:** Portfolio Fit is
inherently portfolio-*wide* (concentration, cash, position sizing need
every holding at once). `atlas.decision_engine.contracts.PortfolioFinding`
documents, by explicit architectural lock, why that computation cannot
live in `atlas.decision_engine`/`atlas.analysis_engine`: those packages
see at most one holding in isolation, and "synthesizing a one-holding
portfolio to force a computation is explicitly forbidden." Only
`atlas.alpha`, which already holds the full `AlphaPortfolioState`, can
honestly compute this -- the same reason `atlas.alpha.portfolio_intelligence`
already reserved a placeholder (`PortfolioFitStatus`) for a future
Portfolio Fit capability. That placeholder is left untouched by this
package (see `service.py`'s own module docstring for why); this is a new,
separate result type, not a replacement of it.
"""
