"""Tests for TypedDomainObjectReference (DO-IMP-002).

Corrected per docs/atlas_domain_object_architecture/
Domain-Object-Type-Set-Discrepancy-Investigation.md, Outcome 1:
Observation is a valid target type; Case is not.
"""
from __future__ import annotations

import dataclasses
import uuid

import pytest

from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.exceptions import InvalidTypedDomainObjectReferenceError
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference


class TestConstruction:
    def test_valid_type_and_id_creates_a_reference(self):
        target_id = uuid.uuid4()
        reference = TypedDomainObjectReference(
            target_type=DomainObjectType.DECISION, target_id=target_id
        )
        assert reference.target_type is DomainObjectType.DECISION
        assert reference.target_id == target_id

    def test_target_type_is_preserved_exactly(self):
        reference = TypedDomainObjectReference(
            target_type=DomainObjectType.KNOWLEDGE_REFERENCE, target_id=uuid.uuid4()
        )
        assert reference.target_type is DomainObjectType.KNOWLEDGE_REFERENCE

    def test_a_valid_observation_reference_can_be_constructed(self):
        target_id = uuid.uuid4()
        reference = TypedDomainObjectReference(
            target_type=DomainObjectType.OBSERVATION, target_id=target_id
        )
        assert reference.target_type is DomainObjectType.OBSERVATION
        assert reference.target_id == target_id

    def test_case_is_not_an_available_target_type_member(self):
        assert not hasattr(DomainObjectType, "CASE")

    def test_a_case_target_type_string_cannot_be_admitted(self):
        with pytest.raises(InvalidTypedDomainObjectReferenceError):
            TypedDomainObjectReference(target_type="Case", target_id=uuid.uuid4())

    def test_target_id_is_preserved_exactly(self):
        target_id = uuid.uuid4()
        reference = TypedDomainObjectReference(
            target_type=DomainObjectType.OUTCOME, target_id=target_id
        )
        assert reference.target_id == target_id

    def test_rejects_invalid_target_type(self):
        with pytest.raises(InvalidTypedDomainObjectReferenceError):
            TypedDomainObjectReference(target_type="Decision", target_id=uuid.uuid4())

    def test_rejects_a_non_adopted_but_plausible_target_type_string(self):
        with pytest.raises(InvalidTypedDomainObjectReferenceError):
            TypedDomainObjectReference(target_type="Evaluation", target_id=uuid.uuid4())

    def test_rejects_malformed_target_id(self):
        with pytest.raises(InvalidTypedDomainObjectReferenceError):
            TypedDomainObjectReference(
                target_type=DomainObjectType.DECISION, target_id="not-a-uuid"
            )

    def test_rejects_missing_target_id(self):
        with pytest.raises(InvalidTypedDomainObjectReferenceError):
            TypedDomainObjectReference(target_type=DomainObjectType.DECISION, target_id=None)


class TestEquality:
    def test_equal_type_and_id_are_equal(self):
        target_id = uuid.uuid4()
        first = TypedDomainObjectReference(
            target_type=DomainObjectType.DECISION, target_id=target_id
        )
        second = TypedDomainObjectReference(
            target_type=DomainObjectType.DECISION, target_id=target_id
        )
        assert first == second

    def test_same_id_different_target_type_is_not_equal(self):
        target_id = uuid.uuid4()
        as_decision = TypedDomainObjectReference(
            target_type=DomainObjectType.DECISION, target_id=target_id
        )
        as_outcome = TypedDomainObjectReference(
            target_type=DomainObjectType.OUTCOME, target_id=target_id
        )
        assert as_decision != as_outcome

    def test_same_id_as_observation_versus_another_target_type_is_not_equal(self):
        target_id = uuid.uuid4()
        as_observation = TypedDomainObjectReference(
            target_type=DomainObjectType.OBSERVATION, target_id=target_id
        )
        as_decision = TypedDomainObjectReference(
            target_type=DomainObjectType.DECISION, target_id=target_id
        )
        assert as_observation != as_decision

    def test_same_target_type_different_id_is_not_equal(self):
        first = TypedDomainObjectReference(
            target_type=DomainObjectType.DECISION, target_id=uuid.uuid4()
        )
        second = TypedDomainObjectReference(
            target_type=DomainObjectType.DECISION, target_id=uuid.uuid4()
        )
        assert first != second


class TestImmutability:
    def test_is_frozen(self):
        reference = TypedDomainObjectReference(
            target_type=DomainObjectType.DECISION, target_id=uuid.uuid4()
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            reference.target_id = uuid.uuid4()


class TestHashableForSetUse:
    def test_is_hashable(self):
        reference = TypedDomainObjectReference(
            target_type=DomainObjectType.DECISION, target_id=uuid.uuid4()
        )
        hash(reference)  # must not raise

    def test_duplicate_equal_references_collapse_in_a_set(self):
        target_id = uuid.uuid4()
        first = TypedDomainObjectReference(
            target_type=DomainObjectType.DECISION, target_id=target_id
        )
        second = TypedDomainObjectReference(
            target_type=DomainObjectType.DECISION, target_id=target_id
        )
        assert {first, second} == {first}
        assert len({first, second}) == 1

    def test_distinct_references_do_not_collapse(self):
        first = TypedDomainObjectReference(
            target_type=DomainObjectType.DECISION, target_id=uuid.uuid4()
        )
        second = TypedDomainObjectReference(
            target_type=DomainObjectType.OUTCOME, target_id=uuid.uuid4()
        )
        assert len({first, second}) == 2


class TestNoExtraSemanticFields:
    def test_only_target_type_and_target_id_are_declared(self):
        declared = {f.name for f in dataclasses.fields(TypedDomainObjectReference)}
        assert declared == {"target_type", "target_id"}
