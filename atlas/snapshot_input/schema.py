"""Snapshot Draft schema for Atlas Snapshot Input.

A Snapshot Draft is a temporary structured interpretation of user-supplied
information — pasted text, manual entry, exported table, or future screenshot
extraction — that is not committed to any Atlas local input file until the user
confirms it.

This module defines:
  - SnapshotType — the eight supported snapshot types
  - SnapshotConfirmationStatus — the five confirmation states
  - SnapshotConfidence — confidence levels (descriptive only)
  - SnapshotDraft — the full draft schema
  - validate_snapshot_draft — validation helper
  - Serialization helpers: to_dict, from_dict, to_json, from_json
  - File helpers: load_snapshot_draft, save_snapshot_draft

No OCR. No image parsing. No AI. No provider imports. No network calls.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SnapshotType(str, Enum):
    """Supported snapshot input types.

    Values match the type identifiers defined in AtlasSnapshotInputWorkflow.md.
    """

    PORTFOLIO_SNAPSHOT = "portfolio_snapshot"
    WATCHLIST_SNAPSHOT = "watchlist_snapshot"
    OPEN_ORDERS_SNAPSHOT = "open_orders_snapshot"
    NEWS_SNAPSHOT = "news_snapshot"
    EXTERNAL_ANALYSIS_SNAPSHOT = "external_analysis_snapshot"
    RESEARCH_NOTES_SNAPSHOT = "research_notes_snapshot"
    COMPANY_FACTS_SNAPSHOT = "company_facts_snapshot"
    UNKNOWN_SNAPSHOT = "unknown_snapshot"


class SnapshotConfirmationStatus(str, Enum):
    """Confirmation states for a Snapshot Draft.

    Only confirmed drafts may be converted into Atlas local input files.
    """

    DRAFT = "draft"
    NEEDS_USER_REVIEW = "needs_user_review"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class SnapshotConfidence(str, Enum):
    """Confidence level for a Snapshot Draft classification or field.

    Confidence is descriptive only. High confidence does not bypass confirmation
    for non-trivial drafts. Low confidence must make uncertainty visible.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Snapshot Draft
# ---------------------------------------------------------------------------


@dataclass
class SnapshotDraft:
    """A structured interpretation of user-supplied information.

    A draft is not authoritative. It must be confirmed by the user before any
    Atlas local input file is updated. Uncertainties and missing required fields
    must be displayed before confirmation is offered.

    Required fields
    ---------------
    draft_id            Caller-supplied identifier. Non-empty string.
    snapshot_type       One of the SnapshotType values.
    source_description  Human-readable description of the source material.
    extracted_fields    Dict of structured fields extracted from the source.
    uncertainties       List of uncertainty strings (may be empty).
    missing_required_fields
                        List of required fields not confidently extracted.
    confirmation_status One of the SnapshotConfirmationStatus values.
    target_local_file   Intended Atlas local input path (e.g. portfolio.json).
    created_at          ISO 8601 date/time string supplied by the caller.

    Optional fields
    ---------------
    confidence          Descriptive confidence level (default: unknown).
    related_tickers     List of tickers (uppercased).
    raw_source_reference
                        Path or description of the original source.
                        Must not contain raw screenshot binary data.
    notes               Safe free-text notes about this draft.
    """

    # Required
    draft_id: str
    snapshot_type: SnapshotType
    source_description: str
    extracted_fields: dict[str, Any]
    uncertainties: list[str]
    missing_required_fields: list[str]
    confirmation_status: SnapshotConfirmationStatus
    target_local_file: str
    created_at: str

    # Optional
    confidence: SnapshotConfidence = SnapshotConfidence.UNKNOWN
    related_tickers: list[str] = field(default_factory=list)
    raw_source_reference: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        # Normalize related_tickers to uppercase
        self.related_tickers = [t.strip().upper() for t in self.related_tickers if t.strip()]
        validate_snapshot_draft(self)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict representation of this draft."""
        return {
            "draft_id": self.draft_id,
            "snapshot_type": self.snapshot_type.value,
            "source_description": self.source_description,
            "extracted_fields": self.extracted_fields,
            "uncertainties": list(self.uncertainties),
            "missing_required_fields": list(self.missing_required_fields),
            "confirmation_status": self.confirmation_status.value,
            "target_local_file": self.target_local_file,
            "created_at": self.created_at,
            "confidence": self.confidence.value,
            "related_tickers": list(self.related_tickers),
            "raw_source_reference": self.raw_source_reference,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SnapshotDraft":
        """Construct a SnapshotDraft from a dict (e.g. loaded from JSON).

        Raises ValueError if required fields are missing or invalid.
        """
        try:
            snapshot_type = SnapshotType(data["snapshot_type"])
        except (KeyError, ValueError) as exc:
            raise ValueError(
                f"Invalid or missing 'snapshot_type': {data.get('snapshot_type')!r}"
            ) from exc

        try:
            confirmation_status = SnapshotConfirmationStatus(data["confirmation_status"])
        except (KeyError, ValueError) as exc:
            raise ValueError(
                f"Invalid or missing 'confirmation_status': {data.get('confirmation_status')!r}"
            ) from exc

        confidence_raw = data.get("confidence", SnapshotConfidence.UNKNOWN.value)
        try:
            confidence = SnapshotConfidence(confidence_raw)
        except ValueError:
            confidence = SnapshotConfidence.UNKNOWN

        return cls(
            draft_id=data.get("draft_id", ""),
            snapshot_type=snapshot_type,
            source_description=data.get("source_description", ""),
            extracted_fields=data.get("extracted_fields", {}),
            uncertainties=list(data.get("uncertainties", [])),
            missing_required_fields=list(data.get("missing_required_fields", [])),
            confirmation_status=confirmation_status,
            target_local_file=data.get("target_local_file", ""),
            created_at=data.get("created_at", ""),
            confidence=confidence,
            related_tickers=list(data.get("related_tickers", [])),
            raw_source_reference=data.get("raw_source_reference", ""),
            notes=data.get("notes", ""),
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize this draft to a deterministic JSON string."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "SnapshotDraft":
        """Construct a SnapshotDraft from a JSON string."""
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("Snapshot draft JSON must be a JSON object.")
        return cls.from_dict(data)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_snapshot_draft(draft: SnapshotDraft) -> None:
    """Validate a SnapshotDraft and raise ValueError on the first violation.

    Called automatically by SnapshotDraft.__post_init__; can also be called
    explicitly after mutating a draft's fields.
    """
    if not draft.draft_id or not draft.draft_id.strip():
        raise ValueError("SnapshotDraft.draft_id must be a non-empty string.")

    if not isinstance(draft.snapshot_type, SnapshotType):
        raise ValueError(
            f"SnapshotDraft.snapshot_type must be a SnapshotType member, "
            f"got {draft.snapshot_type!r}."
        )

    if not draft.source_description or not draft.source_description.strip():
        raise ValueError("SnapshotDraft.source_description must be a non-empty string.")

    if not isinstance(draft.extracted_fields, dict):
        raise ValueError(
            "SnapshotDraft.extracted_fields must be a dict (mapping), "
            f"got {type(draft.extracted_fields).__name__}."
        )

    if not isinstance(draft.uncertainties, list):
        raise ValueError("SnapshotDraft.uncertainties must be a list.")

    if not isinstance(draft.missing_required_fields, list):
        raise ValueError("SnapshotDraft.missing_required_fields must be a list.")

    if not isinstance(draft.confirmation_status, SnapshotConfirmationStatus):
        raise ValueError(
            f"SnapshotDraft.confirmation_status must be a SnapshotConfirmationStatus member, "
            f"got {draft.confirmation_status!r}."
        )

    if not draft.target_local_file or not draft.target_local_file.strip():
        raise ValueError("SnapshotDraft.target_local_file must be a non-empty string.")

    if not draft.created_at or not draft.created_at.strip():
        raise ValueError("SnapshotDraft.created_at must be a non-empty string.")


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------


def load_snapshot_draft(path: Path) -> SnapshotDraft:
    """Load and validate a SnapshotDraft from a local JSON file.

    Raises ValueError on validation errors. Raises OSError if the file cannot
    be read. Does not make network calls or provider lookups.
    """
    text = path.read_text(encoding="utf-8")
    return SnapshotDraft.from_json(text)


def save_snapshot_draft(path: Path, draft: SnapshotDraft) -> None:
    """Write a SnapshotDraft to a local JSON file.

    Creates parent directories if needed. Writes deterministic, sort-keyed JSON.
    Does not make network calls or provider lookups.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(draft.to_json(), encoding="utf-8")
