"""SQLAlchemy-backed InvestorIdentityRepository (ATLAS-009B).

`resolve()` is the only operation: it reads the store's single
InvestorIdentity if one exists, or atomically establishes one and
reconciles every existing Decision's `user_id` to it, in one
transaction. This is the one place in this codebase where a repository
touches another aggregate's table directly — justified solely by
atomicity (see docs/InvestorIdentityATLAS009B.md): composing two
independently-transactional repositories here would leave a real crash
window in which a store could end up with an InvestorIdentity but
permanently-unreconciled legacy Decisions.

Assumes `investor_identity_table` and `decisions_table` already exist —
guaranteed by `atlas.core.application.investor_identity.composition.resolve_investor_identity`,
the shared entry point that calls both tables' `create_*_table(engine)`
before constructing this repository.
"""
from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy import insert, select, update
from sqlalchemy.engine import Engine

from atlas.core.domain.decision.value_objects import UserId
from atlas.core.domain.investor_identity.entity import InvestorIdentity
from atlas.core.infrastructure.persistence.decision.table import decisions_table
from atlas.core.infrastructure.persistence.investor_identity.table import (
    investor_identity_table,
)

_SINGLETON_ID = "singleton"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SqlAlchemyInvestorIdentityRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def resolve(self, clock: Callable[[], datetime] = _utc_now) -> UserId:
        with self._engine.begin() as connection:
            row = (
                connection.execute(
                    select(investor_identity_table).where(
                        investor_identity_table.c.id == _SINGLETON_ID
                    )
                )
                .mappings()
                .first()
            )
            if row is not None:
                return UserId(uuid.UUID(row["user_id"]))

            identity = InvestorIdentity.register(clock=clock)
            connection.execute(
                insert(investor_identity_table).values(
                    id=_SINGLETON_ID,
                    user_id=str(identity.user_id),
                    established_at=identity.established_at.isoformat(),
                )
            )
            connection.execute(
                update(decisions_table).values(user_id=str(identity.user_id))
            )
            return identity.user_id
