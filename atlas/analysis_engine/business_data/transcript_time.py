"""What a transcript record says about time (Stage 3.1 / 3.2).

A transcript `BusinessRecord` carries three kinds of time, and exactly
one of them is evidence about the call itself:

- **The reporting period** -- the provider's own label, "2025Q3", in
  `metadata["quarter"]`. It is the company's *fiscal* quarter, not a
  calendar one: CRM's "2025Q3" call opens "our Fiscal 2025 Third Quarter
  Results Conference Call". One company's labels are that company's
  fiscal quarters in order, so they establish the order of its calls --
  and nothing about another issuer's calendar, and nothing about dates.
- **When management spoke** -- `transcript_statement_date`. Unknown for
  every transcript Atlas holds: Alpha Vantage supplies no call date.
- **Operational time** -- `published_at`, `version.created_at`,
  `provenance.computed_at`. When a fetch was evaluated as of, and when
  Atlas ingested the result. Never evidence of when anything was said.

The record's `period_start`/`period_end`, on transcripts ingested before
Stage 3.2, are Atlas's *calendar* reading of the fiscal label -- wrong
for any company whose fiscal year is not the calendar year: NVIDIA's
"2025Q3" call says "All our statements are made as of today, November
20, 2024", ten months before the 2025-09-30 stored as that quarter's
end. New transcript records carry no period dates at all. Either way, no
consumer reads a transcript's period or operational dates as the time
of the call: they ask this module, which answers from the label, or
answers unknown.
"""
from __future__ import annotations

import re
from datetime import date

from atlas.analysis_engine.business_data.models import BusinessRecord

__all__ = ["period_ordinal", "transcript_period", "transcript_statement_date"]

_PERIOD = re.compile(r"^(20\d\d)Q([1-4])$")


def transcript_period(record: BusinessRecord) -> str | None:
    """The provider's label for the fiscal quarter a transcript reports
    on, exactly as stored -- `None` when the record carries no label in
    the provider's "YYYYQn" form. Never converted to calendar dates."""
    label = record.metadata.get("quarter")
    return label if isinstance(label, str) and _PERIOD.match(label) else None


def period_ordinal(period: str | None) -> tuple[int, int] | None:
    """(fiscal year, quarter), for ordering one company's periods. Two
    ordinals are comparable only for the same company and provider."""
    match = _PERIOD.match(period) if isinstance(period, str) else None
    return (int(match.group(1)), int(match.group(2))) if match else None


def transcript_statement_date(record: BusinessRecord) -> date | None:
    """When management made the statements in this transcript, as far as
    the record can prove it -- always `None` today. The provider supplies
    no call date, and neither the record's `published_at` (a fetch
    instant), its `period_end` (a calendar reading of a fiscal label) nor
    its ingestion time may stand in for one. The single place a genuine
    source date would be read, once a source supplies it."""
    del record
    return None
