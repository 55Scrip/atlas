"""`enrich_holdings` tests (Internal Alpha Fix Sprint 1, Part 1 --
confirmed root cause IA-001).

Real in-memory SQLite persistence throughout; fake `BusinessDataProvider`
implementations (no network) -- the composition under test is the batch
orchestration itself (already-enriched skip / partial-progress /
unsupported / per-ticker failure isolation), not any one provider's
parsing, which `test_service.py` already covers in depth.

Sprint O: `enrich_holdings` now requires `identity_gate`, delegating to
`ensure_company_enriched`'s own mandatory gate. `_identity_provider`
mirrors `test_service.py`'s own helper of the same name -- a
`CompanyProfileProvider`-only fake supplying exactly the fields needed
to reach `AUTO_ACCEPT` for whichever tickers it is given, added
alongside whatever fundamentals fake each test already used. One test
(`test_every_provider_erroring_is_reported_unsupported_with_the_real_error_text`)
has been rewritten: with no identity source present, the Gate now
blocks before the failing fundamentals provider is ever invoked, so
there is no longer a real error string to surface -- see its own
updated docstring.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.bulk import enrich_holdings
from atlas.alpha.business_data_refresh.models import EnrichmentOutcome, ProviderFailure
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.canonical_security_gate.factory import build_identity_gate
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.alpha.ingestion.models import IngestionResult
from atlas.alpha.ingestion.repository import SqlAlchemyIngestionResultRepository
from atlas.alpha.ingestion.table import create_ingestion_result_table
from atlas.analysis_engine.business_data.models import RawBusinessDocument

_EVALUATED_AT = datetime(2026, 8, 9, tzinfo=timezone.utc)


@dataclass(frozen=True)
class _FakeProvider:
    documents: tuple[RawBusinessDocument, ...] = ()
    exception: Exception | None = None

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        if self.exception is not None:
            raise self.exception
        return tuple(d for d in self.documents if d.company == company_identifier)


@dataclass(frozen=True)
class _IdentityProvider:
    """See `test_service.py`'s identically-named/shaped fixture for
    the full rationale."""

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


def _doc(*, identifier: str, company: str, revenue: float = 100.0) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=identifier,
        company=company,
        source_kind="financial_statement",
        published_at=_EVALUATED_AT,
        provider_id="fake_provider",
        raw_reference="https://example.test/doc",
        content_hash=f"hash-{identifier}",
        language="en",
        metadata={"revenue": revenue, "currency": "USD"},
    )


def _make_engine() -> Engine:
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_business_record_table(engine)
    return engine


def _make_identity_gate(engine: Engine) -> CanonicalSecurityIdentityGate:
    return build_identity_gate(engine)


@pytest.fixture
def engine() -> Engine:
    return _make_engine()


@pytest.fixture
def repository(engine) -> SqlAlchemyBusinessRecordRepository:
    return SqlAlchemyBusinessRecordRepository(engine)


@pytest.fixture
def identity_gate(engine) -> CanonicalSecurityIdentityGate:
    return _make_identity_gate(engine)


class TestEmptyInput:
    def test_no_tickers_produces_an_empty_summary(self, repository, identity_gate):
        provider = _FakeProvider(exception=AssertionError("must never be called"))
        summary = enrich_holdings((), (provider,), repository, identity_gate=identity_gate)
        assert summary.results == ()
        assert summary.enriched_count == 0


class TestRealProgress:
    def test_a_ticker_with_real_data_is_reported_enriched(self, repository, identity_gate):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", company="AAPL"),))
        summary = enrich_holdings(
            ("AAPL",), (provider, _identity_provider("AAPL")), repository, identity_gate=identity_gate
        )
        assert len(summary.results) == 1
        assert summary.results[0].ticker == "AAPL"
        assert summary.results[0].outcome is EnrichmentOutcome.ENRICHED
        assert summary.results[0].detail is None
        assert summary.enriched_count == 1

    def test_a_partial_provider_failure_with_real_progress_still_counts_as_enriched(self, repository, identity_gate):
        """One provider succeeds, another fails -- `refresh_company_data`'s
        own isolation already guarantees the succeeding provider's data
        persists; real progress happening at all is what `ENRICHED`
        means here, matching the codebase's existing "one provider's
        failure never blocks another's success" doctrine."""
        good = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", company="AAPL"),))
        bad = _FakeProvider(exception=RuntimeError("provider down"))
        summary = enrich_holdings(
            ("AAPL",), (good, bad, _identity_provider("AAPL")), repository, identity_gate=identity_gate
        )
        assert summary.results[0].outcome is EnrichmentOutcome.ENRICHED
        assert len(repository.get_by_company("AAPL")) == 2  # fundamentals + identity/profile


class TestAlreadyEnriched:
    def test_an_already_minimally_complete_ticker_is_skipped(self, repository, identity_gate):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", company="AAPL"),))
        enrich_holdings(
            ("AAPL",), (provider, _identity_provider("AAPL")), repository, identity_gate=identity_gate
        )  # first pass: real enrichment

        calling_provider = _FakeProvider(exception=AssertionError("must never be called again"))
        summary = enrich_holdings(("AAPL",), (calling_provider,), repository, identity_gate=identity_gate)
        assert summary.results[0].outcome is EnrichmentOutcome.SKIPPED_ALREADY_ENRICHED
        assert summary.results[0].detail is None
        assert summary.skipped_count == 1


class TestUnsupportedTicker:
    def test_every_provider_returning_nothing_is_reported_unsupported_not_fabricated(self, repository, identity_gate):
        provider = _FakeProvider(documents=())  # runs cleanly, produces nothing
        summary = enrich_holdings(("ZZZZ",), (provider,), repository, identity_gate=identity_gate)
        assert summary.results[0].outcome is EnrichmentOutcome.UNSUPPORTED
        assert summary.unsupported_count == 1
        assert len(repository.get_by_company("ZZZZ")) == 0

    def test_every_provider_erroring_is_reported_unsupported_with_the_real_error_text(self, repository, identity_gate):
        """Sprint O: with no identity source present, the failing
        fundamentals provider is now never even invoked -- the Identity
        Gate resolves `NO_MATCH` first and blocks the whole run, so
        there is no provider error text to surface here anymore (no
        provider actually ran). The ticker is still, correctly,
        reported `UNSUPPORTED`."""
        provider = _FakeProvider(exception=RuntimeError("no coverage for this ticker"))
        summary = enrich_holdings(("ZZZZ",), (provider,), repository, identity_gate=identity_gate)
        result = summary.results[0]
        assert result.outcome is EnrichmentOutcome.UNSUPPORTED
        assert result.detail is None


class TestPerTickerFailureIsolation:
    def test_an_unexpected_exception_for_one_ticker_never_aborts_the_batch(self, repository, identity_gate, monkeypatch):
        """Simulates a genuine bug escaping `ensure_company_enriched`
        itself (never a real-world case -- provider failures already
        never raise) to prove the batch loop's own isolation, not
        `ensure_company_enriched`'s (already covered by `test_service.py`)."""
        import atlas.alpha.business_data_refresh.bulk as bulk_module

        real_ensure = bulk_module.ensure_company_enriched

        def _flaky_ensure(ticker, providers, repo, *, identity_gate, known_provider_failures=()):
            if ticker == "BROKEN":
                raise RuntimeError("unexpected bug")
            return real_ensure(
                ticker, providers, repo, identity_gate=identity_gate, known_provider_failures=known_provider_failures
            )

        monkeypatch.setattr(bulk_module, "ensure_company_enriched", _flaky_ensure)

        provider = _FakeProvider(
            documents=(_doc(identifier="AAPL:FY:2023", company="AAPL"), _doc(identifier="GOOG:FY:2023", company="GOOG"))
        )
        summary = enrich_holdings(
            ("AAPL", "BROKEN", "GOOG"),
            (provider, _identity_provider("AAPL", "GOOG")),
            repository,
            identity_gate=identity_gate,
        )

        assert [r.ticker for r in summary.results] == ["AAPL", "BROKEN", "GOOG"]
        assert summary.results[0].outcome is EnrichmentOutcome.ENRICHED
        assert summary.results[1].outcome is EnrichmentOutcome.FAILED
        assert "unexpected bug" in summary.results[1].detail
        assert summary.results[2].outcome is EnrichmentOutcome.ENRICHED  # never blocked by BROKEN
        assert summary.failed_count == 1


class TestManyTickersMixedOutcomes:
    def test_a_realistic_mixed_batch_reports_each_ticker_independently_in_order(self, repository, identity_gate):
        provider = _FakeProvider(
            documents=(
                _doc(identifier="AAPL:FY:2023", company="AAPL"),
                _doc(identifier="MSFT:FY:2023", company="MSFT"),
            )
        )
        summary = enrich_holdings(
            ("AAPL", "MSFT", "ZZZZ"),
            (provider, _identity_provider("AAPL", "MSFT")),
            repository,
            identity_gate=identity_gate,
        )
        outcomes = {r.ticker: r.outcome for r in summary.results}
        assert outcomes == {
            "AAPL": EnrichmentOutcome.ENRICHED,
            "MSFT": EnrichmentOutcome.ENRICHED,
            "ZZZZ": EnrichmentOutcome.UNSUPPORTED,
        }

    def test_no_duplicate_records_are_created_across_repeated_runs(self, repository, identity_gate):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", company="AAPL"),))
        identity = _identity_provider("AAPL")
        enrich_holdings(("AAPL",), (provider, identity), repository, identity_gate=identity_gate)
        enrich_holdings(("AAPL",), (provider, identity), repository, identity_gate=identity_gate)
        assert len(repository.get_by_company("AAPL")) == 2  # fundamentals + identity/profile


class TestDeterminism:
    def test_identical_inputs_produce_deeply_equal_summaries(self, repository, identity_gate):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", company="AAPL"),))
        identity = _identity_provider("AAPL")
        first = enrich_holdings(("AAPL",), (provider, identity), repository, identity_gate=identity_gate)

        second_engine = _make_engine()
        second_repository = SqlAlchemyBusinessRecordRepository(second_engine)
        second_identity_gate = _make_identity_gate(second_engine)
        second = enrich_holdings(("AAPL",), (provider, identity), second_repository, identity_gate=second_identity_gate)
        assert first == second


class TestProviderAwareCompletionAndIngestionPersistence:
    """Automatic Enrichment Coverage, Implementation Phase 1. Requires
    both `ingestion_result_repository` and `case_ids_by_ticker` -- the
    two new, optional, progressively-enhancing parameters."""

    def test_omitting_the_new_parameters_persists_nothing(self, engine, repository, identity_gate):
        """Regression: `enrich_holdings` behaves exactly as it did
        before this field existed when the new parameters are omitted."""
        create_ingestion_result_table(engine)
        ingestion_repository = SqlAlchemyIngestionResultRepository(engine)
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", company="AAPL"),))
        enrich_holdings(("AAPL",), (provider, _identity_provider("AAPL")), repository, identity_gate=identity_gate)
        assert ingestion_repository.get_by_ticker("AAPL") is None

    def test_a_resolvable_case_id_persists_the_run_as_ingestion_result(self, engine, repository, identity_gate):
        create_ingestion_result_table(engine)
        ingestion_repository = SqlAlchemyIngestionResultRepository(engine)
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", company="AAPL"),))
        enrich_holdings(
            ("AAPL",),
            (provider, _identity_provider("AAPL")),
            repository,
            identity_gate=identity_gate,
            ingestion_result_repository=ingestion_repository,
            case_ids_by_ticker={"AAPL": "case-aapl"},
        )
        persisted = ingestion_repository.get(case_id="case-aapl")
        assert persisted is not None
        assert persisted.ticker == "AAPL"
        assert persisted.has_new_data is True

    def test_a_ticker_with_no_resolvable_case_id_is_not_persisted(self, engine, repository, identity_gate):
        """`case_ids_by_ticker` deliberately absent for this ticker --
        a real, honest condition (e.g. a Watchlist-only ticker not yet
        linked) never fabricates a `case_id` to force persistence."""
        create_ingestion_result_table(engine)
        ingestion_repository = SqlAlchemyIngestionResultRepository(engine)
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", company="AAPL"),))
        enrich_holdings(
            ("AAPL",),
            (provider, _identity_provider("AAPL")),
            repository,
            identity_gate=identity_gate,
            ingestion_result_repository=ingestion_repository,
            case_ids_by_ticker={},
        )
        assert ingestion_repository.get_by_ticker("AAPL") is None

    def test_a_known_unsupported_failure_is_not_retried_on_the_next_bulk_run(self, engine, repository, identity_gate):
        """End-to-end proof through the real bulk path: a prior run's
        classified `FAILED_UNSUPPORTED` provider failure, persisted and
        read back via `get_by_ticker`, suppresses the retry a fresh
        `enrich_holdings` call would otherwise attempt for that provider
        -- Requirement 8, exercised through `enrich_holdings` itself
        rather than `assess_enrichment_completion` in isolation."""
        create_ingestion_result_table(engine)
        ingestion_repository = SqlAlchemyIngestionResultRepository(engine)
        # Seed a prior run's own persisted, classified-unsupported SEC
        # failure for a ticker that already has real identity data --
        # simulating "Alpha Vantage succeeded, SEC never will."
        ingestion_repository.upsert(
            IngestionResult(
                ticker="XYZ",
                case_id="case-xyz",
                ran_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                changes=(),
                has_new_data=False,
                fetched_documents=1,
                duplicates_skipped=0,
                rejected_documents=0,
                provider_errors=(),
                identity_gate_outcome="AUTO_ACCEPT",
                provider_failures=(
                    ProviderFailure(provider_id="SecEdgarFundamentalsProvider", error="not an SEC filer", kind="CompanyNotFound"),
                ),
            )
        )
        identity = _identity_provider("XYZ")
        enrich_holdings(("XYZ",), (identity,), repository, identity_gate=identity_gate)
        assert len(repository.get_by_company("XYZ")) == 1  # profile only -- pre-seeded, no SEC record

        never_called = _FakeProvider(exception=AssertionError("SEC must never be called -- already unsupported"))
        summary = enrich_holdings(
            ("XYZ",),
            (never_called, _identity_provider("XYZ")),
            repository,
            identity_gate=identity_gate,
            ingestion_result_repository=ingestion_repository,
        )
        assert summary.results[0].outcome is EnrichmentOutcome.SKIPPED_ALREADY_ENRICHED
