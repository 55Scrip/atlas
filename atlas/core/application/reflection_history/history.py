"""Reflection History data model (ATLAS-010).

Not a domain aggregate: no persisted identity, recomputed fresh on every
ReflectionHistoryQuery.build() call. `entries` holds ReflectionResponse
directly rather than a wrapper type — a real, disclosed trade-off:
introducing a ReflectionHistoryEntry wrapper later would change this
field's element type, a breaking change to ReflectionHistory's own
public contract, not a free addition.
"""
from __future__ import annotations

from dataclasses import dataclass

from atlas.core.domain.reflection_response.entity import ReflectionResponse


@dataclass(frozen=True)
class ReflectionHistory:
    """The full, ordered chronological arrangement of one investor's own
    preserved Reflection Responses. Ordered by (recorded_at, id.value) —
    see query.py."""

    entries: tuple[ReflectionResponse, ...]
