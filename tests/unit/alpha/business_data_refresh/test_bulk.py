"""`enrich_holdings` tests (Internal Alpha Fix Sprint 1, Part 1 --
confirmed root cause IA-001).

Real in-memory SQLite persistence throughout; fake `BusinessDataProvider`
implementations (no network) -- the composition under test is the batch
orchestration itself (already-enriched skip / partial-progress /
unsupported / per-ticker failure isolation), not any one provider's
parsing, which `test_service.py` already covers in depth.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.bulk import enrich_holdings
from atlas.alpha.business_data_refresh.models import EnrichmentOutcome
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
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


@pytest.fixture
def engine() -> Engine:
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_business_record_table(engine)
    return engine


@pytest.fixture
def repository(engine) -> SqlAlchemyBusinessRecordRepository:
    return SqlAlchemyBusinessRecordRepository(engine)


class TestEmptyInput:
    def test_no_tickers_produces_an_empty_summary(self, repository):
        provider = _FakeProvider(exception=AssertionError("must never be called"))
        summary = enrich_holdings((), (provider,), repository)
        assert summary.results == ()
        assert summary.enriched_count == 0


class TestRealProgress:
    def test_a_ticker_with_real_data_is_reported_enriched(self, repository):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", company="AAPL"),))
        summary = enrich_holdings(("AAPL",), (provider,), repository)
        assert len(summary.results) == 1
        assert summary.results[0].ticker == "AAPL"
        assert summary.results[0].outcome is EnrichmentOutcome.ENRICHED
        assert summary.results[0].detail is None
        assert summary.enriched_count == 1

    def test_a_partial_provider_failure_with_real_progress_still_counts_as_enriched(self, repository):
        """One provider succeeds, another fails -- `refresh_company_data`'s
        own isolation already guarantees the succeeding provider's data
        persists; real progress happening at all is what `ENRICHED`
        means here, matching the codebase's existing "one provider's
        failure never blocks another's success" doctrine."""
        good = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", company="AAPL"),))
        bad = _FakeProvider(exception=RuntimeError("provider down"))
        summary = enrich_holdings(("AAPL",), (good, bad), repository)
        assert summary.results[0].outcome is EnrichmentOutcome.ENRICHED
        assert len(repository.get_by_company("AAPL")) == 1


class TestAlreadyEnriched:
    def test_an_already_minimally_complete_ticker_is_skipped(self, repository):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", company="AAPL"),))
        enrich_holdings(("AAPL",), (provider,), repository)  # first pass: real enrichment

        calling_provider = _FakeProvider(exception=AssertionError("must never be called again"))
        summary = enrich_holdings(("AAPL",), (calling_provider,), repository)
        assert summary.results[0].outcome is EnrichmentOutcome.SKIPPED_ALREADY_ENRICHED
        assert summary.results[0].detail is None
        assert summary.skipped_count == 1


class TestUnsupportedTicker:
    def test_every_provider_returning_nothing_is_reported_unsupported_not_fabricated(self, repository):
        provider = _FakeProvider(documents=())  # runs cleanly, produces nothing
        summary = enrich_holdings(("ZZZZ",), (provider,), repository)
        assert summary.results[0].outcome is EnrichmentOutcome.UNSUPPORTED
        assert summary.unsupported_count == 1
        assert len(repository.get_by_company("ZZZZ")) == 0

    def test_every_provider_erroring_is_reported_unsupported_with_the_real_error_text(self, repository):
        provider = _FakeProvider(exception=RuntimeError("no coverage for this ticker"))
        summary = enrich_holdings(("ZZZZ",), (provider,), repository)
        result = summary.results[0]
        assert result.outcome is EnrichmentOutcome.UNSUPPORTED
        assert result.detail is not None
        assert "no coverage for this ticker" in result.detail


class TestPerTickerFailureIsolation:
    def test_an_unexpected_exception_for_one_ticker_never_aborts_the_batch(self, repository, monkeypatch):
        """Simulates a genuine bug escaping `ensure_company_enriched`
        itself (never a real-world case -- provider failures already
        never raise) to prove the batch loop's own isolation, not
        `ensure_company_enriched`'s (already covered by `test_service.py`)."""
        import atlas.alpha.business_data_refresh.bulk as bulk_module

        real_ensure = bulk_module.ensure_company_enriched

        def _flaky_ensure(ticker, providers, repo):
            if ticker == "BROKEN":
                raise RuntimeError("unexpected bug")
            return real_ensure(ticker, providers, repo)

        monkeypatch.setattr(bulk_module, "ensure_company_enriched", _flaky_ensure)

        provider = _FakeProvider(
            documents=(_doc(identifier="AAPL:FY:2023", company="AAPL"), _doc(identifier="GOOG:FY:2023", company="GOOG"))
        )
        summary = enrich_holdings(("AAPL", "BROKEN", "GOOG"), (provider,), repository)

        assert [r.ticker for r in summary.results] == ["AAPL", "BROKEN", "GOOG"]
        assert summary.results[0].outcome is EnrichmentOutcome.ENRICHED
        assert summary.results[1].outcome is EnrichmentOutcome.FAILED
        assert "unexpected bug" in summary.results[1].detail
        assert summary.results[2].outcome is EnrichmentOutcome.ENRICHED  # never blocked by BROKEN
        assert summary.failed_count == 1


class TestManyTickersMixedOutcomes:
    def test_a_realistic_mixed_batch_reports_each_ticker_independently_in_order(self, repository):
        provider = _FakeProvider(
            documents=(
                _doc(identifier="AAPL:FY:2023", company="AAPL"),
                _doc(identifier="MSFT:FY:2023", company="MSFT"),
            )
        )
        summary = enrich_holdings(("AAPL", "MSFT", "ZZZZ"), (provider,), repository)
        outcomes = {r.ticker: r.outcome for r in summary.results}
        assert outcomes == {
            "AAPL": EnrichmentOutcome.ENRICHED,
            "MSFT": EnrichmentOutcome.ENRICHED,
            "ZZZZ": EnrichmentOutcome.UNSUPPORTED,
        }

    def test_no_duplicate_records_are_created_across_repeated_runs(self, repository):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", company="AAPL"),))
        enrich_holdings(("AAPL",), (provider,), repository)
        enrich_holdings(("AAPL",), (provider,), repository)
        assert len(repository.get_by_company("AAPL")) == 1


class TestDeterminism:
    def test_identical_inputs_produce_deeply_equal_summaries(self, repository):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2023", company="AAPL"),))
        first = enrich_holdings(("AAPL",), (provider,), repository)

        second_engine = create_engine(
            "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
        )
        create_business_record_table(second_engine)
        second_repository = SqlAlchemyBusinessRecordRepository(second_engine)
        second = enrich_holdings(("AAPL",), (provider,), second_repository)
        assert first == second
