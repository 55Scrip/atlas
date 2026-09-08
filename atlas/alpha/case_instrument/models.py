"""The binding value type. Deliberately tiny: this package records a
fact, it does not interpret one."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

__all__ = ["CaseInstrumentBinding"]


@dataclass(frozen=True)
class CaseInstrumentBinding:
    """Which operative instrument a Case is about.

    `instrument_key` is the operative ticker exactly as the rest of
    Alpha already keys on it -- `business_records.company`, the trade
    log's `security`, `alpha_watchlist_entry.ticker`, a holding's
    `ticker`. It is stored verbatim, never re-normalized here: this
    package is not an identity engine, and inventing a normalization
    of its own is precisely how `SU.PA` (Schneider Electric, Euronext
    Paris) would end up sharing a key with `SU` (Suncor Energy, NYSE),
    two unrelated companies that both exist in this database today.
    Share classes stay distinct for the same reason -- `GOOG` and
    `GOOGL`, `BRK.B`, `VOLV-B` are simply different keys.

    `canonical_security_id` is the migration seam to
    `atlas.alpha.canonical_security`. Always `None` today; see this
    package's `__init__` for why it cannot be filled yet.
    """

    case_id: str
    instrument_key: str
    bound_at: datetime
    canonical_security_id: str | None = None
