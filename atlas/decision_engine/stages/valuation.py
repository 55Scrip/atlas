"""Valuation stage (`Doctrine` §5; Sprint 3).

Real, deterministic evaluator for exactly one structural fact:
execution-price-**history coverage**, built entirely from
`DecisionEngineInput.trade_log` — presence, count, and timestamps only.
No inference from the price level itself (whether a price was high,
low, good, or bad) is ever performed.

Substantive Valuation (`Doctrine` §5's own content — valuation thesis,
named assumptions, ranges, change triggers, intrinsic value, fair
value, multiples, upside/downside) is always `INSUFFICIENT_INPUT`
(`ValuationFinding`) — Sprint 3's own repository-discovery finding,
confirmed and locked by the sprint's own scope: `DecisionEngineInput`
carries no market price, financial-statement, multiple, or forecast
data, and nothing in it marks any Decision, Observation, or Evidence as
being *about* valuation specifically, so there is no honest,
non-NLP way to identify a "valuation thesis" among the undifferentiated
records. This module never parses free text to infer topic. It does
not, and structurally cannot, produce a cheap/expensive,
undervalued/overvalued, fair-value, intrinsic-value, buying-range,
target-price, margin-of-safety, expected-return, upside/downside, or
valuation-score conclusion — `ValuationFinding` has no field any of
those could occupy.
"""
from __future__ import annotations

from atlas.decision_engine.contracts import (
    DecisionEngineInput,
    EvaluationState,
    ExecutionPriceHistoryCoverage,
    ExecutionPriceHistoryFinding,
    ValuationFinding,
    ValuationNotAssessableReason,
    ValuationResult,
)

_SUBSTANTIVE_VALUATION_FINDING = ValuationFinding(
    state=EvaluationState.INSUFFICIENT_INPUT,
    reason=ValuationNotAssessableReason.NO_VALUATION_DATA_IN_INPUT,
)


def _execution_price_history(engine_input: DecisionEngineInput) -> ExecutionPriceHistoryFinding:
    entries = engine_input.trade_log
    if not entries:
        return ExecutionPriceHistoryFinding(
            coverage=ExecutionPriceHistoryCoverage.ABSENT,
            entry_count=0,
        )
    timestamps = tuple(entry.executed_at for entry in entries)
    return ExecutionPriceHistoryFinding(
        coverage=ExecutionPriceHistoryCoverage.PRESENT,
        entry_count=len(entries),
        earliest_executed_at=min(timestamps),
        latest_executed_at=max(timestamps),
    )


def evaluate_valuation(engine_input: DecisionEngineInput) -> ValuationResult:
    """Deterministic: identical `engine_input` always produces a deeply
    equal result. `min()`/`max()` over `executed_at` do not depend on
    `trade_log`'s original ordering. No timestamp, randomness, UUID
    generation, wall-clock access, global state, or side effect."""
    return ValuationResult(
        state=EvaluationState.EVALUATED,
        substantive_valuation=_SUBSTANTIVE_VALUATION_FINDING,
        execution_price_history=_execution_price_history(engine_input),
    )
