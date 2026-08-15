"""`ConfirmSecuritySelectionService` -- the one write path for Sprint
20. Never touches `Decision` beyond a single read (`DecisionRepository
.get`, to confirm the Decision actually exists) -- no method here can
mutate a Decision, because none of `DecisionRepository`'s methods this
package calls are anything but reads (see
`atlas.core.domain.decision.repository`'s own insert-only Protocol).

Honesty boundary (see this package's own `__init__.py`): this service
cannot verify that `confirmed_ticker` was genuinely one of the
candidates Sprint 19's discovery returned for this Decision's subject
-- discovery results are not persisted anywhere. What is recorded is
exactly what the caller asserts: "the investor confirms this ticker
for this Decision." `discovery_source` is validated against a closed
allow-list (currently only the one source Sprint 19 actually built)
purely to prevent silently inventing a new, unaudited provenance
label -- it is not, and cannot be, proof that discovery actually ran.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.alpha.security_confirmation.exceptions import (
    ConflictingConfirmationError,
    DecisionNotFoundError,
    UnsupportedDiscoverySourceError,
)
from atlas.alpha.security_confirmation.models import ConfirmedSecuritySelection
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
        if self._decisions.get(DecisionId(uuid.UUID(request.decision_id))) is None:
            raise DecisionNotFoundError(request.decision_id)
        if request.discovery_source not in _SUPPORTED_DISCOVERY_SOURCES:
            raise UnsupportedDiscoverySourceError(request.discovery_source)

        existing = self._confirmations.get_by_decision_id(request.decision_id)
        if existing is not None:
            if existing.confirmed_ticker == request.confirmed_ticker:
                return existing  # idempotent: same assertion, no new row
            raise ConflictingConfirmationError(
                decision_id=request.decision_id,
                existing_ticker=existing.confirmed_ticker,
                requested_ticker=request.confirmed_ticker,
            )

        selection = ConfirmedSecuritySelection(
            id=str(uuid.uuid4()),
            decision_id=request.decision_id,
            confirmed_ticker=request.confirmed_ticker,
            confirmed_display_name=request.confirmed_display_name,
            confirmed_cik=request.confirmed_cik,
            discovery_method=request.discovery_method,
            discovery_source=request.discovery_source,
            confirmed_at=self._clock(),
        )
        self._confirmations.add(selection)
        return selection

    def get(self, decision_id: str) -> ConfirmedSecuritySelection | None:
        return self._confirmations.get_by_decision_id(decision_id)
