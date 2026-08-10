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
from atlas.alpha.investment_case.company_profile import CompanyProfile
from atlas.alpha.investment_case.financial_history import FinancialPeriod, MarketSnapshot
from atlas.alpha.investment_case.models import CurrentThesis, InvestmentCaseComposition
from atlas.alpha.portfolio.models import AlphaHolding, AlphaTradeLogEntry
from atlas.analysis_engine.business_contracts import BusinessAnalysisResult, BusinessFinding
from atlas.analysis_engine.conviction import ConvictionAssessment
from atlas.analysis_engine.models import CanonicalAnalysis
from atlas.analysis_engine.risk.models import RiskAnalysisResult, RiskFinding
from atlas.analysis_engine.valuation.models import ValuationEngineResult, ValuationFinding
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.observation.entity import Observation
from atlas.core.infrastructure.api.serialization import CamelModel


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
    def from_domain(cls, finding: BusinessFinding) -> "BusinessFindingView":
        return cls(
            kind=finding.kind.value,
            status=finding.status.value,
            severity=finding.severity.value,
            supporting_evidence=list(finding.supporting_evidence),
            contradicting_evidence=list(finding.contradicting_evidence),
            missing_evidence=[m.value for m in finding.missing_evidence],
            confidence=finding.confidence.value,
            updated_at=finding.updated_at,
        )


class BusinessAnalysisView(CamelModel):
    state: str
    findings: list[BusinessFindingView]

    @classmethod
    def from_domain(cls, result: BusinessAnalysisResult) -> "BusinessAnalysisView":
        return cls(state=result.state.value, findings=[BusinessFindingView.from_domain(f) for f in result.findings])


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
    def from_domain(cls, finding: ValuationFinding) -> "ValuationFindingView":
        return cls(
            kind=finding.kind.value,
            status=finding.status.value,
            severity=finding.severity.value,
            supporting_facts=list(finding.supporting_facts),
            contradicting_facts=list(finding.contradicting_facts),
            assumptions=[a.value for a in finding.assumptions],
            missing_evidence=[m.value for m in finding.missing_evidence],
            confidence=finding.confidence.value,
            current_yield=finding.current_yield,
        )


class ValuationEngineView(CamelModel):
    state: str
    findings: list[ValuationFindingView]

    @classmethod
    def from_domain(cls, result: ValuationEngineResult) -> "ValuationEngineView":
        return cls(state=result.state.value, findings=[ValuationFindingView.from_domain(f) for f in result.findings])


class RiskFindingView(CamelModel):
    category: str
    status: str
    severity: str
    supporting_facts: list[str]
    contradicting_facts: list[str]
    missing_evidence: list[str]
    confidence: str

    @classmethod
    def from_domain(cls, finding: RiskFinding) -> "RiskFindingView":
        return cls(
            category=finding.category.value,
            status=finding.status.value,
            severity=finding.severity.value,
            supporting_facts=list(finding.supporting_facts),
            contradicting_facts=list(finding.contradicting_facts),
            missing_evidence=[m.value for m in finding.missing_evidence],
            confidence=finding.confidence.value,
        )


class RiskAnalysisView(CamelModel):
    state: str
    findings: list[RiskFindingView]

    @classmethod
    def from_domain(cls, result: RiskAnalysisResult) -> "RiskAnalysisView":
        return cls(state=result.state.value, findings=[RiskFindingView.from_domain(f) for f in result.findings])


class ConvictionAssessmentView(CamelModel):
    level: str
    reasons: list[str]

    @classmethod
    def from_domain(cls, assessment: ConvictionAssessment) -> "ConvictionAssessmentView":
        return cls(level=assessment.level.value, reasons=[r.value for r in assessment.reasons])


class RecommendationStateView(CamelModel):
    """Always withheld today (ATLAS-020/024) -- `reason` is the one
    canonical, categorical explanation, never a fabricated directional
    call. `conviction_gate_met` names the one real gate this analysis
    checked, without restating Conviction's own level."""

    kind: str
    reason: str
    conviction_gate_met: bool

    @classmethod
    def from_domain(cls, gate_result) -> "RecommendationStateView":
        recommendation = gate_result.recommendation
        return cls(
            kind=recommendation.kind.value,
            reason=recommendation.reason.value,
            conviction_gate_met=gate_result.conviction_gate_met,
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
    """(Investment Case Engine v1 slice) Descriptive company identity,
    as currently known -- every field beyond `ticker` may be `None`."""

    ticker: str
    name: str | None
    exchange: str | None
    sector: str | None
    industry: str | None
    country: str | None
    description: str | None
    as_of: datetime

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
        )


class FinancialPeriodView(CamelModel):
    period_start: date | None
    period_end: date | None
    revenue: float | None
    free_cash_flow: float | None
    capital_expenditure: float | None
    share_buybacks: float | None
    share_issuance: float | None
    dividends: float | None
    currency: str | None

    @classmethod
    def from_domain(cls, period: FinancialPeriod) -> "FinancialPeriodView":
        return cls(
            period_start=period.period_start,
            period_end=period.period_end,
            revenue=period.revenue,
            free_cash_flow=period.free_cash_flow,
            capital_expenditure=period.capital_expenditure,
            share_buybacks=period.share_buybacks,
            share_issuance=period.share_issuance,
            dividends=period.dividends,
            currency=period.currency,
        )


class MarketSnapshotView(CamelModel):
    as_of: datetime
    share_price: float | None
    shares_outstanding: float | None
    currency: str | None

    @classmethod
    def from_domain(cls, snapshot: MarketSnapshot) -> "MarketSnapshotView":
        return cls(
            as_of=snapshot.as_of,
            share_price=snapshot.share_price,
            shares_outstanding=snapshot.shares_outstanding,
            currency=snapshot.currency,
        )


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
    business_analysis: BusinessAnalysisView
    valuation: ValuationEngineView
    risk: RiskAnalysisView
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
    generated_at: datetime

    @classmethod
    def from_domain(cls, composition: InvestmentCaseComposition) -> "InvestmentCaseAnalysisView":
        analysis: CanonicalAnalysis = composition.canonical_analysis
        return cls(
            case_id=composition.case_id,
            holding_context=HoldingContextView.from_domain(composition.holding_context),
            current_thesis=CurrentThesisView.from_domain(composition.current_thesis),
            is_thesis_stale=composition.is_thesis_stale,
            confidence=analysis.confidence.value,
            conviction=ConvictionAssessmentView.from_domain(analysis.conviction),
            business_analysis=BusinessAnalysisView.from_domain(analysis.business_analysis),
            valuation=ValuationEngineView.from_domain(analysis.valuation_engine),
            risk=RiskAnalysisView.from_domain(analysis.risk_analysis),
            evidence_quality=(
                EvidenceQualityFindingsSchema.from_domain(analysis.business.evidence_quality)
                if analysis.business.evidence_quality
                else None
            ),
            open_questions=[OpenQuestionSchema.from_domain(q) for q in analysis.open_questions],
            recommendation=RecommendationStateView.from_domain(analysis.recommendation),
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
            generated_at=composition.generated_at,
        )
