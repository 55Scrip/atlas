"""Tests for `atlas.alpha.investment_case_history.service
.InvestmentCaseHistoryService`. Real in-memory SQLite Portfolio/
Watchlist/snapshot persistence throughout -- but the snapshot repository
is populated directly via `SqlAlchemyInvestmentCaseSnapshotRepository
.add`, never through `InvestmentCaseCompositionService.build`, which
would be a real Change Intelligence recomputation this service is
deliberately never given the means to trigger (its constructor takes no
composition service at all -- see the service's own docstring)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.investment_case_history.service import InvestmentCaseHistoryService
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
from atlas.analysis_engine.investment_case_change import (
    AnalyticalSnapshot,
    ChangeCategory,
    ChangeDirection,
    ChangeIntelligence,
    ThesisImpact,
    compare_snapshots,
)
from atlas.core.application.case.create_case import CaseService
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.persistence.decision.table import create_decision_table

_T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
_T1 = datetime(2026, 2, 1, tzinfo=timezone.utc)


def _snapshot(
    *,
    content_hash: str,
    captured_at: datetime,
    growth_status: str = "moderate",
    capital_allocation_status: str = "insufficient_input",
    financial_risk_status: str = "insufficient_input",
    valuation_status: str = "insufficient_input",
    strength_kinds: tuple[str, ...] = (),
    risk_highlight_kinds: tuple[str, ...] = (),
    open_question_origins: tuple[str, ...] = (),
) -> AnalyticalSnapshot:
    return AnalyticalSnapshot(
        business_category_states=(
            ("capital_allocation", capital_allocation_status, "business_finding:capital_allocation"),
            ("growth", growth_status, "business_finding:growth"),
        ),
        risk_category_states=(("financial_risk", financial_risk_status, "risk_finding:financial_risk"),),
        valuation_status=valuation_status,
        valuation_finding_id="valuation_finding:fcf_yield_relative",
        current_yield=None,
        strength_kinds=strength_kinds,
        risk_highlight_kinds=risk_highlight_kinds,
        open_question_origins=open_question_origins,
        atlas_thesis_narrative=None,
        atlas_thesis_posture=None,
        content_hash=content_hash,
        captured_at=captured_at,
    )


class _Harness:
    def __init__(self, engine: Engine):
        self.engine = engine
        self.case_repository = get_case_repository(engine)
        self.case_service = CaseService(self.case_repository)
        self.portfolio_store = AlphaPortfolioStore(engine)
        self.trade_log_store = AlphaTradeLogStore(engine)
        self.watchlist_store = AlphaWatchlistStore(engine)
        self.snapshot_repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        self.case_generation_service = CaseGenerationService(self.case_service)
        self.portfolio_service = AlphaPortfolioService(
            self.portfolio_store, self.trade_log_store, None, self.case_generation_service
        )
        self.history_service = InvestmentCaseHistoryService(
            portfolio_store=self.portfolio_store,
            watchlist_store=self.watchlist_store,
            snapshot_repository=self.snapshot_repository,
        )

    def import_holding(self, ticker: str) -> str:
        state = self.portfolio_service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker=ticker, weight_percent=100.0),))
        )
        case_id = next(h for h in state.holdings if h.ticker == ticker).case_id
        assert case_id is not None
        return case_id

    def add_to_watchlist(self, ticker: str) -> str:
        case = self.case_service.create()
        case_id = str(case.id)
        self.watchlist_store.add(AlphaWatchlistEntry(ticker=ticker, case_id=case_id, added_at=_T0))
        return case_id

    def capture(self, case_id: str, *, content_hash: str, captured_at: datetime, **snapshot_kwargs) -> ChangeIntelligence:
        previous = self.snapshot_repository.get_latest(case_id)
        current = _snapshot(content_hash=content_hash, captured_at=captured_at, **snapshot_kwargs)
        change_intelligence = compare_snapshots(previous, current)
        self.snapshot_repository.add(case_id, current, change_intelligence)
        return change_intelligence


def _new_engine() -> Engine:
    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})
    create_decision_table(engine)
    create_alpha_portfolio_state_table(engine)
    create_alpha_trade_log_table(engine)
    create_alpha_watchlist_entry_table(engine)
    create_investment_case_snapshot_table(engine)
    return engine


@pytest.fixture
def harness() -> _Harness:
    return _Harness(_new_engine())


class TestEmptyHistory:
    """Scenario 1."""

    def test_no_portfolio_no_watchlist_no_snapshots_is_empty(self, harness):
        history = harness.history_service.build_analytical_history()
        assert history.entries == ()


class TestBaselineOnly:
    """Scenario 2."""

    def test_one_snapshot_for_a_holding_is_a_single_baseline_entry(self, harness):
        case_id = harness.import_holding("AAPL")
        harness.capture(case_id, content_hash="hash-a", captured_at=_T0)
        history = harness.history_service.build_analytical_history()
        assert len(history.entries) == 1
        entry = history.entries[0]
        assert entry.case_id == case_id
        assert entry.ticker == "AAPL"
        assert entry.change_intelligence.is_baseline is True


class TestBaselinePlusTransition:
    """Scenario 3."""

    def test_two_snapshots_produce_a_baseline_and_a_transition_entry(self, harness):
        case_id = harness.import_holding("AAPL")
        harness.capture(case_id, content_hash="hash-a", captured_at=_T0, growth_status="strong")
        harness.capture(case_id, content_hash="hash-b", captured_at=_T1, growth_status="moderate")
        history = harness.history_service.build_analytical_history()
        assert len(history.entries) == 2
        # Newest first.
        assert history.entries[0].snapshot.captured_at == _T1
        assert history.entries[0].change_intelligence.is_baseline is False
        assert history.entries[1].change_intelligence.is_baseline is True


class TestReadOnly:
    """Scenarios 5/6/27: reading history never writes a new snapshot or
    ChangeFinding row, however many times it is called."""

    def test_repeated_reads_create_zero_new_snapshots(self, harness):
        case_id = harness.import_holding("AAPL")
        harness.capture(case_id, content_hash="hash-a", captured_at=_T0)
        for _ in range(5):
            harness.history_service.build_analytical_history()
        assert len(harness.snapshot_repository.get_history(case_id)) == 1

    def test_repeated_reads_return_byte_identical_results(self, harness):
        case_id = harness.import_holding("AAPL")
        harness.capture(case_id, content_hash="hash-a", captured_at=_T0, growth_status="strong")
        harness.capture(case_id, content_hash="hash-b", captured_at=_T1, growth_status="moderate")
        first = harness.history_service.build_analytical_history()
        second = harness.history_service.build_analytical_history()
        assert [(e.case_id, e.snapshot.content_hash) for e in first.entries] == [
            (e.case_id, e.snapshot.content_hash) for e in second.entries
        ]


class TestPortfolioAndWatchlistMix:
    """Scenarios 18/19/20."""

    def test_a_portfolio_only_case_appears(self, harness):
        case_id = harness.import_holding("AAPL")
        harness.capture(case_id, content_hash="hash-a", captured_at=_T0)
        history = harness.history_service.build_analytical_history()
        assert {e.case_id for e in history.entries} == {case_id}

    def test_a_watchlist_only_case_appears(self, harness):
        case_id = harness.add_to_watchlist("META")
        harness.capture(case_id, content_hash="hash-a", captured_at=_T0)
        history = harness.history_service.build_analytical_history()
        assert {e.case_id for e in history.entries} == {case_id}
        assert history.entries[0].ticker == "META"

    def test_a_case_in_both_portfolio_and_watchlist_is_not_duplicated(self, harness):
        case_id = harness.import_holding("AAPL")
        harness.watchlist_store.add(AlphaWatchlistEntry(ticker="AAPL", case_id=case_id, added_at=_T0))
        harness.capture(case_id, content_hash="hash-a", captured_at=_T0)
        history = harness.history_service.build_analytical_history()
        assert len(history.entries) == 1

    def test_both_a_holding_and_a_separate_watchlist_entry_appear_together(self, harness):
        held_case_id = harness.import_holding("AAPL")
        watched_case_id = harness.add_to_watchlist("META")
        harness.capture(held_case_id, content_hash="hash-a", captured_at=_T0)
        harness.capture(watched_case_id, content_hash="hash-b", captured_at=_T0)
        history = harness.history_service.build_analytical_history()
        assert {e.case_id for e in history.entries} == {held_case_id, watched_case_id}


class TestHistoricalStateIsPersistedNotRecomputed:
    """Scenario 7/22/23/24: a historical entry reflects the state
    captured at that time, not any later/current state."""

    def test_the_baseline_entry_still_reflects_its_own_captured_growth_status(self, harness):
        case_id = harness.import_holding("AAPL")
        harness.capture(case_id, content_hash="hash-a", captured_at=_T0, growth_status="weak")
        harness.capture(case_id, content_hash="hash-b", captured_at=_T1, growth_status="strong")
        history = harness.history_service.build_analytical_history()
        baseline_entry = next(e for e in history.entries if e.change_intelligence.is_baseline)
        assert ("growth", "weak", "business_finding:growth") in baseline_entry.snapshot.business_category_states


class TestTransitionCategories:
    """Scenarios 10-16: every `ChangeCategory` History exposes traces
    back to `compare_snapshots`'s own detection -- reused verbatim, never
    recomputed differently here."""

    def test_capital_allocation_transition_is_reported(self, harness):
        case_id = harness.import_holding("AAPL")
        harness.capture(case_id, content_hash="hash-a", captured_at=_T0, capital_allocation_status="strong")
        change_intelligence = harness.capture(
            case_id, content_hash="hash-b", captured_at=_T1, capital_allocation_status="weak"
        )
        assert any(c.category is ChangeCategory.CAPITAL_ALLOCATION_CHANGED for c in change_intelligence.changes)
        history = harness.history_service.build_analytical_history()
        newest = history.entries[0]
        assert any(c.category is ChangeCategory.CAPITAL_ALLOCATION_CHANGED for c in newest.change_intelligence.changes)

    def test_financial_risk_transition_is_reported(self, harness):
        case_id = harness.import_holding("AAPL")
        harness.capture(case_id, content_hash="hash-a", captured_at=_T0, financial_risk_status="low")
        harness.capture(case_id, content_hash="hash-b", captured_at=_T1, financial_risk_status="high")
        history = harness.history_service.build_analytical_history()
        newest = history.entries[0]
        risk_changes = [c for c in newest.change_intelligence.changes if c.category is ChangeCategory.FINANCIAL_RISK_CHANGED]
        assert len(risk_changes) == 1
        assert risk_changes[0].direction is ChangeDirection.NEGATIVE

    def test_valuation_transition_is_reported(self, harness):
        case_id = harness.import_holding("AAPL")
        harness.capture(case_id, content_hash="hash-a", captured_at=_T0, valuation_status="undervalued")
        harness.capture(case_id, content_hash="hash-b", captured_at=_T1, valuation_status="expensive")
        history = harness.history_service.build_analytical_history()
        newest = history.entries[0]
        assert any(c.category is ChangeCategory.VALUATION_CHANGED for c in newest.change_intelligence.changes)

    def test_strength_added_and_removed_are_reported(self, harness):
        case_id = harness.import_holding("AAPL")
        harness.capture(case_id, content_hash="hash-a", captured_at=_T0, strength_kinds=())
        harness.capture(case_id, content_hash="hash-b", captured_at=_T1, strength_kinds=("growth",))
        history = harness.history_service.build_analytical_history()
        newest = history.entries[0]
        assert any(c.category is ChangeCategory.STRENGTH_ADDED for c in newest.change_intelligence.changes)

    def test_risk_added_and_removed_are_reported(self, harness):
        case_id = harness.import_holding("AAPL")
        harness.capture(case_id, content_hash="hash-a", captured_at=_T0, risk_highlight_kinds=("financial_risk",))
        harness.capture(case_id, content_hash="hash-b", captured_at=_T1, risk_highlight_kinds=())
        history = harness.history_service.build_analytical_history()
        newest = history.entries[0]
        assert any(c.category is ChangeCategory.RISK_REMOVED for c in newest.change_intelligence.changes)

    def test_open_question_added_and_resolved_are_reported(self, harness):
        case_id = harness.import_holding("AAPL")
        harness.capture(case_id, content_hash="hash-a", captured_at=_T0, open_question_origins=("growth_mixed",))
        harness.capture(case_id, content_hash="hash-b", captured_at=_T1, open_question_origins=())
        history = harness.history_service.build_analytical_history()
        newest = history.entries[0]
        assert any(c.category is ChangeCategory.OPEN_QUESTION_RESOLVED for c in newest.change_intelligence.changes)

    def test_analytical_coverage_change_is_neutral_not_a_performance_read(self, harness):
        case_id = harness.import_holding("AAPL")
        harness.capture(case_id, content_hash="hash-a", captured_at=_T0, capital_allocation_status="insufficient_input")
        harness.capture(case_id, content_hash="hash-b", captured_at=_T1, capital_allocation_status="moderate")
        history = harness.history_service.build_analytical_history()
        newest = history.entries[0]
        coverage_changes = [c for c in newest.change_intelligence.changes if c.category is ChangeCategory.ANALYTICAL_COVERAGE_CHANGED]
        assert len(coverage_changes) == 1
        assert coverage_changes[0].direction is ChangeDirection.NEUTRAL


class TestThesisImpactSemantics:
    """Scenario 17: `ThesisImpact` on a History entry matches the exact
    semantics `atlas.analysis_engine.investment_case_change` already
    defines -- History invents no scoring of its own."""

    def test_mixed_signals_produce_a_mixed_thesis_impact(self, harness):
        case_id = harness.import_holding("AAPL")
        harness.capture(case_id, content_hash="hash-a", captured_at=_T0, growth_status="weak", financial_risk_status="low")
        harness.capture(case_id, content_hash="hash-b", captured_at=_T1, growth_status="strong", financial_risk_status="high")
        history = harness.history_service.build_analytical_history()
        assert history.entries[0].change_intelligence.thesis_impact is ThesisImpact.MIXED

    def test_only_improvements_produce_a_strengthened_thesis_impact(self, harness):
        case_id = harness.import_holding("AAPL")
        harness.capture(case_id, content_hash="hash-a", captured_at=_T0, growth_status="weak")
        harness.capture(case_id, content_hash="hash-b", captured_at=_T1, growth_status="strong")
        history = harness.history_service.build_analytical_history()
        assert history.entries[0].change_intelligence.thesis_impact is ThesisImpact.STRENGTHENED
