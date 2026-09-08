"""The invariant this sprint exists for, end to end.

A Case is about an instrument. Watchlist and Portfolio describe the
investor's relationship to that instrument. The relationship must not
be what gives the Case its identity.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.case_instrument.repository import CaseInstrumentBindingRepository
from atlas.alpha.case_instrument.table import create_case_instrument_binding_table
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio.trade_log_table import create_alpha_trade_log_table
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.alpha.watchlist.table import create_alpha_watchlist_entry_table
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.core.application.case.create_case import CaseService
from atlas.core.infrastructure.persistence.case.sqlalchemy_repository import SqlAlchemyCaseRepository
from atlas.core.infrastructure.persistence.case.table import create_case_table
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import SqlAlchemyDecisionRepository
from atlas.core.infrastructure.persistence.decision.table import create_decision_table
from atlas.core.infrastructure.persistence.evidence.sqlalchemy_repository import SqlAlchemyEvidenceRepository
from atlas.core.infrastructure.persistence.evidence.table import create_evidence_table
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
)
from atlas.core.infrastructure.persistence.observation.table import create_observation_table
from atlas.core.infrastructure.persistence.outcome.sqlalchemy_repository import SqlAlchemyOutcomeRepository
from atlas.core.infrastructure.persistence.outcome.table import create_outcome_table

_NOW = datetime(2026, 9, 8, tzinfo=timezone.utc)


class _Harness:
    def __init__(self) -> None:
        self.engine = create_engine(
            "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
        )
        for create in (
            create_case_table, create_decision_table, create_observation_table, create_evidence_table,
            create_outcome_table, create_business_record_table, create_alpha_portfolio_state_table,
            create_alpha_trade_log_table, create_alpha_watchlist_entry_table,
            create_case_instrument_binding_table,
        ):
            create(self.engine)

        self.bindings = CaseInstrumentBindingRepository(self.engine)
        self.portfolio = AlphaPortfolioStore(self.engine)
        self.watchlist = AlphaWatchlistStore(self.engine)
        self.records = SqlAlchemyBusinessRecordRepository(self.engine)
        case_repository = SqlAlchemyCaseRepository(self.engine)
        self.case_repository = case_repository
        self.generation = CaseGenerationService(CaseService(case_repository), self.bindings)
        self.composition = InvestmentCaseCompositionService(
            case_repository=case_repository,
            decision_repository=SqlAlchemyDecisionRepository(self.engine),
            observation_repository=SqlAlchemyObservationRepository(self.engine),
            evidence_repository=SqlAlchemyEvidenceRepository(self.engine),
            outcome_repository=SqlAlchemyOutcomeRepository(self.engine),
            portfolio_store=self.portfolio,
            trade_log_store=AlphaTradeLogStore(self.engine),
            business_record_repository=self.records,
            watchlist_store=self.watchlist,
            binding_repository=self.bindings,
        )

    def ingest_company(self, ticker: str, name: str) -> None:
        """Persist a company profile and one financial period, the same
        way real enrichment does."""
        from datetime import date

        for identifier, kind, period_end, metadata in (
            ("profile", "company_profile", None, {"name": name, "sector": "TECHNOLOGY"}),
            ("fy2024", "financial_statement", date(2024, 12, 31), {"revenue": 4000.0, "free_cash_flow": 900.0}),
            ("fy2025", "financial_statement", date(2025, 12, 31), {"revenue": 5000.0, "free_cash_flow": 1200.0}),
        ):
            document = RawBusinessDocument(
                identifier=f"{ticker}:{identifier}",
                company=ticker,
                source_kind=kind,
                published_at=_NOW,
                provider_id="test",
                raw_reference=f"ref://{ticker}/{identifier}",
                content_hash=f"{ticker}-{identifier}",
                language="en",
                period_end=period_end,
                metadata=metadata,
            )
            result = ingest(document, evaluated_at=_NOW)
            assert isinstance(result, IngestedRecord)
            self.records.add(result.record)


@pytest.fixture
def harness():
    return _Harness()


class TestMembershiplessCase:
    def test_a_case_with_no_membership_still_knows_its_company(self, harness):
        """The exact scenario that failed before this sprint: the Case
        came back with no profile, no facts and no coverage."""
        harness.ingest_company("ASML", "ASML Holding NV")
        case_id = harness.generation.ensure_case_id(current_case_id=None, ticker="ASML")

        assert harness.watchlist.get_by_ticker_including_removed("ASML") is None
        assert harness.portfolio.get() is None

        composition = harness.composition.build(case_id)
        assert composition is not None
        assert composition.company_profile is not None
        assert composition.company_profile.name == "ASML Holding NV"
        assert composition.business_facts

    def test_ensure_writes_the_binding_immediately(self, harness):
        case_id = harness.generation.ensure_case_id(current_case_id=None, ticker="ASML")
        stored = harness.bindings.get_by_case_id(case_id)
        assert stored is not None and stored.instrument_key == "ASML"

    def test_ensure_reuses_the_bound_case_rather_than_duplicating(self, harness):
        first = harness.generation.ensure_case_id(current_case_id=None, ticker="ASML")
        second = harness.generation.ensure_case_id(current_case_id=None, ticker="ASML")
        assert first == second
        assert len(harness.bindings.list_all()) == 1

    def test_distinct_instruments_get_distinct_cases(self, harness):
        goog = harness.generation.ensure_case_id(current_case_id=None, ticker="GOOG")
        googl = harness.generation.ensure_case_id(current_case_id=None, ticker="GOOGL")
        assert goog != googl

    def test_su_pa_and_su_never_share_a_case(self, harness):
        schneider = harness.generation.ensure_case_id(current_case_id=None, ticker="SU.PA")
        suncor = harness.generation.ensure_case_id(current_case_id=None, ticker="SU")
        assert schneider != suncor


class TestEnsureTouchesNothingElse:
    def test_it_creates_no_watchlist_membership(self, harness):
        harness.generation.ensure_case_id(current_case_id=None, ticker="ASML")
        assert harness.watchlist.list_all() == ()
        assert harness.watchlist.get_by_ticker_including_removed("ASML") is None

    def test_it_creates_no_portfolio_membership(self, harness):
        harness.generation.ensure_case_id(current_case_id=None, ticker="ASML")
        assert harness.portfolio.get() is None

    def test_it_records_no_decision(self, harness):
        case_id = harness.generation.ensure_case_id(current_case_id=None, ticker="ASML")
        composition = harness.composition.build(case_id)
        assert composition.decision_history == ()
        assert composition.observation_history == ()


class TestIdentityResolutionIsLocal:
    def test_resolution_needs_no_provider_of_any_kind(self, harness):
        """`CaseGenerationService` and the binding repository are
        constructed from a Case repository and an engine. Neither can
        reach a provider, a quota tracker or a refresh coordinator --
        there is nowhere for one to enter."""
        harness.ingest_company("ASML", "ASML Holding NV")
        case_id = harness.generation.ensure_case_id(current_case_id=None, ticker="ASML")
        assert harness.bindings.get_by_case_id(case_id).instrument_key == "ASML"

        import inspect

        for service in (harness.generation, harness.bindings):
            source = inspect.getsource(type(service))
            for forbidden in ("provider", "alpha_vantage", "quota", "refresh"):
                assert forbidden not in source.lower(), f"{type(service).__name__} mentions {forbidden}"


class TestBindingIsTheAuthorityNotMembership:
    def test_the_binding_wins_over_membership(self, harness):
        """A Case bound to one instrument keeps resolving to it even
        when a membership row would have named another. Membership is
        no longer consulted once a binding exists."""
        harness.ingest_company("ASML", "ASML Holding NV")
        harness.ingest_company("AAPL", "Apple Inc")
        case_id = harness.generation.ensure_case_id(current_case_id=None, ticker="ASML")

        from atlas.alpha.watchlist.models import AlphaWatchlistEntry

        harness.watchlist.add(AlphaWatchlistEntry(ticker="AAPL", case_id=case_id, added_at=_NOW))

        composition = harness.composition.build(case_id)
        assert composition.company_profile.name == "ASML Holding NV"

    def test_an_unbound_legacy_case_still_resolves_through_membership(self, harness):
        """The documented compatibility fallback: a Case written before
        the binding table existed, and not yet backfilled."""
        from atlas.alpha.watchlist.models import AlphaWatchlistEntry

        harness.ingest_company("MU", "Micron Technology Inc")
        legacy_case_id = str(CaseService(harness.case_repository).create().id)
        harness.watchlist.add(AlphaWatchlistEntry(ticker="MU", case_id=legacy_case_id, added_at=_NOW))
        assert harness.bindings.get_by_case_id(legacy_case_id) is None

        composition = harness.composition.build(legacy_case_id)
        assert composition.company_profile.name == "Micron Technology Inc"

    def test_a_case_with_neither_binding_nor_membership_fails_honestly(self, harness):
        orphan = str(CaseService(harness.case_repository).create().id)
        composition = harness.composition.build(orphan)
        # Not an exception and not a guess -- an honest empty result.
        assert composition is not None
        assert composition.company_profile is None
        assert composition.business_facts == ()
