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

matching_key (ATLAS-007) is the canonical, structured grouping key each
strategy already computes internally to decide which Decisions belong
together — retained here, rather than discarded after grouping, so a
later consumer (Decision Reflection) can compare its own in-progress
context against a specific Pattern using exact equality on already-
structured values, never by parsing `description` (presentation only)
or dereferencing `member_decision_ids` (a Decision lookup). It is
ordinary structural content describing what the Pattern is about, not
incidental metadata like `recognized_at` — deliberately left as part of
this dataclass's default equality/hash (no `field(compare=False)`),
since it is a pure function of the same `(strategy, underlying
decisions)` pair that already determines `member_decision_ids` and
`description`: two Patterns that already agree on those necessarily
agree on `matching_key` too, so including it introduces no new
distinction for genuine, strategy-produced data. Defaulted to `()` so
every existing construction site — including every pre-ATLAS-007 test —
continues to work unchanged.
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
    matching_key: tuple[str, ...] = ()
