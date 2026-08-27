"""API tests for the unified import preview endpoint."""
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


class TestPreviewImportEndpoint:
    def test_a_clean_broker_export_resolves_with_no_review_needed(self, client):
        response = client.post(
            "/alpha-portfolio/import/preview",
            json={"rawText": "Namn;Antal;Kurs;Värde;Andel %\nVolvo B;100;220,50;22050;100%"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["headerDetected"] is True
        assert body["holdingsFound"] == 1
        assert body["resolvedCount"] == 1
        assert body["needsReview"] is False
        assert body["rows"][0]["ticker"] == "VOLV-B"
        assert body["rows"][0]["quantity"] == 100

    def test_an_unresolved_company_name_asks_for_review(self, client):
        response = client.post(
            "/alpha-portfolio/import/preview",
            json={"rawText": "Name;Weight\nSchneider Electric;100"},
        )
        body = response.json()
        assert body["needsReview"] is True
        assert body["rows"][0]["status"] == "UNRESOLVED"

    def test_ticker_already_in_the_current_portfolio_is_flagged(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 100}]},
        )
        response = client.post(
            "/alpha-portfolio/import/preview",
            json={"rawText": "Ticker;Weight\nAMD;100"},
        )
        body = response.json()
        assert body["rows"][0]["alreadyHeld"] is True
        assert body["needsReview"] is False
