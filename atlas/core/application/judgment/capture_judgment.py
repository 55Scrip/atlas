"""Application service for the Judgment capture use case (DO-IMP-004).

`characterization` is always required (Judgment-Implementation-Design.md
Section 11); `subject`, when present, selects the referential form.
INV-012 root eligibility requires no separate check here: the
internal-content form (`subject is None`) is unconditionally
capture-eligible as a Case's first Domain Object, and the referential
form can never be first, since `_verify_subject` already requires its
target to be an already-accepted, same-Case object.

**Canonical target eligibility and present capture availability are
distinct** — the identical principle already established and corrected
for Knowledge Reference (see docs/atlas_domain_object_architecture/
Knowledge-Reference-Pre-Commit-Architecture-Review.md, Outcome 2). All
six `DomainObjectType` members remain fully canonical, reference-eligible
Domain Object types (OE-002 §5.4) as Judgment subjects — none is
removed, narrowed, or reinterpreted here. At the current repository
state, only **Knowledge Reference** and **Judgment** targets can have
both INV-005 and INV-004 positively established:

- Observation, Decision, and Outcome each lack a `case_id` today
  (DO-REC-026, DO-REC-005, DO-REC-013, none yet implemented), so
  same-Case membership (INV-004) cannot currently be established
  against any of them.
- Reasoning Trace has no accepted-instance repository yet (DO-IMP-009
  has not shipped), so prior acceptance (INV-005) is not merely
  unverifiable but determinately violated for it: no instance of that
  type has ever been accepted anywhere in this system.

Every one of these four target types therefore fails the "every
applicable invariant positively established" bar OE-006 §5/§9/§16
requires, and capture against any of them is rejected with
`TargetTypeUnavailableError`. Capture against each becomes available,
with no change to Judgment's own schema or API contract, once that
type's own prerequisite work lands.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.judgment.entity import Judgment
from atlas.core.domain.judgment.exceptions import (
    CrossCaseTargetError,
    JudgmentNotFoundError,
    TargetNotFoundError,
    TargetTypeUnavailableError,
)
from atlas.core.domain.judgment.repository import JudgmentRepository
from atlas.core.domain.judgment.value_objects import Characterization, JudgmentId
from atlas.core.domain.knowledge_reference.repository import KnowledgeReferenceRepository
from atlas.core.domain.knowledge_reference.value_objects import KnowledgeReferenceId
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference

_CURRENTLY_CAPTURE_ENABLED_SUBJECT_TARGET_TYPES = frozenset(
    {DomainObjectType.KNOWLEDGE_REFERENCE, DomainObjectType.JUDGMENT}
)


@dataclass(frozen=True)
class CaptureJudgmentRequest:
    case_id: uuid.UUID
    characterization: str
    subject: TypedDomainObjectReference | None = None


class JudgmentService:
    def __init__(
        self,
        repository: JudgmentRepository,
        knowledge_reference_repository: KnowledgeReferenceRepository,
    ) -> None:
        self._judgments = repository
        self._knowledge_references = knowledge_reference_repository

    def capture(self, request: CaptureJudgmentRequest) -> Judgment:
        case_id = CaseId(request.case_id)
        if request.subject is not None:
            self._verify_subject(case_id=case_id, subject=request.subject)

        judgment = Judgment.capture(
            case_id=case_id,
            characterization=Characterization(request.characterization),
            subject=request.subject,
        )
        self._judgments.add(judgment)
        return judgment

    def get(self, judgment_id: JudgmentId) -> Judgment:
        judgment = self._judgments.get(judgment_id)
        if judgment is None:
            raise JudgmentNotFoundError(f"No Judgment found with id {judgment_id}")
        return judgment

    def _verify_subject(self, *, case_id: CaseId, subject: TypedDomainObjectReference) -> None:
        if subject.target_type not in _CURRENTLY_CAPTURE_ENABLED_SUBJECT_TARGET_TYPES:
            raise TargetTypeUnavailableError(
                f"{subject.target_type.value} is a canonical, reference-eligible target "
                f"type (OE-002 §5.4), but Judgment capture cannot currently establish "
                f"every applicable invariant for it"
            )

        if subject.target_type is DomainObjectType.JUDGMENT:
            existing = self._judgments.get(JudgmentId(subject.target_id))
        else:
            existing = self._knowledge_references.get(KnowledgeReferenceId(subject.target_id))

        if existing is None:
            raise TargetNotFoundError(
                f"No accepted {subject.target_type.value} found with id {subject.target_id}"
            )
        if existing.case_id != case_id:
            raise CrossCaseTargetError(
                f"{subject.target_type.value} {subject.target_id} belongs to a different Case"
            )
