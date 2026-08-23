"""Value objects for the Assumption aggregate (ADR-AS-001).

Only `AssumptionId` lives here. The assumption's own statement is
deliberately a plain, unvalidated string, mirroring `CaseCondition`'s
identical choice (`DecisionDraft`/`CaseCondition` precedent) — ADR-AS-001
§1 itself describes the content as "free text," with no fixed schema.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AssumptionId:
    """Identity of an Assumption. Generated once, at creation, and never reused."""

    value: uuid.UUID = field(default_factory=uuid.uuid4)

    def __str__(self) -> str:
        return str(self.value)
