"""Case Intelligence (ATLAS-017).

Not a second reasoning engine. This package is a presentation-layer
assembly over the canonical `atlas.decision_engine.pipeline` -- the
exact same pipeline `atlas.alpha.portfolio_intelligence` (ATLAS-016)
already wires into the Portfolio page, now run for a single Investment
Case instead of aggregated across the whole portfolio. Every field on
`CaseIntelligenceReport` (`models.py`) is either read verbatim from a
Core record, reused directly from the Decision Engine's own output
(`atlas.decision_engine.contracts`), or reused directly from
`atlas.alpha.portfolio_status.PortfolioStatusService` (ATLAS-015) --
never a second computation of a fact those already establish.

`atlas.alpha.portfolio_intelligence.pipeline_bridge.run_decision_engine_for_case`
is the one shared function both this package and
`atlas.alpha.portfolio_intelligence` call to run the pipeline -- so a
Case's Evidence Quality/Reasoning/Missing Evidence here can never drift
from what the Portfolio page's Consider/Risk Signals for that same
ticker already say, because both are the same pipeline run.

Conviction is always `unavailable` -- no field in this codebase's domain
model represents an Atlas-computed conviction (only
`Decision.confidence`, which is investor-entered and never interpreted
by Atlas; see `atlas/core/domain/decision/value_objects.py`). Confidence
reuses `EvidenceCoverageLevel` verbatim, the same categorical scale
`atlas.alpha.portfolio_intelligence` already reuses for `ConsiderItem`
-- not a second confidence framework.
"""
