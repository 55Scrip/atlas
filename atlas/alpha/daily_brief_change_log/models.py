"""The domain objects this package owns. See this package's own
`__init__.py` for why they exist and what they deliberately do not do.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

__all__ = ["ChangeLogEntry"]


@dataclass(frozen=True)
class ChangeLogEntry:
    """One durably-captured, eligible investment-case change. `id` is
    server-generated at write time (never client-supplied); the real
    dedup key is `(user_id, ticker, reason_code, value, secondary_value)`
    -- see `store.py::record_if_new`. `seen_at is None` is the NEW
    state (Phase 8); once set, the entry is SEEN but stays visible
    until `detected_at` ages past the archive window (`store.py`'s own
    `DEFAULT_ARCHIVE_AFTER`) -- "seen" and "archived" are deliberately
    two different fields, never conflated into one."""

    id: str
    user_id: str
    ticker: str
    case_id: str | None
    reason_code: str
    """The same `ReasonCode` value already on the wire for this fact
    (e.g. `"investment_decision_transition"`) -- never a second,
    parallel vocabulary. Kept as a plain string here (not the enum)
    since this package must stay readable independent of exactly which
    upstream engines exist; `eligibility.py` is the one place that
    knows the real enum."""
    value: str | None
    secondary_value: str | None
    label: str | None
    headline: str
    """The real, already-rendered `AgendaItem.headline` this change was
    observed on -- kept as a fallback for a reason code the frontend's
    own translation table doesn't (yet) recognize, never the primary
    rendering path."""
    priority_rank: int
    """`eligibility.py::EligibleChange.priority_rank`, persisted
    verbatim -- the fixed, disclosed severity order used to pick one
    primary change per ticker at read time (`synthesis.py`), never
    recomputed from `reason_code` a second way."""
    detected_at: datetime
    seen_at: datetime | None
