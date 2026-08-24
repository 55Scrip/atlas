"""Tests for `atlas.alpha.ingestion.repository
.SqlAlchemyIngestionResultRepository` -- round-trip fidelity, and
`get_by_ticker` (Automatic Enrichment Coverage, Implementation Phase 1).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.models import ProviderFailure
from atlas.alpha.ingestion.models import IngestionResult
from atlas.alpha.ingestion.repository import SqlAlchemyIngestionResultRepository
from atlas.alpha.ingestion.table import create_ingestion_result_table

EARLIER = datetime(2026, 1, 1, tzinfo=timezone.utc)
LATER = datetime(2026, 1, 2, tzinfo=timezone.utc)


def _engine():
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_ingestion_result_table(engine)
    return engine


def _result(*, case_id: str, ticker: str, ran_at: datetime, provider_failures: tuple = ()) -> IngestionResult:
    return IngestionResult(
        ticker=ticker,
        case_id=case_id,
        ran_at=ran_at,
        changes=(),
        has_new_data=False,
        fetched_documents=1,
        duplicates_skipped=0,
        rejected_documents=0,
        provider_errors=(),
        identity_gate_outcome="AUTO_ACCEPT",
        provider_failures=provider_failures,
    )


class TestProviderFailuresRoundTrip:
    def test_provider_failures_survive_a_round_trip(self):
        repository = SqlAlchemyIngestionResultRepository(_engine())
        failures = (
            ProviderFailure(provider_id="SecEdgarFundamentalsProvider", error="no us-gaap facts", kind="MissingRequiredField"),
        )
        repository.upsert(_result(case_id="case-1", ticker="ASML", ran_at=EARLIER, provider_failures=failures))
        fetched = repository.get(case_id="case-1")
        assert fetched.provider_failures == failures

    def test_a_result_persisted_before_this_field_existed_defaults_to_empty(self):
        """`provider_failures` defaults to `()` -- a row from before this
        field existed round-trips as an empty tuple, never an error."""
        repository = SqlAlchemyIngestionResultRepository(_engine())
        repository.upsert(_result(case_id="case-1", ticker="ASML", ran_at=EARLIER))
        fetched = repository.get(case_id="case-1")
        assert fetched.provider_failures == ()


class TestGetByTicker:
    def test_returns_none_for_an_unknown_ticker(self):
        repository = SqlAlchemyIngestionResultRepository(_engine())
        assert repository.get_by_ticker("ASML") is None

    def test_returns_the_result_for_a_known_ticker(self):
        repository = SqlAlchemyIngestionResultRepository(_engine())
        repository.upsert(_result(case_id="case-1", ticker="ASML", ran_at=EARLIER))
        fetched = repository.get_by_ticker("ASML")
        assert fetched is not None
        assert fetched.case_id == "case-1"

    def test_multiple_case_ids_for_the_same_ticker_returns_the_most_recent(self):
        """The real condition this sprint's own live verification found:
        a ticker's Case identity was re-resolved over time, leaving more
        than one `IngestionResult` row for the identical ticker string.
        `get_by_ticker` must never return an arbitrary/stale one -- an
        earlier, unordered implementation returned whichever row SQLite
        happened to store first, silently resurrecting an out-of-date
        `provider_failures` history for a ticker whose Case identity had
        since moved on."""
        repository = SqlAlchemyIngestionResultRepository(_engine())
        stale_failure = (
            ProviderFailure(provider_id="AlphaVantageMarketDataProvider.fetch_company_profile", error="stale", kind="MissingRequiredField"),
        )
        current_failure = (
            ProviderFailure(provider_id="SecEdgarFundamentalsProvider", error="no us-gaap facts", kind="MissingRequiredField"),
        )
        repository.upsert(_result(case_id="stale-case", ticker="ASML", ran_at=EARLIER, provider_failures=stale_failure))
        repository.upsert(_result(case_id="current-case", ticker="ASML", ran_at=LATER, provider_failures=current_failure))

        fetched = repository.get_by_ticker("ASML")
        assert fetched.case_id == "current-case"
        assert fetched.provider_failures == current_failure

    def test_insertion_order_does_not_affect_which_one_is_returned(self):
        """Same scenario, rows upserted in the opposite (chronologically
        reversed) order -- proves the ordering is by `ran_at`, never by
        insertion/rowid order."""
        repository = SqlAlchemyIngestionResultRepository(_engine())
        repository.upsert(_result(case_id="current-case", ticker="ASML", ran_at=LATER))
        repository.upsert(_result(case_id="stale-case", ticker="ASML", ran_at=EARLIER))

        fetched = repository.get_by_ticker("ASML")
        assert fetched.case_id == "current-case"
