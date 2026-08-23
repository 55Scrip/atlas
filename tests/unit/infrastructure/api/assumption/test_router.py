"""API tests for the Assumption REST controller (ADR-AS-001)."""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.case.entity import Case
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.value_objects import (
    Confidence,
    DecisionType,
    InvestmentCase,
    Subject,
    UserId,
)
from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.assumption.dependencies import get_assumption_repository
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.api.case_condition.dependencies import (
    get_case_condition_repository,
)
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
from atlas.core.infrastructure.persistence.assumption.sqlalchemy_repository import (
    SqlAlchemyAssumptionEventRepository,
)
from atlas.core.infrastructure.persistence.assumption.table import create_assumption_events_table
from atlas.core.infrastructure.persistence.case.sqlalchemy_repository import (
    SqlAlchemyCaseRepository,
)
from atlas.core.infrastructure.persistence.case.table import create_case_table
from atlas.core.infrastructure.persistence.case_condition.sqlalchemy_repository import (
    SqlAlchemyCaseConditionEventRepository,
)
from atlas.core.infrastructure.persistence.case_condition.table import (
    create_case_condition_events_table,
)
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.decision.table import create_decision_table


@pytest.fixture
def repositories():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_case_table(engine)
    create_decision_table(engine)
    create_case_condition_events_table(engine)
    create_assumption_events_table(engine)
    return {
        "case": SqlAlchemyCaseRepository(engine),
        "decision": SqlAlchemyDecisionRepository(engine),
        "case_condition": SqlAlchemyCaseConditionEventRepository(engine),
        "assumption": SqlAlchemyAssumptionEventRepository(engine),
    }


@pytest.fixture
def client(repositories):
    app = create_app()
    app.dependency_overrides[get_case_repository] = lambda: repositories["case"]
    app.dependency_overrides[get_decision_repository] = lambda: repositories["decision"]
    app.dependency_overrides[get_case_condition_repository] = lambda: repositories["case_condition"]
    app.dependency_overrides[get_assumption_repository] = lambda: repositories["assumption"]
    return TestClient(app)


@pytest.fixture
def existing_case(repositories) -> Case:
    case = Case.create()
    repositories["case"].add(case)
    return case


@pytest.fixture
def existing_decision(repositories, existing_case) -> Decision:
    decision = Decision.register(
        case_id=existing_case.id,
        user_id=UserId(uuid.uuid4()),
        decision_type=DecisionType.BUY,
        subject=Subject("ASML"),
        investment_case=InvestmentCase("Durable moat"),
        confidence=Confidence(75),
    )
    repositories["decision"].add(decision)
    return decision


class TestCreateAssumption:
    def test_returns_201_with_the_created_assumption(self, client, existing_decision, existing_case):
        response = client.post(
            f"/decisions/{existing_decision.id.value}/assumptions",
            json={"statement": "GCP margin expansion continues", "authorship": "atlas"},
        )
        assert response.status_code == 201
        body = response.json()
        assert uuid.UUID(body["assumptionId"])
        assert body["decisionId"] == str(existing_decision.id.value)
        assert body["caseId"] == str(existing_case.id.value)
        assert body["status"] == "supported"
        assert body["isActive"] is True
        assert body["statement"] == "GCP margin expansion continues"

    def test_returns_404_for_an_unknown_decision(self, client):
        response = client.post(f"/decisions/{uuid.uuid4()}/assumptions", json={})
        assert response.status_code == 404


class TestListAssumptionsForDecision:
    def test_excludes_terminal_by_default(self, client, existing_decision):
        active = client.post(f"/decisions/{existing_decision.id.value}/assumptions", json={}).json()
        retired = client.post(f"/decisions/{existing_decision.id.value}/assumptions", json={}).json()
        client.post(f"/assumptions/{retired['assumptionId']}/retire")

        response = client.get(f"/decisions/{existing_decision.id.value}/assumptions")

        assert response.status_code == 200
        ids = {a["assumptionId"] for a in response.json()}
        assert ids == {active["assumptionId"]}


class TestListAssumptionsForCase:
    def test_returns_assumptions_across_decisions(self, client, repositories, existing_case):
        decision_a = Decision.register(
            case_id=existing_case.id, user_id=UserId(uuid.uuid4()), decision_type=DecisionType.BUY,
            subject=Subject("ASML"), investment_case=InvestmentCase("Reason A"), confidence=Confidence(70),
        )
        repositories["decision"].add(decision_a)
        client.post(f"/decisions/{decision_a.id.value}/assumptions", json={})

        response = client.get(f"/cases/{existing_case.id.value}/assumptions")

        assert response.status_code == 200
        assert len(response.json()) == 1


class TestGetAssumption:
    def test_returns_the_current_state(self, client, existing_decision):
        created = client.post(
            f"/decisions/{existing_decision.id.value}/assumptions",
            json={"statement": "GCP margin expansion continues"},
        ).json()

        response = client.get(f"/assumptions/{created['assumptionId']}")

        assert response.status_code == 200
        assert response.json()["statement"] == "GCP margin expansion continues"

    def test_returns_404_for_an_unknown_assumption(self, client):
        response = client.get(f"/assumptions/{uuid.uuid4()}")
        assert response.status_code == 404


class TestListAssumptionEvents:
    def test_returns_full_history(self, client, existing_decision):
        created = client.post(f"/decisions/{existing_decision.id.value}/assumptions", json={}).json()
        client.patch(f"/assumptions/{created['assumptionId']}", json={"statement": "revised"})

        response = client.get(f"/assumptions/{created['assumptionId']}/events")

        assert response.status_code == 200
        assert [e["eventType"] for e in response.json()] == ["revised", "revised"]


class TestReviseAssumption:
    def test_returns_200_with_the_revised_content(self, client, existing_decision):
        created = client.post(
            f"/decisions/{existing_decision.id.value}/assumptions",
            json={"statement": "v1"},
        ).json()

        response = client.patch(f"/assumptions/{created['assumptionId']}", json={"statement": "v2"})

        assert response.status_code == 200
        assert response.json()["statement"] == "v2"

    def test_returns_409_for_a_retired_assumption(self, client, existing_decision):
        created = client.post(f"/decisions/{existing_decision.id.value}/assumptions", json={}).json()
        client.post(f"/assumptions/{created['assumptionId']}/retire")

        response = client.patch(f"/assumptions/{created['assumptionId']}", json={})

        assert response.status_code == 409

    def test_returns_404_for_an_unknown_assumption(self, client):
        response = client.patch(f"/assumptions/{uuid.uuid4()}", json={})
        assert response.status_code == 404


class TestChallengeAssumption:
    def test_defaults_to_challenged(self, client, existing_decision):
        created = client.post(f"/decisions/{existing_decision.id.value}/assumptions", json={}).json()

        response = client.post(
            f"/assumptions/{created['assumptionId']}/challenge", json={"note": "mixed signals"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "challenged"

    def test_explicit_invalidated_severity(self, client, existing_decision):
        created = client.post(f"/decisions/{existing_decision.id.value}/assumptions", json={}).json()

        response = client.post(
            f"/assumptions/{created['assumptionId']}/challenge", json={"severity": "invalidated"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "invalidated"


class TestRetireAssumption:
    def test_returns_204(self, client, existing_decision):
        created = client.post(f"/decisions/{existing_decision.id.value}/assumptions", json={}).json()

        response = client.post(f"/assumptions/{created['assumptionId']}/retire")

        assert response.status_code == 204
        assert client.get(f"/assumptions/{created['assumptionId']}").json()["status"] == "retired"

    def test_is_idempotent(self, client, existing_decision):
        created = client.post(f"/decisions/{existing_decision.id.value}/assumptions", json={}).json()

        first = client.post(f"/assumptions/{created['assumptionId']}/retire")
        second = client.post(f"/assumptions/{created['assumptionId']}/retire")

        assert first.status_code == 204
        assert second.status_code == 204


class TestSupersedeAssumption:
    def test_returns_200_with_the_replacement_reference(self, client, existing_decision):
        old = client.post(f"/decisions/{existing_decision.id.value}/assumptions", json={}).json()
        new = client.post(f"/decisions/{existing_decision.id.value}/assumptions", json={}).json()

        response = client.post(
            f"/assumptions/{old['assumptionId']}/supersede",
            json={"supersededByAssumptionId": new["assumptionId"]},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "superseded"
        assert body["supersededByAssumptionId"] == new["assumptionId"]

    def test_returns_409_for_an_already_terminal_assumption(self, client, existing_decision):
        created = client.post(f"/decisions/{existing_decision.id.value}/assumptions", json={}).json()
        client.post(f"/assumptions/{created['assumptionId']}/retire")

        response = client.post(f"/assumptions/{created['assumptionId']}/supersede", json={})

        assert response.status_code == 409


class TestAttachDetachCaseCondition:
    def test_attach_links_a_real_case_condition(self, client, existing_decision, existing_case):
        assumption = client.post(
            f"/decisions/{existing_decision.id.value}/assumptions", json={}
        ).json()
        condition = client.post(
            f"/cases/{existing_case.id.value}/case-conditions", json={}
        ).json()

        response = client.post(
            f"/assumptions/{assumption['assumptionId']}/case-conditions/{condition['conditionId']}/attach"
        )

        assert response.status_code == 200
        assert response.json()["linkedCaseConditionIds"] == [condition["conditionId"]]

    def test_attach_returns_422_for_an_unknown_case_condition(self, client, existing_decision):
        assumption = client.post(
            f"/decisions/{existing_decision.id.value}/assumptions", json={}
        ).json()

        response = client.post(
            f"/assumptions/{assumption['assumptionId']}/case-conditions/{uuid.uuid4()}/attach"
        )

        assert response.status_code == 422

    def test_detach_unlinks_a_case_condition(self, client, existing_decision, existing_case):
        assumption = client.post(
            f"/decisions/{existing_decision.id.value}/assumptions", json={}
        ).json()
        condition = client.post(
            f"/cases/{existing_case.id.value}/case-conditions", json={}
        ).json()
        client.post(
            f"/assumptions/{assumption['assumptionId']}/case-conditions/{condition['conditionId']}/attach"
        )

        response = client.post(
            f"/assumptions/{assumption['assumptionId']}/case-conditions/{condition['conditionId']}/detach"
        )

        assert response.status_code == 200
        assert response.json()["linkedCaseConditionIds"] == []
