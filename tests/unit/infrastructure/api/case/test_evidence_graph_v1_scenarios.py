"""Evidence Graph & Dependency Understanding -- the real HTTP surface
(`GET /evidence-graph/{case_id}`), powered by `atlas.alpha.evidence_graph
.service.EvidenceGraphService`. Follows the exact fixture/helper
pattern `test_ingestion_v1_scenarios.py` already established.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.decision.table import create_decision_table

_NOW = datetime.now(timezone.utc).isoformat()


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_decision_table(engine)
    app = create_app()
    app.dependency_overrides[get_decision_engine] = lambda: engine
    return TestClient(app)


def _import_holding(client, ticker: str, weight_percent: float = 100.0) -> str:
    response = client.post("/alpha-portfolio/import", json={"holdings": [{"ticker": ticker, "weightPercent": weight_percent}]})
    assert response.status_code == 201, response.text
    return response.json()["holdings"][0]["caseId"]


def _observe(client, case_id: str, statement: str = "Revenue grew 20% YoY") -> str:
    response = client.post(
        "/observations",
        json={"caseId": case_id, "subject": "NVDA", "statement": statement, "observedAt": _NOW},
    )
    assert response.status_code == 201, response.text
    return response.json()["observationId"]


def _decide(client, case_id: str, *, observation_id: str | None = None) -> None:
    response = client.post(
        "/decisions",
        json={
            "caseId": case_id,
            "userId": str(uuid.uuid4()),
            "decisionType": "BUY",
            "subject": "NVDA",
            "reason": "Strong growth",
            "confidence": 70,
            "observationId": observation_id,
        },
    )
    assert response.status_code == 201, response.text


def _cite_evidence(client, observation_id: str, direction: str = "SUPPORTS") -> None:
    response = client.post(
        "/evidence",
        json={"observationId": observation_id, "statement": "Confirmed by filing", "direction": direction, "observedAt": _NOW},
    )
    assert response.status_code == 201, response.text


class TestEvidenceGraphShape:
    def test_unknown_case_returns_404(self, client):
        response = client.get(f"/evidence-graph/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_a_real_case_with_no_activity_returns_an_empty_but_real_graph(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/evidence-graph/{case_id}").json()
        assert body["caseId"] == case_id
        assert set(body) == {"caseId", "generatedAt", "nodes", "edges", "weakDependencies", "impactedChanges", "summary"}
        assert set(body["summary"]) == {
            "nodeCount",
            "edgeCount",
            "singleSupportCount",
            "noSupportCount",
            "criticalDependencyCount",
            "isolatedChainCount",
            "mostCriticalNodeId",
        }

    def test_the_graph_never_leaks_investment_status_fields(self, client):
        """Deliverable 11's own language-boundary check at the wire
        level -- nothing here should ever carry a stance/conviction
        word as a field name."""
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/evidence-graph/{case_id}").json()
        assert "stanceLevel" not in body and "conviction" not in body


class TestEvidenceGraphRealActivity:
    def test_an_observation_and_decision_produce_a_real_depends_on_edge(self, client):
        case_id = _import_holding(client, "NVDA")
        observation_id = _observe(client, case_id)
        _decide(client, case_id, observation_id=observation_id)

        body = client.get(f"/evidence-graph/{case_id}").json()
        assert any(n["id"] == observation_id and n["kind"] == "observation" for n in body["nodes"])
        assert any(
            e["targetId"] == observation_id and e["kind"] == "depends_on" for e in body["edges"]
        )

    def test_evidence_direction_is_reflected_as_supports(self, client):
        case_id = _import_holding(client, "NVDA")
        observation_id = _observe(client, case_id)
        _cite_evidence(client, observation_id, direction="SUPPORTS")

        body = client.get(f"/evidence-graph/{case_id}").json()
        supports = [e for e in body["edges"] if e["kind"] == "supports" and e["targetId"] == observation_id]
        assert len(supports) == 1

    def test_evidence_direction_is_reflected_as_contradicts(self, client):
        case_id = _import_holding(client, "NVDA")
        observation_id = _observe(client, case_id)
        _cite_evidence(client, observation_id, direction="CHALLENGES")

        body = client.get(f"/evidence-graph/{case_id}").json()
        contradicts = [e for e in body["edges"] if e["kind"] == "contradicts" and e["targetId"] == observation_id]
        assert len(contradicts) == 1

    def test_an_observation_never_used_downstream_is_a_weak_dependency(self, client):
        case_id = _import_holding(client, "NVDA")
        observation_id = _observe(client, case_id)

        body = client.get(f"/evidence-graph/{case_id}").json()
        assert any(
            w["nodeId"] == observation_id and w["kind"] == "isolated_chain" for w in body["weakDependencies"]
        )
        assert body["summary"]["isolatedChainCount"] >= 1
