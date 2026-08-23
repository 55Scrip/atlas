"""ATLAS-031 Phase 23 -- cross-surface consistency using real-data-shaped
BusinessRecords: for the same Case, Portfolio Cockpit, the canonical
Investment Case API, and Discovery's own context must all agree once
external business data has been ingested, exactly as ATLAS-030's own
`test_portfolio_cockpit_investment_case_discovery_consistency_v1.py`
already proved for the pre-real-data ("everything INSUFFICIENT_INPUT")
case.

No live network anywhere in this file -- records are persisted directly
via `SqlAlchemyBusinessRecordRepository`, standing in for a completed
`refresh_company_data` run (that orchestration itself is tested in
`tests/unit/alpha/business_data_refresh/test_service.py`).
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.discovery_context.service import DiscoveryContextService
from atlas.alpha.evidence_timeline.api.dependencies import get_evidence_snapshot_repository
from atlas.alpha.ingestion.api.dependencies import get_ingestion_result_repository
from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.investment_case_change.table import create_investment_case_snapshot_table
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
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
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

_EVALUATED_AT = datetime(2026, 8, 9, tzinfo=timezone.utc)


def _fundamentals_doc(*, ticker: str, period_end: str, revenue: float, fcf: float) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=f"{ticker}:FY:{period_end}",
        company=ticker,
        source_kind="financial_statement",
        published_at=_EVALUATED_AT,
        provider_id="sec_edgar",
        raw_reference="https://example.test/filing",
        content_hash=f"hash-{ticker}-{period_end}-{revenue}",
        language="en",
        period_start=date(int(period_end[:4]) - 1, 1, 1),
        period_end=date.fromisoformat(period_end),
        metadata={"revenue": revenue, "free_cash_flow": fcf, "currency": "USD"},
    )


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
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
    business_record_repository = SqlAlchemyBusinessRecordRepository(engine)
    create_investment_case_snapshot_table(engine)
    snapshot_repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
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
        snapshot_repository=snapshot_repository,
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


def _persist_real_data(engine: Engine, ticker: str) -> None:
    create_business_record_table(engine)
    repository = SqlAlchemyBusinessRecordRepository(engine)
    documents = (
        _fundamentals_doc(ticker=ticker, period_end="2022-12-31", revenue=100, fcf=10),
        _fundamentals_doc(ticker=ticker, period_end="2023-12-31", revenue=125, fcf=20),
    )
    records: list = []
    for document in documents:
        result = ingest(document, existing_records=tuple(records), evaluated_at=_EVALUATED_AT)
        assert isinstance(result, IngestedRecord), result
        records.append(result.record)
        repository.add(result.record)


class TestRealDataCrossSurfaceAgreement:
    def test_growth_agrees_across_cockpit_investment_case_and_discovery(self, client):
        _import_portfolio(client, [{"ticker": "NVDA", "weightPercent": 100}])
        _persist_real_data(client.engine, "NVDA")

        cockpit = client.get("/alpha-portfolio/cockpit").json()
        case_id = cockpit["holdings"][0]["caseId"]
        investment_case = client.get(f"/cases/{case_id}/analysis").json()
        discovery = _discovery_context_service(client.engine).build(case_id)
        composition = _discovery_context_service(client.engine)._investment_case_composition_service.build(case_id)

        case_growth = next(f for f in investment_case["businessAnalysis"]["findings"] if f["kind"] == "growth")["status"]
        composition_growth = next(
            f for f in composition.canonical_analysis.business_analysis.findings if f.kind.value == "growth"
        ).status.value

        assert cockpit["holdings"][0]["business"]["growth"] == "strong"
        assert case_growth == "strong"
        assert composition_growth == "strong"
        assert discovery.case is not None
        assert discovery.case.held is True

    def test_a_second_holdings_business_records_never_leak_into_the_first(self, client):
        """Real-data isolation: NVDA gets real (strong) data, MSFT gets
        none -- MSFT must stay honestly INSUFFICIENT_INPUT."""
        _import_portfolio(
            client, [{"ticker": "NVDA", "weightPercent": 50}, {"ticker": "MSFT", "weightPercent": 50}]
        )
        _persist_real_data(client.engine, "NVDA")

        cockpit = client.get("/alpha-portfolio/cockpit").json()
        by_ticker = {h["ticker"]: h for h in cockpit["holdings"]}
        assert by_ticker["NVDA"]["business"]["growth"] == "strong"
        assert by_ticker["MSFT"]["business"]["growth"] == "insufficient_input"
