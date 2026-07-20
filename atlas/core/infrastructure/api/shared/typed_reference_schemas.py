"""API wire schema for TypedDomainObjectReference (DO-IMP-002).

Wraps the domain value object for camelCase JSON I/O (ADR-004); does
not redefine it — `DomainObjectType` and `TypedDomainObjectReference`
remain defined only in `atlas.core.domain.shared`. No owning API
endpoint exists yet: this schema exists so that Knowledge Reference,
Reasoning Trace, Judgment, Decision, and Outcome's own future API
schemas can embed it without each independently reinventing camelCase
target-reference serialization.

`DomainObjectType` is a `(str, Enum)`, so Pydantic validates an incoming
`targetType` string against the six adopted values directly — an
unrecognized value is rejected by Pydantic's own validation (422 at the
API layer, once an owning router exists), never silently coerced —
and serializes a valid value back out as its own canonical string
(e.g. `"Decision"`), never as a Python enum member name.
"""
from __future__ import annotations

import uuid

from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference
from atlas.core.infrastructure.api.serialization import CamelModel


class TypedDomainObjectReferenceSchema(CamelModel):
    target_type: DomainObjectType
    target_id: uuid.UUID

    @classmethod
    def from_domain(
        cls, reference: TypedDomainObjectReference
    ) -> TypedDomainObjectReferenceSchema:
        return cls(target_type=reference.target_type, target_id=reference.target_id)

    def to_domain(self) -> TypedDomainObjectReference:
        return TypedDomainObjectReference(
            target_type=self.target_type, target_id=self.target_id
        )
