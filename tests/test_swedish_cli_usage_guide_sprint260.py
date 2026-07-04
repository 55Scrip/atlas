"""Sprint 260 — Swedish CLI usage guide tests.

Verifies that docs/SwedishCLIUsageGuide.md exists and contains the required
documentation content, that CLI language support remains functional, that
supported locales remain exactly en and sv, and that no runtime behavior
changed.

No production code is changed by Sprint 260. This is a documentation sprint.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

GUIDE = Path("docs/SwedishCLIUsageGuide.md")
CLI_MAIN = Path("atlas/cli/main.py")
LOCALE_SUPPORT = Path("atlas/locale_support.py")

_PORTFOLIO = Path("examples/weekly_review/portfolio.json")
_WATCHLIST = Path("examples/weekly_review/watchlist.json")
_DRAFT_RESEARCH = Path("examples/snapshot_drafts/research_notes_snapshot.json")


def _atlas_cli(*args: str) -> subprocess.CompletedProcess:
    atlas_bin = str(Path(".venv/bin/atlas").resolve())
    return subprocess.run([atlas_bin, *args], capture_output=True, text=True)


# ---------------------------------------------------------------------------
# Guide exists and has content
# ---------------------------------------------------------------------------

def test_guide_exists() -> None:
    assert GUIDE.exists()


def test_guide_not_empty() -> None:
    assert len(GUIDE.read_text(encoding="utf-8")) > 1000


def test_guide_has_purpose_section() -> None:
    assert "## Purpose" in GUIDE.read_text(encoding="utf-8")


def test_guide_has_quick_start_section() -> None:
    assert "Quick Start" in GUIDE.read_text(encoding="utf-8")


def test_guide_has_supported_commands_section() -> None:
    assert "Supported Commands" in GUIDE.read_text(encoding="utf-8")


def test_guide_has_default_behavior_section() -> None:
    assert "Default Behavior" in GUIDE.read_text(encoding="utf-8")


def test_guide_has_examples_section() -> None:
    assert "## Examples" in GUIDE.read_text(encoding="utf-8")


def test_guide_has_what_changes_section() -> None:
    content = GUIDE.read_text(encoding="utf-8")
    assert "What Changes" in content


def test_guide_has_canonical_english_section() -> None:
    content = GUIDE.read_text(encoding="utf-8")
    assert "Canonical English" in content or "Canonical" in content


def test_guide_has_does_not_translate_section() -> None:
    content = GUIDE.read_text(encoding="utf-8")
    assert "Does Not Translate" in content or "Not Translate" in content


def test_guide_has_written_file_section() -> None:
    content = GUIDE.read_text(encoding="utf-8")
    assert "Written File" in content


def test_guide_has_unsupported_languages_section() -> None:
    content = GUIDE.read_text(encoding="utf-8")
    assert "Unsupported" in content


def test_guide_has_safety_boundaries_section() -> None:
    content = GUIDE.read_text(encoding="utf-8")
    assert "Safety" in content


def test_guide_has_related_documents_section() -> None:
    content = GUIDE.read_text(encoding="utf-8")
    assert "Related" in content


# ---------------------------------------------------------------------------
# Guide documents --language sv and --language en
# ---------------------------------------------------------------------------

def test_guide_documents_language_sv() -> None:
    assert "--language sv" in GUIDE.read_text(encoding="utf-8")


def test_guide_documents_language_en() -> None:
    assert "--language en" in GUIDE.read_text(encoding="utf-8")


def test_guide_documents_default_english() -> None:
    content = GUIDE.read_text(encoding="utf-8").lower()
    assert "default" in content
    assert "english" in content


def test_guide_states_omitting_language_keeps_english() -> None:
    content = GUIDE.read_text(encoding="utf-8").lower()
    assert "omit" in content or "omitting" in content


# ---------------------------------------------------------------------------
# Guide lists all supported commands
# ---------------------------------------------------------------------------

def test_guide_lists_weekly_review() -> None:
    assert "weekly-review" in GUIDE.read_text(encoding="utf-8")


def test_guide_lists_snapshot_validate() -> None:
    assert "snapshot validate" in GUIDE.read_text(encoding="utf-8")


def test_guide_lists_snapshot_review() -> None:
    assert "snapshot review" in GUIDE.read_text(encoding="utf-8")


def test_guide_lists_snapshot_confirm() -> None:
    assert "snapshot confirm" in GUIDE.read_text(encoding="utf-8")


def test_guide_lists_snapshot_reject() -> None:
    assert "snapshot reject" in GUIDE.read_text(encoding="utf-8")


def test_guide_lists_export_research_notes() -> None:
    assert "export-research-notes" in GUIDE.read_text(encoding="utf-8")


def test_guide_lists_export_company_facts() -> None:
    assert "export-company-facts" in GUIDE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Guide states display-text-only localization
# ---------------------------------------------------------------------------

def test_guide_states_display_text_only() -> None:
    content = GUIDE.read_text(encoding="utf-8").lower()
    assert "display" in content and "only" in content


def test_guide_states_language_does_not_change_files() -> None:
    content = GUIDE.read_text(encoding="utf-8").lower()
    assert "written" in content
    assert "unchanged" in content or "identical" in content or "same" in content


# ---------------------------------------------------------------------------
# Guide states canonical values remain English
# ---------------------------------------------------------------------------

def test_guide_documents_snapshot_type_canonical() -> None:
    assert "research_notes_snapshot" in GUIDE.read_text(encoding="utf-8")


def test_guide_documents_confirmation_status_canonical() -> None:
    content = GUIDE.read_text(encoding="utf-8")
    assert "confirmed" in content and "rejected" in content


def test_guide_documents_warning_codes_canonical() -> None:
    content = GUIDE.read_text(encoding="utf-8")
    assert "missing_optional_profile" in content or "warning" in content.lower()


def test_guide_documents_ticker_canonical() -> None:
    content = GUIDE.read_text(encoding="utf-8")
    assert "ASML" in content or "ticker" in content.lower()


# ---------------------------------------------------------------------------
# Guide states user-provided content is not translated
# ---------------------------------------------------------------------------

def test_guide_documents_user_content_not_translated() -> None:
    content = GUIDE.read_text(encoding="utf-8").lower()
    assert "user-provided" in content or "user provided" in content
    assert "not translated" in content or "never translated" in content or "does not translate" in content


def test_guide_documents_research_notes_preserved() -> None:
    content = GUIDE.read_text(encoding="utf-8").lower()
    assert "research note" in content


def test_guide_documents_scope_notes_preserved() -> None:
    content = GUIDE.read_text(encoding="utf-8").lower()
    assert "scope note" in content


# ---------------------------------------------------------------------------
# Guide documents written file behavior
# ---------------------------------------------------------------------------

def test_guide_documents_confirm_file_unchanged() -> None:
    content = GUIDE.read_text(encoding="utf-8").lower()
    assert "confirm" in content
    assert "json" in content


def test_guide_documents_notes_md_unchanged() -> None:
    assert "notes.md" in GUIDE.read_text(encoding="utf-8")


def test_guide_documents_company_facts_unchanged() -> None:
    content = GUIDE.read_text(encoding="utf-8").lower()
    assert "company facts" in content


# ---------------------------------------------------------------------------
# Guide documents unsupported languages
# ---------------------------------------------------------------------------

def test_guide_documents_fr_as_unsupported() -> None:
    assert "fr" in GUIDE.read_text(encoding="utf-8")


def test_guide_documents_no_fallback() -> None:
    content = GUIDE.read_text(encoding="utf-8").lower()
    assert "no fallback" in content or "fallback" in content


def test_guide_documents_no_case_normalization() -> None:
    content = GUIDE.read_text(encoding="utf-8").lower()
    assert "case" in content or "EN" in GUIDE.read_text(encoding="utf-8")


def test_guide_documents_no_region_codes() -> None:
    content = GUIDE.read_text(encoding="utf-8")
    assert "en-US" in content or "sv-SE" in content or "region" in content.lower()


# ---------------------------------------------------------------------------
# Guide documents safety boundaries
# ---------------------------------------------------------------------------

def test_guide_states_no_recommendations() -> None:
    content = GUIDE.read_text(encoding="utf-8").lower()
    assert "recommendation" in content


def test_guide_states_language_does_not_change_reasoning() -> None:
    content = GUIDE.read_text(encoding="utf-8").lower()
    assert "reasoning" in content or "judgment" in content


# ---------------------------------------------------------------------------
# Guide references related localization documents
# ---------------------------------------------------------------------------

def test_guide_references_localization_boundary() -> None:
    assert "AtlasLocalizationBoundary" in GUIDE.read_text(encoding="utf-8")


def test_guide_references_swedish_guardrails() -> None:
    assert "SwedishSafeLanguageGuardrails" in GUIDE.read_text(encoding="utf-8")


def test_guide_references_cli_language_plan() -> None:
    assert "CLILanguageOptionPlan" in GUIDE.read_text(encoding="utf-8")


def test_guide_references_phase2_plan() -> None:
    assert "Phase2SnapshotCLILanguagePlan" in GUIDE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI still supports --language on all intended commands
# ---------------------------------------------------------------------------

def test_weekly_review_help_has_language() -> None:
    result = _atlas_cli("weekly-review", "--help")
    assert result.returncode == 0
    assert "--language" in result.stdout


def test_snapshot_validate_help_has_language() -> None:
    result = _atlas_cli("snapshot", "validate", "--help")
    assert result.returncode == 0
    assert "--language" in result.stdout


def test_snapshot_review_help_has_language() -> None:
    result = _atlas_cli("snapshot", "review", "--help")
    assert result.returncode == 0
    assert "--language" in result.stdout


def test_snapshot_confirm_help_has_language() -> None:
    result = _atlas_cli("snapshot", "confirm", "--help")
    assert result.returncode == 0
    assert "--language" in result.stdout


def test_snapshot_reject_help_has_language() -> None:
    result = _atlas_cli("snapshot", "reject", "--help")
    assert result.returncode == 0
    assert "--language" in result.stdout


def test_snapshot_export_research_notes_help_has_language() -> None:
    result = _atlas_cli("snapshot", "export-research-notes", "--help")
    assert result.returncode == 0
    assert "--language" in result.stdout


def test_snapshot_export_company_facts_help_has_language() -> None:
    result = _atlas_cli("snapshot", "export-company-facts", "--help")
    assert result.returncode == 0
    assert "--language" in result.stdout


# ---------------------------------------------------------------------------
# Supported locales remain exactly en and sv
# ---------------------------------------------------------------------------

def test_supported_locales_still_en_sv() -> None:
    from atlas.locale_support import _SUPPORTED_LOCALES
    assert _SUPPORTED_LOCALES == frozenset({"en", "sv"})


def test_ensure_supported_locale_en_passes() -> None:
    from atlas.locale_support import ensure_supported_locale
    ensure_supported_locale("en")


def test_ensure_supported_locale_sv_passes() -> None:
    from atlas.locale_support import ensure_supported_locale
    ensure_supported_locale("sv")


def test_ensure_supported_locale_fr_still_raises() -> None:
    import pytest
    from atlas.locale_support import ensure_supported_locale
    with pytest.raises(ValueError):
        ensure_supported_locale("fr")


# ---------------------------------------------------------------------------
# No runtime behavior changed
# ---------------------------------------------------------------------------

def test_no_gettext_import_in_locale_support() -> None:
    assert "import gettext" not in LOCALE_SUPPORT.read_text(encoding="utf-8")


def test_no_locale_detection_in_locale_support() -> None:
    source = LOCALE_SUPPORT.read_text(encoding="utf-8")
    assert "import locale" not in source
    assert "locale.getlocale" not in source


def test_no_translation_catalogs() -> None:
    import atlas
    assert not any(Path(atlas.__file__).parent.glob("*.po"))
    assert not any(Path(atlas.__file__).parent.glob("*.mo"))


def test_weekly_review_default_still_english() -> None:
    result = _atlas_cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
    )
    assert result.returncode == 0, result.stderr
    assert "Atlas Weekly Investment Review" in result.stdout
    assert "Atlas veckovis investeringsgranskning" not in result.stdout


def test_snapshot_validate_default_still_english() -> None:
    result = _atlas_cli("snapshot", "validate", str(_DRAFT_RESEARCH))
    assert result.returncode == 0, result.stderr
    assert "Snapshot Draft Validation" in result.stdout
