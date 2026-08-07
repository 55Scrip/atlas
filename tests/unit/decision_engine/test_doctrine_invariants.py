"""Doctrine regression tests (Sprint Phase 8).

Test names are written to make the Decision Engine Doctrine's own
invariants explicit, per the Sprint's own required names. Grouped under
one class, following this repository's established
`class Test<Thing>: def test_snake_case(self):` convention.
"""
from __future__ import annotations

import dataclasses

from atlas.decision_engine.contracts import RecommendationOutcomeKind
from atlas.decision_engine.pipeline import run_pipeline
from tests.unit.decision_engine._fixtures import GENERATED_AT, build_minimal_input


class TestDoctrineInvariants:
    def test_recommendation_withheld_has_no_direction(self):
        """`DE-002` §4: "Direction ... is omitted entirely" under
        Recommendation Withheld. Enforced structurally: the type itself
        has no `direction` field, so there is nothing to be empty or
        wrong — it cannot exist."""
        output = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        field_names = {f.name for f in dataclasses.fields(output.recommendation)}
        assert "direction" not in field_names

    def test_recommendation_withheld_has_no_conviction(self):
        """`DE-002` §4: "Conviction ... is omitted entirely" under
        Recommendation Withheld."""
        output = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        field_names = {f.name for f in dataclasses.fields(output.recommendation)}
        assert "conviction" not in field_names
        assert "conviction_level" not in field_names

    def test_recommendation_withheld_does_not_default_to_hold(self):
        """`DE-001` §2's "Recommendation Withheld (Not a Seventh
        Direction)": Recommendation Withheld SHALL NOT default to Hold.
        There is no code path in this sprint's `determine_recommendation`
        that could produce a `Hold` value — this test documents that
        invariant at the output level, not just by code inspection."""
        output = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        assert output.recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD
        rendered = repr(output.recommendation)
        assert "HOLD" not in rendered.upper().replace("WITHHELD", "")

    def test_recommendation_withheld_does_not_default_to_no_action(self):
        """`DE-001` §2's "Recommendation Withheld (Not a Seventh
        Direction)": Recommendation Withheld SHALL NOT default to No
        Action."""
        output = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        assert output.recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD
        rendered = repr(output.recommendation)
        assert "NO_ACTION" not in rendered.upper()
        assert "NO ACTION" not in rendered.upper()

    def test_recommendation_withheld_is_not_a_seventh_direction(self):
        """`DE-001` §2: "An Atlas Recommendation states 'exactly one of
        six directions' — Recommendation Withheld is not a seventh."
        `RecommendationOutcomeKind` has exactly two members, and neither
        is one of the six named directions."""
        member_values = {member.value for member in RecommendationOutcomeKind}
        assert member_values == {"directional", "recommendation_withheld"}
        six_directions = {"buy", "add", "hold", "trim", "exit", "no_action"}
        assert member_values.isdisjoint(six_directions)

    def test_pipeline_returns_all_stage_results_when_unevaluated(self):
        """Sprint Phase 5: "The final output must always be complete and
        structurally valid, even when every substantive stage is
        unevaluated." No stage may be silently omitted."""
        output = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        for field in dataclasses.fields(output):
            assert getattr(output, field.name) is not None, (
                f"DecisionEngineOutput.{field.name} was None; no stage may "
                "be silently omitted"
            )

    def test_pipeline_is_deterministic_for_identical_input(self):
        """Sprint Phase 6: identical input and timestamp produce deeply
        equal output."""
        engine_input = build_minimal_input()
        first = run_pipeline(engine_input, generated_at=GENERATED_AT)
        second = run_pipeline(engine_input, generated_at=GENERATED_AT)
        assert first == second
