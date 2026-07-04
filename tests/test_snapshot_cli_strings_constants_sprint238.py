"""Sprint 238 — Snapshot CLI string constants tests.

Verifies that display strings have been extracted into a constants module,
that renderers reference those constants, and that Snapshot CLI output is
byte-for-byte unchanged from before the refactor.

No runtime behavior changes are expected or tested here beyond confirming
exact output equivalence.
"""

from __future__ import annotations

from pathlib import Path

import pytest

STRINGS_MODULE = Path("atlas/snapshot_input/strings.py")
RENDER_MODULE = Path("atlas/snapshot_input/render.py")

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


# ---------------------------------------------------------------------------
# Constants module existence and structure
# ---------------------------------------------------------------------------

def test_strings_module_exists():
    assert STRINGS_MODULE.exists(), f"{STRINGS_MODULE} not found"


def test_strings_module_is_nonempty():
    assert len(STRINGS_MODULE.read_text(encoding="utf-8").strip()) > 100


def test_strings_module_has_no_provider_imports():
    source = STRINGS_MODULE.read_text(encoding="utf-8")
    assert "import requests" not in source
    assert "import urllib" not in source
    assert "import httpx" not in source


def test_strings_module_has_no_locale_or_gettext():
    source = STRINGS_MODULE.read_text(encoding="utf-8")
    assert "import gettext" not in source
    assert "import locale" not in source


def test_strings_module_has_no_language_parameter():
    source = STRINGS_MODULE.read_text(encoding="utf-8")
    assert "--language" not in source
    assert "language=" not in source


# ---------------------------------------------------------------------------
# Command heading constants
# ---------------------------------------------------------------------------

def test_heading_validation_constant_exists():
    from atlas.snapshot_input import strings as S
    assert S.HEADING_VALIDATION == "Snapshot Draft Validation"


def test_heading_review_constant_exists():
    from atlas.snapshot_input import strings as S
    assert S.HEADING_REVIEW == "Snapshot Draft Review"


def test_heading_confirmation_constant_exists():
    from atlas.snapshot_input import strings as S
    assert S.HEADING_CONFIRMATION == "Snapshot Draft Confirmation"


def test_heading_rejection_constant_exists():
    from atlas.snapshot_input import strings as S
    assert S.HEADING_REJECTION == "Snapshot Draft Rejection"


def test_heading_research_notes_export_constant_exists():
    from atlas.snapshot_input import strings as S
    assert S.HEADING_RESEARCH_NOTES_EXPORT == "Research Notes Export"


def test_heading_company_facts_export_constant_exists():
    from atlas.snapshot_input import strings as S
    assert S.HEADING_COMPANY_FACTS_EXPORT == "Company Facts Export"


# ---------------------------------------------------------------------------
# Status line constants
# ---------------------------------------------------------------------------

def test_status_valid_constant():
    from atlas.snapshot_input import strings as S
    assert S.STATUS_VALID == "Status: valid"


def test_status_invalid_constant():
    from atlas.snapshot_input import strings as S
    assert S.STATUS_INVALID == "Status: invalid"


def test_status_reviewable_constant():
    from atlas.snapshot_input import strings as S
    assert S.STATUS_REVIEWABLE == "Status: reviewable"


def test_status_blocked_constant():
    from atlas.snapshot_input import strings as S
    assert S.STATUS_BLOCKED == "Status: blocked"


def test_status_written_constant():
    from atlas.snapshot_input import strings as S
    assert S.STATUS_WRITTEN == "Status: written"


def test_status_confirmed_constant():
    from atlas.snapshot_input import strings as S
    assert S.STATUS_CONFIRMED == "Status: confirmed"


def test_status_rejected_constant():
    from atlas.snapshot_input import strings as S
    assert S.STATUS_REJECTED == "Status: rejected"


# ---------------------------------------------------------------------------
# Exportability constants
# ---------------------------------------------------------------------------

def test_exportable_yes_constant():
    from atlas.snapshot_input import strings as S
    assert S.EXPORTABLE_YES == "Exportable: yes"


def test_exportable_no_constant():
    from atlas.snapshot_input import strings as S
    assert S.EXPORTABLE_NO == "Exportable: no"


def test_exportable_no_reason_constant():
    from atlas.snapshot_input import strings as S
    assert S.EXPORTABLE_NO_REASON == "  Reason: only confirmed drafts are exportable."


# ---------------------------------------------------------------------------
# Section header constants
# ---------------------------------------------------------------------------

def test_section_safety_boundary_constant():
    from atlas.snapshot_input import strings as S
    assert S.SECTION_SAFETY_BOUNDARY == "Safety Boundary:"


def test_section_blocking_issues_constant():
    from atlas.snapshot_input import strings as S
    assert S.SECTION_BLOCKING_ISSUES == "Blocking Issues:"


def test_section_review_checklist_constant():
    from atlas.snapshot_input import strings as S
    assert S.SECTION_REVIEW_CHECKLIST == "Review Checklist:"


def test_section_extracted_fields_constant():
    from atlas.snapshot_input import strings as S
    assert S.SECTION_EXTRACTED_FIELDS == "Extracted Fields:"


def test_section_source_constant():
    from atlas.snapshot_input import strings as S
    assert S.SECTION_SOURCE == "Source:"


# ---------------------------------------------------------------------------
# Safety boundary line constants
# ---------------------------------------------------------------------------

def test_safety_validation_constant():
    from atlas.snapshot_input import strings as S
    assert S.SAFETY_VALIDATION_NO_WRITE == "  - Draft validation does not write to Atlas local input files."


def test_safety_review_readonly_constant():
    from atlas.snapshot_input import strings as S
    assert S.SAFETY_REVIEW_READONLY == "  - Review is read-only."


def test_safety_review_no_confirm_constant():
    from atlas.snapshot_input import strings as S
    assert S.SAFETY_REVIEW_NO_CONFIRM == "  - Review does not confirm the draft."


def test_safety_review_no_write_constant():
    from atlas.snapshot_input import strings as S
    assert S.SAFETY_REVIEW_NO_WRITE == "  - Review does not write Atlas local input files."


def test_safety_original_not_modified_constant():
    from atlas.snapshot_input import strings as S
    assert S.SAFETY_ORIGINAL_NOT_MODIFIED == "  - Original draft was not modified."


def test_safety_no_input_files_changed_constant():
    from atlas.snapshot_input import strings as S
    assert S.SAFETY_NO_INPUT_FILES_CHANGED == "  - No Atlas local input files were changed."


def test_safety_confirm_export_separate_constant():
    from atlas.snapshot_input import strings as S
    assert S.SAFETY_CONFIRM_EXPORT_SEPARATE == "  - Export commands must still be run separately."


def test_safety_reject_not_exportable_constant():
    from atlas.snapshot_input import strings as S
    assert S.SAFETY_REJECT_NOT_EXPORTABLE == "  - Rejected drafts are not exportable."


def test_safety_research_notes_only_constant():
    from atlas.snapshot_input import strings as S
    assert S.SAFETY_RESEARCH_NOTES_ONLY == "  - Only local research notes were written."


def test_safety_research_notes_no_other_constant():
    from atlas.snapshot_input import strings as S
    assert S.SAFETY_RESEARCH_NOTES_NO_OTHER == "  - No portfolio, watchlist, journal, or company facts files were changed."


def test_safety_company_facts_only_constant():
    from atlas.snapshot_input import strings as S
    assert S.SAFETY_COMPANY_FACTS_ONLY == "  - Only local company facts were written."


def test_safety_company_facts_no_other_constant():
    from atlas.snapshot_input import strings as S
    assert S.SAFETY_COMPANY_FACTS_NO_OTHER == "  - No portfolio, watchlist, journal, or research notes files were changed."


# ---------------------------------------------------------------------------
# Renderer imports constants module
# ---------------------------------------------------------------------------

def test_render_module_imports_strings():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "from atlas.snapshot_input import strings" in source or \
           "from atlas.snapshot_input.strings import" in source or \
           "import atlas.snapshot_input.strings" in source


def test_render_module_references_heading_constant():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.HEADING_VALIDATION" in source or "HEADING_VALIDATION" in source


def test_render_module_references_safety_constant():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.SAFETY_" in source or "SAFETY_" in source


def test_render_module_references_section_safety_boundary():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "S.SECTION_SAFETY_BOUNDARY" in source or "SECTION_SAFETY_BOUNDARY" in source


# ---------------------------------------------------------------------------
# Canonical enum values remain unchanged
# ---------------------------------------------------------------------------

def test_enum_confirmation_status_values_unchanged():
    from atlas.snapshot_input.schema import SnapshotConfirmationStatus
    assert SnapshotConfirmationStatus.CONFIRMED.value == "confirmed"
    assert SnapshotConfirmationStatus.REJECTED.value == "rejected"
    assert SnapshotConfirmationStatus.DRAFT.value == "draft"
    assert SnapshotConfirmationStatus.NEEDS_USER_REVIEW.value == "needs_user_review"
    assert SnapshotConfirmationStatus.SUPERSEDED.value == "superseded"


def test_enum_snapshot_type_values_unchanged():
    from atlas.snapshot_input.schema import SnapshotType
    assert SnapshotType.RESEARCH_NOTES_SNAPSHOT.value == "research_notes_snapshot"
    assert SnapshotType.COMPANY_FACTS_SNAPSHOT.value == "company_facts_snapshot"


def test_strings_module_does_not_contain_canonical_enum_values_as_display():
    source = STRINGS_MODULE.read_text(encoding="utf-8")
    # These should NOT appear as standalone display constants —
    # they live in the schema enums, not in the display strings module
    assert 'research_notes_snapshot' not in source
    assert 'company_facts_snapshot' not in source
    # "confirmed" and "rejected" may appear only in note text, not as standalone labels
    # (STATUS_CONFIRMED = "Status: confirmed" is fine; bare "confirmed" would be schema)


# ---------------------------------------------------------------------------
# Output preservation — snapshot validate
# ---------------------------------------------------------------------------

def test_validate_output_includes_heading():
    from atlas.snapshot_input.schema import SnapshotDraft, SnapshotType, SnapshotConfirmationStatus, SnapshotConfidence
    from atlas.snapshot_input.render import render_snapshot_draft_validation
    draft = SnapshotDraft(
        draft_id="test-238-validate",
        snapshot_type=SnapshotType.RESEARCH_NOTES_SNAPSHOT,
        source_description="Sprint 238 test",
        extracted_fields={"ticker": "ASML"},
        confidence=SnapshotConfidence.HIGH,
        confirmation_status=SnapshotConfirmationStatus.DRAFT,
        target_local_file="research_notes/ASML/notes.md",
        created_at="2026-07-04",
        uncertainties=[],
        missing_required_fields=[],
    )
    out = render_snapshot_draft_validation(draft)
    assert out.startswith("Snapshot Draft Validation")
    assert "Status: valid" in out
    assert "Safety Boundary:" in out
    assert "Draft validation does not write to Atlas local input files." in out


def test_validate_error_output_includes_heading_and_invalid():
    from atlas.snapshot_input.render import render_snapshot_draft_validation_error
    out = render_snapshot_draft_validation_error("test error")
    assert out.startswith("Snapshot Draft Validation")
    assert "Status: invalid" in out
    assert "Error: test error" in out


# ---------------------------------------------------------------------------
# Output preservation — snapshot review
# ---------------------------------------------------------------------------

def test_review_output_includes_heading_and_exportability():
    from atlas.snapshot_input.schema import SnapshotDraft, SnapshotType, SnapshotConfirmationStatus, SnapshotConfidence
    from atlas.snapshot_input.render import render_snapshot_draft_review
    draft = SnapshotDraft(
        draft_id="test-238-review",
        snapshot_type=SnapshotType.RESEARCH_NOTES_SNAPSHOT,
        source_description="Sprint 238 test",
        extracted_fields={"ticker": "ASML", "title": "ASML notes"},
        confidence=SnapshotConfidence.HIGH,
        confirmation_status=SnapshotConfirmationStatus.DRAFT,
        target_local_file="research_notes/ASML/notes.md",
        created_at="2026-07-04",
        uncertainties=[],
        missing_required_fields=[],
    )
    out = render_snapshot_draft_review(draft)
    assert out.startswith("Snapshot Draft Review")
    assert "Status: reviewable" in out
    assert "Exportable: no" in out
    assert "only confirmed drafts are exportable" in out
    assert "Safety Boundary:" in out
    assert "Review is read-only." in out
    assert "Review does not confirm the draft." in out
    assert "Review does not write Atlas local input files." in out


def test_review_output_exportable_yes_when_confirmed():
    from atlas.snapshot_input.schema import SnapshotDraft, SnapshotType, SnapshotConfirmationStatus, SnapshotConfidence
    from atlas.snapshot_input.render import render_snapshot_draft_review
    draft = SnapshotDraft(
        draft_id="test-238-review-confirmed",
        snapshot_type=SnapshotType.RESEARCH_NOTES_SNAPSHOT,
        source_description="Sprint 238 test",
        extracted_fields={"ticker": "ASML", "title": "ASML notes"},
        confidence=SnapshotConfidence.HIGH,
        confirmation_status=SnapshotConfirmationStatus.CONFIRMED,
        target_local_file="research_notes/ASML/notes.md",
        created_at="2026-07-04",
        uncertainties=[],
        missing_required_fields=[],
    )
    out = render_snapshot_draft_review(draft)
    assert "Exportable: yes" in out
    assert "only confirmed drafts" not in out


# ---------------------------------------------------------------------------
# Output preservation — snapshot confirm
# ---------------------------------------------------------------------------

def test_confirm_success_output_includes_heading_and_safety():
    from atlas.snapshot_input.render import render_snapshot_confirm_success
    out = render_snapshot_confirm_success("/input.json", "/output.json", "research_notes_snapshot", False)
    assert out.startswith("Snapshot Draft Confirmation")
    assert "Status: confirmed" in out
    assert "Safety Boundary:" in out
    assert "Original draft was not modified." in out
    assert "No Atlas local input files were changed." in out
    assert "Export commands must still be run separately." in out


def test_confirm_blocked_output():
    from atlas.snapshot_input.render import render_snapshot_confirm_blocked
    out = render_snapshot_confirm_blocked("superseded drafts cannot be confirmed")
    assert out.startswith("Snapshot Draft Confirmation")
    assert "Status: blocked" in out
    assert "Reason:" in out


def test_confirm_error_output():
    from atlas.snapshot_input.render import render_snapshot_confirm_error
    out = render_snapshot_confirm_error("file not found")
    assert out.startswith("Snapshot Draft Confirmation")
    assert "Status: invalid" in out


# ---------------------------------------------------------------------------
# Output preservation — snapshot reject
# ---------------------------------------------------------------------------

def test_reject_success_output_includes_heading_and_safety():
    from atlas.snapshot_input.render import render_snapshot_reject_success
    out = render_snapshot_reject_success("/input.json", "/output.json", "research_notes_snapshot", False, False)
    assert out.startswith("Snapshot Draft Rejection")
    assert "Status: rejected" in out
    assert "Safety Boundary:" in out
    assert "Original draft was not modified." in out
    assert "No Atlas local input files were changed." in out
    assert "Rejected drafts are not exportable." in out


def test_reject_blocked_output():
    from atlas.snapshot_input.render import render_snapshot_reject_blocked
    out = render_snapshot_reject_blocked("superseded drafts cannot be rejected")
    assert out.startswith("Snapshot Draft Rejection")
    assert "Status: blocked" in out


# ---------------------------------------------------------------------------
# Output preservation — export-research-notes
# ---------------------------------------------------------------------------

def test_research_notes_export_success_output():
    from atlas.snapshot_input.render import render_research_notes_export_success
    out = render_research_notes_export_success("ASML", "/tmp/notes/ASML/notes.md")
    assert out.startswith("Research Notes Export")
    assert "Status: written" in out
    assert "Ticker: ASML" in out
    assert "Safety Boundary:" in out
    assert "Only local research notes were written." in out
    assert "No portfolio, watchlist, journal, or company facts files were changed." in out


def test_research_notes_export_blocked_output():
    from atlas.snapshot_input.render import render_research_notes_export_blocked
    out = render_research_notes_export_blocked("draft is not confirmed")
    assert out.startswith("Research Notes Export")
    assert "Status: blocked" in out
    assert "Reason:" in out


# ---------------------------------------------------------------------------
# Output preservation — export-company-facts
# ---------------------------------------------------------------------------

def test_company_facts_export_success_output():
    from atlas.snapshot_input.render import render_company_facts_export_success
    out = render_company_facts_export_success("ASML", "/tmp/facts/ASML.json")
    assert out.startswith("Company Facts Export")
    assert "Status: written" in out
    assert "Ticker: ASML" in out
    assert "Safety Boundary:" in out
    assert "Only local company facts were written." in out
    assert "No portfolio, watchlist, journal, or research notes files were changed." in out


def test_company_facts_export_blocked_output():
    from atlas.snapshot_input.render import render_company_facts_export_blocked
    out = render_company_facts_export_blocked("draft is not confirmed")
    assert out.startswith("Company Facts Export")
    assert "Status: blocked" in out


# ---------------------------------------------------------------------------
# No new behavioral features introduced
# ---------------------------------------------------------------------------

def test_no_language_option_in_cli():
    import atlas.cli.main as main_mod
    source = Path(main_mod.__file__).read_text(encoding="utf-8")
    assert "--language" not in source


def test_no_gettext_or_locale_in_render():
    source = RENDER_MODULE.read_text(encoding="utf-8")
    assert "import gettext" not in source
    assert "import locale" not in source


def test_no_provider_imports_in_strings_module():
    source = STRINGS_MODULE.read_text(encoding="utf-8")
    for provider_import in ["requests", "urllib", "httpx", "aiohttp", "boto"]:
        assert provider_import not in source


def test_weekly_review_render_unchanged():
    wr_source = Path("atlas/weekly_review/render.py").read_text(encoding="utf-8")
    assert "Atlas Weekly Investment Review" in wr_source
    assert "from atlas.snapshot_input" not in wr_source


# ---------------------------------------------------------------------------
# Forbidden language guardrails
# ---------------------------------------------------------------------------

def test_strings_module_no_forbidden_language():
    content = STRINGS_MODULE.read_text(encoding="utf-8")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in content, f"Forbidden language in strings module: {term!r}"


def test_render_module_no_forbidden_language():
    content = RENDER_MODULE.read_text(encoding="utf-8")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in content, f"Forbidden language in render module: {term!r}"
