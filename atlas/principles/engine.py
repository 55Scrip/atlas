import re
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from atlas.conversation import ConversationResponse
    from atlas.intelligence import IntelligenceReport
    from atlas.reasoning import ReasoningReport
    from atlas.suitability import SuitabilityAssessment


class PrincipleCategory(str, Enum):
    USER_FIRST = "User First"
    CONTEXT_BEFORE_CONCLUSION = "Context Before Conclusion"
    PORTFOLIO_BEFORE_POSITION = "Portfolio Before Position"
    RISK_BEFORE_RETURN = "Risk Before Return"
    TRANSPARENCY = "Transparency"
    SUITABILITY = "Suitability"
    LONG_TERM_THINKING = "Long-term Thinking"
    HUMILITY = "Humility"
    EDUCATIONAL_VALUE = "Educational Value"
    CONSISTENCY = "Consistency"


class PrinciplesResult(str, Enum):
    PASS = "Pass"
    WARNING = "Warning"
    FAIL = "Fail"


@dataclass(frozen=True)
class AtlasPrinciple:
    category: PrincipleCategory
    statement: str
    positive_markers: tuple[str, ...]


@dataclass(frozen=True)
class PrincipleEvaluation:
    principle: AtlasPrinciple
    followed: bool
    reasoning: str


@dataclass(frozen=True)
class PrinciplesCheck:
    overall_result: PrinciplesResult
    principles_followed: tuple[PrincipleEvaluation, ...]
    principles_potentially_missing: tuple[PrincipleEvaluation, ...]
    guardrail_warnings: tuple[str, ...]
    missing_context: tuple[str, ...]
    suggested_improvements: tuple[str, ...]
    confidence: int


class PrinciplesEngine:
    def __init__(
        self,
        principles: tuple[AtlasPrinciple, ...] | None = None,
    ) -> None:
        self.principles = principles or DEFAULT_PRINCIPLES

    def check(self, text: str) -> PrinciplesCheck:
        normalized = _normalize(text)
        evaluations = tuple(
            _evaluate_principle(principle, normalized) for principle in self.principles
        )
        followed = tuple(item for item in evaluations if item.followed)
        missing = tuple(item for item in evaluations if not item.followed)
        guardrails = _guardrail_warnings(text)
        missing_context = _missing_context(normalized)
        result = _overall_result(guardrails, missing)
        return PrinciplesCheck(
            overall_result=result,
            principles_followed=followed,
            principles_potentially_missing=missing,
            guardrail_warnings=guardrails,
            missing_context=missing_context,
            suggested_improvements=_suggested_improvements(missing, guardrails, missing_context),
            confidence=_confidence(text, evaluations, guardrails),
        )


def render_principles_check(check: PrinciplesCheck) -> str:
    lines = [
        "Atlas Principles Check",
        "",
        f"Overall Principles Result: {check.overall_result.value}",
        f"Confidence: {check.confidence}/100",
        "",
        "Principles Followed",
    ]
    lines.extend(_render_evaluations(check.principles_followed))
    lines.extend(["", "Principles Potentially Missing"])
    lines.extend(_render_evaluations(check.principles_potentially_missing))
    lines.extend(
        [
            "",
            "Guardrail Warnings",
            *_render_list(check.guardrail_warnings),
            "",
            "Missing Context",
            *_render_list(check.missing_context),
            "",
            "Suggested Improvements",
            *_render_list(check.suggested_improvements),
            "",
            "Research Framing",
            (
                "This validates communication guardrails only. It does not create "
                "investment recommendations."
            ),
        ]
    )
    return "\n".join(lines)


def check_text_against_principles(text: str) -> PrinciplesCheck:
    return PrinciplesEngine().check(text)


def check_conversation_response(response: "ConversationResponse") -> PrinciplesCheck:
    text = "\n".join(
        (
            response.short_answer,
            *response.supporting_reasoning,
            *response.suggested_follow_up_questions,
        )
    )
    return check_text_against_principles(text)


def check_intelligence_report(report: "IntelligenceReport") -> PrinciplesCheck:
    from atlas.intelligence import render_intelligence_report

    return check_text_against_principles(render_intelligence_report(report))


def check_suitability_assessment(assessment: "SuitabilityAssessment") -> PrinciplesCheck:
    from atlas.suitability import render_suitability_assessment

    return check_text_against_principles(render_suitability_assessment(assessment))


def check_reasoning_report(report: "ReasoningReport") -> PrinciplesCheck:
    from atlas.reasoning import render_reasoning_report

    return check_text_against_principles(render_reasoning_report(report))


def _evaluate_principle(
    principle: AtlasPrinciple,
    normalized_text: str,
) -> PrincipleEvaluation:
    found_markers = [marker for marker in principle.positive_markers if marker in normalized_text]
    if found_markers:
        return PrincipleEvaluation(
            principle=principle,
            followed=True,
            reasoning=f"Detected principle marker: {found_markers[0]}.",
        )
    return PrincipleEvaluation(
        principle=principle,
        followed=False,
        reasoning="The text does not clearly show this principle.",
    )


def _guardrail_warnings(text: str) -> tuple[str, ...]:
    searchable = _normalize(_remove_quoted_text(text))
    warnings = []
    for phrase in PROHIBITED_LANGUAGE:
        pattern = r"\b" + re.escape(phrase).replace(r"\ ", r"\s+") + r"\b"
        if re.search(pattern, searchable):
            warnings.append(f"Guardrail language detected: {phrase}.")
    return tuple(warnings)


def _missing_context(normalized_text: str) -> tuple[str, ...]:
    missing = []
    if not _contains_any(normalized_text, ("profile", "investor", "goals", "objectives")):
        missing.append("Investor profile or stated objectives are not clearly referenced.")
    if not _contains_any(normalized_text, ("assumption", "missing", "uncertain", "confidence")):
        missing.append("Assumptions, uncertainty, or missing information are not explicit.")
    if not _contains_any(normalized_text, ("risk", "downside", "concern", "volatility")):
        missing.append("Risk context is not clearly surfaced.")
    return tuple(missing)


def _suggested_improvements(
    missing: tuple[PrincipleEvaluation, ...],
    guardrails: tuple[str, ...],
    missing_context: tuple[str, ...],
) -> tuple[str, ...]:
    improvements = []
    if guardrails:
        improvements.append("Replace directive or absolute language with contextual language.")
    for evaluation in missing[:4]:
        improvements.append(f"Add clearer support for {evaluation.principle.category.value}.")
    if missing_context:
        improvements.append("State relevant facts, assumptions, uncertainty, and missing context.")
    if not improvements:
        improvements.append("No major communication improvements were detected.")
    return tuple(improvements)


def _overall_result(
    guardrails: tuple[str, ...],
    missing: tuple[PrincipleEvaluation, ...],
) -> PrinciplesResult:
    if guardrails:
        return PrinciplesResult.FAIL
    if len(missing) >= 4:
        return PrinciplesResult.WARNING
    return PrinciplesResult.PASS


def _confidence(
    text: str,
    evaluations: tuple[PrincipleEvaluation, ...],
    guardrails: tuple[str, ...],
) -> int:
    if not text.strip():
        return 20
    followed_count = sum(1 for evaluation in evaluations if evaluation.followed)
    confidence = 50 + followed_count * 4
    if guardrails:
        confidence += 10
    if len(text.split()) < 12:
        confidence -= 16
    return max(0, min(100, confidence))


def _remove_quoted_text(text: str) -> str:
    without_double_quotes = re.sub(r'"[^"]*"', " ", text)
    without_single_quotes = re.sub(r"'[^']*'", " ", without_double_quotes)
    return without_single_quotes


def _normalize(text: str) -> str:
    return text.lower().replace("-", " ")


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _render_evaluations(evaluations: tuple[PrincipleEvaluation, ...]) -> list[str]:
    if not evaluations:
        return ["- None"]
    return [
        (
            f"- {evaluation.principle.category.value}: "
            f"{evaluation.principle.statement} {evaluation.reasoning}"
        )
        for evaluation in evaluations
    ]


def _render_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]


PROHIBITED_LANGUAGE = (
    "strong buy",
    "strong sell",
    "buy",
    "sell",
    "guaranteed",
    "can't lose",
    "cant lose",
    "risk free",
    "sure thing",
)


DEFAULT_PRINCIPLES = (
    AtlasPrinciple(
        category=PrincipleCategory.USER_FIRST,
        statement="Start from the investor's stated goals, profile and context.",
        positive_markers=("investor", "profile", "goals", "objectives", "context"),
    ),
    AtlasPrinciple(
        category=PrincipleCategory.CONTEXT_BEFORE_CONCLUSION,
        statement="Explain the relevant context before drawing conclusions.",
        positive_markers=("context", "because", "given", "based on", "depends"),
    ),
    AtlasPrinciple(
        category=PrincipleCategory.PORTFOLIO_BEFORE_POSITION,
        statement="If portfolio context exists, avoid evaluating an investment in isolation.",
        positive_markers=("portfolio", "holdings", "position", "concentration", "allocation"),
    ),
    AtlasPrinciple(
        category=PrincipleCategory.RISK_BEFORE_RETURN,
        statement="Surface important risks before upside.",
        positive_markers=("risk", "downside", "concern", "volatility", "uncertainty"),
    ),
    AtlasPrinciple(
        category=PrincipleCategory.TRANSPARENCY,
        statement="Clearly distinguish facts, assumptions, uncertainty and missing information.",
        positive_markers=("assumption", "uncertain", "missing", "confidence", "not enough"),
    ),
    AtlasPrinciple(
        category=PrincipleCategory.SUITABILITY,
        statement="Evaluate compatibility with the investor's objectives.",
        positive_markers=("suitable", "compatib", "objectives", "profile", "fit"),
    ),
    AtlasPrinciple(
        category=PrincipleCategory.LONG_TERM_THINKING,
        statement="Avoid encouraging unnecessary trading or short-term speculation.",
        positive_markers=("long term", "time horizon", "monitor", "unnecessary trading"),
    ),
    AtlasPrinciple(
        category=PrincipleCategory.HUMILITY,
        statement="Allow Atlas to say it does not know or lacks enough information.",
        positive_markers=("don't know", "not enough information", "plausible", "depends"),
    ),
    AtlasPrinciple(
        category=PrincipleCategory.EDUCATIONAL_VALUE,
        statement="Every response should help the user understand something better.",
        positive_markers=("why", "because", "understand", "explain", "learn"),
    ),
    AtlasPrinciple(
        category=PrincipleCategory.CONSISTENCY,
        statement="Responses should not contradict each other without explaining why.",
        positive_markers=("consistent", "contradict", "align", "conflict", "explain why"),
    ),
)
