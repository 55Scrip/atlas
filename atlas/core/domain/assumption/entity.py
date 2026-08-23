"""The Assumption aggregate root (ADR-AS-001).

`Assumption` has no separate root table or root entity of its own —
directly mirroring `CaseCondition` (`atlas.core.domain.case_condition
.entity`, Sprint 10), per ADR-AS-001 §10's own explicit instruction:
"Assumption's lifecycle MUST use the identical event-stream pattern
established for CaseCondition." One physical stream of
`AssumptionEvent` rows *is* the aggregate; "the assumption" as a
queryable thing is the derived projection this module's own
`reconstruct_current_state` computes over that stream.

**Decision-anchored, not Case-scoped.** Unlike `CaseCondition`
(Case-scoped identity, optional `decision_id`), ADR-AS-001 §1 adopts
Assumption as "a stable, **Decision-anchored** identity (with `case_id`
reachable transitively...)" — the identical shape `DecisionContext`
already has (no `case_id` field of its own; `Case` is reached only by
joining through `decision_id`). `decision_id` is therefore *required*
here, and `case_id` is a denormalized convenience value derived from
the referenced `Decision` at creation time, carried on every event row
for query efficiency (the same repeated-field-per-row discipline
`DecisionDraftEvent`/`CaseConditionEvent` already use for their own
identity fields) — never an independently caller-supplied identity of
its own.

**Event types** (ADR-AS-001 Invariants, verbatim): `revised`,
`challenged`, `retired`, `superseded` — note this is a *different* set
of names than `CaseConditionEvent`'s own four types
(`revised`/`evaluated_satisfied`/`superseded`/`retired`), even though
both follow the identical structural pattern: one non-terminal
"something happened to the content's own truth-relationship" event
(`evaluated_satisfied` for CaseCondition, `challenged` here) alongside
the shared `revised`/`superseded`/`retired`.

**Terminal vs. non-terminal** — the same implementation-level
resolution already applied to `CaseCondition` (Sprint 10) and
`DecisionDraft` (Sprint 9): `superseded`/`retired` are terminal;
`revised`/`challenged` are not (an investor may revise an assumption
again after it was challenged — reaffirming or updating it in light of
new evidence is a legitimate, undesignated-against case).

**"Challenged" carries a degree, not a second event type**, per
ADR-AS-001 §9: "'Challenged' and 'Invalidated' collapse toward one
event type, differentiated by degree, not a truth verdict." `severity`
(`"challenged" | "invalidated"`) is that degree field.

**Attach/detach are `revised` events, not new event types** — see
`AssumptionService.attach_case_condition`/`detach_case_condition`'s own
docstring for why: ADR-AS-001 §8's "loose, optional cross-reference"
between `Assumption` and `CaseCondition` is modeled as ordinary content
(`linked_case_condition_ids`) carried on the same full-snapshot
`revised` event every other content edit already uses, not a fifth
event type ADR-AS-001's own Invariants never names.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from atlas.core.domain.assumption.value_objects import AssumptionId
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.value_objects import DecisionId

AssumptionEventType = Literal["revised", "challenged", "retired", "superseded"]
AssumptionAuthorship = Literal["atlas", "user", "mixed"]
AssumptionChallengeSeverity = Literal["challenged", "invalidated"]

_TERMINAL_EVENT_TYPES: frozenset[AssumptionEventType] = frozenset({"superseded", "retired"})

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def is_terminal(event_type: AssumptionEventType) -> bool:
    return event_type in _TERMINAL_EVENT_TYPES


@dataclass(frozen=True)
class AssumptionEvent:
    """One append-only row in a single assumption's own lifecycle.

    A `"revised"` event carries the complete content snapshot as of
    that edit — `statement`, `authorship`, and `linked_case_condition_ids`
    — never a delta, matching `CaseConditionEvent`'s own identical
    discipline. `"challenged"` carries `evidence_id`/`note`/`severity`
    only. `"retired"` carries no content. `"superseded"` carries only
    `superseded_by_assumption_id`.
    """

    id: str
    assumption_id: AssumptionId
    decision_id: DecisionId
    case_id: CaseId
    event_type: AssumptionEventType
    recorded_at: datetime
    statement: str | None = None
    authorship: AssumptionAuthorship | None = None
    linked_case_condition_ids: tuple[str, ...] = field(default_factory=tuple)
    evidence_id: str | None = None
    note: str | None = None
    severity: AssumptionChallengeSeverity | None = None
    superseded_by_assumption_id: str | None = None

    @classmethod
    def revised(
        cls,
        *,
        assumption_id: AssumptionId,
        decision_id: DecisionId,
        case_id: CaseId,
        statement: str | None = None,
        authorship: AssumptionAuthorship | None = None,
        linked_case_condition_ids: tuple[str, ...] = (),
        event_id: str,
        clock: _Clock = _utc_now,
    ) -> AssumptionEvent:
        """The event both `AssumptionService.create()` (the first
        `"revised"` event for a fresh `assumption_id`) and
        `AssumptionService.revise()`/`attach_case_condition()`/
        `detach_case_condition()` (every subsequent one) append."""
        return cls(
            id=event_id,
            assumption_id=assumption_id,
            decision_id=decision_id,
            case_id=case_id,
            event_type="revised",
            recorded_at=clock(),
            statement=statement,
            authorship=authorship,
            linked_case_condition_ids=tuple(linked_case_condition_ids),
        )

    @classmethod
    def challenged(
        cls,
        *,
        assumption_id: AssumptionId,
        decision_id: DecisionId,
        case_id: CaseId,
        evidence_id: str | None = None,
        note: str | None = None,
        severity: AssumptionChallengeSeverity = "challenged",
        event_id: str,
        clock: _Clock = _utc_now,
    ) -> AssumptionEvent:
        return cls(
            id=event_id,
            assumption_id=assumption_id,
            decision_id=decision_id,
            case_id=case_id,
            event_type="challenged",
            recorded_at=clock(),
            evidence_id=evidence_id,
            note=note,
            severity=severity,
        )

    @classmethod
    def superseded(
        cls,
        *,
        assumption_id: AssumptionId,
        decision_id: DecisionId,
        case_id: CaseId,
        superseded_by_assumption_id: str | None = None,
        event_id: str,
        clock: _Clock = _utc_now,
    ) -> AssumptionEvent:
        return cls(
            id=event_id,
            assumption_id=assumption_id,
            decision_id=decision_id,
            case_id=case_id,
            event_type="superseded",
            recorded_at=clock(),
            superseded_by_assumption_id=superseded_by_assumption_id,
        )

    @classmethod
    def retired(
        cls,
        *,
        assumption_id: AssumptionId,
        decision_id: DecisionId,
        case_id: CaseId,
        event_id: str,
        clock: _Clock = _utc_now,
    ) -> AssumptionEvent:
        return cls(
            id=event_id,
            assumption_id=assumption_id,
            decision_id=decision_id,
            case_id=case_id,
            event_type="retired",
            recorded_at=clock(),
        )


AssumptionStatus = Literal["supported", "challenged", "invalidated", "superseded", "retired"]

_STATUS_BY_EVENT_TYPE_AND_SEVERITY: dict[tuple[AssumptionEventType, AssumptionChallengeSeverity | None], AssumptionStatus] = {
    ("revised", None): "supported",
    ("challenged", "challenged"): "challenged",
    ("challenged", "invalidated"): "invalidated",
    ("superseded", None): "superseded",
    ("retired", None): "retired",
}


@dataclass(frozen=True)
class AssumptionView:
    """The derived "current state" of one assumption — never itself
    persisted, always recomputed from its own event stream by
    `reconstruct_current_state`."""

    assumption_id: AssumptionId
    decision_id: DecisionId
    case_id: CaseId
    status: AssumptionStatus
    statement: str | None
    authorship: AssumptionAuthorship | None
    linked_case_condition_ids: tuple[str, ...]
    last_challenge_evidence_id: str | None
    last_challenge_note: str | None
    superseded_by_assumption_id: str | None
    latest_event_id: str
    created_at: datetime
    updated_at: datetime

    @property
    def is_active(self) -> bool:
        """True while the assumption may still receive further events —
        i.e., its latest event is not terminal (`superseded`/`retired`)."""
        return self.status in ("supported", "challenged", "invalidated")


def reconstruct_current_state(events: list[AssumptionEvent]) -> AssumptionView | None:
    """Derive an assumption's current state from its full, oldest-first
    event history. Returns `None` if `events` is empty (the assumption
    never existed).

    Status and `updated_at` come from the latest event, whatever its
    type. `statement`/`authorship`/`linked_case_condition_ids` come
    from the latest `"revised"` event specifically —
    `"challenged"`/`"superseded"`/`"retired"` events carry no content of
    their own, so a challenged, superseded, or retired assumption's
    view still shows the statement it was last defined by.
    """
    if not events:
        return None

    latest = events[-1]
    latest_revision = next(
        (event for event in reversed(events) if event.event_type == "revised"),
        None,
    )
    # `create()` always writes a "revised" event first, so an
    # assumption with any events at all always has at least one
    # revision to draw content from.
    assert latest_revision is not None

    latest_challenge = next(
        (event for event in reversed(events) if event.event_type == "challenged"),
        None,
    )

    first = events[0]

    severity = latest.severity if latest.event_type == "challenged" else None
    status = _STATUS_BY_EVENT_TYPE_AND_SEVERITY[(latest.event_type, severity)]

    return AssumptionView(
        assumption_id=latest.assumption_id,
        decision_id=latest.decision_id,
        case_id=latest.case_id,
        status=status,
        statement=latest_revision.statement,
        authorship=latest_revision.authorship,
        linked_case_condition_ids=latest_revision.linked_case_condition_ids,
        last_challenge_evidence_id=(
            latest_challenge.evidence_id if latest_challenge is not None else None
        ),
        last_challenge_note=latest_challenge.note if latest_challenge is not None else None,
        superseded_by_assumption_id=latest.superseded_by_assumption_id,
        latest_event_id=latest.id,
        created_at=first.recorded_at,
        updated_at=latest.recorded_at,
    )
