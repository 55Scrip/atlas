"""Company/ticker resolution -- progressively weaker strategies, tried
in order, before Atlas ever asks the user (Zero-Effort Import Polish,
Sprint 11 Phase 1):

1. An explicit ticker column -- trust it directly.
2. Exact registry name/alias match, tried against the name as given
   and against ADR-suffix-stripped / legal-entity-suffix-stripped
   variants (`name_matching.name_variants`) -- "Schneider Electric SE"
   matches the registry's "schneider electric" once "SE" is stripped.
3. A previously learned resolution (`ResolvedAliasStore`) -- a name
   Atlas has ever resolved before (a genuine ambiguity the investor
   picked one of, or a manually typed ticker) is remembered, so it is
   never asked about twice.
4. A bounded, explainable abbreviation match against the registry
   (`instrument_registry.fuzzy_lookup_instrument`) -- catches real
   broker abbreviations ("Semicond" for "Semiconductor"). Lower
   confidence than an exact match, so this becomes `SUGGESTED`, a
   one-question yes/no confirmation, never a silent auto-resolve.
5. `security_discovery`'s own exact ticker-symbol or canonical-title
   match (SEC-filer coverage), tried against the same name variants.
6. The ticker-shape-and-uppercase heuristic, on the original name only.

A row nothing here can resolve becomes `UNRESOLVED`, never a guess.
"""
from __future__ import annotations

import re
from collections.abc import Callable

from atlas.alpha.portfolio_import.instrument_registry import (
    fuzzy_lookup_instrument,
    lookup_instrument,
)
from atlas.alpha.portfolio_import.models import (
    ColumnRole,
    ParsedHoldingRow,
    ResolutionCandidate,
    RowResolutionStatus,
)
from atlas.alpha.portfolio_import.name_matching import name_variants
from atlas.alpha.portfolio_import.row_parser import RawRow, parse_numeric
from atlas.alpha.security_discovery.models import SecurityCandidate

_TICKER_SHAPE_PATTERN = re.compile(r"^[A-Za-z]{1,5}([.-][A-Za-z]{1,2})?$")

DiscoverFn = Callable[[str], "tuple[SecurityCandidate, ...]"]
LookupAliasFn = Callable[[str], "str | None"]


def _looks_like_explicit_ticker(trimmed: str) -> bool:
    """Shape AND already-uppercase, ported from `resolution.ts`'s
    identical function -- see that file for why shape alone is not
    enough ("Volvo" would otherwise become the fabricated "VOLVO")."""
    return bool(_TICKER_SHAPE_PATTERN.match(trimmed)) and trimmed == trimmed.upper()


def resolve_row(
    row: RawRow,
    *,
    discover: DiscoverFn | None = None,
    lookup_alias: LookupAliasFn | None = None,
) -> ParsedHoldingRow:
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
    suggested = False

    if ticker_field:
        # Step 1: the source already told us the ticker directly.
        ticker = ticker_field.strip().upper()
    elif company_name:
        variants = name_variants(company_name)

        # Step 2: exact registry match, across every name variant.
        for variant in variants:
            registry_hit = lookup_instrument(variant)
            if registry_hit is not None:
                if registry_hit.ticker is not None:
                    ticker = registry_hit.ticker
                else:
                    # A genuinely *known* identity Atlas can't hold as
                    # ticker+weight (a fund, an ETP, or an unlisted/
                    # private company) -- not "unknown," never offered
                    # a manual-ticker override.
                    unsupported_instrument_type = registry_hit.instrument_type
                break

        # Step 3: a previously learned resolution, across every variant.
        if ticker is None and unsupported_instrument_type is None and lookup_alias is not None:
            for variant in variants:
                learned = lookup_alias(variant)
                if learned is not None:
                    ticker = learned
                    break

        # Step 4: a bounded abbreviation match against the registry --
        # lower confidence, so this always asks for confirmation.
        if ticker is None and unsupported_instrument_type is None:
            for variant in variants:
                fuzzy_hit = fuzzy_lookup_instrument(variant)
                if fuzzy_hit is not None:
                    ticker = fuzzy_hit.entry.ticker
                    suggested = True
                    candidates = (
                        ResolutionCandidate(
                            ticker=fuzzy_hit.entry.ticker,
                            # The registry's own aliases are stored lower-
                            # cased (they're matching keys, not display
                            # copy) -- title-case before this ever reaches
                            # the confirmation prompt the investor reads.
                            display_name=fuzzy_hit.matched_display_name.title(),
                        ),
                    )
                    break

        # Step 5: security_discovery, across every variant.
        if ticker is None and unsupported_instrument_type is None and not candidates:
            for variant in variants:
                discovered = discover(variant) if discover is not None else ()
                if len(discovered) == 1:
                    ticker = discovered[0].ticker
                    break
                elif len(discovered) > 1:
                    # Genuine ambiguity -- one clarification question,
                    # never a guess (e.g. Berkshire's A/B classes).
                    candidates = tuple(
                        ResolutionCandidate(ticker=c.ticker, display_name=c.display_name)
                        for c in discovered
                    )
                    break

        # Step 6: the ticker-shape heuristic, on the original name only.
        if ticker is None and unsupported_instrument_type is None and not candidates:
            if _looks_like_explicit_ticker(company_name.strip()):
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

    if ticker is not None and value_absolute is None and weight is None:
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

    if suggested:
        assert ticker is not None
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
            status=RowResolutionStatus.SUGGESTED,
            message=f"Atlas believes this is {candidates[0].display_name} ({candidates[0].ticker}).",
            candidates=candidates,
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
