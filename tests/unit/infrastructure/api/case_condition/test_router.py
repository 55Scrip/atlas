"""API tests for the CaseCondition REST controller (ADR-CC-001)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

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
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.api.case_condition.dependencies import (
    get_case_condition_repository,
)
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
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
    return {
        "case": SqlAlchemyCaseRepository(engine),
        "decision": SqlAlchemyDecisionRepository(engine),
        "case_condition": SqlAlchemyCaseConditionEventRepository(engine),
    }


@pytest.fixture
def client(repositories):
    app = create_app()
    app.dependency_overrides[get_case_repository] = lambda: repositories["case"]
    app.dependency_overrides[get_decision_repository] = lambda: repositories["decision"]
    app.dependency_overrides[get_case_condition_repository] = lambda: repositories["case_condition"]
    return TestClient(app)


@pytest.fixture
def existing_case(repositories) -> Case:
    case = Case.create()
    repositories["case"].add(case)
    return case


def _decision_in_case(repositories, case_id) -> Decision:
    decision = Decision.register(
        case_id=case_id,
        user_id=UserId(uuid.uuid4()),
        decision_type=DecisionType.BUY,
        subject=Subject("ASML"),
        investment_case=InvestmentCase("Durable moat"),
        confidence=Confidence(75),
    )
    repositories["decision"].add(decision)
    return decision


class TestCreateCaseCondition:
    def test_returns_201_with_the_created_condition(self, client, existing_case):
        response = client.post(
            f"/cases/{existing_case.id.value}/case-conditions",
            json={"predicateText": "China revenue trend", "role": "monitoring"},
        )
        assert response.status_code == 201
        body = response.json()
        assert uuid.UUID(body["conditionId"])
        assert body["caseId"] == str(existing_case.id.value)
        assert body["status"] == "active"
        assert body["isActive"] is True
        assert body["predicateText"] == "China revenue trend"

    def test_returns_404_for_an_unknown_case(self, client):
        response = client.post(f"/cases/{uuid.uuid4()}/case-conditions", json={})
        assert response.status_code == 404

    def test_returns_422_for_a_decision_in_a_different_case(self, client, repositories):
        case = Case.create()
        repositories["case"].add(case)
        other_case = Case.create()
        repositories["case"].add(other_case)
        decision = _decision_in_case(repositories, other_case.id)

        response = client.post(
            f"/cases/{case.id.value}/case-conditions",
            json={"decisionId": str(decision.id.value)},
        )
        assert response.status_code == 422


class TestListCaseConditionsForCase:
    def test_excludes_terminal_by_default(self, client, existing_case):
        active = client.post(
            f"/cases/{existing_case.id.value}/case-conditions", json={}
        ).json()
        retired = client.post(
            f"/cases/{existing_case.id.value}/case-conditions", json={}
        ).json()
        client.post(f"/case-conditions/{retired['conditionId']}/retire")

        response = client.get(f"/cases/{existing_case.id.value}/case-conditions")

        assert response.status_code == 200
        ids = {c["conditionId"] for c in response.json()}
        assert ids == {active["conditionId"]}

    def test_includes_terminal_when_requested(self, client, existing_case):
        active = client.post(
            f"/cases/{existing_case.id.value}/case-conditions", json={}
        ).json()
        retired = client.post(
            f"/cases/{existing_case.id.value}/case-conditions", json={}
        ).json()
        client.post(f"/case-conditions/{retired['conditionId']}/retire")

        response = client.get(
            f"/cases/{existing_case.id.value}/case-conditions", params={"includeTerminal": True}
        )

        ids = {c["conditionId"] for c in response.json()}
        assert ids == {active["conditionId"], retired["conditionId"]}


class TestListCaseConditionsForDecision:
    def test_returns_only_conditions_for_that_decision(self, client, repositories, existing_case):
        decision = _decision_in_case(repositories, existing_case.id)
        client.post(
            f"/cases/{existing_case.id.value}/case-conditions",
            json={"decisionId": str(decision.id.value)},
        )
        client.post(f"/cases/{existing_case.id.value}/case-conditions", json={})

        response = client.get(f"/decisions/{decision.id.value}/case-conditions")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["decisionId"] == str(decision.id.value)


class TestGetCaseCondition:
    def test_returns_the_current_state(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/case-conditions",
            json={"predicateText": "China revenue trend"},
        ).json()

        response = client.get(f"/case-conditions/{created['conditionId']}")

        assert response.status_code == 200
        assert response.json()["predicateText"] == "China revenue trend"

    def test_returns_404_for_an_unknown_condition(self, client):
        response = client.get(f"/case-conditions/{uuid.uuid4()}")
        assert response.status_code == 404


class TestListCaseConditionEvents:
    def test_returns_full_history(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/case-conditions", json={}
        ).json()
        client.patch(f"/case-conditions/{created['conditionId']}", json={"predicateText": "revised"})

        response = client.get(f"/case-conditions/{created['conditionId']}/events")

        assert response.status_code == 200
        assert [e["eventType"] for e in response.json()] == ["revised", "revised"]


class TestReviseCaseCondition:
    def test_returns_200_with_the_revised_content(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/case-conditions",
            json={"predicateText": "China revenue trend"},
        ).json()

        response = client.patch(
            f"/case-conditions/{created['conditionId']}", json={"predicateText": "China revenue growth"}
        )

        assert response.status_code == 200
        assert response.json()["predicateText"] == "China revenue growth"

    def test_returns_409_for_a_retired_condition(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/case-conditions", json={}
        ).json()
        client.post(f"/case-conditions/{created['conditionId']}/retire")

        response = client.patch(f"/case-conditions/{created['conditionId']}", json={})

        assert response.status_code == 409

    def test_returns_404_for_an_unknown_condition(self, client):
        response = client.patch(f"/case-conditions/{uuid.uuid4()}", json={})
        assert response.status_code == 404


class TestEvaluateCaseCondition:
    def test_transitions_a_date_based_condition_to_satisfied(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/case-conditions",
            json={"structuredKind": "date", "thresholdDate": "2020-01-01T00:00:00+00:00"},
        ).json()

        response = client.post(
            f"/case-conditions/{created['conditionId']}/evaluate",
            json={"evaluatedAt": "2026-01-01T00:00:00+00:00"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["satisfied"] is True
        assert body["transitioned"] is True
        assert body["condition"]["status"] == "satisfied"

    def test_threshold_condition_requires_an_observed_value(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/case-conditions",
            json={
                "structuredKind": "threshold",
                "thresholdMetric": "china_revenue_growth",
                "thresholdOperator": "<",
                "thresholdValue": 0.05,
            },
        ).json()

        response = client.post(f"/case-conditions/{created['conditionId']}/evaluate", json={})

        assert response.status_code == 422

    def test_accepts_a_human_assertion_for_free_text_conditions(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/case-conditions",
            json={"predicateText": "Management changes capital allocation"},
        ).json()

        response = client.post(
            f"/case-conditions/{created['conditionId']}/evaluate",
            json={"humanAssertedSatisfied": True},
        )

        assert response.status_code == 200
        assert response.json()["satisfied"] is True

    def test_returns_422_for_a_free_text_condition_with_no_assertion(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/case-conditions",
            json={"predicateText": "Management changes capital allocation"},
        ).json()

        response = client.post(f"/case-conditions/{created['conditionId']}/evaluate", json={})

        assert response.status_code == 422


class TestRetireCaseCondition:
    def test_returns_204(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/case-conditions", json={}
        ).json()

        response = client.post(f"/case-conditions/{created['conditionId']}/retire")

        assert response.status_code == 204
        assert client.get(f"/case-conditions/{created['conditionId']}").json()["status"] == "retired"

    def test_is_idempotent(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/case-conditions", json={}
        ).json()

        first = client.post(f"/case-conditions/{created['conditionId']}/retire")
        second = client.post(f"/case-conditions/{created['conditionId']}/retire")

        assert first.status_code == 204
        assert second.status_code == 204


class TestSupersedeCaseCondition:
    def test_returns_200_with_the_replacement_reference(self, client, existing_case):
        old = client.post(f"/cases/{existing_case.id.value}/case-conditions", json={}).json()
        new = client.post(f"/cases/{existing_case.id.value}/case-conditions", json={}).json()

        response = client.post(
            f"/case-conditions/{old['conditionId']}/supersede",
            json={"supersededByConditionId": new["conditionId"]},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "superseded"
        assert body["supersededByConditionId"] == new["conditionId"]

    def test_returns_409_for_an_already_terminal_condition(self, client, existing_case):
        created = client.post(
            f"/cases/{existing_case.id.value}/case-conditions", json={}
        ).json()
        client.post(f"/case-conditions/{created['conditionId']}/retire")

        response = client.post(f"/case-conditions/{created['conditionId']}/supersede", json={})

        assert response.status_code == 409
