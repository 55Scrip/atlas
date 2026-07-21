"""Human-facing question copy for Decision Review (ATLAS-003).

No Core Loop aggregate name is surfaced beyond what the Decision
selection list itself needs to show — the three review questions
themselves never mention "Outcome," "Evaluation," or "Learning."
"""
from __future__ import annotations

SELECTION_HEADER = "Which decision would you like to review?"
SELECTION_REASK_PROMPT = "Sorry, I didn't catch that — please type the number of a decision."
NO_DECISIONS_MESSAGE = (
    "There are no recorded decisions to review yet. Have a First Decision "
    "Conversation first."
)

OUTCOME_PROMPT = "Looking back, what actually happened?"
EVALUATION_PROMPT = "How did that compare to what you expected?"
LEARNING_PROMPT = "What will you take from this for next time?"

CLOSING_MESSAGE = "Thanks — this review has been recorded."

# The review itself (Outcome/Evaluation/Learning) succeeded either way —
# the only difference from CLOSING_MESSAGE is that the separate,
# additive canonical Judgment write (Package M2) failed. Never returned
# for any Outcome/Evaluation/Learning failure, only for this second,
# independent write's own failure.
CLOSING_MESSAGE_JUDGMENT_FAILED = (
    "Thanks — this review has been recorded. (Note: the supporting "
    "characterization could not be saved.)"
)
