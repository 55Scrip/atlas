"""End-to-end tests for `PortfolioImportPreviewService` -- exercises
parse -> resolve -> derive -> detect-duplicates as one pipeline, the
same shape every entry door (paste, CSV, broker-guided paste, manual)
goes through.
"""
from __future__ import annotations

from atlas.alpha.portfolio_import.models import RowResolutionStatus
from atlas.alpha.portfolio_import.service import PortfolioImportPreviewService

_service = PortfolioImportPreviewService()


class TestRealBrokerExport:
    def test_a_real_avanza_style_export_resolves_and_derives_cleanly(self):
        raw = (
            "Namn;Antal;Kurs;Värde;Andel %\n"
            "Volvo B;100;220,50;22050;55,1%\n"
            "Investor B;200;90,00;18000;44,9%"
        )
        preview = _service.preview(raw)
        assert preview.header_detected is True
        assert preview.holdings_found == 2
        assert preview.resolved_count == 2
        assert preview.needs_review is False

        by_line = {row.line_number: row for row in preview.rows}
        volvo = by_line[2]
        assert volvo.ticker == "VOLV-B"
        assert volvo.quantity == 100
        assert volvo.price == 220.50
        assert volvo.value_absolute == 22050
        assert volvo.status == RowResolutionStatus.RESOLVED

    def test_quantity_and_price_alone_derive_a_value(self):
        raw = "Company,Ticker,Quantity,Price\nMicrosoft,MSFT,10,400.00"
        preview = _service.preview(raw)
        row = preview.rows[0]
        assert row.value_absolute == 4000.00
        assert row.status == RowResolutionStatus.RESOLVED


class TestCompanyNameResolution:
    def test_exact_registry_match_resolves_without_a_ticker_column(self):
        raw = "Name;Weight\nMicrosoft;60\nApple;40"
        preview = _service.preview(raw)
        tickers = {row.ticker for row in preview.rows}
        assert tickers == {"MSFT", "AAPL"}
        assert preview.needs_review is False

    def test_unmapped_company_name_is_unresolved_not_guessed(self):
        raw = "Name;Weight\nSchneider Electric;100"
        preview = _service.preview(raw)
        row = preview.rows[0]
        assert row.status == RowResolutionStatus.UNRESOLVED
        assert row.ticker is None
        assert preview.needs_review is True

    def test_multi_class_company_without_a_class_is_unresolved(self):
        # Deliberately absent from the registry as a bare name -- see
        # instrument_registry.py's own docstring.
        raw = "Name;Weight\nAlphabet;100"
        preview = _service.preview(raw)
        assert preview.rows[0].status == RowResolutionStatus.UNRESOLVED

    def test_unsupported_instrument_type_is_unresolved_with_a_reason(self):
        raw = "Name;Weight\nSpaceX;100"
        preview = _service.preview(raw)
        row = preview.rows[0]
        assert row.status == RowResolutionStatus.UNRESOLVED
        assert "private" in row.message

    def test_explicit_uppercase_ticker_shaped_name_resolves(self):
        raw = "Name;Weight\nAMD;100"
        preview = _service.preview(raw)
        assert preview.rows[0].ticker == "AMD"
        assert preview.rows[0].status == RowResolutionStatus.RESOLVED

    def test_ticker_column_takes_priority_over_company_name_lookup(self):
        raw = "Company,Ticker,Weight\nSome Unlisted Alias,QCOM,100"
        preview = _service.preview(raw)
        assert preview.rows[0].ticker == "QCOM"


class TestDuplicateDetection:
    def test_repeated_ticker_within_batch_is_flagged(self):
        raw = "Ticker;Weight\nAMD;50\nAMD;50"
        preview = _service.preview(raw)
        statuses = [row.status for row in preview.rows]
        assert statuses == [RowResolutionStatus.RESOLVED, RowResolutionStatus.DUPLICATE]
        assert preview.needs_review is True

    def test_ticker_already_in_existing_portfolio_is_flagged_but_not_blocking(self):
        raw = "Ticker;Weight\nAMD;100"
        preview = _service.preview(raw, existing_tickers=frozenset({"AMD"}))
        row = preview.rows[0]
        assert row.already_held is True
        assert row.status == RowResolutionStatus.RESOLVED
        assert preview.needs_review is False


class TestCurrencyConflict:
    def test_mixed_currencies_across_resolved_rows_forces_review(self):
        raw = "Ticker,Value,Currency\nMSFT,4000,USD\nVOLV-B,22050,SEK"
        preview = _service.preview(raw)
        assert preview.currency_conflict is True
        assert preview.needs_review is True

    def test_a_single_shared_currency_does_not_force_review(self):
        raw = "Ticker,Value,Currency\nMSFT,4000,USD\nAAPL,3000,usd"
        preview = _service.preview(raw)
        assert preview.currency_conflict is False


class TestErrorRows:
    def test_a_row_with_no_sizing_information_is_an_error(self):
        preview = _service.preview("AMD")
        assert preview.rows[0].status == RowResolutionStatus.ERROR
        assert preview.needs_review is True

    def test_an_unreadable_numeric_field_is_an_error(self):
        raw = "Ticker;Weight\nAMD;not-a-number"
        preview = _service.preview(raw)
        assert preview.rows[0].status == RowResolutionStatus.ERROR
