"""When a forward claim was made, and what Atlas does not know about
that (Forward-Looking Evidence, Stage 3.1).

A transcript record carries three different kinds of time, and exactly
one of them is evidence about the call:

- **The reporting period** -- the provider's own label, "2025Q3", in
  the record's `metadata["quarter"]`. It is the company's *fiscal*
  quarter, not a calendar one: CRM's "2025Q3" call opens "our Fiscal 2025
  Third Quarter Results Conference Call", NVIDIA's "2025Q3" is its "third
  quarter of fiscal 2025". For one company, those labels are one
  company's fiscal quarters in order, which is what lets Stage 2.1
  order that company's guidance -- and only that company's: a label says
  nothing about another issuer's calendar.
- **When management spoke** -- unknown. Alpha Vantage supplies no call
  date. The record's `published_at` is the instant a fetch was
  evaluated as of (for a historical backfill, a date the operator's
  command chose so the provider would select an older quarter), and its
  `period_start`/`period_end` are Atlas's calendar reading of the
  fiscal label. NVIDIA's own transcripts show both are wrong: its
  "2025Q3" call says "All our statements are made as of today, November
  20, 2024", ten months before the 2025-09-30 Atlas stores as that
  quarter's end.
- **When Atlas ingested it** -- the record's `version.created_at`,
  which is operational, never evidence of when anything was said.

So a claim carries its period and, only when a source actually supplies
one, the moment it was stated. Chronology between two calls of the same
company can be read from their periods; how *old* a statement is can
only be read from a statement date, and without one the answer is
unknown rather than approximated.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from atlas.analysis_engine.business_data.transcript_time import period_ordinal, transcript_period

if TYPE_CHECKING:  # pragma: no cover - typing only
    from atlas.analysis_engine.forward_claims.models import ForwardClaim

__all__ = ["period_ordinal", "statement_age", "transcript_period"]

#: `transcript_period` and `period_ordinal` live with the transcript
#: record's own temporal contract (`business_data.transcript_time`, Stage
#: 3.2), where the legacy earnings-call consumers read them too; they are
#: re-exported here unchanged.


def statement_age(claim: ForwardClaim, *, as_of: datetime) -> timedelta | None:
    """How long ago management made the claim -- or `None` when no
    source says when that was. The one way to ask this question, so a
    period, a fetch time or an ingestion time can never stand in for
    it."""
    if claim.statement_at is None:
        return None
    return as_of - claim.statement_at
