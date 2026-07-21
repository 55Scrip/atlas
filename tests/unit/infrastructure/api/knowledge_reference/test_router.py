"""API tests for the Knowledge Reference REST controller (DO-IMP-003).

**Corrected per docs/atlas_domain_object_architecture/
Knowledge-Reference-Pre-Commit-Architecture-Review.md, Outcome 2, and
widened per docs/atlas_domain_object_architecture/
Reference-Validation-Availability-Implementation-Design.md**: capture
is now enabled for `targetType` values `"KnowledgeReference"`,
`"Observation"`, `"Judgment"`, `"Decision"`, and `"Outcome"`.
`"ReasoningTrace"` remains rejected — it has no accepted-instance
repository at all anywhere in this codebase.

Since capture cannot itself produce the *first* accepted Domain Object
in an empty store (there is nothing yet to target — see the
application-layer test module's own docstring for the full argument),
tests that need a pre-existing accepted target seed one directly into
the shared repository instance the API's dependency override provides,
bypassing the API/service layers for setup only.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

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
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference
from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
from atlas.core.infrastructure.api.knowledge_reference.dependencies import (
    _get_judgment_repository,
    get_knowledge_reference_repository,
    get_outcome_repository,
)
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository
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

_CURRENTLY_UNAVAILABLE_TARGET_TYPES = ("ReasoningTrace",)

_NEWLY_ENABLED_TARGET_TYPES = ("Observation", "Judgment", "Decision", "Outcome")


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
    return eng


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
def context(
    engine, observation_repository, judgment_repository, decision_repository, outcome_repository
):
    repository = SqlAlchemyKnowledgeReferenceRepository(engine)

    app = create_app()
    app.dependency_overrides[get_knowledge_reference_repository] = lambda: repository
    app.dependency_overrides[get_observation_repository] = lambda: observation_repository
    app.dependency_overrides[_get_judgment_repository] = lambda: judgment_repository
    app.dependency_overrides[get_decision_repository] = lambda: decision_repository
    app.dependency_overrides[get_outcome_repository] = lambda: outcome_repository
    return TestClient(app), repository


@pytest.fixture
def client(context):
    return context[0]


def _seed(context, *, case_id: uuid.UUID | None = None) -> KnowledgeReference:
    _, repository = context
    seed = KnowledgeReference.capture(
        case_id=CaseId(case_id if case_id is not None else uuid.uuid4()),
        target=TypedDomainObjectReference(
            target_type=DomainObjectType.KNOWLEDGE_REFERENCE, target_id=uuid.uuid4()
        ),
    )
    repository.add(seed)
    return seed


def _seed_target(
    target_type: str,
    *,
    observation_repository,
    judgment_repository,
    decision_repository,
    outcome_repository,
    case_id: uuid.UUID,
) -> uuid.UUID:
    """Construct and persist an accepted instance of `target_type` directly
    into its own repository, bypassing every service/router layer —
    the only way each newly-enabled target type can exist to be
    referenced by a real, HTTP-driven Knowledge Reference capture.
    """
    now = datetime.now(timezone.utc)
    if target_type == "Observation":
        seed = Observation.capture(
            case_id=CaseId(case_id),
            subject=ObservationSubject("Semiconductor sector"),
            statement=ObservationStatement("Capex guidance raised."),
            observed_at=now,
        )
        observation_repository.add(seed)
        return seed.id.value
    if target_type == "Judgment":
        seed = Judgment.capture(
            case_id=CaseId(case_id), characterization=Characterization("a settled assessment")
        )
        judgment_repository.add(seed)
        return seed.id.value
    if target_type == "Decision":
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


def _create(client, case_id, target_type, target_id):
    return client.post(
        "/knowledge-references",
        json={
            "caseId": str(case_id),
            "target": {"targetType": target_type, "targetId": str(target_id)},
        },
    )


class TestCreateKnowledgeReference:
    def test_returns_201_when_targeting_a_previously_accepted_knowledge_reference(self, context):
        client, _ = context
        case_id = uuid.uuid4()
        seed = _seed(context, case_id=case_id)
        response = _create(client, case_id, "KnowledgeReference", seed.id.value)

        assert response.status_code == 201
        body = response.json()
        assert uuid.UUID(body["knowledgeReferenceId"])
        assert body["caseId"] == str(case_id)
        assert body["target"] == {
            "targetType": "KnowledgeReference",
            "targetId": str(seed.id.value),
        }
        assert "recordedAt" in body

    def test_accepts_snake_case_request_body_for_backward_compatibility(self, context):
        client, _ = context
        case_id = uuid.uuid4()
        seed = _seed(context, case_id=case_id)
        response = client.post(
            "/knowledge-references",
            json={
                "case_id": str(case_id),
                "target": {"target_type": "KnowledgeReference", "target_id": str(seed.id.value)},
            },
        )
        assert response.status_code == 201

    def test_persists_the_reference_so_it_can_be_read_back(self, context):
        client, _ = context
        case_id = uuid.uuid4()
        seed = _seed(context, case_id=case_id)
        created = _create(client, case_id, "KnowledgeReference", seed.id.value).json()
        fetched = client.get(f"/knowledge-references/{created['knowledgeReferenceId']}")
        assert fetched.status_code == 200
        assert fetched.json() == created


class TestPriorAcceptanceAndSameCaseFailures:
    def test_rejects_a_nonexistent_knowledge_reference_target(self, client):
        response = _create(client, uuid.uuid4(), "KnowledgeReference", uuid.uuid4())
        assert response.status_code == 400

    def test_rejects_a_cross_case_knowledge_reference_target(self, context):
        client, _ = context
        seed = _seed(context)  # its own random Case
        response = _create(client, uuid.uuid4(), "KnowledgeReference", seed.id.value)
        assert response.status_code == 400


class TestCreateKnowledgeReferenceAgainstNewlyEnabledTargetTypes:
    @pytest.mark.parametrize("target_type", _NEWLY_ENABLED_TARGET_TYPES)
    def test_returns_201_when_targeting_an_existing_same_case_target(
        self,
        client,
        observation_repository,
        judgment_repository,
        decision_repository,
        outcome_repository,
        target_type,
    ):
        case_id = uuid.uuid4()
        target_id = _seed_target(
            target_type,
            observation_repository=observation_repository,
            judgment_repository=judgment_repository,
            decision_repository=decision_repository,
            outcome_repository=outcome_repository,
            case_id=case_id,
        )
        response = _create(client, case_id, target_type, target_id)

        assert response.status_code == 201
        body = response.json()
        assert body["target"] == {"targetType": target_type, "targetId": str(target_id)}

    @pytest.mark.parametrize("target_type", _NEWLY_ENABLED_TARGET_TYPES)
    def test_rejects_a_nonexistent_target(self, client, target_type):
        response = _create(client, uuid.uuid4(), target_type, uuid.uuid4())
        assert response.status_code == 400

    @pytest.mark.parametrize("target_type", _NEWLY_ENABLED_TARGET_TYPES)
    def test_rejects_a_cross_case_target(
        self,
        client,
        observation_repository,
        judgment_repository,
        decision_repository,
        outcome_repository,
        target_type,
    ):
        target_id = _seed_target(
            target_type,
            observation_repository=observation_repository,
            judgment_repository=judgment_repository,
            decision_repository=decision_repository,
            outcome_repository=outcome_repository,
            case_id=uuid.uuid4(),  # its own random Case
        )
        response = _create(client, uuid.uuid4(), target_type, target_id)
        assert response.status_code == 400


class TestCanonicalButCurrentlyUnavailableTargetTypes:
    @pytest.mark.parametrize("target_type", _CURRENTLY_UNAVAILABLE_TARGET_TYPES)
    def test_rejects_with_a_client_error_not_a_server_fault(self, client, target_type):
        response = _create(client, uuid.uuid4(), target_type, uuid.uuid4())
        assert response.status_code == 400
        assert "detail" in response.json()

    @pytest.mark.parametrize("target_type", _CURRENTLY_UNAVAILABLE_TARGET_TYPES)
    def test_error_detail_does_not_call_the_type_unknown(self, client, target_type):
        response = _create(client, uuid.uuid4(), target_type, uuid.uuid4())
        detail = response.json()["detail"].lower()
        assert "unknown" not in detail
        assert "not adopted" not in detail


class TestUnknownTargetTypeRejection:
    def test_rejects_case_as_an_unknown_target_type_distinctly(self, client):
        # Distinct failure mode from the five canonical-but-unavailable
        # types above: this is rejected by Pydantic's own enum
        # validation (422), never reaching the application service at
        # all, unlike the 400s above.
        response = _create(client, uuid.uuid4(), "Case", uuid.uuid4())
        assert response.status_code == 422


class TestCreateKnowledgeReferenceValidationFailures:
    def test_rejects_malformed_target_id(self, client):
        response = client.post(
            "/knowledge-references",
            json={
                "caseId": str(uuid.uuid4()),
                "target": {"targetType": "KnowledgeReference", "targetId": "not-a-uuid"},
            },
        )
        assert response.status_code == 422

    def test_rejects_missing_case_id(self, client):
        response = client.post(
            "/knowledge-references",
            json={"target": {"targetType": "KnowledgeReference", "targetId": str(uuid.uuid4())}},
        )
        assert response.status_code == 422


class TestGetKnowledgeReference:
    def test_returns_404_for_unknown_id(self, client):
        response = client.get(f"/knowledge-references/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_rejects_malformed_id(self, client):
        response = client.get("/knowledge-references/not-a-uuid")
        assert response.status_code == 422
