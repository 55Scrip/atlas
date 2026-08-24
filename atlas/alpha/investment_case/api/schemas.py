"""HTTP response schemas for the canonical Investment Case API
(ATLAS-029). Wire format is camelCase via the shared Core `CamelModel`
(ADR-004), matching every other Alpha schema module. Every enum is
serialized as its raw English `.value`.

This is a renderer of `InvestmentCaseComposition`/`CanonicalAnalysis`
(ATLAS-027) -- no field here is computed; every value is either a direct
attribute or a structural narrowing (unwrapping a value object, joining
an enum to its `.value`) of the real, already-produced analysis. Reuses
`EvidenceQualityFindingsSchema`/`ObservationEvidenceClassificationSchema`
/`EvidenceGapSchema`/`OpenQuestionSchema` directly from
`atlas.alpha.case_intelligence.api.schemas` -- the same wire shape for
the same underlying `decision_engine.contracts` types, never redefined.

Deliberately does NOT import from `atlas.alpha.portfolio_cockpit`:
`portfolio_cockpit` already depends on `investment_case` at the service
layer (`InvestmentCaseCompositionService.build_many`), so importing back
from here would create a package-level cycle. `ValuationFindingView`/
`RiskFindingView`/`ConvictionAssessmentView` below are therefore this
package's own, field-for-field independent of `portfolio_cockpit`'s
identically-shaped ones -- both narrow the same real domain objects,
neither recomputes anything.
"""
from __future__ import annotations

from datetime import date, datetime

from atlas.alpha.case_intelligence.api.schemas import (
    EvidenceQualityFindingsSchema,
    OpenQuestionSchema,
)
from atlas.alpha.coverage import CoverageAssessment, DimensionCoverage
from atlas.alpha.coverage import assess_coverage as _assess_coverage
from atlas.alpha.coverage.models import ConfidenceReason
from atlas.alpha.knowledge_coverage.models import InvestmentCaseKnowledgeCoverage, KnowledgeDomainCoverage
from atlas.alpha.decision_support import DecisionSupportView as DecisionSupportViewDomain
from atlas.alpha.decision_support import describe_recommendation
from atlas.alpha.investment_case.business_quality_intelligence import (
    BusinessConsistency,
    BusinessDurability,
    BusinessEfficiency,
    BusinessEvolution,
    BusinessQualityFinding,
    BusinessQualityKnowledge,
    BusinessStability,
    GrowthDurabilitySummary,
    HistoricalDisruption,
)
from atlas.alpha.investment_case.capital_allocation_intelligence import (
    CapitalAllocationHistory,
    CapitalAllocationPeriod,
    CapitalAllocationTrendObservation,
    ManagementCapitalAllocationKnowledge,
    assess_buyback_consistency,
    assess_dividend_continuity,
    assess_management_capital_allocation,
    compute_capital_allocation_trends,
)
from atlas.alpha.investment_case.financial_quality_intelligence import (
    CapitalEfficiencyKnowledge,
    CapitalEfficiencyObservation,
    CashConversionKnowledge,
    CashConversionObservation,
    FinancialDurabilityKnowledge,
    FinancialQualityKnowledge,
    MarginDurability,
    MarginReversal,
    ProfitabilityDurability,
    WorkingCapitalIntelligence,
    WorkingCapitalObservation,
)
from atlas.alpha.investment_case.company_profile import CompanyProfile
from atlas.alpha.investment_case.earnings_call import (
    CommentaryCategoryChange,
    EarningsCallChangeIntelligence,
    EarningsCallKnowledge,
    EarningsCallTranscript,
    ManagementStatement,
    compute_change_intelligence,
)
from atlas.alpha.investment_case.financial_history import FinancialPeriod, MarketSnapshot
from atlas.alpha.investment_case.financial_statement_intelligence import (
    BalanceSheetPeriod,
    CashFlowStatementPeriod,
    FinancialHealthKnowledge,
    FinancialStatementHistory,
    FinancialTrendObservation,
    IncomeStatementPeriod,
    assess_financial_health,
    compute_cash_flow_consistency,
    compute_trend_intelligence,
)
from atlas.alpha.investment_case.growth_intelligence import (
    GrowthDurability,
    GrowthKnowledge,
    GrowthObservation,
    GrowthTrendKnowledge,
    SegmentGrowthInformation,
)
from atlas.alpha.investment_case.historical_valuation import (
    HistoricalValuationKnowledge,
    ValuationDeviation,
    ValuationMetricHistory,
    ValuationObservation,
)
from atlas.alpha.investment_case.management_credibility_intelligence import (
    CommunicationConsistency,
    CredibilityFinding,
    GuidanceReliabilityKnowledge,
    ManagementCommitment,
    ManagementCredibilityKnowledge,
)
from atlas.alpha.investment_case.management_guidance_intelligence import (
    ExplicitTarget,
    ExplicitTargetRange,
    GuidanceItem,
    GuidanceReliabilitySummary,
    ManagementGuidanceKnowledge,
)
from atlas.alpha.investment_case.executive_change_intelligence import (
    ExecutiveChangeKnowledge,
    ExecutiveIdentity,
    LeadershipChangeEvent,
    LeadershipChangeFinding,
    SuccessionRelationship,
)
from atlas.alpha.investment_case.executive_track_record_intelligence import (
    ExecutiveTenureRecord,
    ExecutiveTrackRecordKnowledge,
    TenureContext,
    TenureGuidanceHistory,
    TenureTimeline,
    TrackRecordFinding,
)
from atlas.alpha.investment_case.incentive_intelligence import (
    CashIncentive,
    CompensationDisclosureFiling,
    DilutionEvent,
    EquityIncentive,
    ExecutiveIncentiveProgram,
    IncentiveChangeFinding,
    IncentiveKnowledge,
    IncentiveStructure,
    IncentiveTimelineEvent,
    OwnershipAlignment,
    PerformanceIncentive,
)
from atlas.alpha.investment_case.insider_alignment_intelligence import (
    AlignmentFinding,
    AlignmentObservation,
    EquityCompensationExposure,
    ExecutiveAlignmentProfile,
    ExecutiveOwnership,
    InsiderAlignmentKnowledge,
    InsiderHolding,
    OwnershipChange,
)
from atlas.alpha.investment_case.governance_intelligence import (
    BoardComposition,
    Committee,
    Director,
    GovernanceChange,
    GovernanceFinding,
    GovernanceKnowledge,
    GovernanceObservation,
    GovernancePolicy,
    ShareClass,
    VotingStructure,
)
from atlas.alpha.investment_case.risk_factor_intelligence import (
    RiskCategorySummary,
    RiskChangeObservation,
    RiskDisclosure,
    RiskFactorKnowledge,
)
from atlas.alpha.investment_case.legal_proceedings_intelligence import (
    LegalChangeObservation,
    LegalProceedingDisclosure,
    LegalProceedingsKnowledge,
    ProceedingCategorySummary,
)
from atlas.alpha.investment_case.ownership_intelligence import (
    OwnerCategorySummary,
    OwnershipChangeObservation,
    OwnershipDisclosure,
    OwnershipKnowledge,
)
from atlas.alpha.investment_case.executive_compensation_intelligence import (
    CompensationChangeObservation,
    EquityAwardDisclosure,
    ExecutiveCompensationKnowledge,
    ExecutiveCompensationRecord,
    PerformanceMetricDisclosure,
)
from atlas.alpha.investment_case.models import CurrentThesis, InvestmentCaseComposition
from atlas.alpha.investment_case.regulatory_filings import RegulatoryFiling
from atlas.alpha.portfolio.models import AlphaHolding, AlphaTradeLogEntry
from atlas.analysis_engine.business_contracts import BusinessAnalysisResult, BusinessFinding
from atlas.analysis_engine.conviction import ConvictionAssessment
from atlas.analysis_engine.evidence_resolution import AnyFact, AnyFinding, resolve_evidence_references
from atlas.analysis_engine.investment_case_change import ChangeFinding, ChangeIntelligence, ThesisImpact
from atlas.analysis_engine.investment_case_synthesis import (
    AtlasThesis,
    CaseHighlight,
    CaseOpenQuestion,
    GrowthAnalysis,
    RecentRevenueTrend,
    ValuationContext,
)
from atlas.analysis_engine.models import CanonicalAnalysis
from atlas.analysis_engine.outlook import (
    ExpectedReturnRange,
    HorizonOutlook,
    Outlook,
    OutlookAssumption,
    OutlookDriver,
    OutlookScenario,
    derive_outlook_momentum,
)
from atlas.analysis_engine.recommendation_outlook_context import RecommendationOutlookContext
from atlas.analysis_engine.risk.models import RiskAnalysisResult, RiskFinding, RiskProjection
from atlas.analysis_engine.risk.projection import risk_projection
from atlas.analysis_engine.valuation.models import ValuationEngineResult, ValuationFinding
from atlas.analysis_engine.valuation.support import ValuationSupport
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.observation.entity import Observation
from atlas.core.infrastructure.api.serialization import CamelModel
from atlas.decision_engine.contracts import RecommendationWithheld


class _EvidenceResolverContext:
    """Product Sprint 14 (Evidence & Explanation Quality): a thin,
    schema-layer-only carrier for the three lookup maps
    `resolve_evidence_references` needs, so `BusinessFindingView`/
    `ValuationFindingView`/`RiskFindingView.from_domain` each take one
    optional keyword argument instead of three. Never constructed by
    any test that doesn't care about resolution -- every `from_domain`
    defaults to `_EMPTY_EVIDENCE_RESOLVER_CONTEXT`, which resolves
    nothing (every reference falls back to itself, the exact prior
    behavior), so no existing call site anywhere in this codebase's
    test suite needs to change."""

    __slots__ = ("facts_by_id", "findings_by_id", "observations_by_id")

    def __init__(
        self,
        *,
        facts_by_id: dict[str, AnyFact],
        findings_by_id: dict[str, AnyFinding],
        observations_by_id: dict[str, Observation],
    ) -> None:
        self.facts_by_id = facts_by_id
        self.findings_by_id = findings_by_id
        self.observations_by_id = observations_by_id

    def resolve(self, references: tuple[str, ...]) -> tuple[str, ...]:
        return resolve_evidence_references(
            references,
            facts_by_id=self.facts_by_id,
            findings_by_id=self.findings_by_id,
            observations_by_id=self.observations_by_id,
        )


_EMPTY_EVIDENCE_RESOLVER_CONTEXT = _EvidenceResolverContext(facts_by_id={}, findings_by_id={}, observations_by_id={})


class HoldingContextView(CamelModel):
    held: bool
    ticker: str | None
    weight_percent: float | None
    value_absolute: float | None
    reconciliation_status: str | None

    @classmethod
    def from_domain(cls, holding: AlphaHolding | None) -> "HoldingContextView":
        if holding is None:
            return cls(held=False, ticker=None, weight_percent=None, value_absolute=None, reconciliation_status=None)
        return cls(
            held=True,
            ticker=holding.ticker,
            weight_percent=holding.weight_percent,
            value_absolute=holding.value_absolute,
            reconciliation_status=holding.reconciliation_status.value,
        )


class CurrentThesisView(CamelModel):
    latest_decision_reason: str | None
    latest_decision_type: str | None
    latest_observation_statement: str | None

    @classmethod
    def from_domain(cls, thesis: CurrentThesis) -> "CurrentThesisView":
        return cls(
            latest_decision_reason=thesis.latest_decision_reason,
            latest_decision_type=thesis.latest_decision_type,
            latest_observation_statement=thesis.latest_observation_statement,
        )


class BusinessFindingView(CamelModel):
    kind: str
    status: str
    severity: str
    supporting_evidence: list[str]
    contradicting_evidence: list[str]
    missing_evidence: list[str]
    confidence: str
    updated_at: datetime

    @classmethod
    def from_domain(
        cls,
        finding: BusinessFinding,
        *,
        resolver: "_EvidenceResolverContext | None" = None,
    ) -> "BusinessFindingView":
        resolver = resolver or _EMPTY_EVIDENCE_RESOLVER_CONTEXT
        return cls(
            kind=finding.kind.value,
            status=finding.status.value,
            severity=finding.severity.value,
            supporting_evidence=list(resolver.resolve(finding.supporting_evidence)),
            contradicting_evidence=list(resolver.resolve(finding.contradicting_evidence)),
            missing_evidence=[m.value for m in finding.missing_evidence],
            confidence=finding.confidence.value,
            updated_at=finding.updated_at,
        )


class BusinessAnalysisView(CamelModel):
    state: str
    findings: list[BusinessFindingView]

    @classmethod
    def from_domain(
        cls,
        result: BusinessAnalysisResult,
        *,
        resolver: "_EvidenceResolverContext | None" = None,
    ) -> "BusinessAnalysisView":
        return cls(
            state=result.state.value,
            findings=[BusinessFindingView.from_domain(f, resolver=resolver) for f in result.findings],
        )


class ValuationFindingView(CamelModel):
    kind: str
    status: str
    severity: str
    supporting_facts: list[str]
    contradicting_facts: list[str]
    assumptions: list[str]
    missing_evidence: list[str]
    confidence: str
    current_yield: float | None

    @classmethod
    def from_domain(
        cls,
        finding: ValuationFinding,
        *,
        resolver: "_EvidenceResolverContext | None" = None,
    ) -> "ValuationFindingView":
        resolver = resolver or _EMPTY_EVIDENCE_RESOLVER_CONTEXT
        return cls(
            kind=finding.kind.value,
            status=finding.status.value,
            severity=finding.severity.value,
            supporting_facts=list(resolver.resolve(finding.supporting_facts)),
            contradicting_facts=list(resolver.resolve(finding.contradicting_facts)),
            assumptions=[a.value for a in finding.assumptions],
            missing_evidence=[m.value for m in finding.missing_evidence],
            confidence=finding.confidence.value,
            current_yield=finding.current_yield,
        )


class ValuationEngineView(CamelModel):
    state: str
    findings: list[ValuationFindingView]

    @classmethod
    def from_domain(
        cls,
        result: ValuationEngineResult,
        *,
        resolver: "_EvidenceResolverContext | None" = None,
    ) -> "ValuationEngineView":
        return cls(
            state=result.state.value,
            findings=[ValuationFindingView.from_domain(f, resolver=resolver) for f in result.findings],
        )


class RiskFindingView(CamelModel):
    category: str
    status: str
    severity: str
    supporting_facts: list[str]
    contradicting_facts: list[str]
    missing_evidence: list[str]
    confidence: str

    @classmethod
    def from_domain(
        cls,
        finding: RiskFinding,
        *,
        resolver: "_EvidenceResolverContext | None" = None,
    ) -> "RiskFindingView":
        resolver = resolver or _EMPTY_EVIDENCE_RESOLVER_CONTEXT
        return cls(
            category=finding.category.value,
            status=finding.status.value,
            severity=finding.severity.value,
            supporting_facts=list(resolver.resolve(finding.supporting_facts)),
            contradicting_facts=list(resolver.resolve(finding.contradicting_facts)),
            missing_evidence=[m.value for m in finding.missing_evidence],
            confidence=finding.confidence.value,
        )


class RiskAnalysisView(CamelModel):
    state: str
    findings: list[RiskFindingView]

    @classmethod
    def from_domain(
        cls,
        result: RiskAnalysisResult,
        *,
        resolver: "_EvidenceResolverContext | None" = None,
    ) -> "RiskAnalysisView":
        return cls(
            state=result.state.value,
            findings=[RiskFindingView.from_domain(f, resolver=resolver) for f in result.findings],
        )


class RiskProjectionView(CamelModel):
    """The single highest-severity risk category, for the Atlas View
    scorecard's one "Risk Level" dot -- the same `risk_projection()`
    Portfolio Cockpit's own Holdings table Risk column already calls
    (`atlas.analysis_engine.risk.projection`), never a second, divergent
    computation. Field-for-field identical to `portfolio_cockpit.api
    .schemas.RiskProjectionView`, independently declared per this
    module's own no-cross-package-import convention (see this file's
    header docstring)."""

    category: str
    status: str

    @classmethod
    def from_domain(cls, projection: RiskProjection) -> "RiskProjectionView":
        return cls(category=projection.category.value, status=projection.status.value)


class ValuationSupportView(CamelModel):
    """Alpha Freeze correction sprint (resolving Principal Engineer Review
    2.0 finding M-2): the first exposure of `DE-015`'s `ValuationSupport`
    to any product surface. Exposes only `status` and `gap` -- never
    `.reasoning` verbatim (`DE-015` §18's own boundary: Recommendation
    itself reads only `.status`; this view extends that same restraint to
    the presentation layer, one level further, rather than relaxing it).
    Raw enum member names (`supported`, `missing_capital_deployment_...`)
    are sent over the wire exactly as internal identifiers already are
    elsewhere in this schema (e.g. `risk_projection.status`) -- the
    frontend owns translating them into the safe, narrow presentation
    labels already specified (`UX-021`/`UX-022`: "Downside support
    present/absent", "Valuation conclusion unresolved"), never rendering
    the raw value or the word "supported" directly. No new computation:
    a direct field mapping of the already-computed `ValuationSupport`."""

    status: str
    gap: str | None

    @classmethod
    def from_domain(cls, support: ValuationSupport) -> "ValuationSupportView":
        return cls(status=support.status.value, gap=support.gap.value if support.gap else None)


class ConvictionAssessmentView(CamelModel):
    level: str
    reasons: list[str]

    @classmethod
    def from_domain(cls, assessment: ConvictionAssessment) -> "ConvictionAssessmentView":
        return cls(level=assessment.level.value, reasons=[r.value for r in assessment.reasons])


class DimensionCoverageView(CamelModel):
    """Atlas Intelligence Sprint 1 (Data Coverage & Confidence Engine).
    One real analysis dimension's coverage -- see
    `atlas.alpha.coverage.models.DimensionCoverage`'s own docstring."""

    dimension: str
    level: str
    reasoning: list[str]

    @classmethod
    def from_domain(cls, coverage: DimensionCoverage) -> "DimensionCoverageView":
        return cls(dimension=coverage.dimension, level=coverage.level.value, reasoning=list(coverage.reasoning))


class KnowledgeDomainCoverageView(CamelModel):
    """Automatic Investment Case Builder Foundation. One knowledge
    domain's current state -- see `atlas.alpha.knowledge_coverage
    .models.KnowledgeDomainCoverage`'s own docstring."""

    domain: str
    group: str
    level: str
    freshness: str
    dominance: str
    missing_reasons: list[str]

    @classmethod
    def from_domain(cls, coverage: KnowledgeDomainCoverage) -> "KnowledgeDomainCoverageView":
        return cls(
            domain=coverage.domain.value,
            group=coverage.group.value,
            level=coverage.level.value,
            freshness=coverage.freshness.value,
            dominance=coverage.dominance.value,
            missing_reasons=[r.value for r in coverage.missing_reasons],
        )


class InvestmentCaseKnowledgeCoverageView(CamelModel):
    """Automatic Investment Case Builder Foundation. The whole-Case
    knowledge-completeness picture -- see `atlas.alpha.knowledge_coverage
    .models.InvestmentCaseKnowledgeCoverage`'s own docstring for why the
    backend domain object itself carries no percentage field.
    `coveragePercent` is computed here, once, at the serialization
    boundary, always alongside the real counts it was derived from
    (`availableCount`/`applicableCount`) -- never a black-box score."""

    domains: list[KnowledgeDomainCoverageView]
    available_count: int
    partially_available_count: int
    applicable_count: int
    total_domain_count: int
    not_applicable_count: int
    missing_domains: list[str]
    not_applicable_domains: list[str]
    coverage_percent: int
    """`round(available_count / applicable_count * 100)`, `0` when
    `applicable_count` is `0` (no domain has a real extractor wired --
    cannot happen today, since `COMPANY_PROFILE`/`FINANCIAL_HISTORY`/
    `VALUATION` are always applicable, but guarded honestly rather than
    dividing by zero)."""

    @classmethod
    def from_domain(cls, coverage: InvestmentCaseKnowledgeCoverage) -> "InvestmentCaseKnowledgeCoverageView":
        coverage_percent = (
            round(coverage.available_count / coverage.applicable_count * 100) if coverage.applicable_count > 0 else 0
        )
        return cls(
            domains=[KnowledgeDomainCoverageView.from_domain(d) for d in coverage.domains],
            available_count=coverage.available_count,
            partially_available_count=coverage.partially_available_count,
            applicable_count=coverage.applicable_count,
            total_domain_count=coverage.total_domain_count,
            not_applicable_count=coverage.not_applicable_count,
            missing_domains=[d.value for d in coverage.missing_domains],
            not_applicable_domains=[d.value for d in coverage.not_applicable_domains],
            coverage_percent=coverage_percent,
        )


class ConfidenceReasonView(CamelModel):
    """Atlas Intelligence Sprint 1. Mirrors `atlas.alpha.coverage.models
    .ConfidenceReasonCode` exactly -- a closed reason code plus whatever
    real count it names, never a pre-written sentence (matching
    `ConvictionAssessmentView.reasons`'s own "frontend owns the
    sentence" convention)."""

    code: str
    count: int | None
    total: int | None

    @classmethod
    def from_domain(cls, reason: "ConfidenceReason") -> "ConfidenceReasonView":
        return cls(code=reason.code.value, count=reason.count, total=reason.total)


class CoverageAssessmentView(CamelModel):
    """Atlas Intelligence Sprint 1. Every field is read straight off an
    already-computed `CoverageAssessment` -- see
    `atlas.alpha.coverage.engine.assess_coverage`'s own module
    docstring for the full derivation and why this is never a second
    analysis computation."""

    dimensions: list[DimensionCoverageView]
    overall_coverage: str
    overall_confidence: str
    missing_dimensions: list[str]
    not_applicable_dimensions: list[str]
    reasoning: list[ConfidenceReasonView]

    @classmethod
    def from_domain(cls, assessment: CoverageAssessment) -> "CoverageAssessmentView":
        return cls(
            dimensions=[DimensionCoverageView.from_domain(d) for d in assessment.dimensions],
            overall_coverage=assessment.overall_coverage.value,
            overall_confidence=assessment.overall_confidence.value,
            missing_dimensions=list(assessment.missing_dimensions),
            not_applicable_dimensions=list(assessment.not_applicable_dimensions),
            reasoning=[ConfidenceReasonView.from_domain(r) for r in assessment.reasoning],
        )


class RecommendationOutlookAlignmentView(CamelModel):
    """Recommendation / Decision Intelligence Sprint 1: the one, narrow,
    sanctioned Outlook<->Recommendation relationship
    (`DE-012`/`DE-014`'s "sibling conclusions" boundary) -- see
    `atlas.analysis_engine.recommendation_outlook_context`'s own module
    docstring for the exact rule. Disclosure only: never read by, and
    with no effect on, `level`/`badge_label`/`statement` above, which are
    derived from `RecommendationGateResult` alone. Each value is one of
    `"corroborates"`/`"diverges"`/`"mixed"`/`"unavailable"` -- a render
    -facing caller must present this as independent, correlated context
    next to the Recommendation, never as its cause."""

    short_term: str
    long_term: str

    @classmethod
    def from_domain(cls, context: RecommendationOutlookContext) -> "RecommendationOutlookAlignmentView":
        return cls(short_term=context.short_term.value, long_term=context.long_term.value)


class RecommendationStateView(CamelModel):
    """Migration Review §11.1/§13's header evidence-support sentence --
    evidence-support language only, never a raw `RecommendationDirection`
    member name (Decision Log #1). See
    `atlas.alpha.decision_support`'s own module docstring for the full
    presentation-layer rationale; this schema is its wire form.

    `conviction_gate_met` names the one real gate this analysis checked
    (`atlas.analysis_engine.recommendation.RECOMMENDATION_GATE_MINIMUM
    _CONVICTION`), without restating Conviction's own level -- unchanged
    from this schema's prior shape.

    `outlook_alignment` is new this sprint -- see
    `RecommendationOutlookAlignmentView`'s own docstring.

    `missing_evaluations` (Beta Recommendation Experience implementation
    sprint, resolving `UX-022` §4): the real
    `RecommendationWithheld.missing_evaluations` pipeline-stage tuple,
    passed through as raw enum values -- empty whenever `level` is not
    `insufficient_evidence`. Additive only: `statement`/`badge_label`
    above keep their existing single fixed sentence for this level
    unchanged (`atlas.alpha.decision_support`'s own documented choice
    not to branch its one statement on *why* withheld); this field lets
    a caller show the real, per-case reason(s) *alongside* that fixed
    sentence, never in place of it. `RecommendationWithheld.reason`
    itself (`ENGINE_NOT_IMPLEMENTED`/`EVIDENCE_INSUFFICIENT`) is
    deliberately not exposed here -- an internal implementation-status
    value, not investor-facing content."""

    level: str
    badge_label: str
    statement: str
    conviction_gate_met: bool
    outlook_alignment: RecommendationOutlookAlignmentView
    missing_evaluations: list[str]

    @classmethod
    def from_domain(cls, gate_result, outlook_context: RecommendationOutlookContext) -> "RecommendationStateView":
        view: DecisionSupportViewDomain = describe_recommendation(gate_result)
        recommendation = gate_result.recommendation
        missing_evaluations = (
            [category.value for category in recommendation.missing_evaluations]
            if isinstance(recommendation, RecommendationWithheld)
            else []
        )
        return cls(
            level=view.level.value,
            badge_label=view.badge_label,
            statement=view.statement,
            conviction_gate_met=gate_result.conviction_gate_met,
            outlook_alignment=RecommendationOutlookAlignmentView.from_domain(outlook_context),
            missing_evaluations=missing_evaluations,
        )


class DecisionHistoryEntryView(CamelModel):
    decision_id: str
    decision_type: str
    reason: str
    investor_confidence: int
    decided_at: datetime
    observation_id: str | None

    @classmethod
    def from_domain(cls, decision: Decision) -> "DecisionHistoryEntryView":
        return cls(
            decision_id=str(decision.id.value),
            decision_type=decision.decision_type.value,
            reason=decision.investment_case.reason,
            investor_confidence=decision.confidence.value,
            decided_at=decision.decided_at,
            observation_id=str(decision.observation_id.value) if decision.observation_id else None,
        )


class ObservationEntryView(CamelModel):
    observation_id: str
    subject: str
    statement: str
    observed_at: datetime

    @classmethod
    def from_domain(cls, observation: Observation) -> "ObservationEntryView":
        return cls(
            observation_id=str(observation.id.value),
            subject=observation.subject.value,
            statement=observation.statement.value,
            observed_at=observation.observed_at,
        )


class OutcomeEntryView(CamelModel):
    outcome_id: str
    decision_id: str
    statement: str
    occurred_at: datetime

    @classmethod
    def from_domain(cls, outcome) -> "OutcomeEntryView":
        """`outcome` is `atlas.core.domain.outcome.entity.Outcome` --
        deliberately untyped here, mirroring
        `InvestmentCaseComposition.outcome_history`'s own untyped tuple:
        `atlas.alpha` may read Outcome via its repository but must never
        import the entity constructor itself (enforced by
        `tests/test_architecture_boundaries.py::test_alpha_does_not_write_to_outcome`)."""
        return cls(
            outcome_id=str(outcome.id.value),
            decision_id=str(outcome.decision_id.value),
            statement=outcome.statement.value,
            occurred_at=outcome.occurred_at,
        )


class CompanyProfileView(CamelModel):
    """(Investment Case Engine v1 slice; extended Company Data
    Foundation v1) Descriptive company identity, as currently known --
    every field beyond `ticker` may be `None`."""

    ticker: str
    name: str | None
    exchange: str | None
    sector: str | None
    industry: str | None
    country: str | None
    description: str | None
    as_of: datetime
    currency: str | None
    fiscal_year_end: str | None

    @classmethod
    def from_domain(cls, profile: CompanyProfile) -> "CompanyProfileView":
        return cls(
            ticker=profile.ticker,
            name=profile.name,
            exchange=profile.exchange,
            sector=profile.sector,
            industry=profile.industry,
            country=profile.country,
            description=profile.description,
            as_of=profile.as_of,
            currency=profile.currency,
            fiscal_year_end=profile.fiscal_year_end,
        )


class RegulatoryFilingView(CamelModel):
    """(Automatic Knowledge Ingestion Framework, Foundation Provider)
    One real SEC filing's own identity -- its existence and metadata,
    never its content."""

    form_type: str
    filed_at: datetime
    accession_number: str
    filing_url: str
    period_of_report: date | None

    @classmethod
    def from_domain(cls, filing: RegulatoryFiling) -> "RegulatoryFilingView":
        return cls(
            form_type=filing.form_type,
            filed_at=filing.filed_at,
            accession_number=filing.accession_number,
            filing_url=filing.filing_url,
            period_of_report=filing.period_of_report,
        )


class ValuationObservationView(CamelModel):
    period_end: date
    value: float

    @classmethod
    def from_domain(cls, observation: ValuationObservation) -> "ValuationObservationView":
        return cls(period_end=observation.period_end, value=observation.value)


class ValuationDeviationView(CamelModel):
    period_end: date
    value: float
    deviation_from_average: float

    @classmethod
    def from_domain(cls, deviation: ValuationDeviation) -> "ValuationDeviationView":
        return cls(
            period_end=deviation.period_end, value=deviation.value, deviation_from_average=deviation.deviation_from_average
        )


class ValuationMetricHistoryView(CamelModel):
    """(Capability Expansion Sprint 1: Historical Valuation
    Intelligence) Structured knowledge, never an opinion -- see
    `historical_valuation.py`'s own module docstring. Every field here
    is explainable: what is known (`observations`, `coverage_period_*`),
    where it stands relative to the company's own history
    (`current_percentile`, `position_in_range`, `trend`, `stability`),
    and what remains missing (`missing_periods`, `data_quality`)."""

    metric: str
    current_value: float | None
    current_period_end: date | None
    observations: list[ValuationObservationView]
    historical_average: float | None
    historical_median: float | None
    historical_minimum: float | None
    historical_maximum: float | None
    current_percentile: float | None
    position_in_range: str
    trend: str
    stability: str
    significant_deviations: list[ValuationDeviationView]
    coverage_period_start: date | None
    coverage_period_end: date | None
    missing_periods: list[date]
    data_quality: str

    @classmethod
    def from_domain(cls, metric: ValuationMetricHistory) -> "ValuationMetricHistoryView":
        return cls(
            metric=metric.metric.value,
            current_value=metric.current_value,
            current_period_end=metric.current_period_end,
            observations=[ValuationObservationView.from_domain(o) for o in metric.observations],
            historical_average=metric.historical_average,
            historical_median=metric.historical_median,
            historical_minimum=metric.historical_minimum,
            historical_maximum=metric.historical_maximum,
            current_percentile=metric.current_percentile,
            position_in_range=metric.position_in_range.value,
            trend=metric.trend.value,
            stability=metric.stability.value,
            significant_deviations=[ValuationDeviationView.from_domain(d) for d in metric.significant_deviations],
            coverage_period_start=metric.coverage_period_start,
            coverage_period_end=metric.coverage_period_end,
            missing_periods=list(metric.missing_periods),
            data_quality=metric.data_quality.value,
        )


class HistoricalValuationView(CamelModel):
    metrics: list[ValuationMetricHistoryView]

    @classmethod
    def from_domain(cls, knowledge: HistoricalValuationKnowledge) -> "HistoricalValuationView":
        return cls(metrics=[ValuationMetricHistoryView.from_domain(m) for m in knowledge.metrics])


class ManagementStatementView(CamelModel):
    """(Capability Expansion Sprint 2: Earnings Call Intelligence)
    `content` is always the verbatim transcript quote -- `categories`/
    `confidence` are the only things this pipeline adds. Traceable to
    its own transcript by nesting inside `EarningsCallTranscriptView`,
    never a floating, unattributed statement."""

    speaker: str
    title: str | None
    content: str
    categories: list[str]
    confidence: float | None
    source_reference: str

    @classmethod
    def from_domain(cls, statement: ManagementStatement) -> "ManagementStatementView":
        return cls(
            speaker=statement.speaker,
            title=statement.title,
            content=statement.content,
            categories=[c.value for c in statement.categories],
            confidence=statement.confidence,
            source_reference=statement.source_reference,
        )


class EarningsCallTranscriptView(CamelModel):
    quarter: str
    fiscal_date_ending: date | None
    published_at: date
    statements: list[ManagementStatementView]

    @classmethod
    def from_domain(cls, transcript: EarningsCallTranscript) -> "EarningsCallTranscriptView":
        return cls(
            quarter=transcript.quarter,
            fiscal_date_ending=transcript.fiscal_date_ending,
            published_at=transcript.published_at,
            statements=[ManagementStatementView.from_domain(s) for s in transcript.statements],
        )


class CommentaryCategoryChangeView(CamelModel):
    category: str
    previous_statement_count: int
    current_statement_count: int
    previous_average_confidence: float | None
    current_average_confidence: float | None
    emphasis_change: str
    sentiment_trend: str

    @classmethod
    def from_domain(cls, change: CommentaryCategoryChange) -> "CommentaryCategoryChangeView":
        return cls(
            category=change.category.value,
            previous_statement_count=change.previous_statement_count,
            current_statement_count=change.current_statement_count,
            previous_average_confidence=change.previous_average_confidence,
            current_average_confidence=change.current_average_confidence,
            emphasis_change=change.emphasis_change.value,
            sentiment_trend=change.sentiment_trend.value,
        )


class EarningsCallChangeIntelligenceView(CamelModel):
    previous_quarter: str | None
    current_quarter: str | None
    category_changes: list[CommentaryCategoryChangeView]

    @classmethod
    def from_domain(cls, change: EarningsCallChangeIntelligence) -> "EarningsCallChangeIntelligenceView":
        return cls(
            previous_quarter=change.previous_quarter,
            current_quarter=change.current_quarter,
            category_changes=[CommentaryCategoryChangeView.from_domain(c) for c in change.category_changes],
        )


class EarningsCallView(CamelModel):
    """(Capability Expansion Sprint 2) `change_intelligence` is derived
    here, once, from `transcripts` -- the identical "a cheap, pure,
    additional derived view computed at the presentation boundary"
    precedent `CoverageAssessment`/`RecommendationStateView` already
    establish in this same module, never a second persisted field."""

    transcripts: list[EarningsCallTranscriptView]
    change_intelligence: EarningsCallChangeIntelligenceView

    @classmethod
    def from_domain(cls, knowledge: EarningsCallKnowledge) -> "EarningsCallView":
        return cls(
            transcripts=[EarningsCallTranscriptView.from_domain(t) for t in knowledge.transcripts],
            change_intelligence=EarningsCallChangeIntelligenceView.from_domain(compute_change_intelligence(knowledge)),
        )


class IncomeStatementPeriodView(CamelModel):
    period_end: date
    revenue: float | None
    gross_profit: float | None
    operating_income: float | None
    ebitda: float | None
    net_income: float | None
    eps: float | None
    gross_margin: float | None
    operating_margin: float | None
    net_margin: float | None
    currency: str | None
    accounting_basis: str | None
    source_reference: str | None

    @classmethod
    def from_domain(cls, period: IncomeStatementPeriod) -> "IncomeStatementPeriodView":
        return cls(
            period_end=period.period_end, revenue=period.revenue, gross_profit=period.gross_profit,
            operating_income=period.operating_income, ebitda=period.ebitda, net_income=period.net_income,
            eps=period.eps, gross_margin=period.gross_margin, operating_margin=period.operating_margin,
            net_margin=period.net_margin, currency=period.currency, accounting_basis=period.accounting_basis,
            source_reference=period.source_reference,
        )


class BalanceSheetPeriodView(CamelModel):
    period_end: date
    cash: float | None
    total_debt: float | None
    equity: float | None
    current_assets: float | None
    current_liabilities: float | None
    working_capital: float | None
    total_assets: float | None
    tangible_assets: float | None
    intangible_assets: float | None
    currency: str | None
    accounting_basis: str | None
    source_reference: str | None

    @classmethod
    def from_domain(cls, period: BalanceSheetPeriod) -> "BalanceSheetPeriodView":
        return cls(
            period_end=period.period_end, cash=period.cash, total_debt=period.total_debt, equity=period.equity,
            current_assets=period.current_assets, current_liabilities=period.current_liabilities,
            working_capital=period.working_capital, total_assets=period.total_assets,
            tangible_assets=period.tangible_assets, intangible_assets=period.intangible_assets,
            currency=period.currency, accounting_basis=period.accounting_basis,
            source_reference=period.source_reference,
        )


class CashFlowStatementPeriodView(CamelModel):
    period_end: date
    operating_cash_flow: float | None
    investing_cash_flow: float | None
    financing_cash_flow: float | None
    free_cash_flow: float | None
    capital_expenditure: float | None
    currency: str | None
    accounting_basis: str | None
    source_reference: str | None

    @classmethod
    def from_domain(cls, period: CashFlowStatementPeriod) -> "CashFlowStatementPeriodView":
        return cls(
            period_end=period.period_end, operating_cash_flow=period.operating_cash_flow,
            investing_cash_flow=period.investing_cash_flow, financing_cash_flow=period.financing_cash_flow,
            free_cash_flow=period.free_cash_flow, capital_expenditure=period.capital_expenditure,
            currency=period.currency, accounting_basis=period.accounting_basis,
            source_reference=period.source_reference,
        )


class FinancialTrendObservationView(CamelModel):
    metric: str
    direction: str
    periods_considered: int

    @classmethod
    def from_domain(cls, observation: FinancialTrendObservation) -> "FinancialTrendObservationView":
        return cls(
            metric=observation.metric.value, direction=observation.direction.value,
            periods_considered=observation.periods_considered,
        )


class FinancialHealthView(CamelModel):
    """(Capability Expansion Sprint 3) Every tier here is a real,
    disclosed, single-ratio-based categorical bucket -- never combined
    into one composite score. See `financial_statement_intelligence.py`'s
    own module docstring."""

    liquidity: str
    solvency: str
    profitability: str
    cash_generation: str
    capital_efficiency: str
    balance_sheet_strength: str
    earnings_durability: str
    financial_flexibility: str

    @classmethod
    def from_domain(cls, health: FinancialHealthKnowledge) -> "FinancialHealthView":
        return cls(
            liquidity=health.liquidity.value, solvency=health.solvency.value,
            profitability=health.profitability.value, cash_generation=health.cash_generation.value,
            capital_efficiency=health.capital_efficiency.value,
            balance_sheet_strength=health.balance_sheet_strength.value,
            earnings_durability=health.earnings_durability.value,
            financial_flexibility=health.financial_flexibility.value,
        )


class FinancialStatementIntelligenceView(CamelModel):
    """(Capability Expansion Sprint 3) `trends`/`cash_flow_consistency`/
    `financial_health` are derived here, once, from `history` -- the
    identical presentation-boundary-derivation precedent `EarningsCallView
    .change_intelligence` already establishes above."""

    income_statements: list[IncomeStatementPeriodView]
    balance_sheets: list[BalanceSheetPeriodView]
    cash_flow_statements: list[CashFlowStatementPeriodView]
    trends: list[FinancialTrendObservationView]
    cash_flow_consistency: str
    financial_health: FinancialHealthView

    @classmethod
    def from_domain(cls, history: FinancialStatementHistory) -> "FinancialStatementIntelligenceView":
        return cls(
            income_statements=[IncomeStatementPeriodView.from_domain(p) for p in history.income_statements],
            balance_sheets=[BalanceSheetPeriodView.from_domain(p) for p in history.balance_sheets],
            cash_flow_statements=[CashFlowStatementPeriodView.from_domain(p) for p in history.cash_flow_statements],
            trends=[FinancialTrendObservationView.from_domain(o) for o in compute_trend_intelligence(history)],
            cash_flow_consistency=compute_cash_flow_consistency(history).value,
            financial_health=FinancialHealthView.from_domain(assess_financial_health(history)),
        )


class CapitalAllocationPeriodView(CamelModel):
    period_end: date
    capital_expenditure: float | None
    maintenance_capex: float | None
    growth_capex: float | None
    dividends: float | None
    share_buybacks: float | None
    treasury_shares_acquired: float | None
    share_issuance: float | None
    shares_outstanding: float | None
    debt_issuance: float | None
    debt_repayment: float | None
    total_debt: float | None
    acquisitions: float | None
    disposals: float | None
    investment_activity: float | None
    currency: str | None
    accounting_basis: str | None
    source_reference: str | None

    @classmethod
    def from_domain(cls, period: CapitalAllocationPeriod) -> "CapitalAllocationPeriodView":
        return cls(
            period_end=period.period_end, capital_expenditure=period.capital_expenditure,
            maintenance_capex=period.maintenance_capex, growth_capex=period.growth_capex,
            dividends=period.dividends, share_buybacks=period.share_buybacks,
            treasury_shares_acquired=period.treasury_shares_acquired, share_issuance=period.share_issuance,
            shares_outstanding=period.shares_outstanding, debt_issuance=period.debt_issuance,
            debt_repayment=period.debt_repayment, total_debt=period.total_debt, acquisitions=period.acquisitions,
            disposals=period.disposals, investment_activity=period.investment_activity, currency=period.currency,
            accounting_basis=period.accounting_basis, source_reference=period.source_reference,
        )


class CapitalAllocationTrendObservationView(CamelModel):
    metric: str
    direction: str
    periods_considered: int

    @classmethod
    def from_domain(cls, observation: CapitalAllocationTrendObservation) -> "CapitalAllocationTrendObservationView":
        return cls(
            metric=observation.metric.value, direction=observation.direction.value,
            periods_considered=observation.periods_considered,
        )


class ManagementCapitalAllocationView(CamelModel):
    """(Capability Expansion Sprint 4) Every field here is one real,
    disclosed, single-signal classification -- never combined into a
    management score. See `capital_allocation_intelligence.py`'s own
    module docstring."""

    reinvestment_discipline: str
    shareholder_return_policy: str
    financing_strategy: str
    acquisition_behavior: str
    debt_discipline: str
    capital_allocation_consistency: str

    @classmethod
    def from_domain(cls, knowledge: ManagementCapitalAllocationKnowledge) -> "ManagementCapitalAllocationView":
        return cls(
            reinvestment_discipline=knowledge.reinvestment_discipline.value,
            shareholder_return_policy=knowledge.shareholder_return_policy.value,
            financing_strategy=knowledge.financing_strategy.value,
            acquisition_behavior=knowledge.acquisition_behavior.value,
            debt_discipline=knowledge.debt_discipline.value,
            capital_allocation_consistency=knowledge.capital_allocation_consistency.value,
        )


class CapitalAllocationIntelligenceView(CamelModel):
    """(Capability Expansion Sprint 4) `trends`/`dividend_continuity`/
    `buyback_consistency`/`management` are all derived here, once, from
    `history` -- the identical presentation-boundary-derivation
    precedent `FinancialStatementIntelligenceView` already establishes."""

    periods: list[CapitalAllocationPeriodView]
    trends: list[CapitalAllocationTrendObservationView]
    dividend_continuity: str
    buyback_consistency: str
    management: ManagementCapitalAllocationView

    @classmethod
    def from_domain(cls, history: CapitalAllocationHistory) -> "CapitalAllocationIntelligenceView":
        return cls(
            periods=[CapitalAllocationPeriodView.from_domain(p) for p in history.periods],
            trends=[CapitalAllocationTrendObservationView.from_domain(o) for o in compute_capital_allocation_trends(history)],
            dividend_continuity=assess_dividend_continuity(history).value,
            buyback_consistency=assess_buyback_consistency(history).value,
            management=ManagementCapitalAllocationView.from_domain(assess_management_capital_allocation(history)),
        )


class CashConversionObservationView(CamelModel):
    period_end: date
    ocf_to_net_income: float | None
    fcf_to_net_income: float | None
    fcf_to_operating_income: float | None
    source_reference: str | None

    @classmethod
    def from_domain(cls, observation: CashConversionObservation) -> "CashConversionObservationView":
        return cls(
            period_end=observation.period_end, ocf_to_net_income=observation.ocf_to_net_income,
            fcf_to_net_income=observation.fcf_to_net_income, fcf_to_operating_income=observation.fcf_to_operating_income,
            source_reference=observation.source_reference,
        )


class CashConversionView(CamelModel):
    observations: list[CashConversionObservationView]
    ocf_conversion_pattern: str
    ocf_conversion_trend: str
    ocf_conversion_stability: str
    fcf_conversion_pattern: str
    fcf_conversion_trend: str
    fcf_conversion_stability: str

    @classmethod
    def from_domain(cls, knowledge: CashConversionKnowledge) -> "CashConversionView":
        return cls(
            observations=[CashConversionObservationView.from_domain(o) for o in knowledge.observations],
            ocf_conversion_pattern=knowledge.ocf_conversion_pattern.value,
            ocf_conversion_trend=knowledge.ocf_conversion_trend.value,
            ocf_conversion_stability=knowledge.ocf_conversion_stability.value,
            fcf_conversion_pattern=knowledge.fcf_conversion_pattern.value,
            fcf_conversion_trend=knowledge.fcf_conversion_trend.value,
            fcf_conversion_stability=knowledge.fcf_conversion_stability.value,
        )


class WorkingCapitalObservationView(CamelModel):
    period_end: date
    working_capital: float | None
    working_capital_to_revenue: float | None
    change_from_prior_period: float | None
    source_reference: str | None

    @classmethod
    def from_domain(cls, observation: WorkingCapitalObservation) -> "WorkingCapitalObservationView":
        return cls(
            period_end=observation.period_end, working_capital=observation.working_capital,
            working_capital_to_revenue=observation.working_capital_to_revenue,
            change_from_prior_period=observation.change_from_prior_period,
            source_reference=observation.source_reference,
        )


class WorkingCapitalIntelligenceView(CamelModel):
    observations: list[WorkingCapitalObservationView]
    trend: str
    most_recent_direction: str
    stability: str

    @classmethod
    def from_domain(cls, knowledge: WorkingCapitalIntelligence) -> "WorkingCapitalIntelligenceView":
        return cls(
            observations=[WorkingCapitalObservationView.from_domain(o) for o in knowledge.observations],
            trend=knowledge.trend.value, most_recent_direction=knowledge.most_recent_direction.value,
            stability=knowledge.stability.value,
        )


class MarginReversalView(CamelModel):
    period_end: date
    margin_value: float
    deviation_from_average: float
    source_reference: str | None

    @classmethod
    def from_domain(cls, reversal: MarginReversal) -> "MarginReversalView":
        return cls(
            period_end=reversal.period_end, margin_value=reversal.margin_value,
            deviation_from_average=reversal.deviation_from_average, source_reference=reversal.source_reference,
        )


class MarginDurabilityView(CamelModel):
    margin: str
    current_level: float | None
    trend: str
    stability: str
    reversals: list[MarginReversalView]
    periods_considered: int

    @classmethod
    def from_domain(cls, durability: MarginDurability) -> "MarginDurabilityView":
        return cls(
            margin=durability.margin.value, current_level=durability.current_level, trend=durability.trend.value,
            stability=durability.stability.value,
            reversals=[MarginReversalView.from_domain(r) for r in durability.reversals],
            periods_considered=durability.periods_considered,
        )


class ProfitabilityDurabilityView(CamelModel):
    gross_margin: MarginDurabilityView
    operating_margin: MarginDurabilityView
    net_margin: MarginDurabilityView

    @classmethod
    def from_domain(cls, durability: ProfitabilityDurability) -> "ProfitabilityDurabilityView":
        return cls(
            gross_margin=MarginDurabilityView.from_domain(durability.gross_margin),
            operating_margin=MarginDurabilityView.from_domain(durability.operating_margin),
            net_margin=MarginDurabilityView.from_domain(durability.net_margin),
        )


class CapitalEfficiencyObservationView(CamelModel):
    period_end: date
    return_on_assets: float | None
    return_on_equity: float | None
    asset_turnover: float | None
    source_reference: str | None

    @classmethod
    def from_domain(cls, observation: CapitalEfficiencyObservation) -> "CapitalEfficiencyObservationView":
        return cls(
            period_end=observation.period_end, return_on_assets=observation.return_on_assets,
            return_on_equity=observation.return_on_equity, asset_turnover=observation.asset_turnover,
            source_reference=observation.source_reference,
        )


class CapitalEfficiencyView(CamelModel):
    """(Capability Expansion Sprint 5) `return_on_invested_capital_
    unavailable_reason` names, as real structured knowledge, why ROIC
    is not computed -- see `financial_quality_intelligence.py`'s own
    module docstring."""

    observations: list[CapitalEfficiencyObservationView]
    return_on_assets_trend: str
    return_on_equity_trend: str
    asset_turnover_trend: str
    capital_intensity_trend: str
    return_on_invested_capital_unavailable_reason: str

    @classmethod
    def from_domain(cls, knowledge: CapitalEfficiencyKnowledge) -> "CapitalEfficiencyView":
        return cls(
            observations=[CapitalEfficiencyObservationView.from_domain(o) for o in knowledge.observations],
            return_on_assets_trend=knowledge.return_on_assets_trend.value,
            return_on_equity_trend=knowledge.return_on_equity_trend.value,
            asset_turnover_trend=knowledge.asset_turnover_trend.value,
            capital_intensity_trend=knowledge.capital_intensity_trend.value,
            return_on_invested_capital_unavailable_reason=knowledge.return_on_invested_capital_unavailable_reason.value,
        )


class FinancialDurabilityView(CamelModel):
    findings: list[str]

    @classmethod
    def from_domain(cls, knowledge: FinancialDurabilityKnowledge) -> "FinancialDurabilityView":
        return cls(findings=[f.value for f in knowledge.findings])


class FinancialQualityIntelligenceView(CamelModel):
    """(Capability Expansion Sprint 5) A pure, second-order
    transformation of `FinancialStatementIntelligenceView`'s own already
    -covered data -- see `financial_quality_intelligence.py`'s own
    module docstring for why this introduces no new Knowledge Coverage
    domain."""

    cash_conversion: CashConversionView
    working_capital: WorkingCapitalIntelligenceView
    profitability_durability: ProfitabilityDurabilityView
    capital_efficiency: CapitalEfficiencyView
    financial_durability: FinancialDurabilityView

    @classmethod
    def from_domain(cls, knowledge: FinancialQualityKnowledge) -> "FinancialQualityIntelligenceView":
        return cls(
            cash_conversion=CashConversionView.from_domain(knowledge.cash_conversion),
            working_capital=WorkingCapitalIntelligenceView.from_domain(knowledge.working_capital),
            profitability_durability=ProfitabilityDurabilityView.from_domain(knowledge.profitability_durability),
            capital_efficiency=CapitalEfficiencyView.from_domain(knowledge.capital_efficiency),
            financial_durability=FinancialDurabilityView.from_domain(knowledge.financial_durability),
        )


class GrowthObservationView(CamelModel):
    period_end: date
    value: float | None
    year_over_year_growth: float | None

    @classmethod
    def from_domain(cls, observation: GrowthObservation) -> "GrowthObservationView":
        return cls(
            period_end=observation.period_end, value=observation.value,
            year_over_year_growth=observation.year_over_year_growth,
        )


class GrowthDurabilityView(CamelModel):
    consistency: str
    consecutive_growth_periods: int
    recovery_status: str

    @classmethod
    def from_domain(cls, durability: GrowthDurability) -> "GrowthDurabilityView":
        return cls(
            consistency=durability.consistency.value,
            consecutive_growth_periods=durability.consecutive_growth_periods,
            recovery_status=durability.recovery_status.value,
        )


class GrowthTrendKnowledgeView(CamelModel):
    metric: str
    observations: list[GrowthObservationView]
    cagr: float | None
    direction: str
    pattern: str
    durability: GrowthDurabilityView
    periods_considered: int

    @classmethod
    def from_domain(cls, trend: GrowthTrendKnowledge) -> "GrowthTrendKnowledgeView":
        return cls(
            metric=trend.metric.value,
            observations=[GrowthObservationView.from_domain(o) for o in trend.observations],
            cagr=trend.cagr, direction=trend.direction.value, pattern=trend.pattern.value,
            durability=GrowthDurabilityView.from_domain(trend.durability),
            periods_considered=trend.periods_considered,
        )


class SegmentGrowthInformationView(CamelModel):
    available: bool

    @classmethod
    def from_domain(cls, segment_growth: SegmentGrowthInformation) -> "SegmentGrowthInformationView":
        return cls(available=segment_growth.available)


class GrowthKnowledgeView(CamelModel):
    """(Capability Expansion Sprint 6) Structured knowledge describing
    the nature, consistency and durability of growth -- see
    `growth_intelligence.py`'s own module docstring."""

    revenue: GrowthTrendKnowledgeView
    earnings: GrowthTrendKnowledgeView
    operating_cash_flow: GrowthTrendKnowledgeView
    free_cash_flow: GrowthTrendKnowledgeView
    book_value: GrowthTrendKnowledgeView
    earnings_per_share: GrowthTrendKnowledgeView
    segment_growth: SegmentGrowthInformationView

    @classmethod
    def from_domain(cls, knowledge: GrowthKnowledge) -> "GrowthKnowledgeView":
        return cls(
            revenue=GrowthTrendKnowledgeView.from_domain(knowledge.revenue),
            earnings=GrowthTrendKnowledgeView.from_domain(knowledge.earnings),
            operating_cash_flow=GrowthTrendKnowledgeView.from_domain(knowledge.operating_cash_flow),
            free_cash_flow=GrowthTrendKnowledgeView.from_domain(knowledge.free_cash_flow),
            book_value=GrowthTrendKnowledgeView.from_domain(knowledge.book_value),
            earnings_per_share=GrowthTrendKnowledgeView.from_domain(knowledge.earnings_per_share),
            segment_growth=SegmentGrowthInformationView.from_domain(knowledge.segment_growth),
        )


class BusinessStabilityView(CamelModel):
    profitability_stability: str
    revenue_stability: str
    cash_generation_stability: str
    capital_allocation_stability: str

    @classmethod
    def from_domain(cls, stability: BusinessStability) -> "BusinessStabilityView":
        return cls(
            profitability_stability=stability.profitability_stability.value,
            revenue_stability=stability.revenue_stability.value,
            cash_generation_stability=stability.cash_generation_stability.value,
            capital_allocation_stability=stability.capital_allocation_stability.value,
        )


class GrowthDurabilitySummaryView(CamelModel):
    metrics_with_consistent_growth: list[str]
    metrics_with_consistent_decline: list[str]
    metrics_recovered_from_decline: list[str]

    @classmethod
    def from_domain(cls, summary: GrowthDurabilitySummary) -> "GrowthDurabilitySummaryView":
        return cls(
            metrics_with_consistent_growth=[m.value for m in summary.metrics_with_consistent_growth],
            metrics_with_consistent_decline=[m.value for m in summary.metrics_with_consistent_decline],
            metrics_recovered_from_decline=[m.value for m in summary.metrics_recovered_from_decline],
        )


class BusinessDurabilityView(CamelModel):
    financial_durability: FinancialDurabilityView
    earnings_durability: str
    growth_durability: GrowthDurabilitySummaryView
    capital_discipline: ManagementCapitalAllocationView

    @classmethod
    def from_domain(cls, durability: BusinessDurability) -> "BusinessDurabilityView":
        return cls(
            financial_durability=FinancialDurabilityView.from_domain(durability.financial_durability),
            earnings_durability=durability.earnings_durability.value,
            growth_durability=GrowthDurabilitySummaryView.from_domain(durability.growth_durability),
            capital_discipline=ManagementCapitalAllocationView.from_domain(durability.capital_discipline),
        )


class BusinessEfficiencyView(CamelModel):
    capital_efficiency: CapitalEfficiencyView
    asset_efficiency_trend: str
    operating_efficiency_trend: str

    @classmethod
    def from_domain(cls, efficiency: BusinessEfficiency) -> "BusinessEfficiencyView":
        return cls(
            capital_efficiency=CapitalEfficiencyView.from_domain(efficiency.capital_efficiency),
            asset_efficiency_trend=efficiency.asset_efficiency_trend.value,
            operating_efficiency_trend=efficiency.operating_efficiency_trend.value,
        )


class HistoricalDisruptionView(CamelModel):
    margin: str
    period_end: date
    margin_value: float
    deviation_from_average: float

    @classmethod
    def from_domain(cls, disruption: HistoricalDisruption) -> "HistoricalDisruptionView":
        return cls(
            margin=disruption.margin.value, period_end=disruption.period_end, margin_value=disruption.margin_value,
            deviation_from_average=disruption.deviation_from_average,
        )


class BusinessConsistencyView(CamelModel):
    stable_dimensions: list[str]
    volatile_dimensions: list[str]
    major_historical_disruptions: list[HistoricalDisruptionView]

    @classmethod
    def from_domain(cls, consistency: BusinessConsistency) -> "BusinessConsistencyView":
        return cls(
            stable_dimensions=list(consistency.stable_dimensions),
            volatile_dimensions=list(consistency.volatile_dimensions),
            major_historical_disruptions=[
                HistoricalDisruptionView.from_domain(d) for d in consistency.major_historical_disruptions
            ],
        )


class BusinessEvolutionView(CamelModel):
    direction: str
    strengthening_signals: list[str]
    weakening_signals: list[str]

    @classmethod
    def from_domain(cls, evolution: BusinessEvolution) -> "BusinessEvolutionView":
        return cls(
            direction=evolution.direction.value,
            strengthening_signals=list(evolution.strengthening_signals),
            weakening_signals=list(evolution.weakening_signals),
        )


class BusinessQualityFindingView(CamelModel):
    kind: str
    supporting_dimensions: list[str]

    @classmethod
    def from_domain(cls, finding: BusinessQualityFinding) -> "BusinessQualityFindingView":
        return cls(kind=finding.kind.value, supporting_dimensions=list(finding.supporting_dimensions))


class BusinessQualityIntelligenceView(CamelModel):
    """(Capability Expansion Sprint 7) A pure, higher-order aggregation
    over Financial Statement/Capital Allocation/Financial Quality/Growth
    Intelligence's own already-computed outputs -- see `business_
    quality_intelligence.py`'s own module docstring."""

    stability: BusinessStabilityView
    durability: BusinessDurabilityView
    efficiency: BusinessEfficiencyView
    consistency: BusinessConsistencyView
    evolution: BusinessEvolutionView
    findings: list[BusinessQualityFindingView]

    @classmethod
    def from_domain(cls, knowledge: BusinessQualityKnowledge) -> "BusinessQualityIntelligenceView":
        return cls(
            stability=BusinessStabilityView.from_domain(knowledge.stability),
            durability=BusinessDurabilityView.from_domain(knowledge.durability),
            efficiency=BusinessEfficiencyView.from_domain(knowledge.efficiency),
            consistency=BusinessConsistencyView.from_domain(knowledge.consistency),
            evolution=BusinessEvolutionView.from_domain(knowledge.evolution),
            findings=[BusinessQualityFindingView.from_domain(f) for f in knowledge.findings],
        )


class ManagementCommitmentView(CamelModel):
    signal: str
    commitment_category: str
    statement_date: date
    reporting_period: str
    fiscal_date_ending: date | None
    speaker: str
    source_transcript: str
    supporting_quotation: str
    revision_direction: str | None
    outcome: str

    @classmethod
    def from_domain(cls, commitment: ManagementCommitment) -> "ManagementCommitmentView":
        return cls(
            signal=commitment.signal.value, commitment_category=commitment.commitment_category.value,
            statement_date=commitment.statement_date, reporting_period=commitment.reporting_period,
            fiscal_date_ending=commitment.fiscal_date_ending, speaker=commitment.speaker,
            source_transcript=commitment.source_transcript, supporting_quotation=commitment.supporting_quotation,
            revision_direction=commitment.revision_direction.value if commitment.revision_direction is not None else None,
            outcome=commitment.outcome.value,
        )


class CommunicationConsistencyView(CamelModel):
    direction: str
    strengthened_categories: list[str]
    weakened_categories: list[str]
    guidance_changed: bool
    strategic_emphasis_shifted: bool

    @classmethod
    def from_domain(cls, consistency: CommunicationConsistency) -> "CommunicationConsistencyView":
        return cls(
            direction=consistency.direction.value,
            strengthened_categories=[c.value for c in consistency.strengthened_categories],
            weakened_categories=[c.value for c in consistency.weakened_categories],
            guidance_changed=consistency.guidance_changed,
            strategic_emphasis_shifted=consistency.strategic_emphasis_shifted,
        )


class GuidanceReliabilityView(CamelModel):
    guidance_history: list[ManagementCommitmentView]
    guidance_revisions: list[ManagementCommitmentView]
    fulfilled_guidance_count: int
    withdrawn_guidance_count: int
    unresolved_guidance_count: int

    @classmethod
    def from_domain(cls, guidance: GuidanceReliabilityKnowledge) -> "GuidanceReliabilityView":
        return cls(
            guidance_history=[ManagementCommitmentView.from_domain(c) for c in guidance.guidance_history],
            guidance_revisions=[ManagementCommitmentView.from_domain(c) for c in guidance.guidance_revisions],
            fulfilled_guidance_count=guidance.fulfilled_guidance_count,
            withdrawn_guidance_count=guidance.withdrawn_guidance_count,
            unresolved_guidance_count=guidance.unresolved_guidance_count,
        )


class CredibilityFindingView(CamelModel):
    kind: str
    supporting_commitments: list[ManagementCommitmentView]

    @classmethod
    def from_domain(cls, finding: CredibilityFinding) -> "CredibilityFindingView":
        return cls(
            kind=finding.kind.value,
            supporting_commitments=[ManagementCommitmentView.from_domain(c) for c in finding.supporting_commitments],
        )


class ManagementCredibilityIntelligenceView(CamelModel):
    """(Capability Expansion Sprint 8) A pure, higher-order aggregation
    over Earnings Call/Financial Statement/Growth/Capital Allocation
    Intelligence's own already-computed outputs -- see `management_
    credibility_intelligence.py`'s own module docstring."""

    commitments: list[ManagementCommitmentView]
    communication_consistency: CommunicationConsistencyView
    guidance_reliability: GuidanceReliabilityView
    execution_consistency: str
    findings: list[CredibilityFindingView]

    @classmethod
    def from_domain(cls, knowledge: ManagementCredibilityKnowledge) -> "ManagementCredibilityIntelligenceView":
        return cls(
            commitments=[ManagementCommitmentView.from_domain(c) for c in knowledge.commitments],
            communication_consistency=CommunicationConsistencyView.from_domain(knowledge.communication_consistency),
            guidance_reliability=GuidanceReliabilityView.from_domain(knowledge.guidance_reliability),
            execution_consistency=knowledge.execution_consistency.value,
            findings=[CredibilityFindingView.from_domain(f) for f in knowledge.findings],
        )


class ExplicitTargetView(CamelModel):
    value: float
    unit: str

    @classmethod
    def from_domain(cls, target: ExplicitTarget) -> "ExplicitTargetView":
        return cls(value=target.value, unit=target.unit.value)


class ExplicitTargetRangeView(CamelModel):
    low: float
    high: float
    unit: str

    @classmethod
    def from_domain(cls, target_range: ExplicitTargetRange) -> "ExplicitTargetRangeView":
        return cls(low=target_range.low, high=target_range.high, unit=target_range.unit.value)


class GuidanceItemView(CamelModel):
    guidance_type: str
    speaker: str
    reporting_period: str
    statement_date: date
    fiscal_date_ending: date | None
    source_transcript: str
    direction: str
    explicit_target: ExplicitTargetView | None
    explicit_target_range: ExplicitTargetRangeView | None
    confidence_wording: str
    supporting_quotation: str
    status: str
    revision_kind: str
    outcome: str

    @classmethod
    def from_domain(cls, item: GuidanceItem) -> "GuidanceItemView":
        return cls(
            guidance_type=item.guidance_type.value, speaker=item.speaker, reporting_period=item.reporting_period,
            statement_date=item.statement_date, fiscal_date_ending=item.fiscal_date_ending,
            source_transcript=item.source_transcript, direction=item.direction.value,
            explicit_target=ExplicitTargetView.from_domain(item.explicit_target) if item.explicit_target is not None else None,
            explicit_target_range=(
                ExplicitTargetRangeView.from_domain(item.explicit_target_range)
                if item.explicit_target_range is not None else None
            ),
            confidence_wording=item.confidence_wording.value, supporting_quotation=item.supporting_quotation,
            status=item.status.value, revision_kind=item.revision_kind.value, outcome=item.outcome.value,
        )


class GuidanceReliabilitySummaryView(CamelModel):
    total_guidance_count: int
    revision_count: int
    fulfilled_count: int
    partially_fulfilled_count: int
    missed_count: int
    unresolved_count: int
    withdrawn_count: int

    @classmethod
    def from_domain(cls, summary: GuidanceReliabilitySummary) -> "GuidanceReliabilitySummaryView":
        return cls(
            total_guidance_count=summary.total_guidance_count, revision_count=summary.revision_count,
            fulfilled_count=summary.fulfilled_count, partially_fulfilled_count=summary.partially_fulfilled_count,
            missed_count=summary.missed_count, unresolved_count=summary.unresolved_count,
            withdrawn_count=summary.withdrawn_count,
        )


class ManagementGuidanceIntelligenceView(CamelModel):
    """(Capability Expansion Sprint 9) A pure, higher-order aggregation
    over Earnings Call/Financial Statement/Growth Intelligence's own
    already-computed outputs -- see `management_guidance_intelligence
    .py`'s own module docstring."""

    guidance_items: list[GuidanceItemView]
    reliability: GuidanceReliabilitySummaryView

    @classmethod
    def from_domain(cls, knowledge: ManagementGuidanceKnowledge) -> "ManagementGuidanceIntelligenceView":
        return cls(
            guidance_items=[GuidanceItemView.from_domain(g) for g in knowledge.guidance_items],
            reliability=GuidanceReliabilitySummaryView.from_domain(knowledge.reliability),
        )


class ExecutiveIdentityView(CamelModel):
    name: str
    role_category: str
    raw_title: str | None
    company: str | None
    start_date: date | None
    end_date: date | None
    is_interim: bool
    first_observed_date: date
    last_observed_date: date
    source_transcripts: list[str]
    statement_count: int

    @classmethod
    def from_domain(cls, identity: ExecutiveIdentity) -> "ExecutiveIdentityView":
        return cls(
            name=identity.name, role_category=identity.role_category.value, raw_title=identity.raw_title,
            company=identity.company, start_date=identity.start_date, end_date=identity.end_date,
            is_interim=identity.is_interim, first_observed_date=identity.first_observed_date,
            last_observed_date=identity.last_observed_date, source_transcripts=list(identity.source_transcripts),
            statement_count=identity.statement_count,
        )


class LeadershipChangeEventView(CamelModel):
    event_type: str
    executive_name: str
    role_category: str
    prior_role_category: str | None
    effective_date: date | None
    announcement_date: date | None
    observed_date: date
    source_transcript: str
    provenance: str

    @classmethod
    def from_domain(cls, event: LeadershipChangeEvent) -> "LeadershipChangeEventView":
        return cls(
            event_type=event.event_type.value, executive_name=event.executive_name,
            role_category=event.role_category.value,
            prior_role_category=event.prior_role_category.value if event.prior_role_category is not None else None,
            effective_date=event.effective_date, announcement_date=event.announcement_date,
            observed_date=event.observed_date, source_transcript=event.source_transcript, provenance=event.provenance,
        )


class SuccessionRelationshipView(CamelModel):
    role_category: str
    outgoing_executive_name: str
    outgoing_last_observed_date: date
    incoming_executive_name: str
    incoming_first_observed_date: date
    evidence: str

    @classmethod
    def from_domain(cls, succession: SuccessionRelationship) -> "SuccessionRelationshipView":
        return cls(
            role_category=succession.role_category.value, outgoing_executive_name=succession.outgoing_executive_name,
            outgoing_last_observed_date=succession.outgoing_last_observed_date,
            incoming_executive_name=succession.incoming_executive_name,
            incoming_first_observed_date=succession.incoming_first_observed_date, evidence=succession.evidence,
        )


class LeadershipChangeFindingView(CamelModel):
    kind: str
    supporting_executives: list[str]
    supporting_events: list[LeadershipChangeEventView]

    @classmethod
    def from_domain(cls, finding: LeadershipChangeFinding) -> "LeadershipChangeFindingView":
        return cls(
            kind=finding.kind.value, supporting_executives=list(finding.supporting_executives),
            supporting_events=[LeadershipChangeEventView.from_domain(e) for e in finding.supporting_events],
        )


class ExecutiveChangeIntelligenceView(CamelModel):
    """(Capability Expansion Sprint 10) A pure, higher-order aggregation
    over Earnings Call Intelligence's own already-classified speaker/
    title metadata -- see `executive_change_intelligence.py`'s own
    module docstring."""

    executives: list[ExecutiveIdentityView]
    leadership_changes: list[LeadershipChangeEventView]
    successions: list[SuccessionRelationshipView]
    findings: list[LeadershipChangeFindingView]

    @classmethod
    def from_domain(cls, knowledge: ExecutiveChangeKnowledge) -> "ExecutiveChangeIntelligenceView":
        return cls(
            executives=[ExecutiveIdentityView.from_domain(e) for e in knowledge.executives],
            leadership_changes=[LeadershipChangeEventView.from_domain(e) for e in knowledge.leadership_changes],
            successions=[SuccessionRelationshipView.from_domain(s) for s in knowledge.successions],
            findings=[LeadershipChangeFindingView.from_domain(f) for f in knowledge.findings],
        )


class TenureContextView(CamelModel):
    financial_periods: list[IncomeStatementPeriodView]
    earnings_calls: list[EarningsCallTranscriptView]
    capital_allocation_periods: list[CapitalAllocationPeriodView]
    growth_observations: list[GrowthObservationView]
    commitments: list[ManagementCommitmentView]

    @classmethod
    def from_domain(cls, context: TenureContext) -> "TenureContextView":
        return cls(
            financial_periods=[IncomeStatementPeriodView.from_domain(p) for p in context.financial_periods],
            earnings_calls=[EarningsCallTranscriptView.from_domain(t) for t in context.earnings_calls],
            capital_allocation_periods=[
                CapitalAllocationPeriodView.from_domain(p) for p in context.capital_allocation_periods
            ],
            growth_observations=[GrowthObservationView.from_domain(o) for o in context.growth_observations],
            commitments=[ManagementCommitmentView.from_domain(c) for c in context.commitments],
        )


class TenureGuidanceHistoryView(CamelModel):
    issued: list[GuidanceItemView]
    revised: list[GuidanceItemView]
    completed: list[GuidanceItemView]
    unresolved: list[GuidanceItemView]
    fulfilled: list[GuidanceItemView]
    withdrawn: list[GuidanceItemView]

    @classmethod
    def from_domain(cls, history: TenureGuidanceHistory) -> "TenureGuidanceHistoryView":
        return cls(
            issued=[GuidanceItemView.from_domain(g) for g in history.issued],
            revised=[GuidanceItemView.from_domain(g) for g in history.revised],
            completed=[GuidanceItemView.from_domain(g) for g in history.completed],
            unresolved=[GuidanceItemView.from_domain(g) for g in history.unresolved],
            fulfilled=[GuidanceItemView.from_domain(g) for g in history.fulfilled],
            withdrawn=[GuidanceItemView.from_domain(g) for g in history.withdrawn],
        )


class TenureTimelineView(CamelModel):
    own_events: list[LeadershipChangeEventView]
    overlapping_executives: list[ExecutiveIdentityView]

    @classmethod
    def from_domain(cls, timeline: TenureTimeline) -> "TenureTimelineView":
        return cls(
            own_events=[LeadershipChangeEventView.from_domain(e) for e in timeline.own_events],
            overlapping_executives=[ExecutiveIdentityView.from_domain(e) for e in timeline.overlapping_executives],
        )


class TrackRecordFindingView(CamelModel):
    kind: str
    evidence_count: int

    @classmethod
    def from_domain(cls, finding: TrackRecordFinding) -> "TrackRecordFindingView":
        return cls(kind=finding.kind.value, evidence_count=finding.evidence_count)


class ExecutiveTenureRecordView(CamelModel):
    executive: ExecutiveIdentityView
    evidence_completeness: str
    context: TenureContextView
    guidance_history: TenureGuidanceHistoryView
    timeline: TenureTimelineView
    findings: list[TrackRecordFindingView]

    @classmethod
    def from_domain(cls, record: ExecutiveTenureRecord) -> "ExecutiveTenureRecordView":
        return cls(
            executive=ExecutiveIdentityView.from_domain(record.executive),
            evidence_completeness=record.evidence_completeness.value,
            context=TenureContextView.from_domain(record.context),
            guidance_history=TenureGuidanceHistoryView.from_domain(record.guidance_history),
            timeline=TenureTimelineView.from_domain(record.timeline),
            findings=[TrackRecordFindingView.from_domain(f) for f in record.findings],
        )


class ExecutiveTrackRecordIntelligenceView(CamelModel):
    """(Capability Expansion Sprint 11) A pure, higher-order aggregation
    over Executive Change/Management Guidance/Management Credibility
    Intelligence's own already-computed outputs -- see `executive_
    track_record_intelligence.py`'s own module docstring."""

    tenures: list[ExecutiveTenureRecordView]

    @classmethod
    def from_domain(cls, knowledge: ExecutiveTrackRecordKnowledge) -> "ExecutiveTrackRecordIntelligenceView":
        return cls(tenures=[ExecutiveTenureRecordView.from_domain(t) for t in knowledge.tenures])


class EquityIncentiveView(CamelModel):
    executive_name: str
    kind: str
    program: str | None
    source: str | None
    effective_period: str | None
    status: str
    provenance: str

    @classmethod
    def from_domain(cls, incentive: EquityIncentive) -> "EquityIncentiveView":
        return cls(
            executive_name=incentive.executive_name, kind=incentive.kind.value, program=incentive.program,
            source=incentive.source, effective_period=incentive.effective_period, status=incentive.status.value,
            provenance=incentive.provenance,
        )


class CashIncentiveView(CamelModel):
    executive_name: str
    kind: str
    program: str | None
    source: str | None
    effective_period: str | None
    status: str
    provenance: str

    @classmethod
    def from_domain(cls, incentive: CashIncentive) -> "CashIncentiveView":
        return cls(
            executive_name=incentive.executive_name, kind=incentive.kind.value, program=incentive.program,
            source=incentive.source, effective_period=incentive.effective_period, status=incentive.status.value,
            provenance=incentive.provenance,
        )


class PerformanceIncentiveView(CamelModel):
    executive_name: str
    metric_kind: str
    explicit_target: float | None
    program: str | None
    source: str | None
    status: str
    provenance: str

    @classmethod
    def from_domain(cls, incentive: PerformanceIncentive) -> "PerformanceIncentiveView":
        return cls(
            executive_name=incentive.executive_name, metric_kind=incentive.metric_kind.value,
            explicit_target=incentive.explicit_target, program=incentive.program, source=incentive.source,
            status=incentive.status.value, provenance=incentive.provenance,
        )


class ExecutiveIncentiveProgramView(CamelModel):
    executive_name: str
    role: str | None
    program: str | None
    source: str | None
    effective_period: str | None
    status: str
    equity_incentives: list[EquityIncentiveView]
    cash_incentives: list[CashIncentiveView]
    performance_incentives: list[PerformanceIncentiveView]

    @classmethod
    def from_domain(cls, program: ExecutiveIncentiveProgram) -> "ExecutiveIncentiveProgramView":
        return cls(
            executive_name=program.executive_name, role=program.role, program=program.program,
            source=program.source, effective_period=program.effective_period, status=program.status.value,
            equity_incentives=[EquityIncentiveView.from_domain(e) for e in program.equity_incentives],
            cash_incentives=[CashIncentiveView.from_domain(c) for c in program.cash_incentives],
            performance_incentives=[PerformanceIncentiveView.from_domain(p) for p in program.performance_incentives],
        )


class IncentiveTimelineEventView(CamelModel):
    kind: str
    executive_name: str | None
    program: str | None
    effective_date: date | None
    source: str | None
    provenance: str

    @classmethod
    def from_domain(cls, event: IncentiveTimelineEvent) -> "IncentiveTimelineEventView":
        return cls(
            kind=event.kind.value, executive_name=event.executive_name, program=event.program,
            effective_date=event.effective_date, source=event.source, provenance=event.provenance,
        )


class OwnershipAlignmentView(CamelModel):
    executive_name: str
    shares_owned: float | None
    ownership_guideline: str | None
    status: str
    source: str | None
    provenance: str

    @classmethod
    def from_domain(cls, alignment: OwnershipAlignment) -> "OwnershipAlignmentView":
        return cls(
            executive_name=alignment.executive_name, shares_owned=alignment.shares_owned,
            ownership_guideline=alignment.ownership_guideline, status=alignment.status.value,
            source=alignment.source, provenance=alignment.provenance,
        )


class DilutionEventView(CamelModel):
    kind: str
    executive_name: str | None
    shares: float | None
    effective_date: date | None
    source: str | None
    provenance: str

    @classmethod
    def from_domain(cls, event: DilutionEvent) -> "DilutionEventView":
        return cls(
            kind=event.kind.value, executive_name=event.executive_name, shares=event.shares,
            effective_date=event.effective_date, source=event.source, provenance=event.provenance,
        )


class IncentiveStructureView(CamelModel):
    executive_name: str
    components: list[str]
    source: str | None
    provenance: str

    @classmethod
    def from_domain(cls, structure: IncentiveStructure) -> "IncentiveStructureView":
        return cls(
            executive_name=structure.executive_name, components=[c.value for c in structure.components],
            source=structure.source, provenance=structure.provenance,
        )


class CompensationDisclosureFilingView(CamelModel):
    filing: RegulatoryFilingView

    @classmethod
    def from_domain(cls, disclosure: CompensationDisclosureFiling) -> "CompensationDisclosureFilingView":
        return cls(filing=RegulatoryFilingView.from_domain(disclosure.filing))


class IncentiveChangeFindingView(CamelModel):
    kind: str
    evidence_count: int

    @classmethod
    def from_domain(cls, finding: IncentiveChangeFinding) -> "IncentiveChangeFindingView":
        return cls(kind=finding.kind.value, evidence_count=finding.evidence_count)


class IncentiveIntelligenceView(CamelModel):
    """(Capability Expansion Sprint 12) A pure re-labeling of
    `RegulatoryFiling`'s own `DEF 14A` records -- see `incentive_
    intelligence.py`'s own module docstring for why every other field
    below is always an empty list in this build. Each is nonetheless
    given its own complete, typed view -- the shape a future filing-
    content-reading capability can populate without redesigning this
    schema."""

    compensation_disclosure_filings: list[CompensationDisclosureFilingView]
    executive_incentive_programs: list[ExecutiveIncentiveProgramView]
    timeline: list[IncentiveTimelineEventView]
    ownership_alignment: list[OwnershipAlignmentView]
    dilution_events: list[DilutionEventView]
    incentive_structures: list[IncentiveStructureView]
    findings: list[IncentiveChangeFindingView]

    @classmethod
    def from_domain(cls, knowledge: IncentiveKnowledge) -> "IncentiveIntelligenceView":
        return cls(
            compensation_disclosure_filings=[
                CompensationDisclosureFilingView.from_domain(d) for d in knowledge.compensation_disclosure_filings
            ],
            executive_incentive_programs=[
                ExecutiveIncentiveProgramView.from_domain(p) for p in knowledge.executive_incentive_programs
            ],
            timeline=[IncentiveTimelineEventView.from_domain(e) for e in knowledge.timeline],
            ownership_alignment=[OwnershipAlignmentView.from_domain(a) for a in knowledge.ownership_alignment],
            dilution_events=[DilutionEventView.from_domain(e) for e in knowledge.dilution_events],
            incentive_structures=[IncentiveStructureView.from_domain(s) for s in knowledge.incentive_structures],
            findings=[IncentiveChangeFindingView.from_domain(f) for f in knowledge.findings],
        )


class InsiderHoldingView(CamelModel):
    disclosed_percentage: str | None
    disclosed_share_count: str | None
    source: str
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    provenance: str

    @classmethod
    def from_domain(cls, holding: InsiderHolding) -> "InsiderHoldingView":
        return cls(
            disclosed_percentage=holding.disclosed_percentage, disclosed_share_count=holding.disclosed_share_count,
            source=holding.source.value, accession_number=holding.accession_number, form_type=holding.form_type,
            filed_at=holding.filed_at, source_reference=holding.source_reference, provenance=holding.provenance,
        )


class OwnershipChangeView(CamelModel):
    executive_name: str
    trend: str
    compared_field: str | None
    previous_value: str | None
    current_value: str | None
    previous_holding: InsiderHoldingView
    current_holding: InsiderHoldingView
    provenance: str

    @classmethod
    def from_domain(cls, change: OwnershipChange) -> "OwnershipChangeView":
        return cls(
            executive_name=change.executive_name, trend=change.trend.value, compared_field=change.compared_field,
            previous_value=change.previous_value, current_value=change.current_value,
            previous_holding=InsiderHoldingView.from_domain(change.previous_holding),
            current_holding=InsiderHoldingView.from_domain(change.current_holding), provenance=change.provenance,
        )


class ExecutiveOwnershipView(CamelModel):
    executive_name: str
    holdings: list[InsiderHoldingView]
    trend: str

    @classmethod
    def from_domain(cls, ownership: ExecutiveOwnership) -> "ExecutiveOwnershipView":
        return cls(
            executive_name=ownership.executive_name, holdings=[InsiderHoldingView.from_domain(h) for h in ownership.holdings],
            trend=ownership.trend.value,
        )


class EquityCompensationExposureView(CamelModel):
    executive_name: str
    has_equity_awards: bool
    equity_incentive_kinds: list[str]
    has_cash_compensation: bool
    disclosed_components: list[str]
    program: ExecutiveIncentiveProgramView | None
    structure: IncentiveStructureView | None

    @classmethod
    def from_domain(cls, exposure: EquityCompensationExposure) -> "EquityCompensationExposureView":
        return cls(
            executive_name=exposure.executive_name, has_equity_awards=exposure.has_equity_awards,
            equity_incentive_kinds=[k.value for k in exposure.equity_incentive_kinds],
            has_cash_compensation=exposure.has_cash_compensation,
            disclosed_components=[c.value for c in exposure.disclosed_components],
            program=ExecutiveIncentiveProgramView.from_domain(exposure.program) if exposure.program is not None else None,
            structure=IncentiveStructureView.from_domain(exposure.structure) if exposure.structure is not None else None,
        )


class AlignmentObservationView(CamelModel):
    kind: str
    executive_name: str
    accession_number: str | None
    form_type: str | None
    filed_at: datetime | None
    source_reference: str | None
    disclosure_source: str | None
    provenance: str

    @classmethod
    def from_domain(cls, observation: AlignmentObservation) -> "AlignmentObservationView":
        return cls(
            kind=observation.kind.value, executive_name=observation.executive_name,
            accession_number=observation.accession_number, form_type=observation.form_type,
            filed_at=observation.filed_at, source_reference=observation.source_reference,
            disclosure_source=observation.disclosure_source, provenance=observation.provenance,
        )


class AlignmentFindingView(CamelModel):
    kind: str
    evidence_count: int

    @classmethod
    def from_domain(cls, finding: AlignmentFinding) -> "AlignmentFindingView":
        return cls(kind=finding.kind.value, evidence_count=finding.evidence_count)


class ExecutiveAlignmentProfileView(CamelModel):
    executive: ExecutiveIdentityView
    ownership: ExecutiveOwnershipView
    ownership_changes: list[OwnershipChangeView]
    equity_compensation: EquityCompensationExposureView
    observations: list[AlignmentObservationView]

    @classmethod
    def from_domain(cls, profile: ExecutiveAlignmentProfile) -> "ExecutiveAlignmentProfileView":
        return cls(
            executive=ExecutiveIdentityView.from_domain(profile.executive),
            ownership=ExecutiveOwnershipView.from_domain(profile.ownership),
            ownership_changes=[OwnershipChangeView.from_domain(c) for c in profile.ownership_changes],
            equity_compensation=EquityCompensationExposureView.from_domain(profile.equity_compensation),
            observations=[AlignmentObservationView.from_domain(o) for o in profile.observations],
        )


class InsiderAlignmentIntelligenceView(CamelModel):
    """(Capability Expansion Sprint 21) Links Ownership Intelligence and
    Executive Compensation Intelligence to Executive Identity by exact
    name -- see `insider_alignment_intelligence.py`'s own module
    docstring for why `profiles` is honestly empty in a live build today
    (no production path yet fetches real DEF 14A filing content into
    this service)."""

    profiles: list[ExecutiveAlignmentProfileView]
    findings: list[AlignmentFindingView]
    filings_considered: list[str]

    @classmethod
    def from_domain(cls, knowledge: InsiderAlignmentKnowledge) -> "InsiderAlignmentIntelligenceView":
        return cls(
            profiles=[ExecutiveAlignmentProfileView.from_domain(p) for p in knowledge.profiles],
            findings=[AlignmentFindingView.from_domain(f) for f in knowledge.findings],
            filings_considered=list(knowledge.filings_considered),
        )


# -- (Integration Sprint 1: Knowledge Activation) Governance, Risk
# Factor, Legal Proceedings, Ownership, and Executive Compensation
# Intelligence (Capability Expansion Sprints 15/16-20) had no API view
# at all before this sprint -- not merely empty, genuinely absent from
# the schema. Each is wired here for the first time, mirroring
# `IncentiveIntelligenceView`'s own precedent exactly. Every field below
# is honestly empty in a live build today -- see `InvestmentCaseComposition
# .governance_intelligence`'s own docstring in `models.py` for why. -----

class DirectorView(CamelModel):
    name: str
    is_chair: bool
    is_lead_independent_director: bool
    disclosed_independence: bool | None
    committee_assignments: list[str]
    appointment_status: str | None
    tenure_years: int | None
    table_order_index: int
    row_index: int
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str

    @classmethod
    def from_domain(cls, director: Director) -> "DirectorView":
        return cls(
            name=director.name, is_chair=director.is_chair,
            is_lead_independent_director=director.is_lead_independent_director,
            disclosed_independence=director.disclosed_independence,
            committee_assignments=[c.value for c in director.committee_assignments],
            appointment_status=director.appointment_status, tenure_years=director.tenure_years,
            table_order_index=director.table_order_index, row_index=director.row_index,
            accession_number=director.accession_number, form_type=director.form_type,
            filed_at=director.filed_at, source_reference=director.source_reference,
        )


class CommitteeView(CamelModel):
    kind: str
    disclosed_name: str
    members: list[DirectorView]
    chair: DirectorView | None
    responsibilities: list[str]
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str

    @classmethod
    def from_domain(cls, committee: Committee) -> "CommitteeView":
        return cls(
            kind=committee.kind.value, disclosed_name=committee.disclosed_name,
            members=[DirectorView.from_domain(m) for m in committee.members],
            chair=DirectorView.from_domain(committee.chair) if committee.chair is not None else None,
            responsibilities=list(committee.responsibilities), accession_number=committee.accession_number,
            form_type=committee.form_type, filed_at=committee.filed_at, source_reference=committee.source_reference,
        )


class ShareClassView(CamelModel):
    name: str
    votes_per_share: str
    table_order_index: int
    row_index: int
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str

    @classmethod
    def from_domain(cls, share_class: ShareClass) -> "ShareClassView":
        return cls(
            name=share_class.name, votes_per_share=share_class.votes_per_share,
            table_order_index=share_class.table_order_index, row_index=share_class.row_index,
            accession_number=share_class.accession_number, form_type=share_class.form_type,
            filed_at=share_class.filed_at, source_reference=share_class.source_reference,
        )


class VotingStructureView(CamelModel):
    dual_class_disclosed: bool
    controlled_company_disclosed: bool
    share_classes: list[ShareClassView]

    @classmethod
    def from_domain(cls, structure: VotingStructure) -> "VotingStructureView":
        return cls(
            dual_class_disclosed=structure.dual_class_disclosed,
            controlled_company_disclosed=structure.controlled_company_disclosed,
            share_classes=[ShareClassView.from_domain(s) for s in structure.share_classes],
        )


class GovernancePolicyView(CamelModel):
    kind: str
    description: str
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str

    @classmethod
    def from_domain(cls, policy: GovernancePolicy) -> "GovernancePolicyView":
        return cls(
            kind=policy.kind, description=policy.description, accession_number=policy.accession_number,
            form_type=policy.form_type, filed_at=policy.filed_at, source_reference=policy.source_reference,
        )


class GovernanceFindingView(CamelModel):
    kind: str
    excerpt: str | None
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    section_kind: str | None
    section_item_number: str | None
    subsection_heading: str | None
    paragraph_order_index: int | None
    table_order_index: int | None

    @classmethod
    def from_domain(cls, finding: GovernanceFinding) -> "GovernanceFindingView":
        return cls(
            kind=finding.kind.value, excerpt=finding.excerpt, accession_number=finding.accession_number,
            form_type=finding.form_type, filed_at=finding.filed_at, source_reference=finding.source_reference,
            section_kind=finding.section_kind.value if finding.section_kind is not None else None,
            section_item_number=finding.section_item_number, subsection_heading=finding.subsection_heading,
            paragraph_order_index=finding.paragraph_order_index, table_order_index=finding.table_order_index,
        )


class GovernanceChangeView(CamelModel):
    kind: str
    excerpt: str
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    section_item_number: str | None
    paragraph_order_index: int

    @classmethod
    def from_domain(cls, change: GovernanceChange) -> "GovernanceChangeView":
        return cls(
            kind=change.kind.value, excerpt=change.excerpt, accession_number=change.accession_number,
            form_type=change.form_type, filed_at=change.filed_at, source_reference=change.source_reference,
            section_item_number=change.section_item_number, paragraph_order_index=change.paragraph_order_index,
        )


class GovernanceObservationView(CamelModel):
    kind: str
    committee_kind: str | None
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    added_names: list[str]
    removed_names: list[str]

    @classmethod
    def from_domain(cls, observation: GovernanceObservation) -> "GovernanceObservationView":
        return cls(
            kind=observation.kind.value,
            committee_kind=observation.committee_kind.value if observation.committee_kind is not None else None,
            accession_number=observation.accession_number, form_type=observation.form_type,
            filed_at=observation.filed_at, source_reference=observation.source_reference,
            added_names=list(observation.added_names), removed_names=list(observation.removed_names),
        )


class BoardCompositionView(CamelModel):
    chair_disclosed: bool
    lead_independent_director_disclosed: bool
    directors: list[DirectorView]
    findings: list[GovernanceFindingView]

    @classmethod
    def from_domain(cls, composition: BoardComposition) -> "BoardCompositionView":
        return cls(
            chair_disclosed=composition.chair_disclosed,
            lead_independent_director_disclosed=composition.lead_independent_director_disclosed,
            directors=[DirectorView.from_domain(d) for d in composition.directors],
            findings=[GovernanceFindingView.from_domain(f) for f in composition.findings],
        )


class GovernanceIntelligenceView(CamelModel):
    board_composition: BoardCompositionView
    committees: list[CommitteeView]
    voting_structure: VotingStructureView
    policies: list[GovernancePolicyView]
    changes: list[GovernanceChangeView]
    observations: list[GovernanceObservationView]
    findings: list[GovernanceFindingView]
    filings_considered: list[str]

    @classmethod
    def from_domain(cls, knowledge: GovernanceKnowledge) -> "GovernanceIntelligenceView":
        return cls(
            board_composition=BoardCompositionView.from_domain(knowledge.board_composition),
            committees=[CommitteeView.from_domain(c) for c in knowledge.committees],
            voting_structure=VotingStructureView.from_domain(knowledge.voting_structure),
            policies=[GovernancePolicyView.from_domain(p) for p in knowledge.policies],
            changes=[GovernanceChangeView.from_domain(c) for c in knowledge.changes],
            observations=[GovernanceObservationView.from_domain(o) for o in knowledge.observations],
            findings=[GovernanceFindingView.from_domain(f) for f in knowledge.findings],
            filings_considered=list(knowledge.filings_considered),
        )


class RiskDisclosureView(CamelModel):
    categories: list[str]
    text: str
    source: str
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    section_kind: str | None
    section_item_number: str | None
    subsection_heading: str | None
    paragraph_order_index: int
    table_order_index: int | None

    @classmethod
    def from_domain(cls, disclosure: RiskDisclosure) -> "RiskDisclosureView":
        return cls(
            categories=[c.value for c in disclosure.categories], text=disclosure.text,
            source=disclosure.source.value, accession_number=disclosure.accession_number,
            form_type=disclosure.form_type, filed_at=disclosure.filed_at,
            source_reference=disclosure.source_reference,
            section_kind=disclosure.section_kind.value if disclosure.section_kind is not None else None,
            section_item_number=disclosure.section_item_number, subsection_heading=disclosure.subsection_heading,
            paragraph_order_index=disclosure.paragraph_order_index, table_order_index=disclosure.table_order_index,
        )


class RiskCategorySummaryView(CamelModel):
    kind: str
    disclosures: list[RiskDisclosureView]

    @classmethod
    def from_domain(cls, summary: RiskCategorySummary) -> "RiskCategorySummaryView":
        return cls(kind=summary.kind.value, disclosures=[RiskDisclosureView.from_domain(d) for d in summary.disclosures])


class RiskChangeObservationView(CamelModel):
    kind: str
    category: str
    previous_excerpts: list[str]
    current_excerpts: list[str]
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str

    @classmethod
    def from_domain(cls, change: RiskChangeObservation) -> "RiskChangeObservationView":
        return cls(
            kind=change.kind.value, category=change.category.value,
            previous_excerpts=list(change.previous_excerpts), current_excerpts=list(change.current_excerpts),
            accession_number=change.accession_number, form_type=change.form_type, filed_at=change.filed_at,
            source_reference=change.source_reference,
        )


class RiskFactorIntelligenceView(CamelModel):
    categories: list[RiskCategorySummaryView]
    changes: list[RiskChangeObservationView]
    disclosures: list[RiskDisclosureView]
    filings_considered: list[str]

    @classmethod
    def from_domain(cls, knowledge: RiskFactorKnowledge) -> "RiskFactorIntelligenceView":
        return cls(
            categories=[RiskCategorySummaryView.from_domain(c) for c in knowledge.categories],
            changes=[RiskChangeObservationView.from_domain(c) for c in knowledge.changes],
            disclosures=[RiskDisclosureView.from_domain(d) for d in knowledge.disclosures],
            filings_considered=list(knowledge.filings_considered),
        )


class LegalProceedingDisclosureView(CamelModel):
    categories: list[str]
    text: str
    source: str
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    section_kind: str | None
    section_item_number: str | None
    subsection_heading: str | None
    paragraph_order_index: int
    table_order_index: int | None

    @classmethod
    def from_domain(cls, disclosure: LegalProceedingDisclosure) -> "LegalProceedingDisclosureView":
        return cls(
            categories=[c.value for c in disclosure.categories], text=disclosure.text,
            source=disclosure.source.value, accession_number=disclosure.accession_number,
            form_type=disclosure.form_type, filed_at=disclosure.filed_at,
            source_reference=disclosure.source_reference,
            section_kind=disclosure.section_kind.value if disclosure.section_kind is not None else None,
            section_item_number=disclosure.section_item_number, subsection_heading=disclosure.subsection_heading,
            paragraph_order_index=disclosure.paragraph_order_index, table_order_index=disclosure.table_order_index,
        )


class ProceedingCategorySummaryView(CamelModel):
    kind: str
    disclosures: list[LegalProceedingDisclosureView]

    @classmethod
    def from_domain(cls, summary: ProceedingCategorySummary) -> "ProceedingCategorySummaryView":
        return cls(
            kind=summary.kind.value, disclosures=[LegalProceedingDisclosureView.from_domain(d) for d in summary.disclosures]
        )


class LegalChangeObservationView(CamelModel):
    kind: str
    category: str
    previous_excerpts: list[str]
    current_excerpts: list[str]
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str

    @classmethod
    def from_domain(cls, change: LegalChangeObservation) -> "LegalChangeObservationView":
        return cls(
            kind=change.kind.value, category=change.category.value,
            previous_excerpts=list(change.previous_excerpts), current_excerpts=list(change.current_excerpts),
            accession_number=change.accession_number, form_type=change.form_type, filed_at=change.filed_at,
            source_reference=change.source_reference,
        )


class LegalProceedingsIntelligenceView(CamelModel):
    categories: list[ProceedingCategorySummaryView]
    changes: list[LegalChangeObservationView]
    disclosures: list[LegalProceedingDisclosureView]
    filings_considered: list[str]

    @classmethod
    def from_domain(cls, knowledge: LegalProceedingsKnowledge) -> "LegalProceedingsIntelligenceView":
        return cls(
            categories=[ProceedingCategorySummaryView.from_domain(c) for c in knowledge.categories],
            changes=[LegalChangeObservationView.from_domain(c) for c in knowledge.changes],
            disclosures=[LegalProceedingDisclosureView.from_domain(d) for d in knowledge.disclosures],
            filings_considered=list(knowledge.filings_considered),
        )


class OwnershipDisclosureView(CamelModel):
    owner_name: str | None
    categories: list[str]
    disclosed_percentage: str | None
    disclosed_share_count: str | None
    text: str
    source: str
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    section_kind: str | None
    section_item_number: str | None
    subsection_heading: str | None
    paragraph_order_index: int | None
    table_order_index: int | None
    row_index: int | None

    @classmethod
    def from_domain(cls, disclosure: OwnershipDisclosure) -> "OwnershipDisclosureView":
        return cls(
            owner_name=disclosure.owner_name, categories=[c.value for c in disclosure.categories],
            disclosed_percentage=disclosure.disclosed_percentage, disclosed_share_count=disclosure.disclosed_share_count,
            text=disclosure.text, source=disclosure.source.value, accession_number=disclosure.accession_number,
            form_type=disclosure.form_type, filed_at=disclosure.filed_at, source_reference=disclosure.source_reference,
            section_kind=disclosure.section_kind.value if disclosure.section_kind is not None else None,
            section_item_number=disclosure.section_item_number, subsection_heading=disclosure.subsection_heading,
            paragraph_order_index=disclosure.paragraph_order_index, table_order_index=disclosure.table_order_index,
            row_index=disclosure.row_index,
        )


class OwnerCategorySummaryView(CamelModel):
    kind: str
    disclosures: list[OwnershipDisclosureView]

    @classmethod
    def from_domain(cls, summary: OwnerCategorySummary) -> "OwnerCategorySummaryView":
        return cls(kind=summary.kind.value, disclosures=[OwnershipDisclosureView.from_domain(d) for d in summary.disclosures])


class OwnershipChangeObservationView(CamelModel):
    kind: str
    owner_name: str
    previous_excerpts: list[str]
    current_excerpts: list[str]
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str

    @classmethod
    def from_domain(cls, change: OwnershipChangeObservation) -> "OwnershipChangeObservationView":
        return cls(
            kind=change.kind.value, owner_name=change.owner_name, previous_excerpts=list(change.previous_excerpts),
            current_excerpts=list(change.current_excerpts), accession_number=change.accession_number,
            form_type=change.form_type, filed_at=change.filed_at, source_reference=change.source_reference,
        )


class OwnershipIntelligenceView(CamelModel):
    categories: list[OwnerCategorySummaryView]
    changes: list[OwnershipChangeObservationView]
    disclosures: list[OwnershipDisclosureView]
    filings_considered: list[str]

    @classmethod
    def from_domain(cls, knowledge: OwnershipKnowledge) -> "OwnershipIntelligenceView":
        return cls(
            categories=[OwnerCategorySummaryView.from_domain(c) for c in knowledge.categories],
            changes=[OwnershipChangeObservationView.from_domain(c) for c in knowledge.changes],
            disclosures=[OwnershipDisclosureView.from_domain(d) for d in knowledge.disclosures],
            filings_considered=list(knowledge.filings_considered),
        )


class ExecutiveCompensationRecordView(CamelModel):
    executive_name: str
    disclosed_role: str | None
    reporting_year: str | None
    salary: str | None
    bonus: str | None
    stock_awards: str | None
    option_awards: str | None
    non_equity_incentive: str | None
    pension_change: str | None
    other_compensation: str | None
    total: str | None
    currency: str | None
    source: str
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    section_kind: str | None
    section_item_number: str | None
    subsection_heading: str | None
    table_order_index: int
    row_index: int
    linked_executive_identity_name: str | None

    @classmethod
    def from_domain(cls, record: ExecutiveCompensationRecord) -> "ExecutiveCompensationRecordView":
        return cls(
            executive_name=record.executive_name, disclosed_role=record.disclosed_role,
            reporting_year=record.reporting_year, salary=record.salary, bonus=record.bonus,
            stock_awards=record.stock_awards, option_awards=record.option_awards,
            non_equity_incentive=record.non_equity_incentive, pension_change=record.pension_change,
            other_compensation=record.other_compensation, total=record.total, currency=record.currency,
            source=record.source.value, accession_number=record.accession_number, form_type=record.form_type,
            filed_at=record.filed_at, source_reference=record.source_reference,
            section_kind=record.section_kind.value if record.section_kind is not None else None,
            section_item_number=record.section_item_number, subsection_heading=record.subsection_heading,
            table_order_index=record.table_order_index, row_index=record.row_index,
            linked_executive_identity_name=record.linked_executive_identity_name,
        )


class EquityAwardDisclosureView(CamelModel):
    executive_name: str
    disclosed_award_type: str | None
    kind: str | None
    grant_value: str | None
    unit_count: str | None
    vesting_disclosure: str | None
    performance_conditions: str | None
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    table_order_index: int
    row_index: int

    @classmethod
    def from_domain(cls, award: EquityAwardDisclosure) -> "EquityAwardDisclosureView":
        return cls(
            executive_name=award.executive_name, disclosed_award_type=award.disclosed_award_type,
            kind=award.kind.value if award.kind is not None else None, grant_value=award.grant_value,
            unit_count=award.unit_count, vesting_disclosure=award.vesting_disclosure,
            performance_conditions=award.performance_conditions, accession_number=award.accession_number,
            form_type=award.form_type, filed_at=award.filed_at, source_reference=award.source_reference,
            table_order_index=award.table_order_index, row_index=award.row_index,
        )


class PerformanceMetricDisclosureView(CamelModel):
    executive_name: str | None
    metric_kind: str
    metric_label: str | None
    target: str | None
    range_disclosure: str | None
    performance_period: str | None
    weighting: str | None
    outcome: str | None
    text: str
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str
    paragraph_order_index: int | None
    table_order_index: int | None
    row_index: int | None

    @classmethod
    def from_domain(cls, metric: PerformanceMetricDisclosure) -> "PerformanceMetricDisclosureView":
        return cls(
            executive_name=metric.executive_name, metric_kind=metric.metric_kind.value,
            metric_label=metric.metric_label, target=metric.target, range_disclosure=metric.range_disclosure,
            performance_period=metric.performance_period, weighting=metric.weighting, outcome=metric.outcome,
            text=metric.text, accession_number=metric.accession_number, form_type=metric.form_type,
            filed_at=metric.filed_at, source_reference=metric.source_reference,
            paragraph_order_index=metric.paragraph_order_index, table_order_index=metric.table_order_index,
            row_index=metric.row_index,
        )


class CompensationChangeObservationView(CamelModel):
    kind: str
    executive_name: str
    component: str | None
    previous_value: str | None
    current_value: str | None
    accession_number: str
    form_type: str
    filed_at: datetime
    source_reference: str

    @classmethod
    def from_domain(cls, change: CompensationChangeObservation) -> "CompensationChangeObservationView":
        return cls(
            kind=change.kind.value, executive_name=change.executive_name,
            component=change.component.value if change.component is not None else None,
            previous_value=change.previous_value, current_value=change.current_value,
            accession_number=change.accession_number, form_type=change.form_type, filed_at=change.filed_at,
            source_reference=change.source_reference,
        )


class ExecutiveCompensationIntelligenceView(CamelModel):
    records: list[ExecutiveCompensationRecordView]
    equity_awards: list[EquityAwardDisclosureView]
    performance_metrics: list[PerformanceMetricDisclosureView]
    changes: list[CompensationChangeObservationView]
    filings_considered: list[str]

    @classmethod
    def from_domain(cls, knowledge: ExecutiveCompensationKnowledge) -> "ExecutiveCompensationIntelligenceView":
        return cls(
            records=[ExecutiveCompensationRecordView.from_domain(r) for r in knowledge.records],
            equity_awards=[EquityAwardDisclosureView.from_domain(a) for a in knowledge.equity_awards],
            performance_metrics=[PerformanceMetricDisclosureView.from_domain(m) for m in knowledge.performance_metrics],
            changes=[CompensationChangeObservationView.from_domain(c) for c in knowledge.changes],
            filings_considered=list(knowledge.filings_considered),
        )


class FinancialPeriodView(CamelModel):
    period_start: date | None
    period_end: date | None
    revenue: float | None
    operating_income: float | None
    net_income: float | None
    eps: float | None
    free_cash_flow: float | None
    capital_expenditure: float | None
    share_buybacks: float | None
    share_issuance: float | None
    dividends: float | None
    cash: float | None
    total_debt: float | None
    shares_outstanding: float | None
    currency: str | None

    @classmethod
    def from_domain(cls, period: FinancialPeriod) -> "FinancialPeriodView":
        return cls(
            period_start=period.period_start,
            period_end=period.period_end,
            revenue=period.revenue,
            operating_income=period.operating_income,
            net_income=period.net_income,
            eps=period.eps,
            free_cash_flow=period.free_cash_flow,
            capital_expenditure=period.capital_expenditure,
            share_buybacks=period.share_buybacks,
            share_issuance=period.share_issuance,
            dividends=period.dividends,
            cash=period.cash,
            total_debt=period.total_debt,
            shares_outstanding=period.shares_outstanding,
            currency=period.currency,
        )


class MarketSnapshotView(CamelModel):
    as_of: datetime
    share_price: float | None
    shares_outstanding: float | None
    currency: str | None
    market_cap: float | None
    #: Internal Alpha Stabilization 1 (MSFT price root cause fix): the
    #: real trading day the price is from -- what "Uppdaterad {{date}}"
    #: shows, never `as_of` (when Atlas happened to fetch it).
    trading_day: date | None
    #: `"fresh" | "stale" | "refreshing" | "failed" | "unavailable"`.
    #: Always overwritten by the router after `from_domain` (which has
    #: no access to the in-process refresh coordinator) -- `"unavailable"`
    #: here is only ever a placeholder, never the real served value.
    price_freshness: str = "unavailable"

    @classmethod
    def from_domain(cls, snapshot: MarketSnapshot) -> "MarketSnapshotView":
        return cls(
            as_of=snapshot.as_of,
            share_price=snapshot.share_price,
            shares_outstanding=snapshot.shares_outstanding,
            currency=snapshot.currency,
            market_cap=snapshot.market_cap,
            trading_day=snapshot.trading_day,
        )


class PriceRefreshResponseView(CamelModel):
    """Internal Alpha Stabilization 1 (MSFT price root cause fix) --
    the manual "Uppdatera" action's own response, reporting exactly
    what `price_refresh.refresh_price_only` (the identical function
    the lazy background trigger also calls) actually did."""

    attempted: bool
    succeeded: bool
    reason: str
    price_freshness: str


class TradeLogEntryView(CamelModel):
    outcome_id: str
    decision_id: str
    transaction_type: str
    quantity: float
    execution_price: float
    executed_at: datetime

    @classmethod
    def from_domain(cls, entry: AlphaTradeLogEntry) -> "TradeLogEntryView":
        return cls(
            outcome_id=entry.outcome_id,
            decision_id=entry.decision_id,
            transaction_type=entry.transaction_type.value,
            quantity=entry.quantity,
            execution_price=entry.execution_price,
            executed_at=entry.executed_at,
        )


class CaseHighlightView(CamelModel):
    """One Strength or Risk -- see `atlas.analysis_engine
    .investment_case_synthesis.CaseHighlight`'s own docstring for the
    exact, documented condition each `kind` was constructed under."""

    kind: str
    supporting_finding_id: str
    evidence_references: list[str]

    @classmethod
    def from_domain(cls, highlight: CaseHighlight) -> "CaseHighlightView":
        return cls(
            kind=highlight.kind.value,
            supporting_finding_id=highlight.supporting_finding_id,
            evidence_references=list(highlight.evidence_references),
        )


class RecentRevenueTrendView(CamelModel):
    trend: str
    periods_considered: list[str]
    evidence_references: list[str]

    @classmethod
    def from_domain(cls, trend: RecentRevenueTrend) -> "RecentRevenueTrendView":
        return cls(
            trend=trend.trend.value,
            periods_considered=list(trend.periods_considered),
            evidence_references=list(trend.evidence_references),
        )


class GrowthAnalysisView(CamelModel):
    status: str
    recent_trend: RecentRevenueTrendView | None
    evidence_references: list[str]

    @classmethod
    def from_domain(cls, growth: GrowthAnalysis) -> "GrowthAnalysisView":
        return cls(
            status=growth.status.value,
            recent_trend=RecentRevenueTrendView.from_domain(growth.recent_trend) if growth.recent_trend else None,
            evidence_references=list(growth.evidence_references),
        )


class ValuationContextView(CamelModel):
    fcf_yield_status: str
    current_yield: float | None
    scenario_available: bool
    evidence_references: list[str]

    @classmethod
    def from_domain(cls, context: ValuationContext) -> "ValuationContextView":
        return cls(
            fcf_yield_status=context.fcf_yield_status.value,
            current_yield=context.current_yield,
            scenario_available=context.scenario_available,
            evidence_references=list(context.evidence_references),
        )


class CaseOpenQuestionView(CamelModel):
    origin: str
    reference: str | None

    @classmethod
    def from_domain(cls, question: CaseOpenQuestion) -> "CaseOpenQuestionView":
        return cls(origin=question.origin.value, reference=question.reference)


class AtlasThesisView(CamelModel):
    """Atlas-generated, provisional -- distinct from
    `CurrentThesisView`, the investor's own most recent words. See
    `atlas.analysis_engine.investment_case_synthesis.AtlasThesis`'s own
    docstring."""

    posture: str
    narrative: str
    supporting_highlight_ids: list[str]
    key_uncertainty_origins: list[str]

    @classmethod
    def from_domain(cls, thesis: AtlasThesis) -> "AtlasThesisView":
        return cls(
            posture=thesis.posture.value,
            narrative=thesis.narrative,
            supporting_highlight_ids=list(thesis.supporting_highlight_ids),
            key_uncertainty_origins=[origin.value for origin in thesis.key_uncertainty_origins],
        )


class ChangeFindingView(CamelModel):
    """One meaningful, traceable change between two analytical states --
    see `atlas.analysis_engine.investment_case_change.ChangeFinding`'s
    own docstring for the exact, documented condition each `category`
    was constructed under."""

    id: str
    category: str
    direction: str
    previous_state: str
    current_state: str
    details: dict[str, str]
    evidence_references: list[str]
    source_finding_id: str | None

    @classmethod
    def from_domain(cls, change: ChangeFinding) -> "ChangeFindingView":
        return cls(
            id=change.id,
            category=change.category.value,
            direction=change.direction.value,
            previous_state=change.previous_state,
            current_state=change.current_state,
            details=dict(change.details),
            evidence_references=list(change.evidence_references),
            source_finding_id=change.source_finding_id,
        )


class OutlookAssumptionView(CamelModel):
    """See `atlas.analysis_engine.outlook.OutlookAssumption`'s own
    docstring: fully structured, fully numeric, never a free-text
    "why" -- a caller renders language from `kind` plus these real
    values, never from a string this API wrote. `observationCount`
    (Semantic Hardening Pass) must be shown alongside `targetFcfYield`
    wherever this assumption renders -- see that field's own domain
    docstring for why. `growthRate`/`horizonYears`/
    `growthObservationCount` (Long-Term Expected Return v1) are `null`
    for every Short-Term assumption and always populated together for
    Long-Term -- a frontend renders a growth-assumption line only when
    `growthRate` is non-null, never inferring its presence from `kind`
    alone."""

    kind: str
    current_fcf_yield: float
    target_fcf_yield: float
    observation_count: int
    growth_rate: float | None
    horizon_years: int | None
    growth_observation_count: int | None

    @classmethod
    def from_domain(cls, assumption: OutlookAssumption) -> "OutlookAssumptionView":
        return cls(
            kind=assumption.kind.value,
            current_fcf_yield=assumption.current_fcf_yield,
            target_fcf_yield=assumption.target_fcf_yield,
            observation_count=assumption.observation_count,
            growth_rate=assumption.growth_rate,
            horizon_years=assumption.horizon_years,
            growth_observation_count=assumption.growth_observation_count,
        )


class ExpectedReturnRangeView(CamelModel):
    """Part 4's own explicit requirement, wire-visible: `basis` and both
    horizon bounds are always present alongside the range -- a frontend
    never has to infer units or horizon."""

    low_percent: float
    high_percent: float
    basis: str
    horizon_months_low: int
    horizon_months_high: int
    assumption: OutlookAssumptionView

    @classmethod
    def from_domain(cls, expected_return: ExpectedReturnRange) -> "ExpectedReturnRangeView":
        return cls(
            low_percent=expected_return.low_percent,
            high_percent=expected_return.high_percent,
            basis=expected_return.basis.value,
            horizon_months_low=expected_return.horizon_months_low,
            horizon_months_high=expected_return.horizon_months_high,
            assumption=OutlookAssumptionView.from_domain(expected_return.assumption),
        )


class OutlookScenarioView(CamelModel):
    kind: str
    return_percent: float
    assumption: OutlookAssumptionView
    driver: str

    @classmethod
    def from_domain(cls, scenario: OutlookScenario) -> "OutlookScenarioView":
        return cls(
            kind=scenario.kind.value,
            return_percent=scenario.return_percent,
            assumption=OutlookAssumptionView.from_domain(scenario.assumption),
            driver=scenario.driver.value,
        )


class OutlookDriverView(CamelModel):
    kind: str
    direction: str
    source_finding_id: str | None

    @classmethod
    def from_domain(cls, driver: OutlookDriver) -> "OutlookDriverView":
        return cls(kind=driver.kind.value, direction=driver.direction.value, source_finding_id=driver.source_finding_id)


class HorizonOutlookView(CamelModel):
    """One horizon's Outlook -- `expectedReturn`/`expectedReturnGap` and
    `scenarios`/`scenariosGap` are each mutually exclusive pairs (see
    `HorizonOutlook.__post_init__`): a frontend checks the gap field to
    render an honest "not yet computed" state, never infers absence from
    an empty/null value alone."""

    horizon: str
    expected_return: ExpectedReturnRangeView | None
    expected_return_gap: str | None
    scenarios: list[OutlookScenarioView]
    scenarios_gap: str | None
    conviction: str
    momentum: str
    key_drivers: list[OutlookDriverView]

    @classmethod
    def from_domain(cls, horizon: HorizonOutlook, *, momentum: str) -> "HorizonOutlookView":
        return cls(
            horizon=horizon.horizon.value,
            expected_return=(
                ExpectedReturnRangeView.from_domain(horizon.expected_return)
                if horizon.expected_return is not None
                else None
            ),
            expected_return_gap=horizon.expected_return_gap.value if horizon.expected_return_gap else None,
            scenarios=[OutlookScenarioView.from_domain(s) for s in horizon.scenarios],
            scenarios_gap=horizon.scenarios_gap.value if horizon.scenarios_gap else None,
            conviction=horizon.conviction.value,
            momentum=momentum,
            key_drivers=[OutlookDriverView.from_domain(d) for d in horizon.key_drivers],
        )


class OutlookView(CamelModel):
    """Outlook Intelligence Sprint 1: real Short-Term/Long-Term Outlook,
    replacing the Investment Case Outlook panel's former "Not yet
    computed" placeholders wherever real data now supports them. See
    `atlas.analysis_engine.outlook`'s own module docstring for the full
    derivation rules, and this class's own `from_domain` for why
    `momentum` is computed here rather than on the domain object."""

    short_term: HorizonOutlookView
    long_term: HorizonOutlookView

    @classmethod
    def from_domain(
        cls, outlook: Outlook, *, change_intelligence: "ChangeIntelligence | None"
    ) -> "OutlookView":
        #: `outlook.py` itself cannot know whether this run's analytical
        #: state is strengthening/weakening/stable -- that needs a
        #: comparison against a previous snapshot, which only exists
        #: once `ChangeIntelligence` has been computed one layer up (see
        #: that module's own docstring). Computed once, shared by both
        #: horizons -- Momentum has no horizon-specific split in this
        #: sprint, the same honest limitation `AtlasOutlookSection`
        #: already documents for "What Changed."
        thesis_impact = change_intelligence.thesis_impact if change_intelligence is not None else None
        is_baseline = change_intelligence.is_baseline if change_intelligence is not None else True
        momentum = derive_outlook_momentum(thesis_impact, is_baseline=is_baseline).value
        return cls(
            short_term=HorizonOutlookView.from_domain(outlook.short_term, momentum=momentum),
            long_term=HorizonOutlookView.from_domain(outlook.long_term, momentum=momentum),
        )


class StanceReasonView(CamelModel):
    """Atlas Intelligence Sprint 2 (Recommendation Quality &
    Actionability). Independently declared here, field-for-field
    identical to `atlas.alpha.stance.api.schemas.StanceReasonView` --
    this codebase's own no-cross-package-View-import convention
    (matching `CoverageAssessmentView`'s own precedent from Sprint 1).
    `investment_case` itself has no dependency on `atlas.alpha.stance`
    at all -- only this router's own composition root does; see
    `api/router.py`'s own docstring."""

    code: str


class StanceView(CamelModel):
    level: str
    reasoning: list[StanceReasonView]
    supporting_signals: list[StanceReasonView]
    limiting_signals: list[StanceReasonView]
    confidence: str
    missing_information: list[str]


class ExplanationView(CamelModel):
    """Atlas Intelligence Sprint 3 (Decision Explainability & Evidence
    Trace). Independently declared here, field-for-field identical to
    `atlas.alpha.explainability.api.schemas.ExplanationView` -- the same
    no-cross-package-View-import convention `StanceReasonView`/
    `StanceView` above already establish. Reuses this module's own
    `DimensionCoverageView`/`ConfidenceReasonView` (Sprint 1) and
    `StanceReasonView` (Sprint 2) rather than redeclaring them a second
    time within this same file -- those two are shared, lower-level
    presentation types already declared once above."""

    supporting_evidence: list[StanceReasonView]
    contradicting_evidence: list[StanceReasonView]
    limiting_factors: list[StanceReasonView]
    missing_evidence: list[DimensionCoverageView]
    confidence_drivers: list[ConfidenceReasonView]
    most_valuable_missing_information: DimensionCoverageView | None

    # No `from_domain` here, deliberately -- mirrors `StanceView`'s own
    # precedent immediately above: this schema module has no dependency
    # on `atlas.alpha.explainability` at all, so the conversion lives in
    # `api/router.py`'s own composition root (`_explanation_view()`),
    # never here.


class EvidenceConflictView(CamelModel):
    """Atlas Intelligence Sprint 4 (Evidence Quality & Conflict
    Resolution). Independently declared here, field-for-field identical
    to `atlas.alpha.evidence_quality.api.schemas.EvidenceConflictView`
    -- the same no-cross-package-View-import convention `StanceView`/
    `ExplanationView` above already establish."""

    fact_kind: str
    period: str
    unit: str
    values: list[float]
    source_record_ids: list[str]


class FactQualityView(CamelModel):
    fact_kind: str
    freshness: str
    dominance: str
    latest_period: str | None
    latest_published_at: datetime | None
    source_record_count: int


class UnsupportedFindingView(CamelModel):
    category: str
    status: str


class EvidenceQualityReportView(CamelModel):
    quality: str
    conflict_status: str
    freshness: str
    dominance: str
    warnings: list[str]
    facts: list[FactQualityView]
    conflicts: list[EvidenceConflictView]
    unsupported_findings: list[UnsupportedFindingView]

    # No `from_domain` here either -- see `ExplanationView`'s own note
    # immediately above; the conversion lives in `api/router.py`'s own
    # composition root (`_evidence_quality_view()`).


class EvidenceTransitionView(CamelModel):
    """Atlas Intelligence Sprint 5 (Evidence Timeline & Historical
    Understanding). Independently declared here, field-for-field
    identical to `atlas.alpha.evidence_timeline.api.schemas
    .EvidenceTransitionView`."""

    id: str
    category: str
    direction: str
    previous_state: str
    current_state: str
    is_material: bool
    """Deliverable 7 -- the real, already-computed output of
    `atlas.alpha.evidence_timeline.is_material_transition()`, a fixed
    declared filter (never a second priority engine). The frontend
    reads this to decide prominence; it never reimplements the
    classification itself."""


class SourceEvidenceEventView(CamelModel):
    """A real `(fact_kind, period)` combination new since the last
    capture -- **Source Evidence History** (a fact about the world),
    deliberately never merged into `transitions` (**Atlas Analysis
    History** -- Atlas's own conclusions changing). See
    `atlas.alpha.evidence_timeline.models`'s own module docstring for
    why this distinction is structural, not just documented."""

    fact_kind: str
    period: str


class EvidenceTimelineView(CamelModel):
    """The most recent `EvidenceHistory` transition for this Case --
    Deliverable 5/8's own "recent evidence changes" (never the full,
    potentially-long timeline; that lives at `GET /evidence-timeline
    /case/{case_id}`, one click away -- progressive disclosure, not a
    second History page). `is_baseline=True` and empty `transitions`/
    `newSourceEvidence` lists are all real, honest states: a Case with
    no prior snapshot to compare against, or one whose evidence
    genuinely has not changed since the last capture."""

    is_baseline: bool
    transitions: list[EvidenceTransitionView]
    new_source_evidence: list[SourceEvidenceEventView]
    previous_captured_at: datetime | None
    current_captured_at: datetime

    # No `from_domain` here either -- same reason as `ExplanationView`/
    # `EvidenceQualityReportView` above.


class MaterialEvidenceView(CamelModel):
    """Atlas Intelligence Sprint -- Materiality & Priority Engine.
    Independently declared here, field-for-field identical to
    `atlas.alpha.materiality.api.schemas.MaterialEvidenceView`."""

    reason: StanceReasonView
    materiality: str


class MaterialityAssessmentView(CamelModel):
    """Deliverable 5 -- the four "top" picks Investment Case leads with,
    plus each bucket's full, materiality-ordered membership (most
    material first) so the page can collapse everything below the top
    pick behind progressive disclosure without a second sort."""

    supporting_evidence: list[MaterialEvidenceView]
    contradicting_evidence: list[MaterialEvidenceView]
    limiting_factors: list[MaterialEvidenceView]
    top_supporting_evidence: MaterialEvidenceView | None
    top_contradicting_evidence: MaterialEvidenceView | None
    top_limiting_factor: MaterialEvidenceView | None
    top_missing_evidence: DimensionCoverageView | None

    # No `from_domain` here either -- same reason as `ExplanationView`
    # above.


class MonitoringStatusView(CamelModel):
    """Sprint 7, Deliverable 13 -- the compact view. Field-identical to
    the relevant slice of `atlas.alpha.monitoring.api.schemas
    .MonitoringResultView`, locally redeclared per this file's own
    "no cross-package View import" convention, and deliberately
    narrower: `latest_change_reason` is the single most material
    change's own reason text (highest-importance category first, ties
    broken by `MonitoringChange.id` for determinism), never the full
    `changes` list."""

    status: str
    material_change_count: int
    latest_change_reason: str | None
    generated_at: datetime | None


class CaseOperationalFreshnessView(CamelModel):
    """Sprint 8/9, Deliverable 15/6/7 -- field-identical to `atlas.alpha
    .monitoring.api.schemas.CaseOperationalFreshnessView`, locally
    redeclared per this file's own "no cross-package View import"
    convention."""

    is_pending: bool
    last_monitored_at: datetime | None
    last_run_failed_for_case: bool
    data_freshness_status: str


class InvestmentCaseAnalysisView(CamelModel):
    """The canonical Investment Case -- one coherent object mirroring
    `InvestmentCaseComposition` plus its `CanonicalAnalysis`. Every
    section is either directly reused or a structural narrowing; no
    section here is computed, joined, or reinterpreted beyond unwrapping
    value objects and enums."""

    case_id: str
    holding_context: HoldingContextView
    current_thesis: CurrentThesisView
    is_thesis_stale: bool
    confidence: str
    conviction: ConvictionAssessmentView
    coverage: CoverageAssessmentView
    """Atlas Intelligence Sprint 1 (Data Coverage & Confidence Engine):
    per-dimension coverage plus a qualitative overall confidence -- see
    `atlas.alpha.coverage`'s own module docstring. A new, additive,
    Alpha-only presentation layer over `business_analysis`/`valuation`/
    `risk` above; none of those fields' own meaning changes."""
    business_analysis: BusinessAnalysisView
    valuation: ValuationEngineView
    valuation_support: ValuationSupportView
    """Alpha Freeze correction sprint, resolving Principal Engineer Review
    2.0 finding M-2 -- see `ValuationSupportView`'s own docstring. Additive
    field; `valuation` above is unchanged and keeps its exact prior
    meaning (`ValuationStatus`, relative-to-history), never conflated with
    this narrower, downside-only field (`DE-015`)."""
    risk: RiskAnalysisView
    risk_projection: RiskProjectionView
    """Figma-fidelity rebuild: Atlas View's compact "Risk Level" dot
    needs one representative category, not the full four-category
    vector `risk` above already carries in full -- see
    `RiskProjectionView`'s own docstring."""
    evidence_quality: EvidenceQualityFindingsSchema | None
    open_questions: list[OpenQuestionSchema]
    recommendation: RecommendationStateView
    decision_history: list[DecisionHistoryEntryView]
    observation_history: list[ObservationEntryView]
    outcome_history: list[OutcomeEntryView]
    trade_log: list[TradeLogEntryView]
    company_profile: CompanyProfileView | None
    financial_history: list[FinancialPeriodView]
    market_snapshot: MarketSnapshotView | None
    regulatory_filings: list[RegulatoryFilingView]
    historical_valuation: HistoricalValuationView
    earnings_call: EarningsCallView
    financial_statement_intelligence: FinancialStatementIntelligenceView
    capital_allocation_intelligence: CapitalAllocationIntelligenceView
    financial_quality_intelligence: FinancialQualityIntelligenceView
    growth_intelligence: GrowthKnowledgeView
    business_quality_intelligence: BusinessQualityIntelligenceView
    management_credibility_intelligence: ManagementCredibilityIntelligenceView
    management_guidance_intelligence: ManagementGuidanceIntelligenceView
    executive_change_intelligence: ExecutiveChangeIntelligenceView
    executive_track_record_intelligence: ExecutiveTrackRecordIntelligenceView
    incentive_intelligence: IncentiveIntelligenceView
    governance_intelligence: GovernanceIntelligenceView
    risk_factor_intelligence: RiskFactorIntelligenceView
    legal_proceedings_intelligence: LegalProceedingsIntelligenceView
    ownership_intelligence: OwnershipIntelligenceView
    executive_compensation_intelligence: ExecutiveCompensationIntelligenceView
    insider_alignment_intelligence: InsiderAlignmentIntelligenceView
    strengths: list[CaseHighlightView]
    risks: list[CaseHighlightView]
    growth_analysis: GrowthAnalysisView
    valuation_context: ValuationContextView
    atlas_thesis: AtlasThesisView
    outlook: OutlookView
    """Outlook Intelligence Sprint 1: real Short-Term/Long-Term
    Expected Return, Scenarios, Conviction, Momentum, and Key Drivers --
    see `OutlookView`'s own docstring."""
    key_open_questions: list[CaseOpenQuestionView]
    """Investment Case Engine v2 slice: distinct from `open_questions`
    above (`decision_engine`'s own case-wide gaps, unchanged) -- these
    are curated, company-analysis-specific questions from
    `atlas.analysis_engine.investment_case_synthesis`, each traceable to
    one real analytical condition."""
    change_intelligence_available: bool
    """Investment Case Monitoring & Change Intelligence v1: `False` only
    when no snapshot repository was wired for this build -- mirrors
    `InvestmentCaseComposition.change_intelligence`'s own `None` case.
    Every real API call site wires one, so this is `True` in practice;
    the flag exists so a caller (frontend or test) never has to infer
    "unavailable" from an empty `latestChanges` list, which would be
    indistinguishable from a genuine "nothing changed" baseline."""
    is_baseline_case: bool
    """`True` only for a Case's first-ever recorded analysis -- there is
    no previous structured state to compare against yet. A baseline is
    never reported as a set of changes (see `ChangeIntelligence`'s own
    docstring)."""
    latest_changes: list[ChangeFindingView]
    change_summary: str
    thesis_change: str
    previous_analysis_at: datetime | None
    current_analysis_at: datetime
    generated_at: datetime
    stance: StanceView | None
    """Atlas Intelligence Sprint 2 -- Deliverable 5. `None` only when no
    `StanceService` was wired for this build (mirrors
    `change_intelligence_available`'s own precedent); every real API
    call site wires one, via `api/router.py`'s own composition root, so
    this is populated in practice. Reuses the existing Executive
    Summary area at the presentation layer -- no new large section."""
    explanation: ExplanationView | None
    """Atlas Intelligence Sprint 3 -- Deliverable 4. `None` only when no
    `Explanation` was built for this call (mirrors `stance`'s own
    `None` precedent above); every real API call site wires one via
    `api/router.py`'s own composition root, so this is populated in
    practice."""
    evidence_quality_report: EvidenceQualityReportView | None
    """Atlas Intelligence Sprint 4 -- Deliverable 5. `None` only when no
    `EvidenceQualityReport` was built for this call, same `stance`/
    `explanation` precedent above. Named `evidence_quality_report`,
    not `evidence_quality` -- that name is already taken by the
    unrelated, older `EvidenceQualityFindingsSchema` field above
    (Product Sprint 14's own per-finding evidence-reference-resolution
    concept), a real, pre-existing naming collision this field must
    not silently shadow."""
    evidence_timeline: EvidenceTimelineView | None
    """Atlas Intelligence Sprint 5 -- Deliverable 5. `None` only when no
    `EvidenceTimelineService`/snapshot capture was wired for this call,
    same `stance`/`explanation`/`evidence_quality_report` precedent
    above."""
    monitoring: "MonitoringStatusView | None"
    """Atlas Intelligence Sprint 7 (Monitoring & Change Detection,
    Deliverable 13). `None` only when Monitoring has never run for this
    Case yet (an honest "not evaluated," never defaulted to "up to
    date"). Deliberately compact -- a status plus the single most
    important change's reason, not the full `MonitoringResult.changes`
    list; the full picture already lives on `evidence_timeline`/
    `materiality` above, which Monitoring only reprioritizes, never
    duplicates (see `atlas.alpha.monitoring`'s own module docstring)."""
    operational_freshness: "CaseOperationalFreshnessView | None"
    """Atlas Intelligence Sprint 8 (Automated Monitoring Operations,
    Deliverable 15). Deliberately a separate field from `monitoring`
    above -- this one is purely operational ("has Atlas recomputed this
    recently, and did that recomputation succeed"), never investment
    confidence. `None` only when Monitoring has no read model wired for
    this build."""
    materiality: MaterialityAssessmentView | None
    """Atlas Intelligence -- Materiality & Priority Engine, Deliverable
    5. `None` only when no materiality classification was built for
    this call, same precedent above."""
    knowledge_coverage: InvestmentCaseKnowledgeCoverageView | None
    """Automatic Investment Case Builder Foundation. `None` only when
    no `InvestmentCaseKnowledgeCoverage` was built for this call, same
    `stance`/`explanation`/`materiality` precedent above -- every real
    API call site wires one, via `api/router.py`'s own composition
    root, so this is populated in practice. A different, lower-level
    question than `coverage` above: not "has Atlas concluded something"
    (evaluator coverage) but "does Atlas have the raw knowledge to
    conclude anything at all" (see `atlas.alpha.knowledge_coverage
    .models`'s own module docstring)."""
    no_provider_data_found: bool = False
    """Import Robustness (Internal Alpha Stabilization 1). `True` only
    when `CanonicalSecurityIdentityGate.latest_resolution_was_no_match`
    reports a real, persisted `NO_MATCH` outcome for this Case's ticker
    -- i.e. no provider has ever returned any identity-bearing data for
    it at all (a crypto/commodity symbol, or any ticker no provider
    recognizes) -- *and* this Case still carries neither
    `company_profile` nor `market_snapshot`. Every other resolution
    outcome (`MANUAL_CONFIRMATION`/`AMBIGUOUS`/`LOW_CONFIDENCE`/
    `REJECT`) means real candidates were found and is deliberately never
    reported here -- see that method's own docstring. `False` (the
    default) is the honest "nothing unusual to report" case, including
    "never even attempted yet" -- never treat this as "Atlas is
    confident this ticker is fine."""

    @classmethod
    def from_domain(
        cls,
        composition: InvestmentCaseComposition,
        *,
        stance: "StanceView | None" = None,
        explanation: "ExplanationView | None" = None,
        evidence_quality_report: "EvidenceQualityReportView | None" = None,
        evidence_timeline: "EvidenceTimelineView | None" = None,
        materiality: "MaterialityAssessmentView | None" = None,
        monitoring: "MonitoringStatusView | None" = None,
        operational_freshness: "CaseOperationalFreshnessView | None" = None,
        knowledge_coverage: "InvestmentCaseKnowledgeCoverageView | None" = None,
    ) -> "InvestmentCaseAnalysisView":
        analysis: CanonicalAnalysis = composition.canonical_analysis

        # Product Sprint 14 (Evidence & Explanation Quality): the one
        # place every finding's own opaque evidence-reference ids get
        # resolved into real prose before they leave this service --
        # built once, from data this method already has in scope
        # (`composition.business_facts`/`.market_facts`/
        # `.observation_history`, plus the very same findings being
        # serialized below, so a Finding-self-reference resolves too).
        resolver = _EvidenceResolverContext(
            facts_by_id={f.id: f for f in (*composition.business_facts, *composition.market_facts)},
            findings_by_id={
                f.id: f
                for f in (
                    *analysis.business_analysis.findings,
                    *analysis.valuation_engine.findings,
                    *analysis.risk_analysis.findings,
                )
            },
            observations_by_id={str(o.id): o for o in composition.observation_history},
        )
        change_intelligence: ChangeIntelligence | None = composition.change_intelligence
        if change_intelligence is None:
            change_intelligence_available = False
            is_baseline_case = False
            latest_changes: list[ChangeFindingView] = []
            change_summary = ""
            thesis_change = ThesisImpact.UNCHANGED.value
            previous_analysis_at = None
            current_analysis_at = composition.generated_at
        else:
            change_intelligence_available = True
            is_baseline_case = change_intelligence.is_baseline
            latest_changes = [ChangeFindingView.from_domain(c) for c in change_intelligence.changes]
            change_summary = change_intelligence.summary_narrative
            thesis_change = change_intelligence.thesis_impact.value
            previous_analysis_at = change_intelligence.previous_captured_at
            current_analysis_at = change_intelligence.current_captured_at
        return cls(
            case_id=composition.case_id,
            holding_context=HoldingContextView.from_domain(composition.holding_context),
            current_thesis=CurrentThesisView.from_domain(composition.current_thesis),
            is_thesis_stale=composition.is_thesis_stale,
            confidence=analysis.confidence.value,
            conviction=ConvictionAssessmentView.from_domain(analysis.conviction),
            coverage=CoverageAssessmentView.from_domain(
                _assess_coverage(analysis, is_thesis_stale=composition.is_thesis_stale)
            ),
            business_analysis=BusinessAnalysisView.from_domain(analysis.business_analysis, resolver=resolver),
            valuation=ValuationEngineView.from_domain(analysis.valuation_engine, resolver=resolver),
            valuation_support=ValuationSupportView.from_domain(analysis.valuation_support),
            risk=RiskAnalysisView.from_domain(analysis.risk_analysis, resolver=resolver),
            risk_projection=RiskProjectionView.from_domain(risk_projection(analysis.risk_analysis)),
            evidence_quality=(
                EvidenceQualityFindingsSchema.from_domain(analysis.business.evidence_quality)
                if analysis.business.evidence_quality
                else None
            ),
            open_questions=[OpenQuestionSchema.from_domain(q) for q in analysis.open_questions],
            recommendation=RecommendationStateView.from_domain(
                analysis.recommendation, analysis.recommendation_outlook_context
            ),
            decision_history=[DecisionHistoryEntryView.from_domain(d) for d in composition.decision_history],
            observation_history=[ObservationEntryView.from_domain(o) for o in composition.observation_history],
            outcome_history=[OutcomeEntryView.from_domain(o) for o in composition.outcome_history],
            trade_log=[TradeLogEntryView.from_domain(t) for t in composition.trade_log],
            company_profile=(
                CompanyProfileView.from_domain(composition.company_profile)
                if composition.company_profile is not None
                else None
            ),
            financial_history=[FinancialPeriodView.from_domain(p) for p in composition.financial_history],
            market_snapshot=(
                MarketSnapshotView.from_domain(composition.market_snapshot)
                if composition.market_snapshot is not None
                else None
            ),
            regulatory_filings=[RegulatoryFilingView.from_domain(f) for f in composition.regulatory_filings],
            historical_valuation=HistoricalValuationView.from_domain(composition.historical_valuation),
            earnings_call=EarningsCallView.from_domain(composition.earnings_call),
            financial_statement_intelligence=FinancialStatementIntelligenceView.from_domain(
                composition.financial_statement_intelligence
            ),
            capital_allocation_intelligence=CapitalAllocationIntelligenceView.from_domain(
                composition.capital_allocation_intelligence
            ),
            financial_quality_intelligence=FinancialQualityIntelligenceView.from_domain(
                composition.financial_quality_intelligence
            ),
            growth_intelligence=GrowthKnowledgeView.from_domain(composition.growth_intelligence),
            business_quality_intelligence=BusinessQualityIntelligenceView.from_domain(composition.business_quality_intelligence),
            management_credibility_intelligence=ManagementCredibilityIntelligenceView.from_domain(
                composition.management_credibility_intelligence
            ),
            management_guidance_intelligence=ManagementGuidanceIntelligenceView.from_domain(
                composition.management_guidance_intelligence
            ),
            executive_change_intelligence=ExecutiveChangeIntelligenceView.from_domain(
                composition.executive_change_intelligence
            ),
            executive_track_record_intelligence=ExecutiveTrackRecordIntelligenceView.from_domain(
                composition.executive_track_record_intelligence
            ),
            incentive_intelligence=IncentiveIntelligenceView.from_domain(composition.incentive_intelligence),
            governance_intelligence=GovernanceIntelligenceView.from_domain(composition.governance_intelligence),
            risk_factor_intelligence=RiskFactorIntelligenceView.from_domain(composition.risk_factor_intelligence),
            legal_proceedings_intelligence=LegalProceedingsIntelligenceView.from_domain(
                composition.legal_proceedings_intelligence
            ),
            ownership_intelligence=OwnershipIntelligenceView.from_domain(composition.ownership_intelligence),
            executive_compensation_intelligence=ExecutiveCompensationIntelligenceView.from_domain(
                composition.executive_compensation_intelligence
            ),
            insider_alignment_intelligence=InsiderAlignmentIntelligenceView.from_domain(
                composition.insider_alignment_intelligence
            ),
            strengths=[CaseHighlightView.from_domain(h) for h in analysis.synthesis.strengths],
            risks=[CaseHighlightView.from_domain(h) for h in analysis.synthesis.risks],
            growth_analysis=GrowthAnalysisView.from_domain(analysis.synthesis.growth),
            valuation_context=ValuationContextView.from_domain(analysis.synthesis.valuation_context),
            atlas_thesis=AtlasThesisView.from_domain(analysis.synthesis.atlas_thesis),
            outlook=OutlookView.from_domain(analysis.outlook, change_intelligence=change_intelligence),
            key_open_questions=[CaseOpenQuestionView.from_domain(q) for q in analysis.synthesis.open_questions],
            change_intelligence_available=change_intelligence_available,
            is_baseline_case=is_baseline_case,
            latest_changes=latest_changes,
            change_summary=change_summary,
            thesis_change=thesis_change,
            previous_analysis_at=previous_analysis_at,
            current_analysis_at=current_analysis_at,
            generated_at=composition.generated_at,
            stance=stance,
            explanation=explanation,
            evidence_quality_report=evidence_quality_report,
            evidence_timeline=evidence_timeline,
            materiality=materiality,
            monitoring=monitoring,
            operational_freshness=operational_freshness,
            knowledge_coverage=knowledge_coverage,
        )
