"""Repository interface for the CaseCondition aggregate (ADR-CC-001).

Insert-only, mirroring `DecisionDraftEventRepository` (Sprint 9)
exactly: there is no update method, so "no UPDATE, ever" is enforced
at the type level, not by convention.
"""
from __future__ import annotations

from typing import Protocol

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.case_condition.entity import CaseConditionEvent
from atlas.core.domain.case_condition.value_objects import CaseConditionId
from atlas.core.domain.decision.value_objects import DecisionId


class CaseConditionEventRepository(Protocol):
    def add(self, event: CaseConditionEvent) -> None:
        """Insert a new event. Never UPDATEs or DELETEs."""
        ...

    def get_latest_event(self, condition_id: CaseConditionId) -> CaseConditionEvent | None:
        """The single most recent event for a condition, or None if it never existed."""
        ...

    def list_events(self, condition_id: CaseConditionId) -> list[CaseConditionEvent]:
        """Full history for one condition, oldest first."""
        ...

    def list_latest_by_case(self, case_id: CaseId) -> list[CaseConditionEvent]:
        """The latest event for every distinct condition_id ever created
        under this Case, regardless of current status — filtering to
        Active/non-terminal is an application-layer concern, not a
        repository one.
        """
        ...

    def list_latest_by_decision(self, decision_id: DecisionId) -> list[CaseConditionEvent]:
        """The latest event for every distinct condition_id whose
        optional `decision_id` back-reference (ADR-CC-001 §6) names
        this Decision."""
        ...
