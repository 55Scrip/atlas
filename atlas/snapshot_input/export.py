"""Snapshot Draft export — confirmed research_notes_snapshot to local notes.md.

This module converts a confirmed research_notes_snapshot draft into a local
research_notes/<TICKER>/notes.md file that the Weekly Review can load via
--research-notes DIR.

No OCR. No image parsing. No AI. No provider imports. No network calls.
Only local Markdown files are written. No portfolio, watchlist, journal, or
company facts files are ever written by this module.
"""

from __future__ import annotations

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

_MAX_BULLET_LENGTH = 500
_MAX_BULLETS_PER_SECTION = 20

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

_KNOWN_SECTIONS = (
    "thesis_notes",
    "evidence_gaps",
    "open_questions",
    "risks_to_monitor",
    "reasons_to_wait",
    "reason_to_wait",
)


@dataclass(frozen=True)
class ResearchNotesExportResult:
    """Outcome of a research notes export attempt."""

    success: bool
    ticker: str
    output_path: Path | None
    reason: str = ""


# ---------------------------------------------------------------------------
# Ticker resolution
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
            "Ticker is required for research notes export. "
            "Add 'ticker' to extracted_fields or include a value in related_tickers."
        )

    if "/" in ticker or "\\" in ticker or ".." in ticker:
        raise ValueError(
            f"Unsafe ticker value {ticker!r}. "
            "Ticker must not contain path separators."
        )

    return ticker


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def _safe_bullet(text: str) -> str:
    return text[:_MAX_BULLET_LENGTH]


def _render_bullets(items: list[str]) -> list[str]:
    """Return bounded bullet lines from a list of strings."""
    lines = []
    for item in items[:_MAX_BULLETS_PER_SECTION]:
        lines.append(f"- {_safe_bullet(str(item))}")
    return lines


def _field_as_list(value: object) -> list[str]:
    """Coerce an extracted_fields value to a list of strings."""
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _build_research_notes_markdown(ticker: str, draft: SnapshotDraft) -> str:
    """Build bounded Markdown content from a confirmed research_notes_snapshot draft."""
    ef = draft.extracted_fields
    lines: list[str] = []

    lines.append(f"# {ticker} Research Notes")
    lines.append("")

    thesis_notes = _field_as_list(ef.get("thesis_notes", []))
    if thesis_notes:
        lines.append("## Thesis Notes")
        lines.extend(_render_bullets(thesis_notes))
        lines.append("")

    evidence_gaps = _field_as_list(ef.get("evidence_gaps", []))
    if evidence_gaps:
        lines.append("## Evidence Gaps")
        lines.extend(_render_bullets(evidence_gaps))
        lines.append("")

    open_questions = _field_as_list(ef.get("open_questions", []))
    if open_questions:
        lines.append("## Open Questions")
        lines.extend(_render_bullets(open_questions))
        lines.append("")

    risks = _field_as_list(ef.get("risks_to_monitor", []))
    if risks:
        lines.append("## Risks to Monitor")
        lines.extend(_render_bullets(risks))
        lines.append("")

    reasons = _field_as_list(ef.get("reasons_to_wait", ef.get("reason_to_wait", [])))
    if reasons:
        lines.append("## Reason to Wait")
        lines.extend(_render_bullets(reasons))
        lines.append("")

    lines.append("## Source")
    lines.append(f"- Source description: {draft.source_description}")
    lines.append(f"- Draft ID: {draft.draft_id}")
    if draft.raw_source_reference:
        lines.append(f"- Source reference: {draft.raw_source_reference}")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Core export function
# ---------------------------------------------------------------------------

def export_research_notes(
    draft: SnapshotDraft,
    output_dir: Path,
    overwrite: bool = False,
) -> ResearchNotesExportResult:
    """Convert a confirmed research_notes_snapshot draft to a local notes.md file.

    Safety guarantees:
    - Only writes research_notes/<TICKER>/notes.md under output_dir.
    - No portfolio, watchlist, journal, or company facts files are written.
    - No provider calls. No network calls. No OCR. No AI.

    Returns a ResearchNotesExportResult describing success or failure.
    """
    # Type check
    if draft.snapshot_type != SnapshotType.RESEARCH_NOTES_SNAPSHOT:
        return ResearchNotesExportResult(
            success=False,
            ticker="",
            output_path=None,
            reason=(
                "Only research_notes_snapshot drafts can be exported to research notes "
                "in this command."
            ),
        )

    # Confirmation check
    if draft.confirmation_status != SnapshotConfirmationStatus.CONFIRMED:
        return ResearchNotesExportResult(
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
        return ResearchNotesExportResult(
            success=False,
            ticker="",
            output_path=None,
            reason=str(exc),
        )

    output_path = output_dir / ticker / "notes.md"

    # Overwrite guard
    if output_path.exists() and not overwrite:
        return ResearchNotesExportResult(
            success=False,
            ticker=ticker,
            output_path=output_path,
            reason=(
                f"{output_path} already exists. "
                "Use --overwrite to replace it."
            ),
        )

    # Build and write markdown
    markdown = _build_research_notes_markdown(ticker, draft)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")

    return ResearchNotesExportResult(
        success=True,
        ticker=ticker,
        output_path=output_path,
    )
