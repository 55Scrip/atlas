"""Tests for select_coaching_question (ATLAS-008).

Covers: no Reflection yields no question; template dispatch (Pattern-only
vs. Strategy-Signature-grounded) is the only thing that varies; the
either-answer test and no-hidden-conclusion invariant are documented and
verified for both fixed templates; Coach's text never restates any
content from the Reflection's own pattern/strategy_signature
descriptions; traceability.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.core.application.decision_coach.coach import select_coaching_question
from atlas.core.application.decision_coach.coaching_question import CoachingQuestion
from atlas.core.application.decision_reflection.reflection import DecisionReflection
from atlas.core.application.pattern_recognition.recognized_pattern import RecognizedPattern
from atlas.core.application.strategy_signature.recognized_strategy_signature import (
    RecognizedStrategySignature,
)
from atlas.core.domain.decision.value_objects import DecisionId

_RECOGNIZED_AT = datetime(2026, 7, 16, 12, 0, 0, tzinfo=timezone.utc)
_REFLECTED_AT = datetime(2026, 7, 16, 12, 30, 0, tzinfo=timezone.utc)


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


def _make_signature(*patterns):
    return RecognizedStrategySignature(
        strategy_name="connected_patterns",
        member_patterns=patterns,
        description="; ".join(p.description for p in patterns),
        recognized_at=_RECOGNIZED_AT,
    )


class TestNoReflectionYieldsNoQuestion:
    def test_none_reflection_yields_none(self):
        assert select_coaching_question(None) is None


class TestTemplateDispatch:
    def test_pattern_only_reflection_selects_the_pattern_only_question(self):
        pattern = _make_pattern()
        reflection = DecisionReflection(
            pattern=pattern,
            strategy_signature=None,
            description=f"This resembles a recognized Pattern: {pattern.description}",
            reflected_at=_REFLECTED_AT,
        )

        question = select_coaching_question(reflection)

        assert isinstance(question, CoachingQuestion)
        assert question.text == (
            "What's similar or different about this situation compared with "
            "what you just saw, if anything?"
        )

    def test_signature_grounded_reflection_selects_the_signature_question(self):
        pattern_a = _make_pattern(description="You have made 2 BUY decisions on NVIDIA.")
        pattern_b = _make_pattern(
            strategy_name="same_confidence",
            description="You recorded confidence 90 on 2 separate Decisions.",
        )
        signature = _make_signature(pattern_a, pattern_b)
        reflection = DecisionReflection(
            pattern=pattern_a,
            strategy_signature=signature,
            description="This resembles a recognized Pattern and a broader Strategy Signature.",
            reflected_at=_REFLECTED_AT,
        )

        question = select_coaching_question(reflection)

        assert question.text == (
            "What's similar or different about this situation compared with "
            "the broader connection you just saw, if anything?"
        )


class TestNoRestatedContent:
    def test_question_text_never_contains_the_pattern_description(self):
        pattern = _make_pattern(description="You have made 2 BUY decisions on NVIDIA.")
        reflection = DecisionReflection(
            pattern=pattern,
            strategy_signature=None,
            description="irrelevant",
            reflected_at=_REFLECTED_AT,
        )

        question = select_coaching_question(reflection)

        assert pattern.description not in question.text

    def test_question_text_never_contains_the_signature_description(self):
        pattern_a = _make_pattern(description="You have made 2 BUY decisions on NVIDIA.")
        pattern_b = _make_pattern(
            strategy_name="same_confidence",
            description="You recorded confidence 90 on 2 separate Decisions.",
        )
        signature = _make_signature(pattern_a, pattern_b)
        reflection = DecisionReflection(
            pattern=pattern_a,
            strategy_signature=signature,
            description="irrelevant",
            reflected_at=_REFLECTED_AT,
        )

        question = select_coaching_question(reflection)

        assert pattern_a.description not in question.text
        assert pattern_b.description not in question.text
        assert signature.description not in question.text


class TestEitherAnswerAndNoHiddenConclusionVerification:
    """Documents, as durable test assertions, the design-time verification
    performed in ATLAS-008-P §3 — not a runtime semantic check (this
    system performs none), but a record of why both fixed templates
    satisfy invariants 10 and 16, kept alongside the code they describe.
    """

    def test_both_templates_offer_symmetric_either_answer_framing(self):
        from atlas.core.application.decision_coach.coach import (
            _PATTERN_ONLY_QUESTION,
            _SIGNATURE_QUESTION,
        )

        for text in (_PATTERN_ONLY_QUESTION, _SIGNATURE_QUESTION):
            # Either-answer test (invariant 10): "similar or different"
            # offers two symmetric directions, neither foregrounded, and
            # the trailing "if anything" explicitly permits a third,
            # equally valid answer — no meaningful correspondence at all.
            assert "similar or different" in text
            assert text.rstrip("?").endswith("if anything")
            # No-hidden-conclusion (invariant 16): no evaluation,
            # recommendation, presumed concern, or expected answer —
            # checked here by absence of any such language, and by every
            # word in the template being traceable to this exact string
            # (i.e., nothing is interpolated that could smuggle one in).
            for forbidden in ("should", "risk", "worry", "mistake", "wrong", "correct"):
                assert forbidden not in text.lower()

    def test_signature_question_never_calls_a_strategy_signature_a_pattern(self):
        from atlas.core.application.decision_coach.coach import _SIGNATURE_QUESTION

        assert "pattern" not in _SIGNATURE_QUESTION.lower()


class TestTraceability:
    def test_coaching_question_reflection_is_the_exact_object_passed_in(self):
        pattern = _make_pattern()
        reflection = DecisionReflection(
            pattern=pattern,
            strategy_signature=None,
            description="irrelevant",
            reflected_at=_REFLECTED_AT,
        )

        question = select_coaching_question(reflection)

        assert question.reflection is reflection
