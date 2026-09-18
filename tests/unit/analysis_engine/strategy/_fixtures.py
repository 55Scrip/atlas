"""Shared transcript builder for the strategy tests.

Every sentence used in these tests is either verbatim from a persisted
benchmark call or a minimal synthetic sentence written to isolate one
rule. Verbatim ones say so and name the company and quarter, so a reader
can go and check.
"""
from datetime import date, datetime, timezone

from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from tests.unit.analysis_engine.business_data._fixtures import build_raw_document

EVALUATED_AT = datetime(2026, 9, 9, tzinfo=timezone.utc)
COMPOSED_AT = datetime(2026, 9, 18, tzinfo=timezone.utc)

EXECUTIVE = "Executive Vice President & Chief Financial Officer"
ANALYST = "Analyst"
OPERATOR = "Operator"


def transcript(
    content: str,
    *,
    title: str = EXECUTIVE,
    company: str = "VST",
    quarter: str = "2026Q2",
    index: int = 0,
    period_end: date | None = date(2026, 6, 30),
):
    result = ingest(
        build_raw_document(
            identifier=f"{company}:transcript:{quarter}:{index}",
            company=company,
            source_kind="transcript",
            published_at=EVALUATED_AT,
            period_start=period_end,
            period_end=period_end,
            content_hash=f"{company}{quarter}{index}",
            metadata={
                "quarter": quarter,
                "statement_index": index,
                "speaker": "Test Speaker",
                "title": title,
                "content": content,
            },
        ),
        evaluated_at=EVALUATED_AT,
    )
    assert isinstance(result, IngestedRecord)
    return result.record


def filing(content: str, *, company: str = "VST"):
    result = ingest(
        build_raw_document(
            identifier=f"{company}:10-Q:2026Q2",
            company=company,
            source_kind="company_filing",
            published_at=EVALUATED_AT,
            period_end=date(2026, 6, 30),
            content_hash=f"{company}filing",
            metadata={"content": content},
        ),
        evaluated_at=EVALUATED_AT,
    )
    assert isinstance(result, IngestedRecord)
    return result.record
