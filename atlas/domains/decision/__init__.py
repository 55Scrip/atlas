"""Decision domain foundation.

Transforms structured evidence into explainable, non-advisory reasoning.
"""

from atlas.domains.decision.engine import DecisionEngine, EvidenceEngine, ReasoningEngine
from atlas.domains.decision.models import (
    Confidence,
    Decision,
    DecisionCard,
    DecisionContext,
    DecisionResult,
    Evidence,
    EvidenceCategory,
    EvidenceStrength,
    Observation,
    ReasoningStep,
    Unknown,
)

__all__ = [
    "Confidence",
    "Decision",
    "DecisionCard",
    "DecisionContext",
    "DecisionEngine",
    "DecisionResult",
    "Evidence",
    "EvidenceCategory",
    "EvidenceEngine",
    "EvidenceStrength",
    "Observation",
    "ReasoningEngine",
    "ReasoningStep",
    "Unknown",
]
