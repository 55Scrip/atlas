"""End-to-end proof that `POST /alpha-portfolio/import` now triggers
background enrichment for every holding, and that
`POST /alpha-portfolio/enrich` gives an already-imported portfolio a
clean backfill path (Internal Alpha Fix Sprint 1, Part 1 -- confirmed
root cause IA-001).

Fake providers throughout (no network) -- monkeypatches the router's
own module-level `get_default_business_data_providers` reference
directly, the same pattern this codebase already uses for provider
substitution elsewhere. `TestClient` runs a `BackgroundTasks` callable
to completion before `.post()`/`.get()` returns control to the test
(documented Starlette/FastAPI behavior), so no polling or sleeping is
needed to observe the result.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

import atlas.alpha.portfolio.api.router as portfolio_router
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.core.infrastructure.api.app import create_app
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.decision.table import create_decision_table

_EVALUATED_AT = datetime(2026, 8, 9, tzinfo=timezone.utc)


@dataclass(frozen=True)
class _FakeProvider:
    documents: tuple[RawBusinessDocument, ...] = ()
    exception: Exception | None = None

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        if self.exception is not None:
            raise self.exception
        return tuple(d for d in self.documents if d.company == company_identifier)


def _doc(*, identifier: str, company: str, revenue: float = 100.0) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=identifier,
        company=company,
        source_kind="financial_statement",
        published_at=_EVALUATED_AT,
        provider_id="fake_provider",
        raw_reference="https://example.test/doc",
        content_hash=f"hash-{identifier}",
        language="en",
        metadata={"revenue": revenue, "currency": "USD"},
    )


@dataclass(frozen=True)
class _IdentityProvider:
    """Sprint O -- a `CompanyProfileProvider`-only fake supplying
    exactly the identity fields the Identity Gate needs to reach
    `AUTO_ACCEPT` (see `business_data_refresh/test_service.py`'s
    identically-shaped helper for the full rationale)."""

    tickers: tuple[str, ...]

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        return ()

    def fetch_company_profile(
        self, *, company_identifier: str, evaluated_at: datetime
    ) -> tuple[RawBusinessDocument, ...]:
        if company_identifier not in self.tickers:
            return ()
        return (
            RawBusinessDocument(
                identifier=f"{company_identifier}:identity-profile",
                company=company_identifier,
                source_kind="company_profile",
                published_at=evaluated_at,
                provider_id="alpha_vantage",
                raw_reference="https://example.test/identity-profile",
                content_hash=f"identity-hash-{company_identifier}",
                language="en",
                metadata={
                    "name": f"{company_identifier} Inc.",
                    "exchange": "NASDAQ",
                    "country": "USA",
                    "currency": "USD",
                    "security_type": "COMMON_STOCK",
                },
            ),
        )


def _identity_provider(*tickers: str) -> _IdentityProvider:
    return _IdentityProvider(tickers=tuple(tickers))


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_decision_table(engine)
    create_business_record_table(engine)
    return engine


@pytest.fixture
def client(engine, monkeypatch):
    # Both the request-scoped `Depends(get_decision_engine)` calls AND
    # the background task's own direct call resolve to this exact
    # in-memory engine -- one isolated dataset per test, never the real
    # `database/atlas.db`.
    monkeypatch.setattr(portfolio_router, "get_decision_engine", lambda: engine)
    app = create_app()
    app.dependency_overrides[get_decision_engine] = lambda: engine
    return TestClient(app)


def _set_fake_providers(monkeypatch, *providers) -> None:
    monkeypatch.setattr(portfolio_router, "get_default_business_data_providers", lambda: providers)


def _business_record_repository(engine) -> SqlAlchemyBusinessRecordRepository:
    return SqlAlchemyBusinessRecordRepository(engine)


class TestImportTriggersBackgroundEnrichment:
    def test_a_freshly_imported_holding_is_enriched_by_the_time_import_returns(self, client, engine, monkeypatch):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2024", company="AAPL"),))
        _set_fake_providers(monkeypatch, provider, _identity_provider("AAPL"))

        response = client.post("/alpha-portfolio/import", json={"holdings": [{"ticker": "AAPL", "weightPercent": 100.0}]})
        assert response.status_code == 201

        records = _business_record_repository(engine).get_by_company("AAPL")
        assert len(records) == 2  # fundamentals + identity/profile

    def test_import_still_succeeds_even_when_every_provider_fails(self, client, monkeypatch):
        """IA-001's own requirement: import and enrichment are related
        but separate transactions -- a total provider outage must never
        fail the import itself."""
        _set_fake_providers(monkeypatch, _FakeProvider(exception=RuntimeError("provider outage")))
        response = client.post("/alpha-portfolio/import", json={"holdings": [{"ticker": "AAPL", "weightPercent": 100.0}]})
        assert response.status_code == 201
        assert response.json()["holdings"][0]["ticker"] == "AAPL"

    def test_multiple_holdings_are_each_independently_enriched(self, client, engine, monkeypatch):
        provider = _FakeProvider(
            documents=(
                _doc(identifier="AAPL:FY:2024", company="AAPL"),
                _doc(identifier="MSFT:FY:2024", company="MSFT"),
            )
        )
        _set_fake_providers(monkeypatch, provider, _identity_provider("AAPL", "MSFT"))
        response = client.post(
            "/alpha-portfolio/import",
            json={"holdings": [{"ticker": "AAPL", "weightPercent": 50.0}, {"ticker": "MSFT", "weightPercent": 50.0}]},
        )
        assert response.status_code == 201
        repository = _business_record_repository(engine)
        assert len(repository.get_by_company("AAPL")) == 2  # fundamentals + identity/profile
        assert len(repository.get_by_company("MSFT")) == 2

    def test_an_unsupported_ticker_fails_honestly_and_persists_nothing(self, client, engine, monkeypatch):
        _set_fake_providers(monkeypatch, _FakeProvider(documents=()))
        response = client.post("/alpha-portfolio/import", json={"holdings": [{"ticker": "ZZZZ", "weightPercent": 100.0}]})
        assert response.status_code == 201
        assert len(_business_record_repository(engine).get_by_company("ZZZZ")) == 0


class TestExplicitEnrichBackfillEndpoint:
    def test_no_portfolio_established_returns_404(self, client):
        response = client.post("/alpha-portfolio/enrich")
        assert response.status_code == 404

    def test_enriches_every_current_holding_of_an_already_imported_portfolio(self, client, engine, monkeypatch):
        """Import with no providers configured (so no data lands),
        exactly like a real bulk-imported portfolio pre-fix. The
        explicit `/enrich` call afterward is the "clean way to enrich
        an already imported portfolio... without deleting and
        re-importing it" this endpoint exists for."""
        _set_fake_providers(monkeypatch, _FakeProvider(documents=()))
        import_response = client.post(
            "/alpha-portfolio/import", json={"holdings": [{"ticker": "AAPL", "weightPercent": 100.0}]}
        )
        assert import_response.status_code == 201
        assert len(_business_record_repository(engine).get_by_company("AAPL")) == 0

        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2024", company="AAPL"),))
        _set_fake_providers(monkeypatch, provider, _identity_provider("AAPL"))
        enrich_response = client.post("/alpha-portfolio/enrich")
        assert enrich_response.status_code == 202
        assert enrich_response.json()["scheduledTickers"] == ["AAPL"]
        assert len(_business_record_repository(engine).get_by_company("AAPL")) == 2  # fundamentals + identity/profile

    def test_case_id_is_unchanged_by_enrichment(self, client, monkeypatch):
        """No duplicate Cases: `enrich_holdings` never touches Case
        creation at all -- the same `case_id` from import must still be
        the one linked after `/enrich` runs."""
        _set_fake_providers(monkeypatch, _FakeProvider(documents=()))
        import_body = client.post(
            "/alpha-portfolio/import", json={"holdings": [{"ticker": "AAPL", "weightPercent": 100.0}]}
        ).json()
        case_id_before = import_body["holdings"][0]["caseId"]

        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2024", company="AAPL"),))
        _set_fake_providers(monkeypatch, provider)
        client.post("/alpha-portfolio/enrich")

        after_body = client.get("/alpha-portfolio").json()
        case_id_after = after_body["holdings"][0]["caseId"]
        assert case_id_after == case_id_before

    def test_an_already_enriched_holding_is_skipped_on_a_second_enrich_call(self, client, engine, monkeypatch):
        provider = _FakeProvider(documents=(_doc(identifier="AAPL:FY:2024", company="AAPL"),))
        _set_fake_providers(monkeypatch, provider, _identity_provider("AAPL"))
        client.post("/alpha-portfolio/import", json={"holdings": [{"ticker": "AAPL", "weightPercent": 100.0}]})
        assert len(_business_record_repository(engine).get_by_company("AAPL")) == 2  # fundamentals + identity/profile

        calling_provider = _FakeProvider(exception=AssertionError("must never be called again"))
        _set_fake_providers(monkeypatch, calling_provider)
        response = client.post("/alpha-portfolio/enrich")
        assert response.status_code == 202
        # No new records, no duplicates -- still exactly two.
        assert len(_business_record_repository(engine).get_by_company("AAPL")) == 2
