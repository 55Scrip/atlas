"""Tests for ReflectionResponse's value objects (ATLAS-009).

ResponseText's no-normalization guarantee is the load-bearing test here:
ATLAS-009-D invariant 10 requires the investor's own words be preserved
without Atlas rewriting their meaning, and validation must not become
transformation.
"""
from __future__ import annotations

import pytest

from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.reflection_response.exceptions import (
    MissingCoachingQuestionTextError,
    MissingReflectionDescriptionError,
    MissingResponseTextError,
)
from atlas.core.domain.reflection_response.value_objects import (
    PatternMembershipSnapshot,
    ProvenanceSnapshot,
    ReflectionResponseId,
    ResponseText,
)


class TestResponseTextNeverNormalizes:
    def test_leading_and_trailing_whitespace_is_preserved(self):
        text = ResponseText("  This time feels different.  ")
        assert text.value == "  This time feels different.  "

    def test_casing_is_preserved(self):
        text = ResponseText("This Time FEELS Different")
        assert text.value == "This Time FEELS Different"

    def test_punctuation_is_preserved(self):
        text = ResponseText("Is it, though?! I'm not so sure...")
        assert text.value == "Is it, though?! I'm not so sure..."

    def test_internal_multiple_spacing_is_preserved(self):
        text = ResponseText("This    time   feels different")
        assert text.value == "This    time   feels different"

    def test_str_returns_the_unmodified_value(self):
        text = ResponseText("  padded  ")
        assert str(text) == "  padded  "


class TestResponseTextEmptinessValidation:
    def test_rejects_empty_string(self):
        with pytest.raises(MissingResponseTextError):
            ResponseText("")

    def test_rejects_whitespace_only_string(self):
        with pytest.raises(MissingResponseTextError):
            ResponseText("   \t  \n ")

    def test_rejects_none(self):
        with pytest.raises(MissingResponseTextError):
            ResponseText(None)  # type: ignore[arg-type]

    def test_accepts_text_that_is_only_whitespace_padded_around_content(self):
        # Emptiness is checked via .strip(), but the stored value is not
        # stripped -- confirmed here alongside the rejection tests above.
        text = ResponseText("  x  ")
        assert text.value == "  x  "


class TestPatternMembershipSnapshot:
    def test_holds_strategy_name_and_member_decision_ids(self):
        d1, d2 = DecisionId(), DecisionId()
        snapshot = PatternMembershipSnapshot(
            strategy_name="same_subject_and_type", member_decision_ids=(d1, d2)
        )
        assert snapshot.strategy_name == "same_subject_and_type"
        assert snapshot.member_decision_ids == (d1, d2)


class TestProvenanceSnapshotValidation:
    def _grounding_pattern(self) -> PatternMembershipSnapshot:
        return PatternMembershipSnapshot(
            strategy_name="same_subject_and_type", member_decision_ids=(DecisionId(),)
        )

    def test_rejects_missing_reflection_description(self):
        with pytest.raises(MissingReflectionDescriptionError):
            ProvenanceSnapshot(
                reflection_description="",
                coaching_question_text="What's similar or different?",
                grounding_pattern=self._grounding_pattern(),
                strategy_signature_patterns=(),
                reasoning_context_subject="NVIDIA",
                reasoning_context_decision_type="BUY",
                reasoning_context_confidence=None,
            )

    def test_rejects_missing_coaching_question_text(self):
        with pytest.raises(MissingCoachingQuestionTextError):
            ProvenanceSnapshot(
                reflection_description="You have made 2 BUY decisions on NVIDIA.",
                coaching_question_text="   ",
                grounding_pattern=self._grounding_pattern(),
                strategy_signature_patterns=(),
                reasoning_context_subject="NVIDIA",
                reasoning_context_decision_type="BUY",
                reasoning_context_confidence=None,
            )

    def test_accepts_a_complete_snapshot(self):
        snapshot = ProvenanceSnapshot(
            reflection_description="You have made 2 BUY decisions on NVIDIA.",
            coaching_question_text="What's similar or different?",
            grounding_pattern=self._grounding_pattern(),
            strategy_signature_patterns=(),
            reasoning_context_subject="NVIDIA",
            reasoning_context_decision_type="BUY",
            reasoning_context_confidence=None,
        )
        assert snapshot.reflection_description == "You have made 2 BUY decisions on NVIDIA."


class TestReflectionResponseId:
    def test_two_instances_are_distinct(self):
        assert ReflectionResponseId() != ReflectionResponseId()
