"""Human-facing question copy for the First Decision Conversation
(ATLAS-002).

No Core Loop aggregate name is ever surfaced to the person — the words
"Observation," "Hypothesis," "Interpretation," "Evidence," "Conclusion,"
and "Decision" appear only in this codebase's own vocabulary, never in a
prompt. Two fields (Evidence's direction, Decision's decision_type) need
translating from the person's own words into the exact enum value the
existing, unmodified domain layer expects — a literal, deterministic
keyword lookup, not interpretation formed by the orchestrator itself. An
unrecognized answer returns None so the caller can re-ask rather than
guess.
"""
from __future__ import annotations

QUESTION_PROMPT = "What are you trying to figure out?"

OBSERVATION_SUBJECT_PROMPT = "What company, sector, or market is this about?"
OBSERVATION_STATEMENT_PROMPT = "What did you notice?"

INTERPRETATION_PROMPT = "Why does that matter — what do you think it suggests?"

HYPOTHESIS_PROMPT = "Based on that, what do you believe might be going on?"

EVIDENCE_STATEMENT_PROMPT = "What have you found that relates to that belief?"
EVIDENCE_DIRECTION_PROMPT = "Does that support it, or challenge it?"

CONCLUSION_PROMPT = "Given everything so far, what's your takeaway?"

DECISION_TYPE_PROMPT = "What are you deciding to do — buy, sell, hold, watch, or pass?"
DECISION_CONFIDENCE_PROMPT = "How confident are you, from 0 to 100?"

CLOSING_MESSAGE = (
    "Your decision has been recorded. There's nothing more to do right "
    "now — how it played out is something we'll only be able to talk "
    "about once time has actually passed."
)

# Decision succeeded and is permanently recorded either way — the only
# difference from CLOSING_MESSAGE is that the separate, additive
# Reasoning Trace write (Package M1) failed. Never returned instead of
# CLOSING_MESSAGE for any Decision-side failure, only for this second,
# independent write's own failure.
CLOSING_MESSAGE_REASONING_TRACE_FAILED = (
    "Your decision has been recorded. There's nothing more to do right "
    "now — how it played out is something we'll only be able to talk "
    "about once time has actually passed. (Note: the supporting "
    "reasoning trace could not be saved.)"
)

UNRECOGNIZED_DIRECTION_PROMPT = (
    "Sorry, I didn't catch that — does it support your belief, or challenge it?"
)
UNRECOGNIZED_DECISION_TYPE_PROMPT = (
    "Sorry, I didn't catch that — buy, sell, hold, watch, or pass?"
)

_DIRECTION_KEYWORDS: dict[str, str] = {
    "support": "SUPPORTS",
    "supports": "SUPPORTS",
    "supporting": "SUPPORTS",
    "confirms": "SUPPORTS",
    "confirm": "SUPPORTS",
    "yes": "SUPPORTS",
    "challenge": "CHALLENGES",
    "challenges": "CHALLENGES",
    "challenging": "CHALLENGES",
    "contradicts": "CHALLENGES",
    "contradict": "CHALLENGES",
    "against": "CHALLENGES",
    "no": "CHALLENGES",
}

_DECISION_TYPE_KEYWORDS: dict[str, str] = {
    "buy": "BUY",
    "sell": "SELL",
    "hold": "HOLD",
    "watch": "WATCH",
    "pass": "PASS",
}


def _first_matching_keyword(answer: str, keywords: dict[str, str]) -> str | None:
    """Find the first known keyword appearing as a whole word in the
    answer — the person may say a full sentence ("it supports it"), not
    just the bare keyword.
    """
    words = answer.strip().lower().split()
    for word in words:
        stripped = word.strip(".,!?;:")
        if stripped in keywords:
            return keywords[stripped]
    return None


def parse_direction(answer: str) -> str | None:
    """Translate the person's own words into Direction's SUPPORTS/CHALLENGES.

    Returns None if the answer doesn't contain a known keyword, so the
    caller can re-ask instead of guessing.
    """
    return _first_matching_keyword(answer, _DIRECTION_KEYWORDS)


def parse_decision_type(answer: str) -> str | None:
    """Translate the person's own words into a DecisionType value.

    Returns None if the answer doesn't contain a known keyword, so the
    caller can re-ask instead of guessing.
    """
    return _first_matching_keyword(answer, _DECISION_TYPE_KEYWORDS)


def parse_confidence(answer: str) -> int | None:
    """Parse a 0-100 confidence answer. Returns None if not a valid integer
    in range, so the caller can re-ask instead of guessing.
    """
    try:
        value = int(answer.strip())
    except ValueError:
        return None
    if not (0 <= value <= 100):
        return None
    return value
