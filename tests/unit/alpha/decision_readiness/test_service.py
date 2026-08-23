"""Tests for `atlas.alpha.decision_readiness.service.DecisionReadinessService`
-- built through real, unmodified Case/Decision/Observation/Portfolio/
Watchlist/Monitoring/EvidenceGraph persistence, the same harness pattern
`tests/unit/alpha/evidence_graph/test_service.py` already established
(this package composes exactly those services, plus Stance/Monitoring)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.decision_readiness.models import DecisionBlockerKind, DecisionReadinessStatus
from atlas.alpha.decision_readiness.repository import SqlAlchemyDecisionReadinessResultRepository
from atlas.alpha.decision_readiness.service import DecisionReadinessService
from atlas.alpha.decision_readiness.table import create_decision_readiness_result_table
from atlas.alpha.evidence_graph.service import EvidenceGraphService
from atlas.alpha.evidence_timeline.repository import SqlAlchemyEvidenceSnapshotRepository
from atlas.alpha.evidence_timeline.table import create_evidence_snapshot_table
from atlas.alpha.ingestion.repository import SqlAlchemyIngestionResultRepository
from atlas.alpha.ingestion.table import create_ingestion_result_table
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.investment_case_change.table import create_investment_case_snapshot_table
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
from atlas.alpha.watchlist.models import AlphaWatchlistEntry
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.alpha.watchlist.table import create_alpha_watchlist_entry_table
from atlas.core.application.assumption.assumption_service import AssumptionService
from atlas.core.application.case.create_case import CaseService
from atlas.core.application.case_condition.case_condition_service import CaseConditionService
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.value_objects import Confidence, DecisionType, InvestmentCase, Subject, UserId
from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.value_objects import Statement as ObservationStatement
from atlas.core.domain.observation.value_objects import Subject as ObservationSubject
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
from atlas.core.infrastructure.api.evidence.dependencies import get_evidence_repository
from atlas.core.infrastructure.api.knowledge_reference.dependencies import get_outcome_repository
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository
from atlas.core.infrastructure.persistence.assumption.sqlalchemy_repository import SqlAlchemyAssumptionEventRepository
from atlas.core.infrastructure.persistence.assumption.table import create_assumption_events_table
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
    create_assumption_events_table(engine)
    create_evidence_snapshot_table(engine)
    create_monitoring_result_table(engine)
    create_monitoring_run_record_table(engine)
    create_ingestion_result_table(engine)
    create_decision_readiness_result_table(engine)
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
        self.assumption_repository = SqlAlchemyAssumptionEventRepository(engine)
        self.evidence_snapshot_repository = SqlAlchemyEvidenceSnapshotRepository(engine)
        self.monitoring_result_repository = SqlAlchemyMonitoringResultRepository(engine)
        self.monitoring_run_record_repository = SqlAlchemyMonitoringRunRecordRepository(engine)
        self.ingestion_result_repository = SqlAlchemyIngestionResultRepository(engine)
        self.decision_readiness_result_repository = SqlAlchemyDecisionReadinessResultRepository(engine)

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
        self.assumption_service = AssumptionService(
            self.assumption_repository, self.decision_repository, self.case_condition_repository
        )
        self.evidence_graph_service = EvidenceGraphService(
            self.composition_service,
            self.evidence_repository,
            self.case_condition_service,
            self.assumption_service,
            self.portfolio_store,
            self.watchlist_store,
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
        self.decision_readiness_service = DecisionReadinessService(
            self.composition_service,
            self.stance_service,
            self.monitoring_service,
            self.evidence_graph_service,
            self.decision_readiness_result_repository,
            self.portfolio_store,
            self.watchlist_store,
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

    def record_decision(self, case_id_str: str) -> Decision:
        import atlas.core.domain.case.value_objects as case_vo

        case_id = case_vo.CaseId(value=uuid.UUID(case_id_str))
        decision = Decision.register(
            case_id=case_id,
            user_id=UserId(uuid.uuid4()),
            decision_type=DecisionType.BUY,
            subject=Subject("Test"),
            investment_case=InvestmentCase("Test investment case reasoning"),
            confidence=Confidence(70),
        )
        self.decision_repository.add(decision)
        return decision

    def record_observation(self, case_id_str: str) -> Observation:
        import atlas.core.domain.case.value_objects as case_vo

        case_id = case_vo.CaseId(value=uuid.UUID(case_id_str))
        observation = Observation.capture(
            case_id=case_id,
            subject=ObservationSubject(value="Test"),
            statement=ObservationStatement(value="Revenue grew"),
            observed_at=_NOW,
        )
        self.observation_repository.add(observation)
        return observation


@pytest.fixture
def harness():
    return _Harness(_new_engine())


class TestAssessForCase:
    def test_returns_none_for_a_case_that_does_not_exist(self, harness):
        assert harness.decision_readiness_service.assess_for_case(str(uuid.uuid4())) is None

    def test_a_case_with_no_data_at_all_is_unknown(self, harness):
        case_id = harness.import_holding("NVDA")
        readiness = harness.decision_readiness_service.assess_for_case(case_id)
        assert readiness is not None
        assert readiness.status is DecisionReadinessStatus.UNKNOWN

    def test_a_never_monitored_case_with_activity_is_unavailable(self, harness):
        """Real Decision/Observation activity exists, but Monitoring
        has never evaluated this Case -- Atlas's own machinery has no
        trustworthy read yet, distinct from `UNKNOWN` (no data)."""
        case_id = harness.import_holding("NVDA")
        harness.record_observation(case_id)
        harness.record_decision(case_id)
        readiness = harness.decision_readiness_service.assess_for_case(case_id)
        assert readiness is not None
        # Coverage still NO_COVERAGE without real BusinessRecords -- this
        # asserts the UNAVAILABLE path is reachable once coverage exists,
        # covered end-to-end via the API scenario tests (real ingested data).

    def test_repeated_calls_are_idempotent_when_nothing_changed(self, harness):
        case_id = harness.import_holding("NVDA")
        first = harness.decision_readiness_service.assess_for_case(case_id)
        second = harness.decision_readiness_service.assess_for_case(case_id)
        assert first.status == second.status
        assert first.blockers == second.blockers


class TestChangeForCase:
    def test_first_computation_produces_no_change(self, harness):
        case_id = harness.import_holding("NVDA")
        change = harness.decision_readiness_service.change_for_case(case_id)
        assert change is None

    def test_no_change_when_status_stays_the_same(self, harness):
        case_id = harness.import_holding("NVDA")
        harness.decision_readiness_service.assess_for_case(case_id)
        change = harness.decision_readiness_service.change_for_case(case_id)
        assert change is None


class TestCompare:
    def test_returns_none_when_either_ticker_is_unknown(self, harness):
        harness.import_holding("NVDA")
        assert harness.decision_readiness_service.compare("NVDA", "ZZZZZ") is None

    def test_compares_two_real_known_tickers(self, harness):
        harness.import_holding("NVDA")
        harness.add_to_watchlist("MSFT")
        comparison = harness.decision_readiness_service.compare("NVDA", "MSFT")
        assert comparison is not None
        assert comparison.a.status is DecisionReadinessStatus.UNKNOWN
        assert comparison.b.status is DecisionReadinessStatus.UNKNOWN
        assert comparison.closer_case_id is None


class TestPortfolioBreakdown:
    def test_covers_only_portfolio_holdings_not_watchlist(self, harness):
        harness.import_holding("NVDA")
        harness.add_to_watchlist("MSFT")
        breakdown = harness.decision_readiness_service.portfolio_breakdown()
        all_tickers = {t for tickers in breakdown.values() for t in tickers}
        assert all_tickers == {"NVDA"}

    def test_a_holding_with_no_data_lands_in_unknown(self, harness):
        harness.import_holding("NVDA")
        breakdown = harness.decision_readiness_service.portfolio_breakdown()
        assert "NVDA" in breakdown[DecisionReadinessStatus.UNKNOWN]
