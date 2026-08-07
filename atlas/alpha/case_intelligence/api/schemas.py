"""HTTP response schemas for the Case Intelligence API (ATLAS-017).

Wire format is camelCase via the shared Core `CamelModel` (ADR-004).
Every enum is serialized as its raw English `.value`. Reuses
`ConsiderItemView`/`PortfolioFitStatusView` directly from
`atlas.alpha.portfolio_intelligence.api.schemas` (ATLAS-016) -- the same
wire shape, never redefined.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.case_intelligence.models import (
    CaseIntelligenceReport,
    ConvictionStatus,
    CurrentThesis,
    CurrentView,
    DecisionHistoryEntry,
    KeyRiskItem,
    ObservationTimelineEntry,
    PortfolioContextSummary,
    ReviewStatus,
)
from atlas.alpha.portfolio_intelligence.api.schemas import ConsiderItemView, PortfolioFitStatusView
from atlas.core.infrastructure.api.serialization import CamelModel
from atlas.decision_engine.contracts import (
    ContradictionSummary,
    EvidenceGap,
    EvidenceQualityFindings,
    ObservationEvidenceClassification,
    OpenQuestion,
    SupportingEvidenceSummary,
)


class CurrentViewSchema(CamelModel):
    ticker: str | None
    held: bool
    weight_percent: float | None
    value_absolute: float | None
    reconciliation_status: str | None

    @classmethod
    def from_domain(cls, view: CurrentView) -> "CurrentViewSchema":
        return cls(
            ticker=view.ticker,
            held=view.held,
            weight_percent=view.weight_percent,
            value_absolute=view.value_absolute,
            reconciliation_status=view.reconciliation_status,
        )


class CurrentThesisSchema(CamelModel):
    latest_decision_reason: str | None
    latest_decision_type: str | None
    latest_observation_statement: str | None

    @classmethod
    def from_domain(cls, thesis: CurrentThesis) -> "CurrentThesisSchema":
        return cls(
            latest_decision_reason=thesis.latest_decision_reason,
            latest_decision_type=thesis.latest_decision_type,
            latest_observation_statement=thesis.latest_observation_statement,
        )


class ObservationEvidenceClassificationSchema(CamelModel):
    observation_id: str
    status: str
    supporting_evidence_count: int
    challenging_evidence_count: int

    @classmethod
    def from_domain(
        cls, item: ObservationEvidenceClassification
    ) -> "ObservationEvidenceClassificationSchema":
        return cls(
            observation_id=str(item.observation_id),
            status=item.status.value,
            supporting_evidence_count=item.supporting_evidence_count,
            challenging_evidence_count=item.challenging_evidence_count,
        )


class EvidenceQualityFindingsSchema(CamelModel):
    total_evidence_count: int
    supporting_evidence_count: int
    challenging_evidence_count: int
    coverage: str
    observation_classifications: list[ObservationEvidenceClassificationSchema]

    @classmethod
    def from_domain(cls, findings: EvidenceQualityFindings) -> "EvidenceQualityFindingsSchema":
        return cls(
            total_evidence_count=findings.total_evidence_count,
            supporting_evidence_count=findings.supporting_evidence_count,
            challenging_evidence_count=findings.challenging_evidence_count,
            coverage=findings.coverage.value,
            observation_classifications=[
                ObservationEvidenceClassificationSchema.from_domain(c)
                for c in findings.observation_classifications
            ],
        )


class SupportingEvidenceSummarySchema(CamelModel):
    observation_classifications: list[ObservationEvidenceClassificationSchema]

    @classmethod
    def from_domain(cls, summary: SupportingEvidenceSummary) -> "SupportingEvidenceSummarySchema":
        return cls(
            observation_classifications=[
                ObservationEvidenceClassificationSchema.from_domain(c)
                for c in summary.observation_classifications
            ]
        )


class ContradictionSummarySchema(CamelModel):
    observation_classifications: list[ObservationEvidenceClassificationSchema]

    @classmethod
    def from_domain(cls, summary: ContradictionSummary) -> "ContradictionSummarySchema":
        return cls(
            observation_classifications=[
                ObservationEvidenceClassificationSchema.from_domain(c)
                for c in summary.observation_classifications
            ]
        )


class EvidenceGapSchema(CamelModel):
    kind: str
    reference: str | None

    @classmethod
    def from_domain(cls, gap: EvidenceGap) -> "EvidenceGapSchema":
        return cls(kind=gap.kind.value, reference=gap.reference)


class OpenQuestionSchema(CamelModel):
    kind: str
    reference: str | None

    @classmethod
    def from_domain(cls, question: OpenQuestion) -> "OpenQuestionSchema":
        return cls(kind=question.kind.value, reference=question.reference)


class KeyRiskItemSchema(CamelModel):
    kind: str
    reference: str | None

    @classmethod
    def from_domain(cls, item: KeyRiskItem) -> "KeyRiskItemSchema":
        return cls(kind=item.kind.value, reference=item.reference)


class DecisionHistoryEntrySchema(CamelModel):
    decision_id: str
    decision_type: str
    reason: str
    investor_confidence: int
    decided_at: datetime
    outcome_id: str | None
    outcome_statement: str | None
    outcome_occurred_at: datetime | None

    @classmethod
    def from_domain(cls, entry: DecisionHistoryEntry) -> "DecisionHistoryEntrySchema":
        return cls(
            decision_id=entry.decision_id,
            decision_type=entry.decision_type,
            reason=entry.reason,
            investor_confidence=entry.investor_confidence,
            decided_at=entry.decided_at,
            outcome_id=entry.outcome_id,
            outcome_statement=entry.outcome_statement,
            outcome_occurred_at=entry.outcome_occurred_at,
        )


class ObservationTimelineEntrySchema(CamelModel):
    observation_id: str
    subject: str
    statement: str
    observed_at: datetime
    evidence_count: int
    epistemic_status: str | None

    @classmethod
    def from_domain(cls, entry: ObservationTimelineEntry) -> "ObservationTimelineEntrySchema":
        return cls(
            observation_id=entry.observation_id,
            subject=entry.subject,
            statement=entry.statement,
            observed_at=entry.observed_at,
            evidence_count=entry.evidence_count,
            epistemic_status=entry.epistemic_status,
        )


class PortfolioContextSummarySchema(CamelModel):
    held: bool
    facts: list[str]
    weight_percent: float | None
    concentration_level: str | None
    most_recent_trade_transaction_type: str | None
    most_recent_trade_at: datetime | None

    @classmethod
    def from_domain(cls, summary: PortfolioContextSummary) -> "PortfolioContextSummarySchema":
        return cls(
            held=summary.held,
            facts=[fact.value for fact in summary.facts],
            weight_percent=summary.weight_percent,
            concentration_level=summary.concentration_level,
            most_recent_trade_transaction_type=summary.most_recent_trade_transaction_type,
            most_recent_trade_at=summary.most_recent_trade_at,
        )


class ConvictionStatusSchema(CamelModel):
    available: bool
    reason: str | None

    @classmethod
    def from_domain(cls, status: ConvictionStatus) -> "ConvictionStatusSchema":
        return cls(available=status.available, reason=status.reason.value if status.reason else None)


class ReviewStatusSchema(CamelModel):
    is_stale: bool
    age_days: int | None

    @classmethod
    def from_domain(cls, status: ReviewStatus) -> "ReviewStatusSchema":
        return cls(is_stale=status.is_stale, age_days=status.age_days)


class CaseIntelligenceView(CamelModel):
    case_id: str
    current_view: CurrentViewSchema
    current_thesis: CurrentThesisSchema
    evidence_quality: EvidenceQualityFindingsSchema | None
    supporting_evidence: SupportingEvidenceSummarySchema | None
    contradicting_evidence: ContradictionSummarySchema | None
    missing_evidence: list[EvidenceGapSchema]
    open_questions: list[OpenQuestionSchema]
    key_risks: list[KeyRiskItemSchema]
    decision_history: list[DecisionHistoryEntrySchema]
    observation_timeline: list[ObservationTimelineEntrySchema]
    portfolio_context: PortfolioContextSummarySchema
    portfolio_fit: PortfolioFitStatusView
    conviction: ConvictionStatusSchema
    confidence: str
    review_status: ReviewStatusSchema
    consider_items: list[ConsiderItemView]

    @classmethod
    def from_domain(cls, report: CaseIntelligenceReport) -> "CaseIntelligenceView":
        return cls(
            case_id=report.case_id,
            current_view=CurrentViewSchema.from_domain(report.current_view),
            current_thesis=CurrentThesisSchema.from_domain(report.current_thesis),
            evidence_quality=(
                EvidenceQualityFindingsSchema.from_domain(report.evidence_quality)
                if report.evidence_quality
                else None
            ),
            supporting_evidence=(
                SupportingEvidenceSummarySchema.from_domain(report.supporting_evidence)
                if report.supporting_evidence
                else None
            ),
            contradicting_evidence=(
                ContradictionSummarySchema.from_domain(report.contradicting_evidence)
                if report.contradicting_evidence
                else None
            ),
            missing_evidence=[EvidenceGapSchema.from_domain(g) for g in report.missing_evidence],
            open_questions=[OpenQuestionSchema.from_domain(q) for q in report.open_questions],
            key_risks=[KeyRiskItemSchema.from_domain(r) for r in report.key_risks],
            decision_history=[DecisionHistoryEntrySchema.from_domain(d) for d in report.decision_history],
            observation_timeline=[
                ObservationTimelineEntrySchema.from_domain(o) for o in report.observation_timeline
            ],
            portfolio_context=PortfolioContextSummarySchema.from_domain(report.portfolio_context),
            portfolio_fit=PortfolioFitStatusView.from_domain(report.portfolio_fit),
            conviction=ConvictionStatusSchema.from_domain(report.conviction),
            confidence=report.confidence.value,
            review_status=ReviewStatusSchema.from_domain(report.review_status),
            consider_items=[ConsiderItemView.from_domain(c) for c in report.consider_items],
        )
