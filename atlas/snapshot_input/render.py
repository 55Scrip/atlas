"""Human-readable renderer for Snapshot Draft validation, review, and export output.

No OCR. No image parsing. No AI. No provider imports. No network calls.
Output is informational only. No function in this module writes to any file.
"""

from __future__ import annotations

from atlas.snapshot_input.schema import SnapshotConfirmationStatus, SnapshotDraft, SnapshotType

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Snapshot types that require a ticker for export/review purposes.
_TICKER_REQUIRED_TYPES = {
    SnapshotType.RESEARCH_NOTES_SNAPSHOT,
    SnapshotType.COMPANY_FACTS_SNAPSHOT,
}

_MAX_SCALAR_DISPLAY = 80


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


# ---------------------------------------------------------------------------
# Review helpers
# ---------------------------------------------------------------------------

def _ticker_from_draft(draft: SnapshotDraft) -> str:
    """Return the ticker from extracted_fields or first related_tickers entry."""
    raw = draft.extracted_fields.get("ticker", "")
    if raw and str(raw).strip():
        return str(raw).strip().upper()
    if draft.related_tickers:
        return draft.related_tickers[0].strip().upper()
    return ""


def _is_unsafe_ticker(ticker: str) -> bool:
    return not ticker or "/" in ticker or "\\" in ticker or ".." in ticker


def _summarise_extracted_fields(extracted_fields: dict) -> list[str]:
    """Return concise summary lines for extracted_fields. No unbounded output."""
    lines: list[str] = []
    for key in sorted(extracted_fields.keys()):
        value = extracted_fields[key]
        if isinstance(value, list):
            lines.append(f"  - {key}: {len(value)} item(s)")
        elif isinstance(value, dict):
            lines.append(f"  - {key}: {len(value)} key(s)")
        elif isinstance(value, str):
            display = value[:_MAX_SCALAR_DISPLAY] + "..." if len(value) > _MAX_SCALAR_DISPLAY else value
            lines.append(f"  - {key}: {display!r}")
        else:
            lines.append(f"  - {key}: {value!r}")
    return lines


def collect_snapshot_draft_review_issues(draft: SnapshotDraft) -> tuple[str, ...]:
    """Collect blocking issues for a Snapshot Draft per Sprint 227 rules.

    Returns a tuple of issue strings. Empty tuple means no blocking issues.
    These issues survive schema validation — schema-level errors prevent a draft
    from being constructed at all.
    """
    issues: list[str] = []

    if draft.snapshot_type == SnapshotType.UNKNOWN_SNAPSHOT:
        issues.append("Unsupported snapshot type: unknown_snapshot cannot be confirmed.")

    already_terminal = draft.confirmation_status in (
        SnapshotConfirmationStatus.CONFIRMED,
        SnapshotConfirmationStatus.REJECTED,
        SnapshotConfirmationStatus.SUPERSEDED,
    )
    if already_terminal:
        issues.append(
            f"Draft is already in terminal state: {draft.confirmation_status.value}. "
            "Confirmation is not applicable."
        )

    if not draft.extracted_fields:
        issues.append("Extracted fields are empty. Review the source interpretation before confirming.")

    if draft.snapshot_type in _TICKER_REQUIRED_TYPES:
        ticker = _ticker_from_draft(draft)
        if not ticker:
            issues.append(
                f"Ticker is required for {draft.snapshot_type.value} drafts "
                "but was not found in extracted_fields or related_tickers."
            )
        elif _is_unsafe_ticker(ticker):
            issues.append(
                f"Unsafe ticker value {ticker!r}: ticker must not contain path separators."
            )

    return tuple(issues)


def render_snapshot_draft_review(draft: SnapshotDraft) -> str:
    """Render a read-only confirmation checklist for a Snapshot Draft.

    This function is informational only. It does not confirm, reject, or
    modify the draft. It does not write to any file.
    """
    lines: list[str] = []

    # Header
    lines.append("Snapshot Draft Review")
    lines.append("")
    lines.append("Status: reviewable")
    lines.append(f"Snapshot Type: {draft.snapshot_type.value}")
    lines.append(f"Confidence: {draft.confidence.value}")
    lines.append(f"Confirmation Status: {draft.confirmation_status.value}")

    # Exportability
    is_confirmed = draft.confirmation_status == SnapshotConfirmationStatus.CONFIRMED
    if is_confirmed:
        lines.append("Exportable: yes")
    else:
        lines.append("Exportable: no")
        lines.append("  Reason: only confirmed drafts are exportable.")

    lines.append(f"Target Local File: {draft.target_local_file}")

    if draft.related_tickers:
        lines.append(f"Related Tickers: {', '.join(draft.related_tickers)}")

    # Source
    lines.append("")
    lines.append("Source:")
    lines.append(f"  - Source Description: {draft.source_description}")
    if draft.raw_source_reference:
        lines.append(f"  - Raw Source Reference: {draft.raw_source_reference}")
    if draft.notes:
        lines.append(f"  - Notes: {draft.notes[:_MAX_SCALAR_DISPLAY]}")

    # Review Checklist
    lines.append("")
    lines.append("Review Checklist:")
    lines.append(f"  - Draft ID: {'present' if draft.draft_id else 'missing'}")
    lines.append(f"  - Snapshot Type: {'present' if draft.snapshot_type else 'missing'}")
    lines.append(f"  - Source Description: {'present' if draft.source_description else 'missing'}")
    lines.append(f"  - Target Local File: {'present' if draft.target_local_file else 'missing'}")
    lines.append(f"  - Extracted Fields: {'present' if draft.extracted_fields else 'empty'}")
    if draft.uncertainties:
        lines.append(f"  - Uncertainties: {len(draft.uncertainties)} listed")
    else:
        lines.append("  - Uncertainties: none listed")
    if draft.missing_required_fields:
        lines.append(f"  - Missing Required Fields: {len(draft.missing_required_fields)} listed")
    else:
        lines.append("  - Missing Required Fields: none listed")
    lines.append("  - Safety Boundary: visible")

    # Uncertainties detail
    if draft.uncertainties:
        lines.append("")
        lines.append("Uncertainties:")
        for u in draft.uncertainties:
            lines.append(f"  - {u}")

    # Missing required fields detail
    if draft.missing_required_fields:
        lines.append("")
        lines.append("Missing Required Fields (warnings — review before confirming):")
        for f in draft.missing_required_fields:
            lines.append(f"  - {f}")

    # Extracted fields summary
    lines.append("")
    lines.append("Extracted Fields:")
    if draft.extracted_fields:
        lines.extend(_summarise_extracted_fields(draft.extracted_fields))
    else:
        lines.append("  (empty)")

    # Blocking issues
    issues = collect_snapshot_draft_review_issues(draft)
    lines.append("")
    lines.append("Blocking Issues:")
    if issues:
        for issue in issues:
            lines.append(f"  - {issue}")
    else:
        lines.append("  None")

    # Research notes specific checklist
    if draft.snapshot_type == SnapshotType.RESEARCH_NOTES_SNAPSHOT:
        ef = draft.extracted_fields
        lines.append("")
        lines.append("Research Notes Review:")
        ticker = _ticker_from_draft(draft)
        lines.append(f"  - Ticker: {ticker if ticker else 'missing'}")
        lines.append(f"  - Title: {'present' if ef.get('title') else 'missing'}")
        lines.append(f"  - Thesis Notes: {'present' if ef.get('thesis_notes') else 'missing'}")
        lines.append(f"  - Evidence Gaps: {'present' if ef.get('evidence_gaps') else 'missing'}")
        lines.append(f"  - Open Questions: {'present' if ef.get('open_questions') else 'missing'}")
        lines.append(f"  - Risks to Monitor: {'present' if ef.get('risks_to_monitor') else 'missing'}")
        rw = ef.get("reasons_to_wait") or ef.get("reason_to_wait")
        lines.append(f"  - Reasons to Wait: {'present' if rw else 'missing'}")

    # Safety boundary
    lines.append("")
    lines.append("Safety Boundary:")
    lines.append("  - Review is read-only.")
    lines.append("  - Review does not confirm the draft.")
    lines.append("  - Review does not write Atlas local input files.")

    return "\n".join(lines)


def render_snapshot_draft_review_error(error_message: str) -> str:
    """Render an error summary for a failed snapshot review load."""
    lines = [
        "Snapshot Draft Review",
        "",
        "Status: invalid",
        f"Error: {error_message}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Confirm renderers
# ---------------------------------------------------------------------------

def render_snapshot_confirm_success(
    input_path: object,
    output_path: object,
    snapshot_type: str,
    already_confirmed: bool,
) -> str:
    """Render a success summary after writing a confirmed draft copy."""
    lines = [
        "Snapshot Draft Confirmation",
        "",
        "Status: confirmed",
    ]
    if already_confirmed:
        lines.append(
            "Note: input draft was already confirmed; a confirmed copy was written."
        )
    lines += [
        f"Input Draft: {input_path}",
        f"Output Draft: {output_path}",
        f"Snapshot Type: {snapshot_type}",
        "Confirmation Status: confirmed",
        "",
        "Safety Boundary:",
        "  - Original draft was not modified.",
        "  - No Atlas local input files were changed.",
        "  - Export commands must still be run separately.",
    ]
    return "\n".join(lines)


def render_snapshot_confirm_blocked(reason: str) -> str:
    """Render a blocked summary when confirmation cannot proceed."""
    lines = [
        "Snapshot Draft Confirmation",
        "",
        "Status: blocked",
        f"Reason: {reason}",
    ]
    return "\n".join(lines)


def render_snapshot_confirm_error(error_message: str) -> str:
    """Render an error summary for a failed snapshot confirm load."""
    lines = [
        "Snapshot Draft Confirmation",
        "",
        "Status: invalid",
        f"Error: {error_message}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reject renderers
# ---------------------------------------------------------------------------

def render_snapshot_reject_success(
    input_path: object,
    output_path: object,
    snapshot_type: str,
    already_rejected: bool,
    was_confirmed: bool,
) -> str:
    """Render a success summary after writing a rejected draft copy."""
    lines = [
        "Snapshot Draft Rejection",
        "",
        "Status: rejected",
    ]
    if already_rejected:
        lines.append(
            "Note: input draft was already rejected; a rejected copy was written."
        )
    elif was_confirmed:
        lines.append(
            "Note: input draft was confirmed; a rejected copy was written for this workflow branch."
        )
    lines += [
        f"Input Draft: {input_path}",
        f"Output Draft: {output_path}",
        f"Snapshot Type: {snapshot_type}",
        "Confirmation Status: rejected",
        "",
        "Safety Boundary:",
        "  - Original draft was not modified.",
        "  - No Atlas local input files were changed.",
        "  - Rejected drafts are not exportable.",
    ]
    return "\n".join(lines)


def render_snapshot_reject_blocked(reason: str) -> str:
    """Render a blocked summary when rejection cannot proceed."""
    lines = [
        "Snapshot Draft Rejection",
        "",
        "Status: blocked",
        f"Reason: {reason}",
    ]
    return "\n".join(lines)


def render_snapshot_reject_error(error_message: str) -> str:
    """Render an error summary for a failed snapshot reject load."""
    lines = [
        "Snapshot Draft Rejection",
        "",
        "Status: invalid",
        f"Error: {error_message}",
    ]
    return "\n".join(lines)
