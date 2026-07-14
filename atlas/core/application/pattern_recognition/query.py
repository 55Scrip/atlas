"""PatternRecognitionQuery — runs registered strategies over a DecisionTimeline (ATLAS-005).

Depends only on DecisionTimelineQuery (ATLAS-004) and the
PatternRecognitionStrategy protocol — never a repository or Engine
directly. Never calls .add(...) on anything; Pattern Recognition only
reads what Decision Timeline already assembled.
"""
from __future__ import annotations

from atlas.core.application.decision_timeline.query import DecisionTimelineQuery
from atlas.core.application.pattern_recognition.recognized_pattern import RecognizedPattern
from atlas.core.application.pattern_recognition.strategies import PatternRecognitionStrategy


class PatternRecognitionQuery:
    def __init__(
        self,
        decision_timeline_query: DecisionTimelineQuery,
        strategies: tuple[PatternRecognitionStrategy, ...],
    ) -> None:
        self._decision_timeline_query = decision_timeline_query
        self._strategies = strategies

    def build(self) -> tuple[RecognizedPattern, ...]:
        timeline = self._decision_timeline_query.build()
        results: list[RecognizedPattern] = []
        for strategy in self._strategies:
            results.extend(strategy.recognize(timeline))
        return tuple(results)
