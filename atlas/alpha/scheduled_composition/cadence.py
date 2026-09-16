"""How often a scheduled batch should run, and why that number.

The cadence is not a performance knob. It is an answer to a product
question: **how often can Atlas's conclusion about a Case actually move?**
Composing faster than that produces reads and no record.

A snapshot is written only when the categorical conclusion changes, or when
the evidence beneath an unchanged conclusion changes. The evidence
fingerprint deliberately excludes the current yield, so a price tick alone
never writes a row. What genuinely moves a conclusion is stored financial
data (new filings -- quarterly), share counts, the fiscal-epoch roll, and
the investor changing what they hold or watch. And because composition never
fetches, it can only ever see what some earlier refresh already wrote.

So the alternatives, and why one daily batch:

- **Manual only.** Honest, and where this sprint starts -- but it makes the
  record a function of whether someone remembered, which is what left the
  history empty in the first place.
- **Hourly.** Twenty-four times the work for the same rows. Stored evidence
  does not change hourly, and nothing composition reads is hourly.
- **Daily.** Matches the fastest thing that plausibly moves a conclusion,
  and gives the history a granularity the coverage read model already
  speaks in ("distinct days observed"). At most one observation per Case
  per day is a meaningful longitudinal series rather than a dense log of a
  Case sitting still.
- **Weekly.** Cheaper, but a conclusion that changes on a Tuesday and
  changes back on a Thursday leaves no trace at all. The record would be a
  sample of Sundays, not a history.
- **On refresh only.** Appealing -- refreshes are what change stored
  evidence -- but it couples the record to an operator action, so a Case
  nobody refreshes silently stops accumulating history and looks stable
  rather than unobserved.

Daily, overridable, and triggered by nothing yet.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta

__all__ = ["DEFAULT_INTERVAL_SECONDS", "INTERVAL_ENV_VAR", "configured_interval", "is_due"]

INTERVAL_ENV_VAR = "ATLAS_SCHEDULED_COMPOSITION_INTERVAL_SECONDS"

DEFAULT_INTERVAL_SECONDS = 24 * 60 * 60


def configured_interval() -> timedelta:
    """The configured interval, or the daily default.

    An unreadable or non-positive value falls back to the default rather
    than raising: a malformed environment variable should not be able to
    stop Atlas, and a zero or negative interval would mean "continuously",
    which is never a cadence anyone intends.
    """
    raw = os.environ.get(INTERVAL_ENV_VAR)
    try:
        seconds = int(raw) if raw is not None and raw.strip() else DEFAULT_INTERVAL_SECONDS
    except ValueError:
        seconds = DEFAULT_INTERVAL_SECONDS
    return timedelta(seconds=seconds if seconds > 0 else DEFAULT_INTERVAL_SECONDS)


def is_due(last_run_at: datetime | None, now: datetime, interval: timedelta | None = None) -> bool:
    """Whether a batch is due.

    A pure function of two timestamps: the caller owns when it last ran, so
    scheduling introduces no table, no state and nothing to keep in sync.
    Never having run is due.
    """
    if last_run_at is None:
        return True
    return now - last_run_at >= (interval if interval is not None else configured_interval())
