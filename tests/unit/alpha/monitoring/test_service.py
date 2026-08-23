"""Tests for `atlas.alpha.monitoring.service.MonitoringService` --
built through real, unmodified Case/Decision/Portfolio/Watchlist
persistence, mirroring `tests/unit/alpha/daily_brief_agenda
/test_service.py`'s own harness pattern exactly. Covers Sprint 8's own
incremental recomputation, idempotence, and failure-handling behavior.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.evidence_timeline.repository import SqlAlchemyEvidenceSnapshotRepository
from atlas.alpha.evidence_timeline.table import create_evidence_snapshot_table
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.investment_case_change.table import create_investment_case_snapshot_table
from atlas.alpha.monitoring.models import MonitoringOperationalStatus, OperationalMonitoringStatus, OperationalRunStatus
from atlas.alpha.monitoring.repository import SqlAlchemyMonitoringResultRepository, SqlAlchemyMonitoringRunRecordRepository
from atlas.alpha.monitoring.service import MonitoringService
from atlas.alpha.ingestion.repository import SqlAlchemyIngestionResultRepository
from atlas.alpha.ingestion.table import create_ingestion_result_table
from atlas.alpha.monitoring.table import create_monitoring_result_table, create_monitoring_run_record_table
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
from atlas.core.application.case_condition.case_condition_service import CaseConditionService
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.value_objects import Confidence, DecisionType, InvestmentCase, Subject, UserId
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
from atlas.core.infrastructure.api.evidence.dependencies import get_evidence_repository
from atlas.core.infrastructure.api.knowledge_reference.dependencies import get_outcome_repository
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository
from atlas.core.infrastructure.persistence.case_condition.sqlalchemy_repository import (
    SqlAlchemyCaseConditionEventRepository,
)
from atlas.core.infrastructure.persistence.case_condition.table import create_case_condition_events_table
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
    create_case_condition_events_table(engine)
    create_evidence_snapshot_table(engine)
    create_monitoring_result_table(engine)
    create_monitoring_run_record_table(engine)
    create_ingestion_result_table(engine)
    return engine


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
        self.case_condition_repository = SqlAlchemyCaseConditionEventRepository(engine)
        self.evidence_snapshot_repository = SqlAlchemyEvidenceSnapshotRepository(engine)
        self.monitoring_result_repository = SqlAlchemyMonitoringResultRepository(engine)
        self.monitoring_run_record_repository = SqlAlchemyMonitoringRunRecordRepository(engine)
        self.ingestion_result_repository = SqlAlchemyIngestionResultRepository(engine)

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
        self.case_condition_service = CaseConditionService(
            self.case_condition_repository, self.case_repository, self.decision_repository
        )
        self.monitoring_service = MonitoringService(
            portfolio_store=self.portfolio_store,
            watchlist_store=self.watchlist_store,
            composition_service=self.composition_service,
            stance_service=self.stance_service,
            business_record_repository=self.business_record_repository,
            evidence_snapshot_repository=self.evidence_snapshot_repository,
            case_condition_service=self.case_condition_service,
            monitoring_result_repository=self.monitoring_result_repository,
            decision_repository=self.decision_repository,
            observation_repository=self.observation_repository,
            monitoring_run_record_repository=self.monitoring_run_record_repository,
            ingestion_result_repository=self.ingestion_result_repository,
        )

    def import_holding(self, ticker: str, weight_percent: float = 100.0) -> str:
        return self.import_holdings({ticker: weight_percent})[ticker]

    def import_holdings(self, weights_by_ticker: dict[str, float]) -> dict[str, str]:
        """`import_portfolio` replaces the whole portfolio -- always
        called once with every ticker a test needs, never accumulated
        across separate calls."""
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

    def record_decision(self, case_id_str: str, subject: str = "Test") -> Decision:
        import atlas.core.domain.case.value_objects as case_vo

        case_id = case_vo.CaseId(value=uuid.UUID(case_id_str))
        decision = Decision.register(
            case_id=case_id,
            user_id=UserId(uuid.uuid4()),
            decision_type=DecisionType.BUY,
            subject=Subject(subject),
            investment_case=InvestmentCase("Test investment case reasoning"),
            confidence=Confidence(70),
        )
        self.decision_repository.add(decision)
        return decision


@pytest.fixture
def harness() -> _Harness:
    return _Harness(_new_engine())


class TestFirstRun:
    def test_a_never_monitored_holding_is_always_evaluated(self, harness):
        harness.import_holding("NVDA")
        run = harness.monitoring_service.run()
        assert len(run.results) == 1
        assert run.results[0].ticker == "NVDA"

    def test_the_run_record_reports_one_evaluated_and_zero_skipped(self, harness):
        harness.import_holding("NVDA")
        harness.monitoring_service.run()
        record = harness.monitoring_run_record_repository.get_latest()
        assert record is not None
        assert record.evaluated_count == 1
        assert record.skipped_count == 0
        assert record.status == OperationalRunStatus.COMPLETED


class TestIncrementalRecomputation:
    def test_a_second_run_with_no_new_signal_skips_the_company(self, harness):
        harness.import_holding("NVDA")
        harness.monitoring_service.run()
        harness.monitoring_service.run()
        record = harness.monitoring_run_record_repository.get_latest()
        assert record.evaluated_count == 0
        assert record.skipped_count == 1

    def test_the_skipped_companys_cached_result_is_carried_forward_unchanged(self, harness):
        harness.import_holding("NVDA")
        run1 = harness.monitoring_service.run()
        run2 = harness.monitoring_service.run()
        assert run1.results[0].generated_at == run2.results[0].generated_at

    def test_recording_a_new_decision_makes_the_case_dirty_and_the_next_run_reevaluates(self, harness):
        case_id = harness.import_holding("NVDA")
        run1 = harness.monitoring_service.run()
        harness.record_decision(case_id, subject="NVDA")
        run2 = harness.monitoring_service.run()
        assert run2.results[0].generated_at != run1.results[0].generated_at
        record = harness.monitoring_run_record_repository.get_latest()
        assert record.evaluated_count == 1

    def test_force_true_reevaluates_even_when_nothing_is_dirty(self, harness):
        harness.import_holding("NVDA")
        harness.monitoring_service.run()
        run2 = harness.monitoring_service.run(force=True)
        record = harness.monitoring_run_record_repository.get_latest()
        assert record.evaluated_count == 1
        assert record.forced is True
        assert len(run2.results) == 1


class TestOperationalStatus:
    def test_status_is_unknown_before_any_run_has_ever_happened(self, harness):
        harness.import_holding("NVDA")
        status = harness.monitoring_service.operational_status()
        assert status.status is OperationalMonitoringStatus.UNKNOWN

    def test_status_is_up_to_date_immediately_after_a_clean_run(self, harness):
        harness.import_holding("NVDA")
        harness.monitoring_service.run()
        status = harness.monitoring_service.operational_status()
        assert status.status is OperationalMonitoringStatus.UP_TO_DATE
        assert status.pending_cases == ()

    def test_status_becomes_pending_the_moment_a_new_decision_is_recorded(self, harness):
        case_id = harness.import_holding("NVDA")
        harness.monitoring_service.run()
        harness.record_decision(case_id, subject="NVDA")
        status = harness.monitoring_service.operational_status()
        assert status.status is OperationalMonitoringStatus.PENDING
        assert len(status.pending_cases) == 1

    def test_a_never_monitored_watchlist_company_counts_as_pending(self, harness):
        harness.import_holding("NVDA")
        harness.monitoring_service.run()
        harness.add_to_watchlist("AMD")
        status = harness.monitoring_service.operational_status()
        assert status.status is OperationalMonitoringStatus.PENDING
        assert any(t == "AMD" for _, t in status.pending_cases)


class TestCaseFreshness:
    def test_a_never_monitored_case_reports_pending_with_no_last_monitored_at(self, harness):
        case_id = harness.import_holding("NVDA")
        freshness = harness.monitoring_service.freshness_for_case(case_id)
        assert freshness.is_pending is True
        assert freshness.last_monitored_at is None

    def test_a_freshly_monitored_case_reports_not_pending(self, harness):
        case_id = harness.import_holding("NVDA")
        harness.monitoring_service.run()
        freshness = harness.monitoring_service.freshness_for_case(case_id)
        assert freshness.is_pending is False
        assert freshness.last_monitored_at is not None


class TestFailureHandling:
    def test_one_failing_company_does_not_abort_the_run_for_others(self, harness, monkeypatch):
        cases = harness.import_holdings({"NVDA": 50.0, "MSFT": 50.0})
        good_case, bad_case = cases["NVDA"], cases["MSFT"]

        real_assess = harness.stance_service.assess_for_case

        def _flaky_assess(case_id: str):
            if case_id == bad_case:
                raise RuntimeError("simulated Stance failure")
            return real_assess(case_id)

        monkeypatch.setattr(harness.stance_service, "assess_for_case", _flaky_assess)

        run = harness.monitoring_service.run()
        tickers = {r.ticker for r in run.results}
        assert "NVDA" in tickers  # the good company still evaluated.

        record = harness.monitoring_run_record_repository.get_latest()
        assert record.status == OperationalRunStatus.FAILED
        assert record.evaluated_count == 1  # only NVDA succeeded.
        assert len(record.failures) == 1
        assert record.failures[0].ticker == "MSFT"

    def test_a_failed_companys_checkpoint_is_never_written_so_it_stays_pending(self, harness, monkeypatch):
        bad_case = harness.import_holding("MSFT")
        monkeypatch.setattr(
            harness.stance_service, "assess_for_case", lambda case_id: (_ for _ in ()).throw(RuntimeError("boom"))
        )
        harness.monitoring_service.run()
        assert harness.monitoring_result_repository.get(bad_case) is None
        status = harness.monitoring_service.operational_status()
        assert status.status is OperationalMonitoringStatus.FAILED
        assert any(c == bad_case for c, _ in status.pending_cases)

    def test_a_subsequent_successful_run_clears_the_failed_status(self, harness, monkeypatch):
        case_id = harness.import_holding("NVDA")
        monkeypatch.setattr(
            harness.stance_service, "assess_for_case", lambda case_id: (_ for _ in ()).throw(RuntimeError("boom"))
        )
        harness.monitoring_service.run()
        assert harness.monitoring_service.operational_status().status is OperationalMonitoringStatus.FAILED

        monkeypatch.undo()
        harness.monitoring_service.run()
        assert harness.monitoring_service.operational_status().status is OperationalMonitoringStatus.UP_TO_DATE
