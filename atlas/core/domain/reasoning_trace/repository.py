"""Repository interface for the Reasoning Trace aggregate.

Atlas Alpha, Reasoning Trace Sprint 1: `list_all()` and `delete()` are
new, mirroring Evidence's and Knowledge Reference's own identical
additions in their own Sprint 1s. The governing design
(docs/atlas_domain_object_architecture/
Reasoning-Trace-Implementation-Design.md, Sections 27/30/38) originally
scoped this Protocol to `add`/`get` only, reasoning that permanence plus
the absence of any delete path eliminates the dangling-reference risk a
foreign key would otherwise guard against for the polymorphic `supports`
set. This sprint's required end-to-end workflow needs both: without
`list_all()`, the frontend has no way to discover which Reasoning Trace
ids exist for a given Observation after a page reload; without
`delete()`, the required "delete and confirm it stays deleted"
validation step has no backend support. This is a deliberate,
user-authorized extension of the documented scope, not an oversight —
see the Reasoning Trace Sprint 1 report for the full conflict and
decision. `delete()` does reintroduce the dangling-reference possibility
the design's own no-delete rule was written to avoid (a future
Reasoning Trace citing another Reasoning Trace as a support could be
orphaned if the cited one is later deleted); no code in this sprint
supports a Reasoning Trace citing another Reasoning Trace, so the risk
is not yet exercised, but it is now structurally possible.
"""

from __future__ import annotations

from typing import Protocol

from atlas.core.domain.reasoning_trace.entity import ReasoningTrace
from atlas.core.domain.reasoning_trace.value_objects import ReasoningTraceId


class ReasoningTraceRepository(Protocol):
    def add(self, reasoning_trace: ReasoningTrace) -> None:
        """Insert a new Reasoning Trace."""
        ...

    def get(self, reasoning_trace_id: ReasoningTraceId) -> ReasoningTrace | None:
        """Return a single Reasoning Trace by id, or None if it does not exist."""
        ...

    def list_all(self) -> list[ReasoningTrace]:
        """Return every Reasoning Trace ever captured, in chronological
        order: recorded_at ascending, then reasoning_trace_id as a
        deterministic final tie-breaker.
        """
        ...

    def delete(self, reasoning_trace_id: ReasoningTraceId) -> None:
        """Remove a Reasoning Trace, including all of its support rows.
        Idempotent: deleting an id that does not exist is not an error.
        """
        ...
