"""Tests for InterpretiveContent and ReflectionUnderstanding (ATLAS-013).

ReflectionUnderstanding's own __post_init__ protects the structural
invariants it can verify directly: empty concerns and duplicate ids are
outright rejected (not silently deduplicated or collapsed — a stronger
guarantee than Reflection Exploration's own silent-dedup rule), and
concerns must already arrive canonically ordered by (recorded_at,
id.value) — this value object never reorders its own input.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from atlas.core.application.reflection_understanding_formation.exceptions import (
    ConcernedMaterialNotCanonicallyOrderedError,
    DuplicateConcernedReflectionResponseError,
    MissingInterpretiveContentError,
    NoConcernedMaterialError,
)
from atlas.core.application.reflection_understanding_formation.understanding import (
    InterpretiveContent,
    ReflectionUnderstanding,
)
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.reflection_response.entity import ReflectionResponse
from atlas.core.domain.reflection_response.value_objects import (
    PatternMembershipSnapshot,
    ProvenanceSnapshot,
    ResponseText,
)

_T0 = datetime(2026, 7, 23, 9, 0, 0, tzinfo=timezone.utc)


def _make_response(recorded_at: datetime, text: str = "Keeping this.") -> ReflectionResponse:
    decision_id = DecisionId()
    return ReflectionResponse.register(
        decision_id=decision_id,
        response_text=ResponseText(text),
        provenance=ProvenanceSnapshot(
            reflection_description="You have made 2 BUY decisions on NVIDIA.",
            coaching_question_text="What's similar or different this time?",
            grounding_pattern=PatternMembershipSnapshot(
                strategy_name="same_subject_and_type",
                member_decision_ids=(decision_id,),
            ),
            strategy_signature_patterns=(),
            reasoning_context_subject="NVIDIA",
            reasoning_context_decision_type="BUY",
            reasoning_context_confidence=80,
        ),
        clock=lambda: recorded_at,
    )


class TestInterpretiveContent:
    def test_rejects_none(self):
        with pytest.raises(MissingInterpretiveContentError):
            InterpretiveContent(None)  # type: ignore[arg-type]

    def test_rejects_whitespace_only(self):
        with pytest.raises(MissingInterpretiveContentError):
            InterpretiveContent("   \n\t  ")

    def test_never_transforms_the_stored_value(self):
        content = InterpretiveContent("  This time feels DIFFERENT.  ")
        assert content.value == "  This time feels DIFFERENT.  "


class TestReflectionUnderstandingConstruction:
    def test_rejects_empty_concerns(self):
        with pytest.raises(NoConcernedMaterialError):
            ReflectionUnderstanding(content=InterpretiveContent("An interpretation."), concerns=())

    def test_rejects_duplicate_concerned_ids(self):
        entry = _make_response(_T0)
        with pytest.raises(DuplicateConcernedReflectionResponseError):
            ReflectionUnderstanding(
                content=InterpretiveContent("An interpretation."),
                concerns=(entry, entry),
            )

    def test_rejects_non_canonically_ordered_concerns(self):
        earlier = _make_response(_T0)
        later = _make_response(_T0.replace(hour=15))
        with pytest.raises(ConcernedMaterialNotCanonicallyOrderedError):
            ReflectionUnderstanding(
                content=InterpretiveContent("An interpretation."),
                concerns=(later, earlier),
            )

    def test_accepts_canonically_ordered_unique_concerns(self):
        earlier = _make_response(_T0)
        later = _make_response(_T0.replace(hour=15))
        understanding = ReflectionUnderstanding(
            content=InterpretiveContent("An interpretation."),
            concerns=(earlier, later),
        )
        assert understanding.concerns == (earlier, later)

    def test_never_reorders_or_deduplicates_valid_input(self):
        # Given already-canonical, already-unique input, the value
        # object stores it exactly as given — construction validates,
        # it does not additionally transform.
        earlier = _make_response(_T0)
        later = _make_response(_T0.replace(hour=15))
        understanding = ReflectionUnderstanding(
            content=InterpretiveContent("An interpretation."),
            concerns=(earlier, later),
        )
        assert understanding.concerns is not None
        assert list(understanding.concerns) == [earlier, later]


class TestReflectionUnderstandingExtensionalIdentity:
    def test_equal_content_and_concerns_are_equal(self):
        entry = _make_response(_T0)
        first = ReflectionUnderstanding(
            content=InterpretiveContent("Same interpretation."), concerns=(entry,)
        )
        second = ReflectionUnderstanding(
            content=InterpretiveContent("Same interpretation."), concerns=(entry,)
        )
        assert first == second
        assert hash(first) == hash(second)

    def test_different_content_is_not_equal(self):
        entry = _make_response(_T0)
        first = ReflectionUnderstanding(content=InterpretiveContent("A."), concerns=(entry,))
        second = ReflectionUnderstanding(content=InterpretiveContent("B."), concerns=(entry,))
        assert first != second

    def test_different_concerned_material_is_not_equal(self):
        first_entry = _make_response(_T0)
        second_entry = _make_response(_T0.replace(hour=15))
        first = ReflectionUnderstanding(
            content=InterpretiveContent("Same interpretation."), concerns=(first_entry,)
        )
        second = ReflectionUnderstanding(
            content=InterpretiveContent("Same interpretation."), concerns=(second_entry,)
        )
        assert first != second

    def test_not_equal_to_a_different_type(self):
        entry = _make_response(_T0)
        understanding = ReflectionUnderstanding(
            content=InterpretiveContent("An interpretation."), concerns=(entry,)
        )
        assert understanding != "not a ReflectionUnderstanding"
