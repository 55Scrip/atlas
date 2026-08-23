"""Tests for `atlas.alpha.portfolio_fit.service.PortfolioFitService`,
built through the real, unmodified Case/Portfolio/Watchlist persistence --
the identical harness style `tests/unit/alpha/daily_brief/test_service.py`
already establishes. These are the Deliverable 10 tests: same input
always produces the same `PortfolioFitAssessment`, and the same engine
call underlies every one of the service's public methods (Portfolio,
Investment Case, and Discovery all end up calling the identical
`_assess`/`assess_portfolio_fit` path -- no duplicated logic)."""
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
from atlas.alpha.portfolio_fit.models import FitRating
from atlas.alpha.portfolio_fit.service import PortfolioFitService
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
        self.fit_service = PortfolioFitService(
            portfolio_store=self.portfolio_store,
            watchlist_store=self.watchlist_store,
            composition_service=self.composition_service,
        )

    def import_holding(self, ticker: str, weight_percent: float = 100.0) -> str:
        return self.import_holdings({ticker: weight_percent})[ticker]

    def import_holdings(self, weights_by_ticker: dict[str, float]) -> dict[str, str]:
        """`AlphaPortfolioService.import_portfolio` *replaces* the whole
        portfolio state on every call (own docstring: "establish or
        re-establish") -- importing tickers one at a time would silently
        wipe out every previously-imported holding, so a multi-holding
        scenario must go through one call."""
        state = self.portfolio_service.import_portfolio(
            ImportPortfolioRequest(
                holdings=tuple(
                    ImportHoldingInput(ticker=ticker, weight_percent=weight_percent)
                    for ticker, weight_percent in weights_by_ticker.items()
                )
            )
        )
        case_ids = {h.ticker: h.case_id for h in state.holdings if h.ticker in weights_by_ticker}
        assert all(case_id is not None for case_id in case_ids.values())
        return case_ids  # type: ignore[return-value]

    def add_to_watchlist(self, ticker: str) -> str:
        case = self.case_service.create()
        case_id = str(case.id)
        self.watchlist_store.add(AlphaWatchlistEntry(ticker=ticker, case_id=case_id, added_at=_NOW))
        return case_id


@pytest.fixture
def harness() -> _Harness:
    return _Harness(_new_engine())


class TestDeterminism:
    """Deliverable 10: same input always produces the same Portfolio Fit."""

    def test_assessing_the_same_case_twice_produces_an_identical_overall_rating(self, harness):
        case_id = harness.import_holding("AAPL")
        first = harness.fit_service.assess_for_case(case_id)
        second = harness.fit_service.assess_for_case(case_id)
        assert first is not None and second is not None
        assert first.overall == second.overall
        assert first.dimensions == second.dimensions

    def test_unknown_case_id_returns_none_not_a_fabricated_assessment(self, harness):
        assert harness.fit_service.assess_for_case("00000000-0000-0000-0000-000000000000") is None

    def test_unknown_ticker_returns_none(self, harness):
        assert harness.fit_service.assess_for_ticker("ZZZZ") is None


class TestSameEngineEverywhere:
    """Deliverable 10: Portfolio, Investment Case, and Discovery all read
    the identical assessment for the same Case -- proven here by checking
    every public entry point produces the exact same `overall`/`dimensions`
    for one Case, not three independently-derived answers."""

    def test_holding_appears_identically_via_case_ticker_and_holdings_listing(self, harness):
        case_id = harness.import_holding("MSFT")

        by_case = harness.fit_service.assess_for_case(case_id)
        by_ticker = harness.fit_service.assess_for_ticker("MSFT")
        via_holdings = next(a for a in harness.fit_service.assess_all_holdings() if a.case_id == case_id)

        assert by_case.overall == by_ticker.overall == via_holdings.overall
        assert by_case.dimensions == by_ticker.dimensions == via_holdings.dimensions

    def test_watchlist_candidate_appears_identically_via_ticker_and_candidate_ranking(self, harness):
        case_id = harness.add_to_watchlist("NVDA")

        by_ticker = harness.fit_service.assess_for_ticker("NVDA")
        via_candidates = next(a for a in harness.fit_service.rank_candidates() if a.case_id == case_id)

        assert by_ticker.overall == via_candidates.overall
        assert by_ticker.dimensions == via_candidates.dimensions


class TestTickerResolution:
    """Regression test for a real bug found during this sprint's own
    live browser verification: a Watchlist-only candidate's `ticker`
    field was falling back to the raw `case_id` UUID, because
    `composition.holding_context` only ever resolves a *Portfolio*
    holding, never a Watchlist one."""

    def test_a_watchlist_only_candidates_ticker_is_never_the_raw_case_id(self, harness):
        case_id = harness.add_to_watchlist("NVDA")
        assessment = next(a for a in harness.fit_service.rank_candidates() if a.case_id == case_id)
        assert assessment.ticker == "NVDA"
        assert assessment.ticker != case_id

    def test_assess_for_case_also_resolves_a_watchlist_only_ticker_correctly(self, harness):
        case_id = harness.add_to_watchlist("NVDA")
        assessment = harness.fit_service.assess_for_case(case_id)
        assert assessment is not None
        assert assessment.ticker == "NVDA"


class TestHoldingsVsCandidates:
    def test_an_existing_holding_is_never_listed_as_a_candidate(self, harness):
        case_id = harness.import_holding("TSLA")
        candidates = harness.fit_service.rank_candidates()
        assert all(a.case_id != case_id for a in candidates)

    def test_a_watchlist_only_ticker_is_not_in_holdings(self, harness):
        case_id = harness.add_to_watchlist("AMD")
        holdings = harness.fit_service.assess_all_holdings()
        assert all(a.case_id != case_id for a in holdings)

    def test_existing_holding_reports_a_real_weight_a_candidate_does_not(self, harness):
        harness.import_holding("GOOGL", weight_percent=42.0)
        candidate_case_id = harness.add_to_watchlist("META")

        holding_assessment = next(a for a in harness.fit_service.assess_all_holdings() if a.ticker == "GOOGL")
        candidate_assessment = next(a for a in harness.fit_service.rank_candidates() if a.case_id == candidate_case_id)

        assert holding_assessment.is_existing_holding is True
        assert holding_assessment.current_weight_percent == pytest.approx(42.0)
        assert candidate_assessment.is_existing_holding is False
        assert candidate_assessment.current_weight_percent is None


class TestComparison:
    def test_comparing_two_real_cases_returns_a_verdict_grounded_in_both_assessments(self, harness):
        harness.import_holdings({"AAPL": 50.0, "MSFT": 50.0})

        comparison = harness.fit_service.compare("AAPL", "MSFT")

        assert comparison is not None
        assert comparison.assessment_a.ticker == "AAPL"
        assert comparison.assessment_b.ticker == "MSFT"
        assert comparison.preferred_ticker in (None, "AAPL", "MSFT")

    def test_comparing_against_an_unknown_ticker_returns_none(self, harness):
        harness.import_holding("AAPL")
        assert harness.fit_service.compare("AAPL", "ZZZZ") is None


class TestNoPersistence:
    """Deliverable 9: this engine stores nothing of its own -- proven by
    showing a fresh `PortfolioFitService` (a brand-new instance, same
    underlying stores) produces the identical result with no state
    carried between service instances."""

    def test_a_brand_new_service_instance_produces_the_identical_assessment(self, harness):
        case_id = harness.import_holding("AAPL")
        first = harness.fit_service.assess_for_case(case_id)

        second_service = PortfolioFitService(
            portfolio_store=harness.portfolio_store,
            watchlist_store=harness.watchlist_store,
            composition_service=harness.composition_service,
        )
        second = second_service.assess_for_case(case_id)

        assert first.overall == second.overall
        assert first.dimensions == second.dimensions
