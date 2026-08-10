"""`refresh_company_data` tests (ATLAS-031, Phase 17/28).

Real in-memory SQLite persistence throughout; fake `BusinessDataProvider`
implementations (no network) standing in for the real SEC EDGAR/Alpha
Vantage providers -- the composition under test is the use case's own
orchestration logic (fetch -> ingest -> persist -> summarize), not any
one provider's parsing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.service import ensure_company_enriched, refresh_company_data
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.analysis_engine.business_data.models import RawBusinessDocument

_EVALUATED_AT = datetime(2026, 8, 9, tzinfo=timezone.utc)


@dataclass(frozen=True)
class _FakeProvider:
    """A minimal `BusinessDataProvider` conforming implementation --
    proves `refresh_company_data` depends only on the Protocol, never a
    concrete provider class."""

    documents: tuple[RawBusinessDocument, ...] = ()
    exception: Exception | None = None

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        if self.exception is not None:
            raise self.exception
        return tuple(d for d in self.documents if d.company == company_identifier)


def _doc(
    *,
    identifier: str,
    company: str = "AAPL",
    revenue: float = 100.0,
    content_hash: str | None = None,
    published_at: datetime = _EVALUATED_AT,
    source_kind: str = "financial_statement",
) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=identifier,
        company=company,
        source_kind=source_kind,
        published_at=published_at,
        provider_id="fake_provider",
        raw_reference="https://example.test/doc",
        content_hash=content_hash or f"hash-{revenue}",
        language="en",
        metadata={"revenue": revenue, "currency": "USD"},
    )


@dataclass(frozen=True)
class _FakeHistoricalProvider:
    """A `BusinessDataProvider` that additionally implements
    `fetch_historical_snapshots` -- structurally conforms to
    `HistoricalMarketDataProvider` with no import of that Protocol,
    proving `refresh_company_data`'s `isinstance` check is real
    duck-typing, not a hardcoded provider-class check."""

    current_documents: tuple[RawBusinessDocument, ...] = ()
    historical_documents: tuple[RawBusinessDocument, ...] = ()
    historical_exception: Exception | None = None
    received_filing_dates: list = field(default_factory=list)

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        return tuple(d for d in self.current_documents if d.company == company_identifier)

    def fetch_historical_snapshots(
        self, *, company_identifier: str, filing_dates: tuple[date, ...], evaluated_at: datetime
    ) -> tuple[RawBusinessDocument, ...]:
        self.received_filing_dates.append(filing_dates)
        if self.historical_exception is not None:
            raise self.historical_exception
        return tuple(d for d in self.historical_documents if d.company == company_identifier)


@pytest.fixture
def engine() -> Engine:
    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})
    create_business_record_table(engine)
    return engine


@pytest.fixture
def repository(engine) -> SqlAlchemyBusinessRecordRepository:
    return SqlAlchemyBusinessRecordRepository(engine)


@dataclass(frozen=True)
class _FakeCompanyProfileProvider:
    """(Investment Case Engine v1 slice) A `BusinessDataProvider` that
    additionally implements `fetch_company_profile` -- structurally
    conforms to `CompanyProfileProvider` with no import of that
    Protocol, mirroring `_FakeHistoricalProvider`'s own duck-typing
    proof for the historical-market-data capability."""

    current_documents: tuple[RawBusinessDocument, ...] = ()
    profile_documents: tuple[RawBusinessDocument, ...] = ()
    profile_exception: Exception | None = None
    profile_call_count: list = field(default_factory=list)

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        return tuple(d for d in self.current_documents if d.company == company_identifier)

    def fetch_company_profile(
        self, *, company_identifier: str, evaluated_at: datetime
    ) -> tuple[RawBusinessDocument, ...]:
        self.profile_call_count.append(company_identifier)
        if self.profile_exception is not None:
            raise self.profile_exception
        return tuple(d for d in self.profile_documents if d.company == company_identifier)


def _profile_doc(*, company: str = "AAPL", name: str = "Apple Inc.", sector: str = "Technology") -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=f"{company}:profile",
        company=company,
        source_kind="company_profile",
        published_at=_EVALUATED_AT,
        provider_id="fake_provider",
        raw_reference="https://example.test/profile",
        content_hash=f"profile-hash-{name}",
        language="en",
        metadata={"name": name, "sector": sector},
    )


class TestBasicRefresh:
    def test_fresh_company_produces_new_records_and_persists_them(self, repository):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2022"), _doc(identifier="AAPL:FY:2023", revenue=110.0)))
        summary = refresh_company_data("AAPL", (provider,), repository)

        assert summary.ticker == "AAPL"
        assert summary.fetched_documents == 2
        assert summary.new_records == 2
        assert summary.new_versions == 0
        assert summary.duplicates_skipped == 0
        assert summary.rejected_documents == 0
        assert summary.provider_errors == ()
        assert len(repository.get_by_company("AAPL")) == 2

    def test_malformed_document_is_rejected_not_persisted(self, repository):
        malformed = RawBusinessDocument(
            identifier=None, company="AAPL", source_kind="financial_statement",
            published_at=_EVALUATED_AT, provider_id="fake", raw_reference="x", content_hash="x",
        )
        provider = _FakeProvider(documents=(malformed,))
        summary = refresh_company_data("AAPL", (provider,), repository)
        assert summary.rejected_documents == 1
        assert summary.new_records == 0
        assert repository.get_by_company("AAPL") == ()


class TestIdempotency:
    def test_identical_refresh_run_twice_is_fully_idempotent(self, repository):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023"),))
        first = refresh_company_data("AAPL", (provider,), repository)
        second = refresh_company_data("AAPL", (provider,), repository)

        assert first.new_records == 1
        assert second.new_records == 0
        assert second.duplicates_skipped == 1
        assert len(repository.get_by_company("AAPL")) == 1

    def test_restated_value_produces_a_new_version_not_a_duplicate(self, repository):
        original = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", revenue=100.0),))
        refresh_company_data("AAPL", (original,), repository)

        restated = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", revenue=95.0, content_hash="hash-restated"),))
        summary = refresh_company_data("AAPL", (restated,), repository)

        assert summary.new_versions == 1
        assert summary.new_records == 0
        records = repository.get_by_company("AAPL")
        assert len(records) == 2  # both versions preserved, old one untouched
        latest = next(r for r in records if r.version.version_number == 2)
        assert latest.metadata["revenue"] == 95.0
        original_record = next(r for r in records if r.version.version_number == 1)
        assert original_record.metadata["revenue"] == 100.0  # immutable, never overwritten


class TestProviderFailureIsolation:
    def test_one_providers_failure_never_blocks_another_providers_documents(self, repository):
        failing = _FakeProvider(exception=RuntimeError("provider unavailable"))
        working = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023"),))
        summary = refresh_company_data("AAPL", (failing, working), repository)

        assert summary.new_records == 1
        assert len(summary.provider_errors) == 1
        assert summary.provider_errors[0].provider_id == "_FakeProvider"
        assert "provider unavailable" in summary.provider_errors[0].error
        assert len(repository.get_by_company("AAPL")) == 1

    def test_all_providers_failing_produces_a_summary_with_zero_documents_not_a_crash(self, repository):
        failing_a = _FakeProvider(exception=RuntimeError("timeout"))
        failing_b = _FakeProvider(exception=RuntimeError("company not found"))
        summary = refresh_company_data("ZZZZ", (failing_a, failing_b), repository)

        assert summary.fetched_documents == 0
        assert summary.new_records == 0
        assert len(summary.provider_errors) == 2


class TestCrossCompanyIsolation:
    def test_refreshing_one_company_never_touches_another_companys_records(self, repository):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", company="AAPL"),))
        refresh_company_data("AAPL", (provider,), repository)
        refresh_company_data("MSFT", (provider,), repository)  # provider has no MSFT docs

        assert len(repository.get_by_company("AAPL")) == 1
        assert repository.get_by_company("MSFT") == ()


class TestHistoricalMarketDataCapability:
    """ATLAS-032, Phase 7 -- the optional second pass for any provider
    that also implements `HistoricalMarketDataProvider`, checked via
    `isinstance`, never a hardcoded provider-class name."""

    def test_provider_without_the_capability_is_never_asked_for_history(self, repository):
        """`_FakeProvider` (used throughout this file) has no
        `fetch_historical_snapshots` -- `refresh_company_data` must not
        error or otherwise treat it specially."""
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023"),))
        summary = refresh_company_data("AAPL", (provider,), repository)
        assert summary.provider_errors == ()
        assert summary.new_records == 1

    def test_no_known_filing_dates_skips_the_historical_call_entirely(self, repository):
        """No FINANCIAL_STATEMENT record exists yet for this company
        (a market-data-only refresh) -- there is nothing to sample
        historical prices around, so the provider is never called."""
        historical_provider = _FakeHistoricalProvider(
            current_documents=(_doc(identifier="AAPL:snap", source_kind="market_data_snapshot"),)
        )
        refresh_company_data("AAPL", (historical_provider,), repository)
        assert historical_provider.received_filing_dates == []

    def test_historical_provider_receives_the_real_known_filing_dates(self, repository):
        fundamentals_provider = _FakeProvider(
            documents=(
                _doc(identifier="AAPL:FY:2022", published_at=datetime(2023, 2, 15, tzinfo=timezone.utc)),
                _doc(identifier="AAPL:FY:2023", published_at=datetime(2024, 2, 15, tzinfo=timezone.utc)),
            )
        )
        historical_provider = _FakeHistoricalProvider(
            historical_documents=(
                _doc(
                    identifier="AAPL:hist:2023-02-28",
                    source_kind="market_data_snapshot",
                    published_at=datetime(2023, 2, 28, tzinfo=timezone.utc),
                    content_hash="hist-1",
                ),
            )
        )
        summary = refresh_company_data("AAPL", (fundamentals_provider, historical_provider), repository)

        assert historical_provider.received_filing_dates == [(date(2023, 2, 15), date(2024, 2, 15))]
        assert summary.provider_errors == ()
        assert summary.new_records == 3  # 2 fundamentals + 1 historical snapshot
        market_records = [r for r in repository.get_by_company("AAPL") if r.document_type.value == "market_data_snapshot"]
        assert len(market_records) == 1

    def test_filing_dates_include_already_persisted_records_from_a_prior_run(self, repository):
        """A second refresh should sample history using fundamentals
        already in the repository, not only ones fetched this run."""
        fundamentals_provider = _FakeProvider(
            documents=(_doc(identifier="AAPL:FY:2022", published_at=datetime(2023, 2, 15, tzinfo=timezone.utc)),)
        )
        refresh_company_data("AAPL", (fundamentals_provider,), repository)

        historical_provider = _FakeHistoricalProvider()
        refresh_company_data("AAPL", (historical_provider,), repository)
        assert historical_provider.received_filing_dates == [(date(2023, 2, 15),)]

    def test_historical_failure_is_isolated_and_reported_distinctly(self, repository):
        fundamentals_provider = _FakeProvider(
            documents=(_doc(identifier="AAPL:FY:2022", published_at=datetime(2023, 2, 15, tzinfo=timezone.utc)),)
        )
        historical_provider = _FakeHistoricalProvider(historical_exception=RuntimeError("rate limited"))
        summary = refresh_company_data("AAPL", (fundamentals_provider, historical_provider), repository)

        assert summary.new_records == 1  # the fundamentals record still persisted
        assert len(summary.provider_errors) == 1
        assert summary.provider_errors[0].provider_id == "_FakeHistoricalProvider.fetch_historical_snapshots"
        assert "rate limited" in summary.provider_errors[0].error

    def test_duplicate_historical_documents_are_skipped_not_duplicated_on_rerun(self, repository):
        fundamentals_provider = _FakeProvider(
            documents=(_doc(identifier="AAPL:FY:2022", published_at=datetime(2023, 2, 15, tzinfo=timezone.utc)),)
        )
        historical_provider = _FakeHistoricalProvider(
            historical_documents=(
                _doc(
                    identifier="AAPL:hist:2023-02-28",
                    source_kind="market_data_snapshot",
                    published_at=datetime(2023, 2, 28, tzinfo=timezone.utc),
                    content_hash="hist-1",
                ),
            )
        )
        refresh_company_data("AAPL", (fundamentals_provider, historical_provider), repository)
        second = refresh_company_data("AAPL", (fundamentals_provider, historical_provider), repository)
        assert second.duplicates_skipped == 2  # the fundamentals record and the historical snapshot both repeat
        assert second.new_records == 0


class TestCompanyProfileCapability:
    """(Investment Case Engine v1 slice) The third, optional
    `CompanyProfileProvider` pass -- proves `refresh_company_data`
    detects it via duck typing (never a hardcoded provider class),
    isolates its failures distinctly from the other two passes, and
    persists what it returns through the identical ingestion pipeline."""

    def test_a_conforming_provider_gets_its_profile_ingested(self, repository):
        provider = _FakeCompanyProfileProvider(profile_documents=(_profile_doc(),))
        summary = refresh_company_data("AAPL", (provider,), repository)

        assert summary.new_records == 1
        records = repository.get_by_company("AAPL")
        assert len(records) == 1
        assert records[0].document_type.value == "company_profile"
        assert records[0].metadata["name"] == "Apple Inc."

    def test_a_non_conforming_provider_is_silently_skipped_for_this_pass(self, repository):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023"),))
        summary = refresh_company_data("AAPL", (provider,), repository)
        assert summary.new_records == 1  # only the fundamentals record -- no profile pass attempted
        assert summary.provider_errors == ()

    def test_profile_failure_is_isolated_and_reported_distinctly(self, repository):
        fundamentals_provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023"),))
        profile_provider = _FakeCompanyProfileProvider(profile_exception=RuntimeError("overview unavailable"))
        summary = refresh_company_data("AAPL", (fundamentals_provider, profile_provider), repository)

        assert summary.new_records == 1  # the fundamentals record still persisted
        assert len(summary.provider_errors) == 1
        assert summary.provider_errors[0].provider_id == "_FakeCompanyProfileProvider.fetch_company_profile"
        assert "overview unavailable" in summary.provider_errors[0].error

    def test_empty_profile_result_produces_no_record_and_no_error(self, repository):
        """A provider that legitimately has no identity fields for this
        company returns `()`, not an exception -- never fabricated,
        never reported as a failure."""
        provider = _FakeCompanyProfileProvider(profile_documents=())
        summary = refresh_company_data("AAPL", (provider,), repository)
        assert summary.new_records == 0
        assert summary.provider_errors == ()
        assert repository.get_by_company("AAPL") == ()

    def test_repeated_refresh_of_the_same_profile_is_idempotent(self, repository):
        provider = _FakeCompanyProfileProvider(profile_documents=(_profile_doc(),))
        first = refresh_company_data("AAPL", (provider,), repository)
        second = refresh_company_data("AAPL", (provider,), repository)
        assert first.new_records == 1
        assert second.new_records == 0
        assert second.duplicates_skipped == 1
        assert len(repository.get_by_company("AAPL")) == 1


class TestEnsureCompanyEnriched:
    """(Investment Case Engine v1 slice) The idempotent, automatic-
    trigger wrapper Watchlist/Portfolio's own "add a company" write
    paths call. Proves the one freshness gate this sprint needs: no
    provider is ever called a second time for an already-enriched
    ticker."""

    def test_a_new_company_is_fetched_and_persisted(self, repository):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023"),))
        summary = ensure_company_enriched("AAPL", (provider,), repository)
        assert summary is not None
        assert summary.new_records == 1
        assert len(repository.get_by_company("AAPL")) == 1

    def test_an_already_enriched_company_makes_no_provider_call_at_all(self, repository):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023"),))
        ensure_company_enriched("AAPL", (provider,), repository)

        calling_provider = _FakeProvider(exception=AssertionError("must never be called"))
        result = ensure_company_enriched("AAPL", (calling_provider,), repository)
        assert result is None
        assert len(repository.get_by_company("AAPL")) == 1  # unchanged

    def test_a_different_ticker_is_still_fetched_independently(self, repository):
        provider = _FakeProvider(
            documents=(_doc(identifier="AAPL:FY:2023", company="AAPL"), _doc(identifier="MSFT:FY:2023", company="MSFT"))
        )
        ensure_company_enriched("AAPL", (provider,), repository)
        second = ensure_company_enriched("MSFT", (provider,), repository)
        assert second is not None
        assert second.new_records == 1
        assert len(repository.get_by_company("MSFT")) == 1

    def test_a_provider_failure_does_not_raise_and_still_returns_a_summary(self, repository):
        provider = _FakeProvider(exception=RuntimeError("SEC EDGAR unavailable"))
        summary = ensure_company_enriched("AAPL", (provider,), repository)
        assert summary is not None
        assert len(summary.provider_errors) == 1
        assert repository.get_by_company("AAPL") == ()

    def test_partial_provider_failure_still_persists_the_succeeding_provider(self, repository):
        """Missing SEC EDGAR coverage (a non-US filer, `CompanyNotFound`
        in the real provider) must not block Alpha Vantage's own market
        data from being persisted -- an expected data-availability
        condition, not a system failure."""
        failing_fundamentals = _FakeProvider(exception=RuntimeError("CompanyNotFound: not an SEC filer"))
        succeeding_market_data = _FakeProvider(
            documents=(_doc(identifier="XYZ:snapshot:2026-08-09", company="XYZ", source_kind="market_data_snapshot"),)
        )
        summary = ensure_company_enriched("XYZ", (failing_fundamentals, succeeding_market_data), repository)
        assert summary is not None
        assert len(summary.provider_errors) == 1
        assert summary.new_records == 1
        assert len(repository.get_by_company("XYZ")) == 1

    def test_a_company_with_only_a_stray_market_snapshot_is_not_treated_as_enriched(self, repository):
        """(Company Data Foundation v1) The exact "too coarse" gap this
        sprint fixes: a company whose only persisted record is a
        `MARKET_DATA_SNAPSHOT` (SEC failed, or the ticker is genuinely
        unsupported) must still retry on a later call -- the old "any
        record at all" gate would have permanently blocked this."""
        failing_fundamentals = _FakeProvider(exception=RuntimeError("CompanyNotFound: not an SEC filer"))
        succeeding_market_data = _FakeProvider(
            documents=(_doc(identifier="XYZ:snapshot:2026-08-09", company="XYZ", source_kind="market_data_snapshot"),)
        )
        first = ensure_company_enriched("XYZ", (failing_fundamentals, succeeding_market_data), repository)
        assert first is not None  # a real refresh happened

        second = ensure_company_enriched("XYZ", (failing_fundamentals, succeeding_market_data), repository)
        assert second is not None  # retried -- never became "enriched" from a market snapshot alone
        assert len(second.provider_errors) == 1

    def test_a_company_profile_alone_stops_further_retries(self, repository):
        """The bounding half of the same fix: the moment either
        provider succeeds with real identity or fundamentals, the
        ticker becomes minimally complete and stops retrying -- this
        never turns into an unbounded background poller."""
        profile_provider = _FakeCompanyProfileProvider(profile_documents=(_profile_doc(company="XYZ"),))
        ensure_company_enriched("XYZ", (profile_provider,), repository)
        assert len(profile_provider.profile_call_count) == 1

        calling_again = _FakeCompanyProfileProvider(profile_documents=(_profile_doc(company="XYZ"),))
        result = ensure_company_enriched("XYZ", (calling_again,), repository)
        assert result is None
        assert len(calling_again.profile_call_count) == 0  # never called -- already minimally complete

    def test_a_financial_statement_alone_stops_further_retries(self, repository):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", source_kind="financial_statement"),))
        ensure_company_enriched("AAPL", (provider,), repository)

        calling_again = _FakeProvider(exception=AssertionError("must never be called"))
        result = ensure_company_enriched("AAPL", (calling_again,), repository)
        assert result is None
