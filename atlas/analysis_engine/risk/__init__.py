"""Risk Analysis v1 (ATLAS-025) -- the canonical owner of every Risk
conclusion Atlas produces: what can go wrong, never what to do about it.

**Answers "what can go wrong?", never "should I buy or sell?"** Risk
Findings are consumed by a future Recommendation layer; this package
never produces a directional conclusion itself, the same separation
`atlas.analysis_engine.business`/`.valuation` already keep from
`recommendation.py`.

**Independent of Business Quality and Valuation**, not a reinterpretation
of Conviction. A category here may disagree with either -- `growth.py`
STRONG and `valuation_risk.py` HIGH can coexist in the same run, the same
"a great company can be expensive" independence `valuation/__init__.py`
already documents for its own relationship to Business Analysis.

**Four real evaluators in v1**, each reusing an already-computed
upstream `Finding` rather than recomputing anything:

- `business_risk.py` -- reuses `growth.evaluate_growth`'s own status.
- `financial_risk.py` -- reuses `capital_allocation.evaluate_capital_allocation`'s
  own status, plus one direct, non-duplicating cash-flow-sign check.
- `valuation_risk.py` -- reuses `valuation.cash_flow
  .evaluate_fcf_yield_relative`'s own status.
- `thesis_risk.py` -- reuses `atlas.decision_engine.stages.reasoning`'s
  own `ContradictionSummary`, additive to the pre-existing per-observation
  Findings mechanism `pipeline.py::_build_findings` already builds (see
  `thesis_risk.py`'s own module docstring for that architecture decision).

**Six `RiskCategory` members stay real, named, and unproduced this
sprint** -- `INDUSTRY_RISK`, `MACRO_RISK`, `BEHAVIORAL_RISK`,
`REGULATORY_RISK` have no canonical data source anywhere in this
codebase. `EXECUTION_RISK` and `PORTFOLIO_RISK` are different: the
ATLAS-025 audit confirmed real, deterministic signals for both already
exist (`atlas.alpha.portfolio_intelligence`'s reconciliation state and
concentration/allocation logic) -- but both depend on Alpha-side data
this package's own architectural boundary must never read. Correct
design, per this sprint's own explicit instruction: leave that reasoning
in the Alpha composition layer that already computes it; do not create
an `analysis_engine` -> `atlas.alpha` dependency merely to make the
taxonomy look complete.

**No numeric score, no weighted aggregate, no overall risk label.**
`risk.models.RiskAnalysisResult` has no top-level summary field, the
same choice `valuation.models.ValuationEngineResult` already made for
its own four methods -- see that module's own docstring.

**Architectural boundary**, identical to every sibling subpackage
(enforced by the same repository-wide
`test_analysis_engine_only_reads_core_and_decision_engine`): no
`atlas.alpha`, no `atlas.core.application`, no `atlas.core.infrastructure`,
no external API calls, no LLM, no NLP.
"""
