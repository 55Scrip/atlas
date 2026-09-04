"""End-to-end provider symbol routing through `refresh_company_data`.

Atlas knows Berkshire Class B as `BRK.B`; Alpha Vantage answers only to
`BRK-B`. Routing the request out is the easy half. The half that can go
wrong quietly is the answer coming back: providers stamp `company` on
their documents from whatever symbol they were handed, so a routed
fetch that is not brought back under Atlas's own name would persist
records under `BRK-B` -- the provider's spelling leaking into the field
the portfolio, every join, and the security-provenance work all key on.

Every provider here is a fake with no network, by construction and by
`tests/conftest.py`'s socket guard.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.models import EnrichmentDepth
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.service import refresh_company_data
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.canonical_security_gate.factory import (
    build_identity_gate,
    build_provider_symbol_resolver,
)
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.sources import SourceKind

_NOW = datetime(2026, 9, 4, tzinfo=timezone.utc)
_CANONICAL = "BRK.B"
_PROVIDER_SYMBOL = "BRK-B"


class _RecordingProvider:
    """Stamps `company` from whatever symbol it is handed -- exactly
    what the real Alpha Vantage provider does."""

    canonical_provider_name = "ALPHA_VANTAGE"

    def __init__(self) -> None:
        self.symbols_received: list[str] = []

    def fetch_company_profile(self, *, company_identifier: str, evaluated_at: datetime):
        self.symbols_received.append(company_identifier)
        return (
            RawBusinessDocument(
                identifier=f"{company_identifier}:profile",
                company=company_identifier,
                source_kind=SourceKind.COMPANY_PROFILE.value,
                published_at=evaluated_at,
                provider_id="alpha_vantage",
                raw_reference=f"av://{company_identifier}",
                content_hash=f"hash-{company_identifier}-profile",
                language="en",
                metadata={
                    "name": "Berkshire Hathaway Inc", "exchange": "NYSE", "country": "USA",
                    "currency": "USD", "asset_type": "Common Stock",
                },
            ),
        )

    def fetch(self, *, company_identifier: str, evaluated_at: datetime):
        self.symbols_received.append(company_identifier)
        return (
            RawBusinessDocument(
                identifier=f"{company_identifier}:quote",
                company=company_identifier,
                source_kind=SourceKind.MARKET_DATA_SNAPSHOT.value,
                published_at=evaluated_at,
                provider_id="alpha_vantage",
                raw_reference=f"av://{company_identifier}/quote",
                content_hash=f"hash-{company_identifier}-quote",
                period_end=date(2026, 9, 4),
                language="en",
                metadata={"price": "512.40", "currency": "USD"},
            ),
        )


class _SecProvider(_RecordingProvider):
    canonical_provider_name = "SEC_EDGAR"


@pytest.fixture
def harness():
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_business_record_table(engine)
    gate = build_identity_gate(engine)
    with engine.begin() as connection:
        connection.execute(text(
            "insert into provider_symbol_routes "
            "(provider_name, canonical_ticker, provider_symbol, evidence, recorded_at) "
            "values ('ALPHA_VANTAGE', :t, :s, 'live-verified', :now)"
        ), {"t": _CANONICAL, "s": _PROVIDER_SYMBOL, "now": _NOW.isoformat()})
    resolver = build_provider_symbol_resolver(engine)
    return engine, SqlAlchemyBusinessRecordRepository(engine), gate, resolver


def _run(harness, provider, *, depth=EnrichmentDepth.FULL):
    engine, repository, gate, resolver = harness
    summary = refresh_company_data(
        _CANONICAL, (provider,), repository, identity_gate=gate,
        depth=depth, provider_symbol=resolver,
    )
    return summary, repository, engine


class TestTheRequestGoesOutRouted:
    def test_alpha_vantage_receives_the_provider_symbol(self, harness):
        provider = _RecordingProvider()
        _run(harness, provider, depth=EnrichmentDepth.MINIMAL)
        assert provider.symbols_received == [_PROVIDER_SYMBOL]

    def test_sec_receives_the_canonical_ticker_unchanged(self, harness):
        """Same security, same run shape, different provider: the Alpha
        Vantage route must not reach SEC."""
        provider = _SecProvider()
        _run(harness, provider, depth=EnrichmentDepth.MINIMAL)
        assert provider.symbols_received == [_CANONICAL]

    def test_without_a_resolver_nothing_is_routed(self, harness):
        """The default path is unchanged for every caller that does not
        opt in."""
        engine, repository, gate, _ = harness
        provider = _RecordingProvider()
        refresh_company_data(_CANONICAL, (provider,), repository, identity_gate=gate,
                             depth=EnrichmentDepth.MINIMAL)
        assert provider.symbols_received == [_CANONICAL]


class TestTheAnswerComesBackCanonical:
    def test_records_are_stored_under_the_canonical_ticker(self, harness):
        provider = _RecordingProvider()
        _, repository, _ = _run(harness, provider, depth=EnrichmentDepth.MINIMAL)
        companies = {r.company for r in repository.get_by_company(_CANONICAL)}
        assert companies == {_CANONICAL}

    def test_no_record_is_ever_stored_under_the_provider_symbol(self, harness):
        provider = _RecordingProvider()
        _, repository, engine = _run(harness, provider)
        with engine.connect() as connection:
            leaked = connection.execute(text(
                "select count(*) from business_records where company = :s"
            ), {"s": _PROVIDER_SYMBOL}).scalar_one()
        assert leaked == 0

    def test_market_data_fetched_through_the_route_stays_on_the_canonical_security(self, harness):
        """The requirement in full: a snapshot requested as `BRK-B`
        must end up attached to the `BRK.B` security, not orphaned
        under the provider's spelling."""
        provider = _RecordingProvider()
        _, repository, _ = _run(harness, provider)
        snapshots = [r for r in repository.get_by_company(_CANONICAL)
                     if r.document_type == SourceKind.MARKET_DATA_SNAPSHOT]
        assert snapshots, "the routed market-data fetch produced no record"
        assert all(r.company == _CANONICAL for r in snapshots)
        assert all(r.canonical_security_id is not None for r in snapshots)


class TestIdentityIsNotDuplicated:
    def test_the_security_keeps_the_canonical_ticker(self, harness):
        provider = _RecordingProvider()
        _, _, engine = _run(harness, provider, depth=EnrichmentDepth.MINIMAL)
        with engine.connect() as connection:
            tickers = [r[0] for r in connection.execute(text(
                "select native_ticker from canonical_securities"))]
        assert tickers == [_CANONICAL]

    def test_no_second_security_is_created_for_the_provider_symbol(self, harness):
        provider = _RecordingProvider()
        _, _, engine = _run(harness, provider, depth=EnrichmentDepth.MINIMAL)
        with engine.connect() as connection:
            assert connection.execute(text(
                "select count(*) from canonical_securities where native_ticker = :s"
            ), {"s": _PROVIDER_SYMBOL}).scalar_one() == 0

    def test_routing_creates_no_second_issuer(self, harness):
        """A differing provider notation is not a differing company."""
        provider = _RecordingProvider()
        _, _, engine = _run(harness, provider, depth=EnrichmentDepth.MINIMAL)
        with engine.connect() as connection:
            assert connection.execute(text(
                "select count(*) from canonical_issuers")).scalar_one() == 1

    def test_a_repeated_run_is_stable(self, harness):
        """Determinism: routing twice creates nothing new."""
        engine, repository, gate, resolver = harness
        for _ in range(2):
            refresh_company_data(_CANONICAL, (_RecordingProvider(),), repository,
                                 identity_gate=gate, depth=EnrichmentDepth.MINIMAL,
                                 provider_symbol=resolver)
        with engine.connect() as connection:
            assert connection.execute(text(
                "select count(*) from canonical_securities")).scalar_one() == 1
            assert connection.execute(text(
                "select count(*) from canonical_issuers")).scalar_one() == 1


class TestSafetyOfNeighbouringTickers:
    @pytest.mark.parametrize("ticker", ["BRK.A", "SU.PA", "SU"])
    def test_an_unrouted_ticker_reaches_the_provider_untouched(self, harness, ticker):
        """`BRK.A` is a different share class; `SU`/`SU.PA` are
        different companies. None has a stored route, so none is
        rewritten."""
        _, repository, gate, resolver = harness
        provider = _RecordingProvider()
        refresh_company_data(ticker, (provider,), repository, identity_gate=gate,
                             depth=EnrichmentDepth.MINIMAL, provider_symbol=resolver)
        assert provider.symbols_received == [ticker]
