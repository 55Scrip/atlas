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

from atlas.analysis_engine.analysis_coverage import AnalysisCoverageAssessment
from atlas.analysis_engine.business import BusinessAnalysisResult
from atlas.analysis_engine.contracts import CapabilityStatus
from atlas.analysis_engine.conviction import ConvictionAssessment
from atlas.analysis_engine.findings import Finding
from atlas.analysis_engine.investment_case_synthesis import InvestmentCaseSynthesis
from atlas.analysis_engine.outlook import Outlook
from atlas.analysis_engine.recommendation import RecommendationGateResult
from atlas.analysis_engine.recommendation_outlook_context import RecommendationOutlookContext
from atlas.analysis_engine.risk.models import RiskAnalysisResult
from atlas.analysis_engine.valuation.models import ValuationEngineResult
from atlas.analysis_engine.valuation.support import ValuationSupport
from atlas.decision_engine.contracts import (
    BusinessEvaluationResult,
    EvidenceCoverageLevel,
    OpenQuestion,
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
    # -- New in Internal Alpha Fix Sprint 1, real (additive -- `conviction`
    # above keeps its exact prior meaning; this is a separate, purely
    # company-data-driven signal -- see `analysis_coverage.py`'s own
    # module docstring for why the two must never be merged) ------------
    analysis_coverage: AnalysisCoverageAssessment
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

    # -- New in ATLAS-027, real (additive -- `reasoning` above (decision_engine's
    # own ReasoningResult, reused verbatim) keeps its exact prior open_questions
    # tuple unchanged; this is a corrected, CanonicalAnalysis-level view) ---
    open_questions: tuple[OpenQuestion, ...]
    """`reasoning.finding.open_questions`, minus any question proven
    stale by a newer `analysis_engine` capability decision_engine's own
    locked stages cannot see. ATLAS-027 Phase 2's audit found exactly
    one such case: `OpenQuestionKind.VALUATION_THESIS_NOT_DOCUMENTED`
    checks decision_engine's own permanently-locked substantive
    Valuation field, structurally blind to this package's own real
    `valuation_engine`. When `valuation_engine`'s `FCF_YIELD_RELATIVE`
    finding reaches a real conclusion, that specific question no longer
    reflects `CanonicalAnalysis`'s true state and is omitted here.

    Stage 3 added the second such case, on the identical grounds:
    `BUSINESS_DURABILITY_NOT_ASSESSABLE` checks decision_engine's own
    permanently-locked `durability` field, structurally blind to this
    package's own real `durability.evaluate_durability`. When that
    evaluator reaches a real status the question is omitted too. **The
    previous wording here -- that Durability was "confirmed genuinely,
    permanently unresolved (Durability has no data source at all)" --
    described the pre-Stage-3 world and is no longer true of
    `CanonicalAnalysis`; it remains true of the decision_engine object,
    which is unchanged and still locked.** A company that genuinely
    lacks the business facts keeps the question: `INSUFFICIENT_INPUT` is
    never suppressed, only a real conclusion displaces it.

    Every `PORTFOLIO_FACTOR_NOT_ASSESSABLE` entry is still never
    removed -- the seven portfolio factors are correctly out of
    decision_engine's/this package's own reach, an architectural
    boundary, not staleness -- the same boundary `atlas.analysis_engine
    .risk`'s own `PORTFOLIO_RISK` category respects. This field feeds
    `conviction.calculate_conviction`'s own `has_open_questions` input;
    `reasoning.finding.open_questions` itself is never mutated."""

    # -- New in Investment Case Engine v2 slice, real (additive -- every
    # field above keeps its exact prior meaning; this is a further,
    # synthesized view derived from business_analysis/valuation_engine/
    # risk_analysis/conviction above, never a second computation of any
    # of them) -------------------------------------------------------
    synthesis: InvestmentCaseSynthesis
    """Strengths, Risks (curated), Growth narrative, Valuation Context,
    Open Questions, and a concise Atlas Thesis -- see
    `atlas.analysis_engine.investment_case_synthesis`'s own module
    docstring for the full derivation rules and why this is not a
    second reasoning engine."""

    # -- New in Outlook Intelligence Sprint 1, real (additive -- every
    # field above keeps its exact prior meaning; a further, synthesized
    # view derived from business_analysis/valuation_engine/risk_analysis/
    # conviction/synthesis above, never a second computation of any of
    # them) -------------------------------------------------------------
    outlook: Outlook
    """Short-Term and Long-Term Expected Return/Scenarios/Conviction/Key
    Drivers -- see `atlas.analysis_engine.outlook`'s own module
    docstring for the full derivation rules and why this is not a
    forward-looking scenario-modeling engine in disguise. `momentum` on
    both horizons is always `OutlookMomentumKind.UNAVAILABLE` here (see
    that module's own docstring for why); a caller with a
    `ChangeIntelligence` fills it in via `derive_outlook_momentum`."""

    # -- New in Recommendation / Decision Intelligence Sprint 1, real
    # (additive -- `recommendation` above keeps its exact prior meaning
    # and is never read by, or fed back into, this field's own
    # derivation; `outlook` above likewise keeps its exact prior meaning.
    # See `recommendation_outlook_context.py`'s own module docstring for
    # why this stays a sibling, disclosure-only fact, never a gating
    # input to either `recommendation` or `outlook`.) -------------------
    recommendation_outlook_context: RecommendationOutlookContext
    """Whether the already-computed `recommendation.recommendation` and
    the already-computed `outlook` currently corroborate or diverge, per
    horizon -- context for the reader, never a cause of either
    conclusion."""

    # -- Valuation Support for Capital Deployment (`DE-015`), real
    # (additive -- `valuation_engine` above keeps its exact prior
    # meaning; this is a further, independent conclusion derived from
    # it, never a second computation of it. `DE-016` forwards only its
    # public `.status` into `recommendation` above (`DE-015` §18) --
    # `.reasoning`/`.gap` and every private proof-path detail remain
    # unread by it; see `valuation/support.py`'s own module docstring) --
    valuation_support: ValuationSupport
    """Whether today's market valuation supports deploying new capital --
    a narrower, independent domain question from `valuation_engine`'s own
    relative-to-history conclusions. Real and case-specific as of `DE-015`
    (see `valuation/support.py`'s own module docstring); its public
    `status` is the `DE-008` BUY/ADD "Valuation Support for Capital
    Deployment" prerequisite, consumed by `recommendation` above via
    `DE-016`'s wiring -- `.reasoning`/`.gap` are not."""

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
