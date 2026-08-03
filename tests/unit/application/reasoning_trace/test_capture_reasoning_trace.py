"""Application-layer tests for ReasoningTraceService (DO-IMP-009).

Per docs/atlas_domain_object_architecture/
Reasoning-Trace-Implementation-Design.md, Sections 28/29/37: all six
adopted Domain Object types (Observation, Knowledge Reference,
Reasoning Trace, Judgment, Decision, Outcome) are immediately eligible
supporting-object types — no `_CURRENTLY_CAPTURE_ENABLED_...` gate and
no `TargetTypeUnavailableError`-equivalent exists for this package.

Every test that needs a pre-existing accepted supporting object seeds
one directly via that type's own domain factory + repository `add()`
(bypassing every service's own referential validation entirely, exactly
as Knowledge Reference's own test suite already does), then exercises
the actual unit under test — `ReasoningTraceService` — against that
seed.

Exercises the service against real (in-memory) SQLite repositories, not
fakes, matching the convention used elsewhere in this codebase — except
for one dedicated test proving "empty collection rejected before any
repository lookup," which the design's own Section 37 explicitly
authorizes verifying via a counting test double, since no real
repository exposes a call count.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool

from atlas.core.application.reasoning_trace.capture_reasoning_trace import (
    CaptureReasoningTraceRequest,
    ReasoningTraceService,
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
from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.value_objects import Statement as ObservationStatement
from atlas.core.domain.observation.value_objects import Subject as ObservationSubject
from atlas.core.domain.outcome.entity import Outcome
from atlas.core.domain.outcome.value_objects import Statement as OutcomeStatement
from atlas.core.domain.reasoning_trace.entity import ReasoningTrace
from atlas.core.domain.reasoning_trace.exceptions import (
    CrossCaseTargetError,
    EmptySupportError,
    ReasoningTraceNotFoundError,
    TargetNotFoundError,
)
from atlas.core.domain.reasoning_trace.value_objects import ReasoningTraceId
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
    reasoning_traces_table,
)

_ALL_SIX_TARGET_TYPES = (
    DomainObjectType.OBSERVATION,
    DomainObjectType.KNOWLEDGE_REFERENCE,
    DomainObjectType.REASONING_TRACE,
    DomainObjectType.JUDGMENT,
    DomainObjectType.DECISION,
    DomainObjectType.OUTCOME,
)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_reasoning_trace_tables(eng)
    create_observation_table(eng)
    create_knowledge_reference_table(eng)
    create_judgment_table(eng)
    create_decision_table(eng)
    create_outcome_table(eng)
    return eng


@pytest.fixture
def repository(engine):
    return SqlAlchemyReasoningTraceRepository(engine)


@pytest.fixture
def observation_repository(engine):
    return SqlAlchemyObservationRepository(engine)


@pytest.fixture
def knowledge_reference_repository(engine):
    return SqlAlchemyKnowledgeReferenceRepository(engine)


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
def service(
    repository,
    observation_repository,
    knowledge_reference_repository,
    judgment_repository,
    decision_repository,
    outcome_repository,
):
    return ReasoningTraceService(
        repository,
        observation_repository,
        knowledge_reference_repository,
        judgment_repository,
        decision_repository,
        outcome_repository,
    )


def _seed_target(
    target_type: DomainObjectType,
    *,
    observation_repository,
    knowledge_reference_repository,
    judgment_repository,
    decision_repository,
    outcome_repository,
    reasoning_trace_repository,
    case_id: uuid.UUID,
) -> uuid.UUID:
    """Construct and persist an accepted instance of `target_type`
    directly into its own repository, bypassing every service's own
    validation — the only way each supporting-object type can exist to
    be referenced by a real, service-validated Reasoning Trace capture.
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
    if target_type is DomainObjectType.KNOWLEDGE_REFERENCE:
        seed = KnowledgeReference.capture(
            case_id=CaseId(case_id),
            target=TypedDomainObjectReference(
                target_type=DomainObjectType.OBSERVATION, target_id=uuid.uuid4()
            ),
        )
        knowledge_reference_repository.add(seed)
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
    if target_type is DomainObjectType.JUDGMENT:
        seed = Judgment.capture(
            case_id=CaseId(case_id), characterization=Characterization("a settled assessment")
        )
        judgment_repository.add(seed)
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
        rows = connection.execute(select(reasoning_traces_table)).mappings().all()
    return {row["reasoning_trace_id"] for row in rows}


class TestSuccessfulCaptureAgainstEverySupportedType:
    @pytest.mark.parametrize("target_type", _ALL_SIX_TARGET_TYPES)
    def test_captures_against_an_existing_same_case_target(
        self,
        service,
        observation_repository,
        knowledge_reference_repository,
        judgment_repository,
        decision_repository,
        outcome_repository,
        repository,
        target_type,
    ):
        case_id = uuid.uuid4()
        target_id = _seed_target(
            target_type,
            observation_repository=observation_repository,
            knowledge_reference_repository=knowledge_reference_repository,
            judgment_repository=judgment_repository,
            decision_repository=decision_repository,
            outcome_repository=outcome_repository,
            reasoning_trace_repository=repository,
            case_id=case_id,
        )
        support = TypedDomainObjectReference(target_type=target_type, target_id=target_id)
        captured = service.capture(
            CaptureReasoningTraceRequest(case_id=case_id, supports=[support])
        )
        assert captured.supports == frozenset({support})


class TestPriorAcceptance:
    @pytest.mark.parametrize("target_type", _ALL_SIX_TARGET_TYPES)
    def test_rejects_a_nonexistent_target(self, service, target_type):
        with pytest.raises(TargetNotFoundError):
            service.capture(
                CaptureReasoningTraceRequest(
                    case_id=uuid.uuid4(),
                    supports=[
                        TypedDomainObjectReference(target_type=target_type, target_id=uuid.uuid4())
                    ],
                )
            )

    def test_no_reasoning_trace_is_persisted_after_rejection(self, service, repository):
        with pytest.raises(TargetNotFoundError):
            service.capture(
                CaptureReasoningTraceRequest(
                    case_id=uuid.uuid4(),
                    supports=[
                        TypedDomainObjectReference(
                            target_type=DomainObjectType.OBSERVATION, target_id=uuid.uuid4()
                        )
                    ],
                )
            )
        assert _row_ids(repository) == set()


class TestSameCase:
    @pytest.mark.parametrize("target_type", _ALL_SIX_TARGET_TYPES)
    def test_rejects_a_target_from_a_different_case(
        self,
        service,
        observation_repository,
        knowledge_reference_repository,
        judgment_repository,
        decision_repository,
        outcome_repository,
        repository,
        target_type,
    ):
        target_id = _seed_target(
            target_type,
            observation_repository=observation_repository,
            knowledge_reference_repository=knowledge_reference_repository,
            judgment_repository=judgment_repository,
            decision_repository=decision_repository,
            outcome_repository=outcome_repository,
            reasoning_trace_repository=repository,
            case_id=uuid.uuid4(),  # its own random Case
        )
        with pytest.raises(CrossCaseTargetError):
            service.capture(
                CaptureReasoningTraceRequest(
                    case_id=uuid.uuid4(),  # deliberately a different Case
                    supports=[
                        TypedDomainObjectReference(target_type=target_type, target_id=target_id)
                    ],
                )
            )

    def test_no_reasoning_trace_is_persisted_after_cross_case_rejection(
        self, service, observation_repository, repository
    ):
        case_id = uuid.uuid4()
        seed = Observation.capture(
            case_id=CaseId(case_id),
            subject=ObservationSubject("Semiconductor sector"),
            statement=ObservationStatement("Capex guidance raised."),
            observed_at=datetime.now(timezone.utc),
        )
        observation_repository.add(seed)
        before_ids = _row_ids(repository)
        with pytest.raises(CrossCaseTargetError):
            service.capture(
                CaptureReasoningTraceRequest(
                    case_id=uuid.uuid4(),
                    supports=[
                        TypedDomainObjectReference(
                            target_type=DomainObjectType.OBSERVATION, target_id=seed.id.value
                        )
                    ],
                )
            )
        assert _row_ids(repository) == before_ids


class TestMultipleSupportsAcrossDifferentTypes:
    def test_captures_with_supports_of_several_different_types(
        self,
        service,
        observation_repository,
        judgment_repository,
        decision_repository,
        repository,
    ):
        case_id = uuid.uuid4()
        observation_id = _seed_target(
            DomainObjectType.OBSERVATION,
            observation_repository=observation_repository,
            knowledge_reference_repository=None,
            judgment_repository=judgment_repository,
            decision_repository=decision_repository,
            outcome_repository=None,
            reasoning_trace_repository=repository,
            case_id=case_id,
        )
        judgment_id = _seed_target(
            DomainObjectType.JUDGMENT,
            observation_repository=observation_repository,
            knowledge_reference_repository=None,
            judgment_repository=judgment_repository,
            decision_repository=decision_repository,
            outcome_repository=None,
            reasoning_trace_repository=repository,
            case_id=case_id,
        )
        supports = [
            TypedDomainObjectReference(
                target_type=DomainObjectType.OBSERVATION, target_id=observation_id
            ),
            TypedDomainObjectReference(
                target_type=DomainObjectType.JUDGMENT, target_id=judgment_id
            ),
        ]
        captured = service.capture(CaptureReasoningTraceRequest(case_id=case_id, supports=supports))
        assert captured.supports == frozenset(supports)


class TestOneInvalidSupportAmongValidSupports:
    def test_rejects_and_persists_nothing_when_one_support_is_invalid(
        self, service, observation_repository, repository
    ):
        case_id = uuid.uuid4()
        observation_id = _seed_target(
            DomainObjectType.OBSERVATION,
            observation_repository=observation_repository,
            knowledge_reference_repository=None,
            judgment_repository=None,
            decision_repository=None,
            outcome_repository=None,
            reasoning_trace_repository=repository,
            case_id=case_id,
        )
        supports = [
            TypedDomainObjectReference(
                target_type=DomainObjectType.OBSERVATION, target_id=observation_id
            ),
            TypedDomainObjectReference(
                target_type=DomainObjectType.JUDGMENT, target_id=uuid.uuid4()
            ),
        ]
        with pytest.raises(TargetNotFoundError):
            service.capture(CaptureReasoningTraceRequest(case_id=case_id, supports=supports))
        assert _row_ids(repository) == set()


class TestDuplicateInputReferencesCollapse:
    def test_the_same_reference_supplied_twice_succeeds_with_one_support(
        self, service, observation_repository, repository
    ):
        case_id = uuid.uuid4()
        observation_id = _seed_target(
            DomainObjectType.OBSERVATION,
            observation_repository=observation_repository,
            knowledge_reference_repository=None,
            judgment_repository=None,
            decision_repository=None,
            outcome_repository=None,
            reasoning_trace_repository=repository,
            case_id=case_id,
        )
        support = TypedDomainObjectReference(
            target_type=DomainObjectType.OBSERVATION, target_id=observation_id
        )
        captured = service.capture(
            CaptureReasoningTraceRequest(case_id=case_id, supports=[support, support])
        )
        assert captured.supports == frozenset({support})


class TestFirstReasoningTraceInACaseSupportedByANonTraceObject:
    def test_succeeds_with_no_special_root_eligible_handling(
        self, service, observation_repository, repository
    ):
        # Non-root-eligibility (INV-012) is naturally satisfied, not
        # specially handled: the very first accepted Domain Object in a
        # Case simply cannot be a Reasoning Trace, since nothing exists
        # yet to support it.
        case_id = uuid.uuid4()
        observation_id = _seed_target(
            DomainObjectType.OBSERVATION,
            observation_repository=observation_repository,
            knowledge_reference_repository=None,
            judgment_repository=None,
            decision_repository=None,
            outcome_repository=None,
            reasoning_trace_repository=repository,
            case_id=case_id,
        )
        captured = service.capture(
            CaptureReasoningTraceRequest(
                case_id=case_id,
                supports=[
                    TypedDomainObjectReference(
                        target_type=DomainObjectType.OBSERVATION, target_id=observation_id
                    )
                ],
            )
        )
        assert captured is not None


class TestLaterReasoningTraceSupportedByAnAcceptedReasoningTrace:
    def test_a_second_trace_may_cite_the_first_as_support(self, service, repository):
        case_id = uuid.uuid4()
        first_support = TypedDomainObjectReference(
            target_type=DomainObjectType.OBSERVATION, target_id=uuid.uuid4()
        )
        # Seed the first Reasoning Trace directly (bypassing the
        # service, since nothing yet exists to satisfy its own
        # supports).
        first = ReasoningTrace.capture(case_id=CaseId(case_id), supports=frozenset({first_support}))
        repository.add(first)

        second = service.capture(
            CaptureReasoningTraceRequest(
                case_id=case_id,
                supports=[
                    TypedDomainObjectReference(
                        target_type=DomainObjectType.REASONING_TRACE, target_id=first.id.value
                    )
                ],
            )
        )
        assert second.supports == frozenset(
            {
                TypedDomainObjectReference(
                    target_type=DomainObjectType.REASONING_TRACE, target_id=first.id.value
                )
            }
        )
        assert second.id != first.id


class TestLiteralSelfReferenceCannotSatisfyPriorAcceptance:
    def test_a_brand_new_candidate_cannot_cite_an_id_that_is_not_yet_accepted(self, service):
        # A candidate Reasoning Trace has no id until construction
        # succeeds (Section 28 of the design) — so it is structurally
        # impossible to supply "its own" id as a support in advance.
        # Citing any not-yet-accepted id (including one nobody has ever
        # assigned) fails exactly like any other missing target.
        never_accepted_id = uuid.uuid4()
        with pytest.raises(TargetNotFoundError):
            service.capture(
                CaptureReasoningTraceRequest(
                    case_id=uuid.uuid4(),
                    supports=[
                        TypedDomainObjectReference(
                            target_type=DomainObjectType.REASONING_TRACE,
                            target_id=never_accepted_id,
                        )
                    ],
                )
            )


class TestEmptySupportCollectionRejectedBeforeAnyLookup:
    def test_raises_empty_support_error(self, service):
        with pytest.raises(EmptySupportError):
            service.capture(CaptureReasoningTraceRequest(case_id=uuid.uuid4(), supports=[]))

    def test_no_repository_lookup_occurs_for_an_empty_collection(
        self,
        observation_repository,
        knowledge_reference_repository,
        judgment_repository,
        decision_repository,
        outcome_repository,
    ):
        class _CountingRepository:
            def __init__(self):
                self.get_calls = 0

            def add(self, _entity):
                raise AssertionError("add() must not be called for a rejected capture")

            def get(self, _id):
                self.get_calls += 1
                return None

        counting_repository = _CountingRepository()
        service = ReasoningTraceService(
            counting_repository,
            observation_repository,
            knowledge_reference_repository,
            judgment_repository,
            decision_repository,
            outcome_repository,
        )
        with pytest.raises(EmptySupportError):
            service.capture(CaptureReasoningTraceRequest(case_id=uuid.uuid4(), supports=[]))
        assert counting_repository.get_calls == 0


class TestDeterministicErrorSelection:
    def test_the_same_invalid_input_always_reports_the_same_violation(self, service):
        supports = [
            TypedDomainObjectReference(
                target_type=DomainObjectType.OBSERVATION, target_id=uuid.uuid4()
            ),
            TypedDomainObjectReference(
                target_type=DomainObjectType.JUDGMENT, target_id=uuid.uuid4()
            ),
        ]
        request = CaptureReasoningTraceRequest(case_id=uuid.uuid4(), supports=supports)

        first_message = None
        for _ in range(3):
            with pytest.raises(TargetNotFoundError) as excinfo:
                service.capture(request)
            if first_message is None:
                first_message = str(excinfo.value)
            else:
                assert str(excinfo.value) == first_message

    def test_the_reported_violation_matches_the_stable_sort_order(self, service):
        # Sorted by (target_type.value, str(target_id)): "Judgment" sorts
        # before "Observation" alphabetically, so the Judgment support's
        # violation must be the one reported, regardless of input order.
        observation_support = TypedDomainObjectReference(
            target_type=DomainObjectType.OBSERVATION, target_id=uuid.uuid4()
        )
        judgment_support = TypedDomainObjectReference(
            target_type=DomainObjectType.JUDGMENT, target_id=uuid.uuid4()
        )
        request = CaptureReasoningTraceRequest(
            case_id=uuid.uuid4(), supports=[observation_support, judgment_support]
        )
        with pytest.raises(TargetNotFoundError) as excinfo:
            service.capture(request)
        assert "Judgment" in str(excinfo.value)
        assert str(judgment_support.target_id) in str(excinfo.value)


class TestRetrieveById:
    def test_returns_the_captured_reasoning_trace(
        self, service, observation_repository, repository
    ):
        case_id = uuid.uuid4()
        observation_id = _seed_target(
            DomainObjectType.OBSERVATION,
            observation_repository=observation_repository,
            knowledge_reference_repository=None,
            judgment_repository=None,
            decision_repository=None,
            outcome_repository=None,
            reasoning_trace_repository=repository,
            case_id=case_id,
        )
        captured = service.capture(
            CaptureReasoningTraceRequest(
                case_id=case_id,
                supports=[
                    TypedDomainObjectReference(
                        target_type=DomainObjectType.OBSERVATION, target_id=observation_id
                    )
                ],
            )
        )
        assert service.get(captured.id) == captured

    def test_unknown_reasoning_trace_is_rejected(self, service):
        with pytest.raises(ReasoningTraceNotFoundError):
            service.get(ReasoningTraceId())


class TestListAll:
    def test_returns_every_captured_trace(self, service, observation_repository, repository):
        case_id = uuid.uuid4()
        observation_id = _seed_target(
            DomainObjectType.OBSERVATION,
            observation_repository=observation_repository,
            knowledge_reference_repository=None,
            judgment_repository=None,
            decision_repository=None,
            outcome_repository=None,
            reasoning_trace_repository=repository,
            case_id=case_id,
        )
        support = [
            TypedDomainObjectReference(
                target_type=DomainObjectType.OBSERVATION, target_id=observation_id
            )
        ]
        first = service.capture(CaptureReasoningTraceRequest(case_id=case_id, supports=support))
        second = service.capture(CaptureReasoningTraceRequest(case_id=case_id, supports=support))
        assert {trace.id for trace in service.list_all()} == {first.id, second.id}

    def test_empty_initially(self, service):
        assert service.list_all() == []


class TestDelete:
    def test_delete_removes_the_trace(self, service, observation_repository, repository):
        case_id = uuid.uuid4()
        observation_id = _seed_target(
            DomainObjectType.OBSERVATION,
            observation_repository=observation_repository,
            knowledge_reference_repository=None,
            judgment_repository=None,
            decision_repository=None,
            outcome_repository=None,
            reasoning_trace_repository=repository,
            case_id=case_id,
        )
        captured = service.capture(
            CaptureReasoningTraceRequest(
                case_id=case_id,
                supports=[
                    TypedDomainObjectReference(
                        target_type=DomainObjectType.OBSERVATION, target_id=observation_id
                    )
                ],
            )
        )
        service.delete(captured.id)
        with pytest.raises(ReasoningTraceNotFoundError):
            service.get(captured.id)

    def test_delete_unknown_trace_is_rejected(self, service):
        with pytest.raises(ReasoningTraceNotFoundError):
            service.delete(ReasoningTraceId())


class TestServiceDependsOnAllSixRepositories:
    def test_service_depends_on_exactly_its_six_repositories(self):
        import inspect

        signature = inspect.signature(ReasoningTraceService.__init__)
        assert list(signature.parameters) == [
            "self",
            "repository",
            "observation_repository",
            "knowledge_reference_repository",
            "judgment_repository",
            "decision_repository",
            "outcome_repository",
        ]
