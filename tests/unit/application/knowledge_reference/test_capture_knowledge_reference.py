"""Application-layer tests for KnowledgeReferenceService (DO-IMP-003).

**Corrected per docs/atlas_domain_object_architecture/
Knowledge-Reference-Pre-Commit-Architecture-Review.md, Outcome 2;
widened per docs/atlas_domain_object_architecture/
Reference-Validation-Availability-Implementation-Design.md; widened
again to include Reasoning Trace per the Reasoning Trace Implementation
Design's own Section 34 follow-on classification**: capture is now
enabled for `DomainObjectType.KNOWLEDGE_REFERENCE`, `OBSERVATION`,
`JUDGMENT`, `DECISION`, `OUTCOME`, and `REASONING_TRACE` targets — all
six adopted types.

**A genuine consequence of the ontology, not a test artifact**: Knowledge
Reference has no internal-content alternative form (OE-002 §5.2 names
only the referential form), so `service.capture()` itself can never
produce the *first* accepted Domain Object in an empty Case — there is
nothing yet to target, regardless of which target type is used. Every
test below that needs a pre-existing accepted target seeds one directly
via that type's own domain factory + repository `add()` (bypassing every
service's own referential validation entirely, exactly as the
persistence-layer tests already do), then exercises the actual unit
under test — `KnowledgeReferenceService` — against that seed.

Exercises the service against a real (in-memory) SQLite repository, not
a fake, matching the convention used elsewhere in this codebase.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.knowledge_reference.capture_knowledge_reference import (
    CaptureKnowledgeReferenceRequest,
    KnowledgeReferenceService,
)
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.value_objects import (
    Confidence,
    DecisionType,
    InvestmentCase,
    UserId,
)
from atlas.core.domain.decision.value_objects import Subject as DecisionSubject
from atlas.core.domain.judgment.entity import Judgment
from atlas.core.domain.judgment.value_objects import Characterization
from atlas.core.domain.knowledge_reference.entity import KnowledgeReference
from atlas.core.domain.knowledge_reference.exceptions import (
    CrossCaseTargetError,
    KnowledgeReferenceNotFoundError,
    TargetNotFoundError,
)
from atlas.core.domain.knowledge_reference.value_objects import KnowledgeReferenceId
from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.value_objects import Statement as ObservationStatement
from atlas.core.domain.observation.value_objects import Subject as ObservationSubject
from atlas.core.domain.outcome.entity import Outcome
from atlas.core.domain.outcome.value_objects import Statement as OutcomeStatement
from atlas.core.domain.reasoning_trace.entity import ReasoningTrace
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.decision.table import create_decision_table
from atlas.core.infrastructure.persistence.judgment.sqlalchemy_repository import (
    SqlAlchemyJudgmentRepository,
)
from atlas.core.infrastructure.persistence.judgment.table import create_judgment_table
from atlas.core.infrastructure.persistence.knowledge_reference.sqlalchemy_repository import (
    SqlAlchemyKnowledgeReferenceRepository,
)
from atlas.core.infrastructure.persistence.knowledge_reference.table import (
    create_knowledge_reference_table,
    knowledge_references_table,
)
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
)
from atlas.core.infrastructure.persistence.observation.table import create_observation_table
from atlas.core.infrastructure.persistence.outcome.sqlalchemy_repository import (
    SqlAlchemyOutcomeRepository,
)
from atlas.core.infrastructure.persistence.outcome.table import create_outcome_table
from atlas.core.infrastructure.persistence.reasoning_trace.sqlalchemy_repository import (
    SqlAlchemyReasoningTraceRepository,
)
from atlas.core.infrastructure.persistence.reasoning_trace.table import (
    create_reasoning_trace_tables,
)

_NEWLY_ENABLED_TARGET_TYPES = (
    DomainObjectType.OBSERVATION,
    DomainObjectType.JUDGMENT,
    DomainObjectType.DECISION,
    DomainObjectType.OUTCOME,
    DomainObjectType.REASONING_TRACE,
)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_knowledge_reference_table(eng)
    create_observation_table(eng)
    create_judgment_table(eng)
    create_decision_table(eng)
    create_outcome_table(eng)
    create_reasoning_trace_tables(eng)
    return eng


@pytest.fixture
def repository(engine):
    return SqlAlchemyKnowledgeReferenceRepository(engine)


@pytest.fixture
def observation_repository(engine):
    return SqlAlchemyObservationRepository(engine)


@pytest.fixture
def judgment_repository(engine):
    return SqlAlchemyJudgmentRepository(engine)


@pytest.fixture
def decision_repository(engine):
    return SqlAlchemyDecisionRepository(engine)


@pytest.fixture
def outcome_repository(engine):
    return SqlAlchemyOutcomeRepository(engine)


@pytest.fixture
def reasoning_trace_repository(engine):
    return SqlAlchemyReasoningTraceRepository(engine)


@pytest.fixture
def service(
    repository,
    observation_repository,
    judgment_repository,
    decision_repository,
    outcome_repository,
    reasoning_trace_repository,
):
    return KnowledgeReferenceService(
        repository,
        observation_repository,
        judgment_repository,
        decision_repository,
        outcome_repository,
        reasoning_trace_repository,
    )


def _seed(repository, *, case_id: uuid.UUID | None = None) -> KnowledgeReference:
    """Directly construct and persist a Knowledge Reference, bypassing
    KnowledgeReferenceService's own referential validation — the only
    way any Knowledge Reference can exist to be targeted by the first
    real, service-validated capture in an otherwise-empty store.
    """
    seed = KnowledgeReference.capture(
        case_id=CaseId(case_id if case_id is not None else uuid.uuid4()),
        target=TypedDomainObjectReference(
            target_type=DomainObjectType.KNOWLEDGE_REFERENCE, target_id=uuid.uuid4()
        ),
    )
    repository.add(seed)
    return seed


def _seed_target(
    target_type: DomainObjectType,
    *,
    observation_repository,
    judgment_repository,
    decision_repository,
    outcome_repository,
    reasoning_trace_repository=None,
    case_id: uuid.UUID,
) -> uuid.UUID:
    """Construct and persist an accepted instance of `target_type` directly
    into its own repository, bypassing every service's own validation —
    the only way each newly-enabled target type can exist to be
    referenced by a real, service-validated Knowledge Reference capture.
    """
    now = datetime.now(timezone.utc)
    if target_type is DomainObjectType.OBSERVATION:
        seed = Observation.capture(
            case_id=CaseId(case_id),
            subject=ObservationSubject("Semiconductor sector"),
            statement=ObservationStatement("Capex guidance raised."),
            observed_at=now,
        )
        observation_repository.add(seed)
        return seed.id.value
    if target_type is DomainObjectType.JUDGMENT:
        seed = Judgment.capture(
            case_id=CaseId(case_id), characterization=Characterization("a settled assessment")
        )
        judgment_repository.add(seed)
        return seed.id.value
    if target_type is DomainObjectType.REASONING_TRACE:
        seed = ReasoningTrace.capture(
            case_id=CaseId(case_id),
            supports=frozenset(
                {
                    TypedDomainObjectReference(
                        target_type=DomainObjectType.OBSERVATION, target_id=uuid.uuid4()
                    )
                }
            ),
        )
        reasoning_trace_repository.add(seed)
        return seed.id.value
    if target_type is DomainObjectType.DECISION:
        seed = Decision.register(
            case_id=CaseId(case_id),
            user_id=UserId(uuid.uuid4()),
            decision_type=DecisionType.BUY,
            subject=DecisionSubject("NVIDIA"),
            investment_case=InvestmentCase("Demand is accelerating."),
            confidence=Confidence(80),
            decided_at=now,
        )
        decision_repository.add(seed)
        return seed.id.value
    seed = Outcome.capture(
        case_id=CaseId(case_id),
        decision_id=Decision.register(
            case_id=CaseId(case_id),
            user_id=UserId(uuid.uuid4()),
            decision_type=DecisionType.BUY,
            subject=DecisionSubject("NVIDIA"),
            investment_case=InvestmentCase("Demand is accelerating."),
            confidence=Confidence(80),
            decided_at=now,
        ).id,
        statement=OutcomeStatement("Revenue grew as expected."),
        occurred_at=now,
    )
    outcome_repository.add(seed)
    return seed.id.value


def _row_ids(repository) -> set[str]:
    with repository._engine.connect() as connection:
        from sqlalchemy import select

        rows = connection.execute(select(knowledge_references_table)).mappings().all()
    return {row["knowledge_reference_id"] for row in rows}


class TestSuccessfulCapture:
    def test_captures_against_a_previously_accepted_knowledge_reference_in_the_same_case(
        self, service, repository
    ):
        case_id = uuid.uuid4()
        seed = _seed(repository, case_id=case_id)
        captured = service.capture(
            CaptureKnowledgeReferenceRequest(
                case_id=case_id,
                target_type=DomainObjectType.KNOWLEDGE_REFERENCE,
                target_id=seed.id.value,
            )
        )
        assert captured.target.target_type is DomainObjectType.KNOWLEDGE_REFERENCE
        assert captured.target.target_id == seed.id.value

    def test_target_is_persisted_exactly(self, service, repository):
        case_id = uuid.uuid4()
        seed = _seed(repository, case_id=case_id)
        captured = service.capture(
            CaptureKnowledgeReferenceRequest(
                case_id=case_id,
                target_type=DomainObjectType.KNOWLEDGE_REFERENCE,
                target_id=seed.id.value,
            )
        )
        reloaded = repository.get(captured.id)
        assert reloaded.target.target_type is DomainObjectType.KNOWLEDGE_REFERENCE
        assert reloaded.target.target_id == seed.id.value

    def test_recorded_at_remains_acceptance_time(self, service, repository):
        case_id = uuid.uuid4()
        seed = _seed(repository, case_id=case_id)
        before = datetime.now(timezone.utc)
        captured = service.capture(
            CaptureKnowledgeReferenceRequest(
                case_id=case_id,
                target_type=DomainObjectType.KNOWLEDGE_REFERENCE,
                target_id=seed.id.value,
            )
        )
        after = datetime.now(timezone.utc)
        assert before <= captured.recorded_at <= after

    def test_a_third_knowledge_reference_may_target_an_earlier_accepted_one(
        self, service, repository
    ):
        case_id = uuid.uuid4()
        seed = _seed(repository, case_id=case_id)
        second = service.capture(
            CaptureKnowledgeReferenceRequest(
                case_id=case_id,
                target_type=DomainObjectType.KNOWLEDGE_REFERENCE,
                target_id=seed.id.value,
            )
        )
        third = service.capture(
            CaptureKnowledgeReferenceRequest(
                case_id=case_id,
                target_type=DomainObjectType.KNOWLEDGE_REFERENCE,
                target_id=seed.id.value,
            )
        )
        assert third.target.target_id == seed.id.value
        assert third.id != second.id


class TestPriorAcceptance:
    def test_rejects_a_nonexistent_knowledge_reference(self, service):
        with pytest.raises(TargetNotFoundError):
            service.capture(
                CaptureKnowledgeReferenceRequest(
                    case_id=uuid.uuid4(),
                    target_type=DomainObjectType.KNOWLEDGE_REFERENCE,
                    target_id=uuid.uuid4(),
                )
            )

    def test_no_knowledge_reference_is_persisted_after_rejection(self, service, repository):
        bogus_target_id = uuid.uuid4()
        with pytest.raises(TargetNotFoundError):
            service.capture(
                CaptureKnowledgeReferenceRequest(
                    case_id=uuid.uuid4(),
                    target_type=DomainObjectType.KNOWLEDGE_REFERENCE,
                    target_id=bogus_target_id,
                )
            )
        assert repository.get(KnowledgeReferenceId(bogus_target_id)) is None


class TestSameCase:
    def test_rejects_a_knowledge_reference_target_from_a_different_case(self, service, repository):
        seed = _seed(repository)  # its own random Case
        with pytest.raises(CrossCaseTargetError):
            service.capture(
                CaptureKnowledgeReferenceRequest(
                    case_id=uuid.uuid4(),  # deliberately a different Case
                    target_type=DomainObjectType.KNOWLEDGE_REFERENCE,
                    target_id=seed.id.value,
                )
            )

    def test_no_knowledge_reference_is_persisted_after_cross_case_rejection(
        self, service, repository
    ):
        seed = _seed(repository)
        before_ids = _row_ids(repository)
        with pytest.raises(CrossCaseTargetError):
            service.capture(
                CaptureKnowledgeReferenceRequest(
                    case_id=uuid.uuid4(),
                    target_type=DomainObjectType.KNOWLEDGE_REFERENCE,
                    target_id=seed.id.value,
                )
            )
        assert _row_ids(repository) == before_ids


class TestSuccessfulCaptureAgainstNewlyEnabledTargetTypes:
    @pytest.mark.parametrize("target_type", _NEWLY_ENABLED_TARGET_TYPES)
    def test_captures_against_an_existing_same_case_target(
        self,
        service,
        observation_repository,
        judgment_repository,
        decision_repository,
        outcome_repository,
        reasoning_trace_repository,
        target_type,
    ):
        case_id = uuid.uuid4()
        target_id = _seed_target(
            target_type,
            observation_repository=observation_repository,
            judgment_repository=judgment_repository,
            decision_repository=decision_repository,
            outcome_repository=outcome_repository,
            reasoning_trace_repository=reasoning_trace_repository,
            case_id=case_id,
        )
        captured = service.capture(
            CaptureKnowledgeReferenceRequest(
                case_id=case_id, target_type=target_type, target_id=target_id
            )
        )
        assert captured.target.target_type is target_type
        assert captured.target.target_id == target_id


class TestPriorAcceptanceForNewlyEnabledTargetTypes:
    @pytest.mark.parametrize("target_type", _NEWLY_ENABLED_TARGET_TYPES)
    def test_rejects_a_nonexistent_target(self, service, target_type):
        with pytest.raises(TargetNotFoundError):
            service.capture(
                CaptureKnowledgeReferenceRequest(
                    case_id=uuid.uuid4(), target_type=target_type, target_id=uuid.uuid4()
                )
            )


class TestSameCaseForNewlyEnabledTargetTypes:
    @pytest.mark.parametrize("target_type", _NEWLY_ENABLED_TARGET_TYPES)
    def test_rejects_a_target_from_a_different_case(
        self,
        service,
        observation_repository,
        judgment_repository,
        decision_repository,
        outcome_repository,
        reasoning_trace_repository,
        target_type,
    ):
        target_id = _seed_target(
            target_type,
            observation_repository=observation_repository,
            judgment_repository=judgment_repository,
            decision_repository=decision_repository,
            outcome_repository=outcome_repository,
            reasoning_trace_repository=reasoning_trace_repository,
            case_id=uuid.uuid4(),  # its own random Case
        )
        with pytest.raises(CrossCaseTargetError):
            service.capture(
                CaptureKnowledgeReferenceRequest(
                    case_id=uuid.uuid4(),  # deliberately a different Case
                    target_type=target_type,
                    target_id=target_id,
                )
            )


class TestAllSixTargetTypesAreCaptureEnabled:
    """All six adopted `DomainObjectType` members — including Reasoning
    Trace, following its own package (DO-IMP-009) and this availability
    widening — are now capture-enabled Knowledge Reference target types.
    Replaces the prior `TestCanonicalButCurrentlyUnavailableTargetTypes`
    class, which tested a condition that no longer holds for any
    adopted type.
    """

    def test_every_adopted_type_is_in_the_enabled_set(self):
        from atlas.core.application.knowledge_reference.capture_knowledge_reference import (
            _CURRENTLY_CAPTURE_ENABLED_TARGET_TYPES,
        )

        assert _CURRENTLY_CAPTURE_ENABLED_TARGET_TYPES == frozenset(DomainObjectType)

    def test_reasoning_trace_target_no_longer_raises_target_type_unavailable(
        self, service, reasoning_trace_repository
    ):
        case_id = uuid.uuid4()
        seed = ReasoningTrace.capture(
            case_id=CaseId(case_id),
            supports=frozenset(
                {
                    TypedDomainObjectReference(
                        target_type=DomainObjectType.OBSERVATION, target_id=uuid.uuid4()
                    )
                }
            ),
        )
        reasoning_trace_repository.add(seed)
        captured = service.capture(
            CaptureKnowledgeReferenceRequest(
                case_id=case_id,
                target_type=DomainObjectType.REASONING_TRACE,
                target_id=seed.id.value,
            )
        )
        assert captured.target.target_type is DomainObjectType.REASONING_TRACE
        assert captured.target.target_id == seed.id.value


class TestUnknownTargetTypeIsNotConflatedWithUnavailableTypes:
    def test_domain_object_type_itself_rejects_unknown_values_before_capture(self):
        # "Case" is not a member of DomainObjectType at all (the
        # ownership boundary, OE-002 §3.1 — not a Domain Object). This
        # is rejected by DomainObjectType.parse/the API schema layer,
        # never reaching KnowledgeReferenceService at all.
        from atlas.core.domain.shared.exceptions import UnknownDomainObjectTypeError

        with pytest.raises(UnknownDomainObjectTypeError):
            DomainObjectType.parse("Case")


class TestRetrieveById:
    def test_returns_the_captured_knowledge_reference(self, service, repository):
        case_id = uuid.uuid4()
        seed = _seed(repository, case_id=case_id)
        captured = service.capture(
            CaptureKnowledgeReferenceRequest(
                case_id=case_id,
                target_type=DomainObjectType.KNOWLEDGE_REFERENCE,
                target_id=seed.id.value,
            )
        )
        assert service.get(captured.id) == captured

    def test_unknown_knowledge_reference_is_rejected(self, service):
        with pytest.raises(KnowledgeReferenceNotFoundError):
            service.get(KnowledgeReferenceId())


class TestServiceDependencyExpansion:
    """Deliberately reverses the single-repository "dependency
    simplification" locked in by
    Knowledge-Reference-Pre-Commit-Architecture-Review.md, Outcome 2 —
    per docs/atlas_domain_object_architecture/
    Reference-Validation-Availability-Implementation-Design.md,
    cross-type reference validation against Observation, Judgment,
    Decision, Outcome, and (per this widening) Reasoning Trace
    genuinely requires their own repositories.
    """

    def test_service_depends_on_exactly_its_six_repositories(self):
        import inspect

        signature = inspect.signature(KnowledgeReferenceService.__init__)
        assert list(signature.parameters) == [
            "self",
            "repository",
            "observation_repository",
            "judgment_repository",
            "decision_repository",
            "outcome_repository",
            "reasoning_trace_repository",
        ]
