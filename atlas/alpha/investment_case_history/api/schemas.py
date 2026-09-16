"""HTTP response schemas for History v1. Wire format is camelCase via
the shared Core `CamelModel` (ADR-004), matching every other Alpha
schema module. Reuses `ChangeFindingView` from `atlas.alpha
.investment_case.api.schemas` directly for the `changes` field -- the
identical wire shape for the identical underlying
`investment_case_change.ChangeFinding`, never redefined.

Every field here is a direct read of an already-persisted
`AnalyticalSnapshot`/`ChangeIntelligence` pair (see this package's own
`__init__.py`) -- nothing is recomputed. `snapshot_id` is the one field
with no direct domain counterpart: `AnalyticalSnapshot` itself carries
no synthetic id (the repository keys rows by `(case_id, captured_at)`
alone), so it is derived here, at the wire boundary only, as
`f"{case_id}:{captured_at.isoformat()}"` -- stable and unique per row,
used by the frontend purely as a React key / expand-state key, never
interpreted as a real persistence identifier.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.investment_case.api.schemas import ChangeFindingView
from atlas.alpha.investment_case.valuation_evidence_snapshot import ValuationEvidenceSnapshot
from atlas.alpha.investment_case_history.service import AnalyticalHistoryWithEvidence, snapshot_identity
from atlas.analysis_engine.investment_case_history import AnalyticalHistory, HistoricalAnalysisEntry
from atlas.core.infrastructure.api.serialization import CamelModel


class BusinessCategoryStateView(CamelModel):
    category: str
    status: str
    finding_id: str


class RiskCategoryStateView(CamelModel):
    category: str
    status: str
    finding_id: str


class HistoricalPriorEpochView(CamelModel):
    """One fiscal year exactly as the analysis of that day compared it."""

    fiscal_period: str
    fiscal_year: int
    fcf_yield: float
    free_cash_flow: float
    issuer_market_cap: float
    denominator_quality: str | None


class HistoricalRangeEdgeView(CamelModel):
    """Which years owned the ends of the observed range at that analysis."""

    low_edge_fiscal_year: int | None
    low_edge_fcf_yield: float | None
    low_edge_denominator_quality: str | None
    second_lowest_fiscal_year: int | None
    second_lowest_fcf_yield: float | None
    high_edge_fiscal_year: int | None
    high_edge_fcf_yield: float | None
    second_highest_fiscal_year: int | None
    second_highest_fcf_yield: float | None
    priors_at_or_below_current: int
    priors_at_or_above_current: int
    single_low_edge_dependency: bool
    single_high_edge_dependency: bool


class HistoricalValuationEvidenceView(CamelModel):
    """What Atlas actually had when it reached this historical conclusion.

    Every value is read from the evidence frozen with that snapshot. Nothing
    is recomputed and nothing is substituted from today: a later filing, a
    price refresh or a new methodology changes what Atlas says *now*, never
    what this entry reports it had *then*.

    Absent entirely (`null` on the entry) for a snapshot written before Atlas
    began freezing evidence -- which is "never recorded", not "there was no
    evidence".
    """

    schema_version: str
    valuation_methodology: str | None
    numerator_method: str | None
    share_count_method: str
    valuation_status: str
    valuation_position: str | None
    fcf_yield_at_analysis: float | None
    eligibility: str
    minimum_prior_count: int
    withheld_reasons: list[str]
    valuation_support_status: str
    valuation_support_gap: str | None
    prior_epoch_count: int
    prior_epochs: list[HistoricalPriorEpochView]
    range_edge: HistoricalRangeEdgeView | None

    @classmethod
    def from_domain(cls, evidence: ValuationEvidenceSnapshot | None) -> "HistoricalValuationEvidenceView | None":
        if evidence is None:
            return None
        metadata = evidence.metadata or {}
        edge = (metadata.get("range_edge") or {}) if isinstance(metadata, dict) else {}

        def side(key: str, field: str):
            return (edge.get(key) or {}).get(field) if edge.get(key) else None

        return cls(
            schema_version=evidence.schema_version,
            valuation_methodology=evidence.valuation_methodology,
            numerator_method=evidence.numerator_method,
            share_count_method=evidence.share_count_method,
            valuation_status=evidence.valuation_status,
            valuation_position=evidence.valuation_position,
            fcf_yield_at_analysis=evidence.current_yield,
            eligibility=evidence.eligibility,
            minimum_prior_count=evidence.minimum_prior_epochs,
            withheld_reasons=list(evidence.withheld_reasons),
            valuation_support_status=evidence.valuation_support_status,
            valuation_support_gap=evidence.valuation_support_gap,
            prior_epoch_count=len(evidence.prior_epochs),
            prior_epochs=[
                HistoricalPriorEpochView(
                    fiscal_period=epoch.fiscal_period,
                    fiscal_year=int(epoch.fiscal_period[:4]),
                    fcf_yield=epoch.fcf_yield,
                    free_cash_flow=epoch.free_cash_flow,
                    issuer_market_cap=(
                        (epoch.market_cap_low + epoch.market_cap_high) / 2
                        if epoch.market_cap_low is not None and epoch.market_cap_high is not None
                        else epoch.share_price * epoch.shares_outstanding
                    ),
                    denominator_quality=epoch.denominator_quality,
                )
                for epoch in evidence.prior_epochs
            ],
            range_edge=None if not edge else HistoricalRangeEdgeView(
                low_edge_fiscal_year=side("low_edge", "fiscal_year"),
                low_edge_fcf_yield=side("low_edge", "fcf_yield"),
                low_edge_denominator_quality=side("low_edge", "denominator_quality"),
                second_lowest_fiscal_year=side("second_lowest", "fiscal_year"),
                second_lowest_fcf_yield=side("second_lowest", "fcf_yield"),
                high_edge_fiscal_year=side("high_edge", "fiscal_year"),
                high_edge_fcf_yield=side("high_edge", "fcf_yield"),
                second_highest_fiscal_year=side("second_highest", "fiscal_year"),
                second_highest_fcf_yield=side("second_highest", "fcf_yield"),
                priors_at_or_below_current=edge.get("priors_at_or_below_current", 0),
                priors_at_or_above_current=edge.get("priors_at_or_above_current", 0),
                single_low_edge_dependency=bool(edge.get("single_low_edge_dependency")),
                single_high_edge_dependency=bool(edge.get("single_high_edge_dependency")),
            ),
        )


class HistoricalAnalysisEntryView(CamelModel):
    """One Case's own persisted analytical state at one point in time,
    plus the (persisted, never recomputed) `ChangeIntelligence`
    describing how it differs from the entry immediately before it for
    the same Case. Product-language field names throughout -- no
    `AnalyticalSnapshot`/`ChangeFinding`/`content_hash`/
    `BusinessCategoryStatus` vocabulary leaks past this schema."""

    case_id: str
    ticker: str | None
    snapshot_id: str
    captured_at: datetime
    is_baseline: bool
    thesis_impact: str
    summary: str
    change_count: int
    changes: list[ChangeFindingView]
    atlas_thesis_narrative: str | None
    atlas_thesis_posture: str | None
    strengths: list[str]
    risks: list[str]
    open_questions: list[str]
    business_category_states: list[BusinessCategoryStateView]
    risk_category_states: list[RiskCategoryStateView]
    valuation_status: str
    current_yield: float | None
    #: The evidence frozen with this snapshot. `null` means the snapshot
    #: predates evidence persistence -- never "Atlas had no evidence".
    valuation_evidence: HistoricalValuationEvidenceView | None = None

    @classmethod
    def from_domain(cls, entry: HistoricalAnalysisEntry,
                    evidence: ValuationEvidenceSnapshot | None = None) -> "HistoricalAnalysisEntryView":
        snapshot = entry.snapshot
        change_intelligence = entry.change_intelligence
        return cls(
            case_id=entry.case_id,
            ticker=entry.ticker,
            snapshot_id=f"{entry.case_id}:{snapshot.captured_at.isoformat()}",
            captured_at=snapshot.captured_at,
            is_baseline=change_intelligence.is_baseline,
            thesis_impact=change_intelligence.thesis_impact.value,
            summary=change_intelligence.summary_narrative,
            change_count=len(change_intelligence.changes),
            changes=[ChangeFindingView.from_domain(c) for c in change_intelligence.changes],
            atlas_thesis_narrative=snapshot.atlas_thesis_narrative,
            atlas_thesis_posture=snapshot.atlas_thesis_posture,
            strengths=list(snapshot.strength_kinds),
            risks=list(snapshot.risk_highlight_kinds),
            open_questions=list(snapshot.open_question_origins),
            business_category_states=[
                BusinessCategoryStateView(category=category, status=status, finding_id=finding_id)
                for category, status, finding_id in snapshot.business_category_states
            ],
            risk_category_states=[
                RiskCategoryStateView(category=category, status=status, finding_id=finding_id)
                for category, status, finding_id in snapshot.risk_category_states
            ],
            valuation_status=snapshot.valuation_status,
            current_yield=snapshot.current_yield,
            valuation_evidence=HistoricalValuationEvidenceView.from_domain(evidence),
        )


class AnalyticalHistoryView(CamelModel):
    """One bounded page of the combined history, newest first.

    `generated_at` is when this page was produced, so successive pages of one
    traversal legitimately differ -- it is response metadata, never a
    pagination identity. The boundary is `next_cursor`, which is opaque: a
    client stores it and sends it back, and must not parse it.
    """

    generated_at: datetime
    entries: list[HistoricalAnalysisEntryView]
    #: `None` when this is the last page. `has_more` says the same thing, and
    #: is what a client should branch on.
    next_cursor: str | None = None
    has_more: bool = False

    @classmethod
    def from_domain(cls, history: AnalyticalHistoryWithEvidence) -> "AnalyticalHistoryView":
        """The join: Core's own ordering is preserved exactly, and each entry
        picks up the evidence frozen with that snapshot by its own identity --
        never the latest evidence for the ticker."""
        by_snapshot = history.evidence_by_snapshot_id
        return cls(
            next_cursor=history.next_cursor,
            has_more=history.has_more,
            generated_at=history.history.generated_at,
            entries=[
                HistoricalAnalysisEntryView.from_domain(
                    entry, by_snapshot.get(snapshot_identity(entry.case_id, entry.snapshot.captured_at)))
                for entry in history.history.entries
            ],
        )
