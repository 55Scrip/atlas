"""Market price freshness (Internal Alpha Stabilization 1 -- MSFT price
root cause fix). A market price is judged fresh or stale against the
most recent trading day it *should* reflect -- never a flat "N days
old" cutoff, since a Friday close is still the correct, current price
all weekend.

Deliberately separate from -- and much stricter than -- company
fundamentals/profile freshness (name, sector, shares outstanding,
financial statements), which change far more slowly and are not
addressed by this module. See `atlas.alpha.business_data_refresh
.price_refresh` for the one place this policy is actually acted on.

Known, disclosed limitation: `latest_expected_trading_day` treats
every Monday-Friday as a trading day. It does not model U.S. market
holidays (Thanksgiving, Christmas, etc.) -- on a holiday, a real,
still-current price will be misjudged "stale" for one extra day. This
is a deliberately accepted, harmless failure mode: the only
consequence is one avoidable refresh attempt against a provider that
returns the identical price and trading day it already had, consuming
one unit of the daily call budget, never a wrong price shown, never
data loss. A real market-holiday calendar is out of scope for this
minimal, first Internal Alpha version.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

__all__ = ["latest_expected_trading_day", "is_price_fresh"]

#: A trading day's own close is not yet "expected" to exist until a
#: conservative buffer after the real ~20:00 UTC (4pm ET) US market
#: close -- comfortably past both the close itself and Alpha Vantage's
#: own short publication lag. Before this hour on any given day, the
#: *previous* trading day's close is still the most recently genuinely
#: available one; a price dated today is not "stale" just because
#: today's own market hasn't closed yet.
_MARKET_CLOSE_BUFFER_UTC_HOUR = 21

_SATURDAY = 5
_SUNDAY = 6


def latest_expected_trading_day(as_of: datetime) -> date:
    """The most recent trading day whose closing price should already
    be available, as of `as_of`. Weekdays only (Mon-Fri) -- see this
    module's own docstring for the accepted U.S.-market-holiday gap."""
    reference = as_of if as_of.tzinfo is not None else as_of.replace(tzinfo=timezone.utc)
    reference = reference.astimezone(timezone.utc)
    candidate = reference.date() if reference.hour >= _MARKET_CLOSE_BUFFER_UTC_HOUR else reference.date() - timedelta(days=1)
    while candidate.weekday() in (_SATURDAY, _SUNDAY):
        candidate -= timedelta(days=1)
    return candidate


def is_price_fresh(trading_day: date | None, *, as_of: datetime) -> bool:
    """`trading_day` is the stored snapshot's own `period_end` -- the
    real trading day the price is *from*, never the moment Atlas
    happened to fetch it. `None` (no snapshot at all) is honestly never
    fresh."""
    if trading_day is None:
        return False
    return trading_day >= latest_expected_trading_day(as_of)
