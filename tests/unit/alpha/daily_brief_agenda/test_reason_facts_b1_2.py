"""Implementation Sprint B1.2 (Engine Reason Localization Contract) --
the 9 additional sources converted this sprint, each exposing an
already-real closed-enum transition on its own `*Change` dataclass as
a `ReasonFact`. Mirrors `test_reason_facts.py`'s own B1.1 style;
`_item_for_ticker`/`build_agenda` are not re-tested here.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.daily_brief_agenda.engine import (
    change_intelligence_signal,
    decision_path_signal,
    decision_readiness_signal,
    decision_reliability_signal,
    investment_decision_signal,
    monitoring_signal,
    portfolio_decision_signal,
    portfolio_fit_signal,
    recommendation_conviction_signal,
)
from atlas.alpha.daily_brief_agenda.reason_facts import ReasonCode, ReasonFact
from atlas.alpha.decision_path.models import FinalReachableState
from atlas.alpha.decision_readiness.models import DecisionReadinessStatus
from atlas.alpha.decision_reliability.models import ReliabilityLevel
from atlas.alpha.investment_decision.models import DecisionAction, DecisionQualifierKind
from atlas.alpha.monitoring.models import MonitoringChangeCategory, MonitoringMateriality
from atlas.alpha.portfolio_decision.models import PortfolioDecisionCategory
from atlas.alpha.portfolio_fit.models import FitRating, FitTrend, FitVerdictReasonCode
from atlas.alpha.recommendation_conviction.models import ConvictionStrength, RecommendationStability
from atlas.analysis_engine.investment_case_change import ThesisImpact

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


class TestChangeIntelligenceSignal:
    def test_carries_thesis_impact_fact_with_ticker(self):
        signal = change_intelligence_signal(ThesisImpact.WEAKENED, "AAPL: raw reason", ticker="AAPL")
        assert signal.fact == ReasonFact(ReasonCode.CHANGE_INTELLIGENCE_THESIS_IMPACT, "AAPL", value="weakened", count=None)

    def test_carries_affected_finding_count_on_the_fact_too(self):
        signal = change_intelligence_signal(ThesisImpact.WEAKENED, "AAPL: raw reason", affected_finding_count=3, ticker="AAPL")
        assert signal.fact is not None
        assert signal.fact.count == 3

    def test_zero_affected_finding_count_is_none_not_zero(self):
        signal = change_intelligence_signal(ThesisImpact.STRENGTHENED, "AAPL: raw reason", affected_finding_count=0, ticker="AAPL")
        assert signal.fact is not None
        assert signal.fact.count is None


class TestPortfolioFitSignal:
    def test_carries_fact_through_to_signal(self):
        fact = ReasonFact(ReasonCode.PORTFOLIO_FIT_VERDICT, "AAPL", value=FitVerdictReasonCode.RISK_GATE.value)
        signal = portfolio_fit_signal(FitRating.POOR, FitTrend.UNAVAILABLE, True, "AAPL: raw reason", fact=fact)
        assert signal is not None
        assert signal.fact is fact

    def test_defaults_to_no_fact(self):
        signal = portfolio_fit_signal(FitRating.POOR, FitTrend.UNAVAILABLE, True, "AAPL: raw reason")
        assert signal is not None
        assert signal.fact is None


class TestMonitoringSignal:
    def test_builds_fact_from_its_own_category_parameter(self):
        signal = monitoring_signal(
            MonitoringChangeCategory.STANCE_WEAKENED, MonitoringMateriality.MATERIAL, True, "AAPL: raw reason", ticker="AAPL"
        )
        assert signal is not None
        assert signal.fact == ReasonFact(ReasonCode.MONITORING_CHANGE, "AAPL", value="stance_weakened")

    def test_minor_materiality_still_returns_none_signal_unaffected_by_fact_change(self):
        signal = monitoring_signal(
            MonitoringChangeCategory.STANCE_WEAKENED, MonitoringMateriality.MINOR, True, "AAPL: raw reason", ticker="AAPL"
        )
        assert signal is None

    def test_excluded_category_still_returns_none(self):
        signal = monitoring_signal(
            MonitoringChangeCategory.CASE_CONDITION_TRIGGERED, MonitoringMateriality.MATERIAL, True, "AAPL: raw reason", ticker="AAPL"
        )
        assert signal is None

    def test_falls_back_to_generic_entity_label_when_no_ticker(self):
        signal = monitoring_signal(MonitoringChangeCategory.COVERAGE_IMPROVED, MonitoringMateriality.MATERIAL, False, "raw reason")
        assert signal is not None
        assert signal.fact is not None
        assert signal.fact.entity == "this company"


class TestDecisionReadinessSignal:
    def test_builds_transition_fact_when_previous_status_given(self):
        signal = decision_readiness_signal(
            DecisionReadinessStatus.READY, "AAPL: raw reason", previous_status=DecisionReadinessStatus.WAITING, ticker="AAPL"
        )
        assert signal.fact == ReasonFact(ReasonCode.DECISION_READINESS_TRANSITION, "AAPL", value="ready", secondary_value="waiting")

    def test_no_fact_without_previous_status(self):
        signal = decision_readiness_signal(DecisionReadinessStatus.READY, "AAPL: raw reason", ticker="AAPL")
        assert signal.fact is None


class TestInvestmentDecisionSignal:
    def test_builds_transition_fact_on_real_action_change(self):
        signal = investment_decision_signal(
            DecisionAction.ADD, (), "AAPL: raw reason", previous_action=DecisionAction.HOLD, ticker="AAPL"
        )
        assert signal.fact == ReasonFact(ReasonCode.INVESTMENT_DECISION_TRANSITION, "AAPL", value="add", secondary_value="hold")

    def test_no_fact_when_only_qualifiers_changed_not_the_action(self):
        signal = investment_decision_signal(
            DecisionAction.HOLD,
            (DecisionQualifierKind.DECISION_BLOCKED,),
            "AAPL: raw reason",
            previous_action=DecisionAction.HOLD,
            ticker="AAPL",
        )
        assert signal.fact is None


class TestRecommendationConvictionSignal:
    def test_builds_transition_fact_on_real_strength_change(self):
        signal = recommendation_conviction_signal(
            RecommendationStability.STABLE,
            "AAPL: raw reason",
            current_strength=ConvictionStrength.STRONG,
            previous_strength=ConvictionStrength.WEAK,
            ticker="AAPL",
        )
        assert signal.fact == ReasonFact(
            ReasonCode.RECOMMENDATION_CONVICTION_TRANSITION, "AAPL", value="strong", secondary_value="weak"
        )

    def test_no_fact_when_strength_unchanged(self):
        signal = recommendation_conviction_signal(
            RecommendationStability.OPERATIONALLY_BLOCKED,
            "AAPL: raw reason",
            current_strength=ConvictionStrength.STRONG,
            previous_strength=ConvictionStrength.STRONG,
            ticker="AAPL",
        )
        assert signal.fact is None


class TestDecisionPathSignal:
    def test_builds_transition_fact(self):
        signal = decision_path_signal(
            FinalReachableState.FULLY_REACHABLE,
            "AAPL: raw reason",
            previous_final_reachable_state=FinalReachableState.PARTIALLY_REACHABLE,
            ticker="AAPL",
        )
        assert signal.fact == ReasonFact(
            ReasonCode.DECISION_PATH_TRANSITION, "AAPL", value="fully_reachable", secondary_value="partially_reachable"
        )


class TestDecisionReliabilitySignal:
    def test_builds_transition_fact_when_level_given(self):
        signal = decision_reliability_signal(
            "AAPL: raw reason", current_level=ReliabilityLevel.HIGH, previous_level=ReliabilityLevel.MODERATE, ticker="AAPL"
        )
        assert signal.fact == ReasonFact(ReasonCode.DECISION_RELIABILITY_TRANSITION, "AAPL", value="high", secondary_value="moderate")

    def test_no_fact_without_level(self):
        signal = decision_reliability_signal("AAPL: raw reason", ticker="AAPL")
        assert signal.fact is None


class TestPortfolioDecisionSignal:
    def test_builds_transition_fact_on_real_category_change(self):
        signal = portfolio_decision_signal(
            "AAPL: raw reason",
            current_category=PortfolioDecisionCategory.CONFLICTS_WITH_PORTFOLIO,
            previous_category=PortfolioDecisionCategory.NEUTRAL,
            ticker="AAPL",
        )
        assert signal.fact == ReasonFact(
            ReasonCode.PORTFOLIO_DECISION_TRANSITION, "AAPL", value="conflicts_with_portfolio", secondary_value="neutral"
        )

    def test_no_fact_when_category_unchanged(self):
        signal = portfolio_decision_signal(
            "AAPL: raw reason",
            current_category=PortfolioDecisionCategory.NEUTRAL,
            previous_category=PortfolioDecisionCategory.NEUTRAL,
            ticker="AAPL",
        )
        assert signal.fact is None
