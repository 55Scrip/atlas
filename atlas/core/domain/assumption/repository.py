"""Repository interface for the Assumption aggregate (ADR-AS-001).

Insert-only, mirroring `CaseConditionEventRepository` (Sprint 10)
exactly: no update method, so "no UPDATE, ever" is enforced at the
type level.
"""
from __future__ import annotations

from typing import Protocol

from atlas.core.domain.assumption.entity import AssumptionEvent
from atlas.core.domain.assumption.value_objects import AssumptionId
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.value_objects import DecisionId


class AssumptionEventRepository(Protocol):
    def add(self, event: AssumptionEvent) -> None:
        """Insert a new event. Never UPDATEs or DELETEs."""
        ...

    def get_latest_event(self, assumption_id: AssumptionId) -> AssumptionEvent | None:
        """The single most recent event for an assumption, or None if it never existed."""
        ...

    def list_events(self, assumption_id: AssumptionId) -> list[AssumptionEvent]:
        """Full history for one assumption, oldest first."""
        ...

    def list_latest_by_decision(self, decision_id: DecisionId) -> list[AssumptionEvent]:
        """The latest event for every distinct assumption_id anchored to
        this Decision, regardless of current status."""
        ...

    def list_latest_by_case(self, case_id: CaseId) -> list[AssumptionEvent]:
        """The latest event for every distinct assumption_id whose
        denormalized `case_id` (reached transitively via `decision_id`,
        per ADR-AS-001 §1) matches this Case."""
        ...
