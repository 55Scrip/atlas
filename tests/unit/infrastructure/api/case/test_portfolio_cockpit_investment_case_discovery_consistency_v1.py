"""ATLAS-030 Phase 19 -- cross-surface consistency: for the same Case,
Portfolio Cockpit (`GET /alpha-portfolio/cockpit`), the canonical
Investment Case API (`GET /cases/{case_id}/analysis`), and Discovery's
own context (`DiscoveryContextService.build`) must all agree. All three
are now built from the exact same `InvestmentCaseComposition` --
Portfolio Cockpit via `build_many`, Investment Case via `build`,
Discovery via `build` -- so any disagreement here would mean one of the
three drifted from the real underlying analysis.

Discovery has no REST endpoint of its own (`DiscoveryContextService` is
injected directly into `/discovery/chat`, never exposed independently),
so it is constructed directly here against the same overridden in-memory
engine the HTTP client uses -- the same composition FastAPI's own
`Depends` chain would otherwise assemble.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.api.dependencies import get_business_record_repository
from atlas.alpha.discovery_context.service import DiscoveryContextService
from atlas.alpha.evidence_timeline.api.dependencies import get_evidence_snapshot_repository
from atlas.alpha.ingestion.api.dependencies import get_ingestion_result_repository
from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case_change.api.dependencies import get_investment_case_snapshot_repository
from atlas.alpha.monitoring.repository import SqlAlchemyMonitoringResultRepository, SqlAlchemyMonitoringRunRecordRepository
from atlas.alpha.monitoring.service import MonitoringService
from atlas.alpha.monitoring.table import create_monitoring_result_table, create_monitoring_run_record_table
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store, get_alpha_trade_log_store
from atlas.alpha.portfolio_fit.api.dependencies import get_portfolio_fit_service
from atlas.alpha.portfolio_intelligence.service import PortfolioIntelligenceService
from atlas.alpha.portfolio_status.api.dependencies import get_portfolio_status_service
from atlas.alpha.stance.api.dependencies import get_stance_service
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.table import create_alpha_watchlist_entry_table
from atlas.core.application.case_condition.case_condition_service import CaseConditionService
from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine, get_decision_repository
from atlas.core.infrastructure.api.evidence.dependencies import get_evidence_repository
from atlas.core.infrastructure.api.knowledge_reference.dependencies import get_outcome_repository
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository
from atlas.core.infrastructure.persistence.case_condition.sqlalchemy_repository import (
    SqlAlchemyCaseConditionEventRepository,
)
from atlas.core.infrastructure.persistence.case_condition.table import create_case_condition_events_table
from atlas.core.infrastructure.persistence.decision.table import create_decision_table


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(engine)
    app = create_app()
    app.dependency_overrides[get_decision_engine] = lambda: engine
    test_client = TestClient(app)
    test_client.engine = engine  # type: ignore[attr-defined]
    return test_client


def _discovery_context_service(engine: Engine) -> DiscoveryContextService:
    portfolio_store = get_alpha_portfolio_store(engine)
    trade_log_store = get_alpha_trade_log_store(engine)
    decision_repository = get_decision_repository(engine)
    observation_repository = get_observation_repository(engine)
    evidence_repository = get_evidence_repository(engine)
    outcome_repository = get_outcome_repository(engine)
    business_record_repository = get_business_record_repository(engine)
    create_alpha_watchlist_entry_table(engine)
    watchlist_store = get_alpha_watchlist_store(engine)
    evidence_snapshot_repository = get_evidence_snapshot_repository(engine)
    create_case_condition_events_table(engine)
    case_condition_service = CaseConditionService(
        SqlAlchemyCaseConditionEventRepository(engine), get_case_repository(engine), decision_repository
    )
    create_monitoring_result_table(engine)
    create_monitoring_run_record_table(engine)
    monitoring_result_repository = SqlAlchemyMonitoringResultRepository(engine)
    monitoring_run_record_repository = SqlAlchemyMonitoringRunRecordRepository(engine)

    portfolio_status_service = get_portfolio_status_service(
        portfolio_store=portfolio_store,
        trade_log_store=trade_log_store,
        decision_repository=decision_repository,
        outcome_repository=outcome_repository,
        observation_repository=observation_repository,
    )
    investment_case_composition_service = get_investment_case_composition_service(
        case_repository=get_case_repository(engine),
        decision_repository=decision_repository,
        observation_repository=observation_repository,
        evidence_repository=evidence_repository,
        outcome_repository=outcome_repository,
        portfolio_store=portfolio_store,
        trade_log_store=trade_log_store,
        business_record_repository=business_record_repository,
        snapshot_repository=get_investment_case_snapshot_repository(engine),
        watchlist_store=watchlist_store,
    )
    portfolio_intelligence_service = PortfolioIntelligenceService(
        portfolio_store,
        trade_log_store,
        decision_repository,
        observation_repository,
        evidence_repository,
        outcome_repository,
        portfolio_status_service,
    )
    portfolio_fit_service = get_portfolio_fit_service(
        portfolio_store=portfolio_store,
        watchlist_store=watchlist_store,
        composition_service=investment_case_composition_service,
    )
    stance_service = get_stance_service(
        composition_service=investment_case_composition_service,
        portfolio_fit_service=portfolio_fit_service,
        portfolio_store=portfolio_store,
        watchlist_store=watchlist_store,
    )
    monitoring_service = MonitoringService(
        portfolio_store=portfolio_store,
        watchlist_store=watchlist_store,
        composition_service=investment_case_composition_service,
        stance_service=stance_service,
        business_record_repository=business_record_repository,
        evidence_snapshot_repository=evidence_snapshot_repository,
        case_condition_service=case_condition_service,
        monitoring_result_repository=monitoring_result_repository,
        decision_repository=decision_repository,
        observation_repository=observation_repository,
        monitoring_run_record_repository=monitoring_run_record_repository,
        ingestion_result_repository=get_ingestion_result_repository(engine),
    )
    return DiscoveryContextService(
        portfolio_intelligence_service=portfolio_intelligence_service,
        investment_case_composition_service=investment_case_composition_service,
        portfolio_status_service=portfolio_status_service,
        monitoring_service=monitoring_service,
    )


def _import_portfolio(client, holdings: list[dict]) -> dict:
    response = client.post("/alpha-portfolio/import", json={"holdings": holdings})
    assert response.status_code == 201, response.text
    return response.json()


class TestConvictionAndConfidenceAgreement:
    def test_all_three_surfaces_agree(self, client):
        _import_portfolio(client, [{"ticker": "NVDA", "weightPercent": 100}])
        cockpit = client.get("/alpha-portfolio/cockpit").json()
        case_id = cockpit["holdings"][0]["caseId"]
        investment_case = client.get(f"/cases/{case_id}/analysis").json()

        discovery = _discovery_context_service(client.engine).build(case_id)

        assert cockpit["holdings"][0]["conviction"]["level"] == investment_case["conviction"]["level"]
        assert discovery.case.conviction_level.value == investment_case["conviction"]["level"]

        assert cockpit["holdings"][0]["confidence"] == investment_case["confidence"]
        assert discovery.case.confidence.value == investment_case["confidence"]


class TestValuationAgreement:
    def test_fcf_yield_status_matches_across_the_board(self, client):
        _import_portfolio(client, [{"ticker": "NVDA", "weightPercent": 100}])
        cockpit = client.get("/alpha-portfolio/cockpit").json()
        case_id = cockpit["holdings"][0]["caseId"]
        investment_case = client.get(f"/cases/{case_id}/analysis").json()
        case_finding = next(f for f in investment_case["valuation"]["findings"] if f["kind"] == "fcf_yield_relative")

        assert cockpit["holdings"][0]["valuation"]["status"] == case_finding["status"]


class TestBusinessAgreement:
    def test_growth_and_capital_allocation_match(self, client):
        _import_portfolio(client, [{"ticker": "NVDA", "weightPercent": 100}])
        cockpit = client.get("/alpha-portfolio/cockpit").json()
        case_id = cockpit["holdings"][0]["caseId"]
        investment_case = client.get(f"/cases/{case_id}/analysis").json()
        findings_by_kind = {f["kind"]: f for f in investment_case["businessAnalysis"]["findings"]}

        assert cockpit["holdings"][0]["business"]["growth"] == findings_by_kind["growth"]["status"]
        assert (
            cockpit["holdings"][0]["business"]["capitalAllocation"]
            == findings_by_kind["capital_allocation"]["status"]
        )


class TestRiskVectorAgreement:
    def test_investment_case_and_discoverys_underlying_composition_agree(self, client):
        _import_portfolio(client, [{"ticker": "NVDA", "weightPercent": 100}])
        cockpit = client.get("/alpha-portfolio/cockpit").json()
        case_id = cockpit["holdings"][0]["caseId"]
        investment_case = client.get(f"/cases/{case_id}/analysis").json()

        service = _discovery_context_service(client.engine)
        discovery = service.build(case_id)
        composition = service._investment_case_composition_service.build(case_id)

        case_statuses = {f["category"]: f["status"] for f in investment_case["risk"]["findings"]}
        composition_statuses = {
            f.category.value: f.status.value for f in composition.canonical_analysis.risk_analysis.findings
        }
        assert case_statuses == composition_statuses
        assert discovery.case is not None


class TestOpenQuestionsAgreement:
    def test_discovery_uses_the_same_corrected_list_as_investment_case(self, client):
        _import_portfolio(client, [{"ticker": "NVDA", "weightPercent": 100}])
        cockpit = client.get("/alpha-portfolio/cockpit").json()
        case_id = cockpit["holdings"][0]["caseId"]
        investment_case = client.get(f"/cases/{case_id}/analysis").json()

        discovery = _discovery_context_service(client.engine).build(case_id)

        case_question_kinds = {q["kind"] for q in investment_case["openQuestions"]}
        discovery_question_kinds = {q.value for q in discovery.case.open_questions}
        assert discovery_question_kinds == case_question_kinds


class TestCaseIdAgreement:
    def test_all_three_resolve_to_the_same_case_id(self, client):
        _import_portfolio(client, [{"ticker": "NVDA", "weightPercent": 100}])
        cockpit = client.get("/alpha-portfolio/cockpit").json()
        case_id = cockpit["holdings"][0]["caseId"]
        investment_case = client.get(f"/cases/{case_id}/analysis").json()
        discovery = _discovery_context_service(client.engine).build(case_id)

        assert investment_case["caseId"] == case_id
        assert discovery.identity.case_id == case_id
