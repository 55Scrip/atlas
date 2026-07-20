"""Application service for the Knowledge Reference capture use case
(DO-IMP-003).

**Corrected per docs/atlas_domain_object_architecture/
Knowledge-Reference-Pre-Commit-Architecture-Review.md, Outcome 2.**

OE-006 §5 and §16 require that acceptance actually establish every
applicable invariant; OE-006 §9 recognizes no "accepted with a deferred
invariant" status. A Knowledge Reference must therefore not be accepted
against a target type whose applicable invariants — prior acceptance
(INV-005) and same-Case membership (INV-004) — cannot currently be
positively established, regardless of whether that target type is
canonically adopted.

**Canonical target eligibility and present capture availability are
distinct.** All six `DomainObjectType` members (Observation, Knowledge
Reference, Reasoning Trace, Judgment, Decision, Outcome) remain fully
canonical, reference-eligible Domain Object types (OE-002 §5.2) — none
of them is removed, narrowed, or reinterpreted here. At the current
repository state, however, only a **Knowledge Reference** target can
have both INV-005 and INV-004 positively established:

- Observation, Decision, and Outcome each already exist as
  implemented, accepted-instance repositories, so prior acceptance
  (INV-005) is, in principle, checkable for them — but none of the
  three yet carries a `case_id` (DO-REC-026, DO-REC-005, DO-REC-013,
  each its own separate, not-yet-implemented reconciliation item), so
  same-Case membership (INV-004) cannot currently be established
  against any of them at all.
- Reasoning Trace and Judgment have no accepted-instance repository
  yet (DO-IMP-009, DO-IMP-004 have not shipped), so prior acceptance
  (INV-005) cannot currently be established against either of them
  either.

Every one of these five target types therefore fails to meet the
"every applicable invariant positively established" bar OE-006
requires, and capture against any of them is rejected with
`TargetTypeUnavailableError` — not because the type is unknown,
invalid, or non-adopted, but because this specific capture operation
cannot currently verify what acceptance would need to certify. Capture
against each becomes available, with no change to Knowledge
Reference's own schema or API contract, once that type's own
prerequisite work lands.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.knowledge_reference.entity import KnowledgeReference
from atlas.core.domain.knowledge_reference.exceptions import (
    CrossCaseTargetError,
    KnowledgeReferenceNotFoundError,
    TargetNotFoundError,
    TargetTypeUnavailableError,
)
from atlas.core.domain.knowledge_reference.repository import KnowledgeReferenceRepository
from atlas.core.domain.knowledge_reference.value_objects import KnowledgeReferenceId
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference

_CURRENTLY_CAPTURE_ENABLED_TARGET_TYPES = frozenset({DomainObjectType.KNOWLEDGE_REFERENCE})


@dataclass(frozen=True)
class CaptureKnowledgeReferenceRequest:
    case_id: uuid.UUID
    target_type: DomainObjectType
    target_id: uuid.UUID


class KnowledgeReferenceService:
    def __init__(self, repository: KnowledgeReferenceRepository) -> None:
        self._knowledge_references = repository

    def capture(self, request: CaptureKnowledgeReferenceRequest) -> KnowledgeReference:
        case_id = CaseId(request.case_id)
        self._verify_target(
            case_id=case_id, target_type=request.target_type, target_id=request.target_id
        )

        target = TypedDomainObjectReference(
            target_type=request.target_type, target_id=request.target_id
        )
        knowledge_reference = KnowledgeReference.capture(case_id=case_id, target=target)
        self._knowledge_references.add(knowledge_reference)
        return knowledge_reference

    def get(self, knowledge_reference_id: KnowledgeReferenceId) -> KnowledgeReference:
        knowledge_reference = self._knowledge_references.get(knowledge_reference_id)
        if knowledge_reference is None:
            raise KnowledgeReferenceNotFoundError(
                f"No Knowledge Reference found with id {knowledge_reference_id}"
            )
        return knowledge_reference

    def _verify_target(
        self, *, case_id: CaseId, target_type: DomainObjectType, target_id: uuid.UUID
    ) -> None:
        if target_type not in _CURRENTLY_CAPTURE_ENABLED_TARGET_TYPES:
            raise TargetTypeUnavailableError(
                f"{target_type.value} is a canonical, reference-eligible target type "
                f"(OE-002 §5.2), but Knowledge Reference capture cannot currently "
                f"establish every applicable invariant for it"
            )

        existing = self._knowledge_references.get(KnowledgeReferenceId(target_id))
        if existing is None:
            raise TargetNotFoundError(f"No accepted Knowledge Reference found with id {target_id}")
        if existing.case_id != case_id:
            raise CrossCaseTargetError(
                f"Knowledge Reference {target_id} belongs to a different Case"
            )
