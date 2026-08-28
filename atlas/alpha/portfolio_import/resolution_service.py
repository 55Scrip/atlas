"""Company/ticker resolution -- the full five-step priority: exact
ticker, exact company name, registry alias lookup, the `security_
discovery` fallback, and a one-question clarification for genuine
ambiguity. A row nothing here can resolve becomes `UNRESOLVED`, never a
guess.
"""
from __future__ import annotations

import re
from collections.abc import Callable

from atlas.alpha.portfolio_import.instrument_registry import lookup_instrument
from atlas.alpha.portfolio_import.models import (
    ColumnRole,
    ParsedHoldingRow,
    ResolutionCandidate,
    RowResolutionStatus,
)
from atlas.alpha.portfolio_import.row_parser import RawRow, parse_numeric
from atlas.alpha.security_discovery.models import SecurityCandidate

_TICKER_SHAPE_PATTERN = re.compile(r"^[A-Za-z]{1,5}([.-][A-Za-z]{1,2})?$")

DiscoverFn = Callable[[str], "tuple[SecurityCandidate, ...]"]


def _looks_like_explicit_ticker(trimmed: str) -> bool:
    """Shape AND already-uppercase, ported from `resolution.ts`'s
    identical function -- see that file for why shape alone is not
    enough ("Volvo" would otherwise become the fabricated "VOLVO")."""
    return bool(_TICKER_SHAPE_PATTERN.match(trimmed)) and trimmed == trimmed.upper()


def resolve_row(row: RawRow, *, discover: DiscoverFn | None = None) -> ParsedHoldingRow:
    company_name = row.fields.get(ColumnRole.COMPANY_NAME)
    ticker_field = row.fields.get(ColumnRole.TICKER)

    if not company_name and not ticker_field:
        return ParsedHoldingRow(
            line_number=row.line_number,
            raw=row.raw,
            status=RowResolutionStatus.ERROR,
            message="No company name or ticker found on this line.",
        )

    ticker: str | None = None
    message: str | None = None
    candidates: tuple[ResolutionCandidate, ...] = ()
    unsupported_instrument_type: str | None = None

    if ticker_field:
        # Priority 1: the source already told us the ticker directly.
        ticker = ticker_field.strip().upper()
    elif company_name:
        registry_hit = lookup_instrument(company_name)
        if registry_hit is not None:
            if registry_hit.ticker is not None:
                # Priority 2/3: exact registry name or alias match.
                ticker = registry_hit.ticker
            else:
                # A genuinely *known* identity Atlas can't hold as
                # ticker+weight (a fund, an ETP, or an unlisted/private
                # company) -- not "unknown," never offered a manual-
                # ticker override (Real Avanza Import Fix, Phase 6).
                unsupported_instrument_type = registry_hit.instrument_type
        else:
            # Priority 4: security_discovery's own exact ticker-symbol
            # or canonical-title match -- SEC-filer coverage only, so a
            # Nordic name/ticker this misses still falls through to the
            # shape heuristic below rather than staying unresolved.
            discovered = discover(company_name) if discover is not None else ()
            if len(discovered) == 1:
                ticker = discovered[0].ticker
            elif len(discovered) > 1:
                # Priority 5: genuine ambiguity -- one clarification
                # question, never a guess (e.g. Berkshire's A/B classes).
                candidates = tuple(
                    ResolutionCandidate(ticker=c.ticker, display_name=c.display_name)
                    for c in discovered
                )
            elif _looks_like_explicit_ticker(company_name.strip()):
                ticker = company_name.strip().upper()

    def _parse_field(role: ColumnRole) -> tuple[float | None, bool]:
        """Returns (value, had_invalid_text) -- `had_invalid_text` is
        True only when the field was present but didn't parse, so a
        genuinely absent field never becomes a spurious error."""
        raw_value = row.fields.get(role)
        if raw_value is None:
            return None, False
        parsed = parse_numeric(raw_value)
        return parsed, parsed is None

    quantity, quantity_invalid = _parse_field(ColumnRole.QUANTITY)
    price, price_invalid = _parse_field(ColumnRole.PRICE)
    value, value_invalid = _parse_field(ColumnRole.VALUE)
    weight, weight_invalid = _parse_field(ColumnRole.WEIGHT)

    if quantity_invalid or price_invalid or value_invalid or weight_invalid:
        return ParsedHoldingRow(
            line_number=row.line_number,
            raw=row.raw,
            original_name=company_name,
            status=RowResolutionStatus.ERROR,
            message="One or more numeric fields on this line could not be read.",
        )

    value_absolute = value
    if value_absolute is None and quantity is not None and price is not None:
        value_absolute = quantity * price

    currency = row.fields.get(ColumnRole.CURRENCY)
    if currency is not None:
        currency = currency.strip().upper() or None

    if unsupported_instrument_type is not None:
        return ParsedHoldingRow(
            line_number=row.line_number,
            raw=row.raw,
            original_name=company_name,
            quantity=quantity,
            price=price,
            value_absolute=value_absolute,
            weight_percent=weight,
            currency=currency,
            status=RowResolutionStatus.UNSUPPORTED,
            message=(
                f"{company_name!r} is a recognized {unsupported_instrument_type}, "
                "not a supported equity holding."
            ),
            instrument_type=unsupported_instrument_type,
        )

    if candidates:
        return ParsedHoldingRow(
            line_number=row.line_number,
            raw=row.raw,
            original_name=company_name,
            quantity=quantity,
            price=price,
            value_absolute=value_absolute,
            weight_percent=weight,
            currency=currency,
            status=RowResolutionStatus.AMBIGUOUS,
            message=f"Atlas found more than one match for {company_name!r}.",
            candidates=candidates,
        )

    if ticker is None:
        return ParsedHoldingRow(
            line_number=row.line_number,
            raw=row.raw,
            original_name=company_name,
            quantity=quantity,
            price=price,
            value_absolute=value_absolute,
            weight_percent=weight,
            currency=currency,
            status=RowResolutionStatus.UNRESOLVED,
            message=message or f"Atlas couldn't identify {company_name!r}.",
        )

    if value_absolute is None and weight is None:
        return ParsedHoldingRow(
            line_number=row.line_number,
            raw=row.raw,
            original_name=company_name,
            ticker=ticker,
            currency=currency,
            status=RowResolutionStatus.ERROR,
            message=(
                "Not enough information to size this holding -- provide a value, "
                "quantity and price, or a weight percentage."
            ),
        )

    return ParsedHoldingRow(
        line_number=row.line_number,
        raw=row.raw,
        original_name=company_name,
        ticker=ticker,
        quantity=quantity,
        price=price,
        value_absolute=value_absolute,
        weight_percent=weight,
        currency=currency,
        status=RowResolutionStatus.RESOLVED,
    )
