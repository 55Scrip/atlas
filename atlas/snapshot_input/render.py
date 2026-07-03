"""Human-readable renderer for Snapshot Draft validation output.

No OCR. No image parsing. No AI. No provider imports. No network calls.
Output is informational only. Validation does not write to Atlas local input files.
"""

from __future__ import annotations

from atlas.snapshot_input.schema import SnapshotDraft


def render_snapshot_draft_validation(draft: SnapshotDraft) -> str:
    """Render a human-readable validation summary for a Snapshot Draft.

    Output is informational only. This function does not write to any
    Atlas local input file and does not modify the draft.
    """
    lines: list[str] = []

    lines.append("Snapshot Draft Validation")
    lines.append("")
    lines.append("Status: valid")
    lines.append(f"Snapshot Type: {draft.snapshot_type.value}")
    lines.append(f"Confidence: {draft.confidence.value}")
    lines.append(f"Confirmation Status: {draft.confirmation_status.value}")
    lines.append(f"Target Local File: {draft.target_local_file}")

    if draft.related_tickers:
        lines.append(f"Related Tickers: {', '.join(draft.related_tickers)}")

    if draft.uncertainties:
        lines.append("Uncertainties:")
        for u in draft.uncertainties:
            lines.append(f"  - {u}")
    else:
        lines.append("Uncertainties: none")

    if draft.missing_required_fields:
        lines.append("Missing Required Fields:")
        for f in draft.missing_required_fields:
            lines.append(f"  - {f}")
    else:
        lines.append("Missing Required Fields: none")

    if draft.raw_source_reference:
        lines.append(f"Source Reference: {draft.raw_source_reference}")

    if draft.notes:
        lines.append(f"Notes: {draft.notes}")

    lines.append("")
    lines.append("Safety Boundary:")
    lines.append("  - Draft validation does not write to Atlas local input files.")

    return "\n".join(lines)


def render_snapshot_draft_validation_error(error_message: str) -> str:
    """Render a human-readable error summary for a failed draft validation."""
    lines = [
        "Snapshot Draft Validation",
        "",
        "Status: invalid",
        f"Error: {error_message}",
    ]
    return "\n".join(lines)


def render_research_notes_export_success(ticker: str, output_path: object) -> str:
    """Render a success summary after writing a research notes file."""
    lines = [
        "Research Notes Export",
        "",
        "Status: written",
        f"Ticker: {ticker}",
        f"Output File: {output_path}",
        "",
        "Safety Boundary:",
        "  - Only local research notes were written.",
        "  - No portfolio, watchlist, journal, or company facts files were changed.",
    ]
    return "\n".join(lines)


def render_research_notes_export_blocked(reason: str) -> str:
    """Render a blocked summary when research notes export cannot proceed."""
    lines = [
        "Research Notes Export",
        "",
        "Status: blocked",
        f"Reason: {reason}",
    ]
    return "\n".join(lines)
