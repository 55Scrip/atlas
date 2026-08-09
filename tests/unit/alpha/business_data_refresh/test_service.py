"""`refresh_company_data` tests (ATLAS-031, Phase 17/28).

Real in-memory SQLite persistence throughout; fake `BusinessDataProvider`
implementations (no network) standing in for the real SEC EDGAR/Alpha
Vantage providers -- the composition under test is the use case's own
orchestration logic (fetch -> ingest -> persist -> summarize), not any
one provider's parsing.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.service import refresh_company_data
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


def _doc(*, identifier: str, company: str = "AAPL", revenue: float = 100.0, content_hash: str | None = None) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=identifier,
        company=company,
        source_kind="financial_statement",
        published_at=_EVALUATED_AT,
        provider_id="fake_provider",
        raw_reference="https://example.test/doc",
        content_hash=content_hash or f"hash-{revenue}",
        language="en",
        metadata={"revenue": revenue, "currency": "USD"},
    )


@pytest.fixture
def engine() -> Engine:
    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})
    create_business_record_table(engine)
    return engine


@pytest.fixture
def repository(engine) -> SqlAlchemyBusinessRecordRepository:
    return SqlAlchemyBusinessRecordRepository(engine)


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
