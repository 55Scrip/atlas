"""Identity captured at import: ISIN, venue and name.

The previous sprint established why this matters. The import stored a bare
ticker and nothing else, so eleven of twenty-six followed holdings -- about
42% of portfolio weight -- could not be resolved to any security at all.
A ticker is venue-local: `SU` is Suncor Energy on the NYSE, `SU.PA` is
Schneider Electric in Paris, and `VOLV-B` means nothing outside Stockholm.
An ISIN is not.

These tests cover the capture, and the refusals that keep a stronger
identifier from being overridden by a weaker one.
"""
from __future__ import annotations

import pytest

from atlas.alpha.portfolio_import.column_detection import detect_header
from atlas.alpha.portfolio_import.isin import is_valid_isin, normalize_isin
from atlas.alpha.portfolio_import.models import ColumnRole


# --- ISIN validity -----------------------------------------------------


@pytest.mark.parametrize(
    "isin,label",
    [
        ("SE0000115446", "Volvo B"),
        ("FR0000121972", "Schneider Electric"),
        ("CA8672241079", "Suncor Energy"),
        ("US8740391003", "TSMC ADR"),
        ("DK0062498333", "Novo Nordisk B"),
        ("US0378331005", "Apple"),
        ("XS1982113463", "a Eurobond -- XS is a real prefix, not a country"),
    ],
)
def test_real_isins_validate(isin: str, label: str) -> None:
    assert is_valid_isin(isin), label


@pytest.mark.parametrize("isin", ["SE0000115445", "FR0000121973", "US0378331004"])
def test_a_wrong_check_digit_is_refused(isin: str) -> None:
    """The reason the check digit is verified at all: a mistyped ISIN that
    still looks like one must never be allowed to resolve a security."""
    assert not is_valid_isin(isin)


@pytest.mark.parametrize("isin", ["", "   ", None, "US037833100", "US03783310055", "0S0378331005"])
def test_malformed_input_is_not_evidence(isin) -> None:
    assert not is_valid_isin(isin)


def test_normalisation_touches_only_whitespace_and_case() -> None:
    assert normalize_isin("  se0000115446 ") == "SE0000115446"
    assert normalize_isin("SE 0000 115446") == "SE0000115446"


def test_an_empty_isin_is_absence_not_an_empty_string() -> None:
    """`""` must never reach resolution as though it were an identifier."""
    assert normalize_isin("") is None
    assert normalize_isin("   ") is None
    assert normalize_isin(None) is None


def test_two_share_classes_of_one_issuer_have_different_isins() -> None:
    """ISIN identifies a security, not an issuer -- which is exactly why it
    can separate Volvo A from Volvo B where a ticker suffix cannot."""
    assert is_valid_isin("SE0000115446")  # Volvo B
    assert is_valid_isin("SE0000115420")  # Volvo A
    assert "SE0000115446" != "SE0000115420"


# --- Column capture ----------------------------------------------------


def test_isin_and_market_are_recognised_columns() -> None:
    roles = detect_header(["Namn", "ISIN", "Marknad", "Antal", "Valuta"])
    assert roles is not None
    assert roles[1] is ColumnRole.ISIN
    assert roles[2] is ColumnRole.MARKET


@pytest.mark.parametrize("header", ["ISIN", "isin", "ISIN-kod", "ISIN code"])
def test_isin_headers_in_both_languages(header: str) -> None:
    roles = detect_header(["Name", header, "Quantity"])
    assert roles is not None and ColumnRole.ISIN in roles


@pytest.mark.parametrize("header", ["Market", "Marknad", "Marketplace", "Exchange", "Börs", "Handelsplats"])
def test_venue_headers_in_both_languages(header: str) -> None:
    roles = detect_header(["Name", header, "Quantity"])
    assert roles is not None and ColumnRole.MARKET in roles


def test_an_export_without_identity_columns_still_parses() -> None:
    """Legacy imports carried name and weight only. They must keep working;
    they simply resolve on weaker evidence."""
    roles = detect_header(["Namn", "Andel %"])
    assert roles is not None
    assert roles[0] is ColumnRole.COMPANY_NAME


def test_unknown_broker_columns_are_ignored_not_forced() -> None:
    roles = detect_header(["Namn", "Förändring idag", "Antal"])
    assert roles is not None
    assert roles[1] is None


# --- Identity is not describable by the account ------------------------


def test_currency_and_isin_are_different_roles() -> None:
    """The live import recorded SEK for all 25 holdings because that is the
    account's reporting currency -- it says nothing about where a security
    trades, and must never be read as venue or identity evidence."""
    assert ColumnRole.CURRENCY is not ColumnRole.ISIN
    assert ColumnRole.CURRENCY is not ColumnRole.MARKET
    roles = detect_header(["Namn", "Valuta", "Marknad", "Antal"])
    assert roles is not None
    assert roles[1] is ColumnRole.CURRENCY
    assert roles[2] is ColumnRole.MARKET


def test_the_isin_module_derives_no_identity_of_its_own() -> None:
    """It validates and normalises. It must never map an ISIN to a company,
    a venue or a ticker -- that is resolution's job, against stored facts."""
    import inspect

    from atlas.alpha.portfolio_import import isin as module

    source = inspect.getsource(module)
    for forbidden in ("requests", "httpx", "ticker_for", "lookup", "COUNTRY_TO_", "MIC"):
        assert forbidden not in source


# --- End to end, on a realistic export ---------------------------------


_SWEDISH_EXPORT = """Namn;ISIN;Marknad;Antal;Kurs;Värde;Valuta
Volvo B;SE0000115446;Nasdaq Stockholm;120;285,40;34248,00;SEK
Schneider Electric;FR0000121972;Euronext Paris;15;238,10;3571,50;SEK
Novo Nordisk B;DK0062498333;Nasdaq Copenhagen;40;412,00;16480,00;SEK
Taiwan Semiconductor;US8740391003;NYSE;25;182,30;4557,50;SEK"""


def _parsed():
    from atlas.alpha.portfolio_import.row_parser import parse_input

    return parse_input(_SWEDISH_EXPORT)


def test_a_real_export_yields_an_isin_for_every_holding() -> None:
    rows = _parsed().rows
    assert len(rows) == 4
    assert all(is_valid_isin(row.fields.get(ColumnRole.ISIN)) for row in rows)


def test_venue_is_captured_and_is_not_the_account_currency() -> None:
    """The live import recorded SEK for all 25 holdings because that is the
    account's reporting currency. A Paris listing held in a Swedish account
    is still a Paris listing, and only the venue column says so."""
    rows = {row.fields[ColumnRole.COMPANY_NAME]: row.fields for row in _parsed().rows}
    schneider = rows["Schneider Electric"]
    assert schneider[ColumnRole.MARKET] == "Euronext Paris"
    assert schneider[ColumnRole.CURRENCY] == "SEK"
    assert schneider[ColumnRole.MARKET] != schneider[ColumnRole.CURRENCY]


def test_the_row_that_caused_the_wrong_company_risk_now_carries_its_own_proof() -> None:
    """`SU.PA` was resolvable only through a curated name table, and bare
    `SU` is Suncor Energy. With an ISIN the ambiguity cannot arise: Suncor
    is CA8672241079 and Schneider is FR0000121972."""
    rows = {row.fields[ColumnRole.COMPANY_NAME]: row.fields for row in _parsed().rows}
    assert rows["Schneider Electric"][ColumnRole.ISIN] == "FR0000121972"
    assert is_valid_isin("CA8672241079")
    assert rows["Schneider Electric"][ColumnRole.ISIN] != "CA8672241079"


def test_share_class_survives_the_import() -> None:
    names = {row.fields[ColumnRole.COMPANY_NAME] for row in _parsed().rows}
    assert "Volvo B" in names
    assert "Novo Nordisk B" in names
