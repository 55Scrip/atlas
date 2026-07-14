"""StrategySignatureRecognitionQuery — runs strategies over recognized Patterns (ATLAS-006).

Depends only on PatternRecognitionQuery (ATLAS-005/005B) and the
StrategySignatureRecognitionStrategy protocol — never a repository, an
Engine, or a DecisionTimelineQuery. Never calls .add(...) on anything;
Strategy Signature Recognition only reads what Pattern Recognition
already found.

recognize(recognized_patterns) (ATLAS-007) is an additive entry point
for callers that already hold one authoritative tuple of
RecognizedPattern — most notably Decision Reflection, which must run
Pattern Recognition exactly once per occasion and thread that single
snapshot through to Strategy Signature Recognition too. Calling build()
a second time would invoke PatternRecognitionQuery.build() again, which
stamps a fresh recognized_at on every RecognizedPattern it returns —
producing objects that are unequal to the ones already matched
elsewhere, even though they describe the same underlying Patterns.
build() itself is unchanged in observable behavior: it simply delegates
through recognize() after fetching its own single snapshot.
"""
from __future__ import annotations

from atlas.core.application.pattern_recognition.query import PatternRecognitionQuery
from atlas.core.application.pattern_recognition.recognized_pattern import RecognizedPattern
from atlas.core.application.strategy_signature.recognized_strategy_signature import (
    RecognizedStrategySignature,
)
from atlas.core.application.strategy_signature.strategies import (
    StrategySignatureRecognitionStrategy,
)


class StrategySignatureRecognitionQuery:
    def __init__(
        self,
        pattern_recognition_query: PatternRecognitionQuery,
        strategies: tuple[StrategySignatureRecognitionStrategy, ...],
    ) -> None:
        self._pattern_recognition_query = pattern_recognition_query
        self._strategies = strategies

    def recognize(
        self, recognized_patterns: tuple[RecognizedPattern, ...]
    ) -> tuple[RecognizedStrategySignature, ...]:
        results: list[RecognizedStrategySignature] = []
        for strategy in self._strategies:
            results.extend(strategy.recognize(recognized_patterns))
        return tuple(results)

    def build(self) -> tuple[RecognizedStrategySignature, ...]:
        return self.recognize(self._pattern_recognition_query.build())
