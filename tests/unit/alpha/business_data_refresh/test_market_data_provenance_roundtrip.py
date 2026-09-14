"""Historical Market-Data Provenance survives the database: provider payload
-> adapter -> BusinessRecord -> SQL row -> reload, with the price basis,
raw close, dividend, retrieval time and share-count filing provenance
unchanged. In-memory SQLite, fake fetchers, no network."""
from __future__ import annotations

from datetime import date as date_

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.analysis_engine.business_data.versioning import latest_versions
from atlas.analysis_engine.valuation.facts import PriceBasis, market_price_provenance
from atlas.business_data_providers.alpha_vantage import AlphaVantageMarketDataProvider
from atlas.business_data_providers.sec_edgar import SecEdgarFundamentalsProvider
from tests.unit.business_data_providers.test_market_data_provenance import (
    _BAR_2012_10,
    _BAR_2014_05,
    _FETCHED,
    _REFETCHED,
    _av_fetcher,
    _legacy,
    _record,
)
from tests.unit.business_data_providers.test_sec_edgar import _TICKER_MAP, _companyfacts, _instant_entry, _usd_entry
from tests.unit.business_data_providers.test_sec_edgar import _fake_fetcher as _sec_fetcher


def _repository():
    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})
    create_business_record_table(engine)
    return SqlAlchemyBusinessRecordRepository(engine)


def _snapshots(series, *, when=_FETCHED):
    provider = AlphaVantageMarketDataProvider(_av_fetcher(series), sleeper=lambda s: None, api_key="k")
    return provider.fetch_historical_snapshots(
        company_identifier="AAPL", filing_dates=tuple(date_.fromisoformat(d) for d in series), evaluated_at=when
    )


def test_every_provenance_field_survives_a_database_round_trip():
    repository = _repository()
    stored = [_record(doc) for doc in _snapshots({"2012-10-31": _BAR_2012_10, "2014-05-30": _BAR_2014_05})]
    for record in stored:
        repository.add(record)
    reloaded = {r.id: r for r in repository.get_by_company("AAPL")}
    for record in stored:
        assert reloaded[record.id].metadata == record.metadata
        assert market_price_provenance(reloaded[record.id]) == market_price_provenance(record)
    p = market_price_provenance(reloaded[stored[1].id])
    assert (p.basis, p.raw_close, p.dividend_amount, p.retrieved_at) == (
        PriceBasis.SPLIT_AND_DIVIDEND_ADJUSTED, 633.0, 3.29, _FETCHED,
    )


def test_a_legacy_row_stays_readable_and_adjusted_after_reload():
    repository = _repository()
    (doc,) = _snapshots({"2012-10-31": _BAR_2012_10})
    legacy = _record(_legacy(doc))
    repository.add(legacy)
    (reloaded,) = repository.get_by_company("AAPL")
    p = market_price_provenance(reloaded)
    assert (p.basis, p.basis_recorded, p.raw_close, p.share_price) == (
        PriceBasis.SPLIT_AND_DIVIDEND_ADJUSTED, False, None, 17.881,
    )


def test_a_revision_and_its_original_both_survive_and_the_latest_wins():
    repository = _repository()
    (first_doc,) = _snapshots({"2012-10-31": {**_BAR_2012_10, "5. adjusted close": "17.8967"}})
    first = _record(first_doc)
    repository.add(first)
    (second_doc,) = _snapshots({"2012-10-31": _BAR_2012_10}, when=_REFETCHED)
    second = _record(second_doc, evaluated_at=_REFETCHED, existing=(first,))
    repository.add(second)
    rows = repository.get_by_company("AAPL")
    assert {r.version.version_number for r in rows} == {1, 2}
    (latest,) = latest_versions(rows)
    p = market_price_provenance(latest)
    assert (p.share_price, p.raw_close, p.retrieved_at) == (17.881, 595.32, _REFETCHED)


def test_share_count_filing_provenance_survives_a_database_round_trip():
    repository = _repository()
    companyfacts = _companyfacts(
        {
            "Revenues": [_usd_entry(start="2012-09-30", end="2013-09-28", val=1000.0, filed="2013-10-30")],
            "CommonStockSharesOutstanding": [
                _instant_entry(end="2013-09-28", val=899_213_000.0, filed="2013-10-30", accn="0001193125-13-416534"),
                _instant_entry(end="2013-09-28", val=6_294_494_000.0, filed="2014-10-27", accn="0001193125-14-383437"),
            ],
        },
        units={"CommonStockSharesOutstanding": "shares"},
    )
    fetcher = _sec_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
    (doc,) = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_FETCHED)
    record = _record(doc)
    repository.add(record)
    (reloaded,) = repository.get_by_company("AAPL")
    keys = [k for k in record.metadata if k.startswith("shares_outstanding")]
    assert len(keys) == 6  # the count and its five provenance keys
    assert {k: reloaded.metadata[k] for k in keys} == {k: record.metadata[k] for k in keys}
