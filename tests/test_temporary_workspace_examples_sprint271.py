"""Sprint 271 — Temporary workspace example fixture tests."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from atlas.temporary_workspace import (
    TemporaryWorkspace,
    WorkspaceCardStatus,
    WorkspaceCardType,
    WorkspaceEntityType,
    WorkspaceInputClassification,
    WorkspaceMissingFieldRequiredness,
    WorkspaceSavePromptReason,
    WorkspaceStatus,
    WorkspaceUncertaintySeverity,
)


EXAMPLE_DIR = Path("examples/temporary_workspaces")
FIXTURES = {
    "portfolio": EXAMPLE_DIR / "portfolio_snapshot_workspace.json",
    "watchlist": EXAMPLE_DIR / "watchlist_research_workspace.json",
    "order": EXAMPLE_DIR / "order_idea_workspace.json",
}
CLI_FILE = Path("atlas/cli/main.py")

USER_TEXT_SNIPPETS = [
    'User note: "Portfolio paste from broker overview, July review."',
    'User note: "Water infrastructure thesis needs evidence."',
    'User note: "Margin durability test 2026."',
    'User note: "Possible order idea needs fit check before decision."',
]

PROHIBITED_PHRASES = [
    "strong buy",
    "price target",
    "target price",
    "guaranteed",
    "risk-free",
    "can't lose",
    "cannot lose",
    "must act",
    "act now",
    "urgent",
    "immediately",
    "we recommend",
    "you should",
    "will outperform",
    "expected to outperform",
    "execute the trade",
    "place the order",
]


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    assert isinstance(data, dict)
    return data


def _workspace(path: Path) -> TemporaryWorkspace:
    return TemporaryWorkspace.from_json(path.read_text(encoding="utf-8"))


def _fixture_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for entry in value for item in _strings(entry)]
    if isinstance(value, dict):
        return [item for entry in value.values() for item in _strings(entry)]
    return []


def test_example_directory_exists() -> None:
    assert EXAMPLE_DIR.exists()
    assert EXAMPLE_DIR.is_dir()


def test_all_three_fixture_files_exist() -> None:
    assert all(path.exists() for path in FIXTURES.values())


def test_each_fixture_is_valid_json() -> None:
    for path in FIXTURES.values():
        assert _load_json(path)["status"] == "temporary"


def test_each_fixture_loads_through_temporary_workspace_schema() -> None:
    for path in FIXTURES.values():
        workspace = _workspace(path)
        assert isinstance(workspace, TemporaryWorkspace)


def test_each_fixture_round_trips_through_json() -> None:
    for path in FIXTURES.values():
        workspace = _workspace(path)
        restored = TemporaryWorkspace.from_json(workspace.to_json())
        assert restored.to_dict() == workspace.to_dict()


def test_each_fixture_has_required_top_level_schema_parts() -> None:
    for path in FIXTURES.values():
        workspace = _workspace(path)
        assert workspace.status is WorkspaceStatus.TEMPORARY
        assert workspace.source_input is not None
        assert workspace.classification is not None
        assert workspace.detected_entities
        assert workspace.cards


def test_each_fixture_has_after_first_value_save_handoff() -> None:
    for path in FIXTURES.values():
        workspace = _workspace(path)
        assert workspace.save_handoff.account_required is False
        assert workspace.save_handoff.prompt_timing == "after_first_value"
        assert workspace.save_handoff.prompt_reason in {
            WorkspaceSavePromptReason.SAVE_WORKSPACE,
            WorkspaceSavePromptReason.CONTINUE_LATER,
        }


def test_each_fixture_has_true_safety_boundary_flags() -> None:
    for path in FIXTURES.values():
        boundary = _workspace(path).safety_boundary.to_dict()
        assert boundary
        assert all(value is True for value in boundary.values())


def test_portfolio_fixture_contains_portfolio_related_cards() -> None:
    card_types = {card.card_type for card in _workspace(FIXTURES["portfolio"]).cards}
    assert {
        WorkspaceCardType.INPUT_SUMMARY,
        WorkspaceCardType.DETECTED_HOLDINGS,
        WorkspaceCardType.PORTFOLIO_CONTEXT,
        WorkspaceCardType.EVIDENCE_GAPS,
        WorkspaceCardType.RISKS_TO_MONITOR,
        WorkspaceCardType.WEEKLY_REVIEW_PREVIEW,
        WorkspaceCardType.SAVE_WORKSPACE_PROMPT,
    }.issubset(card_types)


def test_watchlist_research_fixture_contains_watchlist_research_cards() -> None:
    workspace = _workspace(FIXTURES["watchlist"])
    card_types = {card.card_type for card in workspace.cards}
    assert workspace.classification.primary_type is WorkspaceInputClassification.MIXED_INPUT
    assert {
        WorkspaceCardType.INPUT_SUMMARY,
        WorkspaceCardType.WATCHLIST_REVIEW,
        WorkspaceCardType.EVIDENCE_GAPS,
        WorkspaceCardType.REASONS_TO_WAIT,
        WorkspaceCardType.FOLLOW_UP_QUESTIONS,
        WorkspaceCardType.SNAPSHOT_DRAFTS,
        WorkspaceCardType.SAVE_WORKSPACE_PROMPT,
    }.issubset(card_types)


def test_order_idea_fixture_contains_open_decision_evidence_and_wait_cards() -> None:
    workspace = _workspace(FIXTURES["order"])
    card_types = {card.card_type for card in workspace.cards}
    entity_types = {entity.entity_type for entity in workspace.detected_entities}
    assert workspace.classification.primary_type is WorkspaceInputClassification.ORDER_REVIEW_INPUT
    assert WorkspaceEntityType.OPEN_DECISION in entity_types
    assert {
        WorkspaceCardType.INPUT_SUMMARY,
        WorkspaceCardType.OPEN_DECISIONS,
        WorkspaceCardType.EVIDENCE_GAPS,
        WorkspaceCardType.REASONS_TO_WAIT,
        WorkspaceCardType.FOLLOW_UP_QUESTIONS,
        WorkspaceCardType.SAVE_WORKSPACE_PROMPT,
    }.issubset(card_types)


def test_fixtures_preserve_user_provided_text_through_round_trip() -> None:
    fixture_text = "\n".join(
        string for path in FIXTURES.values() for string in _strings(_load_json(path))
    )
    for snippet in USER_TEXT_SNIPPETS:
        assert snippet in fixture_text
    for path in FIXTURES.values():
        original_text = "\n".join(_strings(_load_json(path)))
        restored_text = "\n".join(
            _strings(TemporaryWorkspace.from_json(_workspace(path).to_json()).to_dict())
        )
        for snippet in USER_TEXT_SNIPPETS:
            if snippet in original_text:
                assert snippet in restored_text


def test_fixtures_use_canonical_english_enum_values() -> None:
    valid_statuses = {item.value for item in WorkspaceStatus}
    valid_classifications = {item.value for item in WorkspaceInputClassification}
    valid_entity_types = {item.value for item in WorkspaceEntityType}
    valid_severities = {item.value for item in WorkspaceUncertaintySeverity}
    valid_requiredness = {item.value for item in WorkspaceMissingFieldRequiredness}
    valid_card_types = {item.value for item in WorkspaceCardType}
    valid_card_statuses = {item.value for item in WorkspaceCardStatus}
    valid_prompt_reasons = {item.value for item in WorkspaceSavePromptReason}

    for path in FIXTURES.values():
        data = _load_json(path)
        assert data["status"] in valid_statuses
        assert data["classification"]["primary_type"] in valid_classifications
        assert data["source_input"]["input_type"] in valid_classifications
        assert all(entity["entity_type"] in valid_entity_types for entity in data["detected_entities"])
        assert all(uncertainty["severity"] in valid_severities for uncertainty in data["uncertainties"])
        assert all(missing["requiredness"] in valid_requiredness for missing in data["missing_fields"])
        assert all(card["card_type"] in valid_card_types for card in data["cards"])
        assert all(card["status"] in valid_card_statuses for card in data["cards"])
        assert data["save_handoff"]["prompt_reason"] in valid_prompt_reasons


def test_fixtures_avoid_prohibited_language() -> None:
    for path in FIXTURES.values():
        text = _fixture_text(path).lower()
        for phrase in PROHIBITED_PHRASES:
            assert phrase not in text, f"{path} contains prohibited phrase: {phrase}"


def test_fixtures_include_source_reference_or_user_provided_text() -> None:
    for path in FIXTURES.values():
        workspace = _workspace(path)
        fixture_text = _fixture_text(path)
        assert "User note:" in fixture_text
        assert any(card.source_references for card in workspace.cards)


def test_no_persistence_auth_backend_or_database_code_added() -> None:
    assert not Path("atlas/temporary_workspace/persistence.py").exists()
    assert not Path("atlas/temporary_workspace/database.py").exists()
    assert not Path("atlas/temporary_workspace/auth.py").exists()
    assert not Path("atlas/temporary_workspace/backend.py").exists()


def test_no_provider_network_or_ai_imports_added_to_temporary_workspace_package() -> None:
    package_files = sorted(Path("atlas/temporary_workspace").glob("*.py"))
    forbidden = {
        "atlas.providers",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "openai",
        "anthropic",
    }
    for path in package_files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        imports.update(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        assert imports.isdisjoint(forbidden)


def test_no_cli_behavior_changed_for_temporary_workspace_examples() -> None:
    cli_source = CLI_FILE.read_text(encoding="utf-8")
    assert "temporary_workspace" not in cli_source
    assert "temporary-workspace" not in cli_source
