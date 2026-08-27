"""HTTP request/response schemas for the unified import preview endpoint.

Wire format is camelCase via the shared Core `CamelModel` (ADR-004),
same convention `atlas.alpha.portfolio.api.schemas` already follows.
"""
from __future__ import annotations

from atlas.alpha.portfolio_import.models import ImportPreview, ParsedHoldingRow, ResolutionCandidate
from atlas.core.infrastructure.api.serialization import CamelModel


class ImportPreviewRequestBody(CamelModel):
    raw_text: str


class ResolutionCandidateView(CamelModel):
    ticker: str
    display_name: str

    @classmethod
    def from_domain(cls, candidate: ResolutionCandidate) -> "ResolutionCandidateView":
        return cls(ticker=candidate.ticker, display_name=candidate.display_name)


class ParsedHoldingRowView(CamelModel):
    line_number: int
    raw: str
    original_name: str | None = None
    ticker: str | None = None
    quantity: float | None = None
    price: float | None = None
    value_absolute: float | None = None
    weight_percent: float | None = None
    currency: str | None = None
    status: str
    message: str | None = None
    candidates: list[ResolutionCandidateView] = []
    already_held: bool = False

    @classmethod
    def from_domain(cls, row: ParsedHoldingRow) -> "ParsedHoldingRowView":
        return cls(
            line_number=row.line_number,
            raw=row.raw,
            original_name=row.original_name,
            ticker=row.ticker,
            quantity=row.quantity,
            price=row.price,
            value_absolute=row.value_absolute,
            weight_percent=row.weight_percent,
            currency=row.currency,
            status=row.status.value,
            message=row.message,
            candidates=[ResolutionCandidateView.from_domain(c) for c in row.candidates],
            already_held=row.already_held,
        )


class ImportPreviewView(CamelModel):
    rows: list[ParsedHoldingRowView]
    header_detected: bool
    holdings_found: int
    resolved_count: int
    needs_review: bool
    currency_conflict: bool

    @classmethod
    def from_domain(cls, preview: ImportPreview) -> "ImportPreviewView":
        return cls(
            rows=[ParsedHoldingRowView.from_domain(row) for row in preview.rows],
            header_detected=preview.header_detected,
            holdings_found=preview.holdings_found,
            resolved_count=preview.resolved_count,
            needs_review=preview.needs_review,
            currency_conflict=preview.currency_conflict,
        )
