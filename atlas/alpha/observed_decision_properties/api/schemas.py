"""HTTP response schemas for Observed Decision Properties v1 (Sprint 13).
Wire format is camelCase via the shared Core `CamelModel` (ADR-004),
matching every other Alpha schema module.

`LIMITATIONS_V1` is a fixed, deterministic constant, not a per-request
computation -- Sprint 12 Phase 13/17 established these truths hold for
every v1 response unconditionally (no property in this endpoint is ever
Outcome-aware, causal, or a fixed identity), so they travel once at the
envelope level rather than being repeated, or risking drifting out of
sync, per property. `outcomeAware`/`sampleSizeWarning` remain per-
property structural fields (see `models.py`) precisely because Sprint
12 required per-observation traceability for those two -- they are not
duplicated into this envelope-level list.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.observed_decision_properties.models import ObservedDecisionProperty, ObservedPropertyScope
from atlas.core.infrastructure.api.serialization import CamelModel

LIMITATIONS_V1: tuple[str, ...] = (
    "Based only on recorded Decisions.",
    "Outcomes are not considered in this view.",
    "Reflects your current recorded history, recomputed on every request -- not a fixed identity.",
    "Observed recurrence is not a performance assessment and does not imply causation.",
)


class ObservedDecisionPropertyView(CamelModel):
    property_type: str
    factual_description: str
    scope: ObservedPropertyScope
    observed_count: int
    total_eligible_decisions: int
    proportion: float
    supporting_decision_ids: list[str]
    first_observed_at: datetime
    last_observed_at: datetime
    outcome_aware: bool
    sample_size_warning: bool

    @classmethod
    def from_domain(cls, property_: ObservedDecisionProperty) -> "ObservedDecisionPropertyView":
        return cls(
            property_type=property_.property_type,
            factual_description=property_.factual_description,
            scope=property_.scope,
            observed_count=property_.observed_count,
            total_eligible_decisions=property_.total_eligible_decisions,
            proportion=property_.proportion,
            supporting_decision_ids=list(property_.supporting_decision_ids),
            first_observed_at=property_.first_observed_at,
            last_observed_at=property_.last_observed_at,
            outcome_aware=property_.outcome_aware,
            sample_size_warning=property_.sample_size_warning,
        )


class ObservedDecisionPropertiesView(CamelModel):
    """The full response envelope. `properties` is empty, never
    fabricated or omitted, for a Decision history with no recognized
    recurrence (Sprint 13 Phase 16/17) -- an empty list is itself the
    honest answer, not an error."""

    properties: list[ObservedDecisionPropertyView]
    limitations: list[str]

    @classmethod
    def from_domain(cls, properties: tuple[ObservedDecisionProperty, ...]) -> "ObservedDecisionPropertiesView":
        return cls(
            properties=[ObservedDecisionPropertyView.from_domain(p) for p in properties],
            limitations=list(LIMITATIONS_V1),
        )
