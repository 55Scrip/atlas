"""Domain tests for the Judgment aggregate (DO-IMP-004)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.judgment.entity import Judgment
from atlas.core.domain.judgment.exceptions import JudgmentError, MissingCharacterizationError
from atlas.core.domain.judgment.value_objects import Characterization, JudgmentId
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference


def _fixed_clock() -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone.utc)


class TestInternalContentForm:
    def test_captures_with_no_subject(self):
        judgment = Judgment.capture(
            case_id=CaseId(),
            characterization=Characterization("The thesis remains intact"),
            clock=_fixed_clock,
        )
        assert judgment.subject is None
        assert str(judgment.characterization) == "The thesis remains intact"

    def test_assigns_identity_and_recorded_at(self):
        judgment = Judgment.capture(
            case_id=CaseId(),
            characterization=Characterization("settled"),
            clock=_fixed_clock,
        )
        assert isinstance(judgment.id, JudgmentId)
        assert judgment.recorded_at == _fixed_clock()

    def test_is_permitted_as_the_first_domain_object_in_an_empty_case(self):
        # INV-012: the internal-content form is unconditionally
        # root-eligible — no prior accepted object is required.
        judgment = Judgment.capture(
            case_id=CaseId(),
            characterization=Characterization("first ever object in this Case"),
        )
        assert judgment.subject is None


class TestReferentialForm:
    def test_captures_with_a_subject_reference(self):
        subject = TypedDomainObjectReference(
            target_type=DomainObjectType.KNOWLEDGE_REFERENCE, target_id=uuid.uuid4()
        )
        judgment = Judgment.capture(
            case_id=CaseId(),
            characterization=Characterization("relying on this knowledge"),
            subject=subject,
        )
        assert judgment.subject == subject

    def test_characterization_remains_required_even_with_a_subject(self):
        with pytest.raises(MissingCharacterizationError):
            Judgment.capture(
                case_id=CaseId(),
                characterization=Characterization(""),
                subject=TypedDomainObjectReference(
                    target_type=DomainObjectType.JUDGMENT, target_id=uuid.uuid4()
                ),
            )


class TestInvalidConstruction:
    def test_rejects_a_subject_that_is_not_a_typed_reference(self):
        with pytest.raises(JudgmentError):
            Judgment(
                id=JudgmentId(),
                case_id=CaseId(),
                characterization=Characterization("settled"),
                recorded_at=_fixed_clock(),
                subject="not-a-typed-reference",
            )


class TestIdentity:
    def test_two_judgments_with_identical_content_remain_distinct(self):
        case_id = CaseId()
        characterization = Characterization("identical text")
        first = Judgment.capture(
            case_id=case_id, characterization=characterization, clock=_fixed_clock
        )
        second = Judgment.capture(
            case_id=case_id, characterization=characterization, clock=_fixed_clock
        )
        assert first.id != second.id
        assert first != second

    def test_identical_id_and_fields_compare_equal(self):
        judgment_id = JudgmentId()
        case_id = CaseId()
        characterization = Characterization("settled")
        recorded_at = _fixed_clock()
        first = Judgment(
            id=judgment_id,
            case_id=case_id,
            characterization=characterization,
            recorded_at=recorded_at,
        )
        second = Judgment(
            id=judgment_id,
            case_id=case_id,
            characterization=characterization,
            recorded_at=recorded_at,
        )
        assert first == second


class TestContradictoryJudgmentsPermitted:
    def test_two_opposite_characterizations_in_the_same_case_are_both_valid(self):
        case_id = CaseId()
        positive = Judgment.capture(case_id=case_id, characterization=Characterization("Bullish"))
        negative = Judgment.capture(case_id=case_id, characterization=Characterization("Bearish"))
        assert positive.case_id == negative.case_id == case_id
        assert positive.id != negative.id
