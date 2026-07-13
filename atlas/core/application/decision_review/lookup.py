"""Decision lookup for selection (ATLAS-003).

Built entirely on DecisionRepository's existing, unmodified interface —
list_all() already returns every recorded Decision, so no new query
method is needed. Pure read: this module never calls
DecisionRepository.add(...) — Decision Review never modifies existing
reasoning history.
"""
from __future__ import annotations

from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.repository import DecisionRepository


def list_decisions_for_selection(repository: DecisionRepository) -> list[tuple[int, Decision]]:
    """Return every recorded Decision paired with a 1-based selection number."""
    return list(enumerate(repository.list_all(), start=1))


def format_decision_for_selection(number: int, decision: Decision) -> str:
    return (
        f"{number}. [{decision.decision_type.value}] {decision.subject.value} "
        f"(confidence {decision.confidence.value}, decided {decision.decided_at.date()})"
    )


def select_decision(numbered_decisions: list[tuple[int, Decision]], answer: str) -> Decision | None:
    """Resolve a person's typed selection number to a Decision.

    Returns None if the answer isn't a valid selection, so the caller can
    re-ask instead of guessing.
    """
    try:
        choice = int(answer.strip())
    except ValueError:
        return None
    for number, decision in numbered_decisions:
        if number == choice:
            return decision
    return None
