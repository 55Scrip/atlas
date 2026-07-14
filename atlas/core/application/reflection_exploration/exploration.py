"""Reflection Exploration data model (ATLAS-012).

Not a domain aggregate: no persisted identity, no lifecycle of its own —
exists only as the return value of one ReflectionExplorationQuery.build()
call. `entries` holds ReflectionResponse directly, the same
already-accepted trade-off ATLAS-010's ReflectionHistory.entries and
ATLAS-011's ReflectionComparison made for their own fields. Shaped as a
tuple, not a fixed pair, because Reflection Exploration is
variable-cardinality by domain definition (zero to all of an investor's
own Reflection History).
"""
from __future__ import annotations

from dataclasses import dataclass

from atlas.core.domain.reflection_response.entity import ReflectionResponse


@dataclass(frozen=True)
class ReflectionExploration:
    """A temporary, investor-defined scope: exactly the Reflection
    Responses the investor explicitly named, each appearing at most
    once, ordered by (recorded_at, id.value) — a presentation fact only.
    See query.py."""

    entries: tuple[ReflectionResponse, ...]
