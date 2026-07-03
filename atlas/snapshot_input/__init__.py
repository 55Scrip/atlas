"""Atlas Snapshot Input — upstream input creation layer.

This package defines the Snapshot Draft schema used to represent
user-supplied information before it is confirmed and written into
Atlas local input files (portfolio.json, watchlist.json, etc.).

No OCR. No image parsing. No AI. No provider imports. No network calls.

See docs/AtlasSnapshotInputWorkflow.md for the full workflow specification.
"""

from atlas.snapshot_input.schema import (
    SnapshotConfidence,
    SnapshotConfirmationStatus,
    SnapshotDraft,
    SnapshotType,
    load_snapshot_draft,
    save_snapshot_draft,
    validate_snapshot_draft,
)

__all__ = [
    "SnapshotConfidence",
    "SnapshotConfirmationStatus",
    "SnapshotDraft",
    "SnapshotType",
    "load_snapshot_draft",
    "save_snapshot_draft",
    "validate_snapshot_draft",
]
