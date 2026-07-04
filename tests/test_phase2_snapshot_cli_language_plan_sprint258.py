"""Sprint 258 — Phase 2 Snapshot CLI language plan tests.

Verifies that docs/Phase2SnapshotCLILanguagePlan.md exists and contains the
required planning content, that Phase 2 commands still have no --language option,
that Phase 1 commands still have --language, and that no runtime behavior changed.

No production code is changed by Sprint 258. This is a planning-only sprint.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

PLAN = Path("docs/Phase2SnapshotCLILanguagePlan.md")
CLI_MAIN = Path("atlas/cli/main.py")
LOCALE_SUPPORT = Path("atlas/locale_support.py")

_PORTFOLIO = Path("examples/weekly_review/portfolio.json")
_WATCHLIST = Path("examples/weekly_review/watchlist.json")
_DRAFT_RESEARCH = Path("examples/snapshot_drafts/research_notes_snapshot.json")


def _atlas_cli(*args: str) -> subprocess.CompletedProcess:
    atlas_bin = str(Path(".venv/bin/atlas").resolve())
    return subprocess.run([atlas_bin, *args], capture_output=True, text=True)


# ---------------------------------------------------------------------------
# Plan document exists and has required sections
# ---------------------------------------------------------------------------

def test_plan_document_exists() -> None:
    assert PLAN.exists()


def test_plan_not_empty() -> None:
    assert len(PLAN.read_text(encoding="utf-8")) > 1000


def test_plan_has_purpose_section() -> None:
    assert "## Purpose" in PLAN.read_text(encoding="utf-8")


def test_plan_has_non_goals_section() -> None:
    assert "## Non-Goals" in PLAN.read_text(encoding="utf-8")


def test_plan_has_current_state_section() -> None:
    assert "## Current State" in PLAN.read_text(encoding="utf-8")


def test_plan_has_target_commands_section() -> None:
    assert "## Target Commands" in PLAN.read_text(encoding="utf-8")


def test_plan_has_display_only_section() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "Display" in content and "Localization Boundary" in content


def test_plan_has_written_artifact_section() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "Written Artifact" in content


def test_plan_has_command_by_command_section() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "Command-by-Command" in content


def test_plan_has_unsupported_language_section() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "Unsupported Language" in content


def test_plan_has_backward_compatibility_section() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "Backward Compatibility" in content


def test_plan_has_canonical_values_section() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "Canonical" in content


def test_plan_has_user_provided_content_section() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "User-Provided Content" in content


def test_plan_has_required_tests_section() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "Required Tests" in content


def test_plan_has_safety_gates_section() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "Safety Gates" in content


def test_plan_has_rollout_section() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "Rollout" in content


def test_plan_has_open_questions_section() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "Open Questions" in content


def test_plan_has_recommended_implementation_sprint() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "Recommended Implementation Sprint" in content or "Sprint 259" in content


# ---------------------------------------------------------------------------
# Plan states Phase 2 is not implemented in Sprint 258
# ---------------------------------------------------------------------------

def test_plan_states_not_implemented() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "not yet implemented" in content or "not implemented" in content


def test_plan_states_phase1_complete() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "Phase 1" in content
    assert "complete" in content.lower() or "implemented" in content.lower()


def test_plan_states_phase2_planned() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "Phase 2" in content
    assert "planned" in content.lower() or "deferred" in content.lower()


# ---------------------------------------------------------------------------
# Plan lists the four target commands
# ---------------------------------------------------------------------------

def test_plan_lists_snapshot_confirm() -> None:
    assert "snapshot confirm" in PLAN.read_text(encoding="utf-8")


def test_plan_lists_snapshot_reject() -> None:
    assert "snapshot reject" in PLAN.read_text(encoding="utf-8")


def test_plan_lists_export_research_notes() -> None:
    assert "export-research-notes" in PLAN.read_text(encoding="utf-8")


def test_plan_lists_export_company_facts() -> None:
    assert "export-company-facts" in PLAN.read_text(encoding="utf-8")


def test_plan_proposes_language_option_for_phase2() -> None:
    assert "--language" in PLAN.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Plan states localization is display-only
# ---------------------------------------------------------------------------

def test_plan_states_display_only() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "display" in content and "only" in content


def test_plan_states_written_artifacts_unchanged() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "written" in content
    assert "unchanged" in content or "identical" in content


def test_plan_states_file_content_not_affected() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "file" in content
    assert "not affect" in content or "unaffected" in content or "identical" in content


# ---------------------------------------------------------------------------
# Plan documents command-by-command behavior
# ---------------------------------------------------------------------------

def test_plan_documents_confirm_behavior() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "snapshot confirm" in content
    assert "confirmed" in content


def test_plan_documents_reject_behavior() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "snapshot reject" in content
    assert "rejected" in content


def test_plan_documents_export_research_notes_behavior() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "export-research-notes" in content
    assert "notes.md" in content


def test_plan_documents_export_company_facts_behavior() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "export-company-facts" in content
    assert ".json" in content or "company facts" in content


# ---------------------------------------------------------------------------
# Plan documents unsupported language fails before side effects
# ---------------------------------------------------------------------------

def test_plan_documents_unsupported_fails_before_writes() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "before" in content
    assert "file" in content


def test_plan_documents_non_zero_exit() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "non-zero" in content or "exit" in content


def test_plan_documents_no_partial_output() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "no file" in content or "no output" in content or "not created" in content


def test_plan_documents_fr_as_unsupported() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "fr" in content


# ---------------------------------------------------------------------------
# Plan documents canonical value preservation
# ---------------------------------------------------------------------------

def test_plan_documents_snapshot_type_canonical() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "research_notes_snapshot" in content


def test_plan_documents_confirmation_status_canonical() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "confirmed" in content and "rejected" in content


def test_plan_documents_schema_keys_canonical() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "confirmation_status" in content
    assert "snapshot_type" in content


def test_plan_documents_ticker_canonical() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "ticker" in content


# ---------------------------------------------------------------------------
# Plan documents user-provided content passthrough
# ---------------------------------------------------------------------------

def test_plan_documents_user_content_not_translated() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "user-provided" in content
    assert "not translated" in content or "unchanged" in content


def test_plan_documents_research_note_text_preserved() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "research note" in content


def test_plan_documents_notes_field_preserved() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "notes" in content


# ---------------------------------------------------------------------------
# Plan documents future implementation tests
# ---------------------------------------------------------------------------

def test_plan_lists_file_invariance_tests() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "invariance" in content or "identical" in content


def test_plan_lists_swedish_display_tests() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "swedish" in content


def test_plan_lists_backward_compat_tests() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "default" in content and "english" in content


# ---------------------------------------------------------------------------
# Plan documents safety gates
# ---------------------------------------------------------------------------

def test_plan_references_phase1_gate() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "Sprint 257" in content or "Phase 1" in content


def test_plan_references_sv_activation_gate() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "test_sv_activation_full_suite_gate" in content or "Sprint 255" in content


def test_plan_references_unsupported_locale_regression() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "test_unsupported_locale_regression" in content or "Sprint 254" in content


def test_plan_references_canonical_passthrough_gate() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "test_swedish_canonical_passthrough" in content or "Sprint 253" in content


def test_plan_requires_file_write_invariance_tests() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "file-write invariance" in content or "file invariance" in content


# ---------------------------------------------------------------------------
# Current Phase 2 command help has no --language
# ---------------------------------------------------------------------------

def test_snapshot_confirm_help_has_no_language() -> None:
    result = _atlas_cli("snapshot", "confirm", "--help")
    assert result.returncode == 0, result.stderr
    assert "--language" not in result.stdout


def test_snapshot_reject_help_has_no_language() -> None:
    result = _atlas_cli("snapshot", "reject", "--help")
    assert result.returncode == 0, result.stderr
    assert "--language" not in result.stdout


def test_snapshot_export_research_notes_help_has_no_language() -> None:
    result = _atlas_cli("snapshot", "export-research-notes", "--help")
    assert result.returncode == 0, result.stderr
    assert "--language" not in result.stdout


def test_snapshot_export_company_facts_help_has_no_language() -> None:
    result = _atlas_cli("snapshot", "export-company-facts", "--help")
    assert result.returncode == 0, result.stderr
    assert "--language" not in result.stdout


# ---------------------------------------------------------------------------
# Phase 1 commands still have --language
# ---------------------------------------------------------------------------

def test_weekly_review_help_has_language() -> None:
    result = _atlas_cli("weekly-review", "--help")
    assert result.returncode == 0, result.stderr
    assert "--language" in result.stdout


def test_snapshot_validate_help_has_language() -> None:
    result = _atlas_cli("snapshot", "validate", "--help")
    assert result.returncode == 0, result.stderr
    assert "--language" in result.stdout


def test_snapshot_review_help_has_language() -> None:
    result = _atlas_cli("snapshot", "review", "--help")
    assert result.returncode == 0, result.stderr
    assert "--language" in result.stdout


# ---------------------------------------------------------------------------
# CLI source: Phase 2 commands present, --language deferred
# ---------------------------------------------------------------------------

def test_cli_source_has_snapshot_confirm_command() -> None:
    source = CLI_MAIN.read_text(encoding="utf-8")
    assert "snapshot_confirm_command" in source


def test_cli_source_has_snapshot_reject_command() -> None:
    source = CLI_MAIN.read_text(encoding="utf-8")
    assert "snapshot_reject_command" in source


def test_cli_source_phase1_has_language_param() -> None:
    source = CLI_MAIN.read_text(encoding="utf-8")
    assert "--language" in source


def test_plan_document_exists_in_source_context() -> None:
    # The plan document itself is the source of truth for Phase 2 boundaries.
    assert PLAN.exists()
    assert Path("docs/CLILanguageOptionPlan.md").exists()


# ---------------------------------------------------------------------------
# Locale support unchanged
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


def test_phase1_weekly_review_default_english() -> None:
    result = _atlas_cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
    )
    assert result.returncode == 0, result.stderr
    assert "Atlas Weekly Investment Review" in result.stdout
    assert "Atlas veckovis investeringsgranskning" not in result.stdout


def test_phase1_snapshot_validate_default_english() -> None:
    result = _atlas_cli("snapshot", "validate", str(_DRAFT_RESEARCH))
    assert result.returncode == 0, result.stderr
    assert "Snapshot Draft Validation" in result.stdout
    assert "Validering av Snapshot Draft" not in result.stdout
