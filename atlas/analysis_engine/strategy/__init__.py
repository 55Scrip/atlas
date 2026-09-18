"""Strategy & Dependency Intelligence, v1.

A deterministic read model over evidence Atlas already persists. It
stores nothing, calls no provider, and is imported by nothing in the
analysis or decision path.
"""
from atlas.analysis_engine.strategy.contracts import (
    ContinuityState,
    EngineElementRole,
    EvidenceStatus,
    FactorClass,
    OutcomeKind,
    RelationKind,
    ResourceKind,
    StrategyNodeKind,
    StrategyRejectionReason,
    SupportPolarity,
)
from atlas.analysis_engine.strategy.extraction import EXTRACTOR_VERSION, extract_strategy
from atlas.analysis_engine.strategy.factors import resolve_factors, resolve_resources
from atlas.analysis_engine.strategy.models import (
    CompanyStrategy,
    CrossCompanyAdjacency,
    FactorParticipation,
    RejectedStrategyCandidate,
    StrategyEdge,
    StrategyEvidence,
    StrategyNode,
)

__all__ = [
    "CompanyStrategy",
    "ContinuityState",
    "CrossCompanyAdjacency",
    "EXTRACTOR_VERSION",
    "EngineElementRole",
    "EvidenceStatus",
    "FactorClass",
    "FactorParticipation",
    "OutcomeKind",
    "RejectedStrategyCandidate",
    "RelationKind",
    "ResourceKind",
    "StrategyEdge",
    "StrategyEvidence",
    "StrategyNode",
    "StrategyNodeKind",
    "StrategyRejectionReason",
    "SupportPolarity",
    "extract_strategy",
    "resolve_factors",
    "resolve_resources",
]
