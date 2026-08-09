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

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.service import refresh_company_data
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.analysis_engine.business_data.providers import BusinessDataProvider
from atlas.business_data_providers.alpha_vantage import AlphaVantageMarketDataProvider
from atlas.business_data_providers.sec_edgar import SecEdgarFundamentalsProvider

_NOW = datetime(2026, 8, 9, tzinfo=timezone.utc)

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
    return {"Symbol": "TESTCO", "SharesOutstanding": "1000000", "Currency": "USD"}


class TestBothRealProvidersConformToTheProtocol:
    def test_sec_edgar_conforms(self):
        assert isinstance(SecEdgarFundamentalsProvider(_sec_fetcher), BusinessDataProvider)

    def test_alpha_vantage_conforms(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        assert isinstance(AlphaVantageMarketDataProvider(_av_fetcher), BusinessDataProvider)


class TestSwappedIntoTheSameRefreshUseCaseWithNoEvaluatorChange:
    def test_both_providers_produce_valid_persisted_records_through_the_identical_pipeline(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})
        create_business_record_table(engine)
        repository = SqlAlchemyBusinessRecordRepository(engine)

        providers: tuple[BusinessDataProvider, ...] = (
            SecEdgarFundamentalsProvider(_sec_fetcher),
            AlphaVantageMarketDataProvider(_av_fetcher),
        )
        summary = refresh_company_data("TESTCO", providers, repository)

        assert summary.provider_errors == ()
        assert summary.new_records == 3  # 2 annual fundamentals periods + 1 market snapshot
        records = repository.get_by_company("TESTCO")
        document_types = {r.document_type.value for r in records}
        assert document_types == {"financial_statement", "market_data_snapshot"}

    def test_a_third_structurally_different_fake_provider_also_swaps_in_cleanly(self, monkeypatch):
        """A fake provider with yet another shape (a static in-memory
        tuple, no network at all -- `StaticBusinessDataProvider`'s own
        pattern) proves this isn't just "two providers happen to work,"
        it's the Protocol itself doing the work."""
        from atlas.analysis_engine.business_data.models import RawBusinessDocument
        from atlas.analysis_engine.business_data.providers import StaticBusinessDataProvider

        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})
        create_business_record_table(engine)
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
        providers: tuple[BusinessDataProvider, ...] = (
            SecEdgarFundamentalsProvider(_sec_fetcher),
            static_provider,
        )
        summary = refresh_company_data("TESTCO", providers, repository)
        assert summary.provider_errors == ()
        assert summary.new_records == 3  # 2 SEC periods + 1 manual document
