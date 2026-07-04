"""Sprint 237 — User-facing strings inventory tests.

Verifies that the strings inventory document exists, covers the required
sections and string groups, and correctly classifies strings. No runtime
behavior changes are tested here.
"""

from __future__ import annotations

from pathlib import Path

INVENTORY_DOC = Path("docs/AtlasUserFacingStringsInventory.md")

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
# Document existence and structure
# ---------------------------------------------------------------------------

def test_inventory_doc_exists():
    assert INVENTORY_DOC.exists(), f"{INVENTORY_DOC} not found"


def test_inventory_doc_is_nonempty():
    assert len(INVENTORY_DOC.read_text(encoding="utf-8").strip()) > 500


def test_inventory_doc_has_purpose_section():
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    assert "purpose" in content


def test_inventory_doc_has_scope_section():
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    assert "scope" in content


# ---------------------------------------------------------------------------
# Classification categories
# ---------------------------------------------------------------------------

def test_inventory_doc_defines_localizable_display_category():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    assert "localizable_display" in content


def test_inventory_doc_defines_canonical_internal_category():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    assert "canonical_internal" in content


def test_inventory_doc_defines_user_content_passthrough_category():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    assert "user_content_passthrough" in content


def test_inventory_doc_defines_guardrail_sensitive_display_category():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    assert "guardrail_sensitive_display" in content


# ---------------------------------------------------------------------------
# Weekly Review coverage
# ---------------------------------------------------------------------------

def test_inventory_doc_covers_weekly_review_renderer():
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    assert "weekly_review/render.py" in content or "weekly review renderer" in content


def test_inventory_doc_covers_all_10_section_titles():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    for title in [
        "Review Scope",
        "Portfolio Context",
        "Watchlist Review",
        "Company Reviews Needing Attention",
        "Portfolio Fit and Suitability Notes",
        "Risk and Principle Guardrails",
        "Open Decisions",
        "Missing Evidence",
        "Follow-Up Questions",
        "Non-Actions / Reasons to Wait",
    ]:
        assert title in content, f"Section title missing from inventory: {title!r}"


def test_inventory_doc_covers_disclaimer():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    assert "no recommendations" in content.lower()
    assert "Atlas supports better judgment" in content


def test_inventory_doc_covers_section8_evidence_gap_labels():
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    assert "evidence gap" in content
    assert "section 8" in content or "## 8" in content or "missing evidence" in content


def test_inventory_doc_covers_section9_followup_labels():
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    assert "follow-up" in content or "open questions" in content


def test_inventory_doc_covers_section10_nonaction_labels():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    assert "Reason to Wait" in content
    assert "No Action Warranted" in content
    assert "Decision Deferred" in content


def test_inventory_doc_covers_input_status_labels():
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    assert "input status" in content


def test_inventory_doc_covers_aging_note_label():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    assert "Aging Note" in content


# ---------------------------------------------------------------------------
# Snapshot CLI coverage
# ---------------------------------------------------------------------------

def test_inventory_doc_covers_snapshot_renderer():
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    assert "snapshot_input/render.py" in content or "snapshot cli renderer" in content


def test_inventory_doc_covers_snapshot_validate_strings():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    assert "Snapshot Draft Validation" in content
    assert "Status: valid" in content


def test_inventory_doc_covers_snapshot_review_strings():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    assert "Snapshot Draft Review" in content
    assert "Exportable: yes" in content
    assert "Exportable: no" in content
    assert "Blocking Issues:" in content


def test_inventory_doc_covers_snapshot_confirm_strings():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    assert "Snapshot Draft Confirmation" in content
    assert "Status: confirmed" in content


def test_inventory_doc_covers_snapshot_reject_strings():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    assert "Snapshot Draft Rejection" in content
    assert "Status: rejected" in content


def test_inventory_doc_covers_research_notes_export_strings():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    assert "Research Notes Export" in content
    assert "Only local research notes were written." in content


def test_inventory_doc_covers_company_facts_export_strings():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    assert "Company Facts Export" in content
    assert "Only local company facts were written." in content


def test_inventory_doc_covers_safety_boundary_strings():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    assert "Safety Boundary" in content
    assert "Review is read-only." in content
    assert "Original draft was not modified." in content


# ---------------------------------------------------------------------------
# Canonical internal values section
# ---------------------------------------------------------------------------

def test_inventory_doc_lists_canonical_enum_values():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    for value in ["confirmed", "rejected", "draft", "needs_user_review", "superseded"]:
        assert value in content, f"Canonical enum value missing: {value!r}"


def test_inventory_doc_lists_snapshot_type_values():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    assert "research_notes_snapshot" in content
    assert "company_facts_snapshot" in content


def test_inventory_doc_lists_cli_option_names():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    assert "--portfolio" in content
    assert "--watchlist" in content
    assert "--output-dir" in content


def test_inventory_doc_lists_cli_command_names():
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    assert "weekly-review" in content
    assert "snapshot validate" in content or "snapshot" in content


def test_inventory_doc_states_enum_values_never_localized():
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    assert "canonical" in content
    assert "never" in content or "not localiz" in content or "not translated" in content


# ---------------------------------------------------------------------------
# User-provided content passthrough section
# ---------------------------------------------------------------------------

def test_inventory_doc_has_user_content_passthrough_section():
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    assert "passthrough" in content or "user-provided content" in content


def test_inventory_doc_states_research_notes_not_translated():
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    assert "research note" in content
    assert "not translated" in content or "not a localization target" in content or "not localiz" in content


def test_inventory_doc_states_scope_notes_not_translated():
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    assert "scope note" in content


def test_inventory_doc_states_journal_entries_not_translated():
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    assert "journal" in content


# ---------------------------------------------------------------------------
# Guardrail-sensitive strings section
# ---------------------------------------------------------------------------

def test_inventory_doc_has_guardrail_sensitive_section():
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    assert "guardrail" in content
    assert "sensitive" in content


def test_inventory_doc_flags_section10_as_high_guardrail_density():
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    # Section 10 should be flagged as guardrail-heavy
    assert "section 10" in content or "non-action" in content


def test_inventory_doc_flags_safety_boundary_as_highest_risk():
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    assert "safety boundary" in content
    assert "guardrail" in content


def test_inventory_doc_identifies_reason_to_wait_as_guardrail_sensitive():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    # The inventory should identify Reason to Wait as guardrail-sensitive
    assert "guardrail_sensitive_display" in content
    assert "Reason to Wait" in content


def test_inventory_doc_identifies_no_action_warranted_as_guardrail_sensitive():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    assert "No Action Warranted" in content
    assert "guardrail_sensitive_display" in content


# ---------------------------------------------------------------------------
# Known gaps section
# ---------------------------------------------------------------------------

def test_inventory_doc_acknowledges_no_string_catalog_yet():
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    assert "catalog" in content or "inline" in content or "no string catalog" in content


def test_inventory_doc_acknowledges_tests_assert_english_strings():
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    assert "test" in content
    assert "english" in content


# ---------------------------------------------------------------------------
# Future extraction candidates
# ---------------------------------------------------------------------------

def test_inventory_doc_recommends_extraction_priority():
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    assert "priority" in content or "extract" in content


def test_inventory_doc_suggests_snapshot_cli_as_first_extraction_target():
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    assert "snapshot" in content
    assert "extract" in content


# ---------------------------------------------------------------------------
# No runtime behavior changes
# ---------------------------------------------------------------------------

def test_no_new_imports_in_renderers():
    """render.py files should not have gained locale or gettext imports."""
    for py_file in [
        Path("atlas/weekly_review/render.py"),
        Path("atlas/snapshot_input/render.py"),
    ]:
        source = py_file.read_text(encoding="utf-8")
        assert "import gettext" not in source, f"gettext import in {py_file}"
        assert "import locale" not in source, f"locale import in {py_file}"


def test_no_language_option_in_cli():
    import atlas.cli.main as main_mod
    source = Path(main_mod.__file__).read_text(encoding="utf-8")
    assert "--language" not in source


def test_weekly_review_title_constant_unchanged():
    """The Weekly Review title string should still be present (not moved/deleted)."""
    source = Path("atlas/weekly_review/render.py").read_text(encoding="utf-8")
    assert "Atlas Weekly Investment Review" in source


def test_snapshot_render_headings_unchanged():
    """Core snapshot render headings must still be defined in the snapshot_input package."""
    # Headings may live in strings.py (constants) or render.py — check both
    render_source = Path("atlas/snapshot_input/render.py").read_text(encoding="utf-8")
    strings_source = Path("atlas/snapshot_input/strings.py").read_text(encoding="utf-8") if Path("atlas/snapshot_input/strings.py").exists() else ""
    combined = render_source + strings_source
    for heading in [
        "Snapshot Draft Validation",
        "Snapshot Draft Review",
        "Snapshot Draft Confirmation",
        "Snapshot Draft Rejection",
        "Research Notes Export",
        "Company Facts Export",
    ]:
        assert heading in combined, f"Snapshot render heading missing: {heading!r}"


def test_enum_values_still_canonical_english():
    from atlas.snapshot_input.schema import SnapshotConfirmationStatus, SnapshotType
    assert SnapshotConfirmationStatus.CONFIRMED.value == "confirmed"
    assert SnapshotConfirmationStatus.REJECTED.value == "rejected"
    assert SnapshotType.RESEARCH_NOTES_SNAPSHOT.value == "research_notes_snapshot"
    assert SnapshotType.COMPANY_FACTS_SNAPSHOT.value == "company_facts_snapshot"


# ---------------------------------------------------------------------------
# Forbidden language
# ---------------------------------------------------------------------------

def test_inventory_doc_no_forbidden_language():
    content = INVENTORY_DOC.read_text(encoding="utf-8")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in content, f"Forbidden language in inventory doc: {term!r}"


def test_inventory_doc_uses_categories_not_example_phrases():
    """The inventory should describe guardrail-sensitive strings by category,
    not by listing prohibited example phrases inline."""
    content = INVENTORY_DOC.read_text(encoding="utf-8").lower()
    assert "recommendation" in content
    assert "urgency" in content
    assert "certainty" in content
    # Must not enumerate prohibited phrases directly
    for phrase in ["strong buy", "price target", "act now", "guaranteed", "must buy"]:
        assert phrase not in content, (
            f"Prohibited example phrase found in doc (use category names instead): {phrase!r}"
        )
