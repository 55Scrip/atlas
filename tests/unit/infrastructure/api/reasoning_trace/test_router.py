"""API tests for the Reasoning Trace REST controller (DO-IMP-009).

All six adopted Domain Object types (Observation, Knowledge Reference,
Reasoning Trace, Judgment, Decision, Outcome) are immediately eligible
`targetType` values — no availability gate exists for this package
(docs/atlas_domain_object_architecture/
Reasoning-Trace-Implementation-Design.md, Section 29/31).

Since capture cannot itself produce the *first* accepted Domain Object
in an empty store (there is nothing yet to support — see the
application-layer test module's own docstring for the full argument),
tests that need a pre-existing accepted supporting object seed one
directly into the shared repository instance the API's dependency
override provides, bypassing the API/service layers for setup only.
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
from atlas.core.domain.reasoning_trace.entity import ReasoningTrace
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference
from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
from atlas.core.infrastructure.api.judgment.dependencies import get_judgment_repository
from atlas.core.infrastructure.api.knowledge_reference.dependencies import (
    get_knowledge_reference_repository,
    get_outcome_repository,
)
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository
from atlas.core.infrastructure.api.reasoning_trace.dependencies import (
    get_reasoning_trace_repository,
)
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
)

_ALL_SIX_TARGET_TYPES = (
    "Observation",
    "KnowledgeReference",
    "ReasoningTrace",
    "Judgment",
    "Decision",
    "Outcome",
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
def context(
    engine,
    observation_repository,
    knowledge_reference_repository,
    judgment_repository,
    decision_repository,
    outcome_repository,
):
    repository = SqlAlchemyReasoningTraceRepository(engine)

    app = create_app()
    app.dependency_overrides[get_reasoning_trace_repository] = lambda: repository
    app.dependency_overrides[get_observation_repository] = lambda: observation_repository
    app.dependency_overrides[get_knowledge_reference_repository] = (
        lambda: knowledge_reference_repository
    )
    app.dependency_overrides[get_judgment_repository] = lambda: judgment_repository
    app.dependency_overrides[get_decision_repository] = lambda: decision_repository
    app.dependency_overrides[get_outcome_repository] = lambda: outcome_repository
    return TestClient(app), repository


@pytest.fixture
def client(context):
    return context[0]


def _seed_target(
    target_type: str,
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
    directly into its own repository, bypassing every service/router
    layer — the only way each supporting-object type can exist to be
    referenced by a real, HTTP-driven Reasoning Trace capture.
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
    if target_type == "KnowledgeReference":
        seed = KnowledgeReference.capture(
            case_id=CaseId(case_id),
            target=TypedDomainObjectReference(
                target_type=DomainObjectType.OBSERVATION, target_id=uuid.uuid4()
            ),
        )
        knowledge_reference_repository.add(seed)
        return seed.id.value
    if target_type == "ReasoningTrace":
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


def _create(client, case_id, supports):
    return client.post(
        "/reasoning-traces",
        json={
            "caseId": str(case_id),
            "supports": [
                {"targetType": target_type, "targetId": str(target_id)}
                for target_type, target_id in supports
            ],
        },
    )


class TestCreateReasoningTrace:
    @pytest.mark.parametrize("target_type", _ALL_SIX_TARGET_TYPES)
    def test_returns_201_with_one_support(
        self,
        context,
        observation_repository,
        knowledge_reference_repository,
        judgment_repository,
        decision_repository,
        outcome_repository,
        target_type,
    ):
        client, repository = context
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
        response = _create(client, case_id, [(target_type, target_id)])

        assert response.status_code == 201
        body = response.json()
        assert uuid.UUID(body["reasoningTraceId"])
        assert body["caseId"] == str(case_id)
        assert body["supports"] == [{"targetType": target_type, "targetId": str(target_id)}]
        assert "recordedAt" in body

    def test_returns_201_with_multiple_supports(
        self, context, observation_repository, judgment_repository
    ):
        client, repository = context
        case_id = uuid.uuid4()
        observation_id = _seed_target(
            "Observation",
            observation_repository=observation_repository,
            knowledge_reference_repository=None,
            judgment_repository=judgment_repository,
            decision_repository=None,
            outcome_repository=None,
            reasoning_trace_repository=repository,
            case_id=case_id,
        )
        judgment_id = _seed_target(
            "Judgment",
            observation_repository=observation_repository,
            knowledge_reference_repository=None,
            judgment_repository=judgment_repository,
            decision_repository=None,
            outcome_repository=None,
            reasoning_trace_repository=repository,
            case_id=case_id,
        )
        response = _create(
            client, case_id, [("Observation", observation_id), ("Judgment", judgment_id)]
        )
        assert response.status_code == 201
        body = response.json()
        assert len(body["supports"]) == 2

    def test_accepts_snake_case_request_body_for_backward_compatibility(
        self, context, observation_repository
    ):
        client, repository = context
        case_id = uuid.uuid4()
        observation_id = _seed_target(
            "Observation",
            observation_repository=observation_repository,
            knowledge_reference_repository=None,
            judgment_repository=None,
            decision_repository=None,
            outcome_repository=None,
            reasoning_trace_repository=repository,
            case_id=case_id,
        )
        response = client.post(
            "/reasoning-traces",
            json={
                "case_id": str(case_id),
                "supports": [
                    {"target_type": "Observation", "target_id": str(observation_id)}
                ],
            },
        )
        assert response.status_code == 201

    def test_persists_the_trace_so_it_can_be_read_back(
        self, context, observation_repository
    ):
        client, repository = context
        case_id = uuid.uuid4()
        observation_id = _seed_target(
            "Observation",
            observation_repository=observation_repository,
            knowledge_reference_repository=None,
            judgment_repository=None,
            decision_repository=None,
            outcome_repository=None,
            reasoning_trace_repository=repository,
            case_id=case_id,
        )
        created = _create(client, case_id, [("Observation", observation_id)]).json()
        fetched = client.get(f"/reasoning-traces/{created['reasoningTraceId']}")
        assert fetched.status_code == 200
        assert fetched.json() == created

    def test_array_ordering_of_supports_has_no_effect_on_the_persisted_set(
        self, context, observation_repository, judgment_repository
    ):
        client, repository = context
        case_id = uuid.uuid4()
        observation_id = _seed_target(
            "Observation",
            observation_repository=observation_repository,
            knowledge_reference_repository=None,
            judgment_repository=judgment_repository,
            decision_repository=None,
            outcome_repository=None,
            reasoning_trace_repository=repository,
            case_id=case_id,
        )
        judgment_id = _seed_target(
            "Judgment",
            observation_repository=observation_repository,
            knowledge_reference_repository=None,
            judgment_repository=judgment_repository,
            decision_repository=None,
            outcome_repository=None,
            reasoning_trace_repository=repository,
            case_id=case_id,
        )
        first = _create(
            client, case_id, [("Observation", observation_id), ("Judgment", judgment_id)]
        ).json()
        second = _create(
            client, case_id, [("Judgment", judgment_id), ("Observation", observation_id)]
        ).json()
        assert set(map(str, first["supports"])) == set(map(str, second["supports"]))


class TestPriorAcceptanceAndSameCaseFailures:
    def test_rejects_a_nonexistent_target(self, client):
        response = _create(client, uuid.uuid4(), [("Observation", uuid.uuid4())])
        assert response.status_code == 400

    def test_rejects_a_cross_case_target(self, context, observation_repository):
        client, repository = context
        seed_case_id = uuid.uuid4()
        observation_id = _seed_target(
            "Observation",
            observation_repository=observation_repository,
            knowledge_reference_repository=None,
            judgment_repository=None,
            decision_repository=None,
            outcome_repository=None,
            reasoning_trace_repository=repository,
            case_id=seed_case_id,
        )
        response = _create(client, uuid.uuid4(), [("Observation", observation_id)])
        assert response.status_code == 400


class TestEmptySupportRejection:
    def test_rejects_an_empty_supports_array(self, client):
        response = _create(client, uuid.uuid4(), [])
        assert response.status_code == 400
        assert "detail" in response.json()


class TestUnknownTargetTypeRejection:
    def test_rejects_case_as_an_unknown_target_type_distinctly(self, client):
        response = _create(client, uuid.uuid4(), [("Case", uuid.uuid4())])
        assert response.status_code == 422


class TestCreateReasoningTraceValidationFailures:
    def test_rejects_malformed_target_id(self, client):
        response = client.post(
            "/reasoning-traces",
            json={
                "caseId": str(uuid.uuid4()),
                "supports": [{"targetType": "Observation", "targetId": "not-a-uuid"}],
            },
        )
        assert response.status_code == 422

    def test_rejects_missing_case_id(self, client):
        response = client.post(
            "/reasoning-traces",
            json={"supports": [{"targetType": "Observation", "targetId": str(uuid.uuid4())}]},
        )
        assert response.status_code == 422


class TestGetReasoningTrace:
    def test_returns_404_for_unknown_id(self, client):
        response = client.get(f"/reasoning-traces/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_rejects_malformed_id(self, client):
        response = client.get("/reasoning-traces/not-a-uuid")
        assert response.status_code == 422


class TestAppMounting:
    def test_reasoning_trace_router_is_mounted(self):
        from atlas.core.infrastructure.api.app import create_app

        app = create_app()
        paths = set(app.openapi()["paths"])
        assert "/reasoning-traces" in paths
        assert "/reasoning-traces/{reasoning_trace_id}" in paths
