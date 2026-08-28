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
        assert parse_numeric("654.50 DKK") == 654.50
        assert parse_numeric("654.50 NOK") == 654.50
        assert parse_numeric("654.50 GBP") == 654.50
        assert parse_numeric("£654.50") == 654.50

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


class TestRealBrokerFlattenedCopy:
    """Real Avanza Import Fix: a real broker holdings page is not a
    semantic <table> -- copying it produces one line per DOM fragment
    (name, % change, action buttons, value), not one line per holding.
    Fixtures below are a sanitized, structurally-identical reconstruction
    of that shape (fictional company names, not the reporter's real
    portfolio), built from the confirmed symptom: ~3x row-count
    inflation and values never associated with names.
    """

    def test_name_and_value_on_separate_lines_are_correctly_paired(self):
        raw = (
            "Nordic Holding B\n"
            "+1,2%\n"
            "Köp\n"
            "Sälj\n"
            "233 324 kr\n"
            "Example Group AB\n"
            "-0,5%\n"
            "Köp\n"
            "Sälj\n"
            "49 010 kr\n"
        )
        result = parse_input(raw)
        assert result.header_detected is False
        # Not 10 rows (one per line) -- exactly 2, one per real holding.
        assert len(result.rows) == 2
        assert result.rows[0].fields[ColumnRole.COMPANY_NAME] == "Nordic Holding B"
        assert result.rows[0].fields[ColumnRole.VALUE] == "233 324 kr"
        assert result.rows[0].fields[ColumnRole.CURRENCY] == "SEK"
        assert result.rows[1].fields[ColumnRole.COMPANY_NAME] == "Example Group AB"
        assert result.rows[1].fields[ColumnRole.VALUE] == "49 010 kr"

    def test_ui_control_and_header_noise_never_become_holdings(self):
        raw = "Innehav\nAndel %\nKurs\nExample Corp\nKöp\nSälj\n100 000 kr\nTotalt\nSumma\n"
        result = parse_input(raw)
        assert len(result.rows) == 1
        assert result.rows[0].fields[ColumnRole.COMPANY_NAME] == "Example Corp"

    def test_standalone_percent_change_is_never_treated_as_weight_or_value(self):
        raw = "Example Corp\n+3,4%\n100 000 kr\n"
        result = parse_input(raw)
        assert len(result.rows) == 1
        assert result.rows[0].fields.get(ColumnRole.WEIGHT) is None
        assert result.rows[0].fields[ColumnRole.VALUE] == "100 000 kr"

    def test_a_name_with_no_value_anywhere_becomes_its_own_row_with_no_value(self):
        raw = "Example Corp\nAnother Corp\n50 000 kr\n"
        result = parse_input(raw)
        assert len(result.rows) == 2
        assert result.rows[0].fields == {ColumnRole.COMPANY_NAME: "Example Corp"}
        assert result.rows[1].fields[ColumnRole.COMPANY_NAME] == "Another Corp"
        assert result.rows[1].fields[ColumnRole.VALUE] == "50 000 kr"

    def test_an_orphan_value_with_no_pending_name_is_dropped_not_misattributed(self):
        raw = "50 000 kr\nExample Corp\n100 000 kr\n"
        result = parse_input(raw)
        assert len(result.rows) == 1
        assert result.rows[0].fields[ColumnRole.COMPANY_NAME] == "Example Corp"
        assert result.rows[0].fields[ColumnRole.VALUE] == "100 000 kr"

    def test_a_name_containing_a_digit_is_still_split_correctly_from_its_value(self):
        raw = "3M Company\n45 937 kr\n"
        result = parse_input(raw)
        assert result.rows[0].fields[ColumnRole.COMPANY_NAME] == "3M Company"
        assert result.rows[0].fields[ColumnRole.VALUE] == "45 937 kr"

    def test_name_and_value_on_the_same_line_with_embedded_thousands_space(self):
        raw = "Nordic Holding B 233 324 kr\nExample Group AB 49 010 kr\n"
        result = parse_input(raw)
        assert len(result.rows) == 2
        assert result.rows[0].fields[ColumnRole.COMPANY_NAME] == "Nordic Holding B"
        assert result.rows[0].fields[ColumnRole.VALUE] == "233 324 kr"

    def test_flag_emoji_and_pure_symbol_lines_are_ignored(self):
        raw = "Example Corp\n🇸🇪\n→\n100 000 kr\n"
        result = parse_input(raw)
        assert len(result.rows) == 1
        assert result.rows[0].fields[ColumnRole.VALUE] == "100 000 kr"

    def test_an_ungrouped_four_digit_value_is_not_truncated(self):
        # Regression: a leading-digit cap of 3 would misparse "1234 kr"
        # as splitting after the third digit.
        raw = "Example Corp\n1234 kr\n"
        result = parse_input(raw)
        assert result.rows[0].fields[ColumnRole.VALUE] == "1234 kr"
