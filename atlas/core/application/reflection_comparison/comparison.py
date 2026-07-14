"""Reflection Comparison data model (ATLAS-011).

Not a domain aggregate: no persisted identity, no lifecycle of its own —
exists only as the return value of one ReflectionComparisonQuery.build()
call. `first`/`second` hold ReflectionResponse directly, the same
already-accepted trade-off ATLAS-010's own ReflectionHistory.entries
made: no wrapper type exists to introduce a breaking change to later.
"""
from __future__ import annotations

from dataclasses import dataclass

from atlas.core.domain.reflection_response.entity import ReflectionResponse


@dataclass(frozen=True)
class ReflectionComparison:
    """Exactly two, investor-selected, already-preserved Reflection
    Responses, arranged by (recorded_at, id.value) ascending — a
    presentation fact only, never a claim about selection order. See
    query.py."""

    first: ReflectionResponse
    second: ReflectionResponse
