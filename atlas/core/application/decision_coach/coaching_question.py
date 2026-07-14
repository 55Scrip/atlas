"""CoachingQuestion — the presented artifact of one Decision Coach engagement (ATLAS-008).

A CoachingQuestion is not the domain concept itself (ATLAS-008-D): a
coaching engagement is occasion-bound, for the same reason Decision
Reflection is (ATLAS-007-D §2) — it has no existence independent of the
specific engagement in which it occurs. There is therefore no "Decision
Coach vs. Decision Coach Recognition" split, exactly as none was needed
for Decision Reflection.

`text` contains only the question itself — never a restated fact from
`reflection.pattern`/`reflection.strategy_signature`. Decision Reflection
has already displayed that content immediately beforehand; repeating it
here would make Coach's own utterance a statement followed by a
question, not a question (ATLAS-008-D invariant: every Coach utterance
is functionally a question). `reflection` is retained only for
traceability (invariant 9) — never persisted, never compared across
occasions.
"""
from __future__ import annotations

from dataclasses import dataclass

from atlas.core.application.decision_reflection.reflection import DecisionReflection


@dataclass(frozen=True)
class CoachingQuestion:
    text: str
    reflection: DecisionReflection
