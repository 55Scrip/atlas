"""API tests for the unified import preview endpoint.

`get_security_discovery_indexes` is overridden to a fixed, real-data-
shaped fixture (same pattern as `tests/unit/infrastructure/api/
security_discovery/test_router.py`) so these tests never make a real
network call to SEC.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.security_discovery.api.dependencies import get_security_discovery_indexes
from atlas.alpha.security_discovery.models import SecTickerEntry
from atlas.alpha.security_discovery.service import build_ticker_index, build_title_index
from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.decision.table import create_decision_table

_SEC_FIXTURE = (
    SecTickerEntry(cik=937966, ticker="ASML", title="ASML HOLDING NV"),
    SecTickerEntry(cik=1067983, ticker="BRK-A", title="BERKSHIRE HATHAWAY INC"),
    SecTickerEntry(cik=1067983, ticker="BRK-B", title="BERKSHIRE HATHAWAY INC"),
)


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
    title_index = build_title_index(_SEC_FIXTURE)
    ticker_index = build_ticker_index(_SEC_FIXTURE)
    app.dependency_overrides[get_security_discovery_indexes] = lambda: (title_index, ticker_index)
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
            json={"rawText": "Name;Weight\nZelkova Materials Group;100"},
        )
        body = response.json()
        assert body["needsReview"] is True
        assert body["rows"][0]["status"] == "UNRESOLVED"

    def test_a_name_the_registry_misses_resolves_via_security_discovery(self, client):
        response = client.post(
            "/alpha-portfolio/import/preview",
            json={"rawText": "Name;Weight\nASML Holding NV;100"},
        )
        body = response.json()
        assert body["rows"][0]["status"] == "RESOLVED"
        assert body["rows"][0]["ticker"] == "ASML"

    def test_a_genuinely_ambiguous_name_asks_one_clarification_question(self, client):
        response = client.post(
            "/alpha-portfolio/import/preview",
            json={"rawText": "Name;Weight\nBerkshire Hathaway Inc;100"},
        )
        body = response.json()
        row = body["rows"][0]
        assert row["status"] == "AMBIGUOUS"
        assert {c["ticker"] for c in row["candidates"]} == {"BRK-A", "BRK-B"}

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

    def test_a_bounded_abbreviation_match_is_suggested_for_confirmation(self, client):
        response = client.post(
            "/alpha-portfolio/import/preview",
            json={"rawText": "Name;Weight\nTaiwan Semicond Manufacturing;100"},
        )
        body = response.json()
        row = body["rows"][0]
        assert row["status"] == "SUGGESTED"
        assert row["ticker"] == "TSM"
        assert row["candidates"][0]["ticker"] == "TSM"


class TestResolutionsEndpoint:
    def test_remembering_a_resolution_makes_the_next_preview_resolve_it_directly(self, client):
        response = client.post(
            "/alpha-portfolio/import/resolutions",
            json={"resolutions": [{"originalName": "Zelkova Materials Group", "ticker": "ZKVA"}]},
        )
        assert response.status_code == 204

        preview = client.post(
            "/alpha-portfolio/import/preview",
            json={"rawText": "Name;Weight\nZelkova Materials Group;100"},
        )
        body = preview.json()
        assert body["rows"][0]["status"] == "RESOLVED"
        assert body["rows"][0]["ticker"] == "ZKVA"

    def test_a_blank_entry_is_silently_ignored(self, client):
        response = client.post(
            "/alpha-portfolio/import/resolutions",
            json={"resolutions": [{"originalName": "  ", "ticker": "  "}]},
        )
        assert response.status_code == 204
