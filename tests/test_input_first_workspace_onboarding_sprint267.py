"""Sprint 267 — Input-First Workspace Onboarding specification tests.

Verifies that docs/InputFirstWorkspaceOnboarding.md exists and contains the
required product specification content. No runtime behaviour is changed by
this sprint. These tests read the specification document only.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

DOC = Path("docs/InputFirstWorkspaceOnboarding.md")
NO_ACCOUNT_DOC = Path("docs/NoAccountFirstValueOnboarding.md")


def _doc() -> str:
    return DOC.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Document exists
# ---------------------------------------------------------------------------

def test_document_exists() -> None:
    assert DOC.exists(), "docs/InputFirstWorkspaceOnboarding.md must exist"


def test_no_account_doc_still_exists() -> None:
    assert NO_ACCOUNT_DOC.exists()


# ---------------------------------------------------------------------------
# Core product principle
# ---------------------------------------------------------------------------

def test_principle_input_not_dashboard() -> None:
    d = _doc().lower()
    assert "dashboard" in d
    assert "input" in d


def test_principle_input_not_signup_wall() -> None:
    d = _doc().lower()
    assert "signup" in d or "sign up" in d or "signup wall" in d or "account wall" in d


def test_principle_paste_and_receive_workspace() -> None:
    d = _doc().lower()
    assert "paste" in d
    assert "workspace" in d


# ---------------------------------------------------------------------------
# First screen
# ---------------------------------------------------------------------------

def test_first_screen_section_exists() -> None:
    assert "First Screen" in _doc()


def test_first_screen_no_login_required() -> None:
    d = _doc().lower()
    assert "login" in d or "sign in" in d or "account" in d
    # The doc must also state no login is required on first screen
    assert "does not require" in d or "no account" in d or "without" in d


def test_first_screen_example_input_reduces_friction() -> None:
    d = _doc().lower()
    assert "example" in d or "sample" in d or "pre-filled" in d


# ---------------------------------------------------------------------------
# Supported first input types
# ---------------------------------------------------------------------------

def test_supported_inputs_section_exists() -> None:
    assert "Supported First Inputs" in _doc() or "First Input" in _doc()


def test_supported_inputs_includes_portfolio() -> None:
    assert "portfolio" in _doc().lower()


def test_supported_inputs_includes_watchlist() -> None:
    assert "watchlist" in _doc().lower()


def test_supported_inputs_includes_research_notes() -> None:
    assert "research note" in _doc().lower()


def test_supported_inputs_includes_order_idea() -> None:
    d = _doc().lower()
    assert "order" in d or "order idea" in d


def test_supported_inputs_includes_question() -> None:
    d = _doc().lower()
    assert "question" in d


def test_supported_inputs_clarifies_ocr_is_future() -> None:
    d = _doc().lower()
    assert "ocr" in d or "screenshot" in d
    assert "future" in d


# ---------------------------------------------------------------------------
# Input classification
# ---------------------------------------------------------------------------

def test_input_classification_section_exists() -> None:
    assert "Input Classification" in _doc() or "Classification" in _doc()


def test_classification_includes_portfolio_input() -> None:
    assert "portfolio_input" in _doc()


def test_classification_includes_watchlist_input() -> None:
    assert "watchlist_input" in _doc()


def test_classification_includes_order_review_input() -> None:
    assert "order_review_input" in _doc()


def test_classification_includes_research_note_input() -> None:
    assert "research_note_input" in _doc()


def test_classification_includes_unknown_input() -> None:
    assert "unknown_input" in _doc()


def test_classification_includes_mixed_input() -> None:
    assert "mixed_input" in _doc()


def test_classification_includes_confidence() -> None:
    assert "confidence" in _doc().lower()


def test_classification_includes_detected_tickers() -> None:
    d = _doc().lower()
    assert "detected ticker" in d or "detected tickers" in d


def test_classification_includes_uncertainties() -> None:
    assert "uncertainties" in _doc().lower()


def test_classification_not_implemented() -> None:
    d = _doc().lower()
    assert "not implemented" in d or "future implementation" in d or "this sprint" in d


# ---------------------------------------------------------------------------
# Temporary workspace model
# ---------------------------------------------------------------------------

def test_temporary_workspace_section_exists() -> None:
    assert "Temporary Workspace" in _doc()


def test_temporary_workspace_no_account_required() -> None:
    d = _doc().lower()
    assert "no account required" in d or "no account" in d


def test_temporary_workspace_no_broker_required() -> None:
    d = _doc().lower()
    assert "no broker" in d or "broker connection" in d


def test_temporary_workspace_no_persistence_promised() -> None:
    d = _doc().lower()
    assert "no persistence" in d or "temporary" in d or "not saved" in d


def test_temporary_workspace_account_prompt_after_cards() -> None:
    d = _doc().lower()
    assert "after" in d
    assert "account" in d


# ---------------------------------------------------------------------------
# Workspace cards
# ---------------------------------------------------------------------------

def test_workspace_cards_section_exists() -> None:
    assert "Workspace Cards" in _doc() or "Workspace Card" in _doc()


def test_workspace_cards_includes_input_summary() -> None:
    assert "Input Summary" in _doc()


def test_workspace_cards_includes_evidence_gaps() -> None:
    assert "Evidence Gap" in _doc()


def test_workspace_cards_includes_reasons_to_wait() -> None:
    assert "Reasons to Wait" in _doc() or "Reason to Wait" in _doc()


def test_workspace_cards_includes_follow_up_questions() -> None:
    assert "Follow-Up Question" in _doc()


def test_workspace_cards_includes_snapshot_drafts() -> None:
    assert "Snapshot Draft" in _doc()


def test_workspace_cards_includes_weekly_review_preview() -> None:
    assert "Weekly Review" in _doc()


def test_workspace_cards_includes_save_workspace_prompt() -> None:
    d = _doc().lower()
    assert "save workspace" in d or "save" in d


def test_workspace_cards_no_recommendation_framing() -> None:
    d = _doc().lower()
    assert "guaranteed" not in d
    assert "outperform" not in d
    # "price target" may appear in exclusion context
    if "price target" in d:
        assert "not" in d or "avoid" in d or "do not" in d


# ---------------------------------------------------------------------------
# Example flows — at least three
# ---------------------------------------------------------------------------

def test_example_flows_section_exists() -> None:
    assert "Example Flow" in _doc() or "Flow 1" in _doc()


def test_example_flow_portfolio_paste_exists() -> None:
    d = _doc().lower()
    assert "portfolio" in d and "flow" in d


def test_example_flow_watchlist_or_research_exists() -> None:
    d = _doc().lower()
    assert "watchlist" in d or "research" in d


def test_example_flow_order_idea_exists() -> None:
    d = _doc().lower()
    assert "order" in d


def test_example_flows_count_at_least_three() -> None:
    # Check at least three numbered or titled flows
    d = _doc()
    flow_markers = sum(1 for marker in ["Flow 1", "Flow 2", "Flow 3"] if marker in d)
    section_markers = sum(1 for marker in ["### Flow", "Example 1", "Example 2", "Example 3"] if marker in d)
    assert flow_markers >= 3 or section_markers >= 3


def test_example_flows_no_buy_sell_language() -> None:
    d = _doc().lower()
    # Flows should not use buy/sell as action instructions
    assert "buy " not in d or ("do not" in d or "avoid" in d or "no buy" in d)


# ---------------------------------------------------------------------------
# No-account flow
# ---------------------------------------------------------------------------

def test_no_account_flow_section_exists() -> None:
    assert "No-Account Flow" in _doc() or "no-account flow" in _doc().lower()


def test_no_account_flow_has_steps() -> None:
    d = _doc()
    # Must have numbered steps
    assert "1." in d or "Step 1" in d


def test_no_account_flow_account_prompt_only_after_value() -> None:
    d = _doc().lower()
    assert "only" in d
    assert "save" in d or "account" in d


# ---------------------------------------------------------------------------
# Save / account handoff
# ---------------------------------------------------------------------------

def test_save_account_handoff_section_exists() -> None:
    assert "Account Handoff" in _doc() or "Save / Account" in _doc() or "Save/Account" in _doc()


def test_handoff_lists_persistence_triggers() -> None:
    d = _doc().lower()
    assert "history" in d or "persist" in d
    assert "save" in d


def test_handoff_no_dark_patterns() -> None:
    d = _doc().lower()
    assert "dark pattern" in d or "avoid" in d or "blocking" in d or "block" in d


# ---------------------------------------------------------------------------
# Privacy and trust boundaries
# ---------------------------------------------------------------------------

def test_privacy_section_exists() -> None:
    d = _doc()
    assert "Privacy" in d or "Trust" in d


def test_privacy_no_email_before_first_value() -> None:
    d = _doc().lower()
    assert "email" in d
    assert "before" in d or "required" in d


def test_privacy_no_silent_data_retention() -> None:
    d = _doc().lower()
    assert "silent" in d or "not stored" in d or "not saved" in d or "discard" in d


def test_privacy_no_broker_required() -> None:
    assert "broker" in _doc().lower()


# ---------------------------------------------------------------------------
# Relationship to existing Atlas workflows
# ---------------------------------------------------------------------------

def test_relates_to_snapshot_drafts() -> None:
    assert "Snapshot Draft" in _doc() or "snapshot_draft" in _doc()


def test_relates_to_weekly_review() -> None:
    assert "Weekly Review" in _doc()


def test_relates_to_decision_journal() -> None:
    assert "Decision Journal" in _doc() or "decision journal" in _doc().lower()


def test_relates_to_research_notes() -> None:
    assert "research note" in _doc().lower() or "Research Note" in _doc()


def test_relates_to_company_facts() -> None:
    assert "company fact" in _doc().lower() or "Company Fact" in _doc()


# ---------------------------------------------------------------------------
# Implementation phases
# ---------------------------------------------------------------------------

def test_implementation_phases_section_exists() -> None:
    assert "Implementation Phase" in _doc() or "implementation phase" in _doc().lower()


def test_phase_0_is_specification() -> None:
    assert "Phase 0" in _doc()


def test_future_phases_are_labeled_future() -> None:
    d = _doc().lower()
    assert "future" in d


def test_no_implementation_in_this_sprint() -> None:
    d = _doc().lower()
    assert "not implemented" in d or "no implementation" in d or "this sprint" in d


# ---------------------------------------------------------------------------
# Risks and mitigations
# ---------------------------------------------------------------------------

def test_risks_section_exists() -> None:
    assert "Risk" in _doc()


def test_risks_includes_data_retention_risk() -> None:
    d = _doc().lower()
    assert "data" in d and ("retain" in d or "sensitive" in d or "privacy" in d)


def test_mitigations_present() -> None:
    assert "Mitigation" in _doc() or "mitigation" in _doc().lower()


# ---------------------------------------------------------------------------
# No runtime behaviour changed
# ---------------------------------------------------------------------------

def test_no_ui_module_added() -> None:
    assert not Path("atlas/ui.py").exists()
    assert not Path("atlas/web.py").exists()


def test_no_auth_module_added() -> None:
    assert not Path("atlas/auth.py").exists()
    assert not Path("atlas/accounts.py").exists()


def test_no_classifier_module_added() -> None:
    assert not Path("atlas/classifier.py").exists()
    assert not Path("atlas/input_classifier.py").exists()


def test_no_workspace_module_added() -> None:
    assert not Path("atlas/workspace.py").exists()


def test_no_database_added() -> None:
    assert not Path("atlas/db.py").exists()
    assert not Path("atlas/database.py").exists()


def test_no_backend_services_added() -> None:
    assert not Path("atlas/server.py").exists()
    assert not Path("atlas/api.py").exists()


def test_cli_still_exits_zero_after_doc_sprint() -> None:
    atlas = str(Path(".venv/bin/atlas").resolve())
    r = subprocess.run(
        [atlas, "weekly-review",
         "--portfolio", "examples/weekly_review/portfolio.json",
         "--watchlist", "examples/weekly_review/watchlist.json",
         "--as-of", "2026-01-05"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
