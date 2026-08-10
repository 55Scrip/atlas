"""Tests for `atlas.alpha.daily_brief.service.DailyBriefService`, built
through the real, unmodified Case/Portfolio/Watchlist/BusinessRecord/
Change-Intelligence persistence -- exactly the "nothing mocked below the
composition service" style `tests/unit/alpha/investment_case
/test_service.py` already establishes."""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.daily_brief.service import DailyBriefService
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.investment_case_change.table import create_investment_case_snapshot_table
from atlas.alpha.portfolio.service import AlphaPortfolioService, ImportHoldingInput, ImportPortfolioRequest
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio.trade_log_table import create_alpha_trade_log_table
from atlas.alpha.watchlist.models import AlphaWatchlistEntry
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.alpha.watchlist.table import create_alpha_watchlist_entry_table
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.core.application.case.create_case import CaseService
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
from atlas.core.infrastructure.api.evidence.dependencies import get_evidence_repository
from atlas.core.infrastructure.api.knowledge_reference.dependencies import get_outcome_repository
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository
from atlas.core.infrastructure.persistence.decision.table import create_decision_table

_NOW = datetime.now(timezone.utc)


def _new_engine():
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_decision_table(engine)
    create_alpha_portfolio_state_table(engine)
    create_alpha_trade_log_table(engine)
    create_business_record_table(engine)
    create_alpha_watchlist_entry_table(engine)
    create_investment_case_snapshot_table(engine)
    return engine


def _growth_record(*, company: str, identifier: str, period_end, revenue: float, free_cash_flow: float):
    document = RawBusinessDocument(
        identifier=identifier,
        company=company,
        source_kind="annual_report",
        published_at=_NOW,
        provider_id="structured_test",
        raw_reference=f"ref://{identifier}",
        content_hash=f"hash-{identifier}",
        language="en",
        period_end=period_end,
        metadata={"revenue": revenue, "free_cash_flow": free_cash_flow},
    )
    result = ingest(document, evaluated_at=_NOW)
    assert isinstance(result, IngestedRecord)
    return result.record


class _Harness:
    def __init__(self, engine):
        self.engine = engine
        self.case_repository = get_case_repository(engine)
        self.case_service = CaseService(self.case_repository)
        self.decision_repository = get_decision_repository(engine)
        self.observation_repository = get_observation_repository(engine)
        self.evidence_repository = get_evidence_repository(engine)
        self.outcome_repository = get_outcome_repository(engine)
        self.portfolio_store = AlphaPortfolioStore(engine)
        self.trade_log_store = AlphaTradeLogStore(engine)
        self.business_record_repository = SqlAlchemyBusinessRecordRepository(engine)
        self.watchlist_store = AlphaWatchlistStore(engine)
        self.snapshot_repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        self.case_generation_service = CaseGenerationService(self.case_service)
        self.portfolio_service = AlphaPortfolioService(
            self.portfolio_store, self.trade_log_store, None, self.case_generation_service
        )
        self.composition_service = InvestmentCaseCompositionService(
            self.case_repository,
            self.decision_repository,
            self.observation_repository,
            self.evidence_repository,
            self.outcome_repository,
            self.portfolio_store,
            self.trade_log_store,
            self.business_record_repository,
            watchlist_store=self.watchlist_store,
            snapshot_repository=self.snapshot_repository,
        )
        self.daily_brief_service = DailyBriefService(
            portfolio_store=self.portfolio_store,
            watchlist_store=self.watchlist_store,
            investment_case_composition_service=self.composition_service,
        )

    def import_holding(self, ticker: str, weight_percent: float = 100.0) -> str:
        state = self.portfolio_service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker=ticker, weight_percent=weight_percent),))
        )
        case_id = next(h for h in state.holdings if h.ticker == ticker).case_id
        assert case_id is not None
        return case_id

    def add_to_watchlist(self, ticker: str) -> str:
        case = self.case_service.create()
        case_id = str(case.id)
        self.watchlist_store.add(AlphaWatchlistEntry(ticker=ticker, case_id=case_id, added_at=_NOW))
        return case_id

    def make_growth_worsen(self, ticker: str) -> None:
        """Ingests a fixture that, added to whatever this ticker already
        has, moves Growth from STRONG to WEAK -- the exact fixture shape
        `tests/unit/analysis_engine/test_growth.py`'s own Scenario B
        already proves produces WEAK."""
        self.business_record_repository.add(
            _growth_record(company=ticker, identifier=f"{ticker}-fy22", period_end=date(2022, 12, 31), revenue=1250.0, free_cash_flow=300.0)
        )
        self.business_record_repository.add(
            _growth_record(company=ticker, identifier=f"{ticker}-fy23", period_end=date(2023, 12, 31), revenue=1100.0, free_cash_flow=240.0)
        )
        self.business_record_repository.add(
            _growth_record(company=ticker, identifier=f"{ticker}-fy24", period_end=date(2024, 12, 31), revenue=1000.0, free_cash_flow=200.0)
        )


@pytest.fixture
def harness() -> _Harness:
    return _Harness(_new_engine())


class TestEmptyPortfolioAndWatchlist:
    """Scenario: empty brief."""

    def test_no_holdings_and_no_watchlist_produces_an_empty_brief(self, harness):
        brief = harness.daily_brief_service.build_daily_brief()
        assert brief.entries == ()
        assert brief.summary == "No material analytical changes since your previous review."


class TestBaselineIsNotAChange:
    def test_first_ever_build_for_a_holding_produces_no_entry(self, harness):
        harness.import_holding("NVDA")
        brief = harness.daily_brief_service.build_daily_brief()
        assert brief.entries == ()


class TestOneCompanyChanged:
    def test_a_real_growth_transition_appears_in_the_brief(self, harness):
        case_id = harness.import_holding("NVDA")
        harness.make_growth_worsen("NVDA")
        harness.composition_service.build(case_id)  # baseline

        # New data arrives: reverse the trend to STRONG.
        harness.business_record_repository.add(
            _growth_record(company="NVDA", identifier="NVDA-fy25", period_end=date(2025, 12, 31), revenue=2000.0, free_cash_flow=600.0)
        )
        harness.business_record_repository.add(
            _growth_record(company="NVDA", identifier="NVDA-fy26", period_end=date(2026, 12, 31), revenue=3000.0, free_cash_flow=900.0)
        )

        brief = harness.daily_brief_service.build_daily_brief()
        assert len(brief.entries) == 1
        assert brief.entries[0].ticker == "NVDA"
        assert brief.entries[0].case_id == case_id


class TestPortfolioAndWatchlistMix:
    """Scenario: Portfolio + Watchlist."""

    def test_both_a_holding_and_a_watchlist_entry_can_appear(self, harness):
        held_case_id = harness.import_holding("NVDA")
        watched_case_id = harness.add_to_watchlist("META")

        for ticker, case_id in (("NVDA", held_case_id), ("META", watched_case_id)):
            harness.make_growth_worsen(ticker)
            harness.composition_service.build(case_id)  # baseline for each
            harness.business_record_repository.add(
                _growth_record(company=ticker, identifier=f"{ticker}-fy25", period_end=date(2025, 12, 31), revenue=2000.0, free_cash_flow=600.0)
            )
            harness.business_record_repository.add(
                _growth_record(company=ticker, identifier=f"{ticker}-fy26", period_end=date(2026, 12, 31), revenue=3000.0, free_cash_flow=900.0)
            )

        brief = harness.daily_brief_service.build_daily_brief()
        assert {e.ticker for e in brief.entries} == {"NVDA", "META"}
        # Alphabetical ordering, regardless of Portfolio/Watchlist origin.
        assert [e.ticker for e in brief.entries] == ["META", "NVDA"]

    def test_a_case_id_that_is_both_held_and_watchlisted_appears_only_once(self, harness):
        case_id = harness.import_holding("NVDA")
        harness.watchlist_store.add(AlphaWatchlistEntry(ticker="NVDA", case_id=case_id, added_at=_NOW))
        harness.make_growth_worsen("NVDA")
        harness.composition_service.build(case_id)
        harness.business_record_repository.add(
            _growth_record(company="NVDA", identifier="NVDA-fy25", period_end=date(2025, 12, 31), revenue=2000.0, free_cash_flow=600.0)
        )
        harness.business_record_repository.add(
            _growth_record(company="NVDA", identifier="NVDA-fy26", period_end=date(2026, 12, 31), revenue=3000.0, free_cash_flow=900.0)
        )
        brief = harness.daily_brief_service.build_daily_brief()
        assert len(brief.entries) == 1


class TestUnchangedCompanyIsExcluded:
    def test_a_second_build_with_no_new_data_is_excluded(self, harness):
        case_id = harness.import_holding("AAPL")
        harness.composition_service.build(case_id)  # baseline
        harness.composition_service.build(case_id)  # unchanged
        brief = harness.daily_brief_service.build_daily_brief()
        assert brief.entries == ()
