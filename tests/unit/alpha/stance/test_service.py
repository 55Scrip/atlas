"""Tests for `atlas.alpha.stance.service.StanceService`'s
request-scoped memoization of `assess_for_case` (Decision Layer
Runtime Verification sprint) -- `assess_for_case` was measured being
called up to 111 times for one Case within a single
`/decision-explanation/{id}` request, the same real harness style
`tests/unit/alpha/portfolio_fit/test_service.py` already established.
`atlas.alpha.stance.test_engine` already covers the pure Stance logic;
this file is service-orchestration-only, mirroring
`InvestmentCaseCompositionService._build_cache`'s own pattern."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.investment_case_change.table import create_investment_case_snapshot_table
from atlas.alpha.portfolio.service import AlphaPortfolioService, ImportHoldingInput, ImportPortfolioRequest
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio.trade_log_table import create_alpha_trade_log_table
from atlas.alpha.portfolio_fit.service import PortfolioFitService
from atlas.alpha.stance.service import StanceService
from atlas.alpha.watchlist.models import AlphaWatchlistEntry
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.alpha.watchlist.table import create_alpha_watchlist_entry_table
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


class _Harness:
    def __init__(self, engine):
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
        self.portfolio_fit_service = PortfolioFitService(
            portfolio_store=self.portfolio_store,
            watchlist_store=self.watchlist_store,
            composition_service=self.composition_service,
        )
        self.stance_service = StanceService(
            composition_service=self.composition_service,
            portfolio_fit_service=self.portfolio_fit_service,
            portfolio_store=self.portfolio_store,
            watchlist_store=self.watchlist_store,
        )

    def import_holding(self, ticker: str, weight_percent: float = 100.0) -> str:
        return self.import_holdings({ticker: weight_percent})[ticker]

    def import_holdings(self, weights_by_ticker: dict[str, float]) -> dict[str, str]:
        state = self.portfolio_service.import_portfolio(
            ImportPortfolioRequest(
                holdings=tuple(
                    ImportHoldingInput(ticker=ticker, weight_percent=weight_percent)
                    for ticker, weight_percent in weights_by_ticker.items()
                )
            )
        )
        return {h.ticker: h.case_id for h in state.holdings if h.ticker in weights_by_ticker}

    def add_to_watchlist(self, ticker: str) -> str:
        case = self.case_service.create()
        case_id = str(case.id)
        self.watchlist_store.add(AlphaWatchlistEntry(ticker=ticker, case_id=case_id, added_at=_NOW))
        return case_id


@pytest.fixture
def harness() -> _Harness:
    return _Harness(_new_engine())


class TestRequestScopedMemoization:
    """Decision Layer Runtime Verification sprint: `assess_for_case` was
    measured being called up to 111 times for one Case within a single
    `/decision-explanation/{id}` request. These tests verify the
    request-scoped fix, mirroring
    `InvestmentCaseCompositionService._build_cache`'s own pattern."""

    def test_same_case_id_is_computed_only_once_per_instance(self, harness, monkeypatch):
        case_id = harness.import_holding("AAPL")
        calls = {"n": 0}
        original = harness.stance_service._assess

        def counting(*args, **kwargs):
            calls["n"] += 1
            return original(*args, **kwargs)

        monkeypatch.setattr(harness.stance_service, "_assess", counting)

        harness.stance_service.assess_for_case(case_id)
        harness.stance_service.assess_for_case(case_id)
        harness.stance_service.assess_for_case(case_id)

        assert calls["n"] == 1

    def test_repeated_calls_return_the_identical_cached_object(self, harness):
        case_id = harness.import_holding("AAPL")
        first = harness.stance_service.assess_for_case(case_id)
        second = harness.stance_service.assess_for_case(case_id)
        assert first is second

    def test_different_cases_are_still_computed_separately(self, harness, monkeypatch):
        case_ids = harness.import_holdings({"AAPL": 50.0, "MSFT": 50.0})
        calls = {"n": 0}
        original = harness.stance_service._assess

        def counting(*args, **kwargs):
            calls["n"] += 1
            return original(*args, **kwargs)

        monkeypatch.setattr(harness.stance_service, "_assess", counting)

        result_a = harness.stance_service.assess_for_case(case_ids["AAPL"])
        result_b = harness.stance_service.assess_for_case(case_ids["MSFT"])

        assert calls["n"] == 2
        assert result_a is not None and result_b is not None

    def test_no_state_leaks_between_service_instances(self, harness):
        case_id = harness.import_holding("AAPL")
        harness.stance_service.assess_for_case(case_id)

        second_service = StanceService(
            composition_service=harness.composition_service,
            portfolio_fit_service=harness.portfolio_fit_service,
            portfolio_store=harness.portfolio_store,
            watchlist_store=harness.watchlist_store,
        )
        calls = {"n": 0}
        original = second_service._assess

        def counting(*args, **kwargs):
            calls["n"] += 1
            return original(*args, **kwargs)

        second_service._assess = counting
        second_service.assess_for_case(case_id)

        assert calls["n"] == 1

    def test_unknown_case_id_returns_none_and_is_still_cached(self, harness, monkeypatch):
        """`None` (Case does not resolve) is a deterministic result too
        -- caching it avoids repeated failed lookups within the same
        request."""
        calls = {"n": 0}
        original = harness.stance_service._assess

        def counting(*args, **kwargs):
            calls["n"] += 1
            return original(*args, **kwargs)

        monkeypatch.setattr(harness.stance_service, "_assess", counting)

        unknown_case_id = "00000000-0000-0000-0000-000000000000"
        first = harness.stance_service.assess_for_case(unknown_case_id)
        second = harness.stance_service.assess_for_case(unknown_case_id)

        assert first is None
        assert second is None
        assert calls["n"] == 1
