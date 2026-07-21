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
Knowledge-Reference-Pre-Commit-Architecture-Review.md, Outcome 2), and
widened per docs/atlas_domain_object_architecture/
Reference-Validation-Availability-Implementation-Design.md. All six
`DomainObjectType` members remain fully canonical, reference-eligible
Domain Object types (OE-002 §5.4) as Judgment subjects — none is
removed, narrowed, or reinterpreted here. At the current repository
state, Knowledge Reference, Judgment, Observation, Decision, and Outcome
each have both INV-005 (prior acceptance, via a working, accepted-
instance repository) and INV-004 (same-Case membership, via a `case_id`
field) positively establishable. Only **Reasoning Trace** does not: it
has no accepted-instance repository at all, so prior acceptance
(INV-005) is not merely unverifiable but determinately violated for it
— no instance of that type has ever been accepted anywhere in this
system.

Capture against Reasoning Trace is rejected with
`TargetTypeUnavailableError`. Capture against it becomes available,
with no change to Judgment's own schema or API contract, once its own
prerequisite work lands.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.decision.value_objects import DecisionId
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
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.domain.observation.value_objects import ObservationId
from atlas.core.domain.outcome.repository import OutcomeRepository
from atlas.core.domain.outcome.value_objects import OutcomeId
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference

_CURRENTLY_CAPTURE_ENABLED_SUBJECT_TARGET_TYPES = frozenset(
    {
        DomainObjectType.KNOWLEDGE_REFERENCE,
        DomainObjectType.JUDGMENT,
        DomainObjectType.OBSERVATION,
        DomainObjectType.DECISION,
        DomainObjectType.OUTCOME,
    }
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
        observation_repository: ObservationRepository,
        decision_repository: DecisionRepository,
        outcome_repository: OutcomeRepository,
    ) -> None:
        self._judgments = repository
        self._knowledge_references = knowledge_reference_repository
        self._observations = observation_repository
        self._decisions = decision_repository
        self._outcomes = outcome_repository

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
        elif subject.target_type is DomainObjectType.KNOWLEDGE_REFERENCE:
            existing = self._knowledge_references.get(KnowledgeReferenceId(subject.target_id))
        elif subject.target_type is DomainObjectType.OBSERVATION:
            existing = self._observations.get(ObservationId(subject.target_id))
        elif subject.target_type is DomainObjectType.DECISION:
            existing = self._decisions.get(DecisionId(subject.target_id))
        else:
            existing = self._outcomes.get(OutcomeId(subject.target_id))

        if existing is None:
            raise TargetNotFoundError(
                f"No accepted {subject.target_type.value} found with id {subject.target_id}"
            )
        if existing.case_id != case_id:
            raise CrossCaseTargetError(
                f"{subject.target_type.value} {subject.target_id} belongs to a different Case"
            )
