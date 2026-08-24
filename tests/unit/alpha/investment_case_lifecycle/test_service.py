"""Tests for `atlas.alpha.investment_case_lifecycle.service
.InvestmentCaseLifecycleService` -- built through real, unmodified Case/
Portfolio/Watchlist/BusinessRecord/Monitoring persistence, the same
trimmed-harness pattern `tests/unit/alpha/decision_readiness
/test_service.py` established (this package composes
`InvestmentCaseCompositionService` + `MonitoringService`, nothing else,
so `EvidenceGraphService`/`AssumptionService`/`CaseConditionService`'s
own machinery is included only insofar as `MonitoringService` itself
still requires it)."""
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.evidence_timeline.repository import SqlAlchemyEvidenceSnapshotRepository
from atlas.alpha.evidence_timeline.table import create_evidence_snapshot_table
from atlas.alpha.ingestion.repository import SqlAlchemyIngestionResultRepository
from atlas.alpha.ingestion.table import create_ingestion_result_table
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.investment_case_change.table import create_investment_case_snapshot_table
from atlas.alpha.investment_case_lifecycle.models import LifecycleState, MandatoryItemId
from atlas.alpha.investment_case_lifecycle.repository import SqlAlchemyLifecycleSnapshotRepository
from atlas.alpha.investment_case_lifecycle.service import InvestmentCaseLifecycleService
from atlas.alpha.investment_case_lifecycle.table import create_investment_case_lifecycle_history_table
from atlas.alpha.monitoring.repository import SqlAlchemyMonitoringResultRepository, SqlAlchemyMonitoringRunRecordRepository
from atlas.alpha.monitoring.service import MonitoringService
from atlas.alpha.monitoring.table import create_monitoring_result_table, create_monitoring_run_record_table
from atlas.alpha.portfolio.service import AlphaPortfolioService, ImportHoldingInput, ImportPortfolioRequest
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio.trade_log_table import create_alpha_trade_log_table
from atlas.alpha.portfolio_fit.service import PortfolioFitService
from atlas.alpha.stance.service import StanceService
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.alpha.watchlist.table import create_alpha_watchlist_entry_table
from atlas.core.application.case.create_case import CaseService
from atlas.core.application.case_condition.case_condition_service import CaseConditionService
from atlas.core.infrastructure.persistence.case_condition.sqlalchemy_repository import (
    SqlAlchemyCaseConditionEventRepository,
)
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
from atlas.core.infrastructure.api.evidence.dependencies import get_evidence_repository
from atlas.core.infrastructure.api.knowledge_reference.dependencies import get_outcome_repository
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository
from atlas.core.infrastructure.persistence.case_condition.table import create_case_condition_events_table
from atlas.core.infrastructure.persistence.decision.table import create_decision_table
from tests.unit.alpha.investment_case_lifecycle._fixtures import full_records

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
    create_investment_case_lifecycle_history_table(engine)
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
        self.lifecycle_snapshot_repository = SqlAlchemyLifecycleSnapshotRepository(engine)

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
        self.lifecycle_service = InvestmentCaseLifecycleService(
            self.composition_service,
            self.monitoring_service,
            self.lifecycle_snapshot_repository,
            self.portfolio_store,
            self.watchlist_store,
        )

    def import_holding(self, ticker: str, weight_percent: float = 100.0) -> str:
        state = self.portfolio_service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker=ticker, weight_percent=weight_percent),))
        )
        return next(h.case_id for h in state.holdings if h.ticker == ticker)

    def add_business_records(self, ticker: str, records: tuple) -> None:
        for record in records:
            self.business_record_repository.add(record)


def _harness():
    return _Harness(_new_engine())


class TestStatusForCase:
    def test_returns_none_for_a_case_that_does_not_exist(self):
        harness = _harness()
        assert harness.lifecycle_service.status_for_case("00000000-0000-0000-0000-000000000000") is None

    def test_case_with_no_business_records_is_company_added(self):
        harness = _harness()
        case_id = harness.import_holding("ASML")
        status = harness.lifecycle_service.status_for_case(case_id)
        assert status is not None
        assert status.lifecycle_state is LifecycleState.COMPANY_ADDED

    def test_case_with_full_evidence_reaches_analysis_running_without_recommendation(self):
        """This harness's own real pipeline never synthesizes a genuine
        `ComputedDirectionalRecommendation` from bare Portfolio/
        BusinessRecord setup alone (`select_direction`'s own real
        preconditions are `evaluate_recommendation_gate`'s tested
        responsibility, not this package's) -- so a fully-evidenced Case
        here is correctly `ANALYSIS_RUNNING`, blocked only on
        `WAITING_FOR_RECOMMENDATION`. `test_engine.py`'s own
        `TestPublicationEligibility` proves the eligible/Published path
        with a real recommendation swapped in via `dataclasses.replace`."""
        harness = _harness()
        case_id = harness.import_holding("ASML")
        harness.add_business_records("ASML", full_records())
        status = harness.lifecycle_service.status_for_case(case_id)
        assert status is not None
        assert status.lifecycle_state is LifecycleState.ANALYSIS_RUNNING
        assert status.mandatory_core.all_satisfied is True
        assert status.published_since is None

    def test_repeated_calls_are_idempotent_when_nothing_changed(self):
        harness = _harness()
        case_id = harness.import_holding("ASML")
        harness.add_business_records("ASML", full_records())
        first = harness.lifecycle_service.status_for_case(case_id)
        second_service = InvestmentCaseLifecycleService(
            harness.composition_service,
            harness.monitoring_service,
            harness.lifecycle_snapshot_repository,
            harness.portfolio_store,
            harness.watchlist_store,
        )
        second = second_service.status_for_case(case_id)
        assert first.lifecycle_state == second.lifecycle_state
        assert first.mandatory_core == second.mandatory_core

    def test_snapshot_is_persisted_for_regression_detection(self):
        harness = _harness()
        case_id = harness.import_holding("ASML")
        harness.add_business_records("ASML", full_records())
        harness.lifecycle_service.status_for_case(case_id)
        persisted = harness.lifecycle_snapshot_repository.get(case_id)
        assert persisted is not None
        assert persisted.lifecycle_state is LifecycleState.ANALYSIS_RUNNING


class TestIsolation:
    """Section 12's explicit isolation requirement: lifecycle evaluation
    must never mutate Decision Layer outputs, recommendation semantics,
    valuation outputs, portfolio-fit outputs, or stored investment
    conclusions -- it is read-only over all of them, writing only to its
    own `investment_case_lifecycle_history` table."""

    def test_evaluating_lifecycle_does_not_change_recomputed_composition(self):
        """Compares the substantive analytical content only (kind/
        status for each finding, recommendation outcome type) --
        `assemble_analysis` itself freshly wall-clock-stamps
        `computed_at`/`updated_at` on every call regardless of whether
        lifecycle evaluation ran in between (confirmed by diffing two
        back-to-back `build()` calls with no lifecycle call at all
        between them), so a byte-for-byte equality would fail for a
        reason unrelated to this test's own isolation claim."""
        harness = _harness()
        case_id = harness.import_holding("ASML")
        harness.add_business_records("ASML", full_records())

        before = harness.composition_service.build(case_id)
        harness.lifecycle_service.status_for_case(case_id)

        # A fresh composition service (no shared request-scoped cache)
        # re-reads the same underlying tables -- proves the lifecycle
        # evaluation wrote nothing that changes what composition/
        # recommendation/valuation/risk building recomputes.
        fresh_composition_service = InvestmentCaseCompositionService(
            harness.case_repository,
            harness.decision_repository,
            harness.observation_repository,
            harness.evidence_repository,
            harness.outcome_repository,
            harness.portfolio_store,
            harness.trade_log_store,
            harness.business_record_repository,
            watchlist_store=harness.watchlist_store,
            snapshot_repository=harness.snapshot_repository,
        )
        after = fresh_composition_service.build(case_id)

        def _business_shape(analysis):
            return tuple((f.kind, f.status) for f in analysis.business_analysis.findings)

        def _risk_shape(analysis):
            return tuple((f.category, f.status) for f in analysis.risk_analysis.findings)

        assert _business_shape(after.canonical_analysis) == _business_shape(before.canonical_analysis)
        assert _risk_shape(after.canonical_analysis) == _risk_shape(before.canonical_analysis)
        assert type(after.canonical_analysis.recommendation.recommendation) == type(
            before.canonical_analysis.recommendation.recommendation
        )

        def _valuation_shape(analysis):
            return tuple((f.kind, f.status) for f in analysis.valuation_engine.findings)

        assert _valuation_shape(after.canonical_analysis) == _valuation_shape(before.canonical_analysis)

    def test_evaluating_lifecycle_only_writes_its_own_table(self):
        harness = _harness()
        case_id = harness.import_holding("ASML")
        harness.add_business_records("ASML", full_records())

        assert harness.monitoring_result_repository.get(case_id) is None
        harness.lifecycle_service.status_for_case(case_id)
        # Lifecycle evaluation must never trigger or persist a
        # Monitoring run as a side effect of a read-only status check.
        assert harness.monitoring_result_repository.get(case_id) is None
        assert harness.lifecycle_snapshot_repository.get(case_id) is not None
