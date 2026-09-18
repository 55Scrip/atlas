"""Strategic Action Attribution v1.

What evidence, if any, links an observed action to a specific strategy
rather than to the company as a whole. A read model over records Atlas
already holds: it stores nothing, fetches nothing, produces no score, and
is imported by nothing in the analysis or decision path.
"""
from atlas.analysis_engine.strategy_attribution.analysis import (
    ATTRIBUTOR_VERSION,
    SEARCHED_CHANNELS,
    UNAVAILABLE_CHANNELS,
    company_attribution,
    extract_linking_facts,
)
from atlas.analysis_engine.strategy_attribution.contracts import (
    ActionTense,
    AttributionBasis,
    AttributionResolution,
    AttributionStatus,
    EvidenceRole,
)
from atlas.analysis_engine.strategy_attribution.models import (
    ActionAttribution,
    AttributedAmount,
    CompanyAttribution,
    EvidenceRef,
    LinkingFact,
)
from atlas.analysis_engine.strategy_attribution.render import render_attribution

__all__ = [
    "ATTRIBUTOR_VERSION",
    "ActionAttribution",
    "ActionTense",
    "AttributedAmount",
    "AttributionBasis",
    "AttributionResolution",
    "AttributionStatus",
    "CompanyAttribution",
    "EvidenceRef",
    "EvidenceRole",
    "LinkingFact",
    "SEARCHED_CHANNELS",
    "UNAVAILABLE_CHANNELS",
    "company_attribution",
    "extract_linking_facts",
    "render_attribution",
]
