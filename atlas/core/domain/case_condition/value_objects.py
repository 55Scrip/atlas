"""Value objects for the CaseCondition aggregate (ADR-CC-001).

Only `CaseConditionId` lives here. Condition content (predicate text,
role, structured threshold/date sub-fields) is deliberately plain,
unvalidated primitives, mirroring `DecisionDraft`'s own identical
choice (`DecisionDraft-Implementation-Design.md` §2.3) — ADR-CC-001 §3
itself states the predicate is "free text by default," with no fixed
schema to validate against.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CaseConditionId:
    """Identity of a CaseCondition. Generated once, at creation, and never reused."""

    value: uuid.UUID = field(default_factory=uuid.uuid4)

    def __str__(self) -> str:
        return str(self.value)
