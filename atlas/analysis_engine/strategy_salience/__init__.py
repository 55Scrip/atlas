"""Strategic Salience v1.

Evidence about which parts of a company's observed strategy its calls
appear to be organised around. A read model over records Atlas already
holds: it stores nothing, fetches nothing, produces no score, and is
imported by nothing in the analysis or decision path.
"""
from atlas.analysis_engine.strategy_salience.analysis import (
    SALIENCE_VERSION,
    classify_role,
    company_salience,
    speaker_identity,
)
from atlas.analysis_engine.strategy_salience.contracts import (
    CallSection,
    SignalSource,
    SpeakerRole,
)
from atlas.analysis_engine.strategy_salience.models import (
    AnalystAttention,
    ForwardEvidenceLink,
    GraphLinkage,
    PassageRef,
    PriorityLanguage,
    SalienceEvidence,
    SpeakerMention,
)
from atlas.analysis_engine.strategy_salience.render import render_salience

__all__ = [
    "AnalystAttention",
    "CallSection",
    "ForwardEvidenceLink",
    "GraphLinkage",
    "PassageRef",
    "PriorityLanguage",
    "SALIENCE_VERSION",
    "SalienceEvidence",
    "SignalSource",
    "SpeakerMention",
    "SpeakerRole",
    "classify_role",
    "company_salience",
    "render_salience",
    "speaker_identity",
]
