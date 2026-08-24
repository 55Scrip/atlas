"""HTTP response schemas for the Investment Case Lifecycle. Wire format
is camelCase via the shared Core `CamelModel` (ADR-004). Every field is
a direct read of an already-computed `AtlasStatus` -- nothing is
recomputed or reworded here."""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.investment_case_lifecycle.models import (
    AtlasStatus,
    MandatoryCoreAssessment,
    MandatoryItemAssessment,
    RegressionRecord,
)
from atlas.core.infrastructure.api.serialization import CamelModel


class MandatoryItemAssessmentView(CamelModel):
    item: str
    satisfied: bool
    satisfied_via: str | None
    reason: str | None

    @classmethod
    def from_domain(cls, item: MandatoryItemAssessment) -> "MandatoryItemAssessmentView":
        return cls(
            item=item.item.value,
            satisfied=item.satisfied,
            satisfied_via=item.satisfied_via,
            reason=item.reason.value if item.reason is not None else None,
        )


class MandatoryCoreAssessmentView(CamelModel):
    items: list[MandatoryItemAssessmentView]
    all_satisfied: bool

    @classmethod
    def from_domain(cls, core: MandatoryCoreAssessment) -> "MandatoryCoreAssessmentView":
        return cls(
            items=[MandatoryItemAssessmentView.from_domain(i) for i in core.items],
            all_satisfied=core.all_satisfied,
        )


class RegressionRecordView(CamelModel):
    occurred_at: datetime
    invalidated_items: list[str]
    reasons: list[str]

    @classmethod
    def from_domain(cls, regression: RegressionRecord) -> "RegressionRecordView":
        return cls(
            occurred_at=regression.occurred_at,
            invalidated_items=[i.value for i in regression.invalidated_items],
            reasons=[r.value for r in regression.reasons],
        )


class AtlasStatusView(CamelModel):
    case_id: str
    lifecycle_state: str
    mandatory_core: MandatoryCoreAssessmentView
    evidence_tier: str
    important_missing_items: list[str]
    optional_missing_items: list[str]
    next_expected_action: str
    last_updated: datetime | None
    next_refresh_description: str
    published_since: datetime | None
    last_regression: RegressionRecordView | None
    generated_at: datetime

    @classmethod
    def from_domain(cls, status: AtlasStatus) -> "AtlasStatusView":
        return cls(
            case_id=status.case_id,
            lifecycle_state=status.lifecycle_state.value,
            mandatory_core=MandatoryCoreAssessmentView.from_domain(status.mandatory_core),
            evidence_tier=status.evidence_tier.value,
            important_missing_items=list(status.important_missing_items),
            optional_missing_items=list(status.optional_missing_items),
            next_expected_action=status.next_expected_action,
            last_updated=status.last_updated,
            next_refresh_description=status.next_refresh_description,
            published_since=status.published_since,
            last_regression=RegressionRecordView.from_domain(status.last_regression)
            if status.last_regression is not None
            else None,
            generated_at=status.generated_at,
        )
