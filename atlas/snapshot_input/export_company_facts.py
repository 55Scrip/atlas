"""Snapshot Draft export — confirmed company_facts_snapshot to local TICKER.json.

This module converts a confirmed company_facts_snapshot draft into a local
company_facts/<TICKER>.json file that the Weekly Review detects via
--company-facts DIR.

No OCR. No image parsing. No AI. No provider imports. No network calls.
No external company data enrichment. Only local JSON files are written.
No portfolio, watchlist, journal, or research notes files are ever written.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from atlas.snapshot_input.schema import (
    SnapshotConfirmationStatus,
    SnapshotDraft,
    SnapshotType,
)

# ---------------------------------------------------------------------------
# Bounds
# ---------------------------------------------------------------------------

_MAX_STRING_LENGTH = 800
_MAX_LIST_ITEMS = 30
_MAX_LIST_ITEM_LENGTH = 500

# Fields from extracted_fields that map directly to the output JSON.
_KNOWN_FIELDS = (
    "ticker",
    "company_name",
    "business_summary",
    "sector",
    "geography",
    "revenue_drivers",
    "key_risks",
    "notes",
)


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompanyFactsExportResult:
    """Outcome of a company facts export attempt."""

    success: bool
    ticker: str
    output_path: Path | None
    reason: str = ""


# ---------------------------------------------------------------------------
# Ticker resolution (mirrors export.py pattern)
# ---------------------------------------------------------------------------


def _resolve_ticker(draft: SnapshotDraft) -> str:
    """Return the ticker from extracted_fields or first related_tickers entry.

    Raises ValueError on missing, empty, or unsafe ticker values.
    """
    ticker: str = ""

    raw = draft.extracted_fields.get("ticker", "")
    if raw and str(raw).strip():
        ticker = str(raw).strip().upper()
    elif draft.related_tickers:
        ticker = draft.related_tickers[0].strip().upper()

    if not ticker:
        raise ValueError(
            "Ticker is required for company facts export. "
            "Add 'ticker' to extracted_fields or include a value in related_tickers."
        )

    if "/" in ticker or "\\" in ticker or ".." in ticker:
        raise ValueError(
            f"Unsafe ticker value {ticker!r}. "
            "Ticker must not contain path separators."
        )

    return ticker


# ---------------------------------------------------------------------------
# JSON generation
# ---------------------------------------------------------------------------


def _safe_string(value: object) -> str:
    """Coerce to string and truncate to _MAX_STRING_LENGTH."""
    s = str(value)
    return s[:_MAX_STRING_LENGTH]


def _safe_list(value: object) -> list[str]:
    """Coerce to a bounded list of safe strings."""
    if isinstance(value, list):
        items = [str(v)[:_MAX_LIST_ITEM_LENGTH] for v in value if str(v).strip()]
    elif isinstance(value, str) and value.strip():
        items = [value.strip()[:_MAX_LIST_ITEM_LENGTH]]
    else:
        return []
    return items[:_MAX_LIST_ITEMS]


def _build_company_facts_json(ticker: str, draft: SnapshotDraft) -> dict:
    """Build bounded company facts dict from a confirmed company_facts_snapshot draft."""
    ef = draft.extracted_fields
    output: dict = {}

    output["ticker"] = ticker

    for field in ("company_name", "business_summary", "sector"):
        value = ef.get(field)
        if value is not None:
            output[field] = _safe_string(value)

    for field in ("geography", "revenue_drivers", "key_risks"):
        value = ef.get(field)
        if value is not None:
            output[field] = _safe_list(value)

    notes = ef.get("notes")
    if notes is not None:
        output["notes"] = _safe_string(notes)

    output["source"] = {
        "draft_id": draft.draft_id,
        "source_description": draft.source_description,
        "raw_source_reference": draft.raw_source_reference,
    }

    return output


# ---------------------------------------------------------------------------
# Core export function
# ---------------------------------------------------------------------------


def export_company_facts(
    draft: SnapshotDraft,
    output_dir: Path,
    overwrite: bool = False,
) -> CompanyFactsExportResult:
    """Convert a confirmed company_facts_snapshot draft to a local TICKER.json file.

    Safety guarantees:
    - Only writes company_facts/<TICKER>.json under output_dir.
    - No portfolio, watchlist, journal, or research notes files are written.
    - No provider calls. No network calls. No OCR. No AI.
    - No external company data enrichment.

    Returns a CompanyFactsExportResult describing success or failure.
    """
    # Type check
    if draft.snapshot_type != SnapshotType.COMPANY_FACTS_SNAPSHOT:
        return CompanyFactsExportResult(
            success=False,
            ticker="",
            output_path=None,
            reason=(
                "Only company_facts_snapshot drafts can be exported to company facts "
                "in this command."
            ),
        )

    # Confirmation check
    if draft.confirmation_status != SnapshotConfirmationStatus.CONFIRMED:
        return CompanyFactsExportResult(
            success=False,
            ticker="",
            output_path=None,
            reason=(
                "Draft is not confirmed. Conversion requires confirmation_status=confirmed."
            ),
        )

    # Ticker resolution
    try:
        ticker = _resolve_ticker(draft)
    except ValueError as exc:
        return CompanyFactsExportResult(
            success=False,
            ticker="",
            output_path=None,
            reason=str(exc),
        )

    output_path = output_dir / f"{ticker}.json"

    # Overwrite guard
    if output_path.exists() and not overwrite:
        return CompanyFactsExportResult(
            success=False,
            ticker=ticker,
            output_path=output_path,
            reason=(
                f"{output_path} already exists. "
                "Use --overwrite to replace it."
            ),
        )

    # Build and write JSON
    facts = _build_company_facts_json(ticker, draft)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(facts, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )

    return CompanyFactsExportResult(
        success=True,
        ticker=ticker,
        output_path=output_path,
    )
