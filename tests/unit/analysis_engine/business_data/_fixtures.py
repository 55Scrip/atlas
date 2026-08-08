"""Shared test fixtures for the Business Data Ingestion test suite."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.analysis_engine.business_data.models import RawBusinessDocument

EVALUATED_AT = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)


def build_raw_document(
    *,
    identifier: str | None = "10-K-2025",
    company: str | None = "ASML",
    source_kind: str | None = "annual_report",
    published_at: datetime | None = EVALUATED_AT,
    provider_id: str | None = "manual_upload",
    raw_reference: str | None = "file://asml-10k-2025.pdf",
    content_hash: str | None = "a1b2c3",
    language: str | None = "en",
    period_start=None,
    period_end=None,
    metadata: dict | None = None,
) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=identifier,
        company=company,
        source_kind=source_kind,
        published_at=published_at,
        provider_id=provider_id,
        raw_reference=raw_reference,
        content_hash=content_hash,
        language=language,
        period_start=period_start,
        period_end=period_end,
        metadata=metadata or {},
    )
