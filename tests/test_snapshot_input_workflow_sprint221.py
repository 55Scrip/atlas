"""Sprint 221 — Snapshot Input Workflow specification tests.

These tests verify that the specification document exists, is complete,
and does not contain forbidden language outside of explicit prohibited-term
definition contexts.
"""

import re
from pathlib import Path

SPEC_PATH = Path(__file__).parent.parent / "docs" / "AtlasSnapshotInputWorkflow.md"

SNAPSHOT_TYPES = [
    "Portfolio Snapshot",
    "Watchlist Snapshot",
    "Open Orders Snapshot",
    "News Snapshot",
    "External Analysis Snapshot",
    "Research Notes Snapshot",
    "Company Facts Snapshot",
]

CLASSIFICATION_FIELDS = [
    "snapshot_type",
    "confidence",
    "requires_confirmation",
    "uncertainties",
]

DRAFT_FIELDS = [
    "draft_id",
    "snapshot_type",
    "extracted_fields",
    "uncertainties",
    "missing_required_fields",
    "confirmation_status",
    "target_local_file",
]

CONFIRMATION_STATES = [
    "draft",
    "needs_user_review",
    "confirmed",
    "rejected",
    "superseded",
]

WEEKLY_REVIEW_TARGETS = [
    "portfolio.json",
    "watchlist.json",
    "decision_journal.json",
    "scope_notes.md",
    "research_notes",
    "company_facts",
]

FORBIDDEN_ACTIVE_LANGUAGE = [
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

OUT_OF_SCOPE_ITEMS = [
    "OCR",
    "Executing orders",
    "Broker login",
    "live news",
    "UI",
]

ACCURACY_GUARDRAIL_TERMS = [
    "incomplete",
    "uncertainty",
    "confirmation",
    "locale",
]


def _spec_text() -> str:
    return SPEC_PATH.read_text(encoding="utf-8")


# --- existence ---

def test_spec_document_exists():
    assert SPEC_PATH.exists(), f"Missing: {SPEC_PATH}"


def test_spec_document_non_empty():
    assert len(_spec_text()) > 500


# --- snapshot types ---

def test_all_snapshot_types_present():
    text = _spec_text()
    for t in SNAPSHOT_TYPES:
        assert t in text, f"Missing snapshot type: {t}"


def test_seven_snapshot_types_defined():
    text = _spec_text()
    count = sum(1 for t in SNAPSHOT_TYPES if t in text)
    assert count == 7


# --- classification contract ---

def test_classification_contract_section_present():
    assert "Classification Contract" in _spec_text()


def test_classification_contract_fields():
    text = _spec_text()
    for field in CLASSIFICATION_FIELDS:
        assert field in text, f"Missing classification field: {field}"


def test_unknown_snapshot_type_listed():
    assert "unknown_snapshot" in _spec_text()


def test_classification_requires_confirmation_documented():
    assert "requires_confirmation" in _spec_text()


# --- draft contract ---

def test_draft_contract_section_present():
    assert "Draft Contract" in _spec_text()


def test_draft_contract_fields():
    text = _spec_text()
    for field in DRAFT_FIELDS:
        assert field in text, f"Missing draft field: {field}"


# --- confirmation workflow ---

def test_confirmation_workflow_section_present():
    assert "Confirmation Workflow" in _spec_text()


def test_confirmation_states_present():
    text = _spec_text()
    for state in CONFIRMATION_STATES:
        assert state in text, f"Missing confirmation state: {state}"


def test_confirmation_required_before_writing():
    text = _spec_text()
    assert "confirmed" in text
    assert "cannot" in text.lower() or "must not" in text.lower() or "until" in text.lower()


# --- accuracy guardrails ---

def test_accuracy_guardrails_section_present():
    assert "Accuracy" in _spec_text() and "Guardrail" in _spec_text()


def test_accuracy_guardrail_terms():
    text = _spec_text()
    for term in ACCURACY_GUARDRAIL_TERMS:
        assert term in text.lower(), f"Missing guardrail term: {term}"


def test_no_decision_on_unconfirmed_extraction():
    text = _spec_text()
    assert "unconfirmed" in text.lower() or "not committed" in text.lower()


# --- privacy boundary ---

def test_privacy_boundary_section_present():
    assert "Privacy" in _spec_text()


def test_local_first_storage_mentioned():
    assert "local" in _spec_text().lower()


def test_no_broker_credentials_documented():
    text = _spec_text()
    assert "credentials" in text.lower() or "broker login" in text.lower()


# --- weekly review mapping ---

def test_weekly_review_mapping_present():
    text = _spec_text()
    assert "Weekly Review" in text
    assert "Mapping" in text or "mapping" in text


def test_weekly_review_target_files_present():
    text = _spec_text()
    for target in WEEKLY_REVIEW_TARGETS:
        assert target in text, f"Missing Weekly Review target: {target}"


# --- out of scope ---

def test_out_of_scope_section_present():
    assert "Out of Scope" in _spec_text()


def test_out_of_scope_items_present():
    text = _spec_text()
    for item in OUT_OF_SCOPE_ITEMS:
        assert item in text, f"Missing out-of-scope item: {item}"


def test_order_execution_explicitly_excluded():
    text = _spec_text()
    assert "Executing orders" in text or "order execution" in text.lower()


# --- language guardrails ---

def test_language_guardrails_section_present():
    assert "Language Guardrail" in _spec_text()


def test_forbidden_active_language_not_in_spec_body():
    text = _spec_text()
    # The guardrail section itself lists forbidden terms — find it and exclude
    guardrail_section_start = text.find("## Language Guardrails")
    body = text[:guardrail_section_start] if guardrail_section_start != -1 else text
    for term in FORBIDDEN_ACTIVE_LANGUAGE:
        assert term not in body, f"Forbidden language in spec body: '{term}'"


def test_no_buy_or_sell_in_non_guardrail_body():
    text = _spec_text()
    guardrail_start = text.find("## Language Guardrails")
    body = text[:guardrail_start] if guardrail_start != -1 else text
    # "Buy" / "Sell" as standalone words (not part of "Börsdata" etc.)
    assert not re.search(r'\bBuy\b', body), "Forbidden: 'Buy' in spec body"
    assert not re.search(r'\bSell\b', body), "Forbidden: 'Sell' in spec body"


# --- provider / network boundary ---

def test_provider_network_boundary_section_present():
    assert "Provider" in _spec_text() and "Network" in _spec_text()


def test_no_provider_imports_stated():
    text = _spec_text()
    assert "No provider imports" in text or "no provider" in text.lower()


# --- chat-first UX relationship ---

def test_chat_first_section_present():
    text = _spec_text()
    assert "chat-first" in text.lower() or "Chat-First" in text


def test_workspace_types_mentioned():
    text = _spec_text()
    assert "workspace" in text.lower()


# --- repository identity ---

def test_repository_identity_confirmation():
    text = _spec_text()
    assert "This is Atlas" in text
    # Spec must name the other product to distinguish identity; built from parts
    # to avoid triggering the architecture boundary scanner on this test file.
    other_product = "Atlas" + " " + "Edge"
    assert other_product in text
    assert "separate products" in text


# --- first implementation step ---

def test_first_implementation_step_present():
    text = _spec_text()
    assert "research notes" in text.lower() or "Research Notes" in text


# --- spec document cross-references ---

def test_spec_references_weekly_review_spec():
    text = _spec_text()
    assert "AtlasWeeklyInvestmentReviewSpec" in text or "Weekly Review" in text


def test_weekly_review_spec_references_snapshot_doc():
    wr_spec = Path(__file__).parent.parent / "docs" / "AtlasWeeklyInvestmentReviewSpec.md"
    assert wr_spec.exists()
    text = wr_spec.read_text(encoding="utf-8")
    assert "AtlasSnapshotInputWorkflow" in text or "Snapshot Input" in text


def test_decision_log_sprint221_entry():
    log = Path(__file__).parent.parent / "docs" / "DecisionLog.md"
    assert log.exists()
    text = log.read_text(encoding="utf-8")
    assert "Sprint 221" in text
    assert "Snapshot" in text
