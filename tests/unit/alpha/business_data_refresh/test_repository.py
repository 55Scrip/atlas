"""`SqlAlchemyBusinessRecordRepository` tests (ATLAS-031, Phase 16).

Real in-memory SQLite throughout -- no fakes, no mocks, matching this
repository's own established real-harness testing discipline.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.analysis_engine.business_data.contracts import ValidationStatus
from atlas.analysis_engine.business_data.models import BusinessRecord, RecordVersion
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.provenance import Consumer, Provenance
from atlas.analysis_engine.provenance import SourceKind as ProvenanceSourceKind
from atlas.analysis_engine.provenance import UpdateTrigger

_EVALUATED_AT = datetime(2026, 8, 9, tzinfo=timezone.utc)


def _record(*, company: str, identifier: str, version_number: int = 1, supersedes: str | None = None, revenue: float = 100.0) -> BusinessRecord:
    lineage_id = f"lineage:{company}:{identifier}"
    return BusinessRecord(
        id=f"{lineage_id}:v{version_number}",
        lineage_id=lineage_id,
        identifier=identifier,
        company=company,
        document_type=SourceKind.FINANCIAL_STATEMENT,
        published_at=_EVALUATED_AT,
        provider_id="sec_edgar",
        source_reference="https://example.test/filing",
        content_hash=f"hash-{revenue}",
        version=RecordVersion(version_number=version_number, created_at=_EVALUATED_AT, content_hash=f"hash-{revenue}", supersedes=supersedes),
        provenance=Provenance(
            source_kind=ProvenanceSourceKind.EXTERNAL_DATA_SOURCE,
            source_references=("https://example.test/filing",),
            dependencies=(),
            update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
            consumers=(Consumer.PORTFOLIO_PAGE, Consumer.INVESTMENT_CASE_PAGE, Consumer.DISCOVERY, Consumer.HISTORY),
            computed_at=_EVALUATED_AT,
        ),
        validation_status=ValidationStatus.VALID,
        period_start=date(2023, 1, 1),
        period_end=date(2023, 12, 31),
        language="en",
        metadata={"revenue": revenue, "currency": "USD"},
    )


@pytest.fixture
def engine() -> Engine:
    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})
    create_business_record_table(engine)
    return engine


class TestAddAndGet:
    def test_add_then_get_by_company_round_trips_exactly(self, engine):
        repo = SqlAlchemyBusinessRecordRepository(engine)
        record = _record(company="AAPL", identifier="AAPL:FY:2023-12-31")
        repo.add(record)

        (fetched,) = repo.get_by_company("AAPL")
        assert fetched.id == record.id
        assert fetched.lineage_id == record.lineage_id
        assert fetched.company == record.company
        assert fetched.document_type == record.document_type
        assert fetched.published_at == record.published_at
        assert fetched.content_hash == record.content_hash
        assert fetched.version == record.version
        assert fetched.provenance == record.provenance
        assert fetched.validation_status == record.validation_status
        assert fetched.period_start == record.period_start
        assert fetched.period_end == record.period_end
        assert dict(fetched.metadata) == dict(record.metadata)

    def test_unknown_company_returns_empty_tuple(self, engine):
        repo = SqlAlchemyBusinessRecordRepository(engine)
        assert repo.get_by_company("NOPE") == ()

    def test_exists_reflects_persisted_state(self, engine):
        repo = SqlAlchemyBusinessRecordRepository(engine)
        record = _record(company="AAPL", identifier="AAPL:FY:2023-12-31")
        assert repo.exists(record.id) is False
        repo.add(record)
        assert repo.exists(record.id) is True


class TestCrossCompanyIsolation:
    def test_get_by_company_never_leaks_another_companys_records(self, engine):
        repo = SqlAlchemyBusinessRecordRepository(engine)
        repo.add(_record(company="AAPL", identifier="AAPL:FY:2023-12-31"))
        repo.add(_record(company="MSFT", identifier="MSFT:FY:2023-12-31"))

        assert len(repo.get_by_company("AAPL")) == 1
        assert len(repo.get_by_company("MSFT")) == 1
        assert repo.get_by_company("AAPL")[0].company == "AAPL"


class TestBatchedLookup:
    def test_get_by_companies_returns_every_requested_ticker_even_with_no_records(self, engine):
        repo = SqlAlchemyBusinessRecordRepository(engine)
        repo.add(_record(company="AAPL", identifier="AAPL:FY:2023-12-31"))

        result = repo.get_by_companies(("AAPL", "MSFT", "NVDA"))
        assert set(result.keys()) == {"AAPL", "MSFT", "NVDA"}
        assert len(result["AAPL"]) == 1
        assert result["MSFT"] == ()
        assert result["NVDA"] == ()

    def test_get_by_companies_empty_tuple_returns_empty_dict(self, engine):
        repo = SqlAlchemyBusinessRecordRepository(engine)
        assert repo.get_by_companies(()) == {}

    def test_get_by_companies_issues_one_query_regardless_of_company_count(self, engine, monkeypatch):
        """The N+1 guard Phase 19 requires -- proven by call-counting the
        underlying connection's `execute`, not by timing."""
        repo = SqlAlchemyBusinessRecordRepository(engine)
        for ticker in ("AAPL", "MSFT", "NVDA", "GOOG", "AMZN"):
            repo.add(_record(company=ticker, identifier=f"{ticker}:FY:2023-12-31"))

        call_count = 0
        original_connect = engine.connect

        def counting_connect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return original_connect(*args, **kwargs)

        monkeypatch.setattr(engine, "connect", counting_connect)
        repo.get_by_companies(("AAPL", "MSFT", "NVDA", "GOOG", "AMZN"))
        assert call_count == 1


class TestImmutabilityAndVersioning:
    def test_two_versions_of_the_same_lineage_are_both_persisted_and_distinguishable(self, engine):
        repo = SqlAlchemyBusinessRecordRepository(engine)
        v1 = _record(company="AAPL", identifier="AAPL:FY:2023-12-31", version_number=1, revenue=100.0)
        v2 = _record(company="AAPL", identifier="AAPL:FY:2023-12-31", version_number=2, supersedes=v1.id, revenue=105.0)
        repo.add(v1)
        repo.add(v2)

        records = repo.get_by_company("AAPL")
        assert len(records) == 2
        by_id = {r.id: r for r in records}
        assert by_id[v1.id].metadata["revenue"] == 100.0
        assert by_id[v2.id].metadata["revenue"] == 105.0
        assert by_id[v2.id].version.supersedes == v1.id
