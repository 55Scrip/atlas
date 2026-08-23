"""`DecisionDraftService` — the application service for DecisionDraft
(ADR-DD-001).

Only the methods named in `DecisionDraft-Implementation-Design.md` §8.1
exist here: `create`, `revise`, `abandon`, `commit`, `get`,
`list_active_for_case`, `list_events`, `daily_brief_summary`. No
additional public API.

`commit()` is the one method that touches another aggregate's own
repositories — and it does so exactly as `capture_decision_context.py`
already touches `DecisionRepository` (a direct call to the sibling
aggregate's own unmodified domain classmethod and its own unmodified
repository, never through that sibling's own application or API
service layer). `Decision.register()` and `DecisionContext.capture()`
are called precisely as they exist today; this module contains no
reimplementation of either's own validation.

Ordering safety follows `security_confirmation/service.py`'s own
`_next_recorded_at` idiom verbatim: every appended event's
`recorded_at` is `max(clock(), previous_latest.recorded_at +
timedelta(microseconds=1))`, never a bare clock call, so two events for
the same draft are always strictly ordered even under an injected,
fixed test clock.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from atlas.core.domain.case.exceptions import CaseNotFoundError
from atlas.core.domain.case.repository import CaseRepository
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.decision.value_objects import (
    Confidence,
    DecisionSource,
    InvestmentCase,
    Subject,
    UserId,
)
from atlas.core.domain.decision_context.entity import DecisionContext
from atlas.core.domain.decision_context.repository import DecisionContextRepository
from atlas.core.domain.decision_context.value_objects import (
    AlternativesConsidered,
    Situation,
    Uncertainties,
)
from atlas.core.domain.decision_draft.entity import (
    DecisionDraftEvent,
    DecisionDraftView,
    reconstruct_current_state,
)
from atlas.core.domain.decision_draft.exceptions import (
    DecisionDraftAlreadyAbandonedError,
    DecisionDraftAlreadyCommittedError,
    DecisionDraftConflictError,
    DecisionDraftNotFoundError,
)
from atlas.core.domain.decision_draft.repository import DecisionDraftEventRepository
from atlas.core.domain.decision_draft.value_objects import DraftId


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class DecisionDraftContent:
    """The draft's own editable content — plain, unvalidated fields.
    See `DecisionDraft-Implementation-Design.md` §2.3 for why these are
    not `Decision`'s/`DecisionContext`'s own value objects.
    """

    decision_type: str | None = None
    subject: str | None = None
    reason: str | None = None
    confidence: int | None = None
    decided_at: datetime | None = None
    source: str | None = None
    situation: str | None = None
    portfolio_relevance: str | None = None
    capital_considerations: str | None = None
    alternatives_considered: tuple[str, ...] = ()
    uncertainties: tuple[str, ...] = ()


@dataclass(frozen=True)
class DecisionDraftCommitResult:
    decision: Decision
    decision_context: DecisionContext | None
    draft: DecisionDraftView


@dataclass(frozen=True)
class DecisionDraftSummary:
    """The narrow, ADR-DD-001 §4-conformant projection: existence,
    subject, and enough identity to build a resume link — never full
    content."""

    draft_id: DraftId
    case_id: CaseId
    subject: str | None
    created_at: datetime


class DecisionDraftService:
    def __init__(
        self,
        draft_repository: DecisionDraftEventRepository,
        case_repository: CaseRepository,
        decision_repository: DecisionRepository,
        decision_context_repository: DecisionContextRepository,
        clock=_utc_now,
    ) -> None:
        self._drafts = draft_repository
        self._cases = case_repository
        self._decisions = decision_repository
        self._decision_contexts = decision_context_repository
        self._clock = clock

    def create(
        self, *, case_id: CaseId, user_id: UserId, content: DecisionDraftContent
    ) -> DecisionDraftView:
        self._ensure_case_exists(case_id)
        event = DecisionDraftEvent.revised(
            draft_id=DraftId(),
            case_id=case_id,
            user_id=user_id,
            event_id=str(uuid.uuid4()),
            clock=self._clock,
            **_content_kwargs(content),
        )
        self._drafts.add(event)
        return self._require_view(event.draft_id)

    def revise(
        self,
        draft_id: DraftId,
        *,
        content: DecisionDraftContent,
        expected_latest_event_id: str | None = None,
    ) -> DecisionDraftView:
        latest = self._require_latest(draft_id)
        self._ensure_still_revisable(latest)
        if expected_latest_event_id is not None and expected_latest_event_id != latest.id:
            raise DecisionDraftConflictError(
                f"Draft {draft_id} was revised elsewhere since expected event "
                f"{expected_latest_event_id!r} (latest is now {latest.id!r})"
            )
        event = DecisionDraftEvent.revised(
            draft_id=draft_id,
            case_id=latest.case_id,
            user_id=latest.user_id,
            event_id=str(uuid.uuid4()),
            clock=lambda: self._next_recorded_at(latest),
            **_content_kwargs(content),
        )
        self._drafts.add(event)
        return self._require_view(draft_id)

    def abandon(self, draft_id: DraftId) -> DecisionDraftView:
        """Idempotent: abandoning an already-abandoned draft writes no
        new event. Abandoning a committed draft is rejected — a real
        Decision already exists; there is nothing left to discard.
        """
        latest = self._require_latest(draft_id)
        if latest.event_type == "abandoned":
            return self._require_view(draft_id)
        if latest.event_type == "committed":
            raise DecisionDraftAlreadyCommittedError(
                f"Draft {draft_id} has already been committed and cannot be abandoned"
            )
        event = DecisionDraftEvent.abandoned(
            draft_id=draft_id,
            case_id=latest.case_id,
            user_id=latest.user_id,
            event_id=str(uuid.uuid4()),
            clock=lambda: self._next_recorded_at(latest),
        )
        self._drafts.add(event)
        return self._require_view(draft_id)

    def commit(self, draft_id: DraftId) -> DecisionDraftCommitResult:
        """Constructs a real `Decision` (and, when `situation` is
        present, a real `DecisionContext`) from exactly what the
        draft's own latest revision holds, via the unmodified
        `Decision.register()`/`DecisionContext.capture()` classmethods,
        then appends the terminal `"committed"` event. Any validation
        exception either classmethod (or its own value objects) raises
        propagates unmodified — this method performs no validation of
        its own beyond constructing the value objects those
        classmethods themselves require as parameters.

        Sequential, independently-transacted writes (Decision, then
        DecisionContext if applicable, then the committed event) — the
        same non-atomic-across-calls risk profile
        `security_confirmation/service.py`'s own `correct()` already
        carries; see `DecisionDraft-Implementation-Design.md` §10.
        """
        latest = self._require_latest(draft_id)
        if latest.event_type == "abandoned":
            raise DecisionDraftAlreadyAbandonedError(
                f"Draft {draft_id} has been abandoned and cannot be committed"
            )
        if latest.event_type == "committed":
            raise DecisionDraftAlreadyCommittedError(
                f"Draft {draft_id} has already been committed"
            )

        decision = Decision.register(
            case_id=latest.case_id,
            user_id=latest.user_id,
            decision_type=latest.decision_type,
            subject=Subject(latest.subject),
            investment_case=InvestmentCase(latest.reason),
            confidence=Confidence(latest.confidence),
            decided_at=latest.decided_at,
            source=DecisionSource(latest.source) if latest.source else DecisionSource.MANUAL,
        )
        self._decisions.add(decision)

        decision_context: DecisionContext | None = None
        if latest.situation is not None:
            decision_context = DecisionContext.capture(
                decision_id=decision.id,
                situation=Situation(latest.situation),
                captured_at=decision.recorded_at,
                portfolio_relevance=latest.portfolio_relevance,
                capital_considerations=latest.capital_considerations,
                alternatives_considered=AlternativesConsidered(latest.alternatives_considered),
                uncertainties=Uncertainties(latest.uncertainties),
            )
            self._decision_contexts.add(decision_context)

        committed_event = DecisionDraftEvent.committed(
            draft_id=draft_id,
            case_id=latest.case_id,
            user_id=latest.user_id,
            committed_decision_id=str(decision.id.value),
            event_id=str(uuid.uuid4()),
            clock=lambda: self._next_recorded_at(latest),
        )
        self._drafts.add(committed_event)

        return DecisionDraftCommitResult(
            decision=decision,
            decision_context=decision_context,
            draft=self._require_view(draft_id),
        )

    def get(self, draft_id: DraftId) -> DecisionDraftView:
        return self._require_view(draft_id)

    def list_active_for_case(self, case_id: CaseId) -> list[DecisionDraftView]:
        latest_events = self._drafts.list_latest_by_case(case_id)
        active_drafts = [event for event in latest_events if event.event_type == "revised"]
        return [self._require_view(event.draft_id) for event in active_drafts]

    def list_events(self, draft_id: DraftId) -> list[DecisionDraftEvent]:
        events = self._drafts.list_events(draft_id)
        if not events:
            raise DecisionDraftNotFoundError(f"No DecisionDraft found with id {draft_id}")
        return events

    def daily_brief_summary(self, user_id: UserId) -> list[DecisionDraftSummary]:
        """The narrow projection ADR-DD-001 §4 requires: existence,
        subject, and identity only — never `reason`, `confidence`,
        `situation`, or any other full-content field.
        """
        latest_events = self._drafts.list_latest_by_user(user_id)
        active = [event for event in latest_events if event.event_type == "revised"]
        return [
            DecisionDraftSummary(
                draft_id=event.draft_id,
                case_id=event.case_id,
                subject=event.subject,
                created_at=self._first_event_recorded_at(event.draft_id),
            )
            for event in active
        ]

    def _ensure_case_exists(self, case_id: CaseId) -> None:
        if self._cases.get(case_id) is None:
            raise CaseNotFoundError(f"No Case found with id {case_id}")

    def _require_latest(self, draft_id: DraftId) -> DecisionDraftEvent:
        latest = self._drafts.get_latest_event(draft_id)
        if latest is None:
            raise DecisionDraftNotFoundError(f"No DecisionDraft found with id {draft_id}")
        return latest

    def _require_view(self, draft_id: DraftId) -> DecisionDraftView:
        events = self._drafts.list_events(draft_id)
        view = reconstruct_current_state(events)
        if view is None:
            raise DecisionDraftNotFoundError(f"No DecisionDraft found with id {draft_id}")
        return view

    def _first_event_recorded_at(self, draft_id: DraftId) -> datetime:
        events = self._drafts.list_events(draft_id)
        return events[0].recorded_at

    @staticmethod
    def _ensure_still_revisable(latest: DecisionDraftEvent) -> None:
        if latest.event_type == "abandoned":
            raise DecisionDraftAlreadyAbandonedError(
                f"Draft {latest.draft_id} has been abandoned and can no longer be revised"
            )
        if latest.event_type == "committed":
            raise DecisionDraftAlreadyCommittedError(
                f"Draft {latest.draft_id} has already been committed and can no longer be revised"
            )

    def _next_recorded_at(self, previous: DecisionDraftEvent) -> datetime:
        now = self._clock()
        return max(now, previous.recorded_at + timedelta(microseconds=1))


def _content_kwargs(content: DecisionDraftContent) -> dict:
    return {
        "decision_type": content.decision_type,
        "subject": content.subject,
        "reason": content.reason,
        "confidence": content.confidence,
        "decided_at": content.decided_at,
        "source": content.source,
        "situation": content.situation,
        "portfolio_relevance": content.portfolio_relevance,
        "capital_considerations": content.capital_considerations,
        "alternatives_considered": content.alternatives_considered,
        "uncertainties": content.uncertainties,
    }
