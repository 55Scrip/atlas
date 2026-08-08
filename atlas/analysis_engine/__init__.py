"""The Analysis Engine (ATLAS-020, Phase 1 foundation).

This package is the intended eventual single source of truth for every
analytical conclusion Atlas produces about a company — Business
Analysis, Valuation, Risk, Conviction, Portfolio Fit, Recommendation.
Portfolio, Investment Case, Discovery, Weekly Review, and any future
surface are expected to converge on reading one
`atlas.analysis_engine.models.CanonicalAnalysis` object rather than
each computing their own.

**This sprint does not move `atlas.decision_engine` here, and does not
duplicate any of its logic.** `atlas.decision_engine.pipeline.run_pipeline`
remains the one place Business Evaluation, Valuation, Portfolio
Intelligence, and Reasoning are actually computed — the exact audit
performed for ATLAS-019 (unchanged since, confirmed by git history)
found nothing in that package worth rewriting: every stage is either a
real, honest, deterministic computation over real data, or a value
structurally locked to `INSUFFICIENT_INPUT` because Atlas has no
external data source to compute it from yet. Moving that code here
today, before a real data source exists to justify the move, would be
motion without progress.

What this sprint adds is the two genuinely new capabilities that do
**not** depend on missing external data — both computable, today, for
real, from signals `atlas.decision_engine` already produces:

- **Conviction** (`conviction.py`) — a deterministic, categorical
  classifier over Evidence Coverage, contradicting evidence, and
  thesis staleness. Never numeric, never manually entered, always
  explainable via `ConvictionReasonCode`.
- **Recommendation Gate** (`recommendation.py`) — wraps
  `atlas.decision_engine.stages.recommendation.determine_recommendation`
  and adds the one new gate condition this sprint introduces
  (Conviction must clear a threshold) — reused, not reimplemented.

...plus the structural scaffolding every future stage will need:
`Finding` (a UI-agnostic, structured analytical conclusion —
`findings.py`), `Provenance` (a traceability record every `Finding`
carries — `provenance.py`), and `CanonicalAnalysis` itself
(`models.py`) — assembled by `pipeline.py`'s `assemble_analysis`, a
pure function over an already-computed `DecisionEngineOutput`.

**Architectural boundary**, mirroring `atlas.decision_engine`'s own
(enforced by `tests/test_architecture_boundaries.py
::test_analysis_engine_only_reads_core_and_decision_engine`): this
package reads only `atlas.core.domain` and `atlas.decision_engine`.
It never imports `atlas.alpha`, `atlas.core.application`, or
`atlas.core.infrastructure`. Wiring real Alpha portfolio/trade data
into an `AnalysisEngine` call remains a composition-layer concern for
a future sprint — exactly the same one-way relationship
`atlas.alpha.portfolio_intelligence.pipeline_bridge` already has with
`atlas.decision_engine` today, not a new coupling this package invents.

Nothing in this package fabricates a conclusion. Where a genuine
capability is designed but not yet computable (Business Analysis,
Valuation, Portfolio Fit's per-factor evaluation, Catalysts, Scenario
Analysis), `CanonicalAnalysis` carries the same honest
`EvaluationState.INSUFFICIENT_INPUT` (or an explicit "not yet
implemented" reason) `atlas.decision_engine` already established as
this codebase's house style for "this is a real gap, not an oversight."
"""
