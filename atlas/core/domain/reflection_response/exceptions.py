"""Domain errors for the ReflectionResponse aggregate (ATLAS-009)."""
from __future__ import annotations


class ReflectionResponseError(Exception):
    """Base class for all ReflectionResponse domain errors."""


class ReflectionResponseValidationError(ReflectionResponseError):
    """Raised when a ReflectionResponse or one of its value objects fails an invariant."""


class MissingResponseTextError(ReflectionResponseValidationError):
    """Raised when ResponseText is missing, or only whitespace."""


class MissingReflectionDescriptionError(ReflectionResponseValidationError):
    """Raised when the provenance snapshot's reflection_description is missing."""


class MissingCoachingQuestionTextError(ReflectionResponseValidationError):
    """Raised when the provenance snapshot's coaching_question_text is missing."""
