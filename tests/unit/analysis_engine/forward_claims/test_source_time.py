"""Forward-Looking Evidence, Stage 3.1 -- transcript temporal semantics.

A transcript record carries a fiscal reporting period, an evaluation
("as of") instant and an ingestion time. None of the three is when
management spoke, and Alpha Vantage supplies no call date. These tests
pin that Atlas never manufactures one: chronology between one company's
calls comes from their periods, and a statement's age is unknown unless
a source states it.
"""
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

import pytest

from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.forward_claims import (
    NonRevisionReason,
    RevisionType,
    compare_claims,
    detect_revisions,
    extract_forward_claims,
    period_ordinal,
    statement_age,
    transcript_period,
)
from tests.unit.analysis_engine.business_data._fixtures import build_raw_document

EXTRACTED = datetime(2026, 9, 11, tzinfo=timezone.utc)
AS_OF = datetime(2026, 9, 11, tzinfo=timezone.utc)


def call(content: str, *, company: str, quarter: object, published_at: datetime, period_end: date | None,
         index: int = 0, ingested_at: datetime | None = None):
    """One transcript statement as Atlas stores it: the provider's label,
    the provider-stamped as-of instant, and Atlas's calendar period."""
    result = ingest(
        build_raw_document(
            identifier=f"{company}:transcript:{quarter}:{index}",
            company=company,
            source_kind="transcript",
            published_at=published_at,
            period_start=period_end,
            period_end=period_end,
            content_hash=f"{company}-{quarter}-{index}",
            metadata={"quarter": quarter, "statement_index": index, "speaker": "A. Exec",
                      "title": "Chief Financial Officer", "content": content},
        ),
        evaluated_at=ingested_at or published_at,
    )
    assert isinstance(result, IngestedRecord)
    return result.record


def claims_of(*records):
    return tuple(c for r in records for c in extract_forward_claims(r, extracted_at=EXTRACTED)[0])


class TestThePeriodIsTheProvidersFiscalLabel:
    def test_a_calendar_year_company_is_placed_by_its_label(self):
        record = call("We expect 2027 revenue of $10 billion.", company="GOOGL", quarter="2026Q2",
                      published_at=datetime(2026, 8, 25, tzinfo=timezone.utc), period_end=date(2026, 6, 30))
        (claim,) = claims_of(record)
        assert claim.source_period == "2026Q2"
        assert claim.statement_at is None

    def test_a_non_calendar_fiscal_company_keeps_its_fiscal_label_not_a_calendar_date(self):
        """CRM's "2025Q3" is its Fiscal 2025 Third Quarter. Atlas stored a
        calendar 2025-09-30 period end and a backfill-chosen 2025-12-12;
        the claim carries neither."""
        record = call(
            "We expect fiscal year 2026 revenue of $40.5 billion to $40.9 billion.",
            company="CRM", quarter="2025Q3",
            published_at=datetime(2025, 12, 12, 16, 6, 28, tzinfo=timezone.utc), period_end=date(2025, 9, 30),
        )
        (claim,) = claims_of(record)
        assert claim.source_period == "2025Q3"
        assert claim.statement_at is None
        assert claim.horizon_period == "2026"

    def test_a_date_in_the_text_is_not_turned_into_a_statement_time_by_guesswork(self):
        """NVIDIA's real "2025Q3" call says "All our statements are made as
        of today, November 20, 2024" -- ten months before the calendar end
        Atlas stored. Atlas neither uses that period end nor parses free
        text into a date: the statement time stays unknown."""
        record = call(
            "All our statements are made as of today, November 20, 2024. We expect fiscal 2026 revenue of "
            "$150 billion.",
            company="NVDA", quarter="2025Q3",
            published_at=datetime(2025, 12, 12, tzinfo=timezone.utc), period_end=date(2025, 9, 30),
        )
        (claim,) = claims_of(record)
        assert claim.source_period == "2025Q3"
        assert claim.statement_at is None

    @pytest.mark.parametrize("label", ["x", "2025-Q3", "Q3 2025", "2025Q5", "", 20253, None])
    def test_a_label_not_in_the_providers_form_is_no_period_at_all(self, label):
        record = call("We expect 2027 revenue of $10 billion.", company="ACME", quarter=label if label is not None else "",
                      published_at=datetime(2026, 8, 25, tzinfo=timezone.utc), period_end=None)
        assert transcript_period(record) is None

    def test_periods_order_across_a_year_boundary(self):
        assert period_ordinal("2025Q4") < period_ordinal("2026Q1") < period_ordinal("2026Q2")
        assert period_ordinal(None) is None and period_ordinal("2026-Q1") is None


class TestChronologyWithoutDates:
    def _pair(self, first_published: datetime, second_published: datetime):
        q1 = call("We expect 2027 revenue of $10 billion.", company="ACME", quarter="2026Q1",
                  published_at=first_published, period_end=None)
        q2 = call("We expect 2027 revenue of $11 billion.", company="ACME", quarter="2026Q2",
                  published_at=second_published, period_end=None)
        return claims_of(q1, q2)

    def test_two_calls_with_ordered_periods_and_unknown_statement_dates_are_ordered(self):
        claims = self._pair(datetime(2026, 6, 1, tzinfo=timezone.utc), datetime(2026, 9, 1, tzinfo=timezone.utc))
        (revision,), _ = detect_revisions(claims)
        assert revision.revision_type is RevisionType.RAISED
        assert (revision.evidence[0].prior_source_period, revision.new_source_period) == ("2026Q1", "2026Q2")

    def test_fetch_order_opposite_to_fiscal_order_never_reverses_the_revision(self):
        """A backfill fetches an older call later than a newer one. Ordered
        by fetch time, 11 -> 10 would read as a cut."""
        claims = self._pair(datetime(2026, 9, 11, tzinfo=timezone.utc), datetime(2026, 8, 25, tzinfo=timezone.utc))
        (revision,), _ = detect_revisions(claims)
        assert revision.revision_type is RevisionType.RAISED

    def test_calls_fetched_in_the_same_instant_are_still_ordered(self):
        same = datetime(2026, 9, 11, tzinfo=timezone.utc)
        (revision,), _ = detect_revisions(self._pair(same, same))
        assert revision.revision_type is RevisionType.RAISED

    def test_two_claims_from_the_same_period_are_ambiguous(self):
        a, b = self._pair(datetime(2026, 6, 1, tzinfo=timezone.utc), datetime(2026, 9, 1, tzinfo=timezone.utc))
        b = replace(b, source_period=a.source_period)
        assert compare_claims(a, b).reason is NonRevisionReason.AMBIGUOUS_ORDER

    def test_a_claim_without_a_period_is_never_ordered_by_its_timestamps(self):
        a, b = self._pair(datetime(2026, 6, 1, tzinfo=timezone.utc), datetime(2026, 9, 1, tzinfo=timezone.utc))
        assert compare_claims(a, replace(b, source_period=None)).reason is NonRevisionReason.AMBIGUOUS_ORDER
        assert compare_claims(replace(a, source_period=None), b).reason is NonRevisionReason.AMBIGUOUS_ORDER


class TestStatementAge:
    def _claim(self, **overrides):
        record = call("We expect 2027 revenue of $10 billion.", company="ACME", quarter="2025Q3",
                      published_at=datetime(2025, 12, 12, tzinfo=timezone.utc), period_end=date(2025, 9, 30),
                      ingested_at=datetime(2026, 9, 11, tzinfo=timezone.utc))
        (claim,) = claims_of(record)
        return replace(claim, **overrides)

    def test_staleness_is_refused_when_no_source_says_when_management_spoke(self):
        assert statement_age(self._claim(), as_of=AS_OF) is None

    def test_an_evaluation_date_long_after_the_call_changes_nothing(self):
        """Evaluated "as of" 2025-12-12, ingested 2026-09-11: neither is a
        statement time, so there is still no age."""
        assert statement_age(self._claim(), as_of=AS_OF + timedelta(days=400)) is None

    def test_a_known_statement_time_gives_a_real_age(self):
        spoke = datetime(2024, 11, 20, tzinfo=timezone.utc)
        assert statement_age(self._claim(statement_at=spoke), as_of=AS_OF) == AS_OF - spoke

    def test_age_is_measured_from_the_statement_never_from_extraction_or_ingestion(self):
        spoke = datetime(2024, 11, 20, tzinfo=timezone.utc)
        claim = self._claim(statement_at=spoke)
        assert statement_age(claim, as_of=AS_OF) != AS_OF - claim.extracted_at
