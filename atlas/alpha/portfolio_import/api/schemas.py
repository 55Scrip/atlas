"""HTTP request/response schemas for the unified import preview endpoint.

Wire format is camelCase via the shared Core `CamelModel` (ADR-004),
same convention `atlas.alpha.portfolio.api.schemas` already follows.
"""
from __future__ import annotations

from atlas.alpha.portfolio_import.models import ImportPreview, ParsedHoldingRow, ResolutionCandidate
from atlas.core.infrastructure.api.serialization import CamelModel


class ImportPreviewRequestBody(CamelModel):
    raw_text: str


class ResolvedNameView(CamelModel):
    original_name: str
    ticker: str


class RememberResolutionsRequestBody(CamelModel):
    resolutions: list[ResolvedNameView]


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
    instrument_type: str | None = None
    candidates: list[ResolutionCandidateView] = []
    already_held: bool = False
    # Which security this row names, as distinct from whether the row could
    # be read. Absent when no identity resolver ran or the row carried no
    # identifier able to answer. Provider payloads are never exposed -- only
    # what Atlas concluded and the identifier it concluded it from.
    isin: str | None = None
    market: str | None = None
    identity_status: str | None = None
    identity_reason: str | None = None
    canonical_security_id: str | None = None
    security_name: str | None = None
    exchange_mic: str | None = None
    strong_identifier_used: str | None = None

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
            instrument_type=row.instrument_type,
            candidates=[ResolutionCandidateView.from_domain(c) for c in row.candidates],
            already_held=row.already_held,
            isin=row.isin,
            market=row.market,
            identity_status=row.identity_status,
            identity_reason=row.identity_reason,
            canonical_security_id=row.canonical_security_id,
            security_name=row.security_name,
            exchange_mic=row.exchange_mic,
            strong_identifier_used=row.strong_identifier_used,
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
