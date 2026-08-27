"""Tests for `atlas.alpha.portfolio_import.row_parser`."""
from __future__ import annotations

from atlas.alpha.portfolio_import.models import ColumnRole
from atlas.alpha.portfolio_import.row_parser import normalize_numeric_text, parse_input, parse_numeric


class TestNormalizeNumericText:
    def test_strips_percent_sign(self):
        assert parse_numeric("6,14%") == 6.14

    def test_swedish_thousands_separator_is_a_space(self):
        assert parse_numeric("12 345,67") == 12345.67

    def test_us_style_thousands_and_decimal(self):
        assert parse_numeric("1,234.50") == 1234.50

    def test_swedish_decimal_comma_only(self):
        assert parse_numeric("654,50") == 654.50

    def test_strips_currency_code(self):
        assert parse_numeric("654,50 kr") == 654.50
        assert parse_numeric("654.50 SEK") == 654.50

    def test_rejects_non_numeric_text(self):
        assert parse_numeric("N/A") is None

    def test_rejects_blank(self):
        assert normalize_numeric_text("   ") is None

    def test_negative_value(self):
        assert parse_numeric("-6.14") == -6.14


class TestParseInputHeaderDetection:
    def test_avanza_style_semicolon_export_is_detected(self):
        raw = "Namn;Antal;Kurs;Värde;Andel %\nVolvo B;100;220,50;22050;12,3%"
        result = parse_input(raw)
        assert result.header_detected is True
        assert len(result.rows) == 1
        fields = result.rows[0].fields
        assert fields[ColumnRole.COMPANY_NAME] == "Volvo B"
        assert fields[ColumnRole.QUANTITY] == "100"
        assert fields[ColumnRole.PRICE] == "220,50"
        assert fields[ColumnRole.VALUE] == "22050"
        assert fields[ColumnRole.WEIGHT] == "12,3%"

    def test_english_csv_style_export_is_detected(self):
        raw = "Company,Ticker,Quantity,Price,Value\nMicrosoft,MSFT,10,400.00,4000.00"
        result = parse_input(raw)
        assert result.header_detected is True
        fields = result.rows[0].fields
        assert fields[ColumnRole.TICKER] == "MSFT"
        assert fields[ColumnRole.QUANTITY] == "10"

    def test_legacy_headerless_two_column_paste_still_works(self):
        raw = "Microsoft – 6,14%\nNVDA – 40"
        result = parse_input(raw)
        assert result.header_detected is False
        assert len(result.rows) == 2
        assert result.rows[0].fields[ColumnRole.COMPANY_NAME] == "Microsoft"
        assert result.rows[0].fields[ColumnRole.WEIGHT] == "6,14%"
        assert result.rows[1].fields[ColumnRole.COMPANY_NAME] == "NVDA"
        assert result.rows[1].fields[ColumnRole.WEIGHT] == "40"

    def test_tab_delimited_paste_also_works(self):
        raw = "Microsoft\t6,14\nNVDA\t40"
        result = parse_input(raw)
        assert result.header_detected is False
        assert result.rows[0].fields[ColumnRole.COMPANY_NAME] == "Microsoft"
        assert result.rows[0].fields[ColumnRole.WEIGHT] == "6,14"

    def test_blank_lines_are_ignored(self):
        raw = "Ticker;Weight\nAMD;50\n\n\nNVDA;50"
        result = parse_input(raw)
        assert len(result.rows) == 2

    def test_empty_input_yields_no_rows(self):
        result = parse_input("")
        assert result.rows == ()
        assert result.header_detected is False
