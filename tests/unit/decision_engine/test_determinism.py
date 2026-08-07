"""Determinism tests for `atlas.decision_engine.pipeline.run_pipeline`
(Sprint Phase 6 and Phase 8)."""
from __future__ import annotations

import dataclasses

from atlas.decision_engine.pipeline import run_pipeline
from tests.unit.decision_engine._fixtures import (
    GENERATED_AT,
    build_minimal_input,
    build_populated_input,
)


class TestIdenticalInputProducesDeeplyEqualOutput:
    def test_minimal_input_is_deterministic(self):
        first = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        second = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        assert first == second

    def test_populated_input_is_deterministic(self):
        """Two independently-built but field-for-field identical inputs
        (fresh Decision/Outcome/Observation/Evidence objects each time,
        same fixed clock) must still produce a deeply equal output —
        this is the real test of determinism, not just re-running the
        same Python object through the pipeline twice."""
        first = run_pipeline(build_populated_input(), generated_at=GENERATED_AT)
        second = run_pipeline(build_populated_input(), generated_at=GENERATED_AT)
        assert first == second


class TestInputIsNotMutated:
    def test_engine_input_is_unchanged_after_a_run(self):
        engine_input = build_populated_input()
        before = dataclasses.replace(engine_input)
        run_pipeline(engine_input, generated_at=GENERATED_AT)
        assert engine_input == before

    def test_engine_input_fields_are_still_the_same_objects(self):
        """Frozen dataclasses already forbid reassignment, but this
        confirms no stage replaces a tuple field's contents in place
        via `object.__setattr__` or similar."""
        engine_input = build_populated_input()
        decisions_before = engine_input.decisions
        run_pipeline(engine_input, generated_at=GENERATED_AT)
        assert engine_input.decisions is decisions_before


class TestOrderingIsStable:
    def test_missing_evaluations_ordering_is_stable_across_runs(self):
        first = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        second = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        assert (
            first.recommendation.missing_evaluations
            == second.recommendation.missing_evaluations
        )

    def test_reasoning_blocked_by_ordering_is_stable_across_runs(self):
        first = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        second = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        assert first.reasoning.blocked_by == second.reasoning.blocked_by
