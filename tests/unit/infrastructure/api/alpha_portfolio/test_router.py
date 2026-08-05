"""API tests for the Alpha Portfolio REST controller (Alpha Sprint 1A)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.core.infrastructure.api.app import create_app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_alpha_portfolio_state_table(engine)
    store = AlphaPortfolioStore(engine)

    app = create_app()
    app.dependency_overrides[get_alpha_portfolio_store] = lambda: store
    return TestClient(app)


class TestGetPortfolioBeforeEstablished:
    def test_returns_200_with_exists_false(self, client):
        response = client.get("/alpha-portfolio")
        assert response.status_code == 200
        assert response.json() == {"exists": False, **_empty_fields()}


class TestImportPortfolio:
    def test_returns_201_with_derived_view(self, client):
        response = client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [{"ticker": "NVDA", "weightPercent": 60}],
                "cashWeightPercent": 40,
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["exists"] is True
        assert body["entryMode"] == "IMPORTED"
        assert body["numberOfHoldings"] == 1
        assert body["hasAbsoluteValues"] is False
        assert body["totalValue"] is None

    def test_rejects_empty_holdings_with_400(self, client):
        response = client.post(
            "/alpha-portfolio/import", json={"holdings": [], "cashWeightPercent": None}
        )
        assert response.status_code == 400

    def test_percentages_alone_are_accepted_no_absolute_value_required(self, client):
        response = client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AMD", "weightPercent": 100}]},
        )
        assert response.status_code == 201

    def test_absolute_values_yield_a_real_total(self, client):
        response = client.post(
            "/alpha-portfolio/import",
            json={
                "holdings": [{"ticker": "NVDA", "weightPercent": 60, "valueAbsolute": 600}],
                "cashWeightPercent": 40,
                "cashValueAbsolute": 400,
            },
        )
        body = response.json()
        assert body["hasAbsoluteValues"] is True
        assert body["totalValue"] == 1000

    def test_get_after_import_reflects_the_established_state(self, client):
        client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "NVDA", "weightPercent": 100}]},
        )
        response = client.get("/alpha-portfolio")
        assert response.status_code == 200
        assert response.json()["exists"] is True


class TestFromScratch:
    def test_returns_201_with_empty_holdings(self, client):
        response = client.post(
            "/alpha-portfolio/from-scratch",
            json={"objective": "Grow capital", "horizon": "Long"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["exists"] is True
        assert body["entryMode"] == "FROM_SCRATCH"
        assert body["holdings"] == []
        assert body["objective"] == "Grow capital"
        assert body["horizon"] == "Long"

    def test_requires_objective(self, client):
        response = client.post(
            "/alpha-portfolio/from-scratch", json={"objective": "", "horizon": "Long"}
        )
        assert response.status_code == 400

    def test_requires_horizon(self, client):
        response = client.post(
            "/alpha-portfolio/from-scratch", json={"objective": "Grow", "horizon": ""}
        )
        assert response.status_code == 400


def _empty_fields() -> dict:
    return {
        "entryMode": None,
        "hasAbsoluteValues": False,
        "holdings": [],
        "cashWeightPercent": None,
        "cashValueAbsolute": None,
        "totalValue": None,
        "numberOfHoldings": 0,
        "concentrationLevel": None,
        "objective": None,
        "horizon": None,
    }
