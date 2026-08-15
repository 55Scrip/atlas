"""`ConfirmSecuritySelectionService` -- the write path for Security
Confirmation. Never touches `Decision` beyond a single read
(`DecisionRepository.get`, to confirm the Decision actually exists) --
no method here can mutate a Decision, because none of
`DecisionRepository`'s methods this package calls are anything but
reads (see `atlas.core.domain.decision.repository`'s own insert-only
Protocol).

Honesty boundary (see this package's own `__init__.py`): this service
cannot verify that `confirmed_ticker` was genuinely one of the
candidates Sprint 19's discovery returned for this Decision's subject
-- discovery results are not persisted anywhere. What is recorded is
exactly what the caller asserts: "the investor confirms this ticker
for this Decision." `discovery_source` is validated against a closed
allow-list (currently only the one source Sprint 19 actually built)
purely to prevent silently inventing a new, unaudited provenance
label -- it is not, and cannot be, proof that discovery actually ran.

Sprint 22 (Correction, Revocation & Historical Integrity) adds
`revoke()` and `correct()` on top of the unchanged `confirm()`/`get()`
contract:

- `confirm()` behaves exactly as it did in Sprint 20/21 -- unconfirmed
  Decision -> new "confirmed" event; same-ticker resubmission ->
  idempotent, no new row; different-ticker resubmission while a
  confirmation is active -> `ConflictingConfirmationError` (409),
  never a silent replacement. A Decision that was previously confirmed
  and then revoked is, for `confirm()`'s purposes, unconfirmed again
  (a fresh "confirmed" event is written, same as if it had never been
  confirmed at all).
- `revoke()` is the new explicit "I no longer stand behind my current
  confirmation" action -- appends a `"revoked"` event carrying through
  the ticker being revoked; never implies the ticker was wrong, only
  that the investor withdrew it (see `models.py`'s own docstring).
  Idempotent no-op if nothing is currently confirmed.
- `correct()` is the new explicit "change my confirmed selection"
  action -- requires a current confirmation to exist (`correct` means
  "change an existing one," not "create a new one"; an unconfirmed
  Decision should use `confirm()` instead), then appends a `"revoked"`
  event for the current selection followed by a `"confirmed"` event
  for the new one, both in the same request. Same-ticker `correct()`
  is a no-op returning the current selection, mirroring `confirm()`'s
  own idempotency philosophy rather than writing a redundant
  revoke+reconfirm pair.

No row is ever UPDATEd or DELETEd by any of these three methods --
every one of them only ever calls `repository.add()` with a new
`SecurityConfirmationEvent`, or writes nothing at all.

Ordering safety: every method that appends a new event derives its
`recorded_at` via `_next_recorded_at`, never a bare `self._clock()`
call. `repository.get_latest_event` orders by `(confirmed_at DESC, id
DESC)`, and `id` is an arbitrary UUID -- under a real clock this never
matters (microsecond resolution makes a same-instant collision
vanishingly unlikely), but under a fixed/injected test clock (see
`tests/unit/alpha/security_confirmation/test_service.py`'s own
`clock=lambda: ...`), two events written "at the same instant" would
otherwise have their relative order decided by an unrelated UUID
comparison -- silently breaking the very "revoked, then reconfirmed"
sequencing this sprint depends on. `_next_recorded_at` guarantees each
new event's timestamp is always strictly after the previous one for
that `decision_id`, regardless of clock resolution.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from atlas.alpha.security_confirmation.exceptions import (
    ConflictingConfirmationError,
    DecisionNotFoundError,
    NoActiveConfirmationError,
    UnsupportedDiscoverySourceError,
)
from atlas.alpha.security_confirmation.models import ConfirmedSecuritySelection, SecurityConfirmationEvent
from atlas.alpha.security_confirmation.repository import SqlAlchemySecurityConfirmationRepository
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.decision.value_objects import DecisionId

#: Closed allow-list -- see this module's own docstring for why this
#: is a provenance guard, not proof of anything. Grows only when a new
#: discovery source is actually built (currently just Sprint 19's SEC
#: `company_tickers.json` path).
_SUPPORTED_DISCOVERY_SOURCES = frozenset({"sec_company_tickers"})


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ConfirmSecuritySelectionRequest:
    decision_id: str
    confirmed_ticker: str
    confirmed_display_name: str
    confirmed_cik: int | None
    discovery_method: str
    discovery_source: str


class ConfirmSecuritySelectionService:
    def __init__(
        self,
        decision_repository: DecisionRepository,
        confirmation_repository: SqlAlchemySecurityConfirmationRepository,
        clock=_utc_now,
    ) -> None:
        self._decisions = decision_repository
        self._confirmations = confirmation_repository
        self._clock = clock

    def confirm(self, request: ConfirmSecuritySelectionRequest) -> ConfirmedSecuritySelection:
        self._ensure_decision_exists(request.decision_id)
        self._ensure_supported_source(request.discovery_source)

        latest = self._confirmations.get_latest_event(request.decision_id)
        if latest is not None and latest.event_type == "confirmed":
            if latest.confirmed_ticker == request.confirmed_ticker:
                return _selection_from_event(latest)  # idempotent: same assertion, no new row
            raise ConflictingConfirmationError(
                decision_id=request.decision_id,
                existing_ticker=latest.confirmed_ticker,
                requested_ticker=request.confirmed_ticker,
            )

        # `latest` is either None (never confirmed) or a "revoked"
        # event (previously confirmed, then withdrawn) -- both are
        # "currently unconfirmed" and free to accept a fresh confirmation.
        return self._append_confirmed_event(request, at=self._next_recorded_at(latest))

    def get(self, decision_id: str) -> ConfirmedSecuritySelection | None:
        return self._confirmations.get_by_decision_id(decision_id)

    def revoke(self, decision_id: str) -> None:
        """Idempotent: writes a `"revoked"` event only when a
        confirmation is currently active; a Decision that is already
        unconfirmed (never confirmed, or already revoked) is left
        exactly as-is -- revoking twice must never produce two
        redundant revocation events."""
        latest = self._confirmations.get_latest_event(decision_id)
        if latest is None or latest.event_type == "revoked":
            return
        self._confirmations.add(
            SecurityConfirmationEvent(
                id=str(uuid.uuid4()),
                decision_id=decision_id,
                event_type="revoked",
                confirmed_ticker=latest.confirmed_ticker,
                confirmed_display_name=latest.confirmed_display_name,
                confirmed_cik=latest.confirmed_cik,
                discovery_method=latest.discovery_method,
                discovery_source=latest.discovery_source,
                recorded_at=self._next_recorded_at(latest),
            )
        )

    def correct(self, request: ConfirmSecuritySelectionRequest) -> ConfirmedSecuritySelection:
        """Requires an active confirmation to correct -- see this
        module's own docstring for why an unconfirmed Decision must
        use `confirm()` instead. Same-ticker `correct()` is a no-op
        (returns the current selection unchanged, no new events)."""
        self._ensure_decision_exists(request.decision_id)
        self._ensure_supported_source(request.discovery_source)

        latest = self._confirmations.get_latest_event(request.decision_id)
        if latest is None or latest.event_type == "revoked":
            raise NoActiveConfirmationError(request.decision_id)
        if latest.confirmed_ticker == request.confirmed_ticker:
            return _selection_from_event(latest)

        revoked_event = SecurityConfirmationEvent(
            id=str(uuid.uuid4()),
            decision_id=request.decision_id,
            event_type="revoked",
            confirmed_ticker=latest.confirmed_ticker,
            confirmed_display_name=latest.confirmed_display_name,
            confirmed_cik=latest.confirmed_cik,
            discovery_method=latest.discovery_method,
            discovery_source=latest.discovery_source,
            recorded_at=self._next_recorded_at(latest),
        )
        self._confirmations.add(revoked_event)
        return self._append_confirmed_event(request, at=self._next_recorded_at(revoked_event))

    def _append_confirmed_event(
        self, request: ConfirmSecuritySelectionRequest, *, at: datetime
    ) -> ConfirmedSecuritySelection:
        event = SecurityConfirmationEvent(
            id=str(uuid.uuid4()),
            decision_id=request.decision_id,
            event_type="confirmed",
            confirmed_ticker=request.confirmed_ticker,
            confirmed_display_name=request.confirmed_display_name,
            confirmed_cik=request.confirmed_cik,
            discovery_method=request.discovery_method,
            discovery_source=request.discovery_source,
            recorded_at=at,
        )
        self._confirmations.add(event)
        return _selection_from_event(event)

    def _next_recorded_at(self, previous: SecurityConfirmationEvent | None) -> datetime:
        now = self._clock()
        if previous is None:
            return now
        return max(now, previous.recorded_at + timedelta(microseconds=1))

    def _ensure_decision_exists(self, decision_id: str) -> None:
        if self._decisions.get(DecisionId(uuid.UUID(decision_id))) is None:
            raise DecisionNotFoundError(decision_id)

    def _ensure_supported_source(self, discovery_source: str) -> None:
        if discovery_source not in _SUPPORTED_DISCOVERY_SOURCES:
            raise UnsupportedDiscoverySourceError(discovery_source)


def _selection_from_event(event: SecurityConfirmationEvent) -> ConfirmedSecuritySelection:
    return ConfirmedSecuritySelection(
        id=event.id,
        decision_id=event.decision_id,
        confirmed_ticker=event.confirmed_ticker,
        confirmed_display_name=event.confirmed_display_name,
        confirmed_cik=event.confirmed_cik,
        discovery_method=event.discovery_method,
        discovery_source=event.discovery_source,
        confirmed_at=event.recorded_at,
    )
