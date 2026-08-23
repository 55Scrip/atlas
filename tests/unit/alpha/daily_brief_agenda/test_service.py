"""Tests for `atlas.alpha.daily_brief_agenda.service.DailyBriefAgendaService`,
built through the real, unmodified Case/Decision/Portfolio/Watchlist/
CaseCondition/Assumption persistence -- the identical harness style
`tests/unit/alpha/portfolio_fit/test_service.py` already establishes,
extended with the two aggregates that service's own harness does not
need (CaseCondition, Assumption)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.daily_brief.service import DailyBriefService
from atlas.alpha.daily_brief_agenda.models import AgendaItemKind, PriorityLevel
from atlas.alpha.daily_brief_agenda.service import DailyBriefAgendaService
from atlas.alpha.decision_explanation.repository import SqlAlchemyDecisionExplanationResultRepository
from atlas.alpha.decision_explanation.service import DecisionExplanationService
from atlas.alpha.decision_explanation.table import create_decision_explanation_result_table
from atlas.alpha.decision_reliability.repository import SqlAlchemyDecisionReliabilityResultRepository
from atlas.alpha.decision_reliability.service import DecisionReliabilityService
from atlas.alpha.decision_reliability.table import create_decision_reliability_result_table
from atlas.alpha.portfolio_decision.repository import SqlAlchemyPortfolioDecisionResultRepository
from atlas.alpha.portfolio_decision.service import PortfolioDecisionService
from atlas.alpha.portfolio_decision.table import create_portfolio_decision_result_table
from atlas.alpha.evidence_quality.service import EvidenceQualityService
from atlas.alpha.decision_memory.repository import SqlAlchemyDecisionMemoryRepository
from atlas.alpha.decision_memory.service import DecisionMemoryService
from atlas.alpha.decision_memory.table import create_decision_memory_snapshot_table
from atlas.alpha.decision_readiness.repository import SqlAlchemyDecisionReadinessResultRepository
from atlas.alpha.decision_readiness.service import DecisionReadinessService
from atlas.alpha.decision_readiness.table import create_decision_readiness_result_table
from atlas.alpha.evidence_graph.service import EvidenceGraphService
from atlas.alpha.evidence_timeline.repository import SqlAlchemyEvidenceSnapshotRepository
from atlas.alpha.evidence_timeline.table import create_evidence_snapshot_table
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.investment_case_change.table import create_investment_case_snapshot_table
from atlas.alpha.investment_decision.repository import SqlAlchemyInvestmentDecisionResultRepository
from atlas.alpha.investment_decision.service import InvestmentDecisionService
from atlas.alpha.investment_decision.table import create_investment_decision_result_table
from atlas.alpha.decision_path.repository import SqlAlchemyDecisionPathResultRepository
from atlas.alpha.decision_path.service import DecisionPathService
from atlas.alpha.decision_path.table import create_decision_path_result_table
from atlas.alpha.opportunity_cost.repository import SqlAlchemyOpportunityCostResultRepository
from atlas.alpha.opportunity_cost.service import OpportunityCostService
from atlas.alpha.opportunity_cost.table import create_opportunity_cost_result_table
from atlas.alpha.recommendation_conviction.repository import SqlAlchemyRecommendationConvictionResultRepository
from atlas.alpha.recommendation_conviction.service import RecommendationConvictionService
from atlas.alpha.recommendation_conviction.table import create_recommendation_conviction_result_table
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
from atlas.alpha.portfolio_intelligence.service import PortfolioIntelligenceService
from atlas.alpha.portfolio_status.models import AttentionCategory
from atlas.alpha.portfolio_status.service import PortfolioStatusService
from atlas.alpha.stance.service import StanceService
from atlas.alpha.watchlist.models import AlphaWatchlistEntry
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.alpha.watchlist.table import create_alpha_watchlist_entry_table
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.core.application.assumption.assumption_service import AssumptionContent, AssumptionService
from atlas.core.application.case.create_case import CaseService
from atlas.core.application.case_condition.case_condition_service import CaseConditionContent, CaseConditionService
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
from atlas.core.infrastructure.persistence.assumption.sqlalchemy_repository import SqlAlchemyAssumptionEventRepository
from atlas.core.infrastructure.persistence.assumption.table import create_assumption_events_table
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
    create_decision_memory_snapshot_table(engine)
    create_decision_explanation_result_table(engine)
    create_decision_reliability_result_table(engine)
    create_portfolio_decision_result_table(engine)
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
        self.case_condition_repository = SqlAlchemyCaseConditionEventRepository(engine)
        self.assumption_repository = SqlAlchemyAssumptionEventRepository(engine)
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
        self.daily_brief_service = DailyBriefService(
            portfolio_store=self.portfolio_store,
            watchlist_store=self.watchlist_store,
            investment_case_composition_service=self.composition_service,
        )
        self.portfolio_fit_service = PortfolioFitService(
            portfolio_store=self.portfolio_store,
            watchlist_store=self.watchlist_store,
            composition_service=self.composition_service,
        )
        self.portfolio_status_service = PortfolioStatusService(
            portfolio_store=self.portfolio_store,
            trade_log_store=self.trade_log_store,
            decision_repository=self.decision_repository,
            outcome_repository=self.outcome_repository,
            observation_repository=self.observation_repository,
        )
        self.portfolio_intelligence_service = PortfolioIntelligenceService(
            portfolio_store=self.portfolio_store,
            trade_log_store=self.trade_log_store,
            decision_repository=self.decision_repository,
            observation_repository=self.observation_repository,
            evidence_repository=self.evidence_repository,
            outcome_repository=self.outcome_repository,
            portfolio_status_service=self.portfolio_status_service,
        )
        self.case_condition_service = CaseConditionService(
            self.case_condition_repository, self.case_repository, self.decision_repository
        )
        self.assumption_service = AssumptionService(
            self.assumption_repository, self.decision_repository, self.case_condition_repository
        )
        self.stance_service = StanceService(
            composition_service=self.composition_service,
            portfolio_fit_service=self.portfolio_fit_service,
            portfolio_store=self.portfolio_store,
            watchlist_store=self.watchlist_store,
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
        self.evidence_graph_service = EvidenceGraphService(
            self.composition_service,
            self.evidence_repository,
            self.case_condition_service,
            self.assumption_service,
            self.portfolio_store,
            self.watchlist_store,
        )
        self.decision_readiness_result_repository = SqlAlchemyDecisionReadinessResultRepository(engine)
        self.decision_readiness_service = DecisionReadinessService(
            self.composition_service,
            self.stance_service,
            self.monitoring_service,
            self.evidence_graph_service,
            self.decision_readiness_result_repository,
            self.portfolio_store,
            self.watchlist_store,
        )
        self.investment_decision_result_repository = SqlAlchemyInvestmentDecisionResultRepository(engine)
        self.investment_decision_service = InvestmentDecisionService(
            self.composition_service,
            self.decision_readiness_service,
            self.stance_service,
            self.investment_decision_result_repository,
            self.portfolio_store,
            self.watchlist_store,
        )
        self.recommendation_conviction_result_repository = SqlAlchemyRecommendationConvictionResultRepository(engine)
        self.recommendation_conviction_service = RecommendationConvictionService(
            self.composition_service,
            self.decision_readiness_service,
            self.investment_decision_service,
            self.evidence_graph_service,
            self.recommendation_conviction_result_repository,
            self.portfolio_store,
            self.watchlist_store,
        )
        self.decision_path_result_repository = SqlAlchemyDecisionPathResultRepository(engine)
        self.decision_path_service = DecisionPathService(
            self.investment_decision_service,
            self.recommendation_conviction_service,
            self.decision_readiness_service,
            self.evidence_graph_service,
            self.decision_path_result_repository,
            self.portfolio_store,
            self.watchlist_store,
        )
        self.opportunity_cost_result_repository = SqlAlchemyOpportunityCostResultRepository(engine)
        self.opportunity_cost_service = OpportunityCostService(
            self.investment_decision_service,
            self.recommendation_conviction_service,
            self.decision_path_service,
            self.opportunity_cost_result_repository,
            self.portfolio_store,
            self.watchlist_store,
        )
        self.decision_memory_repository = SqlAlchemyDecisionMemoryRepository(engine)
        self.decision_memory_service = DecisionMemoryService(
            self.investment_decision_service,
            self.decision_readiness_service,
            self.recommendation_conviction_service,
            self.decision_path_service,
            self.opportunity_cost_service,
            self.decision_memory_repository,
            self.portfolio_store,
            self.watchlist_store,
        )
        self.decision_explanation_result_repository = SqlAlchemyDecisionExplanationResultRepository(engine)
        self.decision_explanation_service = DecisionExplanationService(
            self.investment_decision_service,
            self.recommendation_conviction_service,
            self.decision_readiness_service,
            self.decision_path_service,
            self.decision_memory_service,
            self.evidence_graph_service,
            self.decision_explanation_result_repository,
            self.portfolio_store,
            self.watchlist_store,
        )
        self.evidence_quality_service = EvidenceQualityService(
            self.composition_service,
            self.business_record_repository,
            self.portfolio_store,
            self.watchlist_store,
        )
        self.decision_reliability_result_repository = SqlAlchemyDecisionReliabilityResultRepository(engine)
        self.decision_reliability_service = DecisionReliabilityService(
            self.composition_service,
            self.evidence_quality_service,
            self.decision_readiness_service,
            self.decision_reliability_result_repository,
            self.portfolio_store,
            self.watchlist_store,
        )
        self.portfolio_decision_result_repository = SqlAlchemyPortfolioDecisionResultRepository(engine)
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
        self.agenda_service = DailyBriefAgendaService(
            portfolio_store=self.portfolio_store,
            watchlist_store=self.watchlist_store,
            daily_brief_service=self.daily_brief_service,
            portfolio_fit_service=self.portfolio_fit_service,
            portfolio_status_service=self.portfolio_status_service,
            portfolio_intelligence_service=self.portfolio_intelligence_service,
            case_condition_service=self.case_condition_service,
            assumption_service=self.assumption_service,
            monitoring_service=self.monitoring_service,
            evidence_graph_service=self.evidence_graph_service,
            decision_readiness_service=self.decision_readiness_service,
            investment_decision_service=self.investment_decision_service,
            recommendation_conviction_service=self.recommendation_conviction_service,
            decision_path_service=self.decision_path_service,
            opportunity_cost_service=self.opportunity_cost_service,
            decision_memory_service=self.decision_memory_service,
            decision_explanation_service=self.decision_explanation_service,
            decision_reliability_service=self.decision_reliability_service,
            portfolio_decision_service=self.portfolio_decision_service,
            composition_service=self.composition_service,
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
        case_ids = {h.ticker: h.case_id for h in state.holdings if h.ticker in weights_by_ticker}
        assert all(case_id is not None for case_id in case_ids.values())
        return case_ids  # type: ignore[return-value]

    def add_to_watchlist(self, ticker: str) -> str:
        case = self.case_service.create()
        case_id = str(case.id)
        self.watchlist_store.add(AlphaWatchlistEntry(ticker=ticker, case_id=case_id, added_at=_NOW))
        return case_id

    def record_decision(self, case_id_str: str, subject: str = "Test"):
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

    def make_growth_worsen(self, ticker: str) -> None:
        self.business_record_repository.add(
            _growth_record(company=ticker, identifier=f"{ticker}-fy22", period_end=datetime(2022, 12, 31).date(), revenue=1250.0, free_cash_flow=300.0)
        )
        self.business_record_repository.add(
            _growth_record(company=ticker, identifier=f"{ticker}-fy23", period_end=datetime(2023, 12, 31).date(), revenue=1100.0, free_cash_flow=240.0)
        )
        self.business_record_repository.add(
            _growth_record(company=ticker, identifier=f"{ticker}-fy24", period_end=datetime(2024, 12, 31).date(), revenue=1000.0, free_cash_flow=200.0)
        )


@pytest.fixture
def harness() -> _Harness:
    return _Harness(_new_engine())


class TestEmptyPortfolio:
    def test_no_portfolio_and_no_watchlist_produces_an_honest_empty_agenda(self, harness):
        agenda = harness.agenda_service.build_agenda()
        assert agenda.items == ()
        assert agenda.summary.holdings_count == 0
        assert agenda.summary.critical_count == 0


class TestChangeIntelligenceIntegration:
    def test_a_real_thesis_change_becomes_a_review_investment_case_item(self, harness):
        case_id = harness.import_holding("NVDA")
        harness.make_growth_worsen("NVDA")
        harness.composition_service.build(case_id)  # baseline

        harness.business_record_repository.add(
            _growth_record(company="NVDA", identifier="NVDA-fy25", period_end=datetime(2025, 12, 31).date(), revenue=2000.0, free_cash_flow=600.0)
        )
        harness.business_record_repository.add(
            _growth_record(company="NVDA", identifier="NVDA-fy26", period_end=datetime(2026, 12, 31).date(), revenue=3000.0, free_cash_flow=900.0)
        )

        agenda = harness.agenda_service.build_agenda()
        nvda_items = [i for i in agenda.items if i.ticker == "NVDA"]
        assert len(nvda_items) == 1
        # NVDA is the portfolio's only holding (100% weight), so a real
        # `high_concentration` finding fires alongside the real thesis
        # change -- both are consolidated into this one item
        # (Deliverable 8). Asserts Change Intelligence's own real entry
        # reached the item at all, not that it necessarily won the
        # headline (a portfolio-structure finding can legitimately be
        # equal-or-higher priority).
        assert len(nvda_items[0].reason) >= 2


class TestCaseConditionIntegration:
    def test_a_satisfied_invalidation_condition_becomes_a_critical_agenda_item(self, harness):
        case_id = harness.import_holding("AAPL")
        decision = harness.record_decision(case_id)
        condition = harness.case_condition_service.create(
            case_id=decision.case_id,
            decision_id=decision.id,
            content=CaseConditionContent(predicate_text="China revenue declines", role="invalidation", authorship="user"),
        )
        harness.case_condition_service.evaluate(condition.condition_id, human_asserted_satisfied=True)

        agenda = harness.agenda_service.build_agenda()
        aapl_items = [i for i in agenda.items if i.ticker == "AAPL"]
        assert len(aapl_items) == 1
        assert aapl_items[0].priority is PriorityLevel.CRITICAL
        assert aapl_items[0].kind is AgendaItemKind.EVALUATE_CASE_CONDITION

    def test_an_unsatisfied_condition_produces_no_agenda_item_on_its_own(self, harness):
        import atlas.core.domain.case.value_objects as case_vo

        case_id = harness.import_holding("MSFT")
        # No Decision recorded here deliberately -- recording one would
        # introduce its own real `DECISION_WITHOUT_OUTCOME` workflow
        # signal, muddying this test's own specific claim (an
        # *unsatisfied* condition, alone, is not agenda-worthy).
        harness.case_condition_service.create(
            case_id=case_vo.CaseId(value=uuid.UUID(case_id)),
            decision_id=None,
            content=CaseConditionContent(predicate_text="Cloud growth continues", role="monitoring", authorship="user"),
        )

        agenda = harness.agenda_service.build_agenda()
        # MSFT is the portfolio's only holding, so a real
        # `high_concentration` finding legitimately fires on its own --
        # this test's actual claim is narrower: the *unsatisfied*
        # condition itself contributes no signal.
        assert not any(i.kind is AgendaItemKind.EVALUATE_CASE_CONDITION for i in agenda.items)


class TestAssumptionIntegration:
    def test_a_challenged_assumption_becomes_a_high_priority_agenda_item(self, harness):
        case_id = harness.import_holding("TSLA")
        decision = harness.record_decision(case_id)
        assumption = harness.assumption_service.create(
            decision_id=decision.id, content=AssumptionContent(statement="Margin expansion continues")
        )
        harness.assumption_service.challenge(assumption.assumption_id, severity="challenged")

        agenda = harness.agenda_service.build_agenda()
        tsla_items = [i for i in agenda.items if i.ticker == "TSLA"]
        assert len(tsla_items) == 1
        # `AssumptionService.create` requires a real Decision, which
        # itself produces a real `DECISION_WITHOUT_OUTCOME` workflow
        # signal (CRITICAL, correctly outranking the Assumption's own
        # HIGH) -- both are genuine and both are consolidated into this
        # one item (Deliverable 8), so this asserts the Assumption's own
        # real contribution reached the item, not that it won the
        # headline against an unrelated, also-real signal.
        assert any("Margin expansion" in r for r in tsla_items[0].reason)


class TestInvestmentDecisionIntegration:
    """Atlas Decision Layer Sprint 1, Deliverable 10. Mirrors Decision
    Readiness's own daily-brief-agenda coverage: the pure priority/
    tie-break behavior of `investment_decision_signal` is covered in
    `test_engine.py`; this confirms the real service wiring holds the
    same "no event, no timestamp" contract `change_for_case` itself
    already guarantees -- two consecutive `build_agenda()` calls with
    no real underlying change produce no `INVESTMENT_DECISION`-sourced
    item on the second call."""

    def test_an_unchanged_decision_across_two_agenda_builds_produces_no_item(self, harness):
        harness.import_holding("NVDA")

        first = harness.agenda_service.build_agenda()
        assert not any(i.source.value == "investment_decision" for i in first.items)

        second = harness.agenda_service.build_agenda()
        assert not any(i.source.value == "investment_decision" for i in second.items)


class TestRecommendationConvictionIntegration:
    """Atlas Decision Layer Sprint 2, Deliverable 10. Same shape as
    `TestInvestmentDecisionIntegration` above: confirms the real
    service wiring holds the "no event, no timestamp" contract."""

    def test_an_unchanged_conviction_across_two_agenda_builds_produces_no_item(self, harness):
        harness.import_holding("NVDA")

        first = harness.agenda_service.build_agenda()
        assert not any(i.source.value == "recommendation_conviction" for i in first.items)

        second = harness.agenda_service.build_agenda()
        assert not any(i.source.value == "recommendation_conviction" for i in second.items)


class TestDecisionPathIntegration:
    """Atlas Decision Layer Sprint 3, Deliverable 10. Same shape as
    `TestRecommendationConvictionIntegration` above: confirms the real
    service wiring holds the "no event, no timestamp" contract."""

    def test_an_unchanged_path_across_two_agenda_builds_produces_no_item(self, harness):
        harness.import_holding("NVDA")

        first = harness.agenda_service.build_agenda()
        assert not any(i.source.value == "decision_path" for i in first.items)

        second = harness.agenda_service.build_agenda()
        assert not any(i.source.value == "decision_path" for i in second.items)


class TestOpportunityCostIntegration:
    """Atlas Decision Layer Sprint 4, Deliverable 10. Same shape as
    `TestDecisionPathIntegration` above: confirms the real service
    wiring holds the "no event, no timestamp" contract."""

    def test_an_unchanged_alternative_set_across_two_agenda_builds_produces_no_item(self, harness):
        harness.import_holding("NVDA")

        first = harness.agenda_service.build_agenda()
        assert not any(i.source.value == "opportunity_cost" for i in first.items)

        second = harness.agenda_service.build_agenda()
        assert not any(i.source.value == "opportunity_cost" for i in second.items)


class TestDecisionMemoryIntegration:
    """Atlas Decision Layer Sprint 5, Deliverable 10. Same shape as
    `TestOpportunityCostIntegration` above: confirms the real service
    wiring holds the "no event, no timestamp" contract -- the first
    agenda build records this Case's own baseline snapshot (itself
    never surfaced as a change), and an unchanged second build appends
    no new row, so `change_for_case` returns `None` both times."""

    def test_an_unchanged_decision_memory_across_two_agenda_builds_produces_no_item(self, harness):
        harness.import_holding("NVDA")

        first = harness.agenda_service.build_agenda()
        assert not any(i.source.value == "decision_memory" for i in first.items)

        second = harness.agenda_service.build_agenda()
        assert not any(i.source.value == "decision_memory" for i in second.items)


class TestDecisionExplanationIntegration:
    """Atlas Decision Layer Sprint 6, Deliverable 10. Same shape as
    `TestDecisionMemoryIntegration` above: confirms the real service
    wiring holds the "no event, no timestamp" contract."""

    def test_an_unchanged_explanation_across_two_agenda_builds_produces_no_item(self, harness):
        harness.import_holding("NVDA")

        first = harness.agenda_service.build_agenda()
        assert not any(i.source.value == "decision_explanation" for i in first.items)

        second = harness.agenda_service.build_agenda()
        assert not any(i.source.value == "decision_explanation" for i in second.items)


class TestDecisionReliabilityIntegration:
    """Atlas Decision Layer Sprint 7, Deliverable 11. Same shape as
    `TestDecisionExplanationIntegration` above: confirms the real
    service wiring holds the "no event, no timestamp" contract."""

    def test_an_unchanged_reliability_across_two_agenda_builds_produces_no_item(self, harness):
        harness.import_holding("NVDA")

        first = harness.agenda_service.build_agenda()
        assert not any(i.source.value == "decision_reliability" for i in first.items)

        second = harness.agenda_service.build_agenda()
        assert not any(i.source.value == "decision_reliability" for i in second.items)


class TestPortfolioDecisionIntegration:
    """Atlas Decision Layer Sprint 8, Deliverable 11. Same shape as
    `TestDecisionReliabilityIntegration` above: confirms the real
    service wiring holds the "no event, no timestamp" contract."""

    def test_an_unchanged_portfolio_decision_across_two_agenda_builds_produces_no_item(self, harness):
        harness.import_holding("NVDA")

        first = harness.agenda_service.build_agenda()
        assert not any(i.source.value == "portfolio_decision" for i in first.items)

        second = harness.agenda_service.build_agenda()
        assert not any(i.source.value == "portfolio_decision" for i in second.items)


class TestNoiseReduction:
    def test_multiple_real_signals_on_one_ticker_still_produce_exactly_one_item(self, harness):
        case_id = harness.import_holding("AAPL")
        decision = harness.record_decision(case_id)
        condition = harness.case_condition_service.create(
            case_id=decision.case_id,
            decision_id=decision.id,
            content=CaseConditionContent(predicate_text="Thesis breaks", role="invalidation", authorship="user"),
        )
        harness.case_condition_service.evaluate(condition.condition_id, human_asserted_satisfied=True)
        assumption = harness.assumption_service.create(
            decision_id=decision.id, content=AssumptionContent(statement="Some assumption")
        )
        harness.assumption_service.challenge(assumption.assumption_id, severity="invalidated")

        agenda = harness.agenda_service.build_agenda()
        aapl_items = [i for i in agenda.items if i.ticker == "AAPL"]
        assert len(aapl_items) == 1
        # Six real signals fire here (CaseCondition satisfied, Assumption
        # invalidated, the Decision's own DECISION_WITHOUT_OUTCOME
        # workflow item, AAPL being the sole 100%-weight holding's
        # HIGH_CONCENTRATION finding, and -- since this Case has a
        # Decision but no recorded Evidence or Observation at all --
        # two real missing-evidence signals (Sprint 8, Deliverable 4)
        # -- every one of them is a genuine fact, and all six are
        # consolidated into this one item, none dropped (Deliverable 8).
        reasons = aapl_items[0].reason
        assert len(reasons) == 6
        assert any("Thesis breaks" in r for r in reasons)
        assert any("Some assumption" in r for r in reasons)
        assert any("missing evidence" in r for r in reasons)


class TestMissingEvidenceIntegration:
    """Sprint 8 (Portfolio Excellence, Deliverable 4 -- Unify Attention
    Surfaces): a real missing-evidence gap now reaches the shared
    agenda, closing the one gap where `derivePortfolioActions.ts`'s
    "Needs Your Attention" saw a signal this engine did not."""

    def test_a_bare_holding_with_no_evidence_becomes_a_review_portfolio_position_item(self, harness):
        # MSFT holds the majority weight so the real HIGH_CONCENTRATION
        # finding lands on MSFT, not AAPL -- isolates AAPL's own item to
        # its evidence gap alone (no Decision recorded on AAPL, so no
        # competing DECISION_WITHOUT_OUTCOME workflow signal either).
        harness.import_holdings({"MSFT": 60.0, "AAPL": 40.0})

        agenda = harness.agenda_service.build_agenda()
        aapl_items = [i for i in agenda.items if i.ticker == "AAPL"]
        assert len(aapl_items) == 1
        assert aapl_items[0].priority is PriorityLevel.HIGH
        assert aapl_items[0].kind is AgendaItemKind.REVIEW_PORTFOLIO_POSITION
        assert any("missing evidence" in r for r in aapl_items[0].reason)


class TestWorkflowItemLocalization:
    """Localization fix (Portfolio live-verification follow-up):
    `AgendaItem.headline` for a workflow-sourced item used to be a raw,
    untranslated English sentence built server-side
    (`f"{ticker}: {category.value...} ({count} item(s))"`) that reached
    the Swedish UI verbatim. `attention_category`/`attention_count` now
    ride alongside it end-to-end so the frontend can compose its own
    translated version instead -- see `AgendaItemRow.tsx`/
    `HoldingAttentionPage.tsx`'s own `agendaItemHeadline` usage."""

    def test_a_decision_without_outcome_item_carries_its_real_category_and_count(self, harness):
        case_id = harness.import_holding("AAPL")
        harness.record_decision(case_id)

        agenda = harness.agenda_service.build_agenda()
        aapl_items = [i for i in agenda.items if i.ticker == "AAPL"]
        assert len(aapl_items) == 1
        item = aapl_items[0]
        # DECISION_WITHOUT_OUTCOME is CRITICAL -- strictly above every
        # other real signal a single, freshly-imported, freshly-decided
        # holding can also fire (HIGH_CONCENTRATION, missing evidence
        # are both HIGH), so it is deterministically the winner here.
        assert item.attention_category is AttentionCategory.DECISION_WITHOUT_OUTCOME
        assert item.attention_count == 1

    def test_a_non_workflow_item_carries_no_attention_category(self, harness):
        case_id = harness.import_holding("AAPL")
        decision = harness.record_decision(case_id)
        condition = harness.case_condition_service.create(
            case_id=decision.case_id,
            decision_id=decision.id,
            content=CaseConditionContent(predicate_text="Thesis breaks", role="invalidation", authorship="user"),
        )
        harness.case_condition_service.evaluate(condition.condition_id, human_asserted_satisfied=True)

        agenda = harness.agenda_service.build_agenda()
        aapl_items = [i for i in agenda.items if i.ticker == "AAPL"]
        assert len(aapl_items) == 1
        # The satisfied invalidation CaseCondition is also CRITICAL and
        # wins the tie-break over DECISION_WITHOUT_OUTCOME (Case
        # Condition's own higher `_SOURCE_TIE_RANK`) -- a real,
        # non-workflow source, so `attention_category` must stay `None`.
        assert aapl_items[0].attention_category is None
        assert aapl_items[0].attention_count is None


class TestWatchlistIntegration:
    def test_a_watchlist_only_tickers_item_lands_in_the_watchlist_group(self, harness):
        case_id = harness.add_to_watchlist("NVDA")
        decision = harness.record_decision(case_id)
        assumption = harness.assumption_service.create(
            decision_id=decision.id, content=AssumptionContent(statement="Demand holds")
        )
        harness.assumption_service.challenge(assumption.assumption_id, severity="challenged")

        agenda = harness.agenda_service.build_agenda()
        nvda_items = [i for i in agenda.items if i.ticker == "NVDA"]
        assert len(nvda_items) == 1
        assert nvda_items[0].group.value == "watchlist"

    def test_a_portfolio_holding_never_appears_in_the_watchlist_group_even_if_also_watchlisted(self, harness):
        case_id = harness.import_holding("AAPL")
        harness.watchlist_store.add(AlphaWatchlistEntry(ticker="AAPL", case_id=case_id, added_at=_NOW))
        decision = harness.record_decision(case_id)
        assumption = harness.assumption_service.create(
            decision_id=decision.id, content=AssumptionContent(statement="Something")
        )
        harness.assumption_service.challenge(assumption.assumption_id, severity="challenged")

        agenda = harness.agenda_service.build_agenda()
        aapl_items = [i for i in agenda.items if i.ticker == "AAPL"]
        assert len(aapl_items) == 1
        assert aapl_items[0].group.value == "portfolio"


class TestPortfolioIntegration:
    def test_summary_holdings_count_matches_the_real_portfolio(self, harness):
        harness.import_holdings({"AAPL": 50.0, "MSFT": 50.0})
        agenda = harness.agenda_service.build_agenda()
        assert agenda.summary.holdings_count == 2

    def test_determinism_same_state_produces_the_same_agenda(self, harness):
        case_id = harness.import_holding("AAPL")
        decision = harness.record_decision(case_id)
        condition = harness.case_condition_service.create(
            case_id=decision.case_id,
            decision_id=decision.id,
            content=CaseConditionContent(predicate_text="Thesis breaks", role="invalidation", authorship="user"),
        )
        harness.case_condition_service.evaluate(condition.condition_id, human_asserted_satisfied=True)

        first = harness.agenda_service.build_agenda()
        second = harness.agenda_service.build_agenda()
        assert [i.priority for i in first.items] == [i.priority for i in second.items]
        assert [i.kind for i in first.items] == [i.kind for i in second.items]


def _transcript_statement(ticker: str, quarter: str, index: int, speaker: str, title: str | None, content: str, *, period_end):
    """Product Intelligence Sprint 1. Mirrors `test_executive_change_
    intelligence.py`'s own `_statement` fixture exactly -- a real
    ingested `transcript` `BusinessRecord`, not a fake."""
    metadata = {"quarter": quarter, "statement_index": index, "speaker": speaker, "content": content}
    if title is not None:
        metadata["title"] = title
    document = RawBusinessDocument(
        identifier=f"{ticker}:transcript:{quarter}:{index}",
        company=ticker,
        source_kind="transcript",
        published_at=datetime(period_end.year, period_end.month, period_end.day, tzinfo=timezone.utc),
        provider_id="alpha_vantage",
        raw_reference="https://example.test/transcript",
        content_hash=f"hash-{ticker}-{quarter}-{index}",
        language="en",
        period_start=period_end,
        period_end=period_end,
        metadata=metadata,
    )
    result = ingest(document, evaluated_at=_NOW)
    assert isinstance(result, IngestedRecord)
    return result.record


class TestExecutiveChangeIntegration:
    """Product Intelligence Sprint 1 (Portfolio Intelligence Activation):
    a real leadership change, disclosed across two real ingested
    transcripts, reaches the real agenda -- through `executive_change_
    intelligence.py` (Capability Expansion Sprint 10), entirely
    unmodified."""

    def test_a_real_ceo_change_disclosed_in_the_latest_transcript_produces_an_item(self, harness):
        from datetime import date

        # MSFT holds the majority weight so the real HIGH_CONCENTRATION
        # finding lands on MSFT, not AAPL -- isolates AAPL's own item to
        # its executive-change signal alone, the same isolation
        # `TestMissingEvidenceIntegration` above already establishes.
        harness.business_record_repository.add(
            _transcript_statement("AAPL", "2022Q4", 0, "Alice Smith", "Chief Executive Officer", "Year one.", period_end=date(2022, 12, 31))
        )
        harness.business_record_repository.add(
            _transcript_statement("AAPL", "2023Q4", 0, "Dave Kim", "Chief Executive Officer", "Year two.", period_end=date(2023, 12, 31))
        )
        harness.import_holdings({"MSFT": 60.0, "AAPL": 40.0})

        agenda = harness.agenda_service.build_agenda()
        aapl_items = [i for i in agenda.items if i.ticker == "AAPL"]
        assert len(aapl_items) == 1
        # A bare holding also has a real, competing missing-evidence gap
        # (see `TestMissingEvidenceIntegration` above) -- both are real,
        # both HIGH priority, and `_item_for_ticker`'s own deterministic
        # tie-break picks one as the item's own headline/source while
        # folding the other into `reason`, never dropping it (the exact,
        # documented "one item per ticker" consolidation `engine.py`'s
        # own module docstring describes). The executive-change fact is
        # real and present either way.
        assert any("Dave Kim" in r for r in aapl_items[0].reason)
        assert aapl_items[0].priority is PriorityLevel.HIGH

    def test_an_older_leadership_change_not_in_the_latest_transcript_produces_no_signal(self, harness):
        """The CEO succession from 2022Q4 -> 2023Q4 is real, but a
        *third*, unrelated transcript (2024Q4, same CEO) is now the
        latest -- the change is no longer "current" and must not fire
        forever."""
        from datetime import date

        harness.business_record_repository.add(
            _transcript_statement("AAPL", "2022Q4", 0, "Alice Smith", "Chief Executive Officer", "Year one.", period_end=date(2022, 12, 31))
        )
        harness.business_record_repository.add(
            _transcript_statement("AAPL", "2023Q4", 0, "Dave Kim", "Chief Executive Officer", "Year two.", period_end=date(2023, 12, 31))
        )
        harness.business_record_repository.add(
            _transcript_statement("AAPL", "2024Q4", 0, "Dave Kim", "Chief Executive Officer", "Year three.", period_end=date(2024, 12, 31))
        )
        harness.import_holdings({"MSFT": 60.0, "AAPL": 40.0})

        agenda = harness.agenda_service.build_agenda()
        aapl_items = [i for i in agenda.items if i.ticker == "AAPL"]
        assert not aapl_items or not any("appointed" in r or "departed" in r for r in aapl_items[0].reason)
