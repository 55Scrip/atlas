"""Snapshot Draft confirmation logic for Atlas.

Loads a SnapshotDraft, checks blocking issues, and writes a new confirmed
copy to the requested output path. The original draft is never modified.

No OCR. No image parsing. No AI. No provider imports. No network calls.
No Atlas local input files are written by this module.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path

from atlas.snapshot_input.schema import (
    SnapshotConfirmationStatus,
    SnapshotDraft,
    save_snapshot_draft,
)
from atlas.snapshot_input.render import collect_snapshot_draft_review_issues


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SnapshotConfirmResult:
    """Result of a Snapshot Draft confirmation attempt.

    success         True if the confirmed copy was written.
    output_path     Path to the written confirmed draft (if success).
    already_confirmed
                    True if the input draft was already confirmed.
    reason          Human-readable reason on failure (empty on success).
    """

    success: bool
    output_path: Path | None
    already_confirmed: bool
    reason: str


# ---------------------------------------------------------------------------
# Blocking checks beyond the shared review rules
# ---------------------------------------------------------------------------

_TERMINAL_BLOCKED = {
    SnapshotConfirmationStatus.REJECTED,
    SnapshotConfirmationStatus.SUPERSEDED,
}


def _collect_confirm_blocks(draft: SnapshotDraft) -> str:
    """Return the first blocking reason for confirmation, or empty string."""
    # Hard blocks: rejected / superseded
    if draft.confirmation_status in _TERMINAL_BLOCKED:
        return (
            f"Draft is {draft.confirmation_status.value} and cannot be confirmed."
        )

    # Shared review blocking rules (unknown type, empty fields, unsafe ticker, …)
    review_issues = collect_snapshot_draft_review_issues(draft)
    # Filter out the "already terminal" issue — confirmed is allowed here
    actionable = [
        i for i in review_issues
        if "terminal state: confirmed" not in i
    ]
    if actionable:
        return actionable[0]

    return ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def confirm_snapshot_draft(
    draft: SnapshotDraft,
    output_path: Path,
    overwrite: bool = False,
) -> SnapshotConfirmResult:
    """Write a confirmed copy of *draft* to *output_path*.

    The original draft object and its source file are never modified.

    Parameters
    ----------
    draft:
        The loaded SnapshotDraft to confirm.
    output_path:
        Destination path for the confirmed draft JSON.
    overwrite:
        If False (default) and output_path already exists, return a failure
        result without writing. If True, overwrite the existing file.

    Returns
    -------
    SnapshotConfirmResult
    """
    # Check blocking issues
    block_reason = _collect_confirm_blocks(draft)
    if block_reason:
        return SnapshotConfirmResult(
            success=False,
            output_path=None,
            already_confirmed=False,
            reason=block_reason,
        )

    already_confirmed = draft.confirmation_status == SnapshotConfirmationStatus.CONFIRMED

    # Output collision guard
    if output_path.exists() and not overwrite:
        return SnapshotConfirmResult(
            success=False,
            output_path=None,
            already_confirmed=already_confirmed,
            reason=(
                f"Output file already exists: {output_path}. "
                "Use --overwrite to replace it."
            ),
        )

    # Build confirmed copy — copy the dict, set status to confirmed
    confirmed_dict = copy.deepcopy(draft.to_dict())
    confirmed_dict["confirmation_status"] = SnapshotConfirmationStatus.CONFIRMED.value
    confirmed_draft = SnapshotDraft.from_dict(confirmed_dict)

    try:
        save_snapshot_draft(output_path, confirmed_draft)
    except OSError as exc:
        return SnapshotConfirmResult(
            success=False,
            output_path=None,
            already_confirmed=already_confirmed,
            reason=f"Could not write output file: {exc}",
        )

    return SnapshotConfirmResult(
        success=True,
        output_path=output_path,
        already_confirmed=already_confirmed,
        reason="",
    )
