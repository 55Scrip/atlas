"""`RegulatoryFiling` extraction (Automatic Knowledge Ingestion
Framework, Foundation Provider).

A small, read-only projection over already-ingested `BusinessRecord`s
-- the same "reuse the currently supported financial data structures"
discipline `company_profile.py`/`financial_history.py` already
establish, applied here to `SourceKind.COMPANY_FILING`. Never imports
a provider, never makes a network call, never fabricates a field: a
company with no ingested `COMPANY_FILING` record simply has an empty
filing history -- an honest `()`, not a guessed one.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.sources import SourceKind

__all__ = ["RegulatoryFiling", "extract_regulatory_filings"]


@dataclass(frozen=True)
class RegulatoryFiling:
    """One real SEC filing's own identity -- its existence and
    metadata, never its content (Atlas does not read or summarize the
    filing document itself)."""

    form_type: str
    filed_at: datetime
    accession_number: str
    filing_url: str
    period_of_report: date | None


def extract_regulatory_filings(business_records: tuple[BusinessRecord, ...]) -> tuple[RegulatoryFiling, ...]:
    """Every `COMPANY_FILING` record among `business_records` (the
    caller's already-`latest_versions`-filtered set), newest first --
    the natural "what has Atlas most recently learned" reading order."""
    filings = [record for record in business_records if record.document_type is SourceKind.COMPANY_FILING]
    filings.sort(key=lambda record: record.published_at, reverse=True)
    result: list[RegulatoryFiling] = []
    for record in filings:
        metadata = record.metadata
        form_type = metadata.get("form_type")
        accession_number = metadata.get("accession_number")
        if form_type is None or accession_number is None:
            continue
        result.append(
            RegulatoryFiling(
                form_type=form_type,
                filed_at=record.published_at,
                accession_number=accession_number,
                filing_url=metadata.get("filing_url", record.source_reference),
                period_of_report=record.period_end,
            )
        )
    return tuple(result)
