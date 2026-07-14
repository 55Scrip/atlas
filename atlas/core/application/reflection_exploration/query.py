"""ReflectionExplorationQuery — assembles a ReflectionExploration (ATLAS-012).

Depends only on an already-built ReflectionHistory value — never on a
SQLAlchemy Engine, a repository, or ReflectionResponseRepository.get(id).
The owner-scoped lookup boundary is inherited entirely from Reflection
History (ATLAS-010): "is this id reachable" is answered by one question
only — is it present among history.entries — never re-verified by a
separate ownership check here.

ReflectionHistory and its contained ReflectionResponse objects are
immutable inputs (both are frozen dataclasses). build() constructs a new
ReflectionExploration on every call; it never mutates the supplied
history or any Response reachable through it.

Never calls .add(...) anywhere — there is no repository reachable from
this module at all.
"""
from __future__ import annotations

from collections.abc import Sequence

from atlas.core.application.reflection_exploration.exceptions import (
    UnreachableReflectionResponseError,
)
from atlas.core.application.reflection_exploration.exploration import ReflectionExploration
from atlas.core.application.reflection_history.history import ReflectionHistory
from atlas.core.domain.reflection_response.value_objects import ReflectionResponseId


class ReflectionExplorationQuery:
    def __init__(self, history: ReflectionHistory) -> None:
        self._history = history

    def build(
        self, selected_ids: Sequence[ReflectionResponseId]
    ) -> ReflectionExploration:
        # Reflection Exploration is defined over set membership, not
        # occurrence count — naming the same Response more than once
        # conveys no additional domain information, so it is
        # deduplicated silently rather than treated as invalid.
        distinct_ids = dict.fromkeys(selected_ids)

        entries_by_id = {entry.id: entry for entry in self._history.entries}
        if any(selected_id not in entries_by_id for selected_id in distinct_ids):
            raise UnreachableReflectionResponseError(
                "One or more selected Reflection Responses are not in "
                "this investor's own Reflection History"
            )

        matched = [entries_by_id[selected_id] for selected_id in distinct_ids]
        ordered = sorted(matched, key=lambda response: (response.recorded_at, response.id.value))
        return ReflectionExploration(entries=tuple(ordered))
