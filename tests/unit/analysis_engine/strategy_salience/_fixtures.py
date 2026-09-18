"""Transcript builder for the salience tests.

Builds whole calls rather than single statements, because the signals
under test -- the prepared/Q&A boundary, speaker breadth, analyst
attention -- are properties of a call's structure and cannot be
exercised one statement at a time.
"""
from datetime import date, datetime, timezone

from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from tests.unit.analysis_engine.business_data._fixtures import build_raw_document

EVALUATED_AT = datetime(2026, 9, 9, tzinfo=timezone.utc)
COMPOSED_AT = datetime(2026, 9, 18, tzinfo=timezone.utc)

CEO = "President and Chief Executive Officer"
CFO = "Executive Vice President and Chief Financial Officer"
IR = "Head of Investor Relations"
ANALYST = "Analyst"
OPERATOR = "Operator"


def statement(content, *, title=CEO, speaker="Pat Lee", company="VST",
              quarter="2026Q2", index=0, period_end=date(2026, 6, 30)):
    result = ingest(
        build_raw_document(
            identifier=f"{company}:transcript:{quarter}:{index}",
            company=company,
            source_kind="transcript",
            published_at=EVALUATED_AT,
            period_start=period_end,
            period_end=period_end,
            content_hash=f"{company}{quarter}{index}",
            metadata={"quarter": quarter, "statement_index": index, "speaker": speaker,
                      "title": title, "content": content},
        ),
        evaluated_at=EVALUATED_AT,
    )
    assert isinstance(result, IngestedRecord)
    return result.record


def call(*turns, company="VST", quarter="2026Q2"):
    """A call from a list of (title, speaker, content) turns, indexed in
    order -- which is what makes the prepared/Q&A split real."""
    return tuple(
        statement(content, title=title, speaker=speaker, company=company,
                  quarter=quarter, index=i)
        for i, (title, speaker, content) in enumerate(turns)
    )
