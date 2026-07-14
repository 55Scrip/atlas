"""RecognizedPattern — the recorded artifact of one act of Pattern Recognition (ATLAS-005).

A RecognizedPattern is not the Pattern itself (ATLAS-005-D): the Pattern
is the structural recurrence, a fact about recorded history that exists
whether or not Atlas has found it. RecognizedPattern is what one Pattern
Recognition strategy produced when it looked — deliberately not named
Observation, to avoid colliding with the Core Loop's unrelated
Observation aggregate (API-003/ATLAS-001).

Not a domain aggregate: no identity of its own beyond its content, never
persisted, recomputed fresh every call — the same status already
established for DecisionTimeline/DecisionTimelineEntry (ATLAS-004).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.core.domain.decision.value_objects import DecisionId


@dataclass(frozen=True)
class RecognizedPattern:
    strategy_name: str
    member_decision_ids: tuple[DecisionId, ...]
    description: str
    recognized_at: datetime
