"""Tests for FormationAct, EpistemicQualification, and the two authorship
mode enums (ATLAS-013A).

The central claim under test: FormationAct uses pure object identity
(eq=False, no hand-written __eq__/__hash__), so two separately
constructed acts remain numerically distinct even when every field —
including two ReflectionUnderstanding values that are themselves
extensionally equal to one another — happens to match. A plain
dataclass-generated structural equality would have silently violated
ATLAS-013A-D Chapter 7's numerical-distinctness rule.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from atlas.core.application.reflection_understanding_formation.exceptions import (
    MissingEpistemicQualificationError,
)
from atlas.core.application.reflection_understanding_formation.formation import (
    ArticulationAuthorshipMode,
    EpistemicQualification,
    FormationAct,
    SubstanceAuthorshipMode,
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


def _make_act(entry: ReflectionResponse, occurred_at: datetime = _T0) -> FormationAct:
    understanding = ReflectionUnderstanding(
        content=InterpretiveContent("An interpretation."), concerns=(entry,)
    )
    return FormationAct(
        understanding=understanding,
        substance_authorship=SubstanceAuthorshipMode.INVESTOR_SUBSTANCE_AUTHORED,
        articulation_authorship=ArticulationAuthorshipMode.INVESTOR_ARTICULATED,
        epistemic_qualification=None,
        occurred_at=occurred_at,
    )


class TestEpistemicQualification:
    def test_rejects_none(self):
        with pytest.raises(MissingEpistemicQualificationError):
            EpistemicQualification(None)  # type: ignore[arg-type]

    def test_rejects_whitespace_only(self):
        with pytest.raises(MissingEpistemicQualificationError):
            EpistemicQualification("   ")

    def test_never_transforms_the_stored_value(self):
        qualification = EpistemicQualification("  fairly tentative  ")
        assert qualification.value == "  fairly tentative  "


class TestFormationActObjectIdentity:
    def test_two_acts_with_identical_fields_remain_unequal(self):
        entry = _make_response(_T0)
        act_one = _make_act(entry)
        act_two = _make_act(entry)

        # Their Understandings are extensionally equal to each other...
        assert act_one.understanding == act_two.understanding
        # ...yet the two acts themselves must remain numerically distinct.
        assert act_one != act_two
        assert not (act_one == act_two)

    def test_an_act_is_equal_only_to_itself(self):
        entry = _make_response(_T0)
        act = _make_act(entry)
        assert act == act

    def test_hashing_treats_identical_field_acts_as_distinct_keys(self):
        entry = _make_response(_T0)
        act_one = _make_act(entry)
        act_two = _make_act(entry)

        distinct_acts = {act_one, act_two}
        assert len(distinct_acts) == 2

    def test_equality_is_not_field_by_field(self):
        # Guards against a future accidental reintroduction of
        # dataclass-generated structural equality: even fields as
        # granular as occurred_at matching exactly must not make two
        # separately constructed acts compare equal.
        entry = _make_response(_T0)
        act_one = _make_act(entry, occurred_at=_T0)
        act_two = _make_act(entry, occurred_at=_T0)
        assert act_one.occurred_at == act_two.occurred_at
        assert act_one != act_two
