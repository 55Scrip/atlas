"""The canonical Investment Case Composition layer (ATLAS-027, Phase 9).

**Not a second reasoning engine.** `InvestmentCaseCompositionService
.build` gathers a Case's own records (Decisions, Observations,
Evidence, Outcomes, its linked holding and trade log, if any) and
assembles the exact same `atlas.decision_engine.pipeline.run_pipeline`
-> `atlas.analysis_engine.pipeline.assemble_analysis` chain every other
canonical consumer runs -- it never computes a Business, Valuation,
Risk, Confidence, Conviction, or Recommendation conclusion of its own.
`InvestmentCaseComposition.canonical_analysis` *is*
`atlas.analysis_engine.models.CanonicalAnalysis`, reused by reference,
never re-derived or reshaped.

**Additive, not a replacement.** `atlas.alpha.case_intelligence
.CaseIntelligenceService` keeps its own existing `CaseIntelligenceReport`
and stable API completely untouched this sprint, per explicit design
confirmation -- this is a new, separate composition layer sitting
alongside it, proving out the real `CanonicalAnalysis` wiring
`case_intelligence` never adopted (see that package's own audit finding:
its `ConvictionStatus` has been hardcoded `available=False` since
ATLAS-017, on a code path that has never called `assemble_analysis`).
A future sprint may migrate `case_intelligence` onto this layer once it
has proven stable; this sprint does not attempt that migration.

**Reuses, never re-derives, the Core-record-gathering step.** The
"decisions/observations/evidence/outcomes/holding/trade-log for this
Case" lookup mirrors `CaseIntelligenceService.build_report`'s own
pattern exactly (both packages independently gather these small,
non-analytical records -- the same "each Alpha service gathers its own
records, but never recomputes analysis" split `pipeline_bridge.py`'s
own `run_decision_engine_for_case`/`build_decision_engine_input` already
establish as the one shared analytical assembly point). This module
calls that exact shared function -- never a second, independent
`DecisionEngineInput` assembly.

**Architectural boundary**, identical to every other Alpha module: no
`atlas.core.infrastructure`, no external API calls, no LLM, no NLP. May
read `atlas.core.domain` (Case, Decision, Observation, Evidence,
Outcome repositories) and `atlas.decision_engine`/`atlas.analysis_engine`
freely -- the same read-only direction `case_intelligence` and
`portfolio_intelligence` already established.
"""
