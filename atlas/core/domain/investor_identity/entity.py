"""The InvestorIdentity domain fact (ATLAS-009B Investor Identity).

InvestorIdentity is not looked up by its own id — it is resolved as "the
one this data store has, if any." Exactly one exists per store for as
long as that store exists (ATLAS-009B-D invariant 8). `user_id` is the
durable payload this whole capability exists to make stable; other
aggregates already depend on `UserId` (Decision.user_id) — this entity
does not introduce a parallel identity type, only a durable source for
the one that already exists.
"""
from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.core.domain.decision.value_objects import UserId

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class InvestorIdentity:
    """The durable investor identity established for one data store."""

    user_id: UserId
    established_at: datetime

    @classmethod
    def register(cls, *, clock: _Clock = _utc_now) -> InvestorIdentity:
        """Establish a brand-new InvestorIdentity.

        This is the only path that assigns a fresh UserId — called
        exactly once per data store's lifetime, on first use.
        """
        return cls(user_id=UserId(uuid.uuid4()), established_at=clock())
