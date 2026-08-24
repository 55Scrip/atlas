"""Price freshness / price-only refresh (Internal Alpha Stabilization
1, MSFT price root cause fix) -- end to end through the real HTTP
surface, following the exact fixture/helper pattern
`test_company_data_foundation_v1_scenarios.py` already established.

The real `AlphaVantageMarketDataProvider` is replaced with a small
in-process fake via `app.dependency_overrides` (matching this
codebase's own established override pattern for `get_decision_engine`)
so these tests never touch the network and can deterministically drive
success/failure outcomes.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.api.dependencies import (
    get_alpha_vantage_price_provider,
    get_alpha_vantage_quota_tracker,
    get_price_refresh_coordinator,
)
from atlas.alpha.business_data_refresh.price_refresh import PriceRefreshCoordinator
from atlas.alpha.business_data_refresh.quota import AlphaVantageQuotaTracker
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.business_data_providers.errors import RateLimited
from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.decision.table import create_decision_table

_NOW = datetime(2026, 8, 24, 12, tzinfo=timezone.utc)
_STALE_TRADING_DAY = date(2026, 8, 7)
_FRESH_TRADING_DAY = date(2026, 8, 21)


class _FakePriceProvider:
    """Records every call and returns a canned `RawBusinessDocument`
    (success mode) or raises (failure mode) -- never touches the
    network, unlike the real `AlphaVantageMarketDataProvider`."""

    def __init__(self, *, price: float = 483.24, trading_day: str = "2026-08-24", raises: Exception | None = None) -> None:
        self.calls: list[str] = []
        self._price = price
        self._trading_day = trading_day
        self._raises = raises

    def fetch_price_only(self, *, company_identifier, evaluated_at, known_currency, known_shares_outstanding):
        self.calls.append(company_identifier)
        if self._raises is not None:
            raise self._raises
        return RawBusinessDocument(
            identifier=f"{company_identifier}:snapshot:{self._trading_day}",
            company=company_identifier,
            source_kind="market_data_snapshot",
            published_at=evaluated_at,
            provider_id="alpha_vantage",
            raw_reference="https://example.test/quote",
            content_hash=f"hash-{company_identifier}-{self._price}-{self._trading_day}",
            language="en",
            period_start=date.fromisoformat(self._trading_day),
            period_end=date.fromisoformat(self._trading_day),
            metadata={"share_price": self._price, "currency": known_currency, "shares_outstanding": known_shares_outstanding},
        )


@pytest.fixture
def fake_price_provider():
    return _FakePriceProvider()


@pytest.fixture
def client(fake_price_provider):
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(engine)
    app = create_app()
    app.dependency_overrides[get_decision_engine] = lambda: engine
    app.dependency_overrides[get_alpha_vantage_price_provider] = lambda: fake_price_provider
    app.dependency_overrides[get_alpha_vantage_quota_tracker] = lambda: AlphaVantageQuotaTracker(engine)
    app.dependency_overrides[get_price_refresh_coordinator] = PriceRefreshCoordinator
    test_client = TestClient(app)
    test_client.engine = engine  # type: ignore[attr-defined]
    return test_client


def _import_holding(client, ticker: str, weight_percent: float = 100.0) -> str:
    response = client.post(
        "/alpha-portfolio/import",
        json={"holdings": [{"ticker": ticker, "weightPercent": weight_percent}]},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    case_id = next(h["caseId"] for h in body["holdings"] if h["ticker"] == ticker)
    assert case_id is not None
    return case_id


def _snapshot_document(*, ticker: str, trading_day: date, share_price: float = 499.99) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=f"{ticker}:snapshot:{trading_day.isoformat()}",
        company=ticker,
        source_kind="market_data_snapshot",
        published_at=datetime.combine(trading_day, datetime.min.time(), tzinfo=timezone.utc),
        provider_id="alpha_vantage",
        raw_reference="https://example.test/quote",
        content_hash=f"hash-snapshot-{ticker}-{trading_day.isoformat()}",
        language="en",
        period_start=trading_day,
        period_end=trading_day,
        metadata={"share_price": share_price, "currency": "USD", "shares_outstanding": 7425545000.0},
    )


def _persist(client, *documents: RawBusinessDocument) -> None:
    engine = client.engine
    create_business_record_table(engine)
    repository = SqlAlchemyBusinessRecordRepository(engine)
    for document in documents:
        result = ingest(document, evaluated_at=_NOW)
        assert isinstance(result, IngestedRecord), result
        repository.add(result.record)


class TestFreshnessFieldOnAnalysisEndpoint:
    def test_fresh_snapshot_reports_fresh_and_never_calls_the_provider(self, client, fake_price_provider):
        case_id = _import_holding(client, "MSFT")
        _persist(client, _snapshot_document(ticker="MSFT", trading_day=_FRESH_TRADING_DAY))

        body = client.get(f"/cases/{case_id}/analysis").json()

        assert body["marketSnapshot"]["priceFreshness"] == "fresh"
        assert fake_price_provider.calls == []

    def test_stale_snapshot_is_shown_immediately_and_schedules_a_background_refresh(self, client, fake_price_provider):
        case_id = _import_holding(client, "MSFT")
        _persist(client, _snapshot_document(ticker="MSFT", trading_day=_STALE_TRADING_DAY, share_price=499.99))

        body = client.get(f"/cases/{case_id}/analysis").json()

        assert body["marketSnapshot"]["sharePrice"] == 499.99
        assert body["marketSnapshot"]["priceFreshness"] == "stale"
        assert fake_price_provider.calls == ["MSFT"]

    def test_a_second_request_after_the_background_refresh_shows_the_new_snapshot(self, client):
        case_id = _import_holding(client, "MSFT")
        _persist(client, _snapshot_document(ticker="MSFT", trading_day=_STALE_TRADING_DAY, share_price=499.99))

        client.get(f"/cases/{case_id}/analysis")  # triggers the background refresh (TestClient runs it inline)
        body = client.get(f"/cases/{case_id}/analysis").json()

        assert body["marketSnapshot"]["sharePrice"] == 483.24

    def test_no_market_snapshot_at_all_never_calls_the_provider(self, client, fake_price_provider):
        case_id = _import_holding(client, "MSFT")

        body = client.get(f"/cases/{case_id}/analysis").json()

        assert body["marketSnapshot"] is None
        assert fake_price_provider.calls == []


class TestManualRefreshEndpoint:
    def test_successful_manual_refresh_returns_the_new_freshness_and_succeeds(self, client):
        case_id = _import_holding(client, "MSFT")
        _persist(client, _snapshot_document(ticker="MSFT", trading_day=_STALE_TRADING_DAY, share_price=499.99))

        response = client.post(f"/cases/{case_id}/refresh-price")

        assert response.status_code == 200
        body = response.json()
        assert body["attempted"] is True
        assert body["succeeded"] is True

    def test_manual_refresh_for_an_unknown_case_returns_404(self, client):
        response = client.post("/cases/00000000-0000-0000-0000-000000000099/refresh-price")
        assert response.status_code == 404

    def test_manual_refresh_is_deduplicated_while_already_in_flight(self, client, fake_price_provider):
        case_id = _import_holding(client, "MSFT")
        _persist(client, _snapshot_document(ticker="MSFT", trading_day=_STALE_TRADING_DAY, share_price=499.99))
        coordinator = client.app.dependency_overrides[get_price_refresh_coordinator]()
        client.app.dependency_overrides[get_price_refresh_coordinator] = lambda: coordinator
        coordinator.try_start("MSFT")

        response = client.post(f"/cases/{case_id}/refresh-price")

        assert response.status_code == 200
        body = response.json()
        assert body["attempted"] is False
        assert body["succeeded"] is False
        assert fake_price_provider.calls == []

    def test_manual_refresh_never_discards_the_last_good_price_on_provider_failure(self, client):
        case_id = _import_holding(client, "MSFT")
        _persist(client, _snapshot_document(ticker="MSFT", trading_day=_STALE_TRADING_DAY, share_price=499.99))
        client.app.dependency_overrides[get_alpha_vantage_price_provider] = lambda: _FakePriceProvider(
            raises=RateLimited("rate limited")
        )

        response = client.post(f"/cases/{case_id}/refresh-price")

        assert response.status_code == 200
        body = response.json()
        assert body["attempted"] is True
        assert body["succeeded"] is False
        assert body["priceFreshness"] == "failed"

        follow_up = client.get(f"/cases/{case_id}/analysis").json()
        assert follow_up["marketSnapshot"]["sharePrice"] == 499.99
