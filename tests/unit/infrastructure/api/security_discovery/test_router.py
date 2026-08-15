"""Sprint 21 -- exercises `GET /security-discovery` end-to-end through
the real app, with `get_security_discovery_indexes` overridden to a
fixed, real-data-shaped index (copied verbatim from Sprint 19's own
fixture) so tests never make a real network call to SEC. Nothing else
is mocked."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from atlas.alpha.security_discovery.api.dependencies import get_security_discovery_indexes
from atlas.alpha.security_discovery.models import SecTickerEntry
from atlas.alpha.security_discovery.service import build_ticker_index, build_title_index
from atlas.core.infrastructure.api.app import create_app

_REAL_SEC_FIXTURE = (
    SecTickerEntry(cik=1045810, ticker="NVDA", title="NVIDIA CORP"),
    SecTickerEntry(cik=1067983, ticker="BRK-A", title="BERKSHIRE HATHAWAY INC"),
    SecTickerEntry(cik=1067983, ticker="BRK-B", title="BERKSHIRE HATHAWAY INC"),
    SecTickerEntry(cik=1652044, ticker="GOOGL", title="Alphabet Inc."),
    SecTickerEntry(cik=1652044, ticker="GOOG", title="Alphabet Inc."),
    SecTickerEntry(cik=320193, ticker="AAPL", title="Apple Inc."),
)


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    title_index = build_title_index(_REAL_SEC_FIXTURE)
    ticker_index = build_ticker_index(_REAL_SEC_FIXTURE)
    app.dependency_overrides[get_security_discovery_indexes] = lambda: (title_index, ticker_index)
    return TestClient(app)


class TestTickerExact:
    def test_ticker_query_returns_single_candidate(self, client: TestClient) -> None:
        response = client.get("/security-discovery", params={"query": "NVDA"})
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["ticker"] == "NVDA"
        assert body[0]["discoveryMethod"] == "ticker_exact"
        assert body[0]["status"] == "candidate_only"


class TestTitleCanonical:
    def test_company_name_resolves_via_title(self, client: TestClient) -> None:
        response = client.get("/security-discovery", params={"query": "NVIDIA"})
        body = response.json()
        assert len(body) == 1
        assert body[0]["ticker"] == "NVDA"
        assert body[0]["displayName"] == "NVIDIA CORP"
        assert body[0]["discoveryMethod"] == "title_canonical"


class TestAmbiguousArray:
    def test_berkshire_returns_both_share_classes_unranked(self, client: TestClient) -> None:
        response = client.get("/security-discovery", params={"query": "Berkshire Hathaway"})
        body = response.json()
        tickers = {c["ticker"] for c in body}
        assert tickers == {"BRK-A", "BRK-B"}
        for candidate in body:
            assert "confidence" not in candidate
            assert "score" not in candidate
            assert "recommended" not in candidate

    def test_alphabet_returns_all_real_candidates(self, client: TestClient) -> None:
        response = client.get("/security-discovery", params={"query": "Alphabet"})
        tickers = {c["ticker"] for c in response.json()}
        assert tickers == {"GOOG", "GOOGL"}


class TestZeroCandidates:
    def test_unknown_query_returns_empty_array_not_404(self, client: TestClient) -> None:
        response = client.get("/security-discovery", params={"query": "Completely Unknown Company XYZ"})
        assert response.status_code == 200
        assert response.json() == []

    def test_empty_query_returns_empty_array(self, client: TestClient) -> None:
        response = client.get("/security-discovery", params={"query": ""})
        assert response.status_code == 200
        assert response.json() == []

    def test_missing_query_param_returns_empty_array(self, client: TestClient) -> None:
        response = client.get("/security-discovery")
        assert response.status_code == 200
        assert response.json() == []


class TestQueryValidation:
    def test_overlong_query_returns_422(self, client: TestClient) -> None:
        response = client.get("/security-discovery", params={"query": "x" * 201})
        assert response.status_code == 422


class TestDeterminism:
    def test_repeated_calls_return_identical_results(self, client: TestClient) -> None:
        first = client.get("/security-discovery", params={"query": "Alphabet"}).json()
        second = client.get("/security-discovery", params={"query": "Alphabet"}).json()
        assert first == second


class TestNoRankingField:
    def test_response_never_carries_a_ranking_or_confidence_field(self, client: TestClient) -> None:
        response = client.get("/security-discovery", params={"query": "Apple"})
        body = response.json()
        assert len(body) == 1
        assert set(body[0].keys()) == {
            "ticker",
            "displayName",
            "cik",
            "discoveryMethod",
            "source",
            "status",
        }
