"""ReasoningContext — the in-progress reasoning context a Decision Reflection reads (ATLAS-007).

A plain value object, deliberately decoupled from ConversationSession —
this module never imports anything from atlas.core.application.conversation.
The caller (the conversation CLI) constructs one from whatever fields
ConversationSession already exposes publicly; Decision Reflection has no
knowledge of ConversationStep, ConversationSession, or any
conversation-package type. This one-way dependency (conversation ->
decision_reflection, never the reverse) is what keeps "do not modify the
Core Loop" true by construction.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReasoningContext:
    subject: str | None = None
    decision_type: str | None = None
    confidence: int | None = None

    def __post_init__(self) -> None:
        # Mirrors Subject.__post_init__'s own normalization exactly (strip
        # only, no case folding) so a populated subject is in precisely
        # the same canonical form Subject.value will be once the Decision
        # is eventually captured — required for exact matching_key equality
        # against a RecognizedPattern's own (subject, decision_type) key.
        if self.subject is not None:
            object.__setattr__(self, "subject", self.subject.strip())
