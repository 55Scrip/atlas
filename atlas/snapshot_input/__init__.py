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
from atlas.snapshot_input.render import (
    collect_snapshot_draft_review_issues,
    render_research_notes_export_blocked,
    render_research_notes_export_success,
    render_snapshot_draft_review,
    render_snapshot_draft_review_error,
    render_snapshot_draft_validation,
    render_snapshot_draft_validation_error,
)
from atlas.snapshot_input.export import (
    ResearchNotesExportResult,
    export_research_notes,
)

__all__ = [
    "ResearchNotesExportResult",
    "SnapshotConfidence",
    "SnapshotConfirmationStatus",
    "SnapshotDraft",
    "SnapshotType",
    "collect_snapshot_draft_review_issues",
    "export_research_notes",
    "load_snapshot_draft",
    "render_research_notes_export_blocked",
    "render_research_notes_export_success",
    "render_snapshot_draft_review",
    "render_snapshot_draft_review_error",
    "render_snapshot_draft_validation",
    "render_snapshot_draft_validation_error",
    "save_snapshot_draft",
    "validate_snapshot_draft",
]
