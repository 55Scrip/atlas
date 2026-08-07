"""Portfolio Intelligence stage tests (Sprint 4, Phase 5).

Mirrors the testing discipline established in
`test_business_evaluation_stage.py` and `test_valuation_evaluation_stage.py`.
No test name here implies a portfolio judgment (concentrated, diversified,
overweight, underweight) — per the locked scope, this evaluator reports
single-holding structural facts and trade-history coverage only, and
locks all seven DE-003 factors to `INSUFFICIENT_INPUT`.
"""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone

import pytest

from atlas.decision_engine.contracts import (
    DecisionEngineInput,
    EvaluationState,
    HoldingLinkage,
    MissingEvaluationCategory,
    PortfolioDataNotAvailableReason,
    PortfolioDoctrineFactor,
    PortfolioFinding,
    ReconciliationState,
)
from atlas.decision_engine.exceptions import DecisionEngineContractError
from atlas.decision_engine.pipeline import run_pipeline
from atlas.decision_engine.stages.portfolio_intelligence import (
    evaluate_portfolio_intelligence,
)
from tests.unit.decision_engine._fixtures import (
    CASE_ID,
    EVALUATED_AT,
    GENERATED_AT,
    build_portfolio_holding_context,
    build_trade_log_entry,
)


class TestNoLinkedHolding:
    def test_absent_linkage_carries_no_holding_field(self):
        engine_input = DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        result = evaluate_portfolio_intelligence(engine_input)
        holding = result.holding_context
        assert holding.linkage is HoldingLinkage.ABSENT
        assert holding.ticker is None
        assert holding.weight_percent is None
        assert holding.value_absolute is None
        assert holding.reconciliation_status is None


class TestLinkedHoldingPresent:
    def test_present_linkage_reports_ticker_and_weight_verbatim(self):
        holding = build_portfolio_holding_context(ticker="ASML", weight_percent=4.5)
        engine_input = DecisionEngineInput(
            case_id=CASE_ID, evaluated_at=EVALUATED_AT, portfolio_holding=holding
        )
        result = evaluate_portfolio_intelligence(engine_input)
        assert result.holding_context.linkage is HoldingLinkage.PRESENT
        assert result.holding_context.ticker == "ASML"
        assert result.holding_context.weight_percent == 4.5


class TestWeightPercentPresent:
    def test_weight_percent_reported_without_interpretation(self):
        """No matter how large the weight, the finding never labels it
        'high,' 'concentrated,' or 'overweight' — it is a bare float."""
        holding = build_portfolio_holding_context(weight_percent=45.0)
        engine_input = DecisionEngineInput(
            case_id=CASE_ID, evaluated_at=EVALUATED_AT, portfolio_holding=holding
        )
        result = evaluate_portfolio_intelligence(engine_input)
        assert result.holding_context.weight_percent == 45.0
        field_names = {f.name for f in dataclasses.fields(result.holding_context)}
        assert "concentration_level" not in field_names
        assert "is_concentrated" not in field_names
        assert "is_overweight" not in field_names


class TestValueAbsoluteAbsent:
    def test_value_absolute_none_when_not_supplied(self):
        holding = build_portfolio_holding_context(value_absolute=None)
        engine_input = DecisionEngineInput(
            case_id=CASE_ID, evaluated_at=EVALUATED_AT, portfolio_holding=holding
        )
        result = evaluate_portfolio_intelligence(engine_input)
        assert result.holding_context.value_absolute is None


class TestReconciliationStatusPresent:
    def test_reconciliation_status_reported_verbatim(self):
        holding = build_portfolio_holding_context(
            reconciliation_status=ReconciliationState.AWAITING_RECONCILIATION
        )
        engine_input = DecisionEngineInput(
            case_id=CASE_ID, evaluated_at=EVALUATED_AT, portfolio_holding=holding
        )
        result = evaluate_portfolio_intelligence(engine_input)
        assert (
            result.holding_context.reconciliation_status
            is ReconciliationState.AWAITING_RECONCILIATION
        )


class TestNoTradeHistory:
    def test_zero_trade_count_no_timestamp_bounds(self):
        engine_input = DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        result = evaluate_portfolio_intelligence(engine_input)
        assert result.holding_context.trade_count == 0
        assert result.holding_context.transaction_types == ()
        assert result.holding_context.earliest_executed_at is None
        assert result.holding_context.latest_executed_at is None


class TestOneTrade:
    def test_single_trade_count_and_matching_bounds(self):
        entry = build_trade_log_entry(transaction_type="BUY", executed_at=EVALUATED_AT)
        engine_input = DecisionEngineInput(
            case_id=CASE_ID, evaluated_at=EVALUATED_AT, trade_log=(entry,)
        )
        result = evaluate_portfolio_intelligence(engine_input)
        holding = result.holding_context
        assert holding.trade_count == 1
        assert holding.transaction_types == ("BUY",)
        assert holding.earliest_executed_at == EVALUATED_AT
        assert holding.latest_executed_at == EVALUATED_AT


class TestMultipleTrades:
    def test_multiple_trades_count_types_and_bounds(self):
        earliest = datetime(2026, 1, 1, tzinfo=timezone.utc)
        middle = datetime(2026, 4, 1, tzinfo=timezone.utc)
        latest = datetime(2026, 7, 1, tzinfo=timezone.utc)
        entries = (
            build_trade_log_entry(transaction_type="BUY", executed_at=middle),
            build_trade_log_entry(transaction_type="BUY", executed_at=earliest),
            build_trade_log_entry(transaction_type="SELL", executed_at=latest),
        )
        engine_input = DecisionEngineInput(
            case_id=CASE_ID, evaluated_at=EVALUATED_AT, trade_log=entries
        )
        result = evaluate_portfolio_intelligence(engine_input)
        holding = result.holding_context
        assert holding.trade_count == 3
        assert holding.transaction_types == ("BUY", "SELL")
        assert holding.earliest_executed_at == earliest
        assert holding.latest_executed_at == latest


class TestDeterministicOrdering:
    def test_bounds_and_transaction_types_independent_of_input_order(self):
        earliest = datetime(2026, 1, 1, tzinfo=timezone.utc)
        latest = datetime(2026, 7, 1, tzinfo=timezone.utc)
        forward = (
            build_trade_log_entry(transaction_type="SELL", executed_at=earliest),
            build_trade_log_entry(transaction_type="BUY", executed_at=latest),
        )
        reversed_order = tuple(reversed(forward))

        result_forward = evaluate_portfolio_intelligence(
            DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT, trade_log=forward)
        )
        result_reversed = evaluate_portfolio_intelligence(
            DecisionEngineInput(
                case_id=CASE_ID, evaluated_at=EVALUATED_AT, trade_log=reversed_order
            )
        )
        assert (
            result_forward.holding_context.transaction_types
            == result_reversed.holding_context.transaction_types
            == ("BUY", "SELL")
        )
        assert (
            result_forward.holding_context.earliest_executed_at
            == result_reversed.holding_context.earliest_executed_at
            == earliest
        )
        assert (
            result_forward.holding_context.latest_executed_at
            == result_reversed.holding_context.latest_executed_at
            == latest
        )


class TestPortfolioFindingAlwaysInsufficientInputForSevenFactors:
    def test_locked_regardless_of_holding_or_trade_presence(self):
        no_data = evaluate_portfolio_intelligence(
            DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        )
        with_data = evaluate_portfolio_intelligence(
            DecisionEngineInput(
                case_id=CASE_ID,
                evaluated_at=EVALUATED_AT,
                portfolio_holding=build_portfolio_holding_context(),
                trade_log=(build_trade_log_entry(),),
            )
        )
        for result in (no_data, with_data):
            assert result.portfolio_factors.state is EvaluationState.INSUFFICIENT_INPUT
            assert set(result.portfolio_factors.factors) == set(PortfolioDoctrineFactor)

    def test_all_seven_doctrine_factors_are_named(self):
        result = evaluate_portfolio_intelligence(
            DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        )
        factor_values = {f.value for f in result.portfolio_factors.factors}
        assert factor_values == {
            "allocation",
            "concentration",
            "diversification",
            "correlation",
            "opportunity_cost",
            "existing_thesis",
            "previous_decisions",
        }

    def test_constructing_a_partial_factor_list_is_forbidden(self):
        with pytest.raises(DecisionEngineContractError):
            PortfolioFinding(
                state=EvaluationState.INSUFFICIENT_INPUT,
                reason=PortfolioDataNotAvailableReason.NO_PORTFOLIO_WIDE_DATA_IN_INPUT,
                factors=(PortfolioDoctrineFactor.ALLOCATION,),
            )

    def test_constructing_any_other_state_is_forbidden(self):
        with pytest.raises(DecisionEngineContractError):
            PortfolioFinding(
                state=EvaluationState.EVALUATED,
                reason=PortfolioDataNotAvailableReason.NO_PORTFOLIO_WIDE_DATA_IN_INPUT,
                factors=tuple(PortfolioDoctrineFactor),
            )


class TestNoJudgmentIsProducedAnywhere:
    def test_no_concentration_diversification_or_risk_judgment_field(self):
        result = evaluate_portfolio_intelligence(
            DecisionEngineInput(
                case_id=CASE_ID,
                evaluated_at=EVALUATED_AT,
                portfolio_holding=build_portfolio_holding_context(weight_percent=60.0),
            )
        )
        all_field_names: set[str] = set()
        for obj in (result, result.holding_context, result.portfolio_factors):
            all_field_names |= {f.name for f in dataclasses.fields(obj)}
        prohibited = {
            "concentration_level",
            "diversification_score",
            "risk_level",
            "is_diversified",
            "is_concentrated",
            "overweight",
            "underweight",
        }
        assert all_field_names.isdisjoint(prohibited)

    def test_no_portfolio_fit_score_or_numeric_score_field(self):
        result = evaluate_portfolio_intelligence(
            DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        )
        all_field_names: set[str] = set()
        for obj in (result, result.holding_context, result.portfolio_factors):
            all_field_names |= {f.name for f in dataclasses.fields(obj)}
        prohibited = {"fit_score", "score", "percentage", "probability"}
        assert all_field_names.isdisjoint(prohibited)


class TestPortfolioIntelligenceResultBecomesEvaluated:
    def test_state_is_evaluated_even_with_no_holding_or_trades(self):
        result = evaluate_portfolio_intelligence(
            DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        )
        assert result.state is EvaluationState.EVALUATED
        assert result.reason is None


class TestPipelineIntegration:
    def test_reasoning_is_evaluated_with_empty_blocked_by(self):
        """Sprint 5: Reasoning is now real too, assembling from all
        three upstream results — `EVALUATED`, `blocked_by` empty."""
        output = run_pipeline(
            DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT),
            generated_at=GENERATED_AT,
        )
        assert output.portfolio_intelligence.state is EvaluationState.EVALUATED
        assert output.reasoning.state is EvaluationState.EVALUATED
        assert output.reasoning.blocked_by == ()

    def test_recommendation_withheld_remains_final(self):
        output = run_pipeline(
            DecisionEngineInput(
                case_id=CASE_ID,
                evaluated_at=EVALUATED_AT,
                portfolio_holding=build_portfolio_holding_context(),
                trade_log=(build_trade_log_entry(),),
            ),
            generated_at=GENERATED_AT,
        )
        assert output.recommendation.kind.value == "recommendation_withheld"

    def test_no_direction_is_produced(self):
        output = run_pipeline(
            DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT),
            generated_at=GENERATED_AT,
        )
        assert not hasattr(output.recommendation, "direction")

    def test_no_conviction_is_produced(self):
        output = run_pipeline(
            DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT),
            generated_at=GENERATED_AT,
        )
        assert not hasattr(output.recommendation, "conviction")
        assert not hasattr(output.recommendation, "conviction_level")

    def test_missing_evaluations_is_now_empty(self):
        """Sprint 5: all four stages are `EVALUATED`."""
        output = run_pipeline(
            DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT),
            generated_at=GENERATED_AT,
        )
        assert MissingEvaluationCategory.PORTFOLIO_INTELLIGENCE not in (
            output.recommendation.missing_evaluations
        )
        assert output.recommendation.missing_evaluations == ()


class TestPipelineDeterminism:
    def test_identical_input_produces_deeply_equal_output(self):
        holding = build_portfolio_holding_context()
        entry = build_trade_log_entry()
        engine_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            portfolio_holding=holding,
            trade_log=(entry,),
        )
        same_data_new_instance = dataclasses.replace(engine_input)
        first = run_pipeline(engine_input, generated_at=GENERATED_AT)
        second = run_pipeline(same_data_new_instance, generated_at=GENERATED_AT)
        assert first == second
