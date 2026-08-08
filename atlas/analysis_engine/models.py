"""The Canonical Analysis Object (ATLAS-020, Phase 3).

`CanonicalAnalysis` is the one object every consumer -- Portfolio,
Investment Case, Discovery, Weekly Review, History, and any future
surface -- should eventually read instead of computing anything
analytical itself. This sprint defines its real shape and assembles it
for real (`pipeline.py`); it does not yet replace what
`atlas.alpha.case_intelligence`/`atlas.alpha.portfolio_intelligence`
independently return to the frontend today -- that migration is a
future sprint's job once this object has been proven correct.

Every field below is one of exactly three things:

1. **Reused verbatim** from `atlas.decision_engine.contracts` -- the
   real, already-computed output of a Decision Engine stage. Never
   copied or re-derived; the same object reference the pipeline
   produced.
2. **New and real** -- computed for the first time in this package
   (`conviction.py`, `recommendation.py`) from signals in (1).
3. **New and honestly absent** -- a real section this document's design
   phases specified (Catalysts, Scenario Analysis), for which no data
   source exists in this codebase yet. Represented as
   `CapabilityStatus.NOT_YET_IMPLEMENTED`, never a fabricated value.

`identity` carries only `case_id` -- **not** a ticker. Company identity
via `AlphaHolding.ticker` is an Alpha-layer fact this package's own
architectural boundary does not read (see `__init__.py`); a future
composition layer attaches it the same way
`atlas.decision_engine.contracts.PortfolioHoldingContext` already
mirrors ticker without this package owning identity resolution.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.analysis_engine.business import BusinessAnalysisResult
from atlas.analysis_engine.contracts import CapabilityStatus
from atlas.analysis_engine.conviction import ConvictionAssessment
from atlas.analysis_engine.findings import Finding
from atlas.analysis_engine.recommendation import RecommendationGateResult
from atlas.analysis_engine.risk.models import RiskAnalysisResult
from atlas.analysis_engine.valuation.models import ValuationEngineResult
from atlas.decision_engine.contracts import (
    BusinessEvaluationResult,
    EvidenceCoverageLevel,
    PortfolioIntelligenceResult,
    ReasoningResult,
    ValuationResult,
)

__all__ = ["Identity", "UnavailableCapability", "RiskSection", "CanonicalAnalysis"]


@dataclass(frozen=True)
class Identity:
    case_id: str


@dataclass(frozen=True)
class UnavailableCapability:
    """A section this document specifies but that has no data source to
    compute from yet -- Catalysts, Scenario Analysis. Distinct from
    `atlas.decision_engine.contracts.EvaluationState.INSUFFICIENT_INPUT`
    (which describes one *dimension* of an existing, real stage) because
    these two sections are not yet real stages at all -- there is no
    `CatalystResult`/`ScenarioResult` type to carry an `EvaluationState`
    on. This type exists so `CanonicalAnalysis` can name them honestly
    rather than omitting the field, matching this sprint's own "report
    unavailable rather than omit or fabricate" instruction."""

    reason: CapabilityStatus = CapabilityStatus.NOT_YET_IMPLEMENTED


@dataclass(frozen=True)
class RiskSection:
    """`findings` holds every generic `Finding` in `CanonicalAnalysis
    .findings` tagged with a `risk_category` in `details` -- a filter
    over the flat list, not a second computation (`pipeline.py`'s own
    module docstring). ATLAS-020 populated this from exactly one source
    (the per-observation `CONTRADICTING_EVIDENCE` Findings for
    `THESIS_RISK`); ATLAS-025 added a second, additive source (one
    `RISK_CATEGORY_ASSESSED` Finding per category in `atlas.
    analysis_engine.risk.models.EVALUATED_RISK_CATEGORIES`), reusing the
    exact same `details["risk_category"]` tag -- `RiskSection` itself,
    and this filter, needed zero changes to pick up the new Findings.

    **This is a legacy/compatibility view, not the canonical Risk
    result.** A consumer that wants the full, structured Risk conclusion
    -- `status`, `missing_evidence`, `confidence`, per category -- reads
    `CanonicalAnalysis.risk_analysis` instead, the same
    "`business`/`business_analysis`" and "`valuation`/`valuation_engine`"
    relationship this object already establishes for its other two
    additive sections. `RiskSection` is kept, unmodified, purely for
    backward compatibility with any existing reader of the flat
    `risk_category`-tagged Finding list."""

    findings: tuple[Finding, ...]


@dataclass(frozen=True)
class CanonicalAnalysis:
    identity: Identity

    # -- Reused verbatim from atlas.decision_engine --------------------
    business: BusinessEvaluationResult
    valuation: ValuationResult
    portfolio_intelligence: PortfolioIntelligenceResult
    reasoning: ReasoningResult
    confidence: EvidenceCoverageLevel

    # -- New this sprint, real -------------------------------------
    risk: RiskSection
    conviction: ConvictionAssessment
    recommendation: RecommendationGateResult
    findings: tuple[Finding, ...]

    # -- New in ATLAS-021, real (additive -- `business` above keeps its
    # exact prior meaning unchanged; this is a second, richer section,
    # not a replacement) -----------------------------------------------
    business_analysis: BusinessAnalysisResult

    # -- New in ATLAS-024, real (additive -- `valuation` above (decision_engine's,
    # permanently locked to INSUFFICIENT_INPUT) keeps its exact prior meaning
    # unchanged; this is a second, richer section, the same pattern
    # business_analysis already established relative to `business`) -------
    valuation_engine: ValuationEngineResult

    # -- New in ATLAS-025, real (additive -- `risk` above (RiskSection,
    # ATLAS-020's flat, tag-filtered view) keeps its exact prior meaning
    # unchanged; this is a second, richer section, the same pattern
    # business_analysis/valuation_engine already established) ------------
    risk_analysis: RiskAnalysisResult

    # -- New this sprint, honestly not yet implemented -----------------
    catalysts: UnavailableCapability
    scenario_analysis: UnavailableCapability
    """Still `UnavailableCapability` (ATLAS-020) -- a different, broader
    concept than `valuation_engine`'s own `SCENARIO_BEAR`/`BASE`/`BULL`
    methods (ATLAS-024), which are a real, narrower Valuation-specific
    structure already homed under `valuation_engine.findings`. This
    field continues to mean "no general, cross-cutting scenario
    capability exists at the CanonicalAnalysis level" -- unrelated to
    whether one specific section (Valuation) has its own scenario
    structure."""

    generated_at: datetime
