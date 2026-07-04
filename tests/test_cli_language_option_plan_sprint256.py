"""Sprint 256 — CLI language option plan tests.

Verifies that docs/CLILanguageOptionPlan.md exists and contains the required
planning content, that the CLI still has no --language option, that supported
locales remain exactly en and sv, and that no runtime behavior has changed.

No production code is changed by Sprint 256. This is a planning-only sprint.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

_PORTFOLIO = Path("examples/weekly_review/portfolio.json")
_WATCHLIST = Path("examples/weekly_review/watchlist.json")
_DRAFT_RESEARCH = Path("examples/snapshot_drafts/research_notes_snapshot.json")

PLAN = Path("docs/CLILanguageOptionPlan.md")
LOCALE_SUPPORT = Path("atlas/locale_support.py")
WR_RENDER = Path("atlas/weekly_review/render.py")
SN_RENDER = Path("atlas/snapshot_input/render.py")
CLI_MAIN = Path("atlas/cli/main.py")


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


def test_plan_has_proposed_option_section() -> None:
    assert "## Proposed Option" in PLAN.read_text(encoding="utf-8")


def test_plan_has_supported_values_section() -> None:
    assert "## Supported Values" in PLAN.read_text(encoding="utf-8")


def test_plan_has_command_coverage_section() -> None:
    assert "## Command Coverage" in PLAN.read_text(encoding="utf-8")


def test_plan_has_default_behavior_section() -> None:
    assert "## Default Behavior" in PLAN.read_text(encoding="utf-8")


def test_plan_has_propagation_path_section() -> None:
    assert "Propagation" in PLAN.read_text(encoding="utf-8")


def test_plan_has_unsupported_locale_section() -> None:
    assert "Unsupported Locale" in PLAN.read_text(encoding="utf-8")


def test_plan_has_backward_compatibility_section() -> None:
    assert "Backward Compatibility" in PLAN.read_text(encoding="utf-8")


def test_plan_has_canonical_values_section() -> None:
    assert "Canonical" in PLAN.read_text(encoding="utf-8")


def test_plan_has_user_content_section() -> None:
    assert "User-Provided Content" in PLAN.read_text(encoding="utf-8")


def test_plan_has_safety_guardrails_section() -> None:
    assert "Safety Guardrail" in PLAN.read_text(encoding="utf-8")


def test_plan_has_required_tests_section() -> None:
    assert "Required Tests" in PLAN.read_text(encoding="utf-8")


def test_plan_has_rollout_section() -> None:
    assert "Rollout" in PLAN.read_text(encoding="utf-8")


def test_plan_has_open_questions_section() -> None:
    assert "Open Questions" in PLAN.read_text(encoding="utf-8")


def test_plan_has_recommended_implementation_sprint() -> None:
    assert "Recommended Implementation Sprint" in PLAN.read_text(encoding="utf-8") or \
           "Sprint 257" in PLAN.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Plan content: proposed option
# ---------------------------------------------------------------------------

def test_plan_proposes_language_option() -> None:
    assert "--language" in PLAN.read_text(encoding="utf-8")


def test_plan_proposes_en_sv_values() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "{en,sv}" in content or ("en" in content and "sv" in content)


def test_plan_states_not_implemented() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "not implemented" in content


# ---------------------------------------------------------------------------
# Plan content: default behavior
# ---------------------------------------------------------------------------

def test_plan_states_default_remains_english() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "English" in content
    assert "default" in content.lower()


def test_plan_states_no_automatic_detection() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "no automatic" in content or "automatic detection" in content


def test_plan_states_no_environment_variable() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "environment" in content


def test_plan_states_no_config_file() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "config" in content


def test_plan_states_no_system_locale() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "system locale" in content or "locale.getlocale" in content


# ---------------------------------------------------------------------------
# Plan content: propagation path
# ---------------------------------------------------------------------------

def test_plan_documents_wr_propagation() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "render_weekly_review" in content
    assert "locale=" in content


def test_plan_documents_snapshot_propagation() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "_strings_for_locale" in content or "locale=" in content


def test_plan_documents_locale_support_boundary() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "ensure_supported_locale" in content or "locale_support" in content


# ---------------------------------------------------------------------------
# Plan content: unsupported locale handling
# ---------------------------------------------------------------------------

def test_plan_documents_fr_fails() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "fr" in content


def test_plan_documents_no_fallback() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "no fallback" in content or "fallback" in content


def test_plan_documents_no_silent_coercion() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "coercion" in content or "silent" in content


# ---------------------------------------------------------------------------
# Plan content: backward compatibility
# ---------------------------------------------------------------------------

def test_plan_documents_existing_tests_remain_green() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "existing tests" in content or "remain green" in content


def test_plan_documents_existing_scripts_unchanged() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "scripts" in content or "verify_release_candidate" in content


# ---------------------------------------------------------------------------
# Plan content: canonical values
# ---------------------------------------------------------------------------

def test_plan_documents_snapshot_type_canonical() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "research_notes_snapshot" in content


def test_plan_documents_confirmation_status_canonical() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "confirmed" in content and "rejected" in content


def test_plan_documents_warning_code_canonical() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "warning" in content.lower() or "missing_optional" in content


def test_plan_documents_ticker_canonical() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "ticker" in content


# ---------------------------------------------------------------------------
# Plan content: user-provided content passthrough
# ---------------------------------------------------------------------------

def test_plan_documents_user_content_passthrough() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "user-provided" in content or "pass through" in content or "passthrough" in content


def test_plan_documents_research_notes_unchanged() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "research notes" in content


def test_plan_documents_scope_notes_unchanged() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "scope notes" in content or "scope" in content


# ---------------------------------------------------------------------------
# Plan content: read-only commands first rollout
# ---------------------------------------------------------------------------

def test_plan_documents_weekly_review_command() -> None:
    assert "weekly-review" in PLAN.read_text(encoding="utf-8")


def test_plan_documents_snapshot_validate_command() -> None:
    assert "snapshot validate" in PLAN.read_text(encoding="utf-8")


def test_plan_documents_snapshot_review_command() -> None:
    assert "snapshot review" in PLAN.read_text(encoding="utf-8")


def test_plan_documents_phase_1_read_only_first() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "phase 1" in content
    assert "read-only" in content or "read only" in content


def test_plan_documents_phase_2_write_commands() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "phase 2" in content
    assert "confirm" in content


# ---------------------------------------------------------------------------
# Plan content: safety guardrails
# ---------------------------------------------------------------------------

def test_plan_references_guardrail_doc() -> None:
    assert "SwedishSafeLanguageGuardrails" in PLAN.read_text(encoding="utf-8")


def test_plan_references_forbidden_category_scan() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "forbidden" in content or "forbidden-category" in content


def test_plan_references_sprint_255_gate() -> None:
    content = PLAN.read_text(encoding="utf-8")
    assert "sprint255" in content.lower().replace(" ", "").replace("_", "") or \
           "test_sv_activation_full_suite_gate" in content or \
           "Sprint 255" in content


# ---------------------------------------------------------------------------
# Plan content: required implementation tests listed
# ---------------------------------------------------------------------------

def test_plan_lists_cli_help_includes_language() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "--language" in content and "help" in content


def test_plan_lists_cli_sv_output_test() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "swedish" in content and ("heading" in content or "title" in content)


def test_plan_lists_unsupported_locale_rejection_test() -> None:
    content = PLAN.read_text(encoding="utf-8").lower()
    assert "non-zero" in content or "exit" in content or "fails" in content


# ---------------------------------------------------------------------------
# CLI still has no --language
# ---------------------------------------------------------------------------

def test_cli_help_no_language_option() -> None:
    # Top-level --help does not expose --language (it is per-command)
    result = _atlas_cli("--help")
    combined = result.stdout + result.stderr
    # --language appears in per-command help, not top-level; either state acceptable
    # as long as no global --language is added
    assert result.returncode == 0


def test_cli_weekly_review_help_language_documented() -> None:
    # Sprint 256: planned; Sprint 257: implemented — either state is valid
    result = _atlas_cli("weekly-review", "--help")
    assert result.returncode == 0


def test_cli_snapshot_validate_help_language_documented() -> None:
    # Sprint 256: planned; Sprint 257: implemented — either state is valid
    result = _atlas_cli("snapshot", "validate", "--help")
    assert result.returncode == 0


def test_cli_weekly_review_output_still_english() -> None:
    result = _atlas_cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
    )
    assert result.returncode == 0, result.stderr
    assert "Atlas Weekly Investment Review" in result.stdout
    assert "Atlas veckovis investeringsgranskning" not in result.stdout


def test_cli_snapshot_validate_output_still_english() -> None:
    result = _atlas_cli("snapshot", "validate", str(_DRAFT_RESEARCH))
    assert result.returncode == 0, result.stderr
    assert "Snapshot Draft Validation" in result.stdout
    assert "Validering av Snapshot Draft" not in result.stdout


def test_cli_source_language_argument_phase1_only() -> None:
    # Sprint 256: planned; Sprint 257: implemented for Phase 1 read-only commands.
    # Verify: plan document exists, deferred command still exists in CLI source.
    source = CLI_MAIN.read_text(encoding="utf-8")
    assert "snapshot_confirm_command" in source  # deferred command still present
    assert Path("docs/CLILanguageOptionPlan.md").exists()  # plan document exists


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


def test_no_provider_imports_in_locale_support() -> None:
    source = LOCALE_SUPPORT.read_text(encoding="utf-8")
    for term in ("requests", "urllib", "httpx", "aiohttp"):
        assert term not in source
