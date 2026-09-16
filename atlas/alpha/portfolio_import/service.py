"""The unified import pipeline's orchestrator: parse -> resolve ->
detect duplicates -> flag genuine ambiguity -- one stateless function,
identical regardless of which of the entry doors (paste, CSV, broker-
guided paste, manual) the raw text came from. Never persists anything;
confirming an import still goes through the existing, unmodified
`atlas.alpha.portfolio.service.AlphaPortfolioService`.

Identity resolution is a second, optional pass over the finished rows.
Optional because it is the only step here that can reach a network: a row
carrying an ISIN Atlas has never seen needs one provider call to learn which
share class it is. `resolve_identity=None` -- the default -- leaves this
pipeline exactly as pure as it has always been, and the API wires a real
resolver in.

It is a pass rather than a step inside `resolve_row` because the two answer
different questions. `resolve_row` asks "can Atlas read this line", and its
`RESOLVED` has always meant "a ticker was found". Whether that ticker names
a security Atlas can actually identify is a separate question with a
separate answer, and conflating them is how a Stockholm holding came to be
reported as resolved while Atlas knew nothing but a string.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable, Protocol

from atlas.alpha.portfolio_import.duplicate_detection import apply_duplicate_detection
from atlas.alpha.portfolio_import.models import ImportPreview, ParsedHoldingRow, RowResolutionStatus
from atlas.alpha.portfolio_import.resolution_service import DiscoverFn, LookupAliasFn, resolve_row
from atlas.alpha.portfolio_import.row_parser import parse_input

_CURRENCY_RELEVANT_STATUSES = (RowResolutionStatus.RESOLVED, RowResolutionStatus.SUGGESTED)


class IdentityResolution(Protocol):
    """What a resolver hands back. Structural rather than imported so this
    package keeps no dependency on the identity packages at all -- the
    security master, the provider and the canonical aggregate stay on the
    other side of this seam."""

    status: Any
    reason: str
    security: Any
    strong_identifier_used: str | None
    exchange_mic: str | None


#: `(ticker, company_name, isin, market, account_currency) -> IdentityResolution`
ResolveIdentityFn = Callable[..., IdentityResolution]


class PortfolioImportPreviewService:
    def preview(
        self,
        raw_text: str,
        existing_tickers: frozenset[str] = frozenset(),
        *,
        discover: DiscoverFn | None = None,
        lookup_alias: LookupAliasFn | None = None,
        resolve_identity: ResolveIdentityFn | None = None,
    ) -> ImportPreview:
        parsed_input = parse_input(raw_text)
        resolved_rows = tuple(
            resolve_row(row, discover=discover, lookup_alias=lookup_alias) for row in parsed_input.rows
        )
        rows = apply_duplicate_detection(resolved_rows, existing_tickers)

        if resolve_identity is not None:
            rows = tuple(_with_identity(row, resolve_identity) for row in rows)

        currencies = {
            row.currency
            for row in rows
            if row.status in _CURRENCY_RELEVANT_STATUSES and row.currency is not None
        }
        currency_conflict = len(currencies) > 1

        return ImportPreview(
            rows=rows, header_detected=parsed_input.header_detected, currency_conflict=currency_conflict
        )


def _with_identity(row: ParsedHoldingRow, resolve_identity: ResolveIdentityFn) -> ParsedHoldingRow:
    """Ask what security this row names, for rows that carry an identifier
    capable of answering.

    Rows with no ISIN are skipped rather than asked: the resolver would
    decline them anyway, and skipping keeps the guarantee visible here --
    a ticker-only import cannot reach a provider through this path.

    A resolver failure is deliberately not caught. An import that quietly
    degrades to "identity unknown" whenever the network hiccups would be
    indistinguishable from an import that genuinely cannot identify the
    holding, and those two need to stay tellable apart; the resolver already
    reports provider trouble as its own status rather than raising.
    """
    if not row.isin:
        return row

    result = resolve_identity(
        ticker=row.ticker,
        company_name=row.original_name,
        isin=row.isin,
        market=row.market,
        account_currency=row.currency,
    )
    security = getattr(result, "security", None)
    status = getattr(result, "status", None)
    return replace(
        row,
        identity_status=getattr(status, "value", status),
        identity_reason=getattr(result, "reason", None),
        canonical_security_id=str(security.id) if security is not None else None,
        security_name=security.canonical_company_name if security is not None else None,
        exchange_mic=getattr(result, "exchange_mic", None),
        strong_identifier_used=getattr(result, "strong_identifier_used", None),
    )
