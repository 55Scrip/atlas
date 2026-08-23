"""The DecisionDraft aggregate root (ADR-DD-001).

`DecisionDraft` has no separate root table or root entity of its own —
directly mirroring `atlas.alpha.security_confirmation.models
.SecurityConfirmationEvent`, which has no separate root table for
`ConfirmedSecuritySelection` either. One physical stream of
`DecisionDraftEvent` rows *is* the aggregate; "the draft" as a
queryable thing is the derived projection this module's own
`reconstruct_current_state` computes over that stream — never a
separately, directly edited row. See
`DecisionDraft-Implementation-Design.md` §3.1.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.value_objects import UserId
from atlas.core.domain.decision_draft.value_objects import DraftId

DecisionDraftEventType = Literal["revised", "abandoned", "committed"]

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class DecisionDraftEvent:
    """One append-only row in a single draft's own lifecycle.

    A `"revised"` event carries the complete draft-content snapshot as
    of that edit — never a delta — matching
    `SecurityConfirmationEvent`'s own fully-self-describing-row
    discipline. `"abandoned"` and `"committed"` events carry no content
    fields (all `None`); `"committed"` events additionally carry
    `committed_decision_id`, the one optional-additive back-reference
    ADR-DD-001 §5 requires.

    Events for one `draft_id` are never UPDATEd or DELETEd; "current
    state" is always derived by reading the full event history (see
    `reconstruct_current_state`), never by mutating a stored row.
    """

    id: str
    draft_id: DraftId
    case_id: CaseId
    user_id: UserId
    event_type: DecisionDraftEventType
    recorded_at: datetime
    decision_type: str | None = None
    subject: str | None = None
    reason: str | None = None
    confidence: int | None = None
    decided_at: datetime | None = None
    source: str | None = None
    situation: str | None = None
    portfolio_relevance: str | None = None
    capital_considerations: str | None = None
    alternatives_considered: tuple[str, ...] = field(default_factory=tuple)
    uncertainties: tuple[str, ...] = field(default_factory=tuple)
    committed_decision_id: str | None = None

    @classmethod
    def revised(
        cls,
        *,
        draft_id: DraftId,
        case_id: CaseId,
        user_id: UserId,
        decision_type: str | None = None,
        subject: str | None = None,
        reason: str | None = None,
        confidence: int | None = None,
        decided_at: datetime | None = None,
        source: str | None = None,
        situation: str | None = None,
        portfolio_relevance: str | None = None,
        capital_considerations: str | None = None,
        alternatives_considered: tuple[str, ...] = (),
        uncertainties: tuple[str, ...] = (),
        event_id: str,
        clock: _Clock = _utc_now,
    ) -> DecisionDraftEvent:
        """The event both `DecisionDraftService.create()` (the first
        `"revised"` event for a fresh `draft_id`) and
        `DecisionDraftService.revise()` (every subsequent one) append.
        """
        return cls(
            id=event_id,
            draft_id=draft_id,
            case_id=case_id,
            user_id=user_id,
            event_type="revised",
            recorded_at=clock(),
            decision_type=decision_type,
            subject=subject,
            reason=reason,
            confidence=confidence,
            decided_at=decided_at,
            source=source,
            situation=situation,
            portfolio_relevance=portfolio_relevance,
            capital_considerations=capital_considerations,
            alternatives_considered=tuple(alternatives_considered),
            uncertainties=tuple(uncertainties),
        )

    @classmethod
    def abandoned(
        cls,
        *,
        draft_id: DraftId,
        case_id: CaseId,
        user_id: UserId,
        event_id: str,
        clock: _Clock = _utc_now,
    ) -> DecisionDraftEvent:
        return cls(
            id=event_id,
            draft_id=draft_id,
            case_id=case_id,
            user_id=user_id,
            event_type="abandoned",
            recorded_at=clock(),
        )

    @classmethod
    def committed(
        cls,
        *,
        draft_id: DraftId,
        case_id: CaseId,
        user_id: UserId,
        committed_decision_id: str,
        event_id: str,
        clock: _Clock = _utc_now,
    ) -> DecisionDraftEvent:
        return cls(
            id=event_id,
            draft_id=draft_id,
            case_id=case_id,
            user_id=user_id,
            event_type="committed",
            recorded_at=clock(),
            committed_decision_id=committed_decision_id,
        )


DecisionDraftStatus = Literal["active", "abandoned", "committed"]


@dataclass(frozen=True)
class DecisionDraftView:
    """The derived "current state" of one draft — never itself
    persisted, always recomputed from its own event stream by
    `reconstruct_current_state`.
    """

    draft_id: DraftId
    case_id: CaseId
    user_id: UserId
    status: DecisionDraftStatus
    decision_type: str | None
    subject: str | None
    reason: str | None
    confidence: int | None
    decided_at: datetime | None
    source: str | None
    situation: str | None
    portfolio_relevance: str | None
    capital_considerations: str | None
    alternatives_considered: tuple[str, ...]
    uncertainties: tuple[str, ...]
    committed_decision_id: str | None
    latest_event_id: str
    created_at: datetime
    updated_at: datetime


_STATUS_BY_EVENT_TYPE: dict[DecisionDraftEventType, DecisionDraftStatus] = {
    "revised": "active",
    "abandoned": "abandoned",
    "committed": "committed",
}


def reconstruct_current_state(events: list[DecisionDraftEvent]) -> DecisionDraftView | None:
    """Derive a draft's current state from its full, oldest-first event
    history. Returns `None` if `events` is empty (the draft never
    existed).

    Status and `updated_at` come from the latest event, whatever its
    type. Content fields come from the latest `"revised"` event
    specifically — `"abandoned"`/`"committed"` events carry no content
    of their own (see `DecisionDraftEvent`'s own docstring), so an
    abandoned or committed draft's view still shows the content it last
    held, not a blanked-out row.
    """
    if not events:
        return None

    latest = events[-1]
    latest_revision = next(
        (event for event in reversed(events) if event.event_type == "revised"),
        None,
    )
    # `create()` always writes a "revised" event first, so a draft with
    # any events at all always has at least one revision to draw
    # content from.
    assert latest_revision is not None

    first = events[0]

    return DecisionDraftView(
        draft_id=latest.draft_id,
        case_id=latest.case_id,
        user_id=latest.user_id,
        status=_STATUS_BY_EVENT_TYPE[latest.event_type],
        decision_type=latest_revision.decision_type,
        subject=latest_revision.subject,
        reason=latest_revision.reason,
        confidence=latest_revision.confidence,
        decided_at=latest_revision.decided_at,
        source=latest_revision.source,
        situation=latest_revision.situation,
        portfolio_relevance=latest_revision.portfolio_relevance,
        capital_considerations=latest_revision.capital_considerations,
        alternatives_considered=latest_revision.alternatives_considered,
        uncertainties=latest_revision.uncertainties,
        committed_decision_id=latest.committed_decision_id,
        latest_event_id=latest.id,
        created_at=first.recorded_at,
        updated_at=latest.recorded_at,
    )
