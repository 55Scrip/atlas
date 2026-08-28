"""The unified import pipeline's orchestrator: parse -> resolve ->
detect duplicates -> flag genuine ambiguity -- one stateless function,
identical regardless of which of the entry doors (paste, CSV, broker-
guided paste, manual) the raw text came from. Never persists anything;
confirming an import still goes through the existing, unmodified
`atlas.alpha.portfolio.service.AlphaPortfolioService`.
"""
from __future__ import annotations

from atlas.alpha.portfolio_import.duplicate_detection import apply_duplicate_detection
from atlas.alpha.portfolio_import.models import ImportPreview, RowResolutionStatus
from atlas.alpha.portfolio_import.resolution_service import DiscoverFn, LookupAliasFn, resolve_row
from atlas.alpha.portfolio_import.row_parser import parse_input

_CURRENCY_RELEVANT_STATUSES = (RowResolutionStatus.RESOLVED, RowResolutionStatus.SUGGESTED)


class PortfolioImportPreviewService:
    def preview(
        self,
        raw_text: str,
        existing_tickers: frozenset[str] = frozenset(),
        *,
        discover: DiscoverFn | None = None,
        lookup_alias: LookupAliasFn | None = None,
    ) -> ImportPreview:
        parsed_input = parse_input(raw_text)
        resolved_rows = tuple(
            resolve_row(row, discover=discover, lookup_alias=lookup_alias) for row in parsed_input.rows
        )
        rows = apply_duplicate_detection(resolved_rows, existing_tickers)

        currencies = {
            row.currency
            for row in rows
            if row.status in _CURRENCY_RELEVANT_STATUSES and row.currency is not None
        }
        currency_conflict = len(currencies) > 1

        return ImportPreview(
            rows=rows, header_detected=parsed_input.header_detected, currency_conflict=currency_conflict
        )
