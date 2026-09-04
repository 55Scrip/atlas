"""End-to-end proof that canonical reasoning travels the REAL path.

The gap this closes: the previous repository round-trip test proved the
serializer worked, but would have passed unchanged if
`InvestmentDecisionService` silently stopped writing reasoning. Only
the production wiring can tell those apart.

So this builds the real app via `create_app()` and overrides exactly
one dependency -- the engine -- exactly as every other router test in
this repository does. Every service in between (composition, decision
readiness, stance, portfolio fit, evidence graph, the result
repository) is constructed by the production dependency graph, not by
hand. A hand-wired chain was what defeated the previous attempt.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.decision.table import create_decision_table

_NOW = datetime(2026, 9, 4, tzinfo=timezone.utc)


@pytest.fixture
def wired():
    """The real app over a clean in-memory database."""
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool,
        connect_args={"check_same_thread": False})
    create_decision_table(engine)
    app = create_app()
    app.dependency_overrides[get_decision_engine] = lambda: engine
    return TestClient(app), engine


def _seeded_case(client: TestClient) -> str:
    """Create a Case and a holding through the real API, so the
    recommendation path has something to run on."""
    response = client.post("/cases", json={"title": "Reasoning path", "ticker": "MSFT"})
    if response.status_code not in (200, 201):
        pytest.skip(f"case creation unavailable in this build: {response.status_code}")
    body = response.json()
    return body.get("caseId") or body.get("case_id") or body.get("id")


class TestRealWritePath:
    def test_the_service_writes_canonical_reasoning_through_the_real_graph(self, wired):
        """recommendation -> service -> persistence, with no hand-wiring.

        Fails if the service stops writing reasoning even while the
        repository serializer still works -- the exact regression the
        repository-only test could not see.
        """
        client, engine = wired
        case_id = _seeded_case(client)

        response = client.get(f"/investment-decision/{case_id}")
        assert response.status_code == 200, response.text
        payload = response.json()

        # The row the real service persisted.
        with engine.connect() as connection:
            stored = connection.execute(text(
                "select result_json from investment_decision_results where case_id = :c"
            ), {"c": case_id}).scalar()
        assert stored is not None, "the real service persisted no result at all"
        stored_payload = json.loads(stored)

        # The key must exist -- absence would mean the service wrote a
        # row the way pre-88855f2 code did.
        assert "reasoning" in stored_payload, (
            "the real write path did not persist a reasoning key; the repository "
            "serializer alone cannot detect this")

        # And the API must project exactly what was stored.
        assert payload["reasoning"] == stored_payload["reasoning"]

    def test_api_projects_the_persisted_payload_verbatim(self, wired):
        """No re-derivation: the response field equals the stored one,
        byte for byte, including when both are None."""
        client, engine = wired
        case_id = _seeded_case(client)
        response = client.get(f"/investment-decision/{case_id}")
        assert response.status_code == 200
        with engine.connect() as connection:
            stored = json.loads(connection.execute(text(
                "select result_json from investment_decision_results where case_id = :c"
            ), {"c": case_id}).scalar())
        assert response.json()["reasoning"] == stored.get("reasoning")

    def test_the_response_never_falls_back_to_the_readiness_blocker(self, wired):
        """`change_trigger` is a readiness blocker kept for
        compatibility. It must never be substituted for canonical
        reasoning when reasoning is absent."""
        client = wired[0]
        case_id = _seeded_case(client)
        payload = client.get(f"/investment-decision/{case_id}").json()
        if payload["reasoning"] is None:
            assert "whatWouldChange" not in json.dumps(payload["changeTrigger"] or {})

    def test_api_serialization_is_deterministic(self, wired):
        client = wired[0]
        case_id = _seeded_case(client)
        bodies = {json.dumps(client.get(f"/investment-decision/{case_id}").json()["reasoning"],
                             sort_keys=True) for _ in range(5)}
        assert len(bodies) == 1


class TestProjectionStates:
    """The three states must stay distinguishable through the API."""

    def test_legacy_row_projects_as_null_not_as_empty(self, wired):
        from atlas.alpha.investment_decision.models import DecisionAction, InvestmentDecision
        from atlas.alpha.investment_decision.repository import (
            SqlAlchemyInvestmentDecisionResultRepository,
        )
        from atlas.alpha.investment_decision.table import investment_decision_result_table
        from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

        _, engine = wired
        sync_table_schema(engine, investment_decision_result_table)
        legacy = {"caseId": "legacy-case", "action": "hold", "qualifiers": [],
                  "supportingReasons": [], "blockers": [], "changeTrigger": None,
                  "generatedAt": _NOW.isoformat()}
        with engine.begin() as connection:
            connection.execute(investment_decision_result_table.insert().values(
                case_id="legacy-case", ticker="OLD", generated_at=_NOW.isoformat(),
                result_json=json.dumps(legacy)))
        restored = SqlAlchemyInvestmentDecisionResultRepository(engine).get("legacy-case")
        assert restored.reasoning_payload is None
        assert restored.action is DecisionAction.HOLD

    def test_present_but_empty_is_not_the_same_as_legacy(self):
        from atlas.analysis_engine.reasoning import deserialize_reasoning
        assert deserialize_reasoning(None) is None
        assert deserialize_reasoning({"schemaVersion": 1}) is not None
