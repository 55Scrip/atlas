"""Data model for the unified portfolio import pipeline's preview step.

Pure, stateless value objects -- nothing here is persisted. `RESOLVED`
rows carry enough (`ticker`, and either `weight_percent` or a derivable
`value_absolute`/`quantity`+`price`) to become an `ImportHoldingInput`
(`atlas.alpha.portfolio.service`) unchanged at confirm time.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ColumnRole(str, Enum):
    """What one column of a parsed import source means. A column with
    no recognized header (an extra broker column this pipeline doesn't
    use, e.g. "Förändring idag") is simply absent from a row's mapping,
    never forced into one of these."""

    COMPANY_NAME = "COMPANY_NAME"
    TICKER = "TICKER"
    QUANTITY = "QUANTITY"
    PRICE = "PRICE"
    VALUE = "VALUE"
    WEIGHT = "WEIGHT"
    CURRENCY = "CURRENCY"


class RowResolutionStatus(str, Enum):
    """A row's outcome after the full pipeline (parse -> resolve ->
    derive -> detect duplicates) has run once. `ImportPreview.needs_review`
    is true whenever any row is anything other than `RESOLVED`."""

    RESOLVED = "RESOLVED"
    # No multi-candidate resolver exists yet (Phase 3: security_discovery
    # + one-question clarification); reserved for that follow-up so
    # `ParsedHoldingRow.status` doesn't need to change shape again then.
    AMBIGUOUS = "AMBIGUOUS"
    UNRESOLVED = "UNRESOLVED"
    DUPLICATE = "DUPLICATE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ResolutionCandidate:
    """One option in an `AMBIGUOUS` row's clarification choice -- e.g.
    "Investor A" vs "Investor B" -- surfaced by the `security_discovery`
    fallback (ticker-resolution priority step 4) when more than one
    company plausibly matches the pasted name."""

    ticker: str
    display_name: str


@dataclass(frozen=True)
class ParsedHoldingRow:
    line_number: int
    raw: str
    original_name: str | None = None
    ticker: str | None = None
    quantity: float | None = None
    price: float | None = None
    value_absolute: float | None = None
    weight_percent: float | None = None
    currency: str | None = None
    status: RowResolutionStatus = RowResolutionStatus.ERROR
    message: str | None = None
    # Populated only when status is AMBIGUOUS -- the one-question
    # clarification the review screen asks ("Investor A or Investor B?").
    candidates: tuple[ResolutionCandidate, ...] = ()
    # Informational only -- never blocks import, never changes `status`.
    # Zero-Effort Onboarding review philosophy: "already held" is a fact
    # worth telling the investor, not a genuine ambiguity to interrupt on.
    already_held: bool = False


@dataclass(frozen=True)
class ImportPreview:
    rows: tuple[ParsedHoldingRow, ...]
    header_detected: bool
    # True when resolved rows report more than one distinct currency --
    # refuses auto-derivation across the batch (see service.py), so this
    # alone forces review even if every row individually resolved.
    currency_conflict: bool = False

    @property
    def holdings_found(self) -> int:
        return len(self.rows)

    @property
    def resolved_count(self) -> int:
        return sum(1 for row in self.rows if row.status == RowResolutionStatus.RESOLVED)

    @property
    def needs_review(self) -> bool:
        if self.currency_conflict:
            return True
        return any(row.status != RowResolutionStatus.RESOLVED for row in self.rows)
