"""Value objects for the DecisionDraft aggregate (ADR-DD-001).

Only `DraftId` lives here. Draft content fields are deliberately plain,
unvalidated primitives (`str | None`, `int | None`, `datetime | None`),
never wrapped in `Decision`'s own strict value objects (`Subject`,
`InvestmentCase`, `Confidence`) — a draft may be incomplete by
definition, and those value objects reject incompleteness on
construction. Full validation happens only at commit time, via
`Decision.register()`/`DecisionContext.capture()` themselves,
unmodified. See `DecisionDraft-Implementation-Design.md` §2.3.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DraftId:
    """Identity of a DecisionDraft. Generated once, at creation, and never reused."""

    value: uuid.UUID = field(default_factory=uuid.uuid4)

    def __str__(self) -> str:
        return str(self.value)
