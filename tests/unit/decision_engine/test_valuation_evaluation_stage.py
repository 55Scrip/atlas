"""Valuation stage tests (Sprint 3, Phase 5).

Mirrors the testing discipline established in
`test_business_evaluation_stage.py`. No test name here implies a
valuation judgment (cheap/expensive, undervalued/overvalued) — per the
locked scope, this evaluator produces execution-price-**history
coverage** only, never a conclusion about the price level itself.
"""
from __future__ import annotations

import dataclasses
import inspect
from datetime import datetime, timezone

import pytest

from atlas.decision_engine.contracts import (
    DecisionEngineInput,
    EvaluationState,
    ExecutionPriceHistoryCoverage,
    ValuationFinding,
    ValuationNotAssessableReason,
)
from atlas.decision_engine.exceptions import DecisionEngineContractError
from atlas.decision_engine.pipeline import run_pipeline
from atlas.decision_engine.stages import valuation as valuation_module
from atlas.decision_engine.stages.valuation import evaluate_valuation
from tests.unit.decision_engine._fixtures import (
    CASE_ID,
    EVALUATED_AT,
    GENERATED_AT,
    build_decision,
    build_evidence,
    build_observation,
    build_trade_log_entry,
)


class TestNoTradeHistory:
    def test_absent_coverage_with_zero_entries(self):
        engine_input = DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        result = evaluate_valuation(engine_input)
        history = result.execution_price_history
        assert history.coverage is ExecutionPriceHistoryCoverage.ABSENT
        assert history.entry_count == 0
        assert history.earliest_executed_at is None
        assert history.latest_executed_at is None


class TestOneExecutionPriceRecord:
    def test_present_coverage_with_one_entry_and_matching_bounds(self):
        entry = build_trade_log_entry(executed_at=EVALUATED_AT)
        engine_input = DecisionEngineInput(
            case_id=CASE_ID, evaluated_at=EVALUATED_AT, trade_log=(entry,)
        )
        result = evaluate_valuation(engine_input)
        history = result.execution_price_history
        assert history.coverage is ExecutionPriceHistoryCoverage.PRESENT
        assert history.entry_count == 1
        assert history.earliest_executed_at == EVALUATED_AT
        assert history.latest_executed_at == EVALUATED_AT


class TestMultipleExecutionPriceRecords:
    def test_entry_count_and_bounds_reflect_all_records(self):
        earliest = datetime(2026, 1, 1, tzinfo=timezone.utc)
        middle = datetime(2026, 4, 1, tzinfo=timezone.utc)
        latest = datetime(2026, 7, 1, tzinfo=timezone.utc)
        entries = (
            build_trade_log_entry(executed_at=middle),
            build_trade_log_entry(executed_at=earliest),
            build_trade_log_entry(executed_at=latest),
        )
        engine_input = DecisionEngineInput(
            case_id=CASE_ID, evaluated_at=EVALUATED_AT, trade_log=entries
        )
        result = evaluate_valuation(engine_input)
        history = result.execution_price_history
        assert history.coverage is ExecutionPriceHistoryCoverage.PRESENT
        assert history.entry_count == 3
        assert history.earliest_executed_at == earliest
        assert history.latest_executed_at == latest


class TestDeterministicOrdering:
    def test_bounds_are_independent_of_input_tuple_order(self):
        """`min()`/`max()` over `executed_at`, not reliance on the
        tuple's original order — confirmed by feeding the same three
        entries in two different orders and requiring identical bounds."""
        earliest = datetime(2026, 1, 1, tzinfo=timezone.utc)
        middle = datetime(2026, 4, 1, tzinfo=timezone.utc)
        latest = datetime(2026, 7, 1, tzinfo=timezone.utc)
        forward = (
            build_trade_log_entry(executed_at=earliest),
            build_trade_log_entry(executed_at=middle),
            build_trade_log_entry(executed_at=latest),
        )
        reversed_order = tuple(reversed(forward))

        result_forward = evaluate_valuation(
            DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT, trade_log=forward)
        )
        result_reversed = evaluate_valuation(
            DecisionEngineInput(
                case_id=CASE_ID, evaluated_at=EVALUATED_AT, trade_log=reversed_order
            )
        )
        assert (
            result_forward.execution_price_history.earliest_executed_at
            == result_reversed.execution_price_history.earliest_executed_at
            == earliest
        )
        assert (
            result_forward.execution_price_history.latest_executed_at
            == result_reversed.execution_price_history.latest_executed_at
            == latest
        )


class TestSubstantiveValuationAlwaysInsufficientInput:
    def test_locked_regardless_of_trade_history_presence(self):
        """Substantive Valuation (Doctrine §5's own content) is always
        `INSUFFICIENT_INPUT` this sprint, whether or not execution-price
        history exists — the two findings are independent."""
        no_history = evaluate_valuation(
            DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        )
        with_history = evaluate_valuation(
            DecisionEngineInput(
                case_id=CASE_ID,
                evaluated_at=EVALUATED_AT,
                trade_log=(build_trade_log_entry(),),
            )
        )
        for result in (no_history, with_history):
            assert result.substantive_valuation == ValuationFinding(
                state=EvaluationState.INSUFFICIENT_INPUT,
                reason=ValuationNotAssessableReason.NO_VALUATION_DATA_IN_INPUT,
            )

    def test_constructing_any_other_state_is_forbidden(self):
        with pytest.raises(DecisionEngineContractError):
            ValuationFinding(
                state=EvaluationState.EVALUATED,
                reason=ValuationNotAssessableReason.NO_VALUATION_DATA_IN_INPUT,
            )


class TestNoSemanticParsingOfFreeText:
    def test_evaluator_never_reads_decision_or_observation_statement_text(self):
        """`evaluate_valuation` only ever reads `trade_log` — confirmed
        by proving a `DecisionEngineInput` with rich Decision/Observation/
        Evidence free text but zero `trade_log` entries still yields
        `ABSENT` coverage: the presence of prose elsewhere in the input
        has no effect on the result."""
        decision = build_decision()
        observation = build_observation()
        evidence = build_evidence(observation=observation)
        engine_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            decisions=(decision,),
            observations=(observation,),
            evidence=(evidence,),
        )
        result = evaluate_valuation(engine_input)
        assert result.execution_price_history.coverage is ExecutionPriceHistoryCoverage.ABSENT
        assert result.execution_price_history.entry_count == 0

    def test_valuation_module_source_contains_no_statement_field_access(self):
        """Static confirmation, not just behavioral: the stage module's
        own source never references `.statement`, `.reason`, or
        `investment_case` — the free-text fields it must never parse."""
        source = inspect.getsource(valuation_module)
        assert ".statement" not in source
        assert ".reason" not in source
        assert "investment_case" not in source


class TestNoNumericValuationScore:
    def test_no_score_or_percentage_field_anywhere_on_the_result(self):
        result = evaluate_valuation(
            DecisionEngineInput(
                case_id=CASE_ID,
                evaluated_at=EVALUATED_AT,
                trade_log=(build_trade_log_entry(),),
            )
        )
        result_fields = {f.name for f in dataclasses.fields(result)}
        history_fields = {f.name for f in dataclasses.fields(result.execution_price_history)}
        finding_fields = {f.name for f in dataclasses.fields(result.substantive_valuation)}
        forbidden = {"score", "percentage", "probability", "valuation_score"}
        assert result_fields.isdisjoint(forbidden)
        assert history_fields.isdisjoint(forbidden)
        assert finding_fields.isdisjoint(forbidden)


class TestNoValuationJudgment:
    def test_no_field_named_after_a_prohibited_conclusion(self):
        result = evaluate_valuation(
            DecisionEngineInput(
                case_id=CASE_ID,
                evaluated_at=EVALUATED_AT,
                trade_log=(build_trade_log_entry(),),
            )
        )
        all_field_names: set[str] = set()
        for obj in (result, result.execution_price_history, result.substantive_valuation):
            all_field_names |= {f.name for f in dataclasses.fields(obj)}
        prohibited = {
            "cheap",
            "expensive",
            "undervalued",
            "overvalued",
            "fair_value",
            "intrinsic_value",
            "buying_range",
            "target_price",
            "margin_of_safety",
            "expected_return",
            "upside",
            "downside",
        }
        assert all_field_names.isdisjoint(prohibited)


class TestValuationResultBecomesEvaluated:
    def test_state_is_evaluated_even_with_no_trade_history(self):
        result = evaluate_valuation(
            DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        )
        assert result.state is EvaluationState.EVALUATED
        assert result.reason is None


class TestPipelineIntegration:
    def test_reasoning_not_evaluated_pending_its_own_evaluator(self):
        """Sprint 4: Portfolio Intelligence is now `EVALUATED` too, so no
        upstream stage blocks Reasoning any more."""
        output = run_pipeline(
            DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT),
            generated_at=GENERATED_AT,
        )
        assert output.valuation.state is EvaluationState.EVALUATED
        blocked_by_values = {b.value for b in output.reasoning.blocked_by}
        assert blocked_by_values == {"reasoning_evaluator_not_implemented"}

    def test_recommendation_withheld_remains_final(self):
        output = run_pipeline(
            DecisionEngineInput(
                case_id=CASE_ID,
                evaluated_at=EVALUATED_AT,
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


class TestPipelineDeterminism:
    def test_identical_input_produces_deeply_equal_output(self):
        entry = build_trade_log_entry()
        engine_input = DecisionEngineInput(
            case_id=CASE_ID, evaluated_at=EVALUATED_AT, trade_log=(entry,)
        )
        same_data_new_instance = dataclasses.replace(engine_input)
        first = run_pipeline(engine_input, generated_at=GENERATED_AT)
        second = run_pipeline(same_data_new_instance, generated_at=GENERATED_AT)
        assert first == second
