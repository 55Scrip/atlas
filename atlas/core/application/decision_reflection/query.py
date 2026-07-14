"""DecisionReflectionQuery — finds at most one occasion-bound correspondence (ATLAS-007).

Depends only on PatternRecognitionQuery and StrategySignatureRecognitionQuery
— never a repository, an Engine, a DecisionTimelineQuery, or a Decision
directly. No Decision lookup: matching is pure tuple-of-strings equality
against RecognizedPattern.matching_key (ATLAS-007 Prerequisite A), never
by parsing `description` or dereferencing `member_decision_ids`.

Pattern Recognition runs exactly once per reflect() call. That single
tuple of RecognizedPattern is used both to find the winning Pattern and
as the direct argument to
StrategySignatureRecognitionQuery.recognize(...) (ATLAS-007
Prerequisite B) — never .build(), which would trigger a second,
independent Pattern Recognition pass and produce RecognizedPattern
objects with different recognized_at values than the ones already
matched, silently breaking `winning_pattern in signature.member_patterns`.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from atlas.core.application.decision_reflection.reasoning_context import ReasoningContext
from atlas.core.application.decision_reflection.reflection import DecisionReflection
from atlas.core.application.pattern_recognition.query import PatternRecognitionQuery
from atlas.core.application.pattern_recognition.recognized_pattern import RecognizedPattern
from atlas.core.application.strategy_signature.query import StrategySignatureRecognitionQuery


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _same_subject_and_type_key(context: ReasoningContext) -> tuple[str, ...] | None:
    if not context.subject or not context.decision_type:
        return None
    return (context.subject, context.decision_type)


def _same_confidence_key(context: ReasoningContext) -> tuple[str, ...] | None:
    if context.confidence is None:
        return None
    return (str(context.confidence),)


_MATCHING_KEY_DERIVERS: dict[str, Callable[[ReasoningContext], tuple[str, ...] | None]] = {
    "same_subject_and_type": _same_subject_and_type_key,
    "same_confidence": _same_confidence_key,
}

_STRATEGY_PRIORITY: tuple[str, ...] = ("same_subject_and_type", "same_confidence")


def _describe(pattern: RecognizedPattern, strategy_signature) -> str:
    description = f"This resembles a recognized Pattern: {pattern.description}"
    if strategy_signature is not None:
        description += (
            f" This Pattern is part of a broader recognized Strategy Signature: "
            f"{strategy_signature.description}"
        )
    return description


class DecisionReflectionQuery:
    def __init__(
        self,
        pattern_recognition_query: PatternRecognitionQuery,
        strategy_signature_recognition_query: StrategySignatureRecognitionQuery,
        clock=_utc_now,
    ) -> None:
        self._pattern_recognition_query = pattern_recognition_query
        self._strategy_signature_recognition_query = strategy_signature_recognition_query
        self._clock = clock

    def reflect(self, context: ReasoningContext) -> DecisionReflection | None:
        recognized_patterns = self._pattern_recognition_query.build()

        winning_pattern: RecognizedPattern | None = None
        for strategy_name in _STRATEGY_PRIORITY:
            current_key = _MATCHING_KEY_DERIVERS[strategy_name](context)
            if current_key is None:
                continue
            for pattern in recognized_patterns:
                if pattern.strategy_name == strategy_name and pattern.matching_key == current_key:
                    winning_pattern = pattern
                    break
            if winning_pattern is not None:
                break

        if winning_pattern is None:
            return None

        signatures = self._strategy_signature_recognition_query.recognize(recognized_patterns)
        containing_signature = next(
            (
                signature
                for signature in signatures
                if winning_pattern in signature.member_patterns
            ),
            None,
        )

        return DecisionReflection(
            pattern=winning_pattern,
            strategy_signature=containing_signature,
            description=_describe(winning_pattern, containing_signature),
            reflected_at=self._clock(),
        )
