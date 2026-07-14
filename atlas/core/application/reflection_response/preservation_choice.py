"""Preservation-choice keyword parsing (ATLAS-009).

A literal, deterministic keyword lookup — mirroring
conversation/prompts.py's own _first_matching_keyword pattern, but
living here rather than touching that Core-Loop-specific file. This is
a mechanical save/discard choice, not a coaching question, and is not
subject to Decision Coach's either-answer/no-hidden-conclusion tests
(ATLAS-008-D invariants 10/16 govern Coach's own substantive question,
not this preservation mechanism).
"""
from __future__ import annotations

_AFFIRMATIVE_KEYWORDS = {"yes", "y", "keep", "save", "preserve"}


def parse_preservation_choice(answer: str) -> bool:
    """Return True only on an explicit affirmative. Anything else —
    "no," silence, an unrecognized answer — discards the text, exactly
    as ATLAS-008's own default already does.
    """
    words = answer.strip().lower().split()
    for word in words:
        stripped = word.strip(".,!?;:")
        if stripped in _AFFIRMATIVE_KEYWORDS:
            return True
    return False
