"""Shared test fixtures for the Analysis Engine test suite.

Reuses `tests.unit.decision_engine._fixtures`'s real Core Domain Object
builders rather than re-deriving them -- `atlas.analysis_engine` is
built entirely on top of `atlas.decision_engine`'s own output, so these
tests exercise the same `DecisionEngineInput` shapes that package's own
suite already validates, then run them through the real
`atlas.decision_engine.pipeline.run_pipeline` to get a real
`DecisionEngineOutput` to assemble analysis from -- never a hand-built
fake `DecisionEngineOutput`.
"""
from __future__ import annotations

from atlas.decision_engine.contracts import DecisionEngineInput, DecisionEngineOutput
from atlas.decision_engine.pipeline import run_pipeline
from tests.unit.decision_engine._fixtures import (  # noqa: F401
    CASE_ID,
    EVALUATED_AT,
    GENERATED_AT,
    build_decision,
    build_evidence,
    build_minimal_input,
    build_observation,
    build_outcome,
    build_populated_input,
)


def run_minimal(*, case_id=CASE_ID) -> tuple[DecisionEngineInput, DecisionEngineOutput]:
    engine_input = build_minimal_input(case_id=case_id)
    return engine_input, run_pipeline(engine_input, generated_at=GENERATED_AT)


def run_populated(*, case_id=CASE_ID) -> tuple[DecisionEngineInput, DecisionEngineOutput]:
    engine_input = build_populated_input(case_id=case_id)
    return engine_input, run_pipeline(engine_input, generated_at=GENERATED_AT)
