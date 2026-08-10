"""Tests for `atlas.alpha.watchlist.service.AlphaWatchlistService`
(Investment Case Engine v1 slice).

Covers: Case creation/linkage on add, idempotency, cross-context Case
reuse with Portfolio, and the automatic enrichment trigger (including
provider-failure isolation and the no-duplicate-provider-call
guarantee).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.portfolio.models import AlphaHolding, AlphaPortfolioState, EntryMode
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.watchlist.exceptions import AlphaWatchlistValidationError
from atlas.alpha.watchlist.service import AlphaWatchlistService
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.alpha.watchlist.table import create_alpha_watchlist_entry_table
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.core.application.case.create_case import CaseService
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.infrastructure.persistence.case.sqlalchemy_repository import SqlAlchemyCaseRepository
from atlas.core.infrastructure.persistence.case.table import create_case_table

_NOW = datetime(2026, 8, 9, tzinfo=timezone.utc)


def _new_engine():
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_alpha_watchlist_entry_table(engine)
    create_alpha_portfolio_state_table(engine)
    create_case_table(engine)
    create_business_record_table(engine)
    return engine


def _case_generation_service(engine) -> CaseGenerationService:
    return CaseGenerationService(CaseService(SqlAlchemyCaseRepository(engine)))


@dataclass(frozen=True)
class _FakeProvider:
    documents: tuple[RawBusinessDocument, ...] = ()
    exception: Exception | None = None
    call_count: list = field(default_factory=list)

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        self.call_count.append(company_identifier)
        if self.exception is not None:
            raise self.exception
        return tuple(d for d in self.documents if d.company == company_identifier)


def _doc(company: str) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=f"{company}:FY:2023",
        company=company,
        source_kind="financial_statement",
        published_at=_NOW,
        provider_id="fake_provider",
        raw_reference="https://example.test/doc",
        content_hash=f"hash-{company}",
        language="en",
        metadata={"revenue": 100.0},
    )


@pytest.fixture
def engine():
    return _new_engine()


@pytest.fixture
def watchlist_store(engine) -> AlphaWatchlistStore:
    return AlphaWatchlistStore(engine)


@pytest.fixture
def service(engine, watchlist_store) -> AlphaWatchlistService:
    return AlphaWatchlistService(watchlist_store, _case_generation_service(engine))


class TestAddTickerCreatesCase:
    def test_a_new_ticker_gets_a_real_case_id(self, service):
        entry = service.add_ticker("AMD")
        assert entry.case_id is not None and entry.case_id != ""

    def test_ticker_is_normalized(self, service):
        entry = service.add_ticker("amd")
        assert entry.ticker == "AMD"

    def test_blank_ticker_is_rejected(self, service):
        with pytest.raises(AlphaWatchlistValidationError):
            service.add_ticker("   ")

    def test_two_different_tickers_get_distinct_cases(self, service):
        amd = service.add_ticker("AMD")
        nvda = service.add_ticker("NVDA")
        assert amd.case_id != nvda.case_id


class TestIdempotency:
    def test_adding_the_same_ticker_twice_returns_the_same_entry(self, service):
        first = service.add_ticker("AMD")
        second = service.add_ticker("AMD")
        assert first.case_id == second.case_id
        assert len(service.list_all()) == 1

    def test_repeated_addition_creates_no_duplicate_row(self, service):
        service.add_ticker("AMD")
        service.add_ticker("AMD")
        service.add_ticker("amd")
        assert len(service.list_all()) == 1


class TestCrossContextCaseReuseWithPortfolio:
    """Watchlist and Portfolio are membership contexts around the same
    company knowledge -- a ticker already linked to a Case in one must
    be reused, never duplicated, in the other."""

    def test_a_ticker_already_in_portfolio_reuses_that_case_when_added_to_watchlist(self, engine, watchlist_store):
        portfolio_store = AlphaPortfolioStore(engine)
        portfolio_store.replace(
            AlphaPortfolioState(
                established_at=_NOW,
                updated_at=_NOW,
                entry_mode=EntryMode.IMPORTED,
                holdings=(AlphaHolding(ticker="AMD", weight_percent=10.0, case_id="portfolio-case-id"),),
            )
        )
        service = AlphaWatchlistService(
            watchlist_store, _case_generation_service(engine), portfolio_store=portfolio_store
        )
        entry = service.add_ticker("AMD")
        assert entry.case_id == "portfolio-case-id"

    def test_a_ticker_with_no_portfolio_case_still_gets_a_brand_new_one(self, engine, watchlist_store):
        portfolio_store = AlphaPortfolioStore(engine)
        portfolio_store.replace(
            AlphaPortfolioState(
                established_at=_NOW,
                updated_at=_NOW,
                entry_mode=EntryMode.IMPORTED,
                holdings=(AlphaHolding(ticker="NVDA", weight_percent=10.0, case_id=None),),
            )
        )
        service = AlphaWatchlistService(
            watchlist_store, _case_generation_service(engine), portfolio_store=portfolio_store
        )
        entry = service.add_ticker("AMD")
        assert entry.case_id is not None

    def test_without_a_portfolio_store_wired_a_brand_new_case_is_still_created(self, service):
        """Omitting `portfolio_store` (the opt-in default) must never
        raise -- it degrades to always creating a new Case, exactly the
        pre-cross-context-aware behavior."""
        entry = service.add_ticker("AMD")
        assert entry.case_id is not None


class TestAutomaticEnrichment:
    def test_a_new_ticker_triggers_enrichment(self, engine, watchlist_store):
        provider = _FakeProvider(documents=(_doc("AMD"),))
        repository = SqlAlchemyBusinessRecordRepository(engine)
        service = AlphaWatchlistService(
            watchlist_store,
            _case_generation_service(engine),
            business_record_repository=repository,
            business_data_providers=(provider,),
        )
        service.add_ticker("AMD")
        assert len(repository.get_by_company("AMD")) == 1

    def test_repeated_addition_never_calls_the_provider_twice(self, engine, watchlist_store):
        provider = _FakeProvider(documents=(_doc("AMD"),))
        repository = SqlAlchemyBusinessRecordRepository(engine)
        service = AlphaWatchlistService(
            watchlist_store,
            _case_generation_service(engine),
            business_record_repository=repository,
            business_data_providers=(provider,),
        )
        service.add_ticker("AMD")
        service.add_ticker("AMD")
        assert provider.call_count == ["AMD"]

    def test_without_enrichment_dependencies_wired_add_ticker_still_succeeds(self, service):
        """Omitting `business_record_repository`/`business_data_
        providers` (the opt-in default) is a deliberate no-op, never a
        failure -- Case linkage is fully independent of enrichment."""
        entry = service.add_ticker("AMD")
        assert entry.case_id is not None

    def test_a_provider_failure_does_not_prevent_the_ticker_from_being_added(self, engine, watchlist_store):
        """Provider limitations must not corrupt or block Watchlist
        addition -- the Case and entry are created regardless."""
        failing_provider = _FakeProvider(exception=RuntimeError("network unavailable"))
        repository = SqlAlchemyBusinessRecordRepository(engine)
        service = AlphaWatchlistService(
            watchlist_store,
            _case_generation_service(engine),
            business_record_repository=repository,
            business_data_providers=(failing_provider,),
        )
        entry = service.add_ticker("AMD")
        assert entry.case_id is not None
        assert entry in service.list_all()
        assert repository.get_by_company("AMD") == ()

    def test_partial_provider_failure_still_persists_the_succeeding_provider(self, engine, watchlist_store):
        failing = _FakeProvider(exception=RuntimeError("SEC EDGAR: not a US filer"))
        succeeding = _FakeProvider(documents=(_doc("AMD"),))
        repository = SqlAlchemyBusinessRecordRepository(engine)
        service = AlphaWatchlistService(
            watchlist_store,
            _case_generation_service(engine),
            business_record_repository=repository,
            business_data_providers=(failing, succeeding),
        )
        service.add_ticker("AMD")
        assert len(repository.get_by_company("AMD")) == 1
