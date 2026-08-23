"""The CaseCondition aggregate root (ADR-CC-001).

`CaseCondition` has no separate root table or root entity of its own —
directly mirroring `DecisionDraft` (`atlas.core.domain.decision_draft
.entity`, Sprint 9), itself modeled on `SecurityConfirmationEvent`. One
physical stream of `CaseConditionEvent` rows *is* the aggregate; "the
condition" as a queryable thing is the derived projection this
module's own `reconstruct_current_state` computes over that stream —
never a separately, directly edited row. See ADR-CC-001 §2.

**Event types** (ADR-CC-001 §2, verbatim): `revised`,
`evaluated_satisfied`, `superseded`, `retired`.

**Terminal vs. non-terminal — an implementation-level resolution, not
part of the ADR's own literal text.** ADR-CC-001 does not spell out
which of the four event types close a condition's own stream to
further events. This module treats `superseded` and `retired` as
terminal (no further event may ever follow either — both describe the
condition's own watching having ended, with or without a replacement),
and `revised`/`evaluated_satisfied` as non-terminal (a condition may be
revised again after being satisfied — an investor reviewing a
triggered condition and choosing to keep watching is a legitimate,
undesigned-against case; nothing in the ADR forecloses it). This
mirrors `DecisionDraft`'s own identical terminal/non-terminal split
(`abandoned`/`committed` terminal, `revised` not) and is disclosed as
an implementation finding in this sprint's own execution report, the
same discipline `DecisionDraft-Implementation-Design.md` §3.6 already
applied to "abandon vs. delete."

**"Superseded" carries an optional forward reference.** Modeled
directly on `DecisionDraftEvent.committed`'s own `committed_decision_id`
back-reference: a `superseded` event may carry
`superseded_by_condition_id`, naming the newer `CaseCondition` that
replaces this one — the concrete difference from `retired` ("stop
watching, no replacement," per `Investigation-006` Phase 10, carried
into this ADR's own Decision §2 as a distinct event type).
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.case_condition.value_objects import CaseConditionId
from atlas.core.domain.decision.value_objects import DecisionId

CaseConditionEventType = Literal["revised", "evaluated_satisfied", "superseded", "retired"]
CaseConditionRole = Literal["monitoring", "invalidation"]
CaseConditionAuthorship = Literal["atlas", "user", "mixed"]
CaseConditionStructuredKind = Literal["date", "threshold"]
ThresholdOperator = Literal["<", "<=", ">", ">=", "==", "!="]

_TERMINAL_EVENT_TYPES: frozenset[CaseConditionEventType] = frozenset({"superseded", "retired"})

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def is_terminal(event_type: CaseConditionEventType) -> bool:
    return event_type in _TERMINAL_EVENT_TYPES


@dataclass(frozen=True)
class CaseConditionEvent:
    """One append-only row in a single condition's own lifecycle.

    A `"revised"` event carries the complete condition-content snapshot
    as of that edit — never a delta — matching `DecisionDraftEvent`'s
    own fully-self-describing-row discipline. `"evaluated_satisfied"`
    carries no content fields of its own beyond the evaluation result
    (`observed_value`, when the transition was threshold-triggered).
    `"superseded"`/`"retired"` carry no content fields either;
    `"superseded"` additionally carries `superseded_by_condition_id`.

    Events for one `condition_id` are never UPDATEd or DELETEd;
    "current state" is always derived by reading the full event history
    (see `reconstruct_current_state`), never by mutating a stored row.
    """

    id: str
    condition_id: CaseConditionId
    case_id: CaseId
    decision_id: DecisionId | None
    event_type: CaseConditionEventType
    recorded_at: datetime
    predicate_text: str | None = None
    role: CaseConditionRole | None = None
    authorship: CaseConditionAuthorship | None = None
    structured_kind: CaseConditionStructuredKind | None = None
    threshold_date: datetime | None = None
    threshold_metric: str | None = None
    threshold_operator: ThresholdOperator | None = None
    threshold_value: float | None = None
    observed_value: float | None = None
    superseded_by_condition_id: str | None = None

    @classmethod
    def revised(
        cls,
        *,
        condition_id: CaseConditionId,
        case_id: CaseId,
        decision_id: DecisionId | None,
        predicate_text: str | None = None,
        role: CaseConditionRole | None = None,
        authorship: CaseConditionAuthorship | None = None,
        structured_kind: CaseConditionStructuredKind | None = None,
        threshold_date: datetime | None = None,
        threshold_metric: str | None = None,
        threshold_operator: ThresholdOperator | None = None,
        threshold_value: float | None = None,
        event_id: str,
        clock: _Clock = _utc_now,
    ) -> CaseConditionEvent:
        """The event both `CaseConditionService.create()` (the first
        `"revised"` event for a fresh `condition_id`) and
        `CaseConditionService.revise()` (every subsequent one) append.
        """
        return cls(
            id=event_id,
            condition_id=condition_id,
            case_id=case_id,
            decision_id=decision_id,
            event_type="revised",
            recorded_at=clock(),
            predicate_text=predicate_text,
            role=role,
            authorship=authorship,
            structured_kind=structured_kind,
            threshold_date=threshold_date,
            threshold_metric=threshold_metric,
            threshold_operator=threshold_operator,
            threshold_value=threshold_value,
        )

    @classmethod
    def evaluated_satisfied(
        cls,
        *,
        condition_id: CaseConditionId,
        case_id: CaseId,
        decision_id: DecisionId | None,
        observed_value: float | None = None,
        event_id: str,
        clock: _Clock = _utc_now,
    ) -> CaseConditionEvent:
        return cls(
            id=event_id,
            condition_id=condition_id,
            case_id=case_id,
            decision_id=decision_id,
            event_type="evaluated_satisfied",
            recorded_at=clock(),
            observed_value=observed_value,
        )

    @classmethod
    def superseded(
        cls,
        *,
        condition_id: CaseConditionId,
        case_id: CaseId,
        decision_id: DecisionId | None,
        superseded_by_condition_id: str | None = None,
        event_id: str,
        clock: _Clock = _utc_now,
    ) -> CaseConditionEvent:
        return cls(
            id=event_id,
            condition_id=condition_id,
            case_id=case_id,
            decision_id=decision_id,
            event_type="superseded",
            recorded_at=clock(),
            superseded_by_condition_id=superseded_by_condition_id,
        )

    @classmethod
    def retired(
        cls,
        *,
        condition_id: CaseConditionId,
        case_id: CaseId,
        decision_id: DecisionId | None,
        event_id: str,
        clock: _Clock = _utc_now,
    ) -> CaseConditionEvent:
        return cls(
            id=event_id,
            condition_id=condition_id,
            case_id=case_id,
            decision_id=decision_id,
            event_type="retired",
            recorded_at=clock(),
        )


CaseConditionStatus = Literal["active", "satisfied", "superseded", "retired"]

_STATUS_BY_EVENT_TYPE: dict[CaseConditionEventType, CaseConditionStatus] = {
    "revised": "active",
    "evaluated_satisfied": "satisfied",
    "superseded": "superseded",
    "retired": "retired",
}


@dataclass(frozen=True)
class CaseConditionView:
    """The derived "current state" of one condition — never itself
    persisted, always recomputed from its own event stream by
    `reconstruct_current_state`.
    """

    condition_id: CaseConditionId
    case_id: CaseId
    decision_id: DecisionId | None
    status: CaseConditionStatus
    predicate_text: str | None
    role: CaseConditionRole | None
    authorship: CaseConditionAuthorship | None
    structured_kind: CaseConditionStructuredKind | None
    threshold_date: datetime | None
    threshold_metric: str | None
    threshold_operator: ThresholdOperator | None
    threshold_value: float | None
    last_observed_value: float | None
    superseded_by_condition_id: str | None
    latest_event_id: str
    created_at: datetime
    updated_at: datetime

    @property
    def is_active(self) -> bool:
        """True while the condition may still receive further events —
        i.e., its latest event is not terminal (`superseded`/`retired`)."""
        return self.status in ("active", "satisfied")


def reconstruct_current_state(events: list[CaseConditionEvent]) -> CaseConditionView | None:
    """Derive a condition's current state from its full, oldest-first
    event history. Returns `None` if `events` is empty (the condition
    never existed).

    Status and `updated_at` come from the latest event, whatever its
    type. Predicate/role/authorship/structured fields come from the
    latest `"revised"` event specifically — `"evaluated_satisfied"`/
    `"superseded"`/`"retired"` events carry no content of their own, so
    a satisfied, superseded, or retired condition's view still shows
    the predicate it was last defined by, not a blanked-out row.
    """
    if not events:
        return None

    latest = events[-1]
    latest_revision = next(
        (event for event in reversed(events) if event.event_type == "revised"),
        None,
    )
    # `create()` always writes a "revised" event first, so a condition
    # with any events at all always has at least one revision to draw
    # content from.
    assert latest_revision is not None

    latest_evaluation = next(
        (event for event in reversed(events) if event.event_type == "evaluated_satisfied"),
        None,
    )

    first = events[0]

    return CaseConditionView(
        condition_id=latest.condition_id,
        case_id=latest.case_id,
        decision_id=latest.decision_id,
        status=_STATUS_BY_EVENT_TYPE[latest.event_type],
        predicate_text=latest_revision.predicate_text,
        role=latest_revision.role,
        authorship=latest_revision.authorship,
        structured_kind=latest_revision.structured_kind,
        threshold_date=latest_revision.threshold_date,
        threshold_metric=latest_revision.threshold_metric,
        threshold_operator=latest_revision.threshold_operator,
        threshold_value=latest_revision.threshold_value,
        last_observed_value=(
            latest_evaluation.observed_value if latest_evaluation is not None else None
        ),
        superseded_by_condition_id=latest.superseded_by_condition_id,
        latest_event_id=latest.id,
        created_at=first.recorded_at,
        updated_at=latest.recorded_at,
    )
