"""Tests for CaptureReflectionResponseService and build_provenance_snapshot (ATLAS-009)."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.core.application.decision_coach.coaching_question import CoachingQuestion
from atlas.core.application.decision_reflection.reasoning_context import ReasoningContext
from atlas.core.application.decision_reflection.reflection import DecisionReflection
from atlas.core.application.pattern_recognition.recognized_pattern import RecognizedPattern
from atlas.core.application.reflection_response.capture_reflection_response import (
    CaptureReflectionResponseService,
)
from atlas.core.application.reflection_response.provisional_response import (
    ProvisionalReflectionResponse,
    build_provenance_snapshot,
)
from atlas.core.application.strategy_signature.recognized_strategy_signature import (
    RecognizedStrategySignature,
)
from atlas.core.domain.decision.value_objects import DecisionId

_RECOGNIZED_AT = datetime(2026, 7, 17, 9, 0, 0, tzinfo=timezone.utc)
_RECORDED_AT = datetime(2026, 7, 17, 10, 0, 0, tzinfo=timezone.utc)


def _make_pattern(
    strategy_name="same_subject_and_type",
    description="You have made 2 BUY decisions on NVIDIA.",
):
    return RecognizedPattern(
        strategy_name=strategy_name,
        member_decision_ids=(DecisionId(), DecisionId()),
        description=description,
        recognized_at=_RECOGNIZED_AT,
        matching_key=("NVIDIA", "BUY"),
    )


class FakeReflectionResponseRepository:
    def __init__(self):
        self.added = []

    def add(self, reflection_response):
        self.added.append(reflection_response)

    def get(self, reflection_response_id):
        return next((r for r in self.added if r.id == reflection_response_id), None)


class TestBuildProvenanceSnapshot:
    def test_captures_reflection_description_and_grounding_pattern(self):
        pattern = _make_pattern()
        reflection = DecisionReflection(
            pattern=pattern,
            strategy_signature=None,
            description=f"This resembles a recognized Pattern: {pattern.description}",
            reflected_at=_RECOGNIZED_AT,
        )
        coaching_question = CoachingQuestion(
            text="What's similar or different?", reflection=reflection
        )
        context = ReasoningContext(subject="NVIDIA", decision_type="BUY")

        snapshot = build_provenance_snapshot(reflection, coaching_question, context)

        assert snapshot.reflection_description == reflection.description
        assert snapshot.coaching_question_text == coaching_question.text
        assert snapshot.grounding_pattern.strategy_name == pattern.strategy_name
        assert snapshot.grounding_pattern.member_decision_ids == pattern.member_decision_ids
        assert snapshot.strategy_signature_patterns == ()
        assert snapshot.reasoning_context_subject == "NVIDIA"
        assert snapshot.reasoning_context_decision_type == "BUY"
        assert snapshot.reasoning_context_confidence is None

    def test_captures_every_constituent_pattern_of_an_attached_signature(self):
        pattern_a = _make_pattern(description="You have made 2 BUY decisions on NVIDIA.")
        pattern_b = _make_pattern(
            strategy_name="same_confidence",
            description="You recorded confidence 90 on 2 separate Decisions.",
        )
        signature = RecognizedStrategySignature(
            strategy_name="connected_patterns",
            member_patterns=(pattern_a, pattern_b),
            description="; ".join((pattern_a.description, pattern_b.description)),
            recognized_at=_RECOGNIZED_AT,
        )
        reflection = DecisionReflection(
            pattern=pattern_a,
            strategy_signature=signature,
            description="irrelevant",
            reflected_at=_RECOGNIZED_AT,
        )
        coaching_question = CoachingQuestion(text="q", reflection=reflection)
        context = ReasoningContext(subject="NVIDIA", decision_type="BUY")

        snapshot = build_provenance_snapshot(reflection, coaching_question, context)

        assert len(snapshot.strategy_signature_patterns) == 2
        assert snapshot.strategy_signature_patterns[0].strategy_name == pattern_a.strategy_name
        assert snapshot.strategy_signature_patterns[1].strategy_name == pattern_b.strategy_name

    def test_does_not_hold_a_reference_to_the_ephemeral_objects(self):
        pattern = _make_pattern()
        reflection = DecisionReflection(
            pattern=pattern, strategy_signature=None, description="d", reflected_at=_RECOGNIZED_AT
        )
        coaching_question = CoachingQuestion(text="q", reflection=reflection)
        context = ReasoningContext(subject="NVIDIA", decision_type="BUY")

        snapshot = build_provenance_snapshot(reflection, coaching_question, context)

        assert not isinstance(snapshot.grounding_pattern, RecognizedPattern)
        assert isinstance(snapshot.grounding_pattern.strategy_name, str)
        assert isinstance(snapshot.reflection_description, str)
        assert isinstance(snapshot.coaching_question_text, str)


class TestCaptureReflectionResponseService:
    def test_capture_persists_a_reflection_response_anchored_to_the_given_decision(self):
        repository = FakeReflectionResponseRepository()
        service = CaptureReflectionResponseService(repository)
        pattern = _make_pattern()
        reflection = DecisionReflection(
            pattern=pattern, strategy_signature=None, description="d", reflected_at=_RECOGNIZED_AT
        )
        coaching_question = CoachingQuestion(text="q", reflection=reflection)
        context = ReasoningContext(subject="NVIDIA", decision_type="BUY")
        provisional = ProvisionalReflectionResponse(
            response_text="This time feels different.",
            provenance=build_provenance_snapshot(reflection, coaching_question, context),
        )
        decision_id = DecisionId()

        result = service.capture(provisional, decision_id=decision_id, clock=lambda: _RECORDED_AT)

        assert repository.added == [result]
        assert result.decision_id == decision_id
        assert result.response_text.value == "This time feels different."
        assert result.recorded_at == _RECORDED_AT
