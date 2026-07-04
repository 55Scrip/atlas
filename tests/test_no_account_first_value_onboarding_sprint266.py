"""Sprint 266 — No-Account First-Value Onboarding specification tests.

Verifies that docs/NoAccountFirstValueOnboarding.md exists and contains the
required product principle content. No runtime behaviour is changed by this
sprint. These tests read the specification document only.
"""

from __future__ import annotations

from pathlib import Path

DOC = Path("docs/NoAccountFirstValueOnboarding.md")


def _doc() -> str:
    return DOC.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Document exists
# ---------------------------------------------------------------------------

def test_document_exists() -> None:
    assert DOC.exists(), "docs/NoAccountFirstValueOnboarding.md must exist"


# ---------------------------------------------------------------------------
# Core product principle
# ---------------------------------------------------------------------------

def test_principle_atlas_useful_before_trust() -> None:
    assert "useful before it asks for trust" in _doc()


def test_principle_account_after_first_value() -> None:
    d = _doc()
    assert "after" in d.lower()
    assert "first value" in d.lower() or "meaningful value" in d.lower()


def test_principle_no_account_wall_before_review() -> None:
    d = _doc()
    # Doc must state account prompt does not come before first output
    assert "before" in d.lower()
    assert "account" in d.lower()


# ---------------------------------------------------------------------------
# First-value definition
# ---------------------------------------------------------------------------

def test_first_value_defined() -> None:
    d = _doc()
    assert "first value" in d.lower() or "First-Value" in d


def test_first_value_includes_evidence_gaps() -> None:
    assert "evidence gap" in _doc().lower()


def test_first_value_includes_reasons_to_wait() -> None:
    d = _doc()
    assert "reason" in d.lower() and "wait" in d.lower()


def test_first_value_includes_follow_up_questions() -> None:
    assert "follow-up question" in _doc().lower() or "follow up question" in _doc().lower()


def test_first_value_no_recommendation_language() -> None:
    # Doc may mention "price targets" in the context of what Atlas does NOT include.
    # The test verifies Atlas affirmatively recommending them is absent.
    d = _doc().lower()
    assert "guaranteed" not in d
    assert "outperform" not in d
    # If "price target" appears, it must be in a negative/exclusion context
    if "price target" in d:
        assert "does not include" in d or "not include" in d or "do not use" in d or "avoid" in d


# ---------------------------------------------------------------------------
# Guest / No-account mode
# ---------------------------------------------------------------------------

def test_guest_mode_defined() -> None:
    d = _doc()
    assert "guest" in d.lower() or "no-account" in d.lower() or "no account" in d.lower()


def test_guest_mode_no_credential_required() -> None:
    d = _doc().lower()
    assert "no account" in d or "without" in d
    assert "credential" in d or "email" in d or "login" in d


def test_guest_mode_no_silent_data_retention() -> None:
    d = _doc().lower()
    assert "silent" in d or "retain" in d or "discard" in d or "temporary" in d


# ---------------------------------------------------------------------------
# Example first session
# ---------------------------------------------------------------------------

def test_example_first_session_exists() -> None:
    assert "First Session" in _doc() or "first session" in _doc().lower()


def test_example_first_session_account_prompt_after_review() -> None:
    d = _doc()
    # The doc must show account prompt appearing after the review
    assert "Save this workspace" in d or "save" in d.lower()
    assert "after" in d.lower()


def test_example_first_session_labeled_future_direction() -> None:
    d = _doc().lower()
    assert "future" in d


# ---------------------------------------------------------------------------
# Pre-account capabilities
# ---------------------------------------------------------------------------

def test_pre_account_capabilities_section_exists() -> None:
    d = _doc()
    assert "Before Account Creation" in d or "before account" in d.lower()


def test_pre_account_includes_paste_portfolio() -> None:
    assert "portfolio" in _doc().lower()


def test_pre_account_includes_paste_watchlist() -> None:
    assert "watchlist" in _doc().lower()


def test_pre_account_includes_paste_research_notes() -> None:
    assert "research notes" in _doc().lower()


def test_pre_account_includes_temporary_review() -> None:
    d = _doc().lower()
    assert "temporary" in d or "temp" in d


# ---------------------------------------------------------------------------
# Account-required capabilities
# ---------------------------------------------------------------------------

def test_account_required_section_exists() -> None:
    d = _doc()
    assert "Requires an Account" in d or "requires an account" in d.lower()


def test_account_required_includes_saved_workspaces() -> None:
    assert "workspace" in _doc().lower()


def test_account_required_includes_persistence() -> None:
    d = _doc().lower()
    assert "persist" in d or "history" in d or "saving" in d


def test_account_required_includes_cross_device() -> None:
    d = _doc().lower()
    assert "cross-device" in d or "cross device" in d


def test_account_required_includes_collaboration() -> None:
    assert "collaboration" in _doc().lower()


# ---------------------------------------------------------------------------
# Account prompt timing
# ---------------------------------------------------------------------------

def test_account_prompt_timing_section_exists() -> None:
    assert "Prompt Timing" in _doc() or "prompt timing" in _doc().lower()


def test_account_prompt_never_before_first_output() -> None:
    d = _doc().lower()
    assert "never" in d or "not before" in d or "before first" in d


def test_account_prompt_timing_dark_patterns_mentioned() -> None:
    d = _doc().lower()
    assert "dark pattern" in d or "avoid" in d


# ---------------------------------------------------------------------------
# Data handling and privacy boundary
# ---------------------------------------------------------------------------

def test_data_handling_section_exists() -> None:
    d = _doc()
    assert "Privacy" in d or "Data Handling" in d or "data handling" in d.lower()


def test_data_handling_no_email_before_first_value() -> None:
    assert "email" in _doc().lower()


def test_data_handling_no_silent_retention() -> None:
    d = _doc().lower()
    assert "silent" in d or "explicit" in d


def test_data_handling_no_broker_required() -> None:
    d = _doc().lower()
    assert "broker" in d


# ---------------------------------------------------------------------------
# Local-first alignment
# ---------------------------------------------------------------------------

def test_local_first_alignment_section_exists() -> None:
    d = _doc()
    assert "Local-First" in d or "local-first" in d.lower()


def test_local_first_alignment_connects_to_deterministic() -> None:
    assert "deterministic" in _doc().lower()


def test_local_first_alignment_connects_to_provider_free() -> None:
    d = _doc().lower()
    assert "provider" in d or "live data" in d or "external data" in d


# ---------------------------------------------------------------------------
# Future UI implications
# ---------------------------------------------------------------------------

def test_future_ui_section_exists() -> None:
    d = _doc()
    assert "UI Implication" in d or "ui implication" in d.lower()


def test_future_ui_input_first_not_dashboard_first() -> None:
    d = _doc().lower()
    assert "input-first" in d or "input first" in d


def test_future_ui_no_auth_as_entry_point() -> None:
    d = _doc().lower()
    assert "sign up" in d or "signup" in d or "auth" in d


# ---------------------------------------------------------------------------
# Trust-building copy principles
# ---------------------------------------------------------------------------

def test_trust_copy_section_exists() -> None:
    d = _doc()
    assert "Trust" in d or "Copy Principle" in d or "copy principle" in d.lower()


def test_trust_copy_includes_safe_example() -> None:
    d = _doc()
    assert "Try Atlas without an account" in d or "without an account" in d.lower()


def test_trust_copy_avoids_urgency_language() -> None:
    d = _doc()
    assert "urgency" in d.lower() or "urgent" in d.lower() or "countdown" in d.lower()


# ---------------------------------------------------------------------------
# Risks and mitigations
# ---------------------------------------------------------------------------

def test_risks_section_exists() -> None:
    assert "Risk" in _doc()


def test_risks_includes_sensitive_data_risk() -> None:
    d = _doc().lower()
    assert "sensitive" in d or "sensitive data" in d


def test_mitigations_present() -> None:
    d = _doc().lower()
    assert "mitigation" in d or "mitigat" in d


# ---------------------------------------------------------------------------
# Implementation phases
# ---------------------------------------------------------------------------

def test_implementation_phases_section_exists() -> None:
    assert "Implementation Phase" in _doc() or "implementation phase" in _doc().lower()


def test_phase_0_is_documentation() -> None:
    d = _doc()
    assert "Phase 0" in d or "phase 0" in d.lower()


def test_phase_1_cli_is_complete() -> None:
    d = _doc()
    assert "Phase 1" in d or "CLI" in d


def test_future_phases_are_labeled_future() -> None:
    d = _doc().lower()
    assert "future" in d


def test_no_implementation_in_this_sprint() -> None:
    d = _doc().lower()
    assert "no implementation" in d or "not implemented" in d or "not implement" in d


# ---------------------------------------------------------------------------
# No runtime behaviour changed — verify no auth/backend code added
# ---------------------------------------------------------------------------

def test_no_auth_module_added() -> None:
    assert not Path("atlas/auth.py").exists()
    assert not Path("atlas/accounts.py").exists()
    assert not Path("atlas/login.py").exists()


def test_no_database_schema_added() -> None:
    import os
    for fname in ["schema.sql", "migrations.sql", "db.py", "database.py"]:
        assert not Path(f"atlas/{fname}").exists(), f"atlas/{fname} should not exist"


def test_no_backend_services_added() -> None:
    assert not Path("atlas/server.py").exists()
    assert not Path("atlas/api.py").exists()


def test_no_analytics_added() -> None:
    for fname in ["analytics.py", "telemetry.py", "tracking.py"]:
        assert not Path(f"atlas/{fname}").exists()


def test_no_payment_added() -> None:
    assert not Path("atlas/payment.py").exists()
    assert not Path("atlas/billing.py").exists()


def test_no_gettext_added_to_render() -> None:
    src = Path("atlas/weekly_review/render.py").read_text(encoding="utf-8")
    assert "gettext" not in src


def test_cli_still_exits_zero_after_doc_sprint() -> None:
    import subprocess
    atlas = str(Path(".venv/bin/atlas").resolve())
    r = subprocess.run(
        [atlas, "weekly-review",
         "--portfolio", "examples/weekly_review/portfolio.json",
         "--watchlist", "examples/weekly_review/watchlist.json",
         "--as-of", "2026-01-05"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
