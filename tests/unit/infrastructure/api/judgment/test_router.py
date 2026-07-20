"""API tests for the Judgment REST controller (DO-IMP-004).

Capture is currently enabled for a subject targeting a Knowledge
Reference or another Judgment (see the application-layer test module's
own docstring). Tests exercising the referential form seed a
pre-existing accepted Knowledge Reference or Judgment directly into the
shared repository instances the API's dependency overrides provide,
bypassing the API/service layers for setup only.
"""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.judgment.entity import Judgment
from atlas.core.domain.judgment.value_objects import Characterization
from atlas.core.domain.knowledge_reference.entity import KnowledgeReference
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference
from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.judgment.dependencies import get_judgment_repository
from atlas.core.infrastructure.api.knowledge_reference.dependencies import (
    get_knowledge_reference_repository,
)
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

_CURRENTLY_UNAVAILABLE_TARGET_TYPES = ("Observation", "ReasoningTrace", "Decision", "Outcome")


@pytest.fixture
def context():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_judgment_table(engine)
    create_knowledge_reference_table(engine)
    judgment_repository = SqlAlchemyJudgmentRepository(engine)
    knowledge_reference_repository = SqlAlchemyKnowledgeReferenceRepository(engine)

    app = create_app()
    app.dependency_overrides[get_judgment_repository] = lambda: judgment_repository
    app.dependency_overrides[get_knowledge_reference_repository] = (
        lambda: knowledge_reference_repository
    )
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
    def test_returns_201_when_targeting_a_previously_accepted_knowledge_reference(
        self, context
    ):
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


class TestCanonicalButCurrentlyUnavailableTargetTypes:
    @pytest.mark.parametrize("target_type", _CURRENTLY_UNAVAILABLE_TARGET_TYPES)
    def test_rejects_with_a_client_error_not_a_server_fault(self, client, target_type):
        response = _create(
            client,
            uuid.uuid4(),
            "settled",
            subject={"targetType": target_type, "targetId": str(uuid.uuid4())},
        )
        assert response.status_code == 400
        assert "detail" in response.json()

    @pytest.mark.parametrize("target_type", _CURRENTLY_UNAVAILABLE_TARGET_TYPES)
    def test_error_detail_does_not_call_the_type_unknown(self, client, target_type):
        response = _create(
            client,
            uuid.uuid4(),
            "settled",
            subject={"targetType": target_type, "targetId": str(uuid.uuid4())},
        )
        detail = response.json()["detail"].lower()
        assert "unknown" not in detail
        assert "not adopted" not in detail


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
