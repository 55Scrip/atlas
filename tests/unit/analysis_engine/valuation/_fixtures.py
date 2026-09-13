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


#: An operating-business industry: the FCF-yield method applies to it.
APPLICABLE_INDUSTRY = "SEMICONDUCTOR EQUIPMENT & MATERIALS"


def statement_record_ids(records) -> frozenset[str]:
    """The records the FCF-yield method may price: annual statements."""
    return frozenset(r.id for r in records if r.document_type.value == "financial_statement")


def valuation_inputs(business_facts) -> dict:
    """The FCF-yield method's eligibility inputs for facts built from these
    fixtures: every fundamentals fixture is an annual statement, and the
    industry is an operating business."""
    return {
        "statement_record_ids": frozenset(f.source_record_id for f in business_facts),
        "industry": APPLICABLE_INDUSTRY,
    }


def fundamentals_record(
    *,
    period_end: date,
    identifier: str,
    company: str = "ASML",
    published_at: datetime | None = None,
    **metadata,
) -> BusinessRecord:
    """An annual financial statement -- the only source whose free cash
    flow the FCF-yield method prices (Valuation Observation Integrity)."""
    return _make_record(
        source_kind="financial_statement",
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
