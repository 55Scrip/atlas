"""DecisionReflection — the presented artifact of one occasion-bound correspondence (ATLAS-007).

A DecisionReflection is not the domain concept itself (ATLAS-007-D): it
is occasion-bound by nature (§2 of the domain chapter) — unlike Pattern
or Strategy Signature, it has no standing existence independent of the
moment it is drawn, since half of what it connects (the in-progress
reasoning context) has no fixed state at any other moment. There is
therefore no "DecisionReflection vs. DecisionReflection Recognition"
split the way Pattern/Strategy Signature required — it is intrinsically
an act, never persisted, never compared across occasions.

`pattern` is always the specific RecognizedPattern whose structured
matching_key corresponds to the current ReasoningContext (ATLAS-007-D
§3/invariant 13). `strategy_signature`, when present, is attached only
because `pattern` is itself one of its member_patterns (invariant 14) —
never asserted independently. `description` is presentation only,
assembled after the correspondence is already established from the
member Pattern's (and, where present, Strategy Signature's) own already-
generated descriptions — it carries no prediction, evaluation, or
recommendation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.core.application.pattern_recognition.recognized_pattern import RecognizedPattern
from atlas.core.application.strategy_signature.recognized_strategy_signature import (
    RecognizedStrategySignature,
)


@dataclass(frozen=True)
class DecisionReflection:
    pattern: RecognizedPattern
    strategy_signature: RecognizedStrategySignature | None
    description: str
    reflected_at: datetime
