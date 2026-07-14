"""ReflectionHistoryQuery — assembles a ReflectionHistory (ATLAS-010).

Depends only on ReflectionResponseRepository and a plain UserId value —
never on a SQLAlchemy Engine, and never on
resolve_investor_identity itself. `owner_user_id` must already be
resolved by the caller before this object is constructed; this class has
no way to resolve or bootstrap one itself, by construction (see
composition.py).

Never calls .add(...) — this query only reads, never owns Reflection
Responses.
"""
from __future__ import annotations

from atlas.core.application.reflection_history.history import ReflectionHistory
from atlas.core.domain.decision.value_objects import UserId
from atlas.core.domain.reflection_response.repository import ReflectionResponseRepository


class ReflectionHistoryQuery:
    def __init__(
        self,
        repository: ReflectionResponseRepository,
        owner_user_id: UserId,
    ) -> None:
        self._repository = repository
        self._owner_user_id = owner_user_id

    def build(self) -> ReflectionHistory:
        entries = self._repository.list_all_for_owner(self._owner_user_id)
        ordered = sorted(entries, key=lambda response: (response.recorded_at, response.id.value))
        return ReflectionHistory(entries=tuple(ordered))
