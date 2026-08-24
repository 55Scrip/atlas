"""`price_refresh.py` tests (Internal Alpha Stabilization 1, MSFT price
root cause fix). Real in-memory SQLite repository/quota tracker, real
`AlphaVantageMarketDataProvider` against a fake fetcher (no live
network) -- matching this package's own established real-harness
testing discipline.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.price_refresh import (
    PriceRefreshCoordinator,
    price_freshness_status,
    refresh_price_only,
)
from atlas.alpha.business_data_refresh.quota import AlphaVantageQuotaTracker
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.analysis_engine.business_data.contracts import ValidationStatus
from atlas.analysis_engine.business_data.models import BusinessRecord, RecordVersion
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.provenance import Consumer, Provenance
from atlas.analysis_engine.provenance import SourceKind as ProvenanceSourceKind
from atlas.analysis_engine.provenance import UpdateTrigger
from atlas.business_data_providers.alpha_vantage import AlphaVantageMarketDataProvider
from atlas.business_data_providers.errors import RateLimited

_NOW = datetime(2026, 8, 24, 12, tzinfo=timezone.utc)
_STALE_TRADING_DAY = date(2026, 8, 7)


def _fake_fetcher(responses: dict[str, object]):
    def fetcher(url: str, headers: dict | None) -> object:
        for key, value in responses.items():
            if key in url:
                return value
        raise AssertionError(f"unexpected URL in test: {url}")

    return fetcher


def _snapshot_record(
    *, company: str = "MSFT", share_price: float = 499.99, trading_day: date = _STALE_TRADING_DAY, currency: str | None = "USD"
) -> BusinessRecord:
    lineage_id = f"lineage:{company}:snapshot"
    metadata = {"share_price": share_price, "shares_outstanding": 7425545000.0}
    if currency is not None:
        metadata["currency"] = currency
    return BusinessRecord(
        id=f"{lineage_id}:v1",
        lineage_id=lineage_id,
        identifier=f"{company}:snapshot:{trading_day.isoformat()}",
        company=company,
        document_type=SourceKind.MARKET_DATA_SNAPSHOT,
        published_at=datetime.combine(trading_day, datetime.min.time(), tzinfo=timezone.utc),
        provider_id="alpha_vantage",
        source_reference="https://example.test/quote",
        content_hash=f"hash-{share_price}-{trading_day}",
        version=RecordVersion(version_number=1, created_at=_NOW, content_hash=f"hash-{share_price}-{trading_day}", supersedes=None),
        provenance=Provenance(
            source_kind=ProvenanceSourceKind.EXTERNAL_DATA_SOURCE,
            source_references=("https://example.test/quote",),
            dependencies=(),
            update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
            consumers=(Consumer.PORTFOLIO_PAGE, Consumer.INVESTMENT_CASE_PAGE, Consumer.DISCOVERY, Consumer.HISTORY),
            computed_at=_NOW,
        ),
        validation_status=ValidationStatus.VALID,
        period_start=trading_day,
        period_end=trading_day,
        language="en",
        metadata=metadata,
        canonical_security_id="canonical:msft",
        resolution_version="v1",
        identity_resolved_at=_NOW,
        provider_evidence_reference="evidence:msft",
    )


@pytest.fixture
def engine() -> Engine:
    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})
    create_business_record_table(engine)
    return engine


@pytest.fixture
def repository(engine) -> SqlAlchemyBusinessRecordRepository:
    return SqlAlchemyBusinessRecordRepository(engine)


@pytest.fixture
def quota(engine) -> AlphaVantageQuotaTracker:
    return AlphaVantageQuotaTracker(engine)


@pytest.fixture
def coordinator() -> PriceRefreshCoordinator:
    return PriceRefreshCoordinator()


def _provider(responses: dict[str, object], *, on_request=None) -> AlphaVantageMarketDataProvider:
    return AlphaVantageMarketDataProvider(_fake_fetcher(responses), api_key="k", on_request=on_request)


_FRESH_QUOTE_RESPONSE = {
    "GLOBAL_QUOTE": {"Global Quote": {"05. price": "483.24", "07. latest trading day": "2026-08-24"}}
}


class TestPriceRefreshCoordinator:
    def test_try_start_claims_and_second_call_is_deduped(self, coordinator):
        assert coordinator.try_start("MSFT") is True
        assert coordinator.try_start("MSFT") is False

    def test_a_different_ticker_is_never_blocked_by_another_tickers_in_flight_claim(self, coordinator):
        assert coordinator.try_start("MSFT") is True
        assert coordinator.try_start("AAPL") is True

    def test_finish_releases_the_claim_so_a_later_call_can_start_again(self, coordinator):
        coordinator.try_start("MSFT")
        coordinator.finish("MSFT", succeeded=True)
        assert coordinator.try_start("MSFT") is True

    def test_finish_succeeded_clears_any_prior_failed_status(self, coordinator):
        coordinator.try_start("MSFT")
        coordinator.finish("MSFT", succeeded=False)
        assert coordinator.has_recently_failed("MSFT") is True
        coordinator.try_start("MSFT")
        coordinator.finish("MSFT", succeeded=True)
        assert coordinator.has_recently_failed("MSFT") is False

    def test_a_fresh_try_start_after_a_failure_clears_the_failed_flag_immediately(self, coordinator):
        coordinator.try_start("MSFT")
        coordinator.finish("MSFT", succeeded=False)
        assert coordinator.has_recently_failed("MSFT") is True
        coordinator.try_start("MSFT")
        assert coordinator.has_recently_failed("MSFT") is False

    def test_is_refreshing_reflects_in_flight_state(self, coordinator):
        assert coordinator.is_refreshing("MSFT") is False
        coordinator.try_start("MSFT")
        assert coordinator.is_refreshing("MSFT") is True
        coordinator.finish("MSFT", succeeded=True)
        assert coordinator.is_refreshing("MSFT") is False


class TestPriceFreshnessStatus:
    def test_refreshing_wins_over_everything_else(self, coordinator):
        coordinator.try_start("MSFT")
        status = price_freshness_status(trading_day=date(2026, 8, 24), ticker="MSFT", coordinator=coordinator, as_of=_NOW)
        assert status == "refreshing"

    def test_unavailable_when_no_trading_day_at_all(self, coordinator):
        status = price_freshness_status(trading_day=None, ticker="MSFT", coordinator=coordinator, as_of=_NOW)
        assert status == "unavailable"

    def test_fresh_when_trading_day_matches_the_latest_expected_trading_day(self, coordinator):
        status = price_freshness_status(trading_day=date(2026, 8, 21), ticker="MSFT", coordinator=coordinator, as_of=_NOW)
        assert status == "fresh"

    def test_stale_when_trading_day_is_behind_and_no_recent_failure(self, coordinator):
        status = price_freshness_status(trading_day=_STALE_TRADING_DAY, ticker="MSFT", coordinator=coordinator, as_of=_NOW)
        assert status == "stale"

    def test_failed_when_trading_day_is_behind_and_the_last_attempt_failed(self, coordinator):
        coordinator.try_start("MSFT")
        coordinator.finish("MSFT", succeeded=False)
        status = price_freshness_status(trading_day=_STALE_TRADING_DAY, ticker="MSFT", coordinator=coordinator, as_of=_NOW)
        assert status == "failed"

    def test_a_recent_failure_is_not_shown_once_the_price_is_actually_fresh(self, coordinator):
        """A failed status must never outlive its own relevance -- if
        someone else's successful refresh (or a new snapshot) makes the
        price fresh again, `failed` must not still be reported."""
        coordinator.try_start("MSFT")
        coordinator.finish("MSFT", succeeded=False)
        status = price_freshness_status(trading_day=date(2026, 8, 21), ticker="MSFT", coordinator=coordinator, as_of=_NOW)
        assert status == "fresh"


class TestRefreshPriceOnly:
    def test_successful_refresh_ingests_the_new_price_and_reports_ok(self, repository, quota, coordinator):
        repository.add(_snapshot_record())
        provider = _provider(_FRESH_QUOTE_RESPONSE)

        outcome = refresh_price_only(
            "MSFT", provider=provider, repository=repository, quota=quota, coordinator=coordinator, evaluated_at=_NOW
        )

        assert outcome.attempted is True
        assert outcome.succeeded is True
        assert outcome.reason == "ok"
        records = repository.get_by_company("MSFT")
        snapshots = [r for r in records if r.document_type is SourceKind.MARKET_DATA_SNAPSHOT]
        latest = max(snapshots, key=lambda r: r.published_at)
        assert latest.metadata["share_price"] == 483.24
        assert latest.period_end == date(2026, 8, 24)

    def test_successful_refresh_records_exactly_one_quota_call(self, repository, quota, coordinator):
        repository.add(_snapshot_record())
        provider = _provider(_FRESH_QUOTE_RESPONSE, on_request=quota.record_call)

        refresh_price_only("MSFT", provider=provider, repository=repository, quota=quota, coordinator=coordinator, evaluated_at=_NOW)

        assert quota.calls_used_today() == 1

    def test_no_prior_snapshot_is_not_attempted_and_never_calls_the_provider(self, repository, quota, coordinator):
        provider = _provider({"GLOBAL_QUOTE": AssertionError("must not be called")})

        outcome = refresh_price_only(
            "MSFT", provider=provider, repository=repository, quota=quota, coordinator=coordinator, evaluated_at=_NOW
        )

        assert outcome.attempted is False
        assert outcome.succeeded is False
        assert outcome.reason == "no_prior_snapshot"

    def test_no_confirmed_currency_on_file_is_not_attempted(self, repository, quota, coordinator):
        repository.add(_snapshot_record(currency=None))
        provider = _provider(_FRESH_QUOTE_RESPONSE)

        outcome = refresh_price_only(
            "MSFT", provider=provider, repository=repository, quota=quota, coordinator=coordinator, evaluated_at=_NOW
        )

        assert outcome.attempted is False
        assert outcome.reason == "no_confirmed_currency"

    def test_quota_exhausted_is_not_attempted_and_never_calls_the_provider(self, repository, coordinator, engine):
        repository.add(_snapshot_record())
        quota = AlphaVantageQuotaTracker(engine, daily_limit=1)
        quota.record_call()
        provider = _provider({"GLOBAL_QUOTE": AssertionError("must not be called")})

        outcome = refresh_price_only(
            "MSFT", provider=provider, repository=repository, quota=quota, coordinator=coordinator, evaluated_at=_NOW
        )

        assert outcome.attempted is False
        assert outcome.succeeded is False
        assert outcome.reason == "quota_exhausted"

    def test_already_refreshing_is_deduplicated_and_never_calls_the_provider(self, repository, quota, coordinator):
        repository.add(_snapshot_record())
        coordinator.try_start("MSFT")
        provider = _provider({"GLOBAL_QUOTE": AssertionError("must not be called")})

        outcome = refresh_price_only(
            "MSFT", provider=provider, repository=repository, quota=quota, coordinator=coordinator, evaluated_at=_NOW
        )

        assert outcome.attempted is False
        assert outcome.succeeded is False
        assert outcome.reason == "already_refreshing"

    def test_provider_error_is_reported_as_a_failed_attempt(self, repository, quota, coordinator):
        repository.add(_snapshot_record())
        provider = _provider({"GLOBAL_QUOTE": {"Information": "Thank you for using Alpha Vantage! ..."}})

        outcome = refresh_price_only(
            "MSFT", provider=provider, repository=repository, quota=quota, coordinator=coordinator, evaluated_at=_NOW
        )

        assert outcome.attempted is True
        assert outcome.succeeded is False

    def test_a_failed_refresh_never_destroys_or_alters_the_last_good_snapshot(self, repository, quota, coordinator):
        """The whole point of `refresh_price_only`'s synchronous,
        ingest-only-after-success design: a rate-limited/malformed
        provider response must leave the previously stored MSFT
        snapshot completely untouched, not discarded, not
        overwritten."""
        repository.add(_snapshot_record())
        before = repository.get_by_company("MSFT")
        provider = _provider({"GLOBAL_QUOTE": {"Information": "rate limited"}})

        refresh_price_only("MSFT", provider=provider, repository=repository, quota=quota, coordinator=coordinator, evaluated_at=_NOW)

        after = repository.get_by_company("MSFT")
        assert after == before
        snapshots = [r for r in after if r.document_type is SourceKind.MARKET_DATA_SNAPSHOT]
        assert len(snapshots) == 1
        assert snapshots[0].metadata["share_price"] == 499.99

    def test_coordinator_claim_is_always_released_even_after_a_provider_failure(self, repository, quota, coordinator):
        repository.add(_snapshot_record())
        provider = _provider({"GLOBAL_QUOTE": {"Information": "rate limited"}})

        refresh_price_only("MSFT", provider=provider, repository=repository, quota=quota, coordinator=coordinator, evaluated_at=_NOW)

        assert coordinator.is_refreshing("MSFT") is False
        assert coordinator.has_recently_failed("MSFT") is True

    def test_coordinator_claim_is_always_released_after_a_no_op_early_return(self, repository, coordinator, engine):
        """Even a `quota_exhausted`/`no_prior_snapshot`/`no_confirmed_
        currency` early return must still release the in-flight claim
        -- otherwise that ticker would be stuck reporting `refreshing`
        forever."""
        quota = AlphaVantageQuotaTracker(engine, daily_limit=0)
        provider = _provider({"GLOBAL_QUOTE": AssertionError("must not be called")})

        refresh_price_only("MSFT", provider=provider, repository=repository, quota=quota, coordinator=coordinator, evaluated_at=_NOW)

        assert coordinator.is_refreshing("MSFT") is False

    def test_identical_price_is_treated_as_a_successful_confirmation_not_a_failure(self, repository, quota, coordinator):
        """A `DuplicateRecord` ingestion result (identical price/trading
        day already stored, same real content hash) is still a real
        confirmation that the stored price is current -- must report
        `succeeded=True`, never be conflated with an actual failure."""
        probe_provider = _provider(_FRESH_QUOTE_RESPONSE)
        probe_document = probe_provider.fetch_price_only(
            company_identifier="MSFT", evaluated_at=_NOW, known_currency="USD", known_shares_outstanding=7425545000.0
        )
        from atlas.analysis_engine.business_data.versioning import compute_lineage_id

        lineage_id = compute_lineage_id(
            provider_id=probe_document.provider_id,
            source_kind=SourceKind.MARKET_DATA_SNAPSHOT,
            company=probe_document.company,
            identifier=probe_document.identifier,
        )
        pre_existing = _snapshot_record(share_price=483.24, trading_day=date(2026, 8, 24))
        object.__setattr__(pre_existing, "lineage_id", lineage_id)
        object.__setattr__(pre_existing, "id", f"{lineage_id}:v1")
        object.__setattr__(pre_existing.version, "content_hash", probe_document.content_hash)
        object.__setattr__(pre_existing, "content_hash", probe_document.content_hash)
        repository.add(pre_existing)

        outcome = refresh_price_only(
            "MSFT", provider=_provider(_FRESH_QUOTE_RESPONSE), repository=repository, quota=quota, coordinator=coordinator, evaluated_at=_NOW
        )

        assert outcome.attempted is True
        assert outcome.succeeded is True
        assert outcome.reason == "duplicaterecord"
