"""Decision Coach — at most one fixed, pre-verified coaching question (ATLAS-008).

Decision Coach requires no infrastructure layer at all: its only input
is a DecisionReflection (ATLAS-007) already computed by someone else.
No repository, no Engine, no independent query of Pattern Recognition,
Strategy Signature Recognition, or Decision Timeline exists anywhere in
this module — enforced structurally, not by discipline alone.

Both templates below are fixed at design time and verified here, once,
against ATLAS-008-D's invariant 10 (either-answer test) and invariant 16
(no hidden conclusion) — never generated or checked per-occasion, since
this system has no semantic-inference capability and must not gain one
here. Dispatch between them is the only thing that varies: which fixed
string applies, never how either string is worded.
"""
from __future__ import annotations

from atlas.core.application.decision_coach.coaching_question import CoachingQuestion
from atlas.core.application.decision_reflection.reflection import DecisionReflection

# Either-answer test (invariant 10): "similar or different" offers two
# symmetric, equally-weighted directions with neither foregrounded, and
# the trailing "if anything" explicitly permits a third, equally valid
# answer — no meaningful correspondence at all. Coach has no preference
# among any of these, and any answer, or none, is equally acceptable.
#
# No-hidden-conclusion (invariant 16): no evaluation, no recommendation,
# no presumed concern, no expected answer, and no restated fact — "what
# you just saw" / "the broader connection you just saw" refers back to
# what Decision Reflection already displayed immediately beforehand,
# rather than repeating it. Strategy Signatures are never called a
# "pattern" here, to avoid conflating the two domain concepts.
_PATTERN_ONLY_QUESTION = (
    "What's similar or different about this situation compared with what "
    "you just saw, if anything?"
)
_SIGNATURE_QUESTION = (
    "What's similar or different about this situation compared with the "
    "broader connection you just saw, if anything?"
)


def select_coaching_question(reflection: DecisionReflection | None) -> CoachingQuestion | None:
    if reflection is None:
        return None
    text = _PATTERN_ONLY_QUESTION if reflection.strategy_signature is None else _SIGNATURE_QUESTION
    return CoachingQuestion(text=text, reflection=reflection)
