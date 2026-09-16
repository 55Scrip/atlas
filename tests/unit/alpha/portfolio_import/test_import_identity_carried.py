"""The identity a broker file carries has to survive the import.

Capture already worked: `ISIN` and `Marknad` were recognised columns and
landed in the parsed row's fields. What did not survive was the step after
-- resolution read the company name, the ticker and the currency out of
those fields and dropped the other two on the floor, so the strongest
identifier in the file existed for the length of one function call.

A row could therefore be reported `RESOLVED` while Atlas knew only a ticker
string, which is what `RESOLVED` had quietly come to mean: "a ticker was
found", not "Atlas knows which security this is".
"""
from __future__ import annotations

import pytest

from atlas.alpha.portfolio_import.models import RowResolutionStatus
from atlas.alpha.portfolio_import.service import PortfolioImportPreviewService

SWEDISH_EXPORT = """Namn,Ticker,ISIN,Marknad,Valuta,Antal,Kurs
Volvo AB ser. B,VOLV-B,SE0000115446,Nasdaq Stockholm,SEK,1000,285.50
Schneider Electric,SU.PA,FR0000121972,Euronext Paris,SEK,100,220.00
"""


@pytest.fixture
def rows():
    return PortfolioImportPreviewService().preview(SWEDISH_EXPORT).rows


def test_the_isin_reaches_the_resolved_row(rows) -> None:
    assert rows[0].isin == "SE0000115446"
    assert rows[1].isin == "FR0000121972"


def test_the_market_reaches_the_resolved_row(rows) -> None:
    assert rows[0].market == "Nasdaq Stockholm"
    assert rows[1].market == "Euronext Paris"


def test_the_security_name_is_preserved(rows) -> None:
    assert rows[0].original_name == "Volvo AB ser. B"
    assert rows[1].original_name == "Schneider Electric"


def test_the_ticker_is_preserved_as_the_broker_wrote_it(rows) -> None:
    """`SU.PA` is not normalised to `SU`. Stripping the venue suffix is
    precisely how Schneider Electric would become Suncor Energy."""
    assert rows[1].ticker == "SU.PA"


def test_the_account_currency_stays_in_its_own_field(rows) -> None:
    """`SEK` is the account's reporting currency and is recorded against a
    Paris listing here. Venue and currency are separate fields because they
    are separate facts."""
    assert rows[1].currency == "SEK"
    assert rows[1].market == "Euronext Paris"


def test_a_malformed_isin_is_dropped_rather_than_carried(rows) -> None:
    """An identifier that is accepted but wrong resolves the wrong company,
    which is worse than resolving nothing -- so a failed check digit is
    absence, not a weaker value."""
    preview = PortfolioImportPreviewService().preview(
        "Namn,Ticker,ISIN,Marknad\nVolvo AB ser. B,VOLV-B,SE0000115440,Nasdaq Stockholm\n"
    )
    assert preview.rows[0].isin is None
    assert preview.rows[0].ticker == "VOLV-B"


def test_a_legacy_file_with_no_identity_columns_still_imports() -> None:
    """The shape of every import before this existed. Absent identity is
    absent, never fabricated from the name or the ticker."""
    preview = PortfolioImportPreviewService().preview(
        "Namn,Ticker,Antal,Kurs\nMicrosoft,MSFT,10,400.00\n"
    )
    row = preview.rows[0]
    assert row.status is RowResolutionStatus.RESOLVED
    assert row.ticker == "MSFT"
    assert row.isin is None
    assert row.market is None


def test_identity_survives_a_row_whose_ticker_could_not_be_resolved() -> None:
    """The case that matters most: the rows Atlas cannot name are exactly
    the ones whose ISIN it most needs to keep."""
    preview = PortfolioImportPreviewService().preview(
        "Namn,ISIN,Marknad,Antal,Kurs\nNagot Okant AB,SE0000115446,Nasdaq Stockholm,10,5.00\n"
    )
    row = preview.rows[0]
    assert row.status is not RowResolutionStatus.RESOLVED
    assert row.isin == "SE0000115446"
    assert row.market == "Nasdaq Stockholm"


# --- The wiring itself -------------------------------------------------


def _resolver(calls):
    """A real resolver over a fake provider and an empty master."""
    from atlas.alpha.canonical_security_gate.import_resolution import (
        ImportedIdentity,
        resolve_imported_identity,
    )
    from tests.unit.alpha.canonical_security_gate import figi_fixtures as fx

    class EmptyMaster:
        def find_by_identifier(self, identifier_type, value):
            return None

        def find_by_ticker_and_exchange(self, ticker, exchange_mic):
            return None

    def provider(isin):
        calls.append(isin)
        return fx.BY_ISIN.get(isin, fx.NO_MATCH)

    def resolve(*, ticker, company_name, isin, market, account_currency):
        return resolve_imported_identity(
            ImportedIdentity(ticker=ticker, company_name=company_name, isin=isin,
                             market=market, account_currency=account_currency),
            master=EmptyMaster(), map_isin_fn=provider)

    return resolve


def test_the_pipeline_actually_calls_the_resolver() -> None:
    """The step this sprint exists to add. Without it every piece below is
    correct and unreachable, which is exactly the state the previous sprint
    left things in."""
    calls: list[str] = []
    preview = PortfolioImportPreviewService().preview(
        SWEDISH_EXPORT, resolve_identity=_resolver(calls))

    volvo, schneider = preview.rows
    assert volvo.identity_status == "CONSTRUCTED"
    assert volvo.security_name == "VOLVO AB-B SHS"
    assert volvo.exchange_mic == "XSTO"
    assert volvo.strong_identifier_used == "SHARE_CLASS_FIGI"
    assert volvo.canonical_security_id is not None

    assert schneider.security_name == "SCHNEIDER ELECTRIC SE"
    assert schneider.exchange_mic == "XPAR"
    assert "SUNCOR" not in (schneider.security_name or "").upper()
    assert calls == ["SE0000115446", "FR0000121972"]


def test_a_row_without_an_identifier_never_reaches_the_provider() -> None:
    calls: list[str] = []
    preview = PortfolioImportPreviewService().preview(
        "Namn,Ticker,Antal,Kurs\nMicrosoft,MSFT,10,400.00\n",
        resolve_identity=_resolver(calls))
    assert calls == []
    assert preview.rows[0].identity_status is None
    assert preview.rows[0].ticker == "MSFT"


def test_without_a_resolver_the_pipeline_is_exactly_as_it_was() -> None:
    """The default. Identity resolution is the only step here that can
    reach a network, so it is opt-in and its absence changes nothing."""
    preview = PortfolioImportPreviewService().preview(SWEDISH_EXPORT)
    for row in preview.rows:
        assert row.identity_status is None
        assert row.canonical_security_id is None
    assert preview.rows[0].isin == "SE0000115446"
