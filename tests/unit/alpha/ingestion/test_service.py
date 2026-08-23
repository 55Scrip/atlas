"""Tests for `atlas.alpha.ingestion.service.IngestionService`. Fake
`BusinessDataProvider` implementations (no network) -- the identical
pattern `tests/unit/alpha/business_data_refresh/test_service.py`
already established -- since the composition under test here is
Ingestion's own classify-and-record orchestration, not any provider's
parsing.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.canonical_security_gate.factory import build_identity_gate
from atlas.alpha.ingestion.models import DataChangeKind
from atlas.alpha.ingestion.repository import SqlAlchemyIngestionResultRepository
from atlas.alpha.ingestion.service import IngestionService
from atlas.alpha.ingestion.table import create_ingestion_result_table
from atlas.analysis_engine.business_data.models import RawBusinessDocument

_EVALUATED_AT = datetime(2026, 8, 21, tzinfo=timezone.utc)


@dataclass(frozen=True)
class _FakeProvider:
    documents: tuple[RawBusinessDocument, ...] = ()

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        return tuple(d for d in self.documents if d.company == company_identifier)


@dataclass(frozen=True)
class _IdentityProvider:
    tickers: tuple[str, ...]

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        return ()

    def fetch_company_profile(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
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


def _doc(*, identifier: str, company: str = "NVDA", content_hash: str) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=identifier,
        company=company,
        source_kind="financial_statement",
        published_at=_EVALUATED_AT,
        provider_id="fake_provider",
        raw_reference="https://example.test/doc",
        content_hash=content_hash,
        language="en",
        metadata={"revenue": 100.0, "currency": "USD"},
    )


@pytest.fixture
def engine() -> Engine:
    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})
    create_business_record_table(engine)
    create_ingestion_result_table(engine)
    return engine


def _service(engine, *, documents=()) -> IngestionService:
    return IngestionService(
        providers=(_IdentityProvider(tickers=("NVDA",)), _FakeProvider(documents=documents)),
        business_record_repository=SqlAlchemyBusinessRecordRepository(engine),
        identity_gate=build_identity_gate(engine),
        ingestion_result_repository=SqlAlchemyIngestionResultRepository(engine),
    )


class TestRefresh:
    def test_a_genuinely_new_document_is_recorded_as_new_dataset(self, engine):
        service = _service(engine, documents=(_doc(identifier="doc-1", content_hash="v1"),))
        result = service.refresh("NVDA", "case-1")
        assert result.has_new_data is True
        assert any(c.kind is DataChangeKind.NEW_DATASET and c.source_kind == "financial_statement" for c in result.changes)

    def test_the_result_is_persisted_and_readable_via_get_latest(self, engine):
        service = _service(engine, documents=(_doc(identifier="doc-1", content_hash="v1"),))
        service.refresh("NVDA", "case-1")
        cached = service.get_latest("case-1")
        assert cached is not None
        assert cached.has_new_data is True

    def test_refreshing_again_with_identical_content_reports_no_new_data(self, engine):
        """Critical requirement: re-fetching the identical document
        must never fabricate a DataChange the second time."""
        service = _service(engine, documents=(_doc(identifier="doc-1", content_hash="v1"),))
        service.refresh("NVDA", "case-1")
        second = service.refresh("NVDA", "case-1")
        assert second.has_new_data is False
        assert second.changes == ()

    def test_a_genuine_restatement_is_recorded_as_dataset_replaced(self, engine):
        service = _service(engine, documents=(_doc(identifier="doc-1", content_hash="v1"),))
        service.refresh("NVDA", "case-1")
        service_v2 = _service(engine, documents=(_doc(identifier="doc-1", content_hash="v2"),))
        result = service_v2.refresh("NVDA", "case-1")
        assert result.has_new_data is True
        assert any(c.kind is DataChangeKind.DATASET_REPLACED for c in result.changes)

    def test_no_case_id_is_never_persisted(self, engine):
        """A ticker with no resolvable Case (e.g. neither a Portfolio
        holding nor a Watchlist entry) must not silently create a
        cache row keyed on `None`."""
        service = _service(engine, documents=(_doc(identifier="doc-1", content_hash="v1"),))
        service.refresh("NVDA", None)
        # No case_id -> nothing to key the read-model cache on; list_all stays empty.
        assert service._ingestion_result_repository.list_all() == ()


class TestEnsureEnrichedAndRecord:
    def test_returns_none_and_records_nothing_when_already_minimally_complete(self, engine):
        service = _service(engine, documents=(_doc(identifier="doc-1", content_hash="v1"),))
        service.refresh("NVDA", "case-1")  # establishes real, minimally-complete records
        result = service.ensure_enriched_and_record("NVDA", "case-1")
        assert result is None
        # The prior real IngestionResult must survive untouched.
        cached = service.get_latest("case-1")
        assert cached is not None and cached.has_new_data is True

    def test_a_genuinely_new_ticker_is_recorded(self, engine):
        service = _service(engine, documents=(_doc(identifier="doc-1", content_hash="v1"),))
        result = service.ensure_enriched_and_record("NVDA", "case-1")
        assert result is not None
        assert result.has_new_data is True
