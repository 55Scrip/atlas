"""ReflectionComparisonQuery — assembles a ReflectionComparison (ATLAS-011).

Depends only on an already-built ReflectionHistory value — never on a
SQLAlchemy Engine, a repository, or ReflectionResponseRepository.get(id).
The owner-scoped lookup boundary is inherited entirely from Reflection
History (ATLAS-010): "is this id reachable" is answered by one question
only — is it present among history.entries — never re-verified by a
separate ownership check here.

Never calls .add(...) anywhere — there is no repository reachable from
this module at all.
"""
from __future__ import annotations

from atlas.core.application.reflection_comparison.comparison import ReflectionComparison
from atlas.core.application.reflection_comparison.exceptions import (
    DuplicateReflectionResponseSelectionError,
    ReflectionResponseNotOwnedError,
)
from atlas.core.application.reflection_history.history import ReflectionHistory
from atlas.core.domain.reflection_response.value_objects import ReflectionResponseId


class ReflectionComparisonQuery:
    def __init__(self, history: ReflectionHistory) -> None:
        self._history = history

    def build(
        self,
        first_id: ReflectionResponseId,
        second_id: ReflectionResponseId,
    ) -> ReflectionComparison:
        if first_id == second_id:
            raise DuplicateReflectionResponseSelectionError(
                "A comparison requires two different Reflection Responses"
            )

        entries_by_id = {entry.id: entry for entry in self._history.entries}
        if first_id not in entries_by_id or second_id not in entries_by_id:
            raise ReflectionResponseNotOwnedError(
                "One or both selected Reflection Responses are not in "
                "this investor's own Reflection History"
            )

        first_entry = entries_by_id[first_id]
        second_entry = entries_by_id[second_id]
        ordered = sorted(
            (first_entry, second_entry),
            key=lambda response: (response.recorded_at, response.id.value),
        )
        return ReflectionComparison(first=ordered[0], second=ordered[1])
