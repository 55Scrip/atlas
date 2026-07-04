"""Temporary workspace schema dataclasses.

This package contains schema-only representations of Atlas temporary
workspaces. It does not classify input, render cards, persist workspaces, call
providers, or change CLI behavior.
"""

from atlas.temporary_workspace.schema import (
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

__all__ = [
    "ClassificationResult",
    "DetectedEntity",
    "SaveAccountHandoff",
    "SourceInput",
    "TemporaryWorkspace",
    "WorkspaceCard",
    "WorkspaceCardStatus",
    "WorkspaceCardType",
    "WorkspaceConfidence",
    "WorkspaceEntityType",
    "WorkspaceInputClassification",
    "WorkspaceMissingField",
    "WorkspaceMissingFieldRequiredness",
    "WorkspaceSafetyBoundary",
    "WorkspaceSavePromptReason",
    "WorkspaceStatus",
    "WorkspaceUncertainty",
    "WorkspaceUncertaintySeverity",
]
