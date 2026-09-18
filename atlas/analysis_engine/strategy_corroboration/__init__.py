"""Strategic Corroboration v1.

What observable evidence outside management's own emphasis supports,
weakens, or fails to corroborate a stated strategy. A read model over
records Atlas already holds: it stores nothing, fetches nothing, produces
no score, and is imported by nothing in the analysis or decision path.
"""
from atlas.analysis_engine.strategy_corroboration.analysis import (
    CORROBORATOR_VERSION,
    EXCLUDED_CHANNELS,
    company_corroboration,
    temporal_relation,
)
from atlas.analysis_engine.strategy_corroboration.contracts import (
    CorroborationRelation,
    CoverageState,
    EvidenceClass,
    IndependenceChannel,
    TemporalRelation,
)
from atlas.analysis_engine.strategy_corroboration.models import (
    CompanyCorroboration,
    CorroborationItem,
    NodeCorroboration,
    ObservedEvidence,
)
from atlas.analysis_engine.strategy_corroboration.render import render_corroboration

__all__ = [
    "CORROBORATOR_VERSION",
    "CompanyCorroboration",
    "CorroborationItem",
    "CorroborationRelation",
    "CoverageState",
    "EXCLUDED_CHANNELS",
    "EvidenceClass",
    "IndependenceChannel",
    "NodeCorroboration",
    "ObservedEvidence",
    "TemporalRelation",
    "company_corroboration",
    "render_corroboration",
    "temporal_relation",
]
