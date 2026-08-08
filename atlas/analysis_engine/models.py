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

from atlas.analysis_engine.contracts import CapabilityStatus
from atlas.analysis_engine.conviction import ConvictionAssessment
from atlas.analysis_engine.findings import Finding
from atlas.analysis_engine.recommendation import RecommendationGateResult
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
    """`findings` holds every `Finding` this sprint's pipeline could
    honestly produce -- today, only `RiskCategory.THESIS_RISK`
    (contradicting evidence against the recorded thesis), reused
    directly from Reasoning's own `ContradictionSummary`. The other
    seven categories in `atlas.analysis_engine.contracts.RiskCategory`
    are real, named, and simply produce zero Findings until their data
    source exists -- see that enum's own per-member docstring."""

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

    # -- New this sprint, honestly not yet implemented -----------------
    catalysts: UnavailableCapability
    scenario_analysis: UnavailableCapability

    generated_at: datetime
