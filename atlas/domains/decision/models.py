from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class EvidenceCategory(str, Enum):
    """Supported evidence categories for decision reasoning."""

    PORTFOLIO = "Portfolio"
    COMPANY = "Company"
    MARKET = "Market"
    RISK = "Risk"
    VALUATION = "Valuation"
    TECHNICAL = "Technical"
    MACRO = "Macro"


class EvidenceStrength(str, Enum):
    """Deterministic evidence strength."""

    STRONG = "Strong"
    MODERATE = "Moderate"
    LIMITED = "Limited"
    MISSING = "Missing"


@dataclass(frozen=True)
class Decision:
    """Non-advisory decision under consideration."""

    id: str
    title: str
    subject: str
    purpose: str = "Understand evidence"


@dataclass(frozen=True)
class Evidence:
    """Fact used by the decision domain.

    Evidence contains facts only. Interpretation belongs in observations and
    reasoning steps.
    """

    id: str
    category: EvidenceCategory
    statement: str
    source: str
    strength: EvidenceStrength = EvidenceStrength.MODERATE
    data: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "data", _freeze_mapping(self.data or {}))


@dataclass(frozen=True)
class Observation:
    """Deterministic observation derived from evidence."""

    id: str
    category: EvidenceCategory
    statement: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class ReasoningStep:
    """Explainable reasoning step tied to evidence."""

    id: str
    statement: str
    evidence_ids: tuple[str, ...]
    observation_ids: tuple[str, ...]


@dataclass(frozen=True)
class Unknown:
    """Material missing information."""

    id: str
    question: str
    category: EvidenceCategory


@dataclass(frozen=True)
class Confidence:
    """Confidence score and explanation."""

    score: int
    level: str
    explanation: str
    drivers: tuple[str, ...]
    uncertainty: tuple[str, ...]


@dataclass(frozen=True)
class DecisionContext:
    """Structured context for deterministic decision reasoning."""

    decision: Decision
    evidence: tuple[Evidence, ...] = ()
    required_categories: tuple[EvidenceCategory, ...] = tuple(EvidenceCategory)


@dataclass(frozen=True)
class DecisionResult:
    """Explainable decision reasoning output without trade recommendations."""

    decision: Decision
    evidence: tuple[Evidence, ...]
    observations: tuple[Observation, ...]
    reasoning_steps: tuple[ReasoningStep, ...]
    unknowns: tuple[Unknown, ...]
    confidence: Confidence
    explanation: str


@dataclass(frozen=True)
class DecisionCard:
    """User-facing structured decision reasoning card."""

    summary: str
    evidence: tuple[Evidence, ...]
    key_observations: tuple[Observation, ...]
    unknowns: tuple[Unknown, ...]
    confidence: Confidence
    risks: tuple[str, ...]
    explanation: str


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType({str(key): _freeze_value(item) for key, item in value.items()})


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _freeze_mapping(value)
    if isinstance(value, list):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze_value(item) for item in value)
    if isinstance(value, frozenset):
        return frozenset(_freeze_value(item) for item in value)
    return value
