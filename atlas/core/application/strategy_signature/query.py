"""StrategySignatureRecognitionQuery — runs strategies over recognized Patterns (ATLAS-006).

Depends only on PatternRecognitionQuery (ATLAS-005/005B) and the
StrategySignatureRecognitionStrategy protocol — never a repository, an
Engine, or a DecisionTimelineQuery. Never calls .add(...) on anything;
Strategy Signature Recognition only reads what Pattern Recognition
already found.
"""
from __future__ import annotations

from atlas.core.application.pattern_recognition.query import PatternRecognitionQuery
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

    def build(self) -> tuple[RecognizedStrategySignature, ...]:
        recognized_patterns = self._pattern_recognition_query.build()
        results: list[RecognizedStrategySignature] = []
        for strategy in self._strategies:
            results.extend(strategy.recognize(recognized_patterns))
        return tuple(results)
