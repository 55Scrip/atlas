"""Data model for the Case Intelligence report (ATLAS-017).

Every field is either read verbatim from a Core record, reused directly
from `atlas.decision_engine.contracts` (the canonical pipeline's own
output types -- imported, never redefined), or reused directly from
`atlas.alpha.portfolio_intelligence.models` (ATLAS-016's own
`ConsiderItem`/`PortfolioFitStatus`). See package `__init__.py` for the
full "no duplicated reasoning" rationale.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.alpha.portfolio_intelligence.models import ConsiderItem, PortfolioFitStatus
from atlas.decision_engine.contracts import (
    ContradictionSummary,
    EvidenceCoverageLevel,
    EvidenceGap,
    EvidenceQualityFindings,
    OpenQuestion,
    SupportingEvidenceSummary,
)

__all__ = [
    "CurrentView",
    "CurrentThesis",
    "KeyRiskKind",
    "KeyRiskItem",
    "DecisionHistoryEntry",
    "ObservationTimelineEntry",
    "PortfolioContextFact",
    "PortfolioContextSummary",
    "ConvictionUnavailableReason",
    "ConvictionStatus",
    "ReviewStatus",
    "CaseIntelligenceReport",
]


@dataclass(frozen=True)
class CurrentView:
    """The Case's present, factual state -- ticker identity (if any)
    comes only from `AlphaHolding.case_id`, the same one linkage
    `InvestmentCasePage.tsx` already reads (`Case` itself carries no
    identity; see `atlas/core/domain/case/entity.py`)."""

    ticker: str | None
    held: bool
    weight_percent: float | None
    value_absolute: float | None
    reconciliation_status: str | None


@dataclass(frozen=True)
class CurrentThesis:
    """The investor's own most recent words -- never summarized,
    never rephrased. `latest_decision_reason` is
    `Decision.investment_case.reason` verbatim; `latest_observation_statement`
    is `Observation.statement` verbatim."""

    latest_decision_reason: str | None
    latest_decision_type: str | None
    latest_observation_statement: str | None


class KeyRiskKind(str, Enum):
    """A deterministic, already-supported risk fact -- every member maps
    1:1 onto a Decision Engine finding or an existing Alpha fact, never a
    new risk model. `CONTRADICTING_EVIDENCE` reuses
    `ReasoningFinding.contradicting_evidence` verbatim; the other two
    reuse the same concentration/reconciliation facts
    `atlas.alpha.portfolio_intelligence` already computes for this
    ticker."""

    CONTRADICTING_EVIDENCE = "contradicting_evidence"
    HIGH_CONCENTRATION = "high_concentration"
    AWAITING_RECONCILIATION = "awaiting_reconciliation"


@dataclass(frozen=True)
class KeyRiskItem:
    kind: KeyRiskKind
    reference: str | None = None


@dataclass(frozen=True)
class DecisionHistoryEntry:
    """One Decision, joined with its most recent Outcome (if any) by
    `decision_id` -- a straight join over already-captured records, no
    interpretation. `investor_confidence` is `Decision.confidence.value`,
    labeled explicitly as investor-entered -- never relabeled or reused
    as Atlas's own conviction (see `ConvictionStatus`)."""

    decision_id: str
    decision_type: str
    reason: str
    investor_confidence: int
    decided_at: datetime
    outcome_id: str | None
    outcome_statement: str | None
    outcome_occurred_at: datetime | None


@dataclass(frozen=True)
class ObservationTimelineEntry:
    """One Observation with its evidence count and epistemic status --
    `epistemic_status` reuses `ObservationEvidenceClassification.status`
    from the Decision Engine's own Evidence Quality finding verbatim,
    `None` only when the pipeline carried no classification for it."""

    observation_id: str
    subject: str
    statement: str
    observed_at: datetime
    evidence_count: int
    epistemic_status: str | None


class PortfolioContextFact(str, Enum):
    """A deterministic portfolio-context fact -- every member reuses an
    existing Portfolio Status/Intelligence computation for this one
    ticker, never a new one. "Recently increased"/"recently trimmed"
    reflect the most recent recorded trade's direction, not a time-decay
    window (no such window exists elsewhere in this codebase to reuse;
    see `CaseIntelligenceService` module docstring)."""

    LARGEST_HOLDING = "largest_holding"
    RECENTLY_INCREASED = "recently_increased"
    RECENTLY_TRIMMED = "recently_trimmed"
    HIGH_CONCENTRATION = "high_concentration"
    PENDING_WORKFLOW = "pending_workflow"
    EVIDENCE_INCOMPLETE = "evidence_incomplete"


@dataclass(frozen=True)
class PortfolioContextSummary:
    held: bool
    facts: tuple[PortfolioContextFact, ...]
    weight_percent: float | None
    concentration_level: str | None
    most_recent_trade_transaction_type: str | None
    most_recent_trade_at: datetime | None


class ConvictionUnavailableReason(str, Enum):
    NO_ATLAS_COMPUTED_CONVICTION_EXISTS = "no_atlas_computed_conviction_exists"


@dataclass(frozen=True)
class ConvictionStatus:
    """Always `available=False` -- no field in this codebase's domain
    model represents an Atlas-computed conviction. `Decision.confidence`
    exists but is investor-entered and never interpreted by Atlas (see
    `atlas/core/domain/decision/value_objects.py`); it is surfaced
    separately, and only, on `DecisionHistoryEntry.investor_confidence`
    -- never folded into this type, so a reader can never mistake the
    investor's own number for an Atlas conclusion."""

    available: bool
    reason: ConvictionUnavailableReason | None = None


@dataclass(frozen=True)
class ReviewStatus:
    """Reuses `atlas.alpha.portfolio_status.service.VERY_OLD_CASE_THRESHOLD_DAYS`
    (ATLAS-015's own 90-day threshold) verbatim -- not a new number."""

    is_stale: bool
    age_days: int | None


@dataclass(frozen=True)
class CaseIntelligenceReport:
    case_id: str
    current_view: CurrentView
    current_thesis: CurrentThesis
    evidence_quality: EvidenceQualityFindings | None
    supporting_evidence: SupportingEvidenceSummary | None
    contradicting_evidence: ContradictionSummary | None
    missing_evidence: tuple[EvidenceGap, ...]
    open_questions: tuple[OpenQuestion, ...]
    key_risks: tuple[KeyRiskItem, ...]
    decision_history: tuple[DecisionHistoryEntry, ...]
    observation_timeline: tuple[ObservationTimelineEntry, ...]
    portfolio_context: PortfolioContextSummary
    portfolio_fit: PortfolioFitStatus
    conviction: ConvictionStatus
    confidence: EvidenceCoverageLevel
    review_status: ReviewStatus
    consider_items: tuple[ConsiderItem, ...]
