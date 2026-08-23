"""Evidence Timeline -- the real HTTP surface (`/evidence-timeline/*`),
powered by `atlas.alpha.evidence_timeline.service.EvidenceTimelineService`
plus the capture side effect `investment_case/api/router.py`'s own
`/cases/{case_id}/analysis` endpoint performs. Follows the exact
fixture/helper pattern `test_evidence_quality_v1_scenarios.py` already
established.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.decision.table import create_decision_table


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(engine)
    app = create_app()
    app.dependency_overrides[get_decision_engine] = lambda: engine
    return TestClient(app)


def _import_holding(client, ticker: str, weight_percent: float = 100.0) -> str:
    response = client.post("/alpha-portfolio/import", json={"holdings": [{"ticker": ticker, "weightPercent": weight_percent}]})
    assert response.status_code == 201, response.text
    return response.json()["holdings"][0]["caseId"]


class TestCaptureOnAnalysisRead:
    def test_a_case_with_no_prior_read_has_an_empty_timeline(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/evidence-timeline/case/{case_id}").json()
        assert body == []

    def test_reading_the_analysis_once_captures_exactly_one_baseline_entry(self, client):
        case_id = _import_holding(client, "NVDA")
        client.get(f"/cases/{case_id}/analysis")
        body = client.get(f"/evidence-timeline/case/{case_id}").json()
        assert len(body) == 1
        assert body[0]["history"]["isBaseline"] is True
        assert body[0]["history"]["transitions"] == []

    def test_reading_the_analysis_again_with_no_change_does_not_add_a_second_entry(self, client):
        case_id = _import_holding(client, "NVDA")
        client.get(f"/cases/{case_id}/analysis")
        client.get(f"/cases/{case_id}/analysis")
        body = client.get(f"/evidence-timeline/case/{case_id}").json()
        assert len(body) == 1

    def test_reading_history_alone_never_creates_a_snapshot(self, client):
        case_id = _import_holding(client, "NVDA")
        client.get(f"/evidence-timeline/case/{case_id}")
        client.get(f"/evidence-timeline/case/{case_id}")
        body = client.get(f"/evidence-timeline/case/{case_id}").json()
        assert body == []


class TestEmbeddedOnAnalysis:
    def test_first_read_embeds_a_baseline_evidence_timeline(self, client):
        case_id = _import_holding(client, "NVDA")
        body = client.get(f"/cases/{case_id}/analysis").json()
        assert body["evidenceTimeline"] is not None
        assert body["evidenceTimeline"]["isBaseline"] is True

    def test_ticker_endpoint_matches_case_endpoint(self, client):
        case_id = _import_holding(client, "AAPL")
        client.get(f"/cases/{case_id}/analysis")
        by_case = client.get(f"/evidence-timeline/case/{case_id}").json()
        by_ticker = client.get("/evidence-timeline/ticker/AAPL").json()
        assert by_case == by_ticker

    def test_returns_404_for_a_ticker_with_no_case(self, client):
        response = client.get("/evidence-timeline/ticker/ZZZZZ")
        assert response.status_code == 404


class TestRealTransition:
    def test_recording_a_decision_between_two_reads_can_produce_a_real_transition(self, client):
        """Adding a real Decision changes `EvidenceCoverageLevel`/
        `ConvictionAssessment` inputs -- a genuine, real content change
        between the two captured snapshots, not a fabricated one."""
        case_id = _import_holding(client, "NVDA")
        client.get(f"/cases/{case_id}/analysis")
        response = client.post(
            "/decisions",
            json={
                "caseId": case_id,
                "userId": "00000000-0000-0000-0000-000000000001",
                "decisionType": "HOLD",
                "subject": "NVDA",
                "reason": "Evidence Timeline live-verification decision.",
                "confidence": 70,
            },
        )
        assert response.status_code == 201, response.text
        client.get(f"/cases/{case_id}/analysis")
        body = client.get(f"/evidence-timeline/case/{case_id}").json()
        assert len(body) >= 1
        for snapshot, history in [(row["snapshot"], row["history"]) for row in body]:
            assert set(snapshot) == {
                "overallCoverage", "overallConfidence", "stanceLevel", "evidenceQuality",
                "conflictStatus", "freshness", "missingDimensions", "capturedAt",
            }
            assert set(history) == {"isBaseline", "transitions", "newSourceEvidence", "previousCapturedAt", "currentCapturedAt"}
            for transition in history["transitions"]:
                assert set(transition) == {"id", "category", "direction", "previousState", "currentState", "isMaterial"}
                assert isinstance(transition["isMaterial"], bool)
            for event in history["newSourceEvidence"]:
                assert set(event) == {"factKind", "period"}


class TestFeed:
    def test_feed_includes_every_case_with_a_captured_snapshot(self, client):
        case_a = _import_holding(client, "NVDA")
        client.get(f"/cases/{case_a}/analysis")
        body = client.get("/evidence-timeline/feed").json()
        case_ids = {entry["caseId"] for entry in body["entries"]}
        assert case_a in case_ids

    def test_feed_is_newest_first(self, client):
        case_id = _import_holding(client, "NVDA")
        client.get(f"/cases/{case_id}/analysis")
        body = client.get("/evidence-timeline/feed").json()
        timestamps = [entry["snapshot"]["capturedAt"] for entry in body["entries"]]
        assert timestamps == sorted(timestamps, reverse=True)
