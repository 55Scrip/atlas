"""The Case aggregate root (DO-IMP-001 Case Aggregate).

Case is the normative ownership boundary within which every other
Domain Object exists (OE-002 §3.1). Its own definition in OE-002 is
limited to that ownership-boundary role; no further lifecycle, status,
title, description, or content is canonically forced, and none is added
here (see docs/atlas_domain_object_architecture/
Domain-Object-Implementation-Reconciliation-Plan.md, DO-REC-001, Section
8). Case does not depend on, and is never automatically accompanied by,
Decision, Outcome, Judgment, Knowledge Reference, Reasoning Trace,
Evaluation, Learning, Hypothesis, or reasoning_link — those, when they
gain a `case_id`, will depend on Case; Case depends on none of them.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.core.domain.case.value_objects import CaseId

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Case:
    """A single, immutable ownership boundary.

    Valid whenever it carries an id and the moment Atlas recorded it —
    no further field is canonically required (OE-002 §3.1). Two Cases
    remain distinct even if created at the identical instant (INV-006):
    this dataclass's default, field-by-field equality already yields
    that result here, since `id` alone is always unique.
    """

    id: CaseId
    recorded_at: datetime

    @classmethod
    def create(cls, *, clock: _Clock = _utc_now) -> Case:
        """Establish a brand-new Case.

        Deliberately named `create`, not `capture`: unlike every other
        aggregate in this codebase, Case captures no investor-supplied
        content at all — there is nothing to capture, only an ownership
        boundary to establish. Creating a Case never creates any other
        Domain Object.
        """
        return cls(id=CaseId(), recorded_at=clock())
