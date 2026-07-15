"""Tests for ReflectionUnderstandingFormationQuery (ATLAS-013).

Constructs the query directly from a plain ReflectionHistory value — no
Engine, no repository, no fake needed — proving the query is a pure,
dependency-free in-memory operation, identical in this respect to
ReflectionComparisonQuery and ReflectionExplorationQuery.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from atlas.core.application.reflection_history.history import ReflectionHistory
from atlas.core.application.reflection_understanding_formation.exceptions import (
    FormationNotExplicitlyRequestedError,
    MissingEpistemicQualificationError,
    MissingInterpretiveContentError,
    NoConcernedMaterialError,
    UnreachableReflectionResponseError,
)
from atlas.core.application.reflection_understanding_formation.formation import (
    ArticulationAuthorshipMode,
    SubstanceAuthorshipMode,
)
from atlas.core.application.reflection_understanding_formation.query import (
    ReflectionUnderstandingFormationQuery,
)
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.reflection_response.entity import ReflectionResponse
from atlas.core.domain.reflection_response.value_objects import (
    PatternMembershipSnapshot,
    ProvenanceSnapshot,
    ReflectionResponseId,
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


class TestNoConcernedMaterial:
    def test_empty_concerns_raises(self):
        entry = _make_response(_T0)
        history = ReflectionHistory(entries=(entry,))
        query = ReflectionUnderstandingFormationQuery(history)

        with pytest.raises(NoConcernedMaterialError):
            query.build(
                concerns=(),
                explicitly_requested=True,
                substance_authorship=SubstanceAuthorshipMode.INVESTOR_SUBSTANCE_AUTHORED,
                articulation_authorship=ArticulationAuthorshipMode.INVESTOR_ARTICULATED,
                content="An interpretation.",
            )


class TestUnreachableMaterial:
    def test_a_nonexistent_id_fails_the_entire_request(self):
        entry = _make_response(_T0)
        history = ReflectionHistory(entries=(entry,))
        query = ReflectionUnderstandingFormationQuery(history)
        nonexistent_id = ReflectionResponseId()

        with pytest.raises(UnreachableReflectionResponseError):
            query.build(
                concerns=(entry.id, nonexistent_id),
                explicitly_requested=True,
                substance_authorship=SubstanceAuthorshipMode.INVESTOR_SUBSTANCE_AUTHORED,
                articulation_authorship=ArticulationAuthorshipMode.INVESTOR_ARTICULATED,
                content="An interpretation.",
            )

    def test_an_id_belonging_to_a_different_owner_is_indistinguishable_from_nonexistent(self):
        owned_entry = _make_response(_T0)
        other_owners_entry = _make_response(_T0.replace(hour=15))
        history = ReflectionHistory(entries=(owned_entry,))
        query = ReflectionUnderstandingFormationQuery(history)

        with pytest.raises(UnreachableReflectionResponseError):
            query.build(
                concerns=(owned_entry.id, other_owners_entry.id),
                explicitly_requested=True,
                substance_authorship=SubstanceAuthorshipMode.INVESTOR_SUBSTANCE_AUTHORED,
                articulation_authorship=ArticulationAuthorshipMode.INVESTOR_ARTICULATED,
                content="An interpretation.",
            )


class TestExplicitRequestIsSeparateFromContribution:
    def test_explicitly_requested_false_fails_even_with_otherwise_valid_input(self):
        # A contribution being ready and material being valid must never
        # substitute for the separate, explicit request.
        entry = _make_response(_T0)
        history = ReflectionHistory(entries=(entry,))
        query = ReflectionUnderstandingFormationQuery(history)

        with pytest.raises(FormationNotExplicitlyRequestedError):
            query.build(
                concerns=(entry.id,),
                explicitly_requested=False,
                substance_authorship=SubstanceAuthorshipMode.INVESTOR_SUBSTANCE_AUTHORED,
                articulation_authorship=ArticulationAuthorshipMode.INVESTOR_ARTICULATED,
                content="A fully-formed interpretation, ready to go.",
            )


class TestContentAndQualificationValidation:
    def test_empty_content_raises(self):
        entry = _make_response(_T0)
        history = ReflectionHistory(entries=(entry,))
        query = ReflectionUnderstandingFormationQuery(history)

        with pytest.raises(MissingInterpretiveContentError):
            query.build(
                concerns=(entry.id,),
                explicitly_requested=True,
                substance_authorship=SubstanceAuthorshipMode.INVESTOR_SUBSTANCE_AUTHORED,
                articulation_authorship=ArticulationAuthorshipMode.INVESTOR_ARTICULATED,
                content="   ",
            )

    def test_empty_qualification_string_raises_but_none_does_not(self):
        entry = _make_response(_T0)
        history = ReflectionHistory(entries=(entry,))
        query = ReflectionUnderstandingFormationQuery(history)

        with pytest.raises(MissingEpistemicQualificationError):
            query.build(
                concerns=(entry.id,),
                explicitly_requested=True,
                substance_authorship=SubstanceAuthorshipMode.INVESTOR_SUBSTANCE_AUTHORED,
                articulation_authorship=ArticulationAuthorshipMode.INVESTOR_ARTICULATED,
                content="An interpretation.",
                epistemic_qualification="   ",
            )

        act = query.build(
            concerns=(entry.id,),
            explicitly_requested=True,
            substance_authorship=SubstanceAuthorshipMode.INVESTOR_SUBSTANCE_AUTHORED,
            articulation_authorship=ArticulationAuthorshipMode.INVESTOR_ARTICULATED,
            content="An interpretation.",
            epistemic_qualification=None,
        )
        assert act.epistemic_qualification is None


class TestSuccessfulBuild:
    def test_investor_substance_authored_build(self):
        entry = _make_response(_T0)
        history = ReflectionHistory(entries=(entry,))
        query = ReflectionUnderstandingFormationQuery(history)

        act = query.build(
            concerns=(entry.id,),
            explicitly_requested=True,
            substance_authorship=SubstanceAuthorshipMode.INVESTOR_SUBSTANCE_AUTHORED,
            articulation_authorship=ArticulationAuthorshipMode.INVESTOR_ARTICULATED,
            content="This time feels different.",
            epistemic_qualification="fairly confident",
        )

        assert act.substance_authorship == SubstanceAuthorshipMode.INVESTOR_SUBSTANCE_AUTHORED
        assert act.articulation_authorship == ArticulationAuthorshipMode.INVESTOR_ARTICULATED
        assert act.understanding.content.value == "This time feels different."
        assert act.epistemic_qualification.value == "fairly confident"
        assert act.understanding.concerns == (entry,)

    def test_duplicate_ids_in_concerns_are_deduplicated_before_construction(self):
        entry = _make_response(_T0)
        history = ReflectionHistory(entries=(entry,))
        query = ReflectionUnderstandingFormationQuery(history)

        act = query.build(
            concerns=(entry.id, entry.id, entry.id),
            explicitly_requested=True,
            substance_authorship=SubstanceAuthorshipMode.INVESTOR_SUBSTANCE_AUTHORED,
            articulation_authorship=ArticulationAuthorshipMode.INVESTOR_ARTICULATED,
            content="An interpretation.",
        )

        assert act.understanding.concerns == (entry,)

    def test_input_order_does_not_affect_the_resulting_canonical_order(self):
        earlier = _make_response(_T0)
        later = _make_response(_T0.replace(hour=15))
        history = ReflectionHistory(entries=(earlier, later))
        query = ReflectionUnderstandingFormationQuery(history)

        act = query.build(
            concerns=(later.id, earlier.id),
            explicitly_requested=True,
            substance_authorship=SubstanceAuthorshipMode.INVESTOR_SUBSTANCE_AUTHORED,
            articulation_authorship=ArticulationAuthorshipMode.INVESTOR_ARTICULATED,
            content="An interpretation.",
        )

        assert act.understanding.concerns == (earlier, later)

    def test_occurred_at_uses_the_injected_clock(self):
        entry = _make_response(_T0)
        history = ReflectionHistory(entries=(entry,))
        query = ReflectionUnderstandingFormationQuery(history)
        fixed_time = _T0.replace(hour=20)

        act = query.build(
            concerns=(entry.id,),
            explicitly_requested=True,
            substance_authorship=SubstanceAuthorshipMode.INVESTOR_SUBSTANCE_AUTHORED,
            articulation_authorship=ArticulationAuthorshipMode.INVESTOR_ARTICULATED,
            content="An interpretation.",
            clock=lambda: fixed_time,
        )

        assert act.occurred_at == fixed_time


class TestStructuralRepresentabilityOfNonOperativeModes:
    """Constructing a FormationAct through this query with
    ATLAS_SUBSTANCE_AUTHORED or JOINTLY_SUBSTANCE_AUTHORED demonstrates
    only that the type system can structurally represent those modes.
    It does not exercise, authorize, or set precedent for any operative
    Formation pathway using them — no such pathway exists in this
    increment. cli.py never asserts either value; only this direct,
    low-level test does, to prove the query itself does not reject them
    structurally.
    """

    def test_atlas_substance_authored_is_structurally_acceptable(self):
        entry = _make_response(_T0)
        history = ReflectionHistory(entries=(entry,))
        query = ReflectionUnderstandingFormationQuery(history)

        act = query.build(
            concerns=(entry.id,),
            explicitly_requested=True,
            substance_authorship=SubstanceAuthorshipMode.ATLAS_SUBSTANCE_AUTHORED,
            articulation_authorship=ArticulationAuthorshipMode.ATLAS_ARTICULATED,
            content="A proposition not already supplied by the investor.",
        )

        assert act.substance_authorship == SubstanceAuthorshipMode.ATLAS_SUBSTANCE_AUTHORED

    def test_jointly_substance_authored_is_structurally_acceptable(self):
        entry = _make_response(_T0)
        history = ReflectionHistory(entries=(entry,))
        query = ReflectionUnderstandingFormationQuery(history)

        act = query.build(
            concerns=(entry.id,),
            explicitly_requested=True,
            substance_authorship=SubstanceAuthorshipMode.JOINTLY_SUBSTANCE_AUTHORED,
            articulation_authorship=ArticulationAuthorshipMode.JOINTLY_ARTICULATED,
            content="A proposition materially depending on both contributions.",
        )

        assert act.substance_authorship == SubstanceAuthorshipMode.JOINTLY_SUBSTANCE_AUTHORED


class TestInputImmutability:
    def test_history_and_entries_are_unchanged_after_a_successful_build(self):
        earlier = _make_response(_T0)
        later = _make_response(_T0.replace(hour=15))
        history = ReflectionHistory(entries=(earlier, later))
        query = ReflectionUnderstandingFormationQuery(history)

        query.build(
            concerns=(earlier.id,),
            explicitly_requested=True,
            substance_authorship=SubstanceAuthorshipMode.INVESTOR_SUBSTANCE_AUTHORED,
            articulation_authorship=ArticulationAuthorshipMode.INVESTOR_ARTICULATED,
            content="An interpretation.",
        )

        assert history.entries == (earlier, later)
        assert history.entries[0] is earlier
        assert history.entries[1] is later

    def test_history_and_entries_are_unchanged_after_a_failed_build(self):
        earlier = _make_response(_T0)
        later = _make_response(_T0.replace(hour=15))
        history = ReflectionHistory(entries=(earlier, later))
        query = ReflectionUnderstandingFormationQuery(history)

        with pytest.raises(UnreachableReflectionResponseError):
            query.build(
                concerns=(earlier.id, ReflectionResponseId()),
                explicitly_requested=True,
                substance_authorship=SubstanceAuthorshipMode.INVESTOR_SUBSTANCE_AUTHORED,
                articulation_authorship=ArticulationAuthorshipMode.INVESTOR_ARTICULATED,
                content="An interpretation.",
            )

        assert history.entries == (earlier, later)
