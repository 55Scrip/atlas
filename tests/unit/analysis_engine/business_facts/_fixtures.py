"""Shared test fixtures for the Business Facts test suite."""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.business_data.models import RawBusinessDocument

EVALUATED_AT = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)


def build_record(
    *,
    identifier: str = "fy2024",
    company: str = "ASML",
    period_end: date | None = date(2024, 12, 31),
    period_start: date | None = None,
    metadata: dict | None = None,
) -> BusinessRecord:
    document = RawBusinessDocument(
        identifier=identifier,
        company=company,
        source_kind="annual_report",
        published_at=EVALUATED_AT,
        provider_id="structured_test_provider",
        raw_reference=f"ref://{identifier}",
        content_hash=f"hash-{identifier}",
        language="en",
        period_end=period_end,
        period_start=period_start,
        metadata=metadata or {},
    )
    result = ingest(document, evaluated_at=EVALUATED_AT)
    assert isinstance(result, IngestedRecord), result
    return result.record
