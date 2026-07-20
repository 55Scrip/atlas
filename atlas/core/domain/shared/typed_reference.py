"""A technical typed pointer to an adopted Domain Object (DO-IMP-002).

`TypedDomainObjectReference` represents only the pair `(target_type,
target_id)` — a structural, technical pointer. It asserts nothing about
whether the target exists, has been accepted, or belongs to the same
Case as whatever object holds this reference: those are referential
concerns belonging to each owning Domain Object's own application-layer
construction path (INV-004, INV-005), and are deliberately out of this
package's scope (see DO-IMP-002's own "Referential Validation
Interfaces" boundary, deferred and documented, not implemented here).

This class is deliberately shared, but sharing a technical
representation does not merge the semantic meaning of the relations
that will eventually hold one: Knowledge Reference's target, Reasoning
Trace's supporting-object reference, Judgment's subject reference,
Decision's committed-to-matter reference, and Outcome's realized-matter
reference remain five independently adopted, semantically distinct
relations. Each owning Domain Object gives this technical pointer its
own attribute name and its own persisted column names (e.g. Decision's
own `matter_target_type`/`matter_target_id`, Judgment's own
`subject_target_type`/`subject_target_id`) — nothing here dictates
those names, and this module is not imported by any owning Domain
Object yet.

`target_id` is deliberately a plain `uuid.UUID`, not a shared
"DomainObjectId" wrapper: a wrapper class would either duplicate each
aggregate's own typed id (ObservationId, DecisionId, OutcomeId, ...)
for no benefit, or would have to import those classes directly — which
would create exactly the dependency direction this module must not
have (a shared module depending on individual Domain Object modules),
and is impossible today regardless, since Knowledge Reference,
Reasoning Trace, and Judgment do not exist yet. Confirming that
`target_type` names, say, "Decision" does NOT retroactively make
`target_id` a `DecisionId` — only the owning object, once it has
independently checked `target_type`, may re-wrap `target_id` into its
own typed id, at its own boundary, outside this module.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.exceptions import InvalidTypedDomainObjectReferenceError


@dataclass(frozen=True)
class TypedDomainObjectReference:
    """An immutable, structural pointer to an adopted Domain Object.

    Equality and hashing are based on both `target_type` and `target_id`
    together — the default frozen-dataclass behavior already does
    exactly this, since both fields are themselves hashable — so this
    value object is directly usable inside a set, e.g. for Reasoning
    Trace's own non-empty support set.

    Deliberately carries no `case_id`, relation name, ordering,
    confidence, provenance, timestamp, acceptance state, or truth
    state: this is a technical pointer only, not an assertion of
    existence, acceptance, same-Case membership, epistemic support,
    knowledge reliance, subjecthood, commitment, realization, truth,
    reliability, or authority. Any of those, where they apply, belong
    to the owning Domain Object, not to this value object.
    """

    target_type: DomainObjectType
    target_id: uuid.UUID

    def __post_init__(self) -> None:
        if not isinstance(self.target_type, DomainObjectType):
            raise InvalidTypedDomainObjectReferenceError(
                f"target_type must be a DomainObjectType, got "
                f"{type(self.target_type).__name__}"
            )
        if not isinstance(self.target_id, uuid.UUID):
            raise InvalidTypedDomainObjectReferenceError(
                f"target_id must be a uuid.UUID, got {type(self.target_id).__name__}"
            )
