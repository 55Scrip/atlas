"""Snapshot Draft rejection logic for Atlas.

Loads a SnapshotDraft and writes a new rejected copy to the requested output
path. The original draft is never modified.

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


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SnapshotRejectResult:
    """Result of a Snapshot Draft rejection attempt.

    success             True if the rejected copy was written.
    output_path         Path to the written rejected draft (if success).
    already_rejected    True if the input draft was already rejected.
    was_confirmed       True if the input draft was confirmed before rejection.
    reason              Human-readable reason on failure (empty on success).
    """

    success: bool
    output_path: Path | None
    already_rejected: bool
    was_confirmed: bool
    reason: str


# ---------------------------------------------------------------------------
# Blocking checks
# ---------------------------------------------------------------------------

_HARD_BLOCKED = {
    SnapshotConfirmationStatus.SUPERSEDED,
}


def _collect_reject_block(draft: SnapshotDraft) -> str:
    """Return the first blocking reason for rejection, or empty string."""
    if draft.confirmation_status in _HARD_BLOCKED:
        return (
            f"Draft is {draft.confirmation_status.value} and cannot be rejected. "
            "Superseded drafts were replaced by a newer draft and should not be "
            "changed independently."
        )
    return ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def reject_snapshot_draft(
    draft: SnapshotDraft,
    output_path: Path,
    overwrite: bool = False,
) -> SnapshotRejectResult:
    """Write a rejected copy of *draft* to *output_path*.

    The original draft object and its source file are never modified.

    Parameters
    ----------
    draft:
        The loaded SnapshotDraft to reject.
    output_path:
        Destination path for the rejected draft JSON.
    overwrite:
        If False (default) and output_path already exists, return a failure
        result without writing. If True, overwrite the existing file.

    Returns
    -------
    SnapshotRejectResult
    """
    block_reason = _collect_reject_block(draft)
    if block_reason:
        return SnapshotRejectResult(
            success=False,
            output_path=None,
            already_rejected=False,
            was_confirmed=False,
            reason=block_reason,
        )

    already_rejected = draft.confirmation_status == SnapshotConfirmationStatus.REJECTED
    was_confirmed = draft.confirmation_status == SnapshotConfirmationStatus.CONFIRMED

    if output_path.exists() and not overwrite:
        return SnapshotRejectResult(
            success=False,
            output_path=None,
            already_rejected=already_rejected,
            was_confirmed=was_confirmed,
            reason=(
                f"Output file already exists: {output_path}. "
                "Use --overwrite to replace it."
            ),
        )

    rejected_dict = copy.deepcopy(draft.to_dict())
    rejected_dict["confirmation_status"] = SnapshotConfirmationStatus.REJECTED.value
    rejected_draft = SnapshotDraft.from_dict(rejected_dict)

    try:
        save_snapshot_draft(output_path, rejected_draft)
    except OSError as exc:
        return SnapshotRejectResult(
            success=False,
            output_path=None,
            already_rejected=already_rejected,
            was_confirmed=was_confirmed,
            reason=f"Could not write output file: {exc}",
        )

    return SnapshotRejectResult(
        success=True,
        output_path=output_path,
        already_rejected=already_rejected,
        was_confirmed=was_confirmed,
        reason="",
    )
