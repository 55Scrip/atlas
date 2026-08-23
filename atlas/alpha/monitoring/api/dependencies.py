"""Composition wiring for the Monitoring API. Reuses every sibling
package's own existing provider directly -- the same "each Alpha
package wires its own dependencies, reusing siblings' providers"
convention every other package here already follows.

**Internal Alpha Fix Sprint 1, Deliverable 3.** `build_monitoring_service`
is new: a plain function (not a FastAPI `Depends()` provider) that builds
the identical `MonitoringService` shape `get_monitoring_service` below
does, from a single already-open `engine` rather than FastAPI's nested
dependency resolution. It exists solely for background-task call sites
(`atlas.alpha.portfolio.api.router._run_bulk_enrichment_in_background`),
which already must construct their own fresh `Engine`/repositories by
hand -- see that function's own docstring for exactly why a request-
scoped `Engine` cannot cross onto Starlette's background-task thread.
This mirrors that function's existing "construct fresh from engine"
convention for a deeper dependency tree, rather than inventing a second
one; every sub-provider it calls is the exact same, unmodified provider
function `get_monitoring_service` itself depends on, just invoked
directly with an explicit `engine=` instead of through `Depends()`.
`get_monitoring_service` itself is left completely unchanged below, so
existing request-time wiring carries zero risk from this addition.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.business_data_refresh.api.dependencies import get_business_record_repository
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.evidence_timeline.api.dependencies import get_evidence_snapshot_repository
from atlas.alpha.evidence_timeline.repository import SqlAlchemyEvidenceSnapshotRepository
from atlas.alpha.ingestion.api.dependencies import get_ingestion_result_repository
from atlas.alpha.ingestion.repository import SqlAlchemyIngestionResultRepository
from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.investment_case_change.api.dependencies import get_investment_case_snapshot_repository
from atlas.alpha.monitoring.repository import SqlAlchemyMonitoringResultRepository, SqlAlchemyMonitoringRunRecordRepository
from atlas.alpha.monitoring.service import MonitoringService
from atlas.alpha.monitoring.table import create_monitoring_result_table, create_monitoring_run_record_table
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store, get_alpha_trade_log_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio_fit.api.dependencies import get_portfolio_fit_service
from atlas.alpha.stance.api.dependencies import get_stance_service
from atlas.alpha.stance.service import StanceService
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.core.application.case_condition.case_condition_service import CaseConditionService
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.api.case_condition.dependencies import get_case_condition_repository, get_case_condition_service
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine, get_decision_repository
from atlas.core.infrastructure.api.evidence.dependencies import get_evidence_repository
from atlas.core.infrastructure.api.knowledge_reference.dependencies import get_outcome_repository
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository

__all__ = [
    "build_monitoring_service",
    "get_monitoring_result_repository",
    "get_monitoring_run_record_repository",
    "get_monitoring_service",
]


def build_monitoring_service(engine: Engine) -> MonitoringService:
    case_repository = get_case_repository(engine=engine)
    decision_repository = get_decision_repository(engine=engine)
    observation_repository = get_observation_repository(engine=engine)
    portfolio_store = get_alpha_portfolio_store(engine=engine)
    watchlist_store = get_alpha_watchlist_store(engine=engine)
    business_record_repository = get_business_record_repository(engine=engine)

    composition_service = get_investment_case_composition_service(
        case_repository=case_repository,
        decision_repository=decision_repository,
        observation_repository=observation_repository,
        evidence_repository=get_evidence_repository(engine=engine),
        outcome_repository=get_outcome_repository(engine=engine),
        portfolio_store=portfolio_store,
        trade_log_store=get_alpha_trade_log_store(engine=engine),
        business_record_repository=business_record_repository,
        watchlist_store=watchlist_store,
        snapshot_repository=get_investment_case_snapshot_repository(engine=engine),
    )
    stance_service = get_stance_service(
        composition_service=composition_service,
        portfolio_fit_service=get_portfolio_fit_service(
            portfolio_store=portfolio_store,
            watchlist_store=watchlist_store,
            composition_service=composition_service,
        ),
        portfolio_store=portfolio_store,
        watchlist_store=watchlist_store,
    )
    case_condition_service = get_case_condition_service(
        condition_repository=get_case_condition_repository(engine=engine),
        case_repository=case_repository,
        decision_repository=decision_repository,
    )
    return MonitoringService(
        portfolio_store=portfolio_store,
        watchlist_store=watchlist_store,
        composition_service=composition_service,
        stance_service=stance_service,
        business_record_repository=business_record_repository,
        evidence_snapshot_repository=get_evidence_snapshot_repository(engine=engine),
        case_condition_service=case_condition_service,
        monitoring_result_repository=get_monitoring_result_repository(engine=engine),
        decision_repository=decision_repository,
        observation_repository=observation_repository,
        monitoring_run_record_repository=get_monitoring_run_record_repository(engine=engine),
        ingestion_result_repository=get_ingestion_result_repository(engine=engine),
    )


def get_monitoring_result_repository(engine: Engine = Depends(get_decision_engine)) -> SqlAlchemyMonitoringResultRepository:
    create_monitoring_result_table(engine)
    return SqlAlchemyMonitoringResultRepository(engine)


def get_monitoring_run_record_repository(engine: Engine = Depends(get_decision_engine)) -> SqlAlchemyMonitoringRunRecordRepository:
    create_monitoring_run_record_table(engine)
    return SqlAlchemyMonitoringRunRecordRepository(engine)


def get_monitoring_service(
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
    composition_service: InvestmentCaseCompositionService = Depends(get_investment_case_composition_service),
    stance_service: StanceService = Depends(get_stance_service),
    business_record_repository: SqlAlchemyBusinessRecordRepository = Depends(get_business_record_repository),
    evidence_snapshot_repository: SqlAlchemyEvidenceSnapshotRepository = Depends(get_evidence_snapshot_repository),
    case_condition_service: CaseConditionService = Depends(get_case_condition_service),
    monitoring_result_repository: SqlAlchemyMonitoringResultRepository = Depends(get_monitoring_result_repository),
    decision_repository: DecisionRepository = Depends(get_decision_repository),
    observation_repository: ObservationRepository = Depends(get_observation_repository),
    monitoring_run_record_repository: SqlAlchemyMonitoringRunRecordRepository = Depends(get_monitoring_run_record_repository),
    ingestion_result_repository: SqlAlchemyIngestionResultRepository = Depends(get_ingestion_result_repository),
) -> MonitoringService:
    return MonitoringService(
        portfolio_store=portfolio_store,
        watchlist_store=watchlist_store,
        composition_service=composition_service,
        stance_service=stance_service,
        business_record_repository=business_record_repository,
        evidence_snapshot_repository=evidence_snapshot_repository,
        case_condition_service=case_condition_service,
        monitoring_result_repository=monitoring_result_repository,
        decision_repository=decision_repository,
        observation_repository=observation_repository,
        monitoring_run_record_repository=monitoring_run_record_repository,
        ingestion_result_repository=ingestion_result_repository,
    )
