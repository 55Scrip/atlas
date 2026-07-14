"""Strategy Signature Recognition strategies (ATLAS-006).

A StrategySignatureRecognitionStrategy is a pure function of the
Patterns Pattern Recognition currently makes available: it never
touches a repository, an Engine, a DecisionTimeline, or performs a
Decision lookup — the only input type is RecognizedPattern.

Structural identity of a RecognizedStrategySignature is its ordered
member_patterns alone (ATLAS-006-P invariant 2) — strategy_name and
recognized_at are recognition metadata, not identity.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Protocol

from atlas.core.application.pattern_recognition.recognized_pattern import RecognizedPattern
from atlas.core.application.strategy_signature.recognized_strategy_signature import (
    RecognizedStrategySignature,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StrategySignatureRecognitionStrategy(Protocol):
    def recognize(
        self, recognized_patterns: tuple[RecognizedPattern, ...]
    ) -> tuple[RecognizedStrategySignature, ...]:
        ...


def _pattern_sort_key(pattern: RecognizedPattern) -> tuple[str, tuple]:
    return (
        pattern.strategy_name,
        tuple(decision_id.value for decision_id in pattern.member_decision_ids),
    )


def _share_a_decision(a: RecognizedPattern, b: RecognizedPattern) -> bool:
    return bool(set(a.member_decision_ids) & set(b.member_decision_ids))


class ConnectedPatternsStrategy:
    """Recognizes maximal connected components in the Pattern-overlap graph.

    Two Patterns are adjacent when they share at least one Decision id
    (pure set-intersection over already-structured DecisionId values —
    no description parsing, no Decision lookup, no heuristic). A
    Strategy Signature is the maximal connected set induced by that
    adjacency relation. Isolated Patterns (no edge to any other) form
    their own component of size one and produce no Signature —
    coherence requires two or more connected Patterns.
    """

    name = "connected_patterns"

    def __init__(self, clock=_utc_now) -> None:
        self._clock = clock

    def recognize(
        self, recognized_patterns: tuple[RecognizedPattern, ...]
    ) -> tuple[RecognizedStrategySignature, ...]:
        adjacency: dict[RecognizedPattern, set[RecognizedPattern]] = {
            pattern: set() for pattern in recognized_patterns
        }
        for i, pattern_a in enumerate(recognized_patterns):
            for pattern_b in recognized_patterns[i + 1 :]:
                if _share_a_decision(pattern_a, pattern_b):
                    adjacency[pattern_a].add(pattern_b)
                    adjacency[pattern_b].add(pattern_a)

        visited: set[RecognizedPattern] = set()
        components: list[list[RecognizedPattern]] = []
        for pattern in recognized_patterns:
            if pattern in visited:
                continue
            component: list[RecognizedPattern] = []
            queue: deque[RecognizedPattern] = deque([pattern])
            visited.add(pattern)
            while queue:
                current = queue.popleft()
                component.append(current)
                for neighbor in adjacency[current]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            components.append(component)

        recognized_at = self._clock()
        results: list[RecognizedStrategySignature] = []
        for component in components:
            if len(component) < 2:
                continue
            ordered_members = tuple(sorted(component, key=_pattern_sort_key))
            description = "; ".join(member.description for member in ordered_members)
            results.append(
                RecognizedStrategySignature(
                    strategy_name=self.name,
                    member_patterns=ordered_members,
                    description=description,
                    recognized_at=recognized_at,
                )
            )
        return tuple(
            sorted(
                results, key=lambda signature: _pattern_sort_key(signature.member_patterns[0])
            )
        )
