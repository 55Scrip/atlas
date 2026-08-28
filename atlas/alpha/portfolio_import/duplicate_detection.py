"""Within-batch duplicate detection (a ticker appearing twice in one
submission -- always a genuine error, since it makes the batch's own
size ambiguous) and against-existing-portfolio detection (a ticker
already held -- informational only, never blocks import; Zero-Effort
Onboarding's review philosophy: "already held" is a fact, not an
ambiguity to interrupt on)."""
from __future__ import annotations

from dataclasses import replace

from atlas.alpha.portfolio_import.models import ParsedHoldingRow, RowResolutionStatus


_TICKER_BEARING_STATUSES = (RowResolutionStatus.RESOLVED, RowResolutionStatus.SUGGESTED)


def apply_duplicate_detection(
    rows: tuple[ParsedHoldingRow, ...], existing_tickers: frozenset[str] = frozenset()
) -> tuple[ParsedHoldingRow, ...]:
    seen: set[str] = set()
    result: list[ParsedHoldingRow] = []
    for row in rows:
        if row.status not in _TICKER_BEARING_STATUSES or row.ticker is None:
            result.append(row)
            continue
        if row.ticker in seen:
            result.append(
                replace(
                    row,
                    status=RowResolutionStatus.DUPLICATE,
                    message=f"{row.ticker} appears more than once in this import.",
                )
            )
            continue
        seen.add(row.ticker)
        result.append(replace(row, already_held=row.ticker in existing_tickers))
    return tuple(result)
