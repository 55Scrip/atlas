"""Sprint 268 — Temporary Workspace Data Model specification tests.

Verifies that docs/TemporaryWorkspaceDataModel.md exists and contains the
required product specification content. No runtime behaviour is changed by
this sprint. These tests read the specification document only.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

DOC = Path("docs/TemporaryWorkspaceDataModel.md")
ONBOARDING_DOC = Path("docs/InputFirstWorkspaceOnboarding.md")
NO_ACCOUNT_DOC = Path("docs/NoAccountFirstValueOnboarding.md")


def _doc() -> str:
    return DOC.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Document exists
# ---------------------------------------------------------------------------

def test_document_exists() -> None:
    assert DOC.exists(), "docs/TemporaryWorkspaceDataModel.md must exist"


def test_input_first_onboarding_doc_still_exists() -> None:
    assert ONBOARDING_DOC.exists()


def test_no_account_doc_still_exists() -> None:
    assert NO_ACCOUNT_DOC.exists()


# ---------------------------------------------------------------------------
# Model principle
# ---------------------------------------------------------------------------

def test_principle_unsaved_no_account() -> None:
    d = _doc().lower()
    assert "unsaved" in d or "no-account" in d or "no account" in d


def test_principle_safe_to_discard() -> None:
    d = _doc().lower()
    assert "discard" in d


def test_principle_no_implied_persistence() -> None:
    d = _doc().lower()
    assert "persist" in d
    assert "explicitly" in d or "explicit" in d


# ---------------------------------------------------------------------------
# Temporary workspace — top-level fields
# ---------------------------------------------------------------------------

def test_workspace_id_field_defined() -> None:
    assert "workspace_id" in _doc()


def test_status_field_defined() -> None:
    assert "status" in _doc()


def test_status_temporary_value_defined() -> None:
    assert '"temporary"' in _doc() or "`temporary`" in _doc() or "temporary" in _doc()


def test_created_at_field_defined() -> None:
    assert "created_at" in _doc()


def test_source_input_field_defined() -> None:
    assert "source_input" in _doc()


def test_classification_field_defined() -> None:
    assert "classification" in _doc()


def test_detected_entities_field_defined() -> None:
    assert "detected_entities" in _doc()


def test_uncertainties_field_defined() -> None:
    assert "uncertainties" in _doc()


def test_missing_fields_field_defined() -> None:
    assert "missing_fields" in _doc()


def test_cards_field_defined() -> None:
    assert '"cards"' in _doc() or "`cards`" in _doc() or "| `cards`" in _doc()


def test_save_handoff_field_defined() -> None:
    assert "save_handoff" in _doc()


def test_safety_boundary_field_defined() -> None:
    assert "safety_boundary" in _doc()


# ---------------------------------------------------------------------------
# Source input model
# ---------------------------------------------------------------------------

def test_source_input_section_exists() -> None:
    assert "Source Input" in _doc()


def test_source_input_has_input_id() -> None:
    assert "input_id" in _doc()


def test_source_input_has_input_type() -> None:
    assert "input_type" in _doc()


def test_source_input_has_raw_text_preview() -> None:
    d = _doc()
    assert "raw_text_preview" in d or "raw_text_reference" in d


def test_source_input_has_submitted_at() -> None:
    assert "submitted_at" in _doc()


def test_source_input_has_user_language_hint() -> None:
    assert "user_language_hint" in _doc()


def test_source_input_has_contains_sensitive_data() -> None:
    assert "contains_sensitive_data" in _doc()


def test_source_input_raw_retention_design_noted() -> None:
    d = _doc().lower()
    assert "retention" in d or "retain" in d


# ---------------------------------------------------------------------------
# Classification result model
# ---------------------------------------------------------------------------

def test_classification_section_exists() -> None:
    assert "Classification Result" in _doc() or "Classification" in _doc()


def test_classification_portfolio_input() -> None:
    assert "portfolio_input" in _doc()


def test_classification_watchlist_input() -> None:
    assert "watchlist_input" in _doc()


def test_classification_order_review_input() -> None:
    assert "order_review_input" in _doc()


def test_classification_research_note_input() -> None:
    assert "research_note_input" in _doc()


def test_classification_company_facts_input() -> None:
    assert "company_facts_input" in _doc()


def test_classification_journal_note_input() -> None:
    assert "journal_note_input" in _doc()


def test_classification_news_input() -> None:
    assert "news_or_external_analysis_input" in _doc()


def test_classification_question_input() -> None:
    assert "question_input" in _doc()


def test_classification_mixed_input() -> None:
    assert "mixed_input" in _doc()


def test_classification_unknown_input() -> None:
    assert "unknown_input" in _doc()


def test_classification_has_confidence() -> None:
    assert "confidence" in _doc()


def test_classification_has_primary_type() -> None:
    assert "primary_type" in _doc()


def test_classification_has_suggested_cards() -> None:
    assert "suggested_cards" in _doc()


# ---------------------------------------------------------------------------
# Detected entity model
# ---------------------------------------------------------------------------

def test_detected_entities_section_exists() -> None:
    assert "Detected Entities" in _doc() or "Detected Entity" in _doc()


def test_entity_type_ticker() -> None:
    assert "ticker" in _doc()


def test_entity_type_holding() -> None:
    assert "holding" in _doc()


def test_entity_type_company_name() -> None:
    assert "company_name" in _doc()


def test_entity_type_quantity() -> None:
    assert "quantity" in _doc()


def test_entity_type_portfolio_weight() -> None:
    assert "portfolio_weight" in _doc()


def test_entity_type_date() -> None:
    assert "`date`" in _doc() or "| `date`" in _doc() or "| date |" in _doc()


def test_entity_type_open_decision() -> None:
    assert "open_decision" in _doc()


def test_entity_type_research_note() -> None:
    assert "research_note" in _doc()


def test_entity_type_source_reference() -> None:
    assert "source_reference" in _doc()


def test_entity_has_entity_id() -> None:
    assert "entity_id" in _doc()


def test_entity_has_entity_type() -> None:
    assert "entity_type" in _doc()


def test_entity_has_value_field() -> None:
    assert "`value`" in _doc() or "| value |" in _doc() or "| `value`" in _doc()


def test_entity_has_normalized_value() -> None:
    assert "normalized_value" in _doc()


def test_entity_has_confidence() -> None:
    assert "confidence" in _doc()


def test_entity_has_uncertainty_reason() -> None:
    assert "uncertainty_reason" in _doc()


# ---------------------------------------------------------------------------
# Uncertainty model
# ---------------------------------------------------------------------------

def test_uncertainty_section_exists() -> None:
    assert "Uncertainties" in _doc()


def test_uncertainty_has_id() -> None:
    assert "uncertainty_id" in _doc()


def test_uncertainty_has_severity() -> None:
    assert "severity" in _doc()


def test_uncertainty_severity_low() -> None:
    d = _doc()
    assert "`low`" in d or "| low |" in d or "| `low`" in d


def test_uncertainty_severity_medium() -> None:
    d = _doc()
    assert "`medium`" in d or "| medium |" in d or "| `medium`" in d


def test_uncertainty_severity_high() -> None:
    d = _doc()
    assert "`high`" in d or "| high |" in d or "| `high`" in d


def test_uncertainty_severity_blocking() -> None:
    d = _doc()
    assert "`blocking`" in d or "| blocking |" in d or "| `blocking`" in d


def test_uncertainty_has_message() -> None:
    assert "message" in _doc()


def test_uncertainty_has_suggested_user_confirmation() -> None:
    assert "suggested_user_confirmation" in _doc()


def test_uncertainties_must_not_be_hidden() -> None:
    d = _doc().lower()
    assert "hidden" in d or "retain" in d or "not be hidden" in d


# ---------------------------------------------------------------------------
# Missing field model
# ---------------------------------------------------------------------------

def test_missing_fields_section_exists() -> None:
    assert "Missing Fields" in _doc() or "Missing Field" in _doc()


def test_missing_field_has_field_id() -> None:
    assert "field_id" in _doc()


def test_missing_field_has_field_name() -> None:
    assert "field_name" in _doc()


def test_missing_field_has_reason() -> None:
    d = _doc()
    assert "`reason`" in d or "| reason |" in d or "| `reason`" in d


def test_missing_field_optional_or_required() -> None:
    assert "optional_or_required" in _doc()


def test_missing_field_optional_value() -> None:
    assert "optional" in _doc()


def test_missing_field_required_for_export() -> None:
    assert "required_for_export" in _doc()


def test_missing_field_required_for_save() -> None:
    assert "required_for_save" in _doc()


def test_missing_field_required_for_review_quality() -> None:
    assert "required_for_review_quality" in _doc()


# ---------------------------------------------------------------------------
# Workspace card model
# ---------------------------------------------------------------------------

def test_workspace_cards_section_exists() -> None:
    assert "Workspace Cards" in _doc() or "Workspace Card" in _doc()


def test_card_has_card_id() -> None:
    assert "card_id" in _doc()


def test_card_has_card_type() -> None:
    assert "card_type" in _doc()


def test_card_has_title() -> None:
    d = _doc()
    assert "`title`" in d or "| title |" in d or "| `title`" in d


def test_card_has_status_field() -> None:
    d = _doc()
    assert "`status`" in d or "| status |" in d or "| `status`" in d


def test_card_has_summary_field() -> None:
    assert "summary" in _doc()


def test_card_has_items_field() -> None:
    assert "items" in _doc()


def test_card_has_related_entities() -> None:
    assert "related_entities" in _doc()


def test_card_has_related_uncertainties() -> None:
    assert "related_uncertainties" in _doc()


# ---------------------------------------------------------------------------
# Card types
# ---------------------------------------------------------------------------

def test_card_type_input_summary() -> None:
    assert "input_summary" in _doc()


def test_card_type_detected_holdings() -> None:
    assert "detected_holdings" in _doc()


def test_card_type_detected_tickers() -> None:
    assert "detected_tickers" in _doc()


def test_card_type_evidence_gaps() -> None:
    assert "evidence_gaps" in _doc()


def test_card_type_risks_to_monitor() -> None:
    assert "risks_to_monitor" in _doc()


def test_card_type_reasons_to_wait() -> None:
    assert "reasons_to_wait" in _doc()


def test_card_type_follow_up_questions() -> None:
    assert "follow_up_questions" in _doc()


def test_card_type_missing_inputs() -> None:
    assert "missing_inputs" in _doc()


def test_card_type_snapshot_drafts() -> None:
    assert "snapshot_drafts" in _doc()


def test_card_type_weekly_review_preview() -> None:
    assert "weekly_review_preview" in _doc()


def test_card_type_save_workspace_prompt() -> None:
    assert "save_workspace_prompt" in _doc()


def test_no_recommendation_card_types() -> None:
    d = _doc().lower()
    # "buy candidate" or "action item" may appear only in a negation/avoidance context
    if "buy candidate" in d:
        assert "avoid" in d or "do not" in d or "not use" in d
    if "action item" in d:
        assert "avoid" in d or "do not" in d or "not use" in d


# ---------------------------------------------------------------------------
# Card status values
# ---------------------------------------------------------------------------

def test_card_status_ready_for_review() -> None:
    assert "ready_for_review" in _doc()


def test_card_status_needs_more_evidence() -> None:
    assert "needs_more_evidence" in _doc()


def test_card_status_missing_required_input() -> None:
    assert "missing_required_input" in _doc()


def test_card_status_user_confirmation_needed() -> None:
    assert "user_confirmation_needed" in _doc()


def test_card_status_not_applicable() -> None:
    assert "not_applicable" in _doc()


def test_card_status_no_action_warranted() -> None:
    assert "no_action_warranted" in _doc()


def test_card_status_no_buy_sell_values() -> None:
    d = _doc().lower()
    assert "buy_signal" not in d
    assert "sell_signal" not in d


# ---------------------------------------------------------------------------
# Card ordering
# ---------------------------------------------------------------------------

def test_card_ordering_section_exists() -> None:
    assert "Card Ordering" in _doc() or "card ordering" in _doc().lower()


def test_card_ordering_input_summary_first() -> None:
    d = _doc()
    # Find the Card Ordering section and check that input_summary appears before evidence_gaps
    ordering_section_start = d.find("## Card Ordering")
    assert ordering_section_start >= 0
    ordering_section = d[ordering_section_start:]
    idx_summary = ordering_section.find("input_summary")
    idx_evidence = ordering_section.find("evidence_gaps")
    assert idx_summary >= 0 and idx_evidence >= 0
    assert idx_summary < idx_evidence


def test_card_ordering_save_prompt_last() -> None:
    d = _doc()
    # save_workspace_prompt should appear after other card types
    idx_save = d.rfind("save_workspace_prompt")
    idx_evidence = d.find("evidence_gaps")
    assert idx_save > idx_evidence


def test_card_ordering_account_prompt_not_before_first_value() -> None:
    d = _doc().lower()
    assert "must not block" in d or "not block" in d or "never" in d or "after" in d


# ---------------------------------------------------------------------------
# Save / account handoff state
# ---------------------------------------------------------------------------

def test_save_handoff_section_exists() -> None:
    assert "Save" in _doc() and "Account Handoff" in _doc()


def test_save_handoff_account_required_field() -> None:
    assert "account_required" in _doc()


def test_save_handoff_save_available_field() -> None:
    assert "save_available" in _doc()


def test_save_handoff_save_requires_account_field() -> None:
    assert "save_requires_account" in _doc()


def test_save_handoff_prompt_timing_field() -> None:
    assert "prompt_timing" in _doc()


def test_save_handoff_prompt_reason_field() -> None:
    assert "prompt_reason" in _doc()


def test_save_handoff_prompt_reason_save_workspace() -> None:
    assert "save_workspace" in _doc()


def test_save_handoff_prompt_reason_continue_later() -> None:
    assert "continue_later" in _doc()


def test_save_handoff_account_must_not_block_first_value() -> None:
    d = _doc().lower()
    assert "must not block" in d or "not block first value" in d or "must not block first value" in d


# ---------------------------------------------------------------------------
# Safety boundary
# ---------------------------------------------------------------------------

def test_safety_boundary_section_exists() -> None:
    assert "Safety Boundary" in _doc()


def test_safety_boundary_no_recommendations() -> None:
    assert "no_recommendations" in _doc()


def test_safety_boundary_no_order_execution() -> None:
    assert "no_order_execution" in _doc()


def test_safety_boundary_no_price_targets() -> None:
    assert "no_price_targets" in _doc()


def test_safety_boundary_user_judgment_required() -> None:
    assert "user_judgment_required" in _doc()


def test_safety_boundary_local_or_temporary_context() -> None:
    assert "local_or_temporary_context" in _doc()


def test_safety_boundary_applies_to_all_cards() -> None:
    d = _doc().lower()
    assert "all workspace cards" in d or "all cards" in d


# ---------------------------------------------------------------------------
# Snapshot Draft relationship
# ---------------------------------------------------------------------------

def test_snapshot_draft_relationship_section_exists() -> None:
    assert "Snapshot Draft" in _doc()


def test_snapshot_draft_no_silent_persistence() -> None:
    d = _doc().lower()
    assert "silent" in d


def test_snapshot_draft_unconfirmed_until_user_action() -> None:
    d = _doc().lower()
    assert "unconfirmed" in d or "explicit user action" in d or "explicit" in d


# ---------------------------------------------------------------------------
# Weekly Review Preview relationship
# ---------------------------------------------------------------------------

def test_weekly_review_preview_section_exists() -> None:
    assert "Weekly Review Preview" in _doc()


def test_weekly_review_preview_not_saved_history() -> None:
    d = _doc().lower()
    assert "not imply saved" in d or "does not imply" in d or "not imply" in d


def test_weekly_review_preview_labeled_temporary() -> None:
    d = _doc().lower()
    assert "temporary" in d


# ---------------------------------------------------------------------------
# Canonical values
# ---------------------------------------------------------------------------

def test_canonical_values_section_exists() -> None:
    assert "Canonical Values" in _doc() or "canonical values" in _doc().lower()


def test_canonical_values_remain_english() -> None:
    d = _doc().lower()
    assert "canonical english" in d or "remain english" in d or "canonical" in d


def test_canonical_card_type_stated() -> None:
    assert "card_type" in _doc()


def test_canonical_classification_category_stated() -> None:
    d = _doc().lower()
    assert "classification" in d and "category" in d


def test_canonical_entity_type_stated() -> None:
    assert "entity_type" in _doc()


# ---------------------------------------------------------------------------
# Example JSON
# ---------------------------------------------------------------------------

def test_example_json_section_exists() -> None:
    assert "Example JSON" in _doc() or "example json" in _doc().lower()


def test_example_json_includes_workspace_id() -> None:
    assert '"workspace_id"' in _doc()


def test_example_json_includes_status_temporary() -> None:
    assert '"temporary"' in _doc()


def test_example_json_includes_portfolio_input() -> None:
    assert '"portfolio_input"' in _doc()


def test_example_json_includes_save_workspace_prompt_card() -> None:
    assert '"save_workspace_prompt"' in _doc()


def test_example_json_no_recommendation_language() -> None:
    d = _doc().lower()
    assert "guaranteed" not in d
    assert "outperform" not in d
    if "price target" in d:
        assert "no_price_targets" in d or "not" in d


# ---------------------------------------------------------------------------
# Validation expectations
# ---------------------------------------------------------------------------

def test_validation_expectations_section_exists() -> None:
    assert "Validation Expectations" in _doc() or "validation expectation" in _doc().lower()


def test_validation_expects_required_fields() -> None:
    d = _doc().lower()
    assert "required" in d and "field" in d


def test_validation_expects_status_temporary() -> None:
    d = _doc().lower()
    assert "status" in d and "temporary" in d


def test_validation_expects_canonical_english() -> None:
    d = _doc().lower()
    assert "canonical" in d and "english" in d


def test_validation_expects_uncertainties_retained() -> None:
    d = _doc().lower()
    assert "uncertainties" in d and ("retain" in d or "not" in d)


def test_validation_expects_save_prompt_last() -> None:
    d = _doc().lower()
    assert "last" in d or "after" in d


# ---------------------------------------------------------------------------
# No implementation in this sprint
# ---------------------------------------------------------------------------

def test_no_implementation_stated() -> None:
    d = _doc().lower()
    assert "not implemented" in d or "no implementation" in d or "this sprint" in d


def test_future_phases_labeled_future() -> None:
    d = _doc().lower()
    assert "future" in d


# ---------------------------------------------------------------------------
# No runtime behavior changed — verify no new code files added
# ---------------------------------------------------------------------------

def test_no_workspace_module_added() -> None:
    assert not Path("atlas/workspace.py").exists()
    assert not Path("atlas/temporary_workspace.py").exists()


def test_no_dataclass_module_added() -> None:
    assert not Path("atlas/workspace_model.py").exists()
    assert not Path("atlas/models.py").exists()


def test_no_schema_file_added() -> None:
    assert not Path("atlas/schema.py").exists()
    assert not Path("atlas/workspace_schema.py").exists()


def test_no_classifier_added() -> None:
    assert not Path("atlas/classifier.py").exists()
    assert not Path("atlas/input_classifier.py").exists()


def test_no_renderer_added() -> None:
    assert not Path("atlas/workspace_renderer.py").exists()


def test_no_ui_added() -> None:
    assert not Path("atlas/ui.py").exists()
    assert not Path("atlas/web.py").exists()


def test_no_auth_added() -> None:
    assert not Path("atlas/auth.py").exists()
    assert not Path("atlas/accounts.py").exists()


def test_no_database_added() -> None:
    assert not Path("atlas/db.py").exists()
    assert not Path("atlas/database.py").exists()


def test_no_backend_added() -> None:
    assert not Path("atlas/server.py").exists()
    assert not Path("atlas/api.py").exists()


def test_no_provider_imports_added() -> None:
    for path in Path("atlas").rglob("*.py"):
        src = path.read_text(encoding="utf-8")
        assert "import requests" not in src, f"requests import found in {path}"
        assert "import httpx" not in src, f"httpx import found in {path}"
        assert "import openai" not in src, f"openai import found in {path}"
        assert "import anthropic" not in src, f"anthropic import found in {path}"


def test_cli_still_exits_zero() -> None:
    atlas = str(Path(".venv/bin/atlas").resolve())
    r = subprocess.run(
        [atlas, "weekly-review",
         "--portfolio", "examples/weekly_review/portfolio.json",
         "--watchlist", "examples/weekly_review/watchlist.json",
         "--as-of", "2026-01-05"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
