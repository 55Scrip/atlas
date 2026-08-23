"""Tests for `atlas.alpha.portfolio_decision.service
.PortfolioDecisionService` -- built through real, unmodified Case/
Decision/Observation/Portfolio/Watchlist/Monitoring/EvidenceQuality/
DecisionReadiness/DecisionReliability/OpportunityCost/PortfolioFit/
PortfolioIntelligence persistence, the same harness pattern
`tests/unit/alpha/decision_reliability/test_service.py` already
established (this package additionally composes `PortfolioFitService`/
`PortfolioIntelligenceService`/`OpportunityCostService` directly)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.decision_path.repository import SqlAlchemyDecisionPathResultRepository
from atlas.alpha.decision_path.service import DecisionPathService
from atlas.alpha.decision_path.table import create_decision_path_result_table
from atlas.alpha.decision_readiness.repository import SqlAlchemyDecisionReadinessResultRepository
from atlas.alpha.decision_readiness.service import DecisionReadinessService
from atlas.alpha.decision_readiness.table import create_decision_readiness_result_table
from atlas.alpha.decision_reliability.repository import SqlAlchemyDecisionReliabilityResultRepository
from atlas.alpha.decision_reliability.service import DecisionReliabilityService
from atlas.alpha.decision_reliability.table import create_decision_reliability_result_table
from atlas.alpha.evidence_graph.service import EvidenceGraphService
from atlas.alpha.evidence_quality.service import EvidenceQualityService
from atlas.alpha.evidence_timeline.repository import SqlAlchemyEvidenceSnapshotRepository
from atlas.alpha.evidence_timeline.table import create_evidence_snapshot_table
from atlas.alpha.ingestion.repository import SqlAlchemyIngestionResultRepository
from atlas.alpha.ingestion.table import create_ingestion_result_table
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.investment_case_change.table import create_investment_case_snapshot_table
from atlas.alpha.investment_decision.repository import SqlAlchemyInvestmentDecisionResultRepository
from atlas.alpha.investment_decision.service import InvestmentDecisionService
from atlas.alpha.investment_decision.table import create_investment_decision_result_table
from atlas.alpha.monitoring.repository import SqlAlchemyMonitoringResultRepository, SqlAlchemyMonitoringRunRecordRepository
from atlas.alpha.monitoring.service import MonitoringService
from atlas.alpha.monitoring.table import create_monitoring_result_table, create_monitoring_run_record_table
from atlas.alpha.opportunity_cost.repository import SqlAlchemyOpportunityCostResultRepository
from atlas.alpha.opportunity_cost.service import OpportunityCostService
from atlas.alpha.opportunity_cost.table import create_opportunity_cost_result_table
from atlas.alpha.portfolio.service import AlphaPortfolioService, ImportHoldingInput, ImportPortfolioRequest
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio.trade_log_table import create_alpha_trade_log_table
from atlas.alpha.portfolio_decision.repository import SqlAlchemyPortfolioDecisionResultRepository
from atlas.alpha.portfolio_decision.service import PortfolioDecisionService
from atlas.alpha.portfolio_decision.table import create_portfolio_decision_result_table
from atlas.alpha.portfolio_fit.service import PortfolioFitService
from atlas.alpha.portfolio_intelligence.service import PortfolioIntelligenceService
from atlas.alpha.portfolio_status.service import PortfolioStatusService
from atlas.alpha.recommendation_conviction.repository import SqlAlchemyRecommendationConvictionResultRepository
from atlas.alpha.recommendation_conviction.service import RecommendationConvictionService
from atlas.alpha.recommendation_conviction.table import create_recommendation_conviction_result_table
from atlas.alpha.stance.service import StanceService
from atlas.alpha.watchlist.models import AlphaWatchlistEntry
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.alpha.watchlist.table import create_alpha_watchlist_entry_table
from atlas.core.application.assumption.assumption_service import AssumptionService
from atlas.core.application.case.create_case import CaseService
from atlas.core.application.case_condition.case_condition_service import CaseConditionService
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
    create_investment_decision_result_table(engine)
    create_recommendation_conviction_result_table(engine)
    create_decision_path_result_table(engine)
    create_opportunity_cost_result_table(engine)
    create_decision_reliability_result_table(engine)
    create_portfolio_decision_result_table(engine)
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
        self.investment_decision_result_repository = SqlAlchemyInvestmentDecisionResultRepository(engine)
        self.recommendation_conviction_result_repository = SqlAlchemyRecommendationConvictionResultRepository(engine)
        self.decision_path_result_repository = SqlAlchemyDecisionPathResultRepository(engine)
        self.opportunity_cost_result_repository = SqlAlchemyOpportunityCostResultRepository(engine)
        self.decision_reliability_result_repository = SqlAlchemyDecisionReliabilityResultRepository(engine)
        self.portfolio_decision_result_repository = SqlAlchemyPortfolioDecisionResultRepository(engine)

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
        self.investment_decision_service = InvestmentDecisionService(
            self.composition_service,
            self.decision_readiness_service,
            self.stance_service,
            self.investment_decision_result_repository,
            self.portfolio_store,
            self.watchlist_store,
        )
        self.recommendation_conviction_service = RecommendationConvictionService(
            self.composition_service,
            self.decision_readiness_service,
            self.investment_decision_service,
            self.evidence_graph_service,
            self.recommendation_conviction_result_repository,
            self.portfolio_store,
            self.watchlist_store,
        )
        self.decision_path_service = DecisionPathService(
            self.investment_decision_service,
            self.recommendation_conviction_service,
            self.decision_readiness_service,
            self.evidence_graph_service,
            self.decision_path_result_repository,
            self.portfolio_store,
            self.watchlist_store,
        )
        self.opportunity_cost_service = OpportunityCostService(
            self.investment_decision_service,
            self.recommendation_conviction_service,
            self.decision_path_service,
            self.opportunity_cost_result_repository,
            self.portfolio_store,
            self.watchlist_store,
        )
        self.evidence_quality_service = EvidenceQualityService(
            self.composition_service,
            self.business_record_repository,
            self.portfolio_store,
            self.watchlist_store,
        )
        self.decision_reliability_service = DecisionReliabilityService(
            self.composition_service,
            self.evidence_quality_service,
            self.decision_readiness_service,
            self.decision_reliability_result_repository,
            self.portfolio_store,
            self.watchlist_store,
        )
        self.portfolio_status_service = PortfolioStatusService(
            self.portfolio_store,
            self.trade_log_store,
            self.decision_repository,
            self.outcome_repository,
            self.observation_repository,
        )
        self.portfolio_intelligence_service = PortfolioIntelligenceService(
            self.portfolio_store,
            self.trade_log_store,
            self.decision_repository,
            self.observation_repository,
            self.evidence_repository,
            self.outcome_repository,
            self.portfolio_status_service,
        )
        self.portfolio_decision_service = PortfolioDecisionService(
            self.investment_decision_service,
            self.decision_reliability_service,
            self.opportunity_cost_service,
            self.portfolio_fit_service,
            self.portfolio_intelligence_service,
            self.portfolio_decision_result_repository,
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


@pytest.fixture
def harness():
    return _Harness(_new_engine())


class TestAssessForCase:
    def test_returns_none_for_a_case_that_does_not_exist(self, harness):
        assert harness.portfolio_decision_service.assess_for_case(str(uuid.uuid4())) is None

    def test_a_case_with_no_data_still_returns_a_real_result(self, harness):
        case_id = harness.import_holding("NVDA")
        decision = harness.portfolio_decision_service.assess_for_case(case_id)
        assert decision is not None
        assert decision.category is not None

    def test_repeated_calls_are_idempotent_when_nothing_changed(self, harness):
        case_id = harness.import_holding("NVDA")
        first = harness.portfolio_decision_service.assess_for_case(case_id)
        second = harness.portfolio_decision_service.assess_for_case(case_id)
        assert first.category == second.category
        assert first.limiting_reasons == second.limiting_reasons

    def test_a_single_100_percent_holding_is_the_largest_position(self, harness):
        case_id = harness.import_holding("NVDA", 100.0)
        decision = harness.portfolio_decision_service.assess_for_case(case_id)
        assert decision.impact.is_largest_position is True
        assert decision.impact.is_existing_holding is True
        assert decision.impact.current_weight_percent == 100.0


class TestChangeForCase:
    def test_first_computation_produces_no_change(self, harness):
        case_id = harness.import_holding("NVDA")
        assert harness.portfolio_decision_service.change_for_case(case_id) is None

    def test_no_change_when_nothing_changed(self, harness):
        case_id = harness.import_holding("NVDA")
        harness.portfolio_decision_service.assess_for_case(case_id)
        assert harness.portfolio_decision_service.change_for_case(case_id) is None


class TestCompare:
    def test_returns_none_when_a_ticker_does_not_resolve(self, harness):
        harness.import_holding("AAPL")
        assert harness.portfolio_decision_service.compare("AAPL", "UNKNOWN") is None

    def test_compares_two_real_cases(self, harness):
        harness.import_holdings({"AAPL": 50.0, "MSFT": 50.0})
        comparison = harness.portfolio_decision_service.compare("AAPL", "MSFT")
        assert comparison is not None
        assert comparison.a.case_id != comparison.b.case_id


class TestPortfolioSynthesisBreakdown:
    def test_empty_portfolio_produces_empty_buckets(self, harness):
        breakdown = harness.portfolio_decision_service.portfolio_synthesis_breakdown()
        assert breakdown.supports_portfolio == ()

    def test_a_fresh_holding_never_lands_in_conflicting_and_supporting_at_once(self, harness):
        harness.import_holding("NVDA")
        breakdown = harness.portfolio_decision_service.portfolio_synthesis_breakdown()
        assert not ("NVDA" in breakdown.supports_portfolio and "NVDA" in breakdown.conflicts_with_portfolio)
