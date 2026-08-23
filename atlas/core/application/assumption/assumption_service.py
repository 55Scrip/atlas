"""`AssumptionService` — the application service for Assumption
(ADR-AS-001).

Method names follow Sprint 11's own brief: `create` (CreateAssumption),
`revise` (ReviseAssumption), `retire` (RetireAssumption),
`attach_case_condition`/`detach_case_condition`
(AttachCaseCondition/DetachCaseCondition), `list_for_decision`/
`list_for_case` (ListAssumptions), `read` (ReadCurrentState). Two
methods beyond that list, `challenge` and `supersede`, are added — see
this sprint's own execution report, "Implementation findings": ADR-AS-001's
own Invariants name exactly four required event types (`revised`,
`challenged`, `retired`, `superseded`), and no method in Sprint 11's
own brief can ever produce the latter two. This is the same class of
gap Sprint 10 already found once for `CaseCondition` (a missing
`supersede` method) and resolved the same way: a direct, mechanical
completion, not a new capability.

**`attach_case_condition`/`detach_case_condition` append a `"revised"`
event, not a new event type.** ADR-AS-001 §8's "loose, optional
cross-reference" between `Assumption` and `CaseCondition` is modeled as
ordinary content (`linked_case_condition_ids`) carried on the same
full-snapshot `revised` event every other content edit already uses —
these two methods read the assumption's own current `statement`/
`authorship` first and carry them forward unchanged, only modifying
the linked set, so the caller never has to resupply unrelated content
just to attach or detach one cross-reference.

Ordering safety follows `security_confirmation`/`decision_draft`/
`case_condition`'s own `_next_recorded_at` idiom verbatim.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from atlas.core.domain.assumption.entity import (
    AssumptionAuthorship,
    AssumptionChallengeSeverity,
    AssumptionEvent,
    AssumptionView,
    is_terminal,
    reconstruct_current_state,
)
from atlas.core.domain.assumption.exceptions import (
    AssumptionNotFoundError,
    AssumptionTerminatedError,
    CaseConditionNotFoundForLinkError,
)
from atlas.core.domain.assumption.repository import AssumptionEventRepository
from atlas.core.domain.assumption.value_objects import AssumptionId
from atlas.core.domain.case.value_objects import CaseId
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
class AssumptionContent:
    """An assumption's own editable content — plain, unvalidated
    fields, mirroring `CaseConditionContent`'s identical choice."""

    statement: str | None = None
    authorship: AssumptionAuthorship | None = None


class AssumptionService:
    def __init__(
        self,
        assumption_repository: AssumptionEventRepository,
        decision_repository: DecisionRepository,
        case_condition_repository: CaseConditionEventRepository,
        clock=_utc_now,
    ) -> None:
        self._assumptions = assumption_repository
        self._decisions = decision_repository
        self._case_conditions = case_condition_repository
        self._clock = clock

    def create(
        self, *, decision_id: DecisionId, content: AssumptionContent
    ) -> AssumptionView:
        case_id = self._case_id_for_decision(decision_id)
        event = AssumptionEvent.revised(
            assumption_id=AssumptionId(),
            decision_id=decision_id,
            case_id=case_id,
            statement=content.statement,
            authorship=content.authorship,
            event_id=str(uuid.uuid4()),
            clock=self._clock,
        )
        self._assumptions.add(event)
        return self._require_view(event.assumption_id)

    def revise(
        self, assumption_id: AssumptionId, *, content: AssumptionContent
    ) -> AssumptionView:
        latest = self._require_latest(assumption_id)
        self._ensure_not_terminal(latest)
        current_view = self._require_view(assumption_id)
        event = AssumptionEvent.revised(
            assumption_id=assumption_id,
            decision_id=latest.decision_id,
            case_id=latest.case_id,
            statement=content.statement,
            authorship=content.authorship,
            linked_case_condition_ids=current_view.linked_case_condition_ids,
            event_id=str(uuid.uuid4()),
            clock=lambda: self._next_recorded_at(latest),
        )
        self._assumptions.add(event)
        return self._require_view(assumption_id)

    def challenge(
        self,
        assumption_id: AssumptionId,
        *,
        evidence_id: str | None = None,
        note: str | None = None,
        severity: AssumptionChallengeSeverity = "challenged",
    ) -> AssumptionView:
        """Evidence supports or challenges an Assumption's underlying
        claim (ADR-AS-001 §4) — this is the "challenges" direction.
        Non-terminal: a challenged assumption may still be revised,
        challenged again, retired, or superseded."""
        latest = self._require_latest(assumption_id)
        self._ensure_not_terminal(latest)
        event = AssumptionEvent.challenged(
            assumption_id=assumption_id,
            decision_id=latest.decision_id,
            case_id=latest.case_id,
            evidence_id=evidence_id,
            note=note,
            severity=severity,
            event_id=str(uuid.uuid4()),
            clock=lambda: self._next_recorded_at(latest),
        )
        self._assumptions.add(event)
        return self._require_view(assumption_id)

    def attach_case_condition(
        self, assumption_id: AssumptionId, case_condition_id: CaseConditionId
    ) -> AssumptionView:
        """Idempotent: attaching an already-linked CaseCondition writes
        no new event."""
        latest = self._require_latest(assumption_id)
        self._ensure_not_terminal(latest)
        self._ensure_case_condition_exists(case_condition_id)
        current_view = self._require_view(assumption_id)

        if str(case_condition_id) in current_view.linked_case_condition_ids:
            return current_view

        updated_links = current_view.linked_case_condition_ids + (str(case_condition_id),)
        event = AssumptionEvent.revised(
            assumption_id=assumption_id,
            decision_id=latest.decision_id,
            case_id=latest.case_id,
            statement=current_view.statement,
            authorship=current_view.authorship,
            linked_case_condition_ids=updated_links,
            event_id=str(uuid.uuid4()),
            clock=lambda: self._next_recorded_at(latest),
        )
        self._assumptions.add(event)
        return self._require_view(assumption_id)

    def detach_case_condition(
        self, assumption_id: AssumptionId, case_condition_id: CaseConditionId
    ) -> AssumptionView:
        """Idempotent: detaching a CaseCondition that is not currently
        linked writes no new event."""
        latest = self._require_latest(assumption_id)
        self._ensure_not_terminal(latest)
        current_view = self._require_view(assumption_id)

        if str(case_condition_id) not in current_view.linked_case_condition_ids:
            return current_view

        updated_links = tuple(
            linked_id
            for linked_id in current_view.linked_case_condition_ids
            if linked_id != str(case_condition_id)
        )
        event = AssumptionEvent.revised(
            assumption_id=assumption_id,
            decision_id=latest.decision_id,
            case_id=latest.case_id,
            statement=current_view.statement,
            authorship=current_view.authorship,
            linked_case_condition_ids=updated_links,
            event_id=str(uuid.uuid4()),
            clock=lambda: self._next_recorded_at(latest),
        )
        self._assumptions.add(event)
        return self._require_view(assumption_id)

    def retire(self, assumption_id: AssumptionId) -> AssumptionView:
        """Idempotent: retiring an already-retired assumption writes no
        new event. Retiring a superseded assumption is rejected."""
        latest = self._require_latest(assumption_id)
        if latest.event_type == "retired":
            return self._require_view(assumption_id)
        if latest.event_type == "superseded":
            raise AssumptionTerminatedError(
                f"Assumption {assumption_id} has already been superseded and cannot be retired"
            )
        event = AssumptionEvent.retired(
            assumption_id=assumption_id,
            decision_id=latest.decision_id,
            case_id=latest.case_id,
            event_id=str(uuid.uuid4()),
            clock=lambda: self._next_recorded_at(latest),
        )
        self._assumptions.add(event)
        return self._require_view(assumption_id)

    def supersede(
        self, assumption_id: AssumptionId, *, superseded_by_assumption_id: str | None = None
    ) -> AssumptionView:
        latest = self._require_latest(assumption_id)
        self._ensure_not_terminal(latest)
        event = AssumptionEvent.superseded(
            assumption_id=assumption_id,
            decision_id=latest.decision_id,
            case_id=latest.case_id,
            superseded_by_assumption_id=superseded_by_assumption_id,
            event_id=str(uuid.uuid4()),
            clock=lambda: self._next_recorded_at(latest),
        )
        self._assumptions.add(event)
        return self._require_view(assumption_id)

    def read(self, assumption_id: AssumptionId) -> AssumptionView:
        return self._require_view(assumption_id)

    def list_events(self, assumption_id: AssumptionId) -> list[AssumptionEvent]:
        events = self._assumptions.list_events(assumption_id)
        if not events:
            raise AssumptionNotFoundError(f"No Assumption found with id {assumption_id}")
        return events

    def list_for_decision(
        self, decision_id: DecisionId, *, include_terminal: bool = False
    ) -> list[AssumptionView]:
        latest_events = self._assumptions.list_latest_by_decision(decision_id)
        return self._views_from_latest(latest_events, include_terminal=include_terminal)

    def list_for_case(
        self, case_id: CaseId, *, include_terminal: bool = False
    ) -> list[AssumptionView]:
        latest_events = self._assumptions.list_latest_by_case(case_id)
        return self._views_from_latest(latest_events, include_terminal=include_terminal)

    def _views_from_latest(
        self, latest_events: list[AssumptionEvent], *, include_terminal: bool
    ) -> list[AssumptionView]:
        selected = [
            event
            for event in latest_events
            if include_terminal or not is_terminal(event.event_type)
        ]
        return [self._require_view(event.assumption_id) for event in selected]

    def _case_id_for_decision(self, decision_id: DecisionId) -> CaseId:
        """`atlas.core.domain.decision_context.exceptions
        .DecisionNotFoundError` is reused directly — it already has an
        app-wide handler, and already carries exactly this meaning."""
        decision = self._decisions.get(decision_id)
        if decision is None:
            raise DecisionContextDecisionNotFoundError(f"No Decision found with id {decision_id}")
        return decision.case_id

    def _ensure_case_condition_exists(self, case_condition_id: CaseConditionId) -> None:
        if self._case_conditions.get_latest_event(case_condition_id) is None:
            raise CaseConditionNotFoundForLinkError(
                f"No CaseCondition found with id {case_condition_id}"
            )

    def _require_latest(self, assumption_id: AssumptionId) -> AssumptionEvent:
        latest = self._assumptions.get_latest_event(assumption_id)
        if latest is None:
            raise AssumptionNotFoundError(f"No Assumption found with id {assumption_id}")
        return latest

    def _require_view(self, assumption_id: AssumptionId) -> AssumptionView:
        events = self._assumptions.list_events(assumption_id)
        view = reconstruct_current_state(events)
        if view is None:
            raise AssumptionNotFoundError(f"No Assumption found with id {assumption_id}")
        return view

    @staticmethod
    def _ensure_not_terminal(latest: AssumptionEvent) -> None:
        if is_terminal(latest.event_type):
            raise AssumptionTerminatedError(
                f"Assumption {latest.assumption_id} has already been "
                f"{latest.event_type} and can no longer be changed"
            )

    def _next_recorded_at(self, previous: AssumptionEvent) -> datetime:
        now = self._clock()
        return max(now, previous.recorded_at + timedelta(microseconds=1))
