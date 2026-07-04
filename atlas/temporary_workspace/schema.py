"""Schema dataclasses for Atlas temporary workspaces.

The temporary workspace schema represents user-supplied input, classification
metadata, detected entities, uncertainties, missing fields, cards, save/account
handoff state, and safety boundaries.

This module is intentionally schema-only. It does not implement classifiers,
entity extraction, card rendering, UI, CLI commands, persistence, provider
calls, network calls, OCR, or AI/LLM behavior.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar


class WorkspaceStatus(str, Enum):
    """Canonical temporary workspace lifecycle status values."""

    TEMPORARY = "temporary"
    SAVED = "saved"
    DISCARDED = "discarded"


class WorkspaceInputClassification(str, Enum):
    """Canonical input classification categories."""

    PORTFOLIO_INPUT = "portfolio_input"
    WATCHLIST_INPUT = "watchlist_input"
    ORDER_REVIEW_INPUT = "order_review_input"
    RESEARCH_NOTE_INPUT = "research_note_input"
    COMPANY_FACTS_INPUT = "company_facts_input"
    JOURNAL_NOTE_INPUT = "journal_note_input"
    NEWS_OR_EXTERNAL_ANALYSIS_INPUT = "news_or_external_analysis_input"
    QUESTION_INPUT = "question_input"
    MIXED_INPUT = "mixed_input"
    UNKNOWN_INPUT = "unknown_input"


class WorkspaceEntityType(str, Enum):
    """Canonical detected entity types."""

    TICKER = "ticker"
    COMPANY_NAME = "company_name"
    HOLDING = "holding"
    QUANTITY = "quantity"
    PORTFOLIO_WEIGHT = "portfolio_weight"
    CURRENCY = "currency"
    DATE = "date"
    WATCHLIST_ITEM = "watchlist_item"
    OPEN_DECISION = "open_decision"
    RESEARCH_NOTE = "research_note"
    COMPANY_FACT = "company_fact"
    SOURCE_REFERENCE = "source_reference"


class WorkspaceUncertaintySeverity(str, Enum):
    """Canonical uncertainty severity values."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKING = "blocking"


class WorkspaceMissingFieldRequiredness(str, Enum):
    """Canonical missing field requiredness values."""

    OPTIONAL = "optional"
    REQUIRED_FOR_EXPORT = "required_for_export"
    REQUIRED_FOR_SAVE = "required_for_save"
    REQUIRED_FOR_REVIEW_QUALITY = "required_for_review_quality"


class WorkspaceCardType(str, Enum):
    """Canonical temporary workspace card types."""

    INPUT_SUMMARY = "input_summary"
    DETECTED_HOLDINGS = "detected_holdings"
    DETECTED_TICKERS = "detected_tickers"
    PORTFOLIO_CONTEXT = "portfolio_context"
    WATCHLIST_REVIEW = "watchlist_review"
    OPEN_DECISIONS = "open_decisions"
    EVIDENCE_GAPS = "evidence_gaps"
    RISKS_TO_MONITOR = "risks_to_monitor"
    REASONS_TO_WAIT = "reasons_to_wait"
    FOLLOW_UP_QUESTIONS = "follow_up_questions"
    MISSING_INPUTS = "missing_inputs"
    SNAPSHOT_DRAFTS = "snapshot_drafts"
    WEEKLY_REVIEW_PREVIEW = "weekly_review_preview"
    SAVE_WORKSPACE_PROMPT = "save_workspace_prompt"


class WorkspaceCardStatus(str, Enum):
    """Canonical temporary workspace card status values."""

    READY_FOR_REVIEW = "ready_for_review"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"
    MISSING_REQUIRED_INPUT = "missing_required_input"
    USER_CONFIRMATION_NEEDED = "user_confirmation_needed"
    NOT_APPLICABLE = "not_applicable"
    NO_ACTION_WARRANTED = "no_action_warranted"
    DECISION_DEFERRED = "decision_deferred"


class WorkspaceSavePromptReason(str, Enum):
    """Canonical save/account prompt reasons."""

    SAVE_WORKSPACE = "save_workspace"
    CONTINUE_LATER = "continue_later"
    KEEP_HISTORY = "keep_history"
    COLLABORATE = "collaborate"
    CROSS_DEVICE_ACCESS = "cross_device_access"


class WorkspaceConfidence(str, Enum):
    """Descriptive confidence levels for schema fields."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


EnumT = TypeVar("EnumT", bound=Enum)


def _require_non_empty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")


def _coerce_enum(value: EnumT | str | None, enum_type: type[EnumT], field_name: str) -> EnumT:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid {enum_type.__name__}: {value!r}") from exc


def _coerce_optional_enum(
    value: EnumT | str | None, enum_type: type[EnumT], field_name: str
) -> EnumT | None:
    if value is None:
        return None
    return _coerce_enum(value, enum_type, field_name)


def _list_of_strings(values: list[str], field_name: str) -> list[str]:
    if not isinstance(values, list):
        raise ValueError(f"{field_name} must be a list.")
    if not all(isinstance(item, str) for item in values):
        raise ValueError(f"{field_name} must contain only strings.")
    return list(values)


def _list_of_dicts(values: list[Any], field_name: str) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        raise ValueError(f"{field_name} must be a list.")
    if not all(isinstance(item, dict) for item in values):
        raise ValueError(f"{field_name} must contain only objects.")
    return list(values)


@dataclass
class SourceInput:
    """Source material submitted by the user, without interpretation."""

    input_id: str
    input_type: str
    source_description: str
    raw_text_preview: str | None = None
    submitted_at: str | None = None
    user_language_hint: str | None = None
    contains_sensitive_data: bool = False

    def __post_init__(self) -> None:
        _require_non_empty(self.input_id, "SourceInput.input_id")
        self.input_type = _coerce_enum(
            self.input_type, WorkspaceInputClassification, "SourceInput.input_type"
        ).value
        _require_non_empty(self.source_description, "SourceInput.source_description")
        if not isinstance(self.contains_sensitive_data, bool):
            raise ValueError("SourceInput.contains_sensitive_data must be a boolean.")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "input_id": self.input_id,
            "input_type": self.input_type,
            "source_description": self.source_description,
            "raw_text_preview": self.raw_text_preview,
            "submitted_at": self.submitted_at,
            "user_language_hint": self.user_language_hint,
            "contains_sensitive_data": self.contains_sensitive_data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceInput":
        """Build SourceInput from a mapping."""
        return cls(
            input_id=data.get("input_id", ""),
            input_type=data.get("input_type", ""),
            source_description=data.get("source_description", ""),
            raw_text_preview=data.get("raw_text_preview"),
            submitted_at=data.get("submitted_at"),
            user_language_hint=data.get("user_language_hint"),
            contains_sensitive_data=data.get("contains_sensitive_data", False),
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize SourceInput to deterministic JSON."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "SourceInput":
        """Build SourceInput from JSON text."""
        data = _json_object(text, "SourceInput")
        return cls.from_dict(data)


@dataclass
class ClassificationResult:
    """Classification metadata for the submitted source input."""

    primary_type: WorkspaceInputClassification
    confidence: WorkspaceConfidence
    secondary_types: list[WorkspaceInputClassification] = field(default_factory=list)
    rationale: str | None = None
    uncertainty_ids: list[str] = field(default_factory=list)
    suggested_card_types: list[WorkspaceCardType] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.primary_type = _coerce_enum(
            self.primary_type, WorkspaceInputClassification, "ClassificationResult.primary_type"
        )
        self.confidence = _coerce_enum(
            self.confidence, WorkspaceConfidence, "ClassificationResult.confidence"
        )
        self.secondary_types = [
            _coerce_enum(
                item, WorkspaceInputClassification, "ClassificationResult.secondary_types"
            )
            for item in self.secondary_types
        ]
        self.uncertainty_ids = _list_of_strings(
            self.uncertainty_ids, "ClassificationResult.uncertainty_ids"
        )
        self.suggested_card_types = [
            _coerce_enum(item, WorkspaceCardType, "ClassificationResult.suggested_card_types")
            for item in self.suggested_card_types
        ]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "primary_type": self.primary_type.value,
            "confidence": self.confidence.value,
            "secondary_types": [item.value for item in self.secondary_types],
            "rationale": self.rationale,
            "uncertainty_ids": list(self.uncertainty_ids),
            "suggested_card_types": [item.value for item in self.suggested_card_types],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClassificationResult":
        """Build ClassificationResult from a mapping."""
        return cls(
            primary_type=data.get("primary_type", ""),
            confidence=data.get("confidence", WorkspaceConfidence.UNKNOWN.value),
            secondary_types=list(data.get("secondary_types", [])),
            rationale=data.get("rationale"),
            uncertainty_ids=list(data.get("uncertainty_ids", [])),
            suggested_card_types=list(data.get("suggested_card_types", [])),
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize ClassificationResult to deterministic JSON."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "ClassificationResult":
        """Build ClassificationResult from JSON text."""
        data = _json_object(text, "ClassificationResult")
        return cls.from_dict(data)


@dataclass
class DetectedEntity:
    """Structured entity detected in user-provided input."""

    entity_id: str
    entity_type: WorkspaceEntityType
    value: str
    normalized_value: str | None = None
    source_reference: str | None = None
    confidence: WorkspaceConfidence = WorkspaceConfidence.UNKNOWN
    uncertainty_reason: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.entity_id, "DetectedEntity.entity_id")
        self.entity_type = _coerce_enum(
            self.entity_type, WorkspaceEntityType, "DetectedEntity.entity_type"
        )
        _require_non_empty(self.value, "DetectedEntity.value")
        self.confidence = _coerce_enum(
            self.confidence, WorkspaceConfidence, "DetectedEntity.confidence"
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "value": self.value,
            "normalized_value": self.normalized_value,
            "source_reference": self.source_reference,
            "confidence": self.confidence.value,
            "uncertainty_reason": self.uncertainty_reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DetectedEntity":
        """Build DetectedEntity from a mapping."""
        return cls(
            entity_id=data.get("entity_id", ""),
            entity_type=data.get("entity_type", ""),
            value=data.get("value", ""),
            normalized_value=data.get("normalized_value"),
            source_reference=data.get("source_reference"),
            confidence=data.get("confidence", WorkspaceConfidence.UNKNOWN.value),
            uncertainty_reason=data.get("uncertainty_reason"),
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize DetectedEntity to deterministic JSON."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "DetectedEntity":
        """Build DetectedEntity from JSON text."""
        data = _json_object(text, "DetectedEntity")
        return cls.from_dict(data)


@dataclass
class WorkspaceUncertainty:
    """Uncertainty that should remain visible in a temporary workspace."""

    uncertainty_id: str
    severity: WorkspaceUncertaintySeverity
    message: str
    related_entity_ids: list[str] = field(default_factory=list)
    related_card_ids: list[str] = field(default_factory=list)
    suggested_user_confirmation: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.uncertainty_id, "WorkspaceUncertainty.uncertainty_id")
        self.severity = _coerce_enum(
            self.severity, WorkspaceUncertaintySeverity, "WorkspaceUncertainty.severity"
        )
        _require_non_empty(self.message, "WorkspaceUncertainty.message")
        self.related_entity_ids = _list_of_strings(
            self.related_entity_ids, "WorkspaceUncertainty.related_entity_ids"
        )
        self.related_card_ids = _list_of_strings(
            self.related_card_ids, "WorkspaceUncertainty.related_card_ids"
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "uncertainty_id": self.uncertainty_id,
            "severity": self.severity.value,
            "message": self.message,
            "related_entity_ids": list(self.related_entity_ids),
            "related_card_ids": list(self.related_card_ids),
            "suggested_user_confirmation": self.suggested_user_confirmation,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkspaceUncertainty":
        """Build WorkspaceUncertainty from a mapping."""
        return cls(
            uncertainty_id=data.get("uncertainty_id", ""),
            severity=data.get("severity", ""),
            message=data.get("message", ""),
            related_entity_ids=list(data.get("related_entity_ids", [])),
            related_card_ids=list(data.get("related_card_ids", [])),
            suggested_user_confirmation=data.get("suggested_user_confirmation"),
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize WorkspaceUncertainty to deterministic JSON."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "WorkspaceUncertainty":
        """Build WorkspaceUncertainty from JSON text."""
        data = _json_object(text, "WorkspaceUncertainty")
        return cls.from_dict(data)


@dataclass
class WorkspaceMissingField:
    """Missing input that should remain visible in a temporary workspace."""

    field_id: str
    field_name: str
    reason: str
    related_card_ids: list[str] = field(default_factory=list)
    requiredness: WorkspaceMissingFieldRequiredness = (
        WorkspaceMissingFieldRequiredness.OPTIONAL
    )

    def __post_init__(self) -> None:
        _require_non_empty(self.field_id, "WorkspaceMissingField.field_id")
        _require_non_empty(self.field_name, "WorkspaceMissingField.field_name")
        _require_non_empty(self.reason, "WorkspaceMissingField.reason")
        self.related_card_ids = _list_of_strings(
            self.related_card_ids, "WorkspaceMissingField.related_card_ids"
        )
        self.requiredness = _coerce_enum(
            self.requiredness,
            WorkspaceMissingFieldRequiredness,
            "WorkspaceMissingField.requiredness",
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "field_id": self.field_id,
            "field_name": self.field_name,
            "reason": self.reason,
            "related_card_ids": list(self.related_card_ids),
            "requiredness": self.requiredness.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkspaceMissingField":
        """Build WorkspaceMissingField from a mapping."""
        return cls(
            field_id=data.get("field_id", ""),
            field_name=data.get("field_name", ""),
            reason=data.get("reason", ""),
            related_card_ids=list(data.get("related_card_ids", [])),
            requiredness=data.get(
                "requiredness", WorkspaceMissingFieldRequiredness.OPTIONAL.value
            ),
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize WorkspaceMissingField to deterministic JSON."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "WorkspaceMissingField":
        """Build WorkspaceMissingField from JSON text."""
        data = _json_object(text, "WorkspaceMissingField")
        return cls.from_dict(data)


@dataclass
class WorkspaceCard:
    """Schema representation of a future temporary workspace card."""

    card_id: str
    card_type: WorkspaceCardType
    title: str
    status: WorkspaceCardStatus
    summary: str | None = None
    items: list[str] = field(default_factory=list)
    related_entity_ids: list[str] = field(default_factory=list)
    related_uncertainty_ids: list[str] = field(default_factory=list)
    related_missing_field_ids: list[str] = field(default_factory=list)
    source_references: list[str] = field(default_factory=list)
    next_prompt: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.card_id, "WorkspaceCard.card_id")
        self.card_type = _coerce_enum(self.card_type, WorkspaceCardType, "WorkspaceCard.card_type")
        _require_non_empty(self.title, "WorkspaceCard.title")
        self.status = _coerce_enum(self.status, WorkspaceCardStatus, "WorkspaceCard.status")
        self.items = _list_of_strings(self.items, "WorkspaceCard.items")
        self.related_entity_ids = _list_of_strings(
            self.related_entity_ids, "WorkspaceCard.related_entity_ids"
        )
        self.related_uncertainty_ids = _list_of_strings(
            self.related_uncertainty_ids, "WorkspaceCard.related_uncertainty_ids"
        )
        self.related_missing_field_ids = _list_of_strings(
            self.related_missing_field_ids, "WorkspaceCard.related_missing_field_ids"
        )
        self.source_references = _list_of_strings(
            self.source_references, "WorkspaceCard.source_references"
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "card_id": self.card_id,
            "card_type": self.card_type.value,
            "title": self.title,
            "status": self.status.value,
            "summary": self.summary,
            "items": list(self.items),
            "related_entity_ids": list(self.related_entity_ids),
            "related_uncertainty_ids": list(self.related_uncertainty_ids),
            "related_missing_field_ids": list(self.related_missing_field_ids),
            "source_references": list(self.source_references),
            "next_prompt": self.next_prompt,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkspaceCard":
        """Build WorkspaceCard from a mapping."""
        return cls(
            card_id=data.get("card_id", ""),
            card_type=data.get("card_type", ""),
            title=data.get("title", ""),
            status=data.get("status", ""),
            summary=data.get("summary"),
            items=list(data.get("items", [])),
            related_entity_ids=list(data.get("related_entity_ids", [])),
            related_uncertainty_ids=list(data.get("related_uncertainty_ids", [])),
            related_missing_field_ids=list(data.get("related_missing_field_ids", [])),
            source_references=list(data.get("source_references", [])),
            next_prompt=data.get("next_prompt"),
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize WorkspaceCard to deterministic JSON."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "WorkspaceCard":
        """Build WorkspaceCard from JSON text."""
        data = _json_object(text, "WorkspaceCard")
        return cls.from_dict(data)


@dataclass
class SaveAccountHandoff:
    """Schema for future save/account prompts after first value is delivered."""

    account_required: bool = False
    save_available: bool = True
    save_requires_account: bool = True
    prompt_timing: str = "after_first_value"
    prompt_reason: WorkspaceSavePromptReason | None = None

    def __post_init__(self) -> None:
        for field_name in ("account_required", "save_available", "save_requires_account"):
            if not isinstance(getattr(self, field_name), bool):
                raise ValueError(f"SaveAccountHandoff.{field_name} must be a boolean.")
        if self.account_required:
            raise ValueError(
                "SaveAccountHandoff.account_required must be false before first value."
            )
        _require_non_empty(self.prompt_timing, "SaveAccountHandoff.prompt_timing")
        self.prompt_reason = _coerce_optional_enum(
            self.prompt_reason,
            WorkspaceSavePromptReason,
            "SaveAccountHandoff.prompt_reason",
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "account_required": self.account_required,
            "save_available": self.save_available,
            "save_requires_account": self.save_requires_account,
            "prompt_timing": self.prompt_timing,
            "prompt_reason": self.prompt_reason.value if self.prompt_reason else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SaveAccountHandoff":
        """Build SaveAccountHandoff from a mapping."""
        return cls(
            account_required=data.get("account_required", False),
            save_available=data.get("save_available", True),
            save_requires_account=data.get("save_requires_account", True),
            prompt_timing=data.get("prompt_timing", "after_first_value"),
            prompt_reason=data.get("prompt_reason"),
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize SaveAccountHandoff to deterministic JSON."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "SaveAccountHandoff":
        """Build SaveAccountHandoff from JSON text."""
        data = _json_object(text, "SaveAccountHandoff")
        return cls.from_dict(data)


@dataclass
class WorkspaceSafetyBoundary:
    """Safety boundary flags for a temporary workspace."""

    no_recommendations: bool = True
    no_order_execution: bool = True
    no_price_targets: bool = True
    user_judgment_required: bool = True
    local_or_temporary_context: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "no_recommendations",
            "no_order_execution",
            "no_price_targets",
            "user_judgment_required",
            "local_or_temporary_context",
        ):
            if getattr(self, field_name) is not True:
                raise ValueError(f"WorkspaceSafetyBoundary.{field_name} must be true.")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "no_recommendations": self.no_recommendations,
            "no_order_execution": self.no_order_execution,
            "no_price_targets": self.no_price_targets,
            "user_judgment_required": self.user_judgment_required,
            "local_or_temporary_context": self.local_or_temporary_context,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkspaceSafetyBoundary":
        """Build WorkspaceSafetyBoundary from a mapping."""
        return cls(
            no_recommendations=data.get("no_recommendations", True),
            no_order_execution=data.get("no_order_execution", True),
            no_price_targets=data.get("no_price_targets", True),
            user_judgment_required=data.get("user_judgment_required", True),
            local_or_temporary_context=data.get("local_or_temporary_context", True),
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize WorkspaceSafetyBoundary to deterministic JSON."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "WorkspaceSafetyBoundary":
        """Build WorkspaceSafetyBoundary from JSON text."""
        data = _json_object(text, "WorkspaceSafetyBoundary")
        return cls.from_dict(data)


@dataclass
class TemporaryWorkspace:
    """Top-level schema object for an unsaved temporary workspace."""

    workspace_id: str
    status: WorkspaceStatus
    created_at: str
    source_input: SourceInput
    classification: ClassificationResult
    detected_entities: list[DetectedEntity] = field(default_factory=list)
    uncertainties: list[WorkspaceUncertainty] = field(default_factory=list)
    missing_fields: list[WorkspaceMissingField] = field(default_factory=list)
    cards: list[WorkspaceCard] = field(default_factory=list)
    save_handoff: SaveAccountHandoff = field(default_factory=SaveAccountHandoff)
    safety_boundary: WorkspaceSafetyBoundary = field(default_factory=WorkspaceSafetyBoundary)

    def __post_init__(self) -> None:
        _require_non_empty(self.workspace_id, "TemporaryWorkspace.workspace_id")
        self.status = _coerce_enum(self.status, WorkspaceStatus, "TemporaryWorkspace.status")
        _require_non_empty(self.created_at, "TemporaryWorkspace.created_at")
        if not isinstance(self.source_input, SourceInput):
            raise ValueError("TemporaryWorkspace.source_input must be a SourceInput.")
        if not isinstance(self.classification, ClassificationResult):
            raise ValueError(
                "TemporaryWorkspace.classification must be a ClassificationResult."
            )
        self.detected_entities = _objects(
            self.detected_entities, DetectedEntity, "TemporaryWorkspace.detected_entities"
        )
        self.uncertainties = _objects(
            self.uncertainties, WorkspaceUncertainty, "TemporaryWorkspace.uncertainties"
        )
        self.missing_fields = _objects(
            self.missing_fields, WorkspaceMissingField, "TemporaryWorkspace.missing_fields"
        )
        self.cards = _objects(self.cards, WorkspaceCard, "TemporaryWorkspace.cards")
        if not isinstance(self.save_handoff, SaveAccountHandoff):
            raise ValueError("TemporaryWorkspace.save_handoff must be a SaveAccountHandoff.")
        if not isinstance(self.safety_boundary, WorkspaceSafetyBoundary):
            raise ValueError(
                "TemporaryWorkspace.safety_boundary must be a WorkspaceSafetyBoundary."
            )
        if self.status == WorkspaceStatus.TEMPORARY and self.save_handoff.account_required:
            raise ValueError(
                "TemporaryWorkspace.save_handoff.account_required must be false for "
                "temporary workspaces."
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation preserving canonical values."""
        return {
            "workspace_id": self.workspace_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "source_input": self.source_input.to_dict(),
            "classification": self.classification.to_dict(),
            "detected_entities": [entity.to_dict() for entity in self.detected_entities],
            "uncertainties": [uncertainty.to_dict() for uncertainty in self.uncertainties],
            "missing_fields": [missing.to_dict() for missing in self.missing_fields],
            "cards": [card.to_dict() for card in self.cards],
            "save_handoff": self.save_handoff.to_dict(),
            "safety_boundary": self.safety_boundary.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TemporaryWorkspace":
        """Build TemporaryWorkspace from a mapping."""
        return cls(
            workspace_id=data.get("workspace_id", ""),
            status=data.get("status", ""),
            created_at=data.get("created_at", ""),
            source_input=SourceInput.from_dict(_required_object(data, "source_input")),
            classification=ClassificationResult.from_dict(
                _required_object(data, "classification")
            ),
            detected_entities=[
                DetectedEntity.from_dict(item)
                for item in _list_of_dicts(
                    data.get("detected_entities", []),
                    "TemporaryWorkspace.detected_entities",
                )
            ],
            uncertainties=[
                WorkspaceUncertainty.from_dict(item)
                for item in _list_of_dicts(
                    data.get("uncertainties", []), "TemporaryWorkspace.uncertainties"
                )
            ],
            missing_fields=[
                WorkspaceMissingField.from_dict(item)
                for item in _list_of_dicts(
                    data.get("missing_fields", []), "TemporaryWorkspace.missing_fields"
                )
            ],
            cards=[
                WorkspaceCard.from_dict(item)
                for item in _list_of_dicts(data.get("cards", []), "TemporaryWorkspace.cards")
            ],
            save_handoff=SaveAccountHandoff.from_dict(
                _optional_object(data, "save_handoff", "TemporaryWorkspace.save_handoff")
            ),
            safety_boundary=WorkspaceSafetyBoundary.from_dict(
                _optional_object(data, "safety_boundary", "TemporaryWorkspace.safety_boundary")
            ),
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize TemporaryWorkspace to deterministic JSON."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "TemporaryWorkspace":
        """Build TemporaryWorkspace from JSON text."""
        data = _json_object(text, "TemporaryWorkspace")
        return cls.from_dict(data)


def _objects(values: list[Any], object_type: type[Any], field_name: str) -> list[Any]:
    if not isinstance(values, list):
        raise ValueError(f"{field_name} must be a list.")
    if not all(isinstance(item, object_type) for item in values):
        raise ValueError(f"{field_name} must contain only {object_type.__name__} objects.")
    return list(values)


def _required_object(data: dict[str, Any], field_name: str) -> dict[str, Any]:
    value = data.get(field_name)
    if not isinstance(value, dict):
        raise ValueError(f"TemporaryWorkspace.{field_name} must be an object.")
    return value


def _optional_object(
    data: dict[str, Any], field_name: str, display_field_name: str
) -> dict[str, Any]:
    if field_name not in data:
        return {}
    value = data[field_name]
    if not isinstance(value, dict):
        raise ValueError(f"{display_field_name} must be an object.")
    return value


def _json_object(text: str, model_name: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{model_name} JSON is invalid: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{model_name} JSON must be an object.")
    return data
