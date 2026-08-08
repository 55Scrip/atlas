"""The Analysis Engine (ATLAS-020 foundation; ATLAS-021 added Business
Analysis as its first real producer).

This package is the intended eventual single source of truth for every
analytical conclusion Atlas produces about a company — Business
Analysis, Valuation, Risk, Conviction, Portfolio Fit, Recommendation.
Portfolio, Investment Case, Discovery, Weekly Review, and any future
surface are expected to converge on reading one
`atlas.analysis_engine.models.CanonicalAnalysis` object rather than
each computing their own.

**Ownership boundaries between the five analytical concerns this
package names** (Phase 12, ATLAS-021 — stated once here so no
subordinate module needs to restate it):

- **Business Analysis** (`business.py`) owns whether the business
  itself is good — Business Model, Competitive Position, Management,
  Capital Allocation, Growth, Durability. It produces facts about the
  company. It never produces a price, a risk, a conviction level, or a
  recommendation.
- **Valuation** (`atlas.decision_engine.stages.valuation`, reused
  verbatim) owns whether the price is good — always a separate
  question from whether the business is good. It never reads Business
  Analysis's conclusions to decide its own.
- **Risk** (`contracts.RiskCategory`, assembled in `pipeline.py`) owns
  naming what could go wrong, across a closed taxonomy that includes
  but is broader than business quality (Macro, Regulatory, Portfolio
  Risk are not Business Analysis's concern). Risk never produces a
  recommendation.
- **Conviction** (`conviction.py`) owns how strongly the *available*
  analysis supports a conclusion — a function of evidence coverage,
  contradiction, and staleness, never a re-judgment of what Business
  Analysis or Valuation themselves concluded.
- **Recommendation** (`recommendation.py`, gate only) owns whether
  enough of the above is complete and strong enough to permit a
  directional view — it decides *whether*, never *what*; no
  `DirectionalRecommendation` type exists anywhere in this package.

Each owns its question exclusively; none recomputes another's answer,
matching this sprint's own "one source of truth per question" mandate.

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

ATLAS-021 added the first genuinely new *findings-producing* stage:

- **Business Analysis** (`business.py`) — the canonical, six-category
  owner of business-quality evaluation (Business Model, Competitive
  Position, Management, Capital Allocation, Growth, Durability).
  Durability is reused verbatim from `atlas.decision_engine`'s own
  `DurabilityFinding`, never recomputed; the other five are genuinely
  new, and — per the Phase 1 audit that preceded this module — every
  one honestly reports `INSUFFICIENT_INPUT` today, because neither
  `Observation` nor `Evidence` carries a structural field attributing a
  record to one of these six categories, and no Financial Statement,
  Filing, or Transcript Core Domain Object exists yet either. Designed
  for extensibility without a future redesign: `evaluate_business_analysis`
  already accepts a typed, currently-always-empty `external_records`
  slot for future financial-statement/filing/transcript/macro/news
  ingestion — see `business.py`'s own module docstring for why
  `WEAK`/`MODERATE`/`STRONG` deliberately stay out of reach even once
  that slot is populated (counting records is not business judgment).

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
capability is designed but not yet computable (Valuation, Portfolio
Fit's per-factor evaluation, Catalysts, Scenario Analysis, and — as of
ATLAS-021 — every individual Business Analysis category), the relevant
result carries the same honest `INSUFFICIENT_INPUT`/`NOT_YET_IMPLEMENTED`
value `atlas.decision_engine` already established as this codebase's
house style for "this is a real gap, not an oversight."
"""
