"""Daily Brief 2.0, Phase 10 -- "one company = one message." Groups the
change log's own real entries by ticker and picks exactly one primary
entry per ticker (lowest `priority_rank`, ties broken by earliest
`detected_at` so the first-observed fact wins a genuine tie); any
other real, eligible facts for that same ticker are counted, never
dropped, so the frontend can offer them behind "view remaining
changes" (this sprint's own Section 1 spec) instead of showing four
separate items for one company.

Pure grouping over already-eligible entries -- this module makes no
new eligibility judgment of its own; that is entirely `eligibility.py`'s
job, already applied before anything reaches the change log.
"""
from __future__ import annotations

from dataclasses import dataclass

from atlas.alpha.daily_brief_change_log.models import ChangeLogEntry

__all__ = ["TickerChangeGroup", "group_by_ticker"]


@dataclass(frozen=True)
class TickerChangeGroup:
    ticker: str
    primary: ChangeLogEntry
    additional_count: int
    """How many other real, eligible changes exist for this ticker
    beyond `primary` -- 0 for the common case of one real change."""
    is_new: bool
    """True iff `primary` itself is unseen (`seen_at is None`). Only
    `primary`'s own seen-state decides the group's NEW-dot treatment
    (Phase 8) -- a group is never shown as new merely because some
    lower-ranked, non-primary fact for the same ticker is unseen."""


def group_by_ticker(entries: tuple[ChangeLogEntry, ...]) -> tuple[TickerChangeGroup, ...]:
    by_ticker: dict[str, list[ChangeLogEntry]] = {}
    for entry in entries:
        by_ticker.setdefault(entry.ticker, []).append(entry)

    groups: list[TickerChangeGroup] = []
    for ticker, ticker_entries in by_ticker.items():
        ordered = sorted(ticker_entries, key=lambda e: (e.priority_rank, e.detected_at))
        primary = ordered[0]
        groups.append(
            TickerChangeGroup(
                ticker=ticker,
                primary=primary,
                additional_count=len(ordered) - 1,
                is_new=primary.seen_at is None,
            )
        )
    # Most recently detected primary first -- Section 1's own "since
    # your last visit" is a recency-ordered briefing, not a severity-
    # ranked worklist (severity already decided which fact represents
    # each company; recency decides the order companies appear in).
    groups.sort(key=lambda g: g.primary.detected_at, reverse=True)
    return tuple(groups)
