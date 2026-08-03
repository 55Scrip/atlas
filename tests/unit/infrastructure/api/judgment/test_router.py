"""API tests for the Judgment REST controller (DO-IMP-004).

**Widened per docs/atlas_domain_object_architecture/
Reference-Validation-Availability-Implementation-Design.md, and widened
again to include Reasoning Trace per the Reasoning Trace Implementation
Design's own Section 34 follow-on classification**: capture is now
enabled for a subject targeting any of the six adopted types —
Knowledge Reference, Judgment, Observation, Decision, Outcome, or
Reasoning Trace (see the application-layer test module's own
docstring). Tests exercising the referential form seed a pre-existing
accepted target directly into the shared repository instances the
API's dependency overrides provide, bypassing the API/service layers
for setup only.

The fixture overrides every collaborator dependency the router's
dependency graph resolves — including the newly added
`_get_reasoning_trace_repository` — so no request under test can fall
through to the real, on-disk `atlas.db` engine.
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
    _get_reasoning_trace_repository,
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
from atlas.core.infrastructure.persistence.reasoning_trace.sqlalchemy_repository import (
    SqlAlchemyReasoningTraceRepository,
)
from atlas.core.infrastructure.persistence.reasoning_trace.table import (
    create_reasoning_trace_tables,
)

_NEWLY_ENABLED_TARGET_TYPES = ("Observation", "Decision", "Outcome", "ReasoningTrace")


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
    create_reasoning_trace_tables(eng)
    return eng


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
def reasoning_trace_repository(engine):
    return SqlAlchemyReasoningTraceRepository(engine)


@pytest.fixture
def context(
    engine,
    observation_repository,
    decision_repository,
    outcome_repository,
    reasoning_trace_repository,
):
    judgment_repository = SqlAlchemyJudgmentRepository(engine)
    knowledge_reference_repository = SqlAlchemyKnowledgeReferenceRepository(engine)

    app = create_app()
    app.dependency_overrides[get_judgment_repository] = lambda: judgment_repository
    app.dependency_overrides[get_knowledge_reference_repository] = lambda: (
        knowledge_reference_repository
    )
    app.dependency_overrides[get_observation_repository] = lambda: observation_repository
    app.dependency_overrides[get_decision_repository] = lambda: decision_repository
    app.dependency_overrides[get_outcome_repository] = lambda: outcome_repository
    app.dependency_overrides[_get_reasoning_trace_repository] = lambda: reasoning_trace_repository
    return TestClient(app), judgment_repository, knowledge_reference_repository


@pytest.fixture
def client(context):
    return context[0]


def _seed_judgment(context, *, case_id: uuid.UUID | None = None) -> Judgment:
    _, judgment_repository, _ = context
    seed = Judgment.capture(
        case_id=CaseId(case_id if case_id is not None else uuid.uuid4()),
        characterization=Characterization("a prior settled characterization"),
    )
    judgment_repository.add(seed)
    return seed


def _seed_knowledge_reference(context, *, case_id: uuid.UUID | None = None) -> KnowledgeReference:
    _, _, knowledge_reference_repository = context
    seed = KnowledgeReference.capture(
        case_id=CaseId(case_id if case_id is not None else uuid.uuid4()),
        target=TypedDomainObjectReference(
            target_type=DomainObjectType.KNOWLEDGE_REFERENCE, target_id=uuid.uuid4()
        ),
    )
    knowledge_reference_repository.add(seed)
    return seed


def _seed_subject(
    target_type: str,
    *,
    observation_repository,
    decision_repository,
    outcome_repository,
    reasoning_trace_repository=None,
    case_id: uuid.UUID,
) -> uuid.UUID:
    """Construct and persist an accepted instance of `target_type` directly
    into its own repository, bypassing every service/router layer —
    the only way each newly-enabled subject type can exist to be
    referenced by a real, HTTP-driven Judgment capture.
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


def _create(client, case_id, characterization, subject=None):
    payload = {"caseId": str(case_id), "characterization": characterization}
    if subject is not None:
        payload["subject"] = subject
    return client.post("/judgments", json=payload)


class TestCreateJudgmentInternalContentForm:
    def test_returns_201_with_no_subject(self, client):
        case_id = uuid.uuid4()
        response = _create(client, case_id, "first object in this Case")

        assert response.status_code == 201
        body = response.json()
        assert uuid.UUID(body["judgmentId"])
        assert body["caseId"] == str(case_id)
        assert body["characterization"] == "first object in this Case"
        assert body["subject"] is None
        assert "recordedAt" in body

    def test_accepts_snake_case_request_body_for_backward_compatibility(self, client):
        response = client.post(
            "/judgments",
            json={"case_id": str(uuid.uuid4()), "characterization": "settled"},
        )
        assert response.status_code == 201

    def test_persists_the_judgment_so_it_can_be_read_back(self, client):
        created = _create(client, uuid.uuid4(), "settled").json()
        fetched = client.get(f"/judgments/{created['judgmentId']}")
        assert fetched.status_code == 200
        assert fetched.json() == created

    def test_rejects_blank_characterization(self, client):
        response = _create(client, uuid.uuid4(), "   ")
        assert response.status_code == 400


class TestCreateJudgmentReferentialFormAgainstKnowledgeReference:
    def test_returns_201_when_targeting_a_previously_accepted_knowledge_reference(self, context):
        client, _, _ = context
        case_id = uuid.uuid4()
        seed = _seed_knowledge_reference(context, case_id=case_id)
        response = _create(
            client,
            case_id,
            "relying on this knowledge",
            subject={"targetType": "KnowledgeReference", "targetId": str(seed.id.value)},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["subject"] == {
            "targetType": "KnowledgeReference",
            "targetId": str(seed.id.value),
        }

    def test_rejects_a_nonexistent_knowledge_reference_target(self, client):
        response = _create(
            client,
            uuid.uuid4(),
            "settled",
            subject={"targetType": "KnowledgeReference", "targetId": str(uuid.uuid4())},
        )
        assert response.status_code == 400

    def test_rejects_a_cross_case_knowledge_reference_target(self, context):
        client, _, _ = context
        seed = _seed_knowledge_reference(context)  # its own random Case
        response = _create(
            client,
            uuid.uuid4(),
            "settled",
            subject={"targetType": "KnowledgeReference", "targetId": str(seed.id.value)},
        )
        assert response.status_code == 400


class TestCreateJudgmentReferentialFormAgainstJudgment:
    def test_returns_201_when_targeting_a_previously_accepted_judgment(self, context):
        client, _, _ = context
        case_id = uuid.uuid4()
        seed = _seed_judgment(context, case_id=case_id)
        response = _create(
            client,
            case_id,
            "a Judgment about that earlier Judgment",
            subject={"targetType": "Judgment", "targetId": str(seed.id.value)},
        )

        assert response.status_code == 201
        assert response.json()["subject"] == {
            "targetType": "Judgment",
            "targetId": str(seed.id.value),
        }

    def test_rejects_a_cross_case_judgment_target(self, context):
        client, _, _ = context
        seed = _seed_judgment(context)  # its own random Case
        response = _create(
            client,
            uuid.uuid4(),
            "settled",
            subject={"targetType": "Judgment", "targetId": str(seed.id.value)},
        )
        assert response.status_code == 400


class TestCreateJudgmentAgainstNewlyEnabledSubjectTypes:
    @pytest.mark.parametrize("target_type", _NEWLY_ENABLED_TARGET_TYPES)
    def test_returns_201_when_targeting_an_existing_same_case_subject(
        self,
        client,
        observation_repository,
        decision_repository,
        outcome_repository,
        reasoning_trace_repository,
        target_type,
    ):
        case_id = uuid.uuid4()
        target_id = _seed_subject(
            target_type,
            observation_repository=observation_repository,
            decision_repository=decision_repository,
            outcome_repository=outcome_repository,
            reasoning_trace_repository=reasoning_trace_repository,
            case_id=case_id,
        )
        response = _create(
            client,
            case_id,
            "a Judgment about that earlier Domain Object",
            subject={"targetType": target_type, "targetId": str(target_id)},
        )

        assert response.status_code == 201
        assert response.json()["subject"] == {
            "targetType": target_type,
            "targetId": str(target_id),
        }

    @pytest.mark.parametrize("target_type", _NEWLY_ENABLED_TARGET_TYPES)
    def test_rejects_a_nonexistent_subject(self, client, target_type):
        response = _create(
            client,
            uuid.uuid4(),
            "settled",
            subject={"targetType": target_type, "targetId": str(uuid.uuid4())},
        )
        assert response.status_code == 400

    @pytest.mark.parametrize("target_type", _NEWLY_ENABLED_TARGET_TYPES)
    def test_rejects_a_cross_case_subject(
        self,
        client,
        observation_repository,
        decision_repository,
        outcome_repository,
        reasoning_trace_repository,
        target_type,
    ):
        target_id = _seed_subject(
            target_type,
            observation_repository=observation_repository,
            decision_repository=decision_repository,
            outcome_repository=outcome_repository,
            reasoning_trace_repository=reasoning_trace_repository,
            case_id=uuid.uuid4(),  # its own random Case
        )
        response = _create(
            client,
            uuid.uuid4(),
            "settled",
            subject={"targetType": target_type, "targetId": str(target_id)},
        )
        assert response.status_code == 400


class TestUnknownTargetTypeRejection:
    def test_rejects_case_as_an_unknown_target_type_distinctly(self, client):
        response = _create(
            client,
            uuid.uuid4(),
            "settled",
            subject={"targetType": "Case", "targetId": str(uuid.uuid4())},
        )
        assert response.status_code == 422


class TestCreateJudgmentValidationFailures:
    def test_rejects_malformed_subject_target_id(self, client):
        response = client.post(
            "/judgments",
            json={
                "caseId": str(uuid.uuid4()),
                "characterization": "settled",
                "subject": {"targetType": "Judgment", "targetId": "not-a-uuid"},
            },
        )
        assert response.status_code == 422

    def test_rejects_missing_case_id(self, client):
        response = client.post("/judgments", json={"characterization": "settled"})
        assert response.status_code == 422

    def test_rejects_missing_characterization(self, client):
        response = client.post("/judgments", json={"caseId": str(uuid.uuid4())})
        assert response.status_code == 422


class TestGetJudgment:
    def test_returns_404_for_unknown_id(self, client):
        response = client.get(f"/judgments/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_rejects_malformed_id(self, client):
        response = client.get("/judgments/not-a-uuid")
        assert response.status_code == 422


class TestListJudgments:
    def test_returns_every_recorded_judgment(self, client):
        case_id = uuid.uuid4()
        first = _create(client, case_id, "first characterization").json()
        second = _create(client, case_id, "second characterization").json()

        response = client.get("/judgments")

        assert response.status_code == 200
        ids = {judgment["judgmentId"] for judgment in response.json()}
        assert ids == {first["judgmentId"], second["judgmentId"]}

    def test_returns_empty_list_initially(self, client):
        response = client.get("/judgments")
        assert response.status_code == 200
        assert response.json() == []


class TestDeleteJudgment:
    def test_delete_returns_204(self, client):
        created = _create(client, uuid.uuid4(), "settled").json()

        response = client.delete(f"/judgments/{created['judgmentId']}")

        assert response.status_code == 204

    def test_deleted_judgment_is_gone_on_reload(self, client):
        created = _create(client, uuid.uuid4(), "settled").json()

        client.delete(f"/judgments/{created['judgmentId']}")

        assert client.get(f"/judgments/{created['judgmentId']}").status_code == 404
        assert created["judgmentId"] not in {
            judgment["judgmentId"] for judgment in client.get("/judgments").json()
        }

    def test_delete_unknown_id_returns_404(self, client):
        response = client.delete(f"/judgments/{uuid.uuid4()}")
        assert response.status_code == 404
