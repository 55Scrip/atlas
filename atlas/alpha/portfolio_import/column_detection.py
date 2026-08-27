"""Header-vocabulary column-role detection -- Swedish and English, the
real broker-export column names (Namn/Antal/Kurs/Värde/Andel %,
Name/Quantity/Price/Value/Weight) plus Ticker/Symbol and
Currency/Valuta. Generalizes the frontend's old 2-column-only header
allowlist (`parser.ts`'s `HEADER_FIRST_COLUMN_LABELS`/
`HEADER_SECOND_COLUMN_LABELS`) to the full column set a real export
carries.
"""
from __future__ import annotations

from atlas.alpha.portfolio_import.models import ColumnRole

_HEADER_VOCABULARY: dict[str, ColumnRole] = {
    # company name
    "name": ColumnRole.COMPANY_NAME,
    "namn": ColumnRole.COMPANY_NAME,
    "company": ColumnRole.COMPANY_NAME,
    "bolag": ColumnRole.COMPANY_NAME,
    "instrument": ColumnRole.COMPANY_NAME,
    "security": ColumnRole.COMPANY_NAME,
    # ticker
    "ticker": ColumnRole.TICKER,
    "symbol": ColumnRole.TICKER,
    # quantity
    "quantity": ColumnRole.QUANTITY,
    "antal": ColumnRole.QUANTITY,
    "shares": ColumnRole.QUANTITY,
    "units": ColumnRole.QUANTITY,
    # price
    "price": ColumnRole.PRICE,
    "kurs": ColumnRole.PRICE,
    "pris": ColumnRole.PRICE,
    # value
    "value": ColumnRole.VALUE,
    "värde": ColumnRole.VALUE,
    "varde": ColumnRole.VALUE,
    "market value": ColumnRole.VALUE,
    "marketvalue": ColumnRole.VALUE,
    # weight
    "weight": ColumnRole.WEIGHT,
    "weight %": ColumnRole.WEIGHT,
    "weightpercent": ColumnRole.WEIGHT,
    "allocation": ColumnRole.WEIGHT,
    "allocation %": ColumnRole.WEIGHT,
    "andel": ColumnRole.WEIGHT,
    "andel %": ColumnRole.WEIGHT,
    # currency
    "currency": ColumnRole.CURRENCY,
    "valuta": ColumnRole.CURRENCY,
}


def detect_header(columns: list[str]) -> list[ColumnRole | None] | None:
    """Returns the per-column role mapping if `columns` looks like a
    real header row (at least a company name or ticker column, plus one
    other recognized label), else `None` -- meaning the caller should
    fall back to the legacy 2-column headerless convention (name,
    weight)."""
    roles = [_HEADER_VOCABULARY.get(column.strip().lower()) for column in columns]
    recognized = [role for role in roles if role is not None]
    if len(recognized) < 2:
        return None
    if ColumnRole.COMPANY_NAME not in recognized and ColumnRole.TICKER not in recognized:
        return None
    return roles
