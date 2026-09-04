"""Proof that EvidenceCoverage reaches Conviction from REAL observations.

Every existing coverage test hands `calculate_recommendation_conviction`
an `EvidenceCoverageLevel` value directly. None of them creates an
Observation. So the chain that *derives* the level --

    Observation/Evidence -> `business_evaluation._coverage()` -> coverage
    -> `calculate_recommendation_conviction` -> RecommendationConviction

-- was unverified end to end: PARTIAL and FULL were reachable only by a
test asserting them into existence. Replacing the `_coverage()` call
with a hardcoded `NOT_APPLICABLE` would have left the suite green,
because nothing connected real observations to the calculator's input.

These build real `Observation`/`Evidence` domain objects, run the real
`run_pipeline`, and then observe what production actually hands the
calculator during a real `assemble_analysis` -- so both halves of the
chain, and the wiring between them, are under test.

The spy is deliberately installed on
`atlas.analysis_engine.recommendation`'s own module-level name, because
that is the binding `evaluate_recommendation_gate` calls through.
Patching the definition module would silently do nothing.
"""
from __future__ import annotations

import pytest

from atlas.analysis_engine import recommendation as recommendation_module
from atlas.analysis_engine.pipeline import assemble_analysis
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.evidence.value_objects import Direction
from atlas.decision_engine.contracts import DecisionEngineInput, EvidenceCoverageLevel
from atlas.decision_engine.pipeline import run_pipeline
from tests.unit.analysis_engine._fixtures import (
    EVALUATED_AT,
    GENERATED_AT,
    build_evidence,
    build_observation,
)


def _engine_input(observations: int, with_evidence: int, direction: Direction):
    """Exactly the shape `_coverage()` reads: it counts observations, and
    counts observations carrying any evidence."""
    case_id = CaseId()
    made = tuple(build_observation(case_id=case_id) for _ in range(observations))
    evidence = tuple(
        build_evidence(observation=observation, direction=direction)
        for observation in made[:with_evidence]
    )
    return DecisionEngineInput(
        case_id=case_id, evaluated_at=EVALUATED_AT,
        observations=made, evidence=evidence)


def _derived_coverage(observations: int, with_evidence: int,
                      direction: Direction = Direction.SUPPORTS) -> EvidenceCoverageLevel:
    """The level the real Decision Engine derives -- never asserted in."""
    engine_input = _engine_input(observations, with_evidence, direction)
    output = run_pipeline(engine_input, generated_at=GENERATED_AT)
    return output.business_evaluation.evidence_quality.coverage


def _conviction_call(monkeypatch, observations: int, with_evidence: int,
                     direction: Direction = Direction.SUPPORTS):
    """Run the real `assemble_analysis` and capture what it passed to
    `calculate_recommendation_conviction`, plus what came back."""
    engine_input = _engine_input(observations, with_evidence, direction)
    output = run_pipeline(engine_input, generated_at=GENERATED_AT)
    real = recommendation_module.calculate_recommendation_conviction
    captured = {}

    def spy(**kwargs):
        result = real(**kwargs)
        captured["kwargs"], captured["result"] = kwargs, result
        return result

    monkeypatch.setattr(
        recommendation_module, "calculate_recommendation_conviction", spy)
    assemble_analysis(engine_input, output, is_thesis_stale=False,
                      generated_at=GENERATED_AT)
    assert captured, "production never called the conviction calculator at all"
    return captured


def _reasons(monkeypatch, observations, with_evidence, direction=Direction.SUPPORTS):
    result = _conviction_call(monkeypatch, observations, with_evidence, direction)["result"]
    return () if result is None else tuple(r.value for r in result.reasons)


class TestCoverageIsDerivedFromRealObservations:
    """`_coverage()`: no observations -> NOT_APPLICABLE; none carrying
    evidence -> NONE; all carrying evidence -> FULL; otherwise PARTIAL."""

    def test_no_observations_is_not_applicable(self):
        assert _derived_coverage(0, 0) is EvidenceCoverageLevel.NOT_APPLICABLE

    def test_observations_without_evidence_are_none_not_partial(self):
        """An observation alone is a claim, not support for one."""
        assert _derived_coverage(1, 0) is EvidenceCoverageLevel.NONE

    def test_some_observations_with_evidence_are_partial(self):
        assert _derived_coverage(2, 1) is EvidenceCoverageLevel.PARTIAL

    def test_every_observation_with_evidence_is_full(self):
        assert _derived_coverage(1, 1) is EvidenceCoverageLevel.FULL
        assert _derived_coverage(3, 3) is EvidenceCoverageLevel.FULL

    def test_challenging_evidence_still_counts_as_coverage(self):
        """Coverage measures whether a claim was *examined*, not whether
        the examination agreed with it."""
        assert _derived_coverage(1, 1, Direction.CHALLENGES) is EvidenceCoverageLevel.FULL


class TestProductionPassesTheDerivedCoverage:
    """The wiring. Without these, both halves could work while nothing
    connected them."""

    @pytest.mark.parametrize("observations,with_evidence,expected", [
        (0, 0, EvidenceCoverageLevel.NOT_APPLICABLE),
        (1, 0, EvidenceCoverageLevel.NONE),
        (2, 1, EvidenceCoverageLevel.PARTIAL),
        (1, 1, EvidenceCoverageLevel.FULL),
    ])
    def test_the_calculator_receives_the_level_the_observations_imply(
            self, monkeypatch, observations, with_evidence, expected):
        captured = _conviction_call(monkeypatch, observations, with_evidence)
        assert captured["kwargs"]["evidence_coverage"] is expected


class TestConvictionReflectsRealCoverage:
    def test_partial_coverage_is_reported_as_partial(self, monkeypatch):
        """PARTIAL, derived from real observations -- not asserted into
        existence by handing the enum to the calculator."""
        assert "evidence_coverage_partial" in _reasons(monkeypatch, 2, 1)

    def test_full_coverage_is_reported_as_full(self, monkeypatch):
        reasons = _reasons(monkeypatch, 1, 1)
        assert "evidence_coverage_full" in reasons
        assert "no_contradicting_evidence" in reasons

    def test_absent_coverage_is_not_reported_as_partial_or_full(self, monkeypatch):
        for reasons in (_reasons(monkeypatch, 0, 0), _reasons(monkeypatch, 1, 0)):
            assert "evidence_coverage_partial" not in reasons
            assert "evidence_coverage_full" not in reasons

    def test_challenging_evidence_is_recorded_as_a_contradiction(self, monkeypatch):
        """Direction is investor-supplied; CHALLENGES must surface as a
        contradiction rather than silently counting as support."""
        reasons = _reasons(monkeypatch, 1, 1, Direction.CHALLENGES)
        assert "contradicting_evidence_present" in reasons
        assert "no_contradicting_evidence" not in reasons

    def test_full_coverage_lifts_conviction_above_low(self, monkeypatch):
        """The branch that had never run on real data: FULL coverage is
        the only route out of LOW."""
        partial = _conviction_call(monkeypatch, 2, 1)["result"]
        full = _conviction_call(monkeypatch, 1, 1)["result"]
        assert partial.level.value == "low"
        assert full.level.value != "low"
