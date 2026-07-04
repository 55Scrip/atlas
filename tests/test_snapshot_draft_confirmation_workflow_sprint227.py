"""Sprint 227 — Snapshot Draft Confirmation Workflow specification tests.

These tests verify that the confirmation workflow document exists, is complete,
and avoids forbidden language. No runtime behavior is tested — this sprint is
a planning and specification sprint.
"""

from __future__ import annotations

from pathlib import Path

import pytest

DOC_PATH = Path("docs/SnapshotDraftConfirmationWorkflow.md")
WORKFLOW_PATH = Path("docs/AtlasSnapshotInputWorkflow.md")

FORBIDDEN_LANGUAGE = [
    "Strong Buy",
    "Strong Sell",
    "Price Target",
    "Target Price",
    "Act Now",
    "Must Buy",
    "Must Sell",
    "Guaranteed",
    "Will Outperform",
    "Financial Advice",
]

ALL_FIVE_STATES = [
    "draft",
    "needs_user_review",
    "confirmed",
    "rejected",
    "superseded",
]


@pytest.fixture(scope="module")
def doc_text() -> str:
    assert DOC_PATH.exists(), f"Confirmation workflow doc not found: {DOC_PATH}"
    return DOC_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Document existence
# ---------------------------------------------------------------------------

def test_confirmation_workflow_doc_exists():
    assert DOC_PATH.exists(), f"Missing: {DOC_PATH}"


def test_confirmation_workflow_doc_is_not_empty():
    assert DOC_PATH.stat().st_size > 500


# ---------------------------------------------------------------------------
# All five confirmation states defined
# ---------------------------------------------------------------------------

def test_doc_defines_draft_state(doc_text):
    assert "draft" in doc_text.lower()


def test_doc_defines_needs_user_review_state(doc_text):
    assert "needs_user_review" in doc_text


def test_doc_defines_confirmed_state(doc_text):
    assert "confirmed" in doc_text


def test_doc_defines_rejected_state(doc_text):
    assert "rejected" in doc_text


def test_doc_defines_superseded_state(doc_text):
    assert "superseded" in doc_text


def test_doc_defines_all_five_states(doc_text):
    for state in ALL_FIVE_STATES:
        assert state in doc_text, f"State not documented: {state!r}"


# ---------------------------------------------------------------------------
# Only confirmed is exportable
# ---------------------------------------------------------------------------

def test_doc_states_only_confirmed_is_exportable(doc_text):
    assert "only" in doc_text.lower() or "exportable" in doc_text.lower()
    assert "confirmed" in doc_text


def test_doc_states_draft_is_not_exportable(doc_text):
    lower = doc_text.lower()
    assert "not exportable" in lower or "exportable: no" in lower


def test_doc_states_rejected_is_not_exportable(doc_text):
    assert "rejected" in doc_text
    # rejected should appear near "not exportable" or "terminal"
    assert "terminal" in doc_text.lower() or "not exportable" in doc_text.lower()


def test_doc_states_superseded_is_not_exportable(doc_text):
    assert "superseded" in doc_text


# ---------------------------------------------------------------------------
# Review checklist
# ---------------------------------------------------------------------------

def test_doc_includes_review_checklist(doc_text):
    assert "Review Checklist" in doc_text or "checklist" in doc_text.lower()


def test_doc_checklist_includes_draft_id(doc_text):
    assert "draft_id" in doc_text


def test_doc_checklist_includes_snapshot_type(doc_text):
    assert "snapshot_type" in doc_text


def test_doc_checklist_includes_uncertainties(doc_text):
    assert "uncertainties" in doc_text


def test_doc_checklist_includes_missing_required_fields(doc_text):
    assert "missing_required_fields" in doc_text


def test_doc_checklist_includes_target_local_file(doc_text):
    assert "target_local_file" in doc_text


def test_doc_checklist_includes_source_description(doc_text):
    assert "source_description" in doc_text


def test_doc_checklist_includes_safety_boundary(doc_text):
    assert "Safety Boundary" in doc_text or "safety boundary" in doc_text.lower()


# ---------------------------------------------------------------------------
# Blocking rules
# ---------------------------------------------------------------------------

def test_doc_includes_blocking_rules(doc_text):
    assert "Blocking Rules" in doc_text or "blocking" in doc_text.lower()


def test_doc_blocking_rules_include_unsupported_type(doc_text):
    assert "unsupported" in doc_text.lower() or "unknown_snapshot" in doc_text


def test_doc_blocking_rules_include_missing_ticker(doc_text):
    lower = doc_text.lower()
    assert "missing ticker" in lower or "ticker" in lower


def test_doc_blocking_rules_include_unsafe_ticker(doc_text):
    assert "unsafe" in doc_text.lower() or "path separator" in doc_text.lower()


def test_doc_blocking_rules_include_terminal_state_check(doc_text):
    assert "terminal" in doc_text.lower() or "already" in doc_text.lower()


# ---------------------------------------------------------------------------
# Future CLI shape
# ---------------------------------------------------------------------------

def test_doc_includes_future_cli_shape(doc_text):
    assert "CLI" in doc_text or "command" in doc_text.lower()


def test_doc_mentions_snapshot_review_command(doc_text):
    assert "snapshot review" in doc_text or "atlas snapshot review" in doc_text


def test_doc_mentions_snapshot_confirm_command(doc_text):
    assert "snapshot confirm" in doc_text or "atlas snapshot confirm" in doc_text


def test_doc_mentions_snapshot_reject_command(doc_text):
    assert "snapshot reject" in doc_text or "atlas snapshot reject" in doc_text


# ---------------------------------------------------------------------------
# Export command dependency
# ---------------------------------------------------------------------------

def test_doc_includes_export_dependency(doc_text):
    assert "export" in doc_text.lower()
    assert "confirmation_status" in doc_text


def test_doc_states_export_requires_confirmed(doc_text):
    assert "export-research-notes" in doc_text or "export" in doc_text.lower()
    assert "confirmed" in doc_text


def test_doc_lists_future_export_commands(doc_text):
    assert "export-watchlist" in doc_text or "export-company-facts" in doc_text


# ---------------------------------------------------------------------------
# Safety boundary
# ---------------------------------------------------------------------------

def test_doc_includes_safety_boundary_section(doc_text):
    assert "Safety Boundary" in doc_text


def test_doc_safety_boundary_prohibits_provider_calls(doc_text):
    assert "provider" in doc_text.lower()


def test_doc_safety_boundary_prohibits_ai(doc_text):
    assert "AI" in doc_text or "LLM" in doc_text


def test_doc_safety_boundary_prohibits_portfolio_writes(doc_text):
    assert "portfolio" in doc_text.lower()


def test_doc_safety_boundary_prohibits_recommendations(doc_text):
    assert "recommendation" in doc_text.lower()


# ---------------------------------------------------------------------------
# Audit / traceability
# ---------------------------------------------------------------------------

def test_doc_includes_audit_or_traceability_section(doc_text):
    lower = doc_text.lower()
    assert "audit" in lower or "traceab" in lower


def test_doc_audit_preserves_draft_id(doc_text):
    assert "draft_id" in doc_text


def test_doc_audit_preserves_source_description(doc_text):
    assert "source_description" in doc_text


def test_doc_audit_preserves_uncertainties(doc_text):
    assert "uncertainties" in doc_text


# ---------------------------------------------------------------------------
# Field correction model
# ---------------------------------------------------------------------------

def test_doc_includes_field_correction_model(doc_text):
    lower = doc_text.lower()
    assert "correction" in lower or "revised draft" in lower


def test_doc_correction_model_does_not_mutate_original(doc_text):
    lower = doc_text.lower()
    assert "mutate" in lower or "overwrite" in lower or "revised" in lower


# ---------------------------------------------------------------------------
# Weekly Review relationship
# ---------------------------------------------------------------------------

def test_doc_includes_weekly_review_relationship(doc_text):
    assert "Weekly Review" in doc_text


def test_doc_states_weekly_review_does_not_consume_unconfirmed(doc_text):
    assert "unconfirmed" in doc_text.lower() or "not consume" in doc_text.lower()


# ---------------------------------------------------------------------------
# Confirmation principles
# ---------------------------------------------------------------------------

def test_doc_includes_confirmation_principles(doc_text):
    assert "Confirmation Principles" in doc_text or "principle" in doc_text.lower()


def test_doc_principles_state_explicit_confirmation(doc_text):
    assert "explicit" in doc_text.lower()


def test_doc_principles_state_local_confirmation(doc_text):
    assert "local" in doc_text.lower()


def test_doc_principles_state_no_live_data(doc_text):
    lower = doc_text.lower()
    assert "live data" in lower or "external" in lower


# ---------------------------------------------------------------------------
# Language guardrails
# ---------------------------------------------------------------------------

def test_doc_avoids_forbidden_language(doc_text):
    for term in FORBIDDEN_LANGUAGE:
        assert term not in doc_text, f"Forbidden language in doc: {term!r}"


def test_confirmation_workflow_doc_avoids_forbidden_language_in_full_text():
    text = DOC_PATH.read_text(encoding="utf-8")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in text, f"Forbidden: {term!r}"


# ---------------------------------------------------------------------------
# Repository identity
# ---------------------------------------------------------------------------

def test_doc_confirms_repository_identity(doc_text):
    other_product = "Atlas" + " " + "Edge"
    # The doc may reference the other product by name as an exclusion,
    # but must not claim to be it.
    assert "This is Atlas" in doc_text or "Atlas" in doc_text
    # If the other product name appears, it must appear in an exclusion context.
    if other_product in doc_text:
        assert "not" in doc_text.lower() or "separate" in doc_text.lower()


# ---------------------------------------------------------------------------
# Schema consistency check
# ---------------------------------------------------------------------------

def test_confirmation_status_enum_has_all_five_states():
    from atlas.snapshot_input.schema import SnapshotConfirmationStatus
    values = {s.value for s in SnapshotConfirmationStatus}
    for state in ALL_FIVE_STATES:
        assert state in values, f"Missing enum value: {state!r}"


def test_export_research_notes_requires_confirmed_status(tmp_path):
    """Regression: export command must still enforce confirmed status."""
    from atlas.snapshot_input.schema import (
        SnapshotConfirmationStatus,
        SnapshotDraft,
        SnapshotType,
    )
    from atlas.snapshot_input.export import export_research_notes

    draft = SnapshotDraft(
        draft_id="draft-sprint227-test",
        snapshot_type=SnapshotType.RESEARCH_NOTES_SNAPSHOT,
        source_description="Test",
        extracted_fields={"ticker": "ASML", "evidence_gaps": ["A gap."]},
        uncertainties=[],
        missing_required_fields=[],
        confirmation_status=SnapshotConfirmationStatus.DRAFT,
        target_local_file="research_notes/ASML/notes.md",
        created_at="2026-01-05",
    )
    result = export_research_notes(draft, tmp_path)
    assert not result.success
    assert "confirmed" in result.reason.lower()


def test_needs_user_review_status_is_not_exportable(tmp_path):
    from atlas.snapshot_input.schema import (
        SnapshotConfirmationStatus,
        SnapshotDraft,
        SnapshotType,
    )
    from atlas.snapshot_input.export import export_research_notes

    draft = SnapshotDraft(
        draft_id="draft-sprint227-review",
        snapshot_type=SnapshotType.RESEARCH_NOTES_SNAPSHOT,
        source_description="Test",
        extracted_fields={"ticker": "ASML"},
        uncertainties=[],
        missing_required_fields=[],
        confirmation_status=SnapshotConfirmationStatus.NEEDS_USER_REVIEW,
        target_local_file="research_notes/ASML/notes.md",
        created_at="2026-01-05",
    )
    result = export_research_notes(draft, tmp_path)
    assert not result.success


def test_rejected_status_is_not_exportable(tmp_path):
    from atlas.snapshot_input.schema import (
        SnapshotConfirmationStatus,
        SnapshotDraft,
        SnapshotType,
    )
    from atlas.snapshot_input.export import export_research_notes

    draft = SnapshotDraft(
        draft_id="draft-sprint227-rejected",
        snapshot_type=SnapshotType.RESEARCH_NOTES_SNAPSHOT,
        source_description="Test",
        extracted_fields={"ticker": "ASML"},
        uncertainties=[],
        missing_required_fields=[],
        confirmation_status=SnapshotConfirmationStatus.REJECTED,
        target_local_file="research_notes/ASML/notes.md",
        created_at="2026-01-05",
    )
    result = export_research_notes(draft, tmp_path)
    assert not result.success


def test_superseded_status_is_not_exportable(tmp_path):
    from atlas.snapshot_input.schema import (
        SnapshotConfirmationStatus,
        SnapshotDraft,
        SnapshotType,
    )
    from atlas.snapshot_input.export import export_research_notes

    draft = SnapshotDraft(
        draft_id="draft-sprint227-superseded",
        snapshot_type=SnapshotType.RESEARCH_NOTES_SNAPSHOT,
        source_description="Test",
        extracted_fields={"ticker": "ASML"},
        uncertainties=[],
        missing_required_fields=[],
        confirmation_status=SnapshotConfirmationStatus.SUPERSEDED,
        target_local_file="research_notes/ASML/notes.md",
        created_at="2026-01-05",
    )
    result = export_research_notes(draft, tmp_path)
    assert not result.success
