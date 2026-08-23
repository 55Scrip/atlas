"""Composition wiring for the Daily Brief Agenda API.

Reuses every sibling package's own existing provider directly -- no new
repository, no new table. Mirrors `atlas.alpha.portfolio_fit.api
.dependencies`'s own "each Alpha package wires its dependencies for
itself" convention.
"""
from __future__ import annotations

from fastapi import Depends

from atlas.alpha.daily_brief.api.dependencies import get_daily_brief_service
from atlas.alpha.daily_brief.service import DailyBriefService
from atlas.alpha.daily_brief_agenda.service import DailyBriefAgendaService
from atlas.alpha.decision_explanation.api.dependencies import get_decision_explanation_service
from atlas.alpha.decision_explanation.service import DecisionExplanationService
from atlas.alpha.decision_reliability.api.dependencies import get_decision_reliability_service
from atlas.alpha.decision_reliability.service import DecisionReliabilityService
from atlas.alpha.portfolio_decision.api.dependencies import get_portfolio_decision_service
from atlas.alpha.portfolio_decision.service import PortfolioDecisionService
from atlas.alpha.decision_memory.api.dependencies import get_decision_memory_service
from atlas.alpha.decision_memory.service import DecisionMemoryService
from atlas.alpha.decision_path.api.dependencies import get_decision_path_service
from atlas.alpha.decision_path.service import DecisionPathService
from atlas.alpha.decision_readiness.api.dependencies import get_decision_readiness_service
from atlas.alpha.opportunity_cost.api.dependencies import get_opportunity_cost_service
from atlas.alpha.opportunity_cost.service import OpportunityCostService
from atlas.alpha.decision_readiness.service import DecisionReadinessService
from atlas.alpha.evidence_graph.api.dependencies import get_evidence_graph_service
from atlas.alpha.evidence_graph.service import EvidenceGraphService
from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.investment_decision.api.dependencies import get_investment_decision_service
from atlas.alpha.investment_decision.service import InvestmentDecisionService
from atlas.alpha.monitoring.api.dependencies import get_monitoring_service
from atlas.alpha.recommendation_conviction.api.dependencies import get_recommendation_conviction_service
from atlas.alpha.recommendation_conviction.service import RecommendationConvictionService
from atlas.alpha.monitoring.service import MonitoringService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio_fit.api.dependencies import get_portfolio_fit_service
from atlas.alpha.portfolio_fit.service import PortfolioFitService
from atlas.alpha.portfolio_intelligence.api.dependencies import get_portfolio_intelligence_service
from atlas.alpha.portfolio_intelligence.service import PortfolioIntelligenceService
from atlas.alpha.portfolio_status.api.dependencies import get_portfolio_status_service
from atlas.alpha.portfolio_status.service import PortfolioStatusService
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.core.application.assumption.assumption_service import AssumptionService
from atlas.core.application.case_condition.case_condition_service import CaseConditionService
from atlas.core.infrastructure.api.assumption.dependencies import get_assumption_service
from atlas.core.infrastructure.api.case_condition.dependencies import get_case_condition_service

__all__ = ["get_daily_brief_agenda_service"]


def get_daily_brief_agenda_service(
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
    daily_brief_service: DailyBriefService = Depends(get_daily_brief_service),
    portfolio_fit_service: PortfolioFitService = Depends(get_portfolio_fit_service),
    portfolio_status_service: PortfolioStatusService = Depends(get_portfolio_status_service),
    portfolio_intelligence_service: PortfolioIntelligenceService = Depends(get_portfolio_intelligence_service),
    case_condition_service: CaseConditionService = Depends(get_case_condition_service),
    assumption_service: AssumptionService = Depends(get_assumption_service),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    evidence_graph_service: EvidenceGraphService = Depends(get_evidence_graph_service),
    decision_readiness_service: DecisionReadinessService = Depends(get_decision_readiness_service),
    investment_decision_service: InvestmentDecisionService = Depends(get_investment_decision_service),
    recommendation_conviction_service: RecommendationConvictionService = Depends(get_recommendation_conviction_service),
    decision_path_service: DecisionPathService = Depends(get_decision_path_service),
    opportunity_cost_service: OpportunityCostService = Depends(get_opportunity_cost_service),
    decision_memory_service: DecisionMemoryService = Depends(get_decision_memory_service),
    decision_explanation_service: DecisionExplanationService = Depends(get_decision_explanation_service),
    decision_reliability_service: DecisionReliabilityService = Depends(get_decision_reliability_service),
    portfolio_decision_service: PortfolioDecisionService = Depends(get_portfolio_decision_service),
    composition_service: InvestmentCaseCompositionService = Depends(get_investment_case_composition_service),
) -> DailyBriefAgendaService:
    return DailyBriefAgendaService(
        portfolio_store=portfolio_store,
        watchlist_store=watchlist_store,
        daily_brief_service=daily_brief_service,
        portfolio_fit_service=portfolio_fit_service,
        portfolio_status_service=portfolio_status_service,
        portfolio_intelligence_service=portfolio_intelligence_service,
        case_condition_service=case_condition_service,
        assumption_service=assumption_service,
        monitoring_service=monitoring_service,
        evidence_graph_service=evidence_graph_service,
        decision_readiness_service=decision_readiness_service,
        investment_decision_service=investment_decision_service,
        recommendation_conviction_service=recommendation_conviction_service,
        decision_path_service=decision_path_service,
        opportunity_cost_service=opportunity_cost_service,
        decision_memory_service=decision_memory_service,
        decision_explanation_service=decision_explanation_service,
        decision_reliability_service=decision_reliability_service,
        portfolio_decision_service=portfolio_decision_service,
        composition_service=composition_service,
    )
