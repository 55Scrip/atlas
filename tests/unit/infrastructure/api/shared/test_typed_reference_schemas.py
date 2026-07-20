"""Serialization tests for TypedDomainObjectReferenceSchema (DO-IMP-002).

Corrected per docs/atlas_domain_object_architecture/
Domain-Object-Type-Set-Discrepancy-Investigation.md, Outcome 1:
Observation is an accepted target type; Case is not.
"""
from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference
from atlas.core.infrastructure.api.shared.typed_reference_schemas import (
    TypedDomainObjectReferenceSchema,
)


class TestCanonicalCamelCaseOutput:
    def test_serializes_to_camelcase_field_names(self):
        target_id = uuid.uuid4()
        schema = TypedDomainObjectReferenceSchema(
            target_type=DomainObjectType.DECISION, target_id=target_id
        )
        dumped = schema.model_dump(by_alias=True, mode="json")
        assert dumped == {"targetType": "Decision", "targetId": str(target_id)}

    def test_accepts_snake_case_input_for_backward_compatibility(self):
        target_id = uuid.uuid4()
        schema = TypedDomainObjectReferenceSchema(target_type="Outcome", target_id=target_id)
        assert schema.target_type is DomainObjectType.OUTCOME

    def test_accepts_camelcase_input(self):
        target_id = str(uuid.uuid4())
        schema = TypedDomainObjectReferenceSchema.model_validate(
            {"targetType": "Judgment", "targetId": target_id}
        )
        assert schema.target_type is DomainObjectType.JUDGMENT
        assert str(schema.target_id) == target_id

    def test_no_internal_enum_names_leak(self):
        schema = TypedDomainObjectReferenceSchema(
            target_type=DomainObjectType.KNOWLEDGE_REFERENCE, target_id=uuid.uuid4()
        )
        dumped = schema.model_dump(by_alias=True, mode="json")
        assert dumped["targetType"] == "KnowledgeReference"
        assert "DomainObjectType" not in dumped["targetType"]
        assert "KNOWLEDGE_REFERENCE" not in dumped["targetType"]

    def test_observation_target_type_is_accepted(self):
        target_id = uuid.uuid4()
        schema = TypedDomainObjectReferenceSchema.model_validate(
            {"targetType": "Observation", "targetId": str(target_id)}
        )
        assert schema.target_type is DomainObjectType.OBSERVATION
        dumped = schema.model_dump(by_alias=True, mode="json")
        assert dumped == {"targetType": "Observation", "targetId": str(target_id)}


class TestRoundTrip:
    def test_domain_to_schema_to_domain_preserves_equality(self):
        original = TypedDomainObjectReference(
            target_type=DomainObjectType.DECISION, target_id=uuid.uuid4()
        )
        schema = TypedDomainObjectReferenceSchema.from_domain(original)
        reconstructed = schema.to_domain()
        assert reconstructed == original

    def test_json_round_trip_preserves_equality(self):
        original = TypedDomainObjectReferenceSchema(
            target_type=DomainObjectType.OUTCOME, target_id=uuid.uuid4()
        )
        json_body = original.model_dump_json(by_alias=True)
        reloaded = TypedDomainObjectReferenceSchema.model_validate_json(json_body)
        assert reloaded.to_domain() == original.to_domain()

    def test_observation_round_trips_correctly(self):
        original = TypedDomainObjectReferenceSchema(
            target_type=DomainObjectType.OBSERVATION, target_id=uuid.uuid4()
        )
        json_body = original.model_dump_json(by_alias=True)
        reloaded = TypedDomainObjectReferenceSchema.model_validate_json(json_body)
        assert reloaded.to_domain() == original.to_domain()


class TestRejection:
    def test_unknown_target_type_is_rejected(self):
        with pytest.raises(ValidationError):
            TypedDomainObjectReferenceSchema(target_type="Evaluation", target_id=uuid.uuid4())

    def test_case_target_type_is_rejected(self):
        # Case is the ownership boundary (OE-002 §3.1), not a member of
        # the closed Domain Object Set, and therefore not a valid
        # target type — see the discrepancy investigation.
        with pytest.raises(ValidationError):
            TypedDomainObjectReferenceSchema.model_validate(
                {"targetType": "Case", "targetId": str(uuid.uuid4())}
            )

    def test_malformed_target_id_is_rejected(self):
        with pytest.raises(ValidationError):
            TypedDomainObjectReferenceSchema(
                target_type=DomainObjectType.DECISION, target_id="not-a-uuid"
            )

    def test_missing_fields_are_rejected(self):
        with pytest.raises(ValidationError):
            TypedDomainObjectReferenceSchema.model_validate({})
