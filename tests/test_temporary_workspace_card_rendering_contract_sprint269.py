"""Sprint 269 — Temporary Workspace Card Rendering Contract tests.

These tests verify the documentation contract only. Sprint 269 intentionally
does not add runtime card rendering, schemas, UI, persistence, providers, or
network integrations.
"""

from __future__ import annotations

import re
import ast
from pathlib import Path


DOC = Path("docs/TemporaryWorkspaceCardRenderingContract.md")
ATLAS_DIR = Path("atlas")

CARD_TYPES = [
    "input_summary",
    "detected_holdings",
    "detected_tickers",
    "portfolio_context",
    "watchlist_review",
    "open_decisions",
    "evidence_gaps",
    "risks_to_monitor",
    "reasons_to_wait",
    "follow_up_questions",
    "missing_inputs",
    "snapshot_drafts",
    "weekly_review_preview",
    "save_workspace_prompt",
]

SAFE_STATUSES = [
    "ready_for_review",
    "needs_more_evidence",
    "missing_required_input",
    "user_confirmation_needed",
    "not_applicable",
    "no_action_warranted",
    "decision_deferred",
]

REQUIRED_CARD_SUBSECTIONS = [
    "Purpose:",
    "Required fields:",
    "Display sections:",
    "Allowed statuses:",
    "Safety notes:",
]


def _doc() -> str:
    return DOC.read_text(encoding="utf-8")


def _card_section(card_type: str) -> str:
    doc = _doc()
    pattern = rf"### `{re.escape(card_type)}`(?P<body>.*?)(?=\n---\n\n### `|\n---\n\n## Example Rendered Cards)"
    match = re.search(pattern, doc, re.DOTALL)
    assert match, f"{card_type} must have its own rendering contract section"
    return match.group("body")


def test_document_exists() -> None:
    assert DOC.exists()


def test_document_states_specification_only_and_no_implementation() -> None:
    doc = _doc().lower()
    assert "specification only" in doc
    assert "no implementation is performed in this sprint" in doc
    assert "change runtime behavior" in doc
    assert "change cli behavior" in doc


def test_document_defines_rendering_principles() -> None:
    doc = _doc().lower()
    for phrase in [
        "surface structure, gaps, and questions",
        "do not create investment recommendations",
        "preserve user-provided content",
        "preserve canonical internal values",
        "make uncertainty visible",
        "make missing inputs visible",
        "show source references when available",
        "discarded unless explicitly saved",
    ]:
        assert phrase in doc


def test_document_defines_shared_card_layout() -> None:
    doc = _doc()
    for field in [
        '"title"',
        '"status_label"',
        '"summary"',
        '"items"',
        '"uncertainties"',
        '"missing_fields"',
        '"source_references"',
        '"next_prompt"',
    ]:
        assert field in doc


def test_document_defines_status_display() -> None:
    doc = _doc()
    for status in SAFE_STATUSES:
        assert status in doc
    for label in [
        "Ready for Review",
        "Needs More Evidence",
        "Missing Required Input",
        "User Confirmation Needed",
        "Not Applicable",
        "No Action Warranted",
        "Decision Deferred",
    ]:
        assert label in doc


def test_document_defines_uncertainty_missing_source_and_content_handling() -> None:
    doc = _doc().lower()
    for heading in [
        "## uncertainty display",
        "## missing field display",
        "## source reference display",
        "## user-provided content handling",
        "## canonical values",
    ]:
        assert heading in doc
    assert "do not hide it" in doc
    assert "do not fabricate default values" in doc
    assert "do not fabricate sources" in doc
    assert "pass through the rendering layer unchanged" in doc
    assert "must not be translated, aliased, or overloaded" in doc


def test_document_defines_safety_copy_rules() -> None:
    doc = _doc().lower()
    assert "## safety copy rules" in doc
    for unsafe_phrase in [
        "direct recommendation language",
        "transaction or execution instruction",
        "urgency language",
        "certainty or promise language",
        "price-target framing",
        "outperformance prediction",
        "personalized financial advice framing",
    ]:
        assert unsafe_phrase in doc
    for safe_phrase in [
        "needs more evidence",
        "reason to wait",
        "risk to monitor",
        "question to revisit",
        "decision deferred",
        "no action warranted",
        "user confirmation needed",
    ]:
        assert safe_phrase in doc


def test_document_covers_all_card_types() -> None:
    doc = _doc()
    for card_type in CARD_TYPES:
        assert f"### `{card_type}`" in doc


def test_each_card_type_defines_required_rendering_contract_parts() -> None:
    for card_type in CARD_TYPES:
        section = _card_section(card_type)
        for subsection in REQUIRED_CARD_SUBSECTIONS:
            assert subsection in section, f"{card_type} missing {subsection}"
        assert "Uncertainty handling:" in section
        assert "Missing field handling:" in section
        assert "Source reference handling:" in section


def test_document_includes_required_example_rendered_cards() -> None:
    doc = _doc()
    assert doc.count("### Example ") >= 3
    for title in [
        "Evidence Gaps Card",
        "Snapshot Drafts Card",
        "Save Workspace Prompt Card",
    ]:
        assert title in doc


def test_document_includes_validation_expectations() -> None:
    doc = _doc().lower().replace("`", "")
    assert "## validation expectations" in doc
    for expectation in [
        "every card has",
        "card_type is from known set",
        "status is allowed",
        "user content marked or traceable",
        "uncertainties retained",
        "missing fields retained",
        "source references preserved",
        "no card copy violates safety language rules",
    ]:
        assert expectation in doc


def test_no_runtime_temporary_workspace_rendering_code_added() -> None:
    forbidden_paths = [
        ATLAS_DIR / "temporary_workspace",
        ATLAS_DIR / "workspace_cards",
        ATLAS_DIR / "card_renderer.py",
        ATLAS_DIR / "temporary_workspace.py",
        ATLAS_DIR / "temporary_workspace_schema.py",
    ]
    assert not any(path.exists() for path in forbidden_paths)


def test_no_provider_or_network_imports_in_contract_tests() -> None:
    test_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(test_tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    imported_modules.update(
        alias.name
        for node in ast.walk(test_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    forbidden_modules = {
        "urllib",
        "requests",
        "httpx",
        "socket",
        "atlas.providers",
    }
    assert imported_modules.isdisjoint(forbidden_modules)
