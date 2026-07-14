"""RecognizedStrategySignature — one act of Strategy Signature Recognition (ATLAS-006).

A RecognizedStrategySignature is not the Strategy Signature itself
(ATLAS-006-D): the Signature is the coherence among Patterns, a fact
that exists whether or not Atlas has found it. RecognizedStrategySignature
is what one Strategy Signature Recognition strategy produced when it
looked — deliberately not named StrategySignature, for the same reason
RecognizedPattern was not named Pattern (ATLAS-005).

Structural identity is the ordered set of member_patterns alone —
strategy_name and recognized_at are recognition metadata, describing
how and when a Signature was found, not which Signature it is
(ATLAS-006-P invariant 2). description is presentation only, generated
after membership has already been finalized by the adjacency relation,
and carries no authority over membership, identity, or coherence
(invariant 3).

Not a domain aggregate: no identity of its own beyond its content, never
persisted, recomputed fresh every call.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.core.application.pattern_recognition.recognized_pattern import RecognizedPattern


@dataclass(frozen=True)
class RecognizedStrategySignature:
    strategy_name: str
    member_patterns: tuple[RecognizedPattern, ...]
    description: str
    recognized_at: datetime
