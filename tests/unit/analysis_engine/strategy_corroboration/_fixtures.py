"""Fixtures for the corroboration tests.

Financial figures are the benchmark companies' real reported numbers, so
a test that passes here is a test that passes against the corpus. Where a
case does not occur in the corpus -- a company whose stated outcome moved
against it -- the numbers are still real ones, recombined, and the test
says so.
"""
from datetime import date, datetime, timezone

from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from tests.unit.analysis_engine.strategy_salience._fixtures import call  # noqa: F401

EVALUATED_AT = datetime(2026, 9, 18, tzinfo=timezone.utc)
COMPOSED_AT = EVALUATED_AT


def financials(metadata, *, company="VST", period_end=date(2025, 12, 31),
               published_at=datetime(2026, 2, 27, tzinfo=timezone.utc), identifier=None):
    """One filed statement carrying reported figures."""
    document = RawBusinessDocument(
        identifier=identifier or f"{company}-fy{period_end.year}",
        company=company,
        source_kind="financial_statement",
        published_at=published_at,
        provider_id="structured_test_provider",
        raw_reference=f"ref://{company}/{period_end}",
        content_hash=f"hash-{company}-{period_end}-{sorted(metadata.items(), key=str)}",
        language="en",
        period_end=period_end,
        metadata=metadata,
    )
    result = ingest(document, evaluated_at=EVALUATED_AT)
    assert isinstance(result, IngestedRecord), result
    return result.record
