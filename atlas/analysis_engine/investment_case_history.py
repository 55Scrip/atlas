"""History v1 -- a read-only presentation layer over persisted
Investment Case analytical snapshots, never a second analytical
representation.

"History does not reason. History does not recompute. History does not
decide what changed." Every field this module produces is a direct
read of an already-persisted `AnalyticalSnapshot`/`ChangeIntelligence`
pair (Investment Case Monitoring & Change Intelligence v1) -- this
module performs exactly one piece of real work: merging each Case's own
chronologically-ordered snapshot history into one cross-Case timeline,
newest first. It computes nothing analytical: no status, no direction,
no thesis impact, no headline is derived here -- all of that is already
real, on the `AnalyticalSnapshot`/`ChangeIntelligence` values a caller
hands in.

**Reuses, never duplicates.** `HistoricalAnalysisEntry` bundles a Case's
identity (`case_id`/`ticker`) with the exact `AnalyticalSnapshot` and
`ChangeIntelligence` `atlas.alpha.investment_case_change`'s own
repository already reconstructed from persisted state -- the same
"thin bundling dataclass, zero computed logic" shape
`atlas.analysis_engine.daily_brief.DailyBriefEntry` already establishes
for an analogous purpose.

**Ordering.** Newest first (`captured_at` descending), with a
deterministic secondary tiebreak (`case_id`, then `content_hash`) for
snapshots sharing an identical timestamp -- never an invented
importance/priority ordering (this module has no scoring concept to
order by in the first place).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.analysis_engine.investment_case_change import AnalyticalSnapshot, ChangeIntelligence

__all__ = ["HistoricalAnalysisEntry", "AnalyticalHistory", "build_analytical_history"]


@dataclass(frozen=True)
class HistoricalAnalysisEntry:
    """One Case's own snapshot, at one point in time, plus the
    (persisted, never recomputed) `ChangeIntelligence` describing how it
    differs from the entry immediately before it for the same Case."""

    case_id: str
    ticker: str | None
    snapshot: AnalyticalSnapshot
    change_intelligence: ChangeIntelligence


@dataclass(frozen=True)
class AnalyticalHistory:
    generated_at: datetime
    entries: tuple[HistoricalAnalysisEntry, ...]


def build_analytical_history(
    entries: tuple[HistoricalAnalysisEntry, ...], *, generated_at: datetime
) -> AnalyticalHistory:
    """`entries` should already be exactly the per-Case history a caller
    read from persistence (one `HistoricalAnalysisEntry` per persisted
    snapshot, across every Case it cares about) -- this function performs
    no eligibility filtering (unlike Daily Brief, History shows every
    entry, including baselines) and no recomputation, only deterministic
    ordering."""
    ordered = tuple(
        sorted(
            entries,
            key=lambda entry: (-entry.snapshot.captured_at.timestamp(), entry.case_id, entry.snapshot.content_hash),
        )
    )
    return AnalyticalHistory(generated_at=generated_at, entries=ordered)
