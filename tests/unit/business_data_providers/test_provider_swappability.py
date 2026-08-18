"""Provider swappability (ATLAS-031, Phase 29) -- re-runs the
architecture proof ATLAS-022's own `test_extensibility.py` established
with a fake provider, this time with the two real providers this
sprint built. SEC EDGAR and Alpha Vantage have completely different
raw response shapes (nested XBRL facts-by-concept vs. two flat
key/value quote objects) and completely different identity resolution
(CIK lookup vs. bare ticker) -- proving both map into the identical
`RawBusinessDocument`/`BusinessRecord` shape with zero changes to
`business_data`, `business_facts`, `valuation.facts`, or any evaluator
is exactly what "provider-specific code stays at the boundary" means.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.service import refresh_company_data
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.canonical_security_gate.factory import build_identity_gate
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.providers import BusinessDataProvider
from atlas.business_data_providers.alpha_vantage import AlphaVantageMarketDataProvider
from atlas.business_data_providers.sec_edgar import SecEdgarFundamentalsProvider

_NOW = datetime(2026, 8, 9, tzinfo=timezone.utc)


def _new_engine():
    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})
    create_business_record_table(engine)
    return engine


def _identity_gate(engine) -> CanonicalSecurityIdentityGate:
    return build_identity_gate(engine)


@dataclass(frozen=True)
class _IdentityCorroboratorProvider:
    """Sprint O -- a `CompanyProfileProvider`-only fake reporting the
    exact same canonicalized company name as Alpha Vantage's own real
    `fetch_company_profile` response for TESTCO. Real
    `SecEdgarFundamentalsProvider` genuinely reports no identity fields
    at all (confirmed: its own CIK
    resolution discards the company `title` it briefly sees) and Alpha
    Vantage alone tops out at `MEDIUM` confidence (no `security_type`/
    `AssetType` in its own `_IDENTITY_FIELD_MAP`) -- so reaching
    `AUTO_ACCEPT` through the two *real* provider classes requires a
    second, independent corroborating identity claim. This fake stands
    in for that second claim (as e.g. a future OpenFIGI or Twelve Data
    adapter might supply) without inventing capability the real,
    unmodified providers do not have."""

    company_name: str

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        return ()

    def fetch_company_profile(
        self, *, company_identifier: str, evaluated_at: datetime
    ) -> tuple[RawBusinessDocument, ...]:
        return (
            RawBusinessDocument(
                identifier=f"{company_identifier}:corroborator-profile",
                company=company_identifier,
                source_kind="company_profile",
                published_at=evaluated_at,
                provider_id="sec_edgar",
                raw_reference="https://example.test/corroborator-profile",
                content_hash=f"corroborator-hash-{company_identifier}",
                language="en",
                metadata={"name": self.company_name},
            ),
        )


@dataclass(frozen=True)
class _IdentityProvider:
    """A `CompanyProfileProvider`-only fake supplying every field
    needed to reach `AUTO_ACCEPT` on its own (including `security_type`
    -- a field no real provider adapter supplies yet; see
    `_IdentityCorroboratorProvider`'s own docstring)."""

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


_TICKER_MAP = {"0": {"cik_str": 1234567, "ticker": "TESTCO", "title": "Test Co"}}
_COMPANYFACTS = {
    "facts": {
        "us-gaap": {
            "Revenues": {
                "units": {
                    "USD": [
                        {"start": "2022-01-01", "end": "2022-12-31", "val": 100, "form": "10-K", "fp": "FY", "filed": "2023-02-01"},
                        {"start": "2023-01-01", "end": "2023-12-31", "val": 120, "form": "10-K", "fp": "FY", "filed": "2024-02-01"},
                    ]
                }
            }
        }
    }
}


def _sec_fetcher(url: str, headers):
    if "company_tickers" in url:
        return _TICKER_MAP
    return _COMPANYFACTS


def _av_fetcher(url: str, headers):
    if "GLOBAL_QUOTE" in url:
        return {"Global Quote": {"05. price": "50.00", "07. latest trading day": "2026-08-07"}}
    if "TIME_SERIES_MONTHLY_ADJUSTED" in url:
        # Covers both SEC filing dates in _COMPANYFACTS (2023-02-01,
        # 2024-02-01) so ATLAS-032's historical second pass has a real
        # "first available close on or after" candidate for each.
        return {
            "Monthly Adjusted Time Series": {
                "2023-02-28": {"4. close": "40.00", "5. adjusted close": "40.00"},
                "2024-02-29": {"4. close": "45.00", "5. adjusted close": "45.00"},
            }
        }
    # A realistic OVERVIEW response (Name/Exchange/Country alongside
    # SharesOutstanding/Currency) -- Sprint O's own candidate mapper
    # reads these into a ProviderCandidate.
    return {
        "Symbol": "TESTCO",
        "Name": "TESTCO Inc.",
        "Exchange": "NASDAQ",
        "Country": "USA",
        "SharesOutstanding": "1000000",
        "Currency": "USD",
    }


class TestBothRealProvidersConformToTheProtocol:
    def test_sec_edgar_conforms(self):
        assert isinstance(SecEdgarFundamentalsProvider(_sec_fetcher), BusinessDataProvider)

    def test_alpha_vantage_conforms(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        assert isinstance(AlphaVantageMarketDataProvider(_av_fetcher), BusinessDataProvider)


class TestSwappedIntoTheSameRefreshUseCaseWithNoEvaluatorChange:
    def test_both_providers_produce_valid_persisted_records_through_the_identical_pipeline(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        engine = _new_engine()
        repository = SqlAlchemyBusinessRecordRepository(engine)

        providers: tuple[BusinessDataProvider, ...] = (
            SecEdgarFundamentalsProvider(_sec_fetcher),
            AlphaVantageMarketDataProvider(_av_fetcher),
            _IdentityCorroboratorProvider(company_name="TESTCO Inc."),
        )
        summary = refresh_company_data("TESTCO", providers, repository, identity_gate=_identity_gate(engine))

        assert summary.provider_errors == ()
        assert summary.identity_gate_outcome == "AUTO_ACCEPT"
        # 2 annual fundamentals periods + 1 current market snapshot +
        # 2 historical market snapshots (ATLAS-032, one per distinct
        # SEC filing date in _COMPANYFACTS: 2023-02-01, 2024-02-01) +
        # 2 company_profile documents (Alpha Vantage's own real
        # `fetch_company_profile` response, now the Identity Gate's
        # accepted candidate, plus `_IdentityCorroboratorProvider`'s
        # own corroborating claim -- Sprint O: real Alpha Vantage alone
        # tops out at MEDIUM confidence with no `security_type` in its
        # own `_IDENTITY_FIELD_MAP`, so a second independent
        # corroborating identity claim is what reaches AUTO_ACCEPT).
        assert summary.new_records == 7
        records = repository.get_by_company("TESTCO")
        document_types = {r.document_type.value for r in records}
        assert document_types == {"financial_statement", "market_data_snapshot", "company_profile"}
        market_records = [r for r in records if r.document_type.value == "market_data_snapshot"]
        assert len(market_records) == 3

    def test_a_third_structurally_different_fake_provider_also_swaps_in_cleanly(self, monkeypatch):
        """A fake provider with yet another shape (a static in-memory
        tuple, no network at all -- `StaticBusinessDataProvider`'s own
        pattern) proves this isn't just "two providers happen to work,"
        it's the Protocol itself doing the work."""
        from atlas.analysis_engine.business_data.models import RawBusinessDocument
        from atlas.analysis_engine.business_data.providers import StaticBusinessDataProvider

        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        engine = _new_engine()
        repository = SqlAlchemyBusinessRecordRepository(engine)

        static_provider = StaticBusinessDataProvider(
            documents=(
                RawBusinessDocument(
                    identifier="TESTCO:manual:2023",
                    company="TESTCO",
                    source_kind="manual_document",
                    published_at=_NOW,
                    provider_id="manual_upload",
                    raw_reference="file://manual.pdf",
                    content_hash="manual-hash",
                    language="en",
                    metadata={"revenue": 999.0, "currency": "USD"},
                ),
            )
        )
        # A single fake CompanyProfileProvider carrying every field
        # (including `security_type`, which no real provider adapter
        # supplies yet) is enough to reach AUTO_ACCEPT alone -- this
        # test is about a third provider *shape* swapping in cleanly,
        # not about identity corroboration, which the first test above
        # already covers.
        identity = _IdentityProvider(tickers=("TESTCO",))
        providers: tuple[BusinessDataProvider, ...] = (
            SecEdgarFundamentalsProvider(_sec_fetcher),
            static_provider,
            identity,
        )
        summary = refresh_company_data("TESTCO", providers, repository, identity_gate=_identity_gate(engine))
        assert summary.provider_errors == ()
        assert summary.new_records == 4  # 2 SEC periods + 1 manual document + identity/profile


class TestSprintO1RealAlphaVantageAloneReachesAutoAccept:
    """Sprint O.1's own end-to-end proof: the real, unmodified-besides-
    `AssetType`-extraction `AlphaVantageMarketDataProvider` -- no
    synthetic `_IdentityCorroboratorProvider`, no second identity
    source of any kind -- reaches `AUTO_ACCEPT` through
    `refresh_company_data`'s real `identity_gate`, using only a
    realistic `OVERVIEW` payload shape (the same fields Alpha Vantage's
    own documentation confirms it returns, `AssetType` included)."""

    def test_sec_edgar_plus_real_alpha_vantage_with_asset_type_reaches_auto_accept_alone(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        engine = _new_engine()
        repository = SqlAlchemyBusinessRecordRepository(engine)

        def _av_fetcher_with_asset_type(url: str, headers):
            if "GLOBAL_QUOTE" in url:
                return {"Global Quote": {"05. price": "50.00", "07. latest trading day": "2026-08-07"}}
            if "TIME_SERIES_MONTHLY_ADJUSTED" in url:
                return {"Monthly Adjusted Time Series": {}}
            return {
                "Symbol": "TESTCO",
                "Name": "TESTCO Inc.",
                "AssetType": "Common Stock",
                "Exchange": "NASDAQ",
                "Country": "USA",
                "SharesOutstanding": "1000000",
                "Currency": "USD",
            }

        providers: tuple[BusinessDataProvider, ...] = (
            SecEdgarFundamentalsProvider(_sec_fetcher),
            AlphaVantageMarketDataProvider(_av_fetcher_with_asset_type),
        )
        summary = refresh_company_data("TESTCO", providers, repository, identity_gate=_identity_gate(engine))

        assert summary.provider_errors == ()
        assert summary.identity_gate_outcome == "AUTO_ACCEPT"
        records = repository.get_by_company("TESTCO")
        assert len(records) == 4  # 2 SEC fundamentals periods + 1 market snapshot + 1 company_profile
        assert all(r.canonical_security_id is not None for r in records)
