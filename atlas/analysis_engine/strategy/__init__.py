"""Strategy & Dependency Intelligence, v1.

A deterministic read model over evidence Atlas already persists. It
stores nothing, calls no provider, and is imported by nothing in the
analysis or decision path -- see
`tests/unit/analysis_engine/strategy/test_integration_safety.py`.
"""
from atlas.analysis_engine.strategy.composition import (
    compose_company_strategy,
    find_cross_company_adjacencies,
)
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
from atlas.analysis_engine.strategy.render import render_adjacency, render_company_strategy

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
    "compose_company_strategy",
    "extract_strategy",
    "find_cross_company_adjacencies",
    "render_adjacency",
    "render_company_strategy",
]
