"""Sprint 270 — Temporary workspace schema dataclass tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from atlas.temporary_workspace import (
    ClassificationResult,
    DetectedEntity,
    SaveAccountHandoff,
    SourceInput,
    TemporaryWorkspace,
    WorkspaceCard,
    WorkspaceCardStatus,
    WorkspaceCardType,
    WorkspaceConfidence,
    WorkspaceEntityType,
    WorkspaceInputClassification,
    WorkspaceMissingField,
    WorkspaceMissingFieldRequiredness,
    WorkspaceSafetyBoundary,
    WorkspaceSavePromptReason,
    WorkspaceStatus,
    WorkspaceUncertainty,
    WorkspaceUncertaintySeverity,
)


SCHEMA_FILE = Path("atlas/temporary_workspace/schema.py")
CLI_FILE = Path("atlas/cli/main.py")
PRECONDITION_DOCS = [
    Path("docs/TemporaryWorkspaceDataModel.md"),
    Path("docs/TemporaryWorkspaceCardRenderingContract.md"),
    Path("docs/InputFirstWorkspaceOnboarding.md"),
    Path("docs/NoAccountFirstValueOnboarding.md"),
]


def _workspace() -> TemporaryWorkspace:
    source = SourceInput(
        input_id="input_001",
        input_type="portfolio_input",
        source_description="Pasted portfolio text",
        raw_text_preview="ASML 12%, NOVO B 18%",
        submitted_at="2026-07-04T12:00:00Z",
        user_language_hint="en",
    )
    classification = ClassificationResult(
        primary_type=WorkspaceInputClassification.PORTFOLIO_INPUT,
        confidence=WorkspaceConfidence.HIGH,
        secondary_types=[WorkspaceInputClassification.WATCHLIST_INPUT],
        rationale="Portfolio weights were detected.",
        uncertainty_ids=["unc_001"],
        suggested_card_types=[
            WorkspaceCardType.INPUT_SUMMARY,
            WorkspaceCardType.DETECTED_HOLDINGS,
        ],
    )
    entity = DetectedEntity(
        entity_id="ent_001",
        entity_type=WorkspaceEntityType.TICKER,
        value="NOVO B",
        normalized_value="NOVO B",
        source_reference="src_001",
        confidence=WorkspaceConfidence.HIGH,
    )
    uncertainty = WorkspaceUncertainty(
        uncertainty_id="unc_001",
        severity=WorkspaceUncertaintySeverity.LOW,
        message="Currency not confirmed.",
        related_entity_ids=["ent_001"],
        related_card_ids=["card_001"],
        suggested_user_confirmation="Are all holdings in the same currency?",
    )
    missing = WorkspaceMissingField(
        field_id="missing_001",
        field_name="currency",
        reason="Currency improves portfolio context.",
        related_card_ids=["card_001"],
        requiredness=WorkspaceMissingFieldRequiredness.OPTIONAL,
    )
    card = WorkspaceCard(
        card_id="card_001",
        card_type=WorkspaceCardType.DETECTED_HOLDINGS,
        title="Detected Holdings",
        status=WorkspaceCardStatus.USER_CONFIRMATION_NEEDED,
        summary="2 holdings detected.",
        items=["NOVO B 18%", "ASML 12%"],
        related_entity_ids=["ent_001"],
        related_uncertainty_ids=["unc_001"],
        related_missing_field_ids=["missing_001"],
        source_references=["src_001"],
        next_prompt="Would you like to confirm these holdings?",
    )
    return TemporaryWorkspace(
        workspace_id="tmp_ws_001",
        status=WorkspaceStatus.TEMPORARY,
        created_at="2026-07-04T12:00:00Z",
        source_input=source,
        classification=classification,
        detected_entities=[entity],
        uncertainties=[uncertainty],
        missing_fields=[missing],
        cards=[card],
        save_handoff=SaveAccountHandoff(
            prompt_reason=WorkspaceSavePromptReason.SAVE_WORKSPACE
        ),
        safety_boundary=WorkspaceSafetyBoundary(),
    )


def test_package_module_exists() -> None:
    assert SCHEMA_FILE.exists()


def test_precondition_docs_exist() -> None:
    assert all(path.exists() for path in PRECONDITION_DOCS)


def test_all_canonical_enum_values_exist() -> None:
    assert {item.value for item in WorkspaceStatus} == {
        "temporary",
        "saved",
        "discarded",
    }
    assert {item.value for item in WorkspaceInputClassification} == {
        "portfolio_input",
        "watchlist_input",
        "order_review_input",
        "research_note_input",
        "company_facts_input",
        "journal_note_input",
        "news_or_external_analysis_input",
        "question_input",
        "mixed_input",
        "unknown_input",
    }
    assert {item.value for item in WorkspaceEntityType} == {
        "ticker",
        "company_name",
        "holding",
        "quantity",
        "portfolio_weight",
        "currency",
        "date",
        "watchlist_item",
        "open_decision",
        "research_note",
        "company_fact",
        "source_reference",
    }
    assert {item.value for item in WorkspaceCardType} == {
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
    }
    assert {item.value for item in WorkspaceCardStatus} == {
        "ready_for_review",
        "needs_more_evidence",
        "missing_required_input",
        "user_confirmation_needed",
        "not_applicable",
        "no_action_warranted",
        "decision_deferred",
    }
    assert {item.value for item in WorkspaceSavePromptReason} == {
        "save_workspace",
        "continue_later",
        "keep_history",
        "collaborate",
        "cross_device_access",
    }


def test_source_input_validates_required_fields() -> None:
    with pytest.raises(ValueError, match="SourceInput.input_id"):
        SourceInput(input_id="", input_type="portfolio_input", source_description="Pasted")
    with pytest.raises(ValueError, match="SourceInput.input_type"):
        SourceInput(input_id="input_001", input_type="non_canonical", source_description="Pasted")


def test_classification_result_validates_category_and_confidence() -> None:
    result = ClassificationResult(primary_type="portfolio_input", confidence="high")
    assert result.primary_type is WorkspaceInputClassification.PORTFOLIO_INPUT
    assert result.confidence is WorkspaceConfidence.HIGH
    with pytest.raises(ValueError, match="ClassificationResult.primary_type"):
        ClassificationResult(primary_type="not_real", confidence="high")
    with pytest.raises(ValueError, match="ClassificationResult.confidence"):
        ClassificationResult(primary_type="portfolio_input", confidence="certain")


def test_detected_entity_validates_entity_type_and_confidence() -> None:
    entity = DetectedEntity(
        entity_id="ent_001",
        entity_type="ticker",
        value="ASML",
        confidence="medium",
    )
    assert entity.entity_type is WorkspaceEntityType.TICKER
    assert entity.confidence is WorkspaceConfidence.MEDIUM
    with pytest.raises(ValueError, match="DetectedEntity.entity_type"):
        DetectedEntity(entity_id="ent_001", entity_type="asset", value="ASML")
    with pytest.raises(ValueError, match="DetectedEntity.confidence"):
        DetectedEntity(
            entity_id="ent_001",
            entity_type="ticker",
            value="ASML",
            confidence="guaranteed",
        )


def test_workspace_uncertainty_validates_severity() -> None:
    uncertainty = WorkspaceUncertainty(
        uncertainty_id="unc_001",
        severity="blocking",
        message="User confirmation needed.",
    )
    assert uncertainty.severity is WorkspaceUncertaintySeverity.BLOCKING
    with pytest.raises(ValueError, match="WorkspaceUncertainty.severity"):
        WorkspaceUncertainty(
            uncertainty_id="unc_001",
            severity="urgent",
            message="User confirmation needed.",
        )


def test_workspace_missing_field_validates_requiredness() -> None:
    missing = WorkspaceMissingField(
        field_id="missing_001",
        field_name="currency",
        reason="Currency not detected.",
        requiredness="required_for_review_quality",
    )
    assert missing.requiredness is WorkspaceMissingFieldRequiredness.REQUIRED_FOR_REVIEW_QUALITY
    with pytest.raises(ValueError, match="WorkspaceMissingField.requiredness"):
        WorkspaceMissingField(
            field_id="missing_001",
            field_name="currency",
            reason="Currency not detected.",
            requiredness="mandatory",
        )


def test_workspace_card_validates_card_type_and_status() -> None:
    card = WorkspaceCard(
        card_id="card_001",
        card_type="evidence_gaps",
        title="Evidence Gaps",
        status="needs_more_evidence",
    )
    assert card.card_type is WorkspaceCardType.EVIDENCE_GAPS
    assert card.status is WorkspaceCardStatus.NEEDS_MORE_EVIDENCE
    with pytest.raises(ValueError, match="WorkspaceCard.card_type"):
        WorkspaceCard(card_id="card_001", card_type="recommendation", title="X", status="ready_for_review")
    with pytest.raises(ValueError, match="WorkspaceCard.status"):
        WorkspaceCard(card_id="card_001", card_type="evidence_gaps", title="X", status="buy_signal")


def test_save_account_handoff_validates_prompt_reason() -> None:
    handoff = SaveAccountHandoff(prompt_reason="continue_later")
    assert handoff.prompt_reason is WorkspaceSavePromptReason.CONTINUE_LATER
    with pytest.raises(ValueError, match="SaveAccountHandoff.prompt_reason"):
        SaveAccountHandoff(prompt_reason="subscribe_now")
    with pytest.raises(ValueError, match="SaveAccountHandoff.account_required"):
        SaveAccountHandoff(account_required=True)


def test_workspace_safety_boundary_defaults_all_flags_true() -> None:
    boundary = WorkspaceSafetyBoundary()
    assert boundary.to_dict() == {
        "no_recommendations": True,
        "no_order_execution": True,
        "no_price_targets": True,
        "user_judgment_required": True,
        "local_or_temporary_context": True,
    }
    with pytest.raises(ValueError, match="WorkspaceSafetyBoundary.no_recommendations"):
        WorkspaceSafetyBoundary(no_recommendations=False)


def test_temporary_workspace_validates_required_fields() -> None:
    workspace = _workspace()
    assert workspace.workspace_id == "tmp_ws_001"
    with pytest.raises(ValueError, match="TemporaryWorkspace.workspace_id"):
        TemporaryWorkspace(
            workspace_id="",
            status=WorkspaceStatus.TEMPORARY,
            created_at="2026-07-04T12:00:00Z",
            source_input=workspace.source_input,
            classification=workspace.classification,
        )


def test_temporary_workspace_can_contain_nested_workspace_objects() -> None:
    workspace = _workspace()
    assert len(workspace.detected_entities) == 1
    assert len(workspace.uncertainties) == 1
    assert len(workspace.missing_fields) == 1
    assert len(workspace.cards) == 1


def test_to_dict_preserves_canonical_values() -> None:
    data = _workspace().to_dict()
    assert data["status"] == "temporary"
    assert data["classification"]["primary_type"] == "portfolio_input"
    assert data["classification"]["confidence"] == "high"
    assert data["detected_entities"][0]["entity_type"] == "ticker"
    assert data["cards"][0]["card_type"] == "detected_holdings"
    assert data["cards"][0]["status"] == "user_confirmation_needed"


def test_from_dict_restores_nested_objects() -> None:
    restored = TemporaryWorkspace.from_dict(_workspace().to_dict())
    assert isinstance(restored.source_input, SourceInput)
    assert isinstance(restored.classification, ClassificationResult)
    assert isinstance(restored.detected_entities[0], DetectedEntity)
    assert isinstance(restored.uncertainties[0], WorkspaceUncertainty)
    assert isinstance(restored.missing_fields[0], WorkspaceMissingField)
    assert isinstance(restored.cards[0], WorkspaceCard)


def test_to_json_from_json_round_trip_preserves_user_text() -> None:
    user_text = "NOVO B 18%, ASML 12% -- keep this exact note."
    workspace = _workspace()
    workspace.source_input.raw_text_preview = user_text
    restored = TemporaryWorkspace.from_json(workspace.to_json())
    assert restored.to_dict() == workspace.to_dict()
    assert restored.source_input.raw_text_preview == user_text


def test_invalid_enum_values_raise_value_error_with_field_name() -> None:
    data = _workspace().to_dict()
    data["cards"][0]["status"] = "strong_buy"
    with pytest.raises(ValueError, match="WorkspaceCard.status"):
        TemporaryWorkspace.from_dict(data)


def test_invalid_nested_object_values_raise_value_error_with_field_name() -> None:
    data = _workspace().to_dict()
    data["save_handoff"] = "not an object"
    with pytest.raises(ValueError, match="TemporaryWorkspace.save_handoff"):
        TemporaryWorkspace.from_dict(data)


def test_empty_required_ids_raise_value_error_with_field_name() -> None:
    data = _workspace().to_dict()
    data["detected_entities"][0]["entity_id"] = ""
    with pytest.raises(ValueError, match="DetectedEntity.entity_id"):
        TemporaryWorkspace.from_dict(data)


def test_schema_code_does_not_write_files_or_add_persistence_helpers() -> None:
    source = SCHEMA_FILE.read_text(encoding="utf-8")
    forbidden = [
        "write_text",
        "open(",
        "Path(",
        "sqlite",
        "postgres",
        "load_workspace",
    ]
    assert not any(token in source for token in forbidden)


def test_no_cli_behavior_changed_for_temporary_workspace() -> None:
    cli_source = CLI_FILE.read_text(encoding="utf-8")
    assert "temporary_workspace" not in cli_source


def test_no_provider_network_or_ai_imports_added_to_schema() -> None:
    tree = ast.parse(SCHEMA_FILE.read_text(encoding="utf-8"))
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
    forbidden = {
        "atlas.providers",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "openai",
        "anthropic",
    }
    assert imports.isdisjoint(forbidden)
