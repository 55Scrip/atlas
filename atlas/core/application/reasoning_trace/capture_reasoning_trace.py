"""Application service for the Reasoning Trace capture use case (DO-IMP-009).

Implements exactly the validation sequence committed in
docs/atlas_domain_object_architecture/
Reasoning-Trace-Implementation-Design.md, Section 28:

1. Receive `case_id` and a collection of support references.
2. Collapse into a `frozenset[TypedDomainObjectReference]` — exact
   duplicates collapse via ordinary set construction.
3. Reject an empty collection with `EmptySupportError` before any
   repository is consulted.
4. Sort the distinct references by `(target_type.value, str(target_id))`
   — a purely technical device for reproducible, deterministic error
   selection. This does not make support order semantic: the persisted
   and reconstructed representation remains an unordered set.
5. Iterate the sorted references in order, dispatching by `target_type`
   to the matching repository.
6. Raise `TargetNotFoundError` on the first missing target.
7. Raise `CrossCaseTargetError` on the first cross-Case target.
8. Construct nothing until every reference has passed.
9. Persist exactly one Reasoning Trace, atomically (parent + support
   rows in one transaction — see
   `atlas/core/infrastructure/persistence/reasoning_trace/
   sqlalchemy_repository.py`).

Per Section 27/29 of the design: unlike Knowledge Reference and
Judgment, no `_CURRENTLY_CAPTURE_ENABLED_...` frozenset and no
`TargetTypeUnavailableError`-equivalent gate exists here. Reasoning
Trace is implemented last among the six adopted Domain Object types —
Observation, Knowledge Reference, Judgment, Decision, and Outcome each
already have a working, accepted-instance repository and a `case_id`,
and Reasoning Trace's own repository is created as part of this same
package. All six adopted types are immediately eligible supporting-
object types.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.judgment.repository import JudgmentRepository
from atlas.core.domain.judgment.value_objects import JudgmentId
from atlas.core.domain.knowledge_reference.repository import KnowledgeReferenceRepository
from atlas.core.domain.knowledge_reference.value_objects import KnowledgeReferenceId
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.domain.observation.value_objects import ObservationId
from atlas.core.domain.outcome.repository import OutcomeRepository
from atlas.core.domain.outcome.value_objects import OutcomeId
from atlas.core.domain.reasoning_trace.entity import ReasoningTrace
from atlas.core.domain.reasoning_trace.exceptions import (
    CrossCaseTargetError,
    EmptySupportError,
    ReasoningTraceNotFoundError,
    TargetNotFoundError,
)
from atlas.core.domain.reasoning_trace.repository import ReasoningTraceRepository
from atlas.core.domain.reasoning_trace.value_objects import ReasoningTraceId
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference


@dataclass(frozen=True)
class CaptureReasoningTraceRequest:
    case_id: uuid.UUID
    supports: Sequence[TypedDomainObjectReference]


class ReasoningTraceService:
    def __init__(
        self,
        repository: ReasoningTraceRepository,
        observation_repository: ObservationRepository,
        knowledge_reference_repository: KnowledgeReferenceRepository,
        judgment_repository: JudgmentRepository,
        decision_repository: DecisionRepository,
        outcome_repository: OutcomeRepository,
    ) -> None:
        self._reasoning_traces = repository
        self._observations = observation_repository
        self._knowledge_references = knowledge_reference_repository
        self._judgments = judgment_repository
        self._decisions = decision_repository
        self._outcomes = outcome_repository

    def capture(self, request: CaptureReasoningTraceRequest) -> ReasoningTrace:
        case_id = CaseId(request.case_id)
        supports = frozenset(request.supports)

        if len(supports) == 0:
            raise EmptySupportError(
                "A Reasoning Trace requires at least one supporting Domain Object (INV-013)"
            )

        for support in sorted(
            supports, key=lambda reference: (reference.target_type.value, str(reference.target_id))
        ):
            self._verify_support(case_id=case_id, support=support)

        reasoning_trace = ReasoningTrace.capture(case_id=case_id, supports=supports)
        self._reasoning_traces.add(reasoning_trace)
        return reasoning_trace

    def get(self, reasoning_trace_id: ReasoningTraceId) -> ReasoningTrace:
        reasoning_trace = self._reasoning_traces.get(reasoning_trace_id)
        if reasoning_trace is None:
            raise ReasoningTraceNotFoundError(
                f"No Reasoning Trace found with id {reasoning_trace_id}"
            )
        return reasoning_trace

    def list_all(self) -> list[ReasoningTrace]:
        return self._reasoning_traces.list_all()

    def delete(self, reasoning_trace_id: ReasoningTraceId) -> None:
        if self._reasoning_traces.get(reasoning_trace_id) is None:
            raise ReasoningTraceNotFoundError(
                f"No Reasoning Trace found with id {reasoning_trace_id}"
            )
        self._reasoning_traces.delete(reasoning_trace_id)

    def _verify_support(self, *, case_id: CaseId, support: TypedDomainObjectReference) -> None:
        target_type = support.target_type
        target_id = support.target_id

        if target_type is DomainObjectType.OBSERVATION:
            existing = self._observations.get(ObservationId(target_id))
        elif target_type is DomainObjectType.KNOWLEDGE_REFERENCE:
            existing = self._knowledge_references.get(KnowledgeReferenceId(target_id))
        elif target_type is DomainObjectType.JUDGMENT:
            existing = self._judgments.get(JudgmentId(target_id))
        elif target_type is DomainObjectType.DECISION:
            existing = self._decisions.get(DecisionId(target_id))
        elif target_type is DomainObjectType.OUTCOME:
            existing = self._outcomes.get(OutcomeId(target_id))
        else:
            existing = self._reasoning_traces.get(ReasoningTraceId(target_id))

        if existing is None:
            raise TargetNotFoundError(f"No accepted {target_type.value} found with id {target_id}")
        if existing.case_id != case_id:
            raise CrossCaseTargetError(
                f"{target_type.value} {target_id} belongs to a different Case"
            )
