"""Tests for `atlas.alpha.investment_case.financial_history
.extract_financial_history`/`extract_market_snapshot` (Investment Case
Engine v1 slice; extended Company Data Foundation v1). No dedicated
test file existed for this module before this sprint."""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.investment_case.financial_history import extract_financial_history, extract_market_snapshot
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

_NOW = datetime(2026, 8, 9, tzinfo=timezone.utc)


def _statement_document(
    *, ticker: str = "AAPL", period_end: date, period_start: date | None = None, **metadata
) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=f"{ticker}:FY:{period_end.isoformat()}",
        company=ticker,
        source_kind="financial_statement",
        published_at=_NOW,
        provider_id="sec_edgar",
        raw_reference="https://example.test/10k",
        content_hash=f"hash-{period_end.isoformat()}",
        language="en",
        period_start=period_start,
        period_end=period_end,
        metadata=metadata,
    )


def _snapshot_document(*, ticker: str = "AAPL", published_at: datetime = _NOW, **metadata) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=f"{ticker}:snapshot:{published_at.date().isoformat()}",
        company=ticker,
        source_kind="market_data_snapshot",
        published_at=published_at,
        provider_id="alpha_vantage",
        raw_reference="https://example.test/quote",
        content_hash=f"hash-{published_at.isoformat()}",
        language="en",
        period_start=published_at.date(),
        period_end=published_at.date(),
        metadata=metadata,
    )


def _ingest(document: RawBusinessDocument):
    result = ingest(document, evaluated_at=_NOW)
    assert isinstance(result, IngestedRecord)
    return result.record


class TestFinancialHistoryFieldCoverage:
    """Company Data Foundation v1: every new field flows through, and
    every field the source record did not report stays honestly None."""

    def test_all_fields_pass_through_when_present(self):
        record = _ingest(
            _statement_document(
                period_start=date(2024, 1, 1),
                period_end=date(2024, 12, 31),
                revenue=1000.0,
                operating_income=250.0,
                net_income=200.0,
                eps=2.5,
                free_cash_flow=300.0,
                capital_expenditure=50.0,
                share_buybacks=20.0,
                share_issuance=5.0,
                dividends=15.0,
                cash=900.0,
                total_debt=550.0,
                shares_outstanding=1_000_000.0,
                currency="USD",
            )
        )
        (period,) = extract_financial_history((record,))
        assert period.period_end == date(2024, 12, 31)
        assert period.revenue == 1000.0
        assert period.operating_income == 250.0
        assert period.net_income == 200.0
        assert period.eps == 2.5
        assert period.free_cash_flow == 300.0
        assert period.capital_expenditure == 50.0
        assert period.share_buybacks == 20.0
        assert period.share_issuance == 5.0
        assert period.dividends == 15.0
        assert period.cash == 900.0
        assert period.total_debt == 550.0
        assert period.shares_outstanding == 1_000_000.0
        assert period.currency == "USD"

    def test_fields_not_reported_stay_none_never_zero(self):
        record = _ingest(_statement_document(period_end=date(2024, 12, 31), revenue=1000.0))
        (period,) = extract_financial_history((record,))
        assert period.revenue == 1000.0
        for field_name in (
            "operating_income",
            "net_income",
            "eps",
            "cash",
            "total_debt",
            "shares_outstanding",
        ):
            assert getattr(period, field_name) is None

    def test_multiple_periods_ordered_oldest_first(self):
        r2024 = _ingest(_statement_document(period_end=date(2024, 12, 31), revenue=1000.0))
        r2022 = _ingest(_statement_document(period_end=date(2022, 12, 31), revenue=800.0))
        r2023 = _ingest(_statement_document(period_end=date(2023, 12, 31), revenue=900.0))
        periods = extract_financial_history((r2024, r2022, r2023))
        assert [p.period_end for p in periods] == [date(2022, 12, 31), date(2023, 12, 31), date(2024, 12, 31)]


class TestMarketSnapshotAndMarketCap:
    def test_market_cap_is_derived_when_both_inputs_are_known(self):
        record = _ingest(_snapshot_document(share_price=500.0, shares_outstanding=7_000_000.0, currency="USD"))
        snapshot = extract_market_snapshot((record,))
        assert snapshot is not None
        assert snapshot.share_price == 500.0
        assert snapshot.shares_outstanding == 7_000_000.0
        assert snapshot.market_cap == 3_500_000_000.0

    def test_market_cap_is_none_when_shares_outstanding_is_missing(self):
        record = _ingest(_snapshot_document(share_price=500.0))
        snapshot = extract_market_snapshot((record,))
        assert snapshot.share_price == 500.0
        assert snapshot.shares_outstanding is None
        assert snapshot.market_cap is None

    def test_market_cap_is_none_when_share_price_is_missing(self):
        record = _ingest(_snapshot_document(shares_outstanding=7_000_000.0))
        snapshot = extract_market_snapshot((record,))
        assert snapshot.market_cap is None

    def test_market_cap_is_never_persisted_only_recomputed(self):
        """A `"market_cap"` key on the raw metadata is never read --
        the value is always derived fresh from `share_price` ×
        `shares_outstanding`, matching this sprint's own "do not
        persist a derived metric" instruction."""
        record = _ingest(
            _snapshot_document(share_price=500.0, shares_outstanding=7_000_000.0, market_cap=999.0)
        )
        snapshot = extract_market_snapshot((record,))
        assert snapshot.market_cap == 3_500_000_000.0  # derived, not the fabricated 999.0

    def test_no_snapshot_record_returns_none(self):
        assert extract_market_snapshot(()) is None

    def test_most_recently_published_snapshot_wins(self):
        older = _ingest(_snapshot_document(published_at=_NOW, share_price=400.0))
        newer_time = datetime(2026, 8, 10, tzinfo=timezone.utc)
        newer = _ingest(_snapshot_document(published_at=newer_time, share_price=500.0))
        snapshot = extract_market_snapshot((older, newer))
        assert snapshot.share_price == 500.0
        assert snapshot.as_of == newer_time


class TestDeterminism:
    def test_identical_records_produce_a_deeply_equal_result(self):
        record = _ingest(_statement_document(period_end=date(2024, 12, 31), revenue=1000.0))
        assert extract_financial_history((record,)) == extract_financial_history((record,))
