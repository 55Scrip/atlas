"""`refresh_company_data` tests (ATLAS-031, Phase 17/28).

Real in-memory SQLite persistence throughout; fake `BusinessDataProvider`
implementations (no network) standing in for the real SEC EDGAR/Alpha
Vantage providers -- the composition under test is the use case's own
orchestration logic (fetch -> ingest -> persist -> summarize), not any
one provider's parsing.

Sprint O: `refresh_company_data`/`ensure_company_enriched` now require
`identity_gate` and only ever ingest anything when it resolves to
`AUTO_ACCEPT`. `_IdentityProvider` below is a `CompanyProfileProvider`-
only fake supplying exactly the fields (company name, exchange,
country, currency, security type) needed to reach it -- added
alongside whatever fundamentals/market-data fake each test already
used. Every test whose premise was "a fundamentals-only provider set
successfully creates records" has been updated to add it and adjust
its expected counts (+1 record for the identity/profile document
itself, exactly as `TestCompanyProfileCapability`'s own pre-existing
tests already modeled for a real profile provider). Two tests whose
premise was specifically "a provider fails but progress still happens
without any identity" have been rewritten to assert the new, honest
behavior instead: with no identity source in the call, the Identity
Gate now blocks before any fundamentals/market-data provider is even
invoked -- see `TestProviderFailureIsolation
::test_all_providers_failing_produces_a_summary_with_zero_documents_not_a_crash`
and `TestEnsureCompanyEnriched
::test_a_company_with_only_a_stray_market_snapshot_is_not_treated_as_enriched`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.models import ProviderFailure
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.service import ensure_company_enriched, refresh_company_data
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.canonical_security_gate.factory import build_identity_gate
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.analysis_engine.business_data.models import RawBusinessDocument

_EVALUATED_AT = datetime(2026, 8, 9, tzinfo=timezone.utc)


@dataclass(frozen=True)
class _FakeProvider:
    """A minimal `BusinessDataProvider` conforming implementation --
    proves `refresh_company_data` depends only on the Protocol, never a
    concrete provider class. Deliberately does not implement
    `CompanyProfileProvider` -- tests that need identity add a separate
    `_IdentityProvider` to the same tuple."""

    documents: tuple[RawBusinessDocument, ...] = ()
    exception: Exception | None = None

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        if self.exception is not None:
            raise self.exception
        return tuple(d for d in self.documents if d.company == company_identifier)


@dataclass(frozen=True)
class _IdentityProvider:
    """Sprint O -- a `CompanyProfileProvider`-only fake supplying
    exactly the identity fields the Identity Gate needs to reach
    `AUTO_ACCEPT` (company name, exchange, country, currency, security
    type) for whichever tickers it is given. Kept independent of
    `_FakeProvider` so every existing fundamentals/market-data fake in
    this file keeps testing exactly what it always tested; identity is
    added to the provider tuple the same way a real
    `AlphaVantageMarketDataProvider` and a real
    `SecEdgarFundamentalsProvider` are two independent providers today.
    `content_hash` is deterministic per ticker, so a second call for
    the same ticker correctly produces a duplicate, not a new version.
    """

    tickers: tuple[str, ...]

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        return ()

    def fetch_company_profile(
        self, *, company_identifier: str, evaluated_at: datetime
    ) -> tuple[RawBusinessDocument, ...]:
        if company_identifier not in self.tickers:
            return ()
        return (
            RawBusinessDocument(
                identifier=f"{company_identifier}:identity-profile",
                company=company_identifier,
                source_kind="company_profile",
                published_at=evaluated_at,
                provider_id="alpha_vantage",
                raw_reference="https://example.test/identity-profile",
                content_hash=f"identity-hash-{company_identifier}",
                language="en",
                metadata={
                    "name": f"{company_identifier} Inc.",
                    "exchange": "NASDAQ",
                    "country": "USA",
                    "currency": "USD",
                    "security_type": "COMMON_STOCK",
                },
            ),
        )


def _identity_provider(*tickers: str) -> _IdentityProvider:
    return _IdentityProvider(tickers=tuple(tickers))


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


@dataclass(frozen=True)
class _FakeEarningsCallProvider:
    """A `BusinessDataProvider` that additionally implements
    `fetch_earnings_call_transcripts` -- structurally conforms to
    `EarningsCallTranscriptProvider` with no import of that Protocol,
    mirroring `_FakeHistoricalProvider`'s own duck-typing proof."""

    current_documents: tuple[RawBusinessDocument, ...] = ()
    transcript_documents: tuple[RawBusinessDocument, ...] = ()
    transcript_exception: Exception | None = None
    call_count: list = field(default_factory=list)

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        return tuple(d for d in self.current_documents if d.company == company_identifier)

    def fetch_earnings_call_transcripts(
        self, *, company_identifier: str, evaluated_at: datetime
    ) -> tuple[RawBusinessDocument, ...]:
        self.call_count.append(company_identifier)
        if self.transcript_exception is not None:
            raise self.transcript_exception
        return tuple(d for d in self.transcript_documents if d.company == company_identifier)


@pytest.fixture
def engine() -> Engine:
    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})
    create_business_record_table(engine)
    return engine


@pytest.fixture
def repository(engine) -> SqlAlchemyBusinessRecordRepository:
    return SqlAlchemyBusinessRecordRepository(engine)


@pytest.fixture
def identity_gate(engine) -> CanonicalSecurityIdentityGate:
    return build_identity_gate(engine)


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
    """Sprint O: `provider_id` is now `"alpha_vantage"` (the one
    provider `canonical_security_gate.candidate_mapping` recognizes)
    and `metadata` now also carries `exchange`/`country`/`currency`/
    `security_type` -- without these, this fixture's own document
    could no longer reach `AUTO_ACCEPT`, and every test using it would
    be blocked before ever persisting anything."""
    return RawBusinessDocument(
        identifier=f"{company}:profile",
        company=company,
        source_kind="company_profile",
        published_at=_EVALUATED_AT,
        provider_id="alpha_vantage",
        raw_reference="https://example.test/profile",
        content_hash=f"profile-hash-{name}",
        language="en",
        metadata={
            "name": name,
            "sector": sector,
            "exchange": "NASDAQ",
            "country": "USA",
            "currency": "USD",
            "security_type": "COMMON_STOCK",
        },
    )


class TestBasicRefresh:
    def test_fresh_company_produces_new_records_and_persists_them(self, repository, identity_gate):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2022"), _doc(identifier="AAPL:FY:2023", revenue=110.0)))
        summary = refresh_company_data(
            "AAPL", (provider, _identity_provider("AAPL")), repository, identity_gate=identity_gate
        )

        assert summary.ticker == "AAPL"
        assert summary.fetched_documents == 3  # 2 fundamentals + 1 identity/profile document
        assert summary.new_records == 3
        assert summary.new_versions == 0
        assert summary.duplicates_skipped == 0
        assert summary.rejected_documents == 0
        assert summary.provider_errors == ()
        assert summary.identity_gate_outcome == "AUTO_ACCEPT"
        assert len(repository.get_by_company("AAPL")) == 3

    def test_malformed_document_is_rejected_not_persisted(self, repository, identity_gate):
        malformed = RawBusinessDocument(
            identifier=None, company="AAPL", source_kind="financial_statement",
            published_at=_EVALUATED_AT, provider_id="fake", raw_reference="x", content_hash="x",
        )
        provider = _FakeProvider(documents=(malformed,))
        summary = refresh_company_data(
            "AAPL", (provider, _identity_provider("AAPL")), repository, identity_gate=identity_gate
        )
        assert summary.rejected_documents == 1
        assert summary.new_records == 1  # the identity/profile document, not the malformed one
        records = repository.get_by_company("AAPL")
        assert len(records) == 1
        assert records[0].document_type.value == "company_profile"


class TestIdempotency:
    def test_identical_refresh_run_twice_is_fully_idempotent(self, repository, identity_gate):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023"),))
        identity = _identity_provider("AAPL")
        first = refresh_company_data("AAPL", (provider, identity), repository, identity_gate=identity_gate)
        second = refresh_company_data("AAPL", (provider, identity), repository, identity_gate=identity_gate)

        assert first.new_records == 2  # fundamentals + identity/profile
        assert second.new_records == 0
        assert second.duplicates_skipped == 2  # both documents repeat
        assert len(repository.get_by_company("AAPL")) == 2

    def test_restated_value_produces_a_new_version_not_a_duplicate(self, repository, identity_gate):
        identity = _identity_provider("AAPL")
        original = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", revenue=100.0),))
        refresh_company_data("AAPL", (original, identity), repository, identity_gate=identity_gate)

        restated = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", revenue=95.0, content_hash="hash-restated"),))
        summary = refresh_company_data("AAPL", (restated, identity), repository, identity_gate=identity_gate)

        assert summary.new_versions == 1
        assert summary.new_records == 0
        assert summary.duplicates_skipped == 1  # the identity/profile document repeats
        records = repository.get_by_company("AAPL")
        assert len(records) == 3  # fundamentals v1, fundamentals v2, identity/profile v1
        latest = next(r for r in records if r.version.version_number == 2)
        assert latest.metadata["revenue"] == 95.0
        original_record = next(
            r for r in records if r.version.version_number == 1 and r.document_type.value == "financial_statement"
        )
        assert original_record.metadata["revenue"] == 100.0  # immutable, never overwritten


class TestProviderFailureIsolation:
    def test_one_providers_failure_never_blocks_another_providers_documents(self, repository, identity_gate):
        failing = _FakeProvider(exception=RuntimeError("provider unavailable"))
        working = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023"),))
        summary = refresh_company_data(
            "AAPL", (failing, working, _identity_provider("AAPL")), repository, identity_gate=identity_gate
        )

        assert summary.new_records == 2  # working's fundamentals record + identity/profile
        assert len(summary.provider_errors) == 1
        assert summary.provider_errors[0].provider_id == "_FakeProvider"
        assert "provider unavailable" in summary.provider_errors[0].error
        assert len(repository.get_by_company("AAPL")) == 2

    def test_all_providers_failing_produces_a_summary_with_zero_documents_not_a_crash(self, repository, identity_gate):
        """Sprint O: with no identity source present at all, the
        Identity Gate now resolves `NO_MATCH` and blocks the run before
        either fundamentals provider is ever invoked -- `provider_errors`
        is therefore empty, not populated with their failures, since
        they are never called. This is the intended, stricter "no
        fallback" behavior: a ticker Atlas cannot even identify never
        gets far enough to discover whether its data providers would
        have failed too."""
        failing_a = _FakeProvider(exception=RuntimeError("timeout"))
        failing_b = _FakeProvider(exception=RuntimeError("company not found"))
        summary = refresh_company_data("ZZZZ", (failing_a, failing_b), repository, identity_gate=identity_gate)

        assert summary.fetched_documents == 0
        assert summary.new_records == 0
        assert summary.provider_errors == ()
        assert summary.identity_gate_outcome == "NO_MATCH"


class TestCrossCompanyIsolation:
    def test_refreshing_one_company_never_touches_another_companys_records(self, repository, identity_gate):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", company="AAPL"),))
        refresh_company_data("AAPL", (provider, _identity_provider("AAPL")), repository, identity_gate=identity_gate)
        # provider has no MSFT docs, and no identity is supplied for MSFT either --
        # correctly blocked (NO_MATCH), leaving MSFT's repository empty either way.
        refresh_company_data("MSFT", (provider,), repository, identity_gate=identity_gate)

        assert len(repository.get_by_company("AAPL")) == 2  # fundamentals + identity/profile
        assert repository.get_by_company("MSFT") == ()


class TestHistoricalMarketDataCapability:
    """ATLAS-032, Phase 7 -- the optional second pass for any provider
    that also implements `HistoricalMarketDataProvider`, checked via
    `isinstance`, never a hardcoded provider-class name."""

    def test_provider_without_the_capability_is_never_asked_for_history(self, repository, identity_gate):
        """`_FakeProvider` (used throughout this file) has no
        `fetch_historical_snapshots` -- `refresh_company_data` must not
        error or otherwise treat it specially."""
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023"),))
        summary = refresh_company_data(
            "AAPL", (provider, _identity_provider("AAPL")), repository, identity_gate=identity_gate
        )
        assert summary.provider_errors == ()
        assert summary.new_records == 2  # fundamentals + identity/profile

    def test_no_known_filing_dates_skips_the_historical_call_entirely(self, repository, identity_gate):
        """No FINANCIAL_STATEMENT record exists yet for this company
        (a market-data-only refresh) -- there is nothing to sample
        historical prices around, so the provider is never called."""
        historical_provider = _FakeHistoricalProvider(
            current_documents=(_doc(identifier="AAPL:snap", source_kind="market_data_snapshot"),)
        )
        refresh_company_data(
            "AAPL", (historical_provider, _identity_provider("AAPL")), repository, identity_gate=identity_gate
        )
        assert historical_provider.received_filing_dates == []

    def test_historical_provider_receives_the_real_known_filing_dates(self, repository, identity_gate):
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
        summary = refresh_company_data(
            "AAPL",
            (fundamentals_provider, historical_provider, _identity_provider("AAPL")),
            repository,
            identity_gate=identity_gate,
        )

        assert historical_provider.received_filing_dates == [(date(2023, 2, 15), date(2024, 2, 15))]
        assert summary.provider_errors == ()
        assert summary.new_records == 4  # 2 fundamentals + 1 historical snapshot + identity/profile
        market_records = [r for r in repository.get_by_company("AAPL") if r.document_type.value == "market_data_snapshot"]
        assert len(market_records) == 1

    def test_filing_dates_include_already_persisted_records_from_a_prior_run(self, repository, identity_gate):
        """A second refresh should sample history using fundamentals
        already in the repository, not only ones fetched this run."""
        identity = _identity_provider("AAPL")
        fundamentals_provider = _FakeProvider(
            documents=(_doc(identifier="AAPL:FY:2022", published_at=datetime(2023, 2, 15, tzinfo=timezone.utc)),)
        )
        refresh_company_data("AAPL", (fundamentals_provider, identity), repository, identity_gate=identity_gate)

        historical_provider = _FakeHistoricalProvider()
        # Identity must still be present on this second, standalone call --
        # the Gate resolves an identity every call, reusing the existing
        # CanonicalSecurity rather than bypassing resolution because one
        # already exists (Sprint O Phase 5: reuse, never skip).
        refresh_company_data("AAPL", (historical_provider, identity), repository, identity_gate=identity_gate)
        assert historical_provider.received_filing_dates == [(date(2023, 2, 15),)]

    def test_historical_failure_is_isolated_and_reported_distinctly(self, repository, identity_gate):
        fundamentals_provider = _FakeProvider(
            documents=(_doc(identifier="AAPL:FY:2022", published_at=datetime(2023, 2, 15, tzinfo=timezone.utc)),)
        )
        historical_provider = _FakeHistoricalProvider(historical_exception=RuntimeError("rate limited"))
        summary = refresh_company_data(
            "AAPL",
            (fundamentals_provider, historical_provider, _identity_provider("AAPL")),
            repository,
            identity_gate=identity_gate,
        )

        assert summary.new_records == 2  # the fundamentals record + identity/profile still persisted
        assert len(summary.provider_errors) == 1
        assert summary.provider_errors[0].provider_id == "_FakeHistoricalProvider.fetch_historical_snapshots"
        assert "rate limited" in summary.provider_errors[0].error


class TestEarningsCallCapability:
    """Capability Expansion Sprint 2 -- the optional fourth pass for
    any provider that also implements `EarningsCallTranscriptProvider`,
    checked via `isinstance`, never a hardcoded provider-class name."""

    def test_provider_without_the_capability_is_never_asked_for_a_transcript(self, repository, identity_gate):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023"),))
        summary = refresh_company_data(
            "AAPL", (provider, _identity_provider("AAPL")), repository, identity_gate=identity_gate
        )
        assert summary.provider_errors == ()

    def test_transcript_provider_is_called_with_no_date_argument(self, repository, identity_gate):
        """Unlike the historical-market-data pass, this needs no
        `known_records`-derived input -- called even when no
        `FINANCIAL_STATEMENT` record exists at all."""
        transcript_provider = _FakeEarningsCallProvider()
        refresh_company_data(
            "AAPL", (transcript_provider, _identity_provider("AAPL")), repository, identity_gate=identity_gate
        )
        assert transcript_provider.call_count == ["AAPL"]

    def test_transcript_documents_are_ingested(self, repository, identity_gate):
        transcript_provider = _FakeEarningsCallProvider(
            transcript_documents=(
                RawBusinessDocument(
                    identifier="AAPL:transcript:2026Q2:0",
                    company="AAPL",
                    source_kind="transcript",
                    published_at=_EVALUATED_AT,
                    provider_id="fake",
                    raw_reference="https://example.test/transcript",
                    content_hash="transcript-hash-1",
                    language="en",
                    metadata={"quarter": "2026Q2", "statement_index": 0, "speaker": "CEO", "content": "Strong quarter."},
                ),
            )
        )
        summary = refresh_company_data(
            "AAPL", (transcript_provider, _identity_provider("AAPL")), repository, identity_gate=identity_gate
        )
        assert summary.new_records == 2  # transcript statement + identity/profile
        transcript_records = [r for r in repository.get_by_company("AAPL") if r.document_type.value == "transcript"]
        assert len(transcript_records) == 1

    def test_transcript_failure_is_isolated_and_reported_distinctly(self, repository, identity_gate):
        fundamentals_provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2022"),))
        transcript_provider = _FakeEarningsCallProvider(transcript_exception=RuntimeError("premium endpoint"))
        summary = refresh_company_data(
            "AAPL",
            (fundamentals_provider, transcript_provider, _identity_provider("AAPL")),
            repository,
            identity_gate=identity_gate,
        )
        assert summary.new_records == 2  # fundamentals + identity/profile still persisted
        assert len(summary.provider_errors) == 1
        assert summary.provider_errors[0].provider_id == "_FakeEarningsCallProvider.fetch_earnings_call_transcripts"
        assert "premium endpoint" in summary.provider_errors[0].error

    def test_duplicate_historical_documents_are_skipped_not_duplicated_on_rerun(self, repository, identity_gate):
        identity = _identity_provider("AAPL")
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
        refresh_company_data(
            "AAPL", (fundamentals_provider, historical_provider, identity), repository, identity_gate=identity_gate
        )
        second = refresh_company_data(
            "AAPL", (fundamentals_provider, historical_provider, identity), repository, identity_gate=identity_gate
        )
        assert second.duplicates_skipped == 3  # fundamentals + historical snapshot + identity/profile all repeat
        assert second.new_records == 0


class TestCompanyProfileCapability:
    """(Investment Case Engine v1 slice) The third, optional
    `CompanyProfileProvider` pass -- proves `refresh_company_data`
    detects it via duck typing (never a hardcoded provider class),
    isolates its failures distinctly from the other two passes, and
    persists what it returns through the identical ingestion pipeline."""

    def test_a_conforming_provider_gets_its_profile_ingested(self, repository, identity_gate):
        provider = _FakeCompanyProfileProvider(profile_documents=(_profile_doc(),))
        summary = refresh_company_data("AAPL", (provider,), repository, identity_gate=identity_gate)

        assert summary.new_records == 1
        records = repository.get_by_company("AAPL")
        assert len(records) == 1
        assert records[0].document_type.value == "company_profile"
        assert records[0].metadata["name"] == "Apple Inc."

    def test_a_non_conforming_provider_is_silently_skipped_for_this_pass(self, repository, identity_gate):
        """`_FakeProvider` itself still does not implement
        `CompanyProfileProvider` (unaffected by Sprint O) -- its own
        profile pass is still silently skipped. A separate
        `_IdentityProvider` supplies the identity this run now needs to
        pass the Gate at all."""
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023"),))
        summary = refresh_company_data(
            "AAPL", (provider, _identity_provider("AAPL")), repository, identity_gate=identity_gate
        )
        assert summary.new_records == 2  # the fundamentals record + the identity provider's own profile
        assert summary.provider_errors == ()

    def test_profile_failure_is_isolated_and_reported_distinctly(self, repository, identity_gate):
        """Sprint O: with no other identity source present, a failed
        profile fetch now blocks the entire run (`NO_MATCH`) rather
        than merely failing to contribute its own record -- "no
        fallback" applies to identity exactly as it does to any other
        provider. The failure itself is still captured and reported,
        never silently swallowed."""
        fundamentals_provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023"),))
        profile_provider = _FakeCompanyProfileProvider(profile_exception=RuntimeError("overview unavailable"))
        summary = refresh_company_data(
            "AAPL", (fundamentals_provider, profile_provider), repository, identity_gate=identity_gate
        )

        assert summary.new_records == 0
        assert summary.identity_gate_outcome == "NO_MATCH"
        assert len(summary.provider_errors) == 1
        assert summary.provider_errors[0].provider_id == "_FakeCompanyProfileProvider.fetch_company_profile"
        assert "overview unavailable" in summary.provider_errors[0].error

    def test_empty_profile_result_produces_no_record_and_no_error(self, repository, identity_gate):
        """A provider that legitimately has no identity fields for this
        company returns `()`, not an exception -- never fabricated,
        never reported as a failure. With zero candidates, the Gate
        resolves `NO_MATCH` -- the same honest-absence outcome as
        before, reached through resolution rather than through a
        skipped pass."""
        provider = _FakeCompanyProfileProvider(profile_documents=())
        summary = refresh_company_data("AAPL", (provider,), repository, identity_gate=identity_gate)
        assert summary.new_records == 0
        assert summary.provider_errors == ()
        assert summary.identity_gate_outcome == "NO_MATCH"
        assert repository.get_by_company("AAPL") == ()

    def test_repeated_refresh_of_the_same_profile_is_idempotent(self, repository, identity_gate):
        provider = _FakeCompanyProfileProvider(profile_documents=(_profile_doc(),))
        first = refresh_company_data("AAPL", (provider,), repository, identity_gate=identity_gate)
        second = refresh_company_data("AAPL", (provider,), repository, identity_gate=identity_gate)
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

    def test_a_new_company_is_fetched_and_persisted(self, repository, identity_gate):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023"),))
        summary = ensure_company_enriched(
            "AAPL", (provider, _identity_provider("AAPL")), repository, identity_gate=identity_gate
        )
        assert summary is not None
        assert summary.new_records == 2  # fundamentals + identity/profile
        assert len(repository.get_by_company("AAPL")) == 2

    def test_an_already_enriched_company_makes_no_provider_call_at_all(self, repository, identity_gate):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023"),))
        ensure_company_enriched(
            "AAPL", (provider, _identity_provider("AAPL")), repository, identity_gate=identity_gate
        )

        calling_provider = _FakeProvider(exception=AssertionError("must never be called"))
        result = ensure_company_enriched("AAPL", (calling_provider,), repository, identity_gate=identity_gate)
        assert result is None
        assert len(repository.get_by_company("AAPL")) == 2  # unchanged

    def test_a_different_ticker_is_still_fetched_independently(self, repository, identity_gate):
        provider = _FakeProvider(
            documents=(_doc(identifier="AAPL:FY:2023", company="AAPL"), _doc(identifier="MSFT:FY:2023", company="MSFT"))
        )
        identity = _identity_provider("AAPL", "MSFT")
        ensure_company_enriched("AAPL", (provider, identity), repository, identity_gate=identity_gate)
        second = ensure_company_enriched("MSFT", (provider, identity), repository, identity_gate=identity_gate)
        assert second is not None
        assert second.new_records == 2  # fundamentals + identity/profile
        assert len(repository.get_by_company("MSFT")) == 2

    def test_a_provider_failure_does_not_raise_and_still_returns_a_summary(self, repository, identity_gate):
        """Sprint O: identity is supplied separately so the failing
        fundamentals provider is still actually invoked (and its
        failure captured) -- without any identity source at all, the
        Gate would block before ever reaching it, as
        `TestProviderFailureIsolation
        ::test_all_providers_failing_produces_a_summary_with_zero_documents_not_a_crash`
        now documents."""
        provider = _FakeProvider(exception=RuntimeError("SEC EDGAR unavailable"))
        summary = ensure_company_enriched(
            "AAPL", (provider, _identity_provider("AAPL")), repository, identity_gate=identity_gate
        )
        assert summary is not None
        assert len(summary.provider_errors) == 1
        records = repository.get_by_company("AAPL")
        assert len(records) == 1
        assert records[0].document_type.value == "company_profile"

    def test_partial_provider_failure_still_persists_the_succeeding_provider(self, repository, identity_gate):
        """Missing SEC EDGAR coverage (a non-US filer, `CompanyNotFound`
        in the real provider) must not block Alpha Vantage's own market
        data from being persisted -- an expected data-availability
        condition, not a system failure."""
        failing_fundamentals = _FakeProvider(exception=RuntimeError("CompanyNotFound: not an SEC filer"))
        succeeding_market_data = _FakeProvider(
            documents=(_doc(identifier="XYZ:snapshot:2026-08-09", company="XYZ", source_kind="market_data_snapshot"),)
        )
        summary = ensure_company_enriched(
            "XYZ",
            (failing_fundamentals, succeeding_market_data, _identity_provider("XYZ")),
            repository,
            identity_gate=identity_gate,
        )
        assert summary is not None
        assert len(summary.provider_errors) == 1
        assert summary.new_records == 2  # market data + identity/profile
        assert len(repository.get_by_company("XYZ")) == 2

    def test_a_company_with_only_a_stray_market_snapshot_is_not_treated_as_enriched(self, repository, identity_gate):
        """(Company Data Foundation v1) The original "too coarse" gap
        this test named: a company whose only persisted record was a
        `MARKET_DATA_SNAPSHOT` permanently blocked every future
        enrichment attempt under the old "any record at all" gate.

        Sprint O supersedes this scenario at a deeper layer: with no
        identity source present at all, the Identity Gate now blocks
        *before* any record -- market snapshot or otherwise -- is ever
        created, so neither provider is even called. The retry
        guarantee still holds (nothing ever becomes permanently stuck),
        just via `NO_MATCH` on every attempt rather than an incomplete
        completeness check."""
        failing_fundamentals = _FakeProvider(exception=RuntimeError("CompanyNotFound: not an SEC filer"))
        succeeding_market_data = _FakeProvider(
            documents=(_doc(identifier="XYZ:snapshot:2026-08-09", company="XYZ", source_kind="market_data_snapshot"),)
        )
        providers = (failing_fundamentals, succeeding_market_data)
        first = ensure_company_enriched("XYZ", providers, repository, identity_gate=identity_gate)
        assert first is not None
        assert first.identity_gate_outcome == "NO_MATCH"
        assert first.provider_errors == ()  # neither provider was ever invoked
        assert repository.get_by_company("XYZ") == ()

        second = ensure_company_enriched("XYZ", providers, repository, identity_gate=identity_gate)
        assert second is not None  # retried -- never permanently stuck
        assert second.identity_gate_outcome == "NO_MATCH"

    def test_a_company_profile_alone_remains_eligible_for_missing_fundamentals_work(self, repository, identity_gate):
        """Automatic Enrichment Coverage, Implementation Phase 1: a
        ticker with only Alpha Vantage identity (no SEC fundamentals
        yet) must remain eligible for the missing fundamentals work --
        `completion.assess_enrichment_completion` reports SEC as
        `NOT_YET_ATTEMPTED`, not folded into a whole-ticker "already
        enriched" boolean the way the superseded `is_minimally_complete`
        gate did. `calling_again` genuinely gets called; its own profile
        document is simply a duplicate of the first call's (same
        content), never a fresh `new_records` count."""
        profile_provider = _FakeCompanyProfileProvider(profile_documents=(_profile_doc(company="XYZ"),))
        ensure_company_enriched("XYZ", (profile_provider,), repository, identity_gate=identity_gate)
        assert len(profile_provider.profile_call_count) == 1
        assert len(repository.get_by_company("XYZ")) == 1  # profile only, no fundamentals yet

        calling_again = _FakeCompanyProfileProvider(profile_documents=(_profile_doc(company="XYZ"),))
        result = ensure_company_enriched("XYZ", (calling_again,), repository, identity_gate=identity_gate)
        assert result is not None
        assert len(calling_again.profile_call_count) == 1  # called again -- SEC leg still outstanding
        assert result.new_records == 0
        assert result.duplicates_skipped == 1  # the identical profile document, not a fresh record

    def test_a_company_profile_alone_stops_retrying_once_fundamentals_classified_unsupported(
        self, repository, identity_gate
    ):
        """The bounding half of the same fix: once the missing provider
        is *known*, from a prior run, to have failed in a way
        `completion.classify_provider_failure` calls `UNSUPPORTED`
        (Requirement 8 -- never retried as though it were a transient
        failure), passing that failure back in as `known_provider
        _failures` stops the retry `refresh_company_data` would
        otherwise attempt. This is what actually bounds retries now --
        not "any one provider succeeded," but "every required provider
        is either succeeded or genuinely unsupported.\""""
        profile_provider = _FakeCompanyProfileProvider(profile_documents=(_profile_doc(company="XYZ"),))
        ensure_company_enriched("XYZ", (profile_provider,), repository, identity_gate=identity_gate)

        known_sec_failure = (
            ProviderFailure(provider_id="SecEdgarFundamentalsProvider", error="not an SEC filer", kind="CompanyNotFound"),
        )
        calling_again = _FakeCompanyProfileProvider(profile_documents=(_profile_doc(company="XYZ"),))
        result = ensure_company_enriched(
            "XYZ", (calling_again,), repository, identity_gate=identity_gate, known_provider_failures=known_sec_failure
        )
        assert result is None
        assert len(calling_again.profile_call_count) == 0  # never called -- nothing retryable remains

    def test_a_financial_statement_alone_stops_further_retries(self, repository, identity_gate):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", source_kind="financial_statement"),))
        ensure_company_enriched(
            "AAPL", (provider, _identity_provider("AAPL")), repository, identity_gate=identity_gate
        )

        calling_again = _FakeProvider(exception=AssertionError("must never be called"))
        result = ensure_company_enriched("AAPL", (calling_again,), repository, identity_gate=identity_gate)
        assert result is None


@dataclass(frozen=True)
class _FakeKnowledgeProvider:
    """Automatic Knowledge Ingestion Framework, Phase 1. A minimal
    `KnowledgeProvider`-shaped fake (declares `provider_id`/
    `supported_domains`/`supported_source_kinds` in addition to the
    already-proven `fetch()`) -- proves `refresh_company_data` needs
    zero changes to accept a real `KnowledgeProvider`: it flows through
    the exact same per-provider loop `_FakeProvider` above already
    exercises, never a second, parallel orchestration path."""

    documents: tuple[RawBusinessDocument, ...] = ()
    provider_id: str = "fake_knowledge_provider"

    @property
    def supported_domains(self):
        from atlas.alpha.knowledge_coverage.models import KnowledgeDomain

        return (KnowledgeDomain.REGULATORY_FILINGS,)

    @property
    def supported_source_kinds(self):
        from atlas.analysis_engine.business_data.sources import SourceKind

        return (SourceKind.COMPANY_FILING,)

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        return tuple(d for d in self.documents if d.company == company_identifier)


class TestKnowledgeProviderContractCompatibility:
    def test_a_knowledge_provider_shaped_fake_is_a_real_isinstance_match(self):
        from atlas.alpha.knowledge_provider import KnowledgeProvider
        from atlas.analysis_engine.business_data.providers import BusinessDataProvider

        provider = _FakeKnowledgeProvider()
        assert isinstance(provider, KnowledgeProvider)
        assert isinstance(provider, BusinessDataProvider)

    def test_its_documents_flow_into_changed_records_unmodified(self, repository, identity_gate):
        filing = _doc(identifier="AAPL:FILING:0001", source_kind="company_filing")
        provider = _FakeKnowledgeProvider(documents=(filing,))
        summary = refresh_company_data(
            "AAPL", (provider, _identity_provider("AAPL")), repository, identity_gate=identity_gate
        )

        assert summary.fetched_documents == 2  # 1 filing + 1 identity/profile document
        assert summary.new_records == 2
        assert summary.provider_errors == ()
        filing_records = [r for r in summary.changed_records if r.document_type.value == "company_filing"]
        assert len(filing_records) == 1
        assert filing_records[0].id.startswith(filing_records[0].lineage_id)
