"""Tests for `atlas.alpha.evidence_graph.service.EvidenceGraphService`
-- built through real, unmodified Case/Decision/Observation/Evidence/
CaseCondition/Assumption/Portfolio/Watchlist persistence, the same
harness pattern `tests/unit/alpha/monitoring/test_service.py` already
established (this package reuses every one of those same real
services)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.evidence_graph.models import DependencyKind, GraphNodeKind, WeaknessKind
from atlas.alpha.evidence_graph.service import EvidenceGraphService
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
from atlas.core.application.assumption.assumption_service import AssumptionContent, AssumptionService
from atlas.core.application.case.create_case import CaseService
from atlas.core.application.case_condition.case_condition_service import CaseConditionContent, CaseConditionService
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.value_objects import Confidence, DecisionType, InvestmentCase, Subject, UserId
from atlas.core.domain.evidence.entity import Evidence
from atlas.core.domain.evidence.value_objects import Statement as EvidenceStatement
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

    def import_holding(self, ticker: str, weight_percent: float = 100.0) -> str:
        state = self.portfolio_service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker=ticker, weight_percent=weight_percent),))
        )
        return next(h.case_id for h in state.holdings if h.ticker == ticker)

    def add_to_watchlist(self, ticker: str) -> str:
        case = self.case_service.create()
        case_id = str(case.id)
        self.watchlist_store.add(AlphaWatchlistEntry(ticker=ticker, case_id=case_id, added_at=_NOW))
        return case_id

    def record_decision(self, case_id_str: str, *, observation_id=None) -> Decision:
        import atlas.core.domain.case.value_objects as case_vo

        case_id = case_vo.CaseId(value=uuid.UUID(case_id_str))
        decision = Decision.register(
            case_id=case_id,
            user_id=UserId(uuid.uuid4()),
            decision_type=DecisionType.BUY,
            subject=Subject("Test"),
            investment_case=InvestmentCase("Test investment case reasoning"),
            confidence=Confidence(70),
            observation_id=observation_id,
        )
        self.decision_repository.add(decision)
        return decision

    def record_observation(self, case_id_str: str, statement: str = "Revenue grew") -> Observation:
        import atlas.core.domain.case.value_objects as case_vo

        case_id = case_vo.CaseId(value=uuid.UUID(case_id_str))
        observation = Observation.capture(
            case_id=case_id,
            subject=ObservationSubject(value="Test"),
            statement=ObservationStatement(value=statement),
            observed_at=_NOW,
        )
        self.observation_repository.add(observation)
        return observation

    def record_evidence(self, observation: Observation, direction: str = "SUPPORTS") -> Evidence:
        evidence = Evidence.capture(
            observation_id=observation.id,
            statement=EvidenceStatement(value="Confirmed by filing"),
            direction=direction,
            observed_at=_NOW,
        )
        self.evidence_repository.add(evidence)
        return evidence

    def record_case_condition(self, case_id_str: str, decision_id=None, predicate_text: str = "Growth stays above 10%"):
        import atlas.core.domain.case.value_objects as case_vo

        case_id = case_vo.CaseId(value=uuid.UUID(case_id_str))
        return self.case_condition_service.create(
            case_id=case_id, decision_id=decision_id, content=CaseConditionContent(predicate_text=predicate_text)
        )

    def record_assumption(self, decision_id, statement: str = "Demand stays strong"):
        return self.assumption_service.create(decision_id=decision_id, content=AssumptionContent(statement=statement))


@pytest.fixture
def harness():
    return _Harness(_new_engine())


class TestBuildForCase:
    def test_returns_none_for_a_case_that_does_not_exist(self, harness):
        assert harness.evidence_graph_service.build_for_case(str(uuid.uuid4())) is None

    def test_returns_a_real_graph_for_a_known_case_with_no_activity(self, harness):
        case_id = harness.import_holding("NVDA")
        built = harness.evidence_graph_service.build_for_case(case_id)
        assert built is not None
        assert built.graph.case_id == case_id

    def test_a_recorded_observation_and_decision_produce_a_depends_on_edge(self, harness):
        case_id = harness.import_holding("NVDA")
        observation = harness.record_observation(case_id)
        harness.record_decision(case_id, observation_id=observation.id)

        built = harness.evidence_graph_service.build_for_case(case_id)
        depends_on = [e for e in built.graph.edges if e.kind is DependencyKind.DEPENDS_ON]
        assert any(e.target_id == str(observation.id) for e in depends_on)

    def test_evidence_is_scoped_to_this_case_only(self, harness):
        case_a = harness.import_holding("NVDA")
        case_b = harness.add_to_watchlist("MSFT")
        obs_a = harness.record_observation(case_a)
        obs_b = harness.record_observation(case_b)
        harness.record_evidence(obs_a)
        harness.record_evidence(obs_b)

        built_a = harness.evidence_graph_service.build_for_case(case_a)
        evidence_nodes_a = [n for n in built_a.graph.nodes if n.kind is GraphNodeKind.EVIDENCE]
        assert len(evidence_nodes_a) == 1

    def test_an_isolated_observation_is_flagged_as_a_weak_dependency(self, harness):
        case_id = harness.import_holding("NVDA")
        observation = harness.record_observation(case_id)

        built = harness.evidence_graph_service.build_for_case(case_id)
        assert any(
            w.node_id == str(observation.id) and w.kind is WeaknessKind.ISOLATED_CHAIN for w in built.weak_dependencies
        )

    def test_case_condition_feeds_its_linked_assumption(self, harness):
        case_id = harness.import_holding("NVDA")
        decision = harness.record_decision(case_id)
        condition = harness.record_case_condition(case_id, decision_id=decision.id)
        assumption = harness.record_assumption(decision.id)
        harness.assumption_service.attach_case_condition(assumption.assumption_id, condition.condition_id)

        built = harness.evidence_graph_service.build_for_case(case_id)
        feeds = [e for e in built.graph.edges if e.kind is DependencyKind.FEEDS]
        assert any(
            e.source_id == str(condition.condition_id) and e.target_id == str(assumption.assumption_id) for e in feeds
        )


class TestBuildForKnownCases:
    def test_covers_both_portfolio_and_watchlist_scope(self, harness):
        holding_case = harness.import_holding("NVDA")
        watchlist_case = harness.add_to_watchlist("MSFT")

        built = harness.evidence_graph_service.build_for_known_cases()
        assert set(built.keys()) == {holding_case, watchlist_case}


class TestCompare:
    def test_returns_none_when_either_ticker_is_unknown(self, harness):
        harness.import_holding("NVDA")
        assert harness.evidence_graph_service.compare("NVDA", "ZZZZZ") is None

    def test_returns_real_counts_for_both_sides(self, harness):
        case_a = harness.import_holding("NVDA")
        case_b = harness.add_to_watchlist("MSFT")
        observation = harness.record_observation(case_a)
        harness.record_decision(case_a, observation_id=observation.id)

        comparison = harness.evidence_graph_service.compare("NVDA", "MSFT")
        assert comparison is not None
        assert comparison.a.case_id == case_a
        assert comparison.b.case_id == case_b
        assert comparison.a.independent_observation_chains == 1
        assert comparison.b.independent_observation_chains == 0
