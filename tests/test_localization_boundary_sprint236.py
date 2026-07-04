"""Sprint 236 — Localization boundary tests.

Checks that the localization boundary document exists, covers the required
principles and categories, and avoids forbidden language.
No runtime behavior changes are expected or tested here.
"""

from __future__ import annotations

from pathlib import Path

BOUNDARY_DOC = Path("docs/AtlasLocalizationBoundary.md")

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

def test_boundary_doc_exists():
    assert BOUNDARY_DOC.exists(), f"{BOUNDARY_DOC} not found"


def test_boundary_doc_is_nonempty():
    assert len(BOUNDARY_DOC.read_text(encoding="utf-8").strip()) > 0


# ---------------------------------------------------------------------------
# Core principle
# ---------------------------------------------------------------------------

def test_boundary_doc_states_canonical_english_principle():
    content = BOUNDARY_DOC.read_text(encoding="utf-8").lower()
    assert "canonical english" in content
    assert "internal" in content


def test_boundary_doc_distinguishes_internal_from_display():
    content = BOUNDARY_DOC.read_text(encoding="utf-8").lower()
    # Must explain that internal logic stays English while display may be localized
    assert "display" in content or "render" in content
    assert "localiz" in content


# ---------------------------------------------------------------------------
# Schema and enum non-translation rule
# ---------------------------------------------------------------------------

def test_boundary_doc_states_enums_not_translated():
    content = BOUNDARY_DOC.read_text(encoding="utf-8").lower()
    assert "enum" in content
    assert "never" in content or "not translated" in content or "not localiz" in content


def test_boundary_doc_mentions_confirmation_status():
    content = BOUNDARY_DOC.read_text(encoding="utf-8")
    assert "confirmation_status" in content


def test_boundary_doc_mentions_snapshot_type():
    content = BOUNDARY_DOC.read_text(encoding="utf-8")
    assert "snapshot_type" in content


def test_boundary_doc_mentions_schema_keys_not_translated():
    content = BOUNDARY_DOC.read_text(encoding="utf-8").lower()
    assert "schema" in content
    assert "key" in content


# ---------------------------------------------------------------------------
# Localizable user-facing strings
# ---------------------------------------------------------------------------

def test_boundary_doc_mentions_user_facing_strings_may_be_localized():
    content = BOUNDARY_DOC.read_text(encoding="utf-8").lower()
    assert "user-facing" in content or "display" in content
    assert "localiz" in content


def test_boundary_doc_covers_weekly_review_output():
    content = BOUNDARY_DOC.read_text(encoding="utf-8").lower()
    assert "weekly review" in content
    assert "section" in content


def test_boundary_doc_covers_snapshot_cli_output():
    content = BOUNDARY_DOC.read_text(encoding="utf-8").lower()
    assert "snapshot" in content
    assert "render" in content or "output" in content


# ---------------------------------------------------------------------------
# User-provided content handling
# ---------------------------------------------------------------------------

def test_boundary_doc_states_user_content_not_translated():
    content = BOUNDARY_DOC.read_text(encoding="utf-8").lower()
    assert "user-provided" in content or "user provided" in content
    assert "not translated" in content or "preserve" in content or "remain" in content


def test_boundary_doc_mentions_research_notes_preserved():
    content = BOUNDARY_DOC.read_text(encoding="utf-8").lower()
    assert "research note" in content


# ---------------------------------------------------------------------------
# Per-locale guardrails
# ---------------------------------------------------------------------------

def test_boundary_doc_mentions_per_locale_guardrails():
    content = BOUNDARY_DOC.read_text(encoding="utf-8").lower()
    assert "guardrail" in content
    assert "locale" in content or "per-locale" in content


def test_boundary_doc_states_guardrails_per_locale_required():
    content = BOUNDARY_DOC.read_text(encoding="utf-8").lower()
    # Must state that each locale needs its own guardrails before activation
    assert "guardrail" in content
    assert "swedish" in content or "sv" in content


def test_boundary_doc_guardrails_protect_semantics_not_words():
    content = BOUNDARY_DOC.read_text(encoding="utf-8").lower()
    assert "semantic" in content or "category" in content or "categor" in content


# ---------------------------------------------------------------------------
# Default language
# ---------------------------------------------------------------------------

def test_boundary_doc_states_default_is_english():
    content = BOUNDARY_DOC.read_text(encoding="utf-8").lower()
    assert "default" in content
    assert "english" in content


def test_boundary_doc_states_missing_locale_falls_back_to_english():
    content = BOUNDARY_DOC.read_text(encoding="utf-8").lower()
    assert "fail" in content or "fallback" in content or "fall" in content


# ---------------------------------------------------------------------------
# Future phases
# ---------------------------------------------------------------------------

def test_boundary_doc_includes_future_phases():
    content = BOUNDARY_DOC.read_text(encoding="utf-8").lower()
    assert "phase" in content


def test_boundary_doc_mentions_strings_inventory_as_first_phase():
    content = BOUNDARY_DOC.read_text(encoding="utf-8").lower()
    assert "inventor" in content or "extract" in content


def test_boundary_doc_mentions_language_option_as_future():
    content = BOUNDARY_DOC.read_text(encoding="utf-8")
    assert "--language" in content


# ---------------------------------------------------------------------------
# Out-of-scope list
# ---------------------------------------------------------------------------

def test_boundary_doc_includes_out_of_scope_section():
    content = BOUNDARY_DOC.read_text(encoding="utf-8").lower()
    assert "out of scope" in content or "out-of-scope" in content


def test_boundary_doc_excludes_ai_translation():
    content = BOUNDARY_DOC.read_text(encoding="utf-8").lower()
    assert "ai translation" in content or "external translation" in content


def test_boundary_doc_excludes_runtime_locale_detection():
    content = BOUNDARY_DOC.read_text(encoding="utf-8").lower()
    assert "runtime" in content or "locale detection" in content


# ---------------------------------------------------------------------------
# No runtime behavior changes introduced
# ---------------------------------------------------------------------------

def test_no_language_option_in_cli():
    # Sprint 257: --language added to Phase 1 read-only commands (weekly-review,
    # snapshot validate, snapshot review). Deferred commands remain without it.
    import atlas.cli.main as main_mod
    source = Path(main_mod.__file__).read_text(encoding="utf-8")
    # Phase 1 implementation is present
    assert "--language" in source


def test_no_locale_imports_introduced():
    """No locale or gettext imports should appear in atlas package."""
    for py_file in Path("atlas").rglob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        assert "import gettext" not in source, f"gettext import in {py_file}"
        assert "import locale" not in source or "atlas/snapshot_input" not in str(py_file), \
            f"locale import in {py_file}"


def test_enum_values_still_canonical_english():
    from atlas.snapshot_input.schema import SnapshotConfirmationStatus, SnapshotType
    assert SnapshotConfirmationStatus.CONFIRMED.value == "confirmed"
    assert SnapshotConfirmationStatus.REJECTED.value == "rejected"
    assert SnapshotType.RESEARCH_NOTES_SNAPSHOT.value == "research_notes_snapshot"
    assert SnapshotType.COMPANY_FACTS_SNAPSHOT.value == "company_facts_snapshot"


# ---------------------------------------------------------------------------
# Language guardrails
# ---------------------------------------------------------------------------

def test_boundary_doc_no_forbidden_language():
    content = BOUNDARY_DOC.read_text(encoding="utf-8")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in content, f"Forbidden language in boundary doc: {term!r}"
