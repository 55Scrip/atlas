"""Repository interface for the Judgment aggregate.

Atlas Alpha, Judgment Sprint 1: `list_all()` and `delete()` are new,
mirroring Evidence's, Knowledge Reference's, and Reasoning Trace's own
identical additions in their own Sprint 1s. The governing design
(docs/atlas_domain_object_architecture/Judgment-Implementation-Design.md,
Section 32: "Delete: forbidden"; confirmed by
Judgment-Pre-Commit-Architecture-Review.md's own H5-H6/H10-H11 findings)
originally scoped this Protocol to `add`/`get` only, for the identical
permanence/no-foreign-key reasoning already documented for Reasoning
Trace. This sprint's required end-to-end workflow needs both: without
`list_all()`, the frontend has no way to discover which Judgment ids
exist for a given Observation after a page reload; without `delete()`,
the required "delete and confirm it stays deleted" validation step has
no backend support. This is a deliberate, user-authorized extension of
the documented scope, following the identical precedent and decision
already made for Reasoning Trace Sprint 1 — see that sprint's report for
the fuller discussion. `delete()` reintroduces the dangling-reference
possibility the design's own no-delete rule was written to avoid (a
future Judgment, Decision, or Reasoning Trace citing another Judgment as
its subject could be orphaned if the cited Judgment is later deleted);
no code in this sprint supports a Judgment being referenced as another
object's subject, so the risk is not yet exercised, but it is now
structurally possible.
"""

from __future__ import annotations

from typing import Protocol

from atlas.core.domain.judgment.entity import Judgment
from atlas.core.domain.judgment.value_objects import JudgmentId


class JudgmentRepository(Protocol):
    def add(self, judgment: Judgment) -> None:
        """Insert a new Judgment."""
        ...

    def get(self, judgment_id: JudgmentId) -> Judgment | None:
        """Return a single Judgment by id, or None if it does not exist."""
        ...

    def list_all(self) -> list[Judgment]:
        """Return every Judgment ever captured, in chronological order:
        recorded_at ascending, then judgment_id as a deterministic final
        tie-breaker.
        """
        ...

    def delete(self, judgment_id: JudgmentId) -> None:
        """Remove a Judgment by id. Idempotent: deleting an id that does
        not exist is not an error.
        """
        ...
