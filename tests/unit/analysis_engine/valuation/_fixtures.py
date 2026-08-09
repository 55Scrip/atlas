"""Shared test fixtures for the Valuation Engine test suite."""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

EVALUATED_AT = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)


def _make_record(
    *,
    source_kind: str,
    period_end: date,
    identifier: str,
    company: str = "ASML",
    metadata: dict | None = None,
    published_at: datetime | None = None,
) -> BusinessRecord:
    document = RawBusinessDocument(
        identifier=identifier,
        company=company,
        source_kind=source_kind,
        published_at=published_at if published_at is not None else EVALUATED_AT,
        provider_id="structured_test_provider",
        raw_reference=f"ref://{identifier}",
        content_hash=f"hash-{identifier}",
        language="en",
        period_end=period_end,
        metadata=metadata or {},
    )
    result = ingest(document, evaluated_at=EVALUATED_AT)
    assert isinstance(result, IngestedRecord), result
    return result.record


def fundamentals_record(
    *,
    period_end: date,
    identifier: str,
    company: str = "ASML",
    published_at: datetime | None = None,
    **metadata,
) -> BusinessRecord:
    return _make_record(
        source_kind="annual_report",
        period_end=period_end,
        identifier=identifier,
        company=company,
        metadata=metadata,
        published_at=published_at,
    )


def market_record(
    *,
    period_end: date,
    identifier: str,
    company: str = "ASML",
    published_at: datetime | None = None,
    **metadata,
) -> BusinessRecord:
    return _make_record(
        source_kind="market_data_snapshot",
        period_end=period_end,
        identifier=identifier,
        company=company,
        metadata=metadata,
        published_at=published_at,
    )
