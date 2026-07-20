"""Tests for the Knowledge Reference aggregate root (DO-IMP-003)."""
from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime, timezone

import pytest

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.knowledge_reference.entity import KnowledgeReference
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference

_CASE_ID = CaseId()
_TARGET = TypedDomainObjectReference(
    target_type=DomainObjectType.OBSERVATION, target_id=uuid.uuid4()
)


def _fixed_clock(dt: datetime):
    return lambda: dt


class TestKnowledgeReferenceCapture:
    def test_captures_the_given_fields(self):
        kr = KnowledgeReference.capture(case_id=_CASE_ID, target=_TARGET)
        assert kr.case_id == _CASE_ID
        assert kr.target == _TARGET

    def test_assigns_a_fresh_id(self):
        first = KnowledgeReference.capture(case_id=_CASE_ID, target=_TARGET)
        second = KnowledgeReference.capture(case_id=_CASE_ID, target=_TARGET)
        assert first.id != second.id

    def test_recorded_at_is_always_now(self):
        now = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)
        kr = KnowledgeReference.capture(case_id=_CASE_ID, target=_TARGET, clock=_fixed_clock(now))
        assert kr.recorded_at == now

    def test_recorded_at_defaults_to_the_real_clock(self):
        before = datetime.now(timezone.utc)
        kr = KnowledgeReference.capture(case_id=_CASE_ID, target=_TARGET)
        after = datetime.now(timezone.utc)
        assert before <= kr.recorded_at <= after

    def test_requires_a_case_id(self):
        with pytest.raises(TypeError):
            KnowledgeReference.capture(target=_TARGET)

    def test_requires_a_target(self):
        with pytest.raises(TypeError):
            KnowledgeReference.capture(case_id=_CASE_ID)


class TestKnowledgeReferenceHasNoSpeculativeFields:
    def test_only_the_four_canonical_fields_are_declared(self):
        # No confidence, weight, rationale, explanation, provenance, or
        # source-quality field exists — Section 3 of DO-IMP-003 forbids
        # all of them.
        declared = {f.name for f in dataclasses.fields(KnowledgeReference)}
        assert declared == {"id", "case_id", "target", "recorded_at"}


class TestExactlyOneTarget:
    def test_target_is_a_single_value_not_a_collection(self):
        # INV-014 (exactly one target) is structurally guaranteed: the
        # `target` field's own type is a single TypedDomainObjectReference,
        # never a list/set/tuple of references.
        kr = KnowledgeReference.capture(case_id=_CASE_ID, target=_TARGET)
        assert isinstance(kr.target, TypedDomainObjectReference)
        assert not isinstance(kr.target, (list, set, tuple))


class TestKnowledgeReferenceImmutability:
    def test_is_frozen(self):
        kr = KnowledgeReference.capture(case_id=_CASE_ID, target=_TARGET)
        with pytest.raises(dataclasses.FrozenInstanceError):
            kr.target = _TARGET


class TestKnowledgeReferenceIdentity:
    def test_two_references_with_identical_case_and_target_remain_distinct(self):
        same_instant = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)
        first = KnowledgeReference.capture(
            case_id=_CASE_ID, target=_TARGET, clock=_fixed_clock(same_instant)
        )
        second = KnowledgeReference.capture(
            case_id=_CASE_ID, target=_TARGET, clock=_fixed_clock(same_instant)
        )
        assert first != second
        assert first.id != second.id

    def test_a_knowledge_reference_equals_itself(self):
        kr = KnowledgeReference.capture(case_id=_CASE_ID, target=_TARGET)
        assert kr == kr

    def test_duplicate_targets_across_separate_references_are_permitted(self):
        # OE-002 §5.2 states no restriction against this.
        first = KnowledgeReference.capture(case_id=_CASE_ID, target=_TARGET)
        second = KnowledgeReference.capture(case_id=_CASE_ID, target=_TARGET)
        assert first.target == second.target
        assert first.id != second.id
