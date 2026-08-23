"""`CaseConditionService` — the application service for CaseCondition
(ADR-CC-001).

Method names follow Sprint 10's own brief: `create` (CreateCondition),
`revise` (ReviseCondition), `retire` (RetireCondition), `evaluate`
(EvaluateCondition), `list_for_case`/`list_for_decision`
(ListConditions), `read` (ReadCurrentState). One method beyond that
list, `supersede`, is added — see this sprint's own execution report,
"Implementation findings": ADR-CC-001 §2 names `superseded` as one of
exactly four required event types, and no method in Sprint 10's own
brief can ever produce one; `supersede` is the direct, mechanical
completion this omission requires, mirroring the identical judgment
call `DecisionDraft-Implementation-Design.md` §5.1 already made once
for a missing repository method (Sprint 9).

Ordering safety follows `security_confirmation`/`decision_draft`'s own
`_next_recorded_at` idiom verbatim.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from atlas.core.domain.case.exceptions import CaseNotFoundError
from atlas.core.domain.case.repository import CaseRepository
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.case_condition.entity import (
    CaseConditionAuthorship,
    CaseConditionEvent,
    CaseConditionRole,
    CaseConditionStructuredKind,
    CaseConditionView,
    ThresholdOperator,
    is_terminal,
    reconstruct_current_state,
)
from atlas.core.domain.case_condition.evaluation import evaluate as mechanically_evaluate
from atlas.core.domain.case_condition.exceptions import (
    CaseConditionNotFoundError,
    CaseConditionTerminatedError,
    CrossCaseDecisionError,
)
from atlas.core.domain.case_condition.repository import CaseConditionEventRepository
from atlas.core.domain.case_condition.value_objects import CaseConditionId
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.decision_context.exceptions import (
    DecisionNotFoundError as DecisionContextDecisionNotFoundError,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class CaseConditionContent:
    """A condition's own editable content — plain, unvalidated fields,
    mirroring `DecisionDraftContent`'s identical choice (Sprint 9)."""

    predicate_text: str | None = None
    role: CaseConditionRole | None = None
    authorship: CaseConditionAuthorship | None = None
    structured_kind: CaseConditionStructuredKind | None = None
    threshold_date: datetime | None = None
    threshold_metric: str | None = None
    threshold_operator: ThresholdOperator | None = None
    threshold_value: float | None = None


@dataclass(frozen=True)
class CaseConditionEvaluationResult:
    satisfied: bool
    transitioned: bool
    view: CaseConditionView


class CaseConditionService:
    def __init__(
        self,
        condition_repository: CaseConditionEventRepository,
        case_repository: CaseRepository,
        decision_repository: DecisionRepository,
        clock=_utc_now,
    ) -> None:
        self._conditions = condition_repository
        self._cases = case_repository
        self._decisions = decision_repository
        self._clock = clock

    def create(
        self,
        *,
        case_id: CaseId,
        decision_id: DecisionId | None,
        content: CaseConditionContent,
    ) -> CaseConditionView:
        self._ensure_case_exists(case_id)
        if decision_id is not None:
            self._ensure_decision_in_case(decision_id, case_id)

        event = CaseConditionEvent.revised(
            condition_id=CaseConditionId(),
            case_id=case_id,
            decision_id=decision_id,
            event_id=str(uuid.uuid4()),
            clock=self._clock,
            **_content_kwargs(content),
        )
        self._conditions.add(event)
        return self._require_view(event.condition_id)

    def revise(self, condition_id: CaseConditionId, *, content: CaseConditionContent) -> CaseConditionView:
        latest = self._require_latest(condition_id)
        self._ensure_not_terminal(latest)
        event = CaseConditionEvent.revised(
            condition_id=condition_id,
            case_id=latest.case_id,
            decision_id=latest.decision_id,
            event_id=str(uuid.uuid4()),
            clock=lambda: self._next_recorded_at(latest),
            **_content_kwargs(content),
        )
        self._conditions.add(event)
        return self._require_view(condition_id)

    def evaluate(
        self,
        condition_id: CaseConditionId,
        *,
        evaluated_at: datetime | None = None,
        observed_value: float | None = None,
        human_asserted_satisfied: bool | None = None,
    ) -> CaseConditionEvaluationResult:
        """Mechanically evaluate the condition (via `evaluation.py`), or
        accept a human's own direct assertion (`human_asserted_satisfied`)
        — the only path available for a free-text-only condition, and
        always available to override a mechanical result the investor
        disagrees with (`Investigation-005` Phase 7).

        Only a genuine not-satisfied -> satisfied transition is ever
        persisted as a new `"evaluated_satisfied"` event — a condition
        already satisfied, evaluated true again, writes nothing new
        (the same "only meaningful transitions are ever stored"
        discipline ADR-CC-001 §2 states explicitly for the not-met
        case, generalized here to the repeated-met case; see this
        sprint's own execution report, "Implementation findings").
        """
        latest = self._require_latest(condition_id)
        self._ensure_not_terminal(latest)
        view = self._require_view(condition_id)

        satisfied = (
            human_asserted_satisfied
            if human_asserted_satisfied is not None
            else mechanically_evaluate(
                view, evaluated_at=evaluated_at or self._clock(), observed_value=observed_value
            )
        )

        already_satisfied = latest.event_type == "evaluated_satisfied"
        if not satisfied or already_satisfied:
            return CaseConditionEvaluationResult(satisfied=satisfied, transitioned=False, view=view)

        event = CaseConditionEvent.evaluated_satisfied(
            condition_id=condition_id,
            case_id=latest.case_id,
            decision_id=latest.decision_id,
            observed_value=observed_value,
            event_id=str(uuid.uuid4()),
            clock=lambda: self._next_recorded_at(latest),
        )
        self._conditions.add(event)
        return CaseConditionEvaluationResult(
            satisfied=True, transitioned=True, view=self._require_view(condition_id)
        )

    def retire(self, condition_id: CaseConditionId) -> CaseConditionView:
        """Idempotent: retiring an already-retired condition writes no
        new event. Retiring a superseded condition is rejected — it
        already has a definitive terminal outcome with a named
        replacement; retiring it too would leave two contradictory
        terminal facts."""
        latest = self._require_latest(condition_id)
        if latest.event_type == "retired":
            return self._require_view(condition_id)
        if latest.event_type == "superseded":
            raise CaseConditionTerminatedError(
                f"CaseCondition {condition_id} has already been superseded and cannot be retired"
            )
        event = CaseConditionEvent.retired(
            condition_id=condition_id,
            case_id=latest.case_id,
            decision_id=latest.decision_id,
            event_id=str(uuid.uuid4()),
            clock=lambda: self._next_recorded_at(latest),
        )
        self._conditions.add(event)
        return self._require_view(condition_id)

    def supersede(
        self, condition_id: CaseConditionId, *, superseded_by_condition_id: str | None = None
    ) -> CaseConditionView:
        latest = self._require_latest(condition_id)
        self._ensure_not_terminal(latest)
        event = CaseConditionEvent.superseded(
            condition_id=condition_id,
            case_id=latest.case_id,
            decision_id=latest.decision_id,
            superseded_by_condition_id=superseded_by_condition_id,
            event_id=str(uuid.uuid4()),
            clock=lambda: self._next_recorded_at(latest),
        )
        self._conditions.add(event)
        return self._require_view(condition_id)

    def read(self, condition_id: CaseConditionId) -> CaseConditionView:
        return self._require_view(condition_id)

    def list_events(self, condition_id: CaseConditionId) -> list[CaseConditionEvent]:
        events = self._conditions.list_events(condition_id)
        if not events:
            raise CaseConditionNotFoundError(f"No CaseCondition found with id {condition_id}")
        return events

    def list_for_case(
        self, case_id: CaseId, *, include_terminal: bool = False
    ) -> list[CaseConditionView]:
        latest_events = self._conditions.list_latest_by_case(case_id)
        return self._views_from_latest(latest_events, include_terminal=include_terminal)

    def list_for_decision(
        self, decision_id: DecisionId, *, include_terminal: bool = False
    ) -> list[CaseConditionView]:
        latest_events = self._conditions.list_latest_by_decision(decision_id)
        return self._views_from_latest(latest_events, include_terminal=include_terminal)

    def _views_from_latest(
        self, latest_events: list[CaseConditionEvent], *, include_terminal: bool
    ) -> list[CaseConditionView]:
        selected = [
            event
            for event in latest_events
            if include_terminal or not is_terminal(event.event_type)
        ]
        return [self._require_view(event.condition_id) for event in selected]

    def _ensure_case_exists(self, case_id: CaseId) -> None:
        if self._cases.get(case_id) is None:
            raise CaseNotFoundError(f"No Case found with id {case_id}")

    def _ensure_decision_in_case(self, decision_id: DecisionId, case_id: CaseId) -> None:
        """`atlas.core.domain.decision_context.exceptions
        .DecisionNotFoundError` is reused directly for "decision_id
        does not exist" — it already carries exactly this meaning
        ("raised when ... captured against a Decision that does not
        exist ... maps to 404") and already has an app-wide handler
        registered, so no new exception type or handler is needed."""
        decision = self._decisions.get(decision_id)
        if decision is None:
            raise DecisionContextDecisionNotFoundError(f"No Decision found with id {decision_id}")
        if decision.case_id != case_id:
            raise CrossCaseDecisionError(
                f"Decision {decision_id} belongs to Case {decision.case_id}, not {case_id}"
            )

    def _require_latest(self, condition_id: CaseConditionId) -> CaseConditionEvent:
        latest = self._conditions.get_latest_event(condition_id)
        if latest is None:
            raise CaseConditionNotFoundError(f"No CaseCondition found with id {condition_id}")
        return latest

    def _require_view(self, condition_id: CaseConditionId) -> CaseConditionView:
        events = self._conditions.list_events(condition_id)
        view = reconstruct_current_state(events)
        if view is None:
            raise CaseConditionNotFoundError(f"No CaseCondition found with id {condition_id}")
        return view

    @staticmethod
    def _ensure_not_terminal(latest: CaseConditionEvent) -> None:
        if is_terminal(latest.event_type):
            raise CaseConditionTerminatedError(
                f"CaseCondition {latest.condition_id} has already been "
                f"{latest.event_type} and can no longer be changed"
            )

    def _next_recorded_at(self, previous: CaseConditionEvent) -> datetime:
        now = self._clock()
        return max(now, previous.recorded_at + timedelta(microseconds=1))


def _content_kwargs(content: CaseConditionContent) -> dict:
    return {
        "predicate_text": content.predicate_text,
        "role": content.role,
        "authorship": content.authorship,
        "structured_kind": content.structured_kind,
        "threshold_date": content.threshold_date,
        "threshold_metric": content.threshold_metric,
        "threshold_operator": content.threshold_operator,
        "threshold_value": content.threshold_value,
    }
