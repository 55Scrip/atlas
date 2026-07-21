"""Application-layer tests for JudgmentService (DO-IMP-004).

**Widened per docs/atlas_domain_object_architecture/
Reference-Validation-Availability-Implementation-Design.md**: capture
is now enabled for a subject targeting a Knowledge Reference, another
Judgment, an Observation, a Decision, or an Outcome. Reasoning Trace
remains fully canonical, reference-eligible (OE-002 §5.4) but is
currently rejected with `TargetTypeUnavailableError`, since it has no
accepted-instance repository at all — see `capture_judgment.py`'s own
module docstring for the precise reason.

Unlike Knowledge Reference, Judgment's internal-content form (no
subject) requires no pre-existing target at all, so `service.capture()`
can produce the very first accepted Domain Object in an empty Case
directly — no seeding helper is needed for that path. Tests exercising
the referential form still seed a pre-existing accepted target directly
via that type's own domain construction + repository insertion,
bypassing the service's own referential validation, exactly as the
Knowledge Reference test suite already does.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.judgment.capture_judgment import (
    CaptureJudgmentRequest,
    JudgmentService,
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
from atlas.core.domain.judgment.exceptions import (
    CrossCaseTargetError,
    JudgmentNotFoundError,
    TargetNotFoundError,
    TargetTypeUnavailableError,
)
from atlas.core.domain.judgment.value_objects import Characterization, JudgmentId
from atlas.core.domain.knowledge_reference.entity import KnowledgeReference
from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.value_objects import Statement as ObservationStatement
from atlas.core.domain.observation.value_objects import Subject as ObservationSubject
from atlas.core.domain.outcome.entity import Outcome
from atlas.core.domain.outcome.value_objects import Statement as OutcomeStatement
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

_CURRENTLY_UNAVAILABLE_TARGET_TYPES = (DomainObjectType.REASONING_TRACE,)

_NEWLY_ENABLED_TARGET_TYPES = (
    DomainObjectType.OBSERVATION,
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
    create_judgment_table(eng)
    create_knowledge_reference_table(eng)
    create_observation_table(eng)
    create_decision_table(eng)
    create_outcome_table(eng)
    return eng


@pytest.fixture
def judgment_repository(engine):
    return SqlAlchemyJudgmentRepository(engine)


@pytest.fixture
def knowledge_reference_repository(engine):
    return SqlAlchemyKnowledgeReferenceRepository(engine)


@pytest.fixture
def observation_repository(engine):
    return SqlAlchemyObservationRepository(engine)


@pytest.fixture
def decision_repository(engine):
    return SqlAlchemyDecisionRepository(engine)


@pytest.fixture
def outcome_repository(engine):
    return SqlAlchemyOutcomeRepository(engine)


@pytest.fixture
def service(
    judgment_repository,
    knowledge_reference_repository,
    observation_repository,
    decision_repository,
    outcome_repository,
):
    return JudgmentService(
        judgment_repository,
        knowledge_reference_repository,
        observation_repository,
        decision_repository,
        outcome_repository,
    )


def _seed_knowledge_reference(
    knowledge_reference_repository, *, case_id: uuid.UUID | None = None
) -> KnowledgeReference:
    seed = KnowledgeReference.capture(
        case_id=CaseId(case_id if case_id is not None else uuid.uuid4()),
        target=TypedDomainObjectReference(
            target_type=DomainObjectType.KNOWLEDGE_REFERENCE, target_id=uuid.uuid4()
        ),
    )
    knowledge_reference_repository.add(seed)
    return seed


def _seed_judgment(judgment_repository, *, case_id: uuid.UUID | None = None) -> Judgment:
    seed = Judgment.capture(
        case_id=CaseId(case_id if case_id is not None else uuid.uuid4()),
        characterization=Characterization("a prior settled characterization"),
    )
    judgment_repository.add(seed)
    return seed


def _seed_subject(
    target_type: DomainObjectType,
    *,
    observation_repository,
    decision_repository,
    outcome_repository,
    case_id: uuid.UUID,
) -> uuid.UUID:
    """Construct and persist an accepted instance of `target_type` directly
    into its own repository, bypassing every service's own validation —
    the only way each newly-enabled subject type can exist to be
    referenced by a real, service-validated Judgment capture.
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


class TestInternalContentFormRootEligibility:
    def test_captures_the_first_ever_domain_object_in_an_empty_case(self, service):
        # No seed of any kind: INV-012 permits the internal-content
        # form to be a Case's first accepted Domain Object.
        captured = service.capture(
            CaptureJudgmentRequest(
                case_id=uuid.uuid4(), characterization="first object in this Case"
            )
        )
        assert captured.subject is None
        assert str(captured.characterization) == "first object in this Case"

    def test_recorded_at_remains_acceptance_time(self, service):
        before = datetime.now(timezone.utc)
        captured = service.capture(
            CaptureJudgmentRequest(case_id=uuid.uuid4(), characterization="settled")
        )
        after = datetime.now(timezone.utc)
        assert before <= captured.recorded_at <= after


class TestReferentialFormAgainstKnowledgeReference:
    def test_captures_against_a_previously_accepted_knowledge_reference(
        self, service, knowledge_reference_repository
    ):
        case_id = uuid.uuid4()
        seed = _seed_knowledge_reference(knowledge_reference_repository, case_id=case_id)
        captured = service.capture(
            CaptureJudgmentRequest(
                case_id=case_id,
                characterization="relying on this knowledge",
                subject=TypedDomainObjectReference(
                    target_type=DomainObjectType.KNOWLEDGE_REFERENCE, target_id=seed.id.value
                ),
            )
        )
        assert captured.subject.target_type is DomainObjectType.KNOWLEDGE_REFERENCE
        assert captured.subject.target_id == seed.id.value

    def test_rejects_a_nonexistent_knowledge_reference_target(self, service):
        with pytest.raises(TargetNotFoundError):
            service.capture(
                CaptureJudgmentRequest(
                    case_id=uuid.uuid4(),
                    characterization="settled",
                    subject=TypedDomainObjectReference(
                        target_type=DomainObjectType.KNOWLEDGE_REFERENCE, target_id=uuid.uuid4()
                    ),
                )
            )

    def test_rejects_a_cross_case_knowledge_reference_target(
        self, service, knowledge_reference_repository
    ):
        seed = _seed_knowledge_reference(knowledge_reference_repository)  # its own random Case
        with pytest.raises(CrossCaseTargetError):
            service.capture(
                CaptureJudgmentRequest(
                    case_id=uuid.uuid4(),
                    characterization="settled",
                    subject=TypedDomainObjectReference(
                        target_type=DomainObjectType.KNOWLEDGE_REFERENCE, target_id=seed.id.value
                    ),
                )
            )


class TestReferentialFormAgainstJudgment:
    def test_captures_against_a_previously_accepted_judgment(self, service, judgment_repository):
        case_id = uuid.uuid4()
        seed = _seed_judgment(judgment_repository, case_id=case_id)
        captured = service.capture(
            CaptureJudgmentRequest(
                case_id=case_id,
                characterization="a Judgment about that earlier Judgment",
                subject=TypedDomainObjectReference(
                    target_type=DomainObjectType.JUDGMENT, target_id=seed.id.value
                ),
            )
        )
        assert captured.subject.target_type is DomainObjectType.JUDGMENT
        assert captured.subject.target_id == seed.id.value

    def test_rejects_a_nonexistent_judgment_target(self, service):
        with pytest.raises(TargetNotFoundError):
            service.capture(
                CaptureJudgmentRequest(
                    case_id=uuid.uuid4(),
                    characterization="settled",
                    subject=TypedDomainObjectReference(
                        target_type=DomainObjectType.JUDGMENT, target_id=uuid.uuid4()
                    ),
                )
            )

    def test_rejects_a_cross_case_judgment_target(self, service, judgment_repository):
        seed = _seed_judgment(judgment_repository)  # its own random Case
        with pytest.raises(CrossCaseTargetError):
            service.capture(
                CaptureJudgmentRequest(
                    case_id=uuid.uuid4(),
                    characterization="settled",
                    subject=TypedDomainObjectReference(
                        target_type=DomainObjectType.JUDGMENT, target_id=seed.id.value
                    ),
                )
            )

    def test_no_judgment_is_persisted_after_rejection(self, service, judgment_repository):
        bogus_target_id = uuid.uuid4()
        with pytest.raises(TargetNotFoundError):
            service.capture(
                CaptureJudgmentRequest(
                    case_id=uuid.uuid4(),
                    characterization="settled",
                    subject=TypedDomainObjectReference(
                        target_type=DomainObjectType.JUDGMENT, target_id=bogus_target_id
                    ),
                )
            )
        assert judgment_repository.get(JudgmentId(bogus_target_id)) is None


class TestReferentialFormAgainstNewlyEnabledTargetTypes:
    @pytest.mark.parametrize("target_type", _NEWLY_ENABLED_TARGET_TYPES)
    def test_captures_against_an_existing_same_case_subject(
        self, service, observation_repository, decision_repository, outcome_repository, target_type
    ):
        case_id = uuid.uuid4()
        target_id = _seed_subject(
            target_type,
            observation_repository=observation_repository,
            decision_repository=decision_repository,
            outcome_repository=outcome_repository,
            case_id=case_id,
        )
        captured = service.capture(
            CaptureJudgmentRequest(
                case_id=case_id,
                characterization="a Judgment about that earlier Domain Object",
                subject=TypedDomainObjectReference(target_type=target_type, target_id=target_id),
            )
        )
        assert captured.subject.target_type is target_type
        assert captured.subject.target_id == target_id

    @pytest.mark.parametrize("target_type", _NEWLY_ENABLED_TARGET_TYPES)
    def test_rejects_a_nonexistent_subject(self, service, target_type):
        with pytest.raises(TargetNotFoundError):
            service.capture(
                CaptureJudgmentRequest(
                    case_id=uuid.uuid4(),
                    characterization="settled",
                    subject=TypedDomainObjectReference(
                        target_type=target_type, target_id=uuid.uuid4()
                    ),
                )
            )

    @pytest.mark.parametrize("target_type", _NEWLY_ENABLED_TARGET_TYPES)
    def test_rejects_a_cross_case_subject(
        self, service, observation_repository, decision_repository, outcome_repository, target_type
    ):
        target_id = _seed_subject(
            target_type,
            observation_repository=observation_repository,
            decision_repository=decision_repository,
            outcome_repository=outcome_repository,
            case_id=uuid.uuid4(),  # its own random Case
        )
        with pytest.raises(CrossCaseTargetError):
            service.capture(
                CaptureJudgmentRequest(
                    case_id=uuid.uuid4(),  # deliberately a different Case
                    characterization="settled",
                    subject=TypedDomainObjectReference(
                        target_type=target_type, target_id=target_id
                    ),
                )
            )


class TestCanonicalButCurrentlyUnavailableTargetTypes:
    """Every one of these four target types is a fully adopted,
    canonical DomainObjectType member (OE-002 §5.4) — rejection here
    reflects only that Judgment capture cannot currently establish
    every applicable invariant for it, never that the type itself is
    unknown, invalid, or non-adopted.
    """

    @pytest.mark.parametrize("target_type", _CURRENTLY_UNAVAILABLE_TARGET_TYPES)
    def test_capture_rejects_it(self, service, target_type):
        with pytest.raises(TargetTypeUnavailableError):
            service.capture(
                CaptureJudgmentRequest(
                    case_id=uuid.uuid4(),
                    characterization="settled",
                    subject=TypedDomainObjectReference(
                        target_type=target_type, target_id=uuid.uuid4()
                    ),
                )
            )

    @pytest.mark.parametrize("target_type", _CURRENTLY_UNAVAILABLE_TARGET_TYPES)
    def test_the_error_does_not_claim_the_type_is_unknown_or_non_adopted(
        self, service, target_type
    ):
        with pytest.raises(TargetTypeUnavailableError) as excinfo:
            service.capture(
                CaptureJudgmentRequest(
                    case_id=uuid.uuid4(),
                    characterization="settled",
                    subject=TypedDomainObjectReference(
                        target_type=target_type, target_id=uuid.uuid4()
                    ),
                )
            )
        message = str(excinfo.value).lower()
        assert "unknown" not in message
        assert "invalid" not in message
        assert "canonical" in message or "reference-eligible" in message

    @pytest.mark.parametrize("target_type", _CURRENTLY_UNAVAILABLE_TARGET_TYPES)
    def test_no_judgment_is_persisted(self, service, judgment_repository, target_type):
        with pytest.raises(TargetTypeUnavailableError):
            service.capture(
                CaptureJudgmentRequest(
                    case_id=uuid.uuid4(),
                    characterization="settled",
                    subject=TypedDomainObjectReference(
                        target_type=target_type, target_id=uuid.uuid4()
                    ),
                )
            )
        with judgment_repository._engine.connect() as connection:
            from sqlalchemy import select

            from atlas.core.infrastructure.persistence.judgment.table import judgments_table

            rows = connection.execute(select(judgments_table)).mappings().all()
        assert rows == []


class TestRetrieveById:
    def test_returns_the_captured_judgment(self, service):
        captured = service.capture(
            CaptureJudgmentRequest(case_id=uuid.uuid4(), characterization="settled")
        )
        assert service.get(captured.id) == captured

    def test_unknown_judgment_is_rejected(self, service):
        with pytest.raises(JudgmentNotFoundError):
            service.get(JudgmentId())


class TestCharacterizationRemainsRequired:
    def test_rejects_blank_characterization_even_with_no_subject(self, service):
        from atlas.core.domain.judgment.exceptions import MissingCharacterizationError

        with pytest.raises(MissingCharacterizationError):
            service.capture(CaptureJudgmentRequest(case_id=uuid.uuid4(), characterization="   "))
