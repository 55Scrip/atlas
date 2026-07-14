"""Pattern Recognition strategies (ATLAS-005).

A PatternRecognitionStrategy is a pure function of an already-assembled
DecisionTimeline: it never touches a repository or an Engine, and it
never writes anything. Different strategies may legitimately recognize
different RecognizedPatterns from the same recorded history — this
module never merges, deduplicates, or ranks across strategies.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Protocol

from atlas.core.application.decision_timeline.timeline import DecisionTimeline
from atlas.core.application.pattern_recognition.recognized_pattern import RecognizedPattern
from atlas.core.domain.decision.entity import Decision


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PatternRecognitionStrategy(Protocol):
    def recognize(self, timeline: DecisionTimeline) -> tuple[RecognizedPattern, ...]:
        ...


class SameSubjectAndTypeStrategy:
    """Recognizes two or more Decisions sharing the same subject and decision type.

    Uses only exact equality on already-structured fields — no text
    similarity, no heuristic scoring — so every result is trivially
    explainable and traceable back to the Decisions it names.
    """

    name = "same_subject_and_type"

    def __init__(self, clock=_utc_now) -> None:
        self._clock = clock

    def recognize(self, timeline: DecisionTimeline) -> tuple[RecognizedPattern, ...]:
        groups: dict[tuple[str, str], list[Decision]] = defaultdict(list)
        for entry in timeline.entries:
            decision = entry.decision
            key = (decision.subject.value, decision.decision_type.value)
            groups[key].append(decision)

        recognized_at = self._clock()
        results: list[RecognizedPattern] = []
        for (subject, decision_type), decisions in groups.items():
            if len(decisions) < 2:
                continue
            member_decision_ids = tuple(decision.id for decision in decisions)
            description = f"You have made {len(decisions)} {decision_type} decisions on {subject}."
            results.append(
                RecognizedPattern(
                    strategy_name=self.name,
                    member_decision_ids=member_decision_ids,
                    description=description,
                    recognized_at=recognized_at,
                    matching_key=(subject, decision_type),
                )
            )
        return tuple(results)


class SameConfidenceStrategy:
    """Recognizes two or more Decisions sharing the identical confidence value.

    Uses only exact equality on Confidence.value — no bucketing, no
    threshold, no heuristic — so every result is trivially explainable
    and traceable, exactly mirroring SameSubjectAndTypeStrategy's own
    discipline applied to a different structured field.
    """

    name = "same_confidence"

    def __init__(self, clock=_utc_now) -> None:
        self._clock = clock

    def recognize(self, timeline: DecisionTimeline) -> tuple[RecognizedPattern, ...]:
        groups: dict[int, list[Decision]] = defaultdict(list)
        for entry in timeline.entries:
            decision = entry.decision
            groups[decision.confidence.value].append(decision)

        recognized_at = self._clock()
        results: list[RecognizedPattern] = []
        for confidence_value, decisions in groups.items():
            if len(decisions) < 2:
                continue
            member_decision_ids = tuple(decision.id for decision in decisions)
            description = (
                f"You recorded confidence {confidence_value} on "
                f"{len(decisions)} separate Decisions."
            )
            results.append(
                RecognizedPattern(
                    strategy_name=self.name,
                    member_decision_ids=member_decision_ids,
                    description=description,
                    recognized_at=recognized_at,
                    matching_key=(str(confidence_value),),
                )
            )
        return tuple(results)
