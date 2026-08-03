"""Application service for the Knowledge Reference capture use case
(DO-IMP-003).

**Corrected per docs/atlas_domain_object_architecture/
Knowledge-Reference-Pre-Commit-Architecture-Review.md, Outcome 2;
widened per docs/atlas_domain_object_architecture/
Reference-Validation-Availability-Implementation-Design.md; widened
again to include Reasoning Trace per the Reasoning Trace Implementation
Design's own Section 34 follow-on classification.**

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
of them is removed, narrowed, or reinterpreted here. **All six now also
have present capture availability**: each has both INV-005 (prior
acceptance, via a working, accepted-instance repository) and INV-004
(same-Case membership, via a `case_id` field) positively establishable.
Reasoning Trace's own package (DO-IMP-009) supplied its accepted-
instance repository, closing the one remaining gap.

`TargetTypeUnavailableError` is retained for structural symmetry with
the currently-enabled-set check, but is not presently reachable for any
adopted type — this is the deliberate, forced consequence of every
member of the closed `DomainObjectType` set now having a working
repository, not a defect to be cleaned up here.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.judgment.repository import JudgmentRepository
from atlas.core.domain.judgment.value_objects import JudgmentId
from atlas.core.domain.knowledge_reference.entity import KnowledgeReference
from atlas.core.domain.knowledge_reference.exceptions import (
    CrossCaseTargetError,
    KnowledgeReferenceNotFoundError,
    TargetNotFoundError,
    TargetTypeUnavailableError,
)
from atlas.core.domain.knowledge_reference.repository import KnowledgeReferenceRepository
from atlas.core.domain.knowledge_reference.value_objects import KnowledgeReferenceId
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.domain.observation.value_objects import ObservationId
from atlas.core.domain.outcome.repository import OutcomeRepository
from atlas.core.domain.outcome.value_objects import OutcomeId
from atlas.core.domain.reasoning_trace.repository import ReasoningTraceRepository
from atlas.core.domain.reasoning_trace.value_objects import ReasoningTraceId
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference

_CURRENTLY_CAPTURE_ENABLED_TARGET_TYPES = frozenset(
    {
        DomainObjectType.KNOWLEDGE_REFERENCE,
        DomainObjectType.OBSERVATION,
        DomainObjectType.JUDGMENT,
        DomainObjectType.DECISION,
        DomainObjectType.OUTCOME,
        DomainObjectType.REASONING_TRACE,
    }
)


@dataclass(frozen=True)
class CaptureKnowledgeReferenceRequest:
    case_id: uuid.UUID
    target_type: DomainObjectType
    target_id: uuid.UUID


class KnowledgeReferenceService:
    def __init__(
        self,
        repository: KnowledgeReferenceRepository,
        observation_repository: ObservationRepository,
        judgment_repository: JudgmentRepository,
        decision_repository: DecisionRepository,
        outcome_repository: OutcomeRepository,
        reasoning_trace_repository: ReasoningTraceRepository,
    ) -> None:
        self._knowledge_references = repository
        self._observations = observation_repository
        self._judgments = judgment_repository
        self._decisions = decision_repository
        self._outcomes = outcome_repository
        self._reasoning_traces = reasoning_trace_repository

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

    def list_all(self) -> list[KnowledgeReference]:
        return self._knowledge_references.list_all()

    def delete(self, knowledge_reference_id: KnowledgeReferenceId) -> None:
        if self._knowledge_references.get(knowledge_reference_id) is None:
            raise KnowledgeReferenceNotFoundError(
                f"No Knowledge Reference found with id {knowledge_reference_id}"
            )
        self._knowledge_references.delete(knowledge_reference_id)

    def _verify_target(
        self, *, case_id: CaseId, target_type: DomainObjectType, target_id: uuid.UUID
    ) -> None:
        if target_type not in _CURRENTLY_CAPTURE_ENABLED_TARGET_TYPES:
            raise TargetTypeUnavailableError(
                f"{target_type.value} is a canonical, reference-eligible target type "
                f"(OE-002 §5.2), but Knowledge Reference capture cannot currently "
                f"establish every applicable invariant for it"
            )

        if target_type is DomainObjectType.OBSERVATION:
            existing = self._observations.get(ObservationId(target_id))
        elif target_type is DomainObjectType.JUDGMENT:
            existing = self._judgments.get(JudgmentId(target_id))
        elif target_type is DomainObjectType.DECISION:
            existing = self._decisions.get(DecisionId(target_id))
        elif target_type is DomainObjectType.OUTCOME:
            existing = self._outcomes.get(OutcomeId(target_id))
        elif target_type is DomainObjectType.REASONING_TRACE:
            existing = self._reasoning_traces.get(ReasoningTraceId(target_id))
        else:
            existing = self._knowledge_references.get(KnowledgeReferenceId(target_id))

        if existing is None:
            raise TargetNotFoundError(f"No accepted {target_type.value} found with id {target_id}")
        if existing.case_id != case_id:
            raise CrossCaseTargetError(
                f"{target_type.value} {target_id} belongs to a different Case"
            )
