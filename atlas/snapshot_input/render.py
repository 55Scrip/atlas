"""Human-readable renderer for Snapshot Draft validation, review, and export output.

No OCR. No image parsing. No AI. No provider imports. No network calls.
Output is informational only. No function in this module writes to any file.
"""

from __future__ import annotations

from atlas.snapshot_input.schema import SnapshotConfirmationStatus, SnapshotDraft, SnapshotType
from atlas.snapshot_input import strings as strings_en
from atlas.snapshot_input import strings_sv as strings_sv
from atlas.locale_support import ensure_supported_locale as _ensure_locale

# ---------------------------------------------------------------------------
# Locale dispatch
# ---------------------------------------------------------------------------

def _strings_for_locale(locale: str):
    """Return the strings module for the given locale.

    Calls _ensure_locale — sv raises until locale_support.py is updated.
    English strings are returned for locale="en".
    Swedish strings are mapped for future locale="sv".
    """
    _ensure_locale(locale)
    if locale == "sv":
        return strings_sv
    return strings_en

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Snapshot types that require a ticker for export/review purposes.
_TICKER_REQUIRED_TYPES = {
    SnapshotType.RESEARCH_NOTES_SNAPSHOT,
    SnapshotType.COMPANY_FACTS_SNAPSHOT,
}

_MAX_SCALAR_DISPLAY = 80


def render_snapshot_draft_validation(draft: SnapshotDraft, *, locale: str = "en") -> str:
    """Render a human-readable validation summary for a Snapshot Draft.

    Output is informational only. This function does not write to any
    Atlas local input file and does not modify the draft.
    Only locale="en" is currently supported.
    """
    S = _strings_for_locale(locale)
    lines: list[str] = []

    lines.append(S.HEADING_VALIDATION)
    lines.append("")
    lines.append(S.STATUS_VALID)
    lines.append(f"Snapshot Type: {draft.snapshot_type.value}")
    lines.append(f"Confidence: {draft.confidence.value}")
    lines.append(f"Confirmation Status: {draft.confirmation_status.value}")
    lines.append(f"Target Local File: {draft.target_local_file}")

    if draft.related_tickers:
        lines.append(f"Related Tickers: {', '.join(draft.related_tickers)}")

    if draft.uncertainties:
        lines.append(S.SECTION_UNCERTAINTIES)
        for u in draft.uncertainties:
            lines.append(f"  - {u}")
    else:
        lines.append(S.UNCERTAINTIES_NONE)

    if draft.missing_required_fields:
        lines.append(S.SECTION_MISSING_REQUIRED_FIELDS)
        for f in draft.missing_required_fields:
            lines.append(f"  - {f}")
    else:
        lines.append(S.MISSING_REQUIRED_FIELDS_NONE)

    if draft.raw_source_reference:
        lines.append(f"Source Reference: {draft.raw_source_reference}")

    if draft.notes:
        lines.append(f"Notes: {draft.notes}")

    lines.append("")
    lines.append(S.SECTION_SAFETY_BOUNDARY)
    lines.append(S.SAFETY_VALIDATION_NO_WRITE)

    return "\n".join(lines)


def render_snapshot_draft_validation_error(error_message: str, *, locale: str = "en") -> str:
    """Render a human-readable error summary for a failed draft validation."""
    S = _strings_for_locale(locale)
    lines = [
        S.HEADING_VALIDATION,
        "",
        S.STATUS_INVALID,
        f"Error: {error_message}",
    ]
    return "\n".join(lines)


def render_research_notes_export_success(ticker: str, output_path: object, *, locale: str = "en") -> str:
    """Render a success summary after writing a research notes file."""
    S = _strings_for_locale(locale)
    lines = [
        S.HEADING_RESEARCH_NOTES_EXPORT,
        "",
        S.STATUS_WRITTEN,
        f"Ticker: {ticker}",
        f"Output File: {output_path}",
        "",
        S.SECTION_SAFETY_BOUNDARY,
        S.SAFETY_RESEARCH_NOTES_ONLY,
        S.SAFETY_RESEARCH_NOTES_NO_OTHER,
    ]
    return "\n".join(lines)


def render_research_notes_export_blocked(reason: str, *, locale: str = "en") -> str:
    """Render a blocked summary when research notes export cannot proceed."""
    S = _strings_for_locale(locale)
    lines = [
        S.HEADING_RESEARCH_NOTES_EXPORT,
        "",
        S.STATUS_BLOCKED,
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


def render_snapshot_draft_review(draft: SnapshotDraft, *, locale: str = "en") -> str:
    """Render a read-only confirmation checklist for a Snapshot Draft.

    This function is informational only. It does not confirm, reject, or
    modify the draft. It does not write to any file.
    Only locale="en" is currently supported.
    """
    S = _strings_for_locale(locale)
    lines: list[str] = []

    # Header
    lines.append(S.HEADING_REVIEW)
    lines.append("")
    lines.append(S.STATUS_REVIEWABLE)
    lines.append(f"Snapshot Type: {draft.snapshot_type.value}")
    lines.append(f"Confidence: {draft.confidence.value}")
    lines.append(f"Confirmation Status: {draft.confirmation_status.value}")

    # Exportability
    is_confirmed = draft.confirmation_status == SnapshotConfirmationStatus.CONFIRMED
    if is_confirmed:
        lines.append(S.EXPORTABLE_YES)
    else:
        lines.append(S.EXPORTABLE_NO)
        lines.append(S.EXPORTABLE_NO_REASON)

    lines.append(f"Target Local File: {draft.target_local_file}")

    if draft.related_tickers:
        lines.append(f"Related Tickers: {', '.join(draft.related_tickers)}")

    # Source
    lines.append("")
    lines.append(S.SECTION_SOURCE)
    lines.append(f"  - Source Description: {draft.source_description}")
    if draft.raw_source_reference:
        lines.append(f"  - Raw Source Reference: {draft.raw_source_reference}")
    if draft.notes:
        lines.append(f"  - Notes: {draft.notes[:_MAX_SCALAR_DISPLAY]}")

    # Review Checklist
    lines.append("")
    lines.append(S.SECTION_REVIEW_CHECKLIST)
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
        lines.append(S.SECTION_UNCERTAINTIES)
        for u in draft.uncertainties:
            lines.append(f"  - {u}")

    # Missing required fields detail
    if draft.missing_required_fields:
        lines.append("")
        lines.append(S.SECTION_MISSING_REQUIRED_FIELDS_WARNINGS)
        for f in draft.missing_required_fields:
            lines.append(f"  - {f}")

    # Extracted fields summary
    lines.append("")
    lines.append(S.SECTION_EXTRACTED_FIELDS)
    if draft.extracted_fields:
        lines.extend(_summarise_extracted_fields(draft.extracted_fields))
    else:
        lines.append("  (empty)")

    # Blocking issues
    issues = collect_snapshot_draft_review_issues(draft)
    lines.append("")
    lines.append(S.SECTION_BLOCKING_ISSUES)
    if issues:
        for issue in issues:
            lines.append(f"  - {issue}")
    else:
        lines.append("  None")

    # Research notes specific checklist
    if draft.snapshot_type == SnapshotType.RESEARCH_NOTES_SNAPSHOT:
        ef = draft.extracted_fields
        lines.append("")
        lines.append(S.SECTION_RESEARCH_NOTES_REVIEW)
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
    lines.append(S.SECTION_SAFETY_BOUNDARY)
    lines.append(S.SAFETY_REVIEW_READONLY)
    lines.append(S.SAFETY_REVIEW_NO_CONFIRM)
    lines.append(S.SAFETY_REVIEW_NO_WRITE)

    return "\n".join(lines)


def render_snapshot_draft_review_error(error_message: str, *, locale: str = "en") -> str:
    """Render an error summary for a failed snapshot review load."""
    S = _strings_for_locale(locale)
    lines = [
        S.HEADING_REVIEW,
        "",
        S.STATUS_INVALID,
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
    *,
    locale: str = "en",
) -> str:
    """Render a success summary after writing a confirmed draft copy."""
    S = _strings_for_locale(locale)
    lines = [
        S.HEADING_CONFIRMATION,
        "",
        S.STATUS_CONFIRMED,
    ]
    if already_confirmed:
        lines.append(S.NOTE_ALREADY_CONFIRMED)
    lines += [
        f"Input Draft: {input_path}",
        f"Output Draft: {output_path}",
        f"Snapshot Type: {snapshot_type}",
        "Confirmation Status: confirmed",
        "",
        S.SECTION_SAFETY_BOUNDARY,
        S.SAFETY_ORIGINAL_NOT_MODIFIED,
        S.SAFETY_NO_INPUT_FILES_CHANGED,
        S.SAFETY_CONFIRM_EXPORT_SEPARATE,
    ]
    return "\n".join(lines)


def render_snapshot_confirm_blocked(reason: str, *, locale: str = "en") -> str:
    """Render a blocked summary when confirmation cannot proceed."""
    S = _strings_for_locale(locale)
    lines = [
        S.HEADING_CONFIRMATION,
        "",
        S.STATUS_BLOCKED,
        f"Reason: {reason}",
    ]
    return "\n".join(lines)


def render_snapshot_confirm_error(error_message: str, *, locale: str = "en") -> str:
    """Render an error summary for a failed snapshot confirm load."""
    S = _strings_for_locale(locale)
    lines = [
        S.HEADING_CONFIRMATION,
        "",
        S.STATUS_INVALID,
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
    *,
    locale: str = "en",
) -> str:
    """Render a success summary after writing a rejected draft copy."""
    S = _strings_for_locale(locale)
    lines = [
        S.HEADING_REJECTION,
        "",
        S.STATUS_REJECTED,
    ]
    if already_rejected:
        lines.append(S.NOTE_ALREADY_REJECTED)
    elif was_confirmed:
        lines.append(S.NOTE_CONFIRMED_TO_REJECTED)
    lines += [
        f"Input Draft: {input_path}",
        f"Output Draft: {output_path}",
        f"Snapshot Type: {snapshot_type}",
        "Confirmation Status: rejected",
        "",
        S.SECTION_SAFETY_BOUNDARY,
        S.SAFETY_ORIGINAL_NOT_MODIFIED,
        S.SAFETY_NO_INPUT_FILES_CHANGED,
        S.SAFETY_REJECT_NOT_EXPORTABLE,
    ]
    return "\n".join(lines)


def render_snapshot_reject_blocked(reason: str, *, locale: str = "en") -> str:
    """Render a blocked summary when rejection cannot proceed."""
    S = _strings_for_locale(locale)
    lines = [
        S.HEADING_REJECTION,
        "",
        S.STATUS_BLOCKED,
        f"Reason: {reason}",
    ]
    return "\n".join(lines)


def render_snapshot_reject_error(error_message: str, *, locale: str = "en") -> str:
    """Render an error summary for a failed snapshot reject load."""
    S = _strings_for_locale(locale)
    lines = [
        S.HEADING_REJECTION,
        "",
        S.STATUS_INVALID,
        f"Error: {error_message}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Company facts export renderers
# ---------------------------------------------------------------------------

def render_company_facts_export_success(ticker: str, output_path: object, *, locale: str = "en") -> str:
    """Render a success summary after writing a company facts JSON file."""
    S = _strings_for_locale(locale)
    lines = [
        S.HEADING_COMPANY_FACTS_EXPORT,
        "",
        S.STATUS_WRITTEN,
        f"Ticker: {ticker}",
        f"Output File: {output_path}",
        "",
        S.SECTION_SAFETY_BOUNDARY,
        S.SAFETY_COMPANY_FACTS_ONLY,
        S.SAFETY_COMPANY_FACTS_NO_OTHER,
    ]
    return "\n".join(lines)


def render_company_facts_export_blocked(reason: str, *, locale: str = "en") -> str:
    """Render a blocked summary when company facts export cannot proceed."""
    S = _strings_for_locale(locale)
    lines = [
        S.HEADING_COMPANY_FACTS_EXPORT,
        "",
        S.STATUS_BLOCKED,
        f"Reason: {reason}",
    ]
    return "\n".join(lines)
