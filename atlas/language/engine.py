import re
from dataclasses import dataclass
from enum import Enum


class ReasoningDepth(str, Enum):
    BOTTOM_LINE = "Bottom Line"
    REASONING = "Reasoning"
    FULL_REASONING = "Full Reasoning"


class ConfidenceLevel(str, Enum):
    VERY_HIGH = "Very High"
    HIGH = "High"
    MODERATE = "Moderate"
    LOW = "Low"
    VERY_LOW = "Very Low"


@dataclass(frozen=True)
class AtlasRating:
    value: str
    explanation: str
    is_recommendation: bool = False


@dataclass(frozen=True)
class AtlasView:
    value: str
    explanation: str


@dataclass(frozen=True)
class AtlasFit:
    value: str
    explanation: str


@dataclass(frozen=True)
class AtlasConfidence:
    overall_confidence: int
    confidence_level: ConfidenceLevel
    key_confidence_drivers: tuple[str, ...]
    uncertainty_drivers: tuple[str, ...]
    missing_information: tuple[str, ...]


@dataclass(frozen=True)
class AtlasThesis:
    current_thesis: str
    supporting_evidence: tuple[str, ...]
    counter_arguments: tuple[str, ...]
    what_could_change_view: tuple[str, ...]
    what_atlas_is_monitoring: tuple[str, ...]


@dataclass(frozen=True)
class AtlasRationale:
    bottom_line: str
    key_reasons: tuple[str, ...]
    main_risk: str
    optional_follow_up_questions: tuple[str, ...] = ()


@dataclass(frozen=True)
class AtlasLanguageReport:
    rating: AtlasRating
    view: AtlasView
    fit: AtlasFit
    confidence: AtlasConfidence
    thesis: AtlasThesis
    rationale: AtlasRationale
    reasoning_depths: tuple[ReasoningDepth, ...]
    engines_used: tuple[str, ...]
    guardrail_warnings: tuple[str, ...]
    principles: tuple[str, ...]


class AtlasLanguageEngine:
    def build_report(
        self,
        rating: AtlasRating,
        view: AtlasView,
        fit: AtlasFit,
        confidence: AtlasConfidence,
        thesis: AtlasThesis,
        rationale: AtlasRationale,
        engines_used: tuple[str, ...] = (),
    ) -> AtlasLanguageReport:
        rendered_source = _render_source_text(rating, view, fit, confidence, thesis, rationale)
        return AtlasLanguageReport(
            rating=_safe_rating(rating),
            view=view,
            fit=fit,
            confidence=confidence,
            thesis=thesis,
            rationale=_safe_rationale(rationale),
            reasoning_depths=(
                ReasoningDepth.BOTTOM_LINE,
                ReasoningDepth.REASONING,
                ReasoningDepth.FULL_REASONING,
            ),
            engines_used=engines_used,
            guardrail_warnings=self.guardrail_warnings(rendered_source),
            principles=ATLAS_LANGUAGE_PRINCIPLES,
        )

    def example_report(self) -> AtlasLanguageReport:
        return self.build_report(
            rating=AtlasRating(
                value="Strong Alignment",
                explanation=(
                    "The assessment reflects fit between profile context, evidence, "
                    "and current risks. It is not an investment instruction."
                ),
            ),
            view=AtlasView(
                value="Constructive",
                explanation=(
                    "Current evidence suggests the subject appears aligned with the "
                    "stated context, while several risks remain worth monitoring."
                ),
            ),
            fit=AtlasFit(
                value="Strong Fit",
                explanation=(
                    "The profile, time horizon, and portfolio purpose appear compatible "
                    "with the current evidence."
                ),
            ),
            confidence=AtlasConfidence(
                overall_confidence=76,
                confidence_level=ConfidenceLevel.HIGH,
                key_confidence_drivers=(
                    "The profile context is explicit.",
                    "The main risks and missing information are visible.",
                ),
                uncertainty_drivers=(
                    "Market conditions can change.",
                    "Some inputs are deterministic placeholders.",
                ),
                missing_information=(
                    "Tax context is not included.",
                    "Exact liquidity needs are not included.",
                ),
            ),
            thesis=AtlasThesis(
                current_thesis=(
                    "Atlas currently sees a constructive but evidence-dependent setup."
                ),
                supporting_evidence=(
                    "The rating is tied to stated profile context.",
                    "The view includes risk and uncertainty language.",
                ),
                counter_arguments=(
                    "The conclusion could weaken if new risks emerge.",
                    "Confidence should fall if important data is missing.",
                ),
                what_could_change_view=(
                    "A material change in investor objectives.",
                    "A material deterioration in market or portfolio risk signals.",
                ),
                what_atlas_is_monitoring=(
                    "Portfolio concentration.",
                    "Market health.",
                    "Investor profile drift.",
                ),
            ),
            rationale=AtlasRationale(
                bottom_line=(
                    "Current evidence suggests the subject appears aligned, with "
                    "risks worth monitoring and some missing context."
                ),
                key_reasons=(
                    "The assessment starts from investor context.",
                    "Confidence explains both evidence and uncertainty.",
                    "The thesis states what could change Atlas' view.",
                ),
                main_risk="The main risk is overconfidence when context is incomplete.",
                optional_follow_up_questions=(
                    "Has the investor's time horizon changed?",
                    "Would new liquidity needs change the conclusion?",
                ),
            ),
            engines_used=("Atlas Language Engine", "Principles Engine"),
        )

    def from_portfolio_review(self, review_report) -> AtlasLanguageReport:
        questions = _material_questions_from_sections(review_report.sections)
        return self.build_report(
            rating=AtlasRating(
                value=review_report.atlas_rating.value,
                explanation=(
                    "The portfolio rating reflects alignment between portfolio "
                    "structure, investor context, market conditions, and risk signals."
                ),
            ),
            view=AtlasView(
                value=_view_from_confidence(review_report.confidence),
                explanation=review_report.bottom_line,
            ),
            fit=AtlasFit(
                value=_fit_from_rating(review_report.atlas_rating.value),
                explanation="Fit is inferred from the portfolio review alignment rating.",
            ),
            confidence=AtlasConfidence(
                overall_confidence=review_report.confidence,
                confidence_level=_confidence_level(review_report.confidence),
                key_confidence_drivers=(
                    "Portfolio structure is available.",
                    "Investor profile context is included.",
                    "Suitability and risk drift are incorporated.",
                ),
                uncertainty_drivers=(
                    "Market and economic signals use deterministic placeholders.",
                    "Portfolio review confidence depends on input completeness.",
                ),
                missing_information=_missing_from_sections(review_report.sections),
            ),
            thesis=AtlasThesis(
                current_thesis=review_report.bottom_line,
                supporting_evidence=_section_summaries(
                    review_report.sections,
                    "Portfolio Strengths",
                ),
                counter_arguments=_section_summaries(review_report.sections, "Main Risks"),
                what_could_change_view=_section_summaries(
                    review_report.sections,
                    "What Could Change Atlas' View",
                ),
                what_atlas_is_monitoring=_section_summaries(
                    review_report.sections,
                    "What Atlas Is Monitoring",
                ),
            ),
            rationale=AtlasRationale(
                bottom_line=review_report.bottom_line,
                key_reasons=(
                    "The review starts from portfolio alignment rather than performance.",
                    "It includes suitability, risk drift, market context, and themes.",
                    "It names missing information before increasing confidence.",
                ),
                main_risk=_first_section_summary(review_report.sections, "Main Risks"),
                optional_follow_up_questions=questions,
            ),
            engines_used=("Portfolio Review Engine", "Atlas Language Engine"),
        )

    def guardrail_warnings(self, text: str) -> tuple[str, ...]:
        searchable = _normalize(_remove_quoted_text(text))
        warnings = []
        for phrase in FORBIDDEN_LANGUAGE:
            pattern = r"\b" + re.escape(phrase).replace(r"\ ", r"\s+") + r"\b"
            if re.search(pattern, searchable):
                warnings.append(f"Guardrail language detected: {phrase}.")
        return tuple(warnings)


def render_atlas_language_report(report: AtlasLanguageReport) -> str:
    lines = [
        "Atlas Language Report",
        "",
        f"Atlas Rating: {report.rating.value}",
        f"Rating Meaning: {report.rating.explanation}",
        "Rating Type: Contextual assessment, not an investment instruction.",
        "",
        f"Atlas View: {report.view.value}",
        report.view.explanation,
        "",
        f"Atlas Fit: {report.fit.value}",
        report.fit.explanation,
        "",
        "Atlas Confidence",
        f"- Overall: {report.confidence.overall_confidence}/100",
        f"- Level: {report.confidence.confidence_level.value}",
        "- Key confidence drivers:",
        *_render_list(report.confidence.key_confidence_drivers),
        "- Uncertainty drivers:",
        *_render_list(report.confidence.uncertainty_drivers),
        "- Missing information:",
        *_render_list(report.confidence.missing_information),
        "",
        "Bottom Line",
        report.rationale.bottom_line,
        "",
        "Key Reasons",
        *_render_list(report.rationale.key_reasons),
        "",
        "Main Risk",
        f"- {report.rationale.main_risk}",
        "",
        "What Could Change Atlas' View",
        *_render_list(report.thesis.what_could_change_view),
        "",
        "Reasoning",
        f"- Current thesis: {report.thesis.current_thesis}",
        "- Supporting evidence:",
        *_render_list(report.thesis.supporting_evidence),
        "- Counter arguments:",
        *_render_list(report.thesis.counter_arguments),
        "",
        "Full Reasoning",
        "- Assumptions: Atlas is using deterministic structured inputs.",
        "- Signals used:",
        *_render_list(report.thesis.supporting_evidence),
        "- Engines used:",
        *_render_list(report.engines_used),
        "- What Atlas is monitoring:",
        *_render_list(report.thesis.what_atlas_is_monitoring),
        "",
        "Optional Follow-up Questions",
        *_render_list(report.rationale.optional_follow_up_questions),
        "",
        "Show Full Reasoning: available through the Full Reasoning section above.",
    ]
    if report.guardrail_warnings:
        lines.extend(["", "Guardrail Warnings", *_render_list(report.guardrail_warnings)])
    return "\n".join(lines)


def _safe_rating(rating: AtlasRating) -> AtlasRating:
    return AtlasRating(
        value=rating.value,
        explanation=rating.explanation,
        is_recommendation=False,
    )


def _safe_rationale(rationale: AtlasRationale) -> AtlasRationale:
    return AtlasRationale(
        bottom_line=rationale.bottom_line,
        key_reasons=rationale.key_reasons,
        main_risk=rationale.main_risk,
        optional_follow_up_questions=_material_questions(rationale.optional_follow_up_questions),
    )


def _material_questions(questions: tuple[str, ...]) -> tuple[str, ...]:
    material_markers = ("change", "material", "horizon", "liquidity", "purpose", "risk")
    return tuple(
        question
        for question in questions
        if any(marker in question.lower() for marker in material_markers)
    )


def _render_source_text(
    rating: AtlasRating,
    view: AtlasView,
    fit: AtlasFit,
    confidence: AtlasConfidence,
    thesis: AtlasThesis,
    rationale: AtlasRationale,
) -> str:
    parts = (
        rating.value,
        rating.explanation,
        view.value,
        view.explanation,
        fit.value,
        fit.explanation,
        str(confidence.overall_confidence),
        *confidence.key_confidence_drivers,
        *confidence.uncertainty_drivers,
        *confidence.missing_information,
        thesis.current_thesis,
        *thesis.supporting_evidence,
        *thesis.counter_arguments,
        *thesis.what_could_change_view,
        *thesis.what_atlas_is_monitoring,
        rationale.bottom_line,
        *rationale.key_reasons,
        rationale.main_risk,
        *rationale.optional_follow_up_questions,
    )
    return "\n".join(parts)


def _confidence_level(score: int) -> ConfidenceLevel:
    if score >= 90:
        return ConfidenceLevel.VERY_HIGH
    if score >= 75:
        return ConfidenceLevel.HIGH
    if score >= 55:
        return ConfidenceLevel.MODERATE
    if score >= 35:
        return ConfidenceLevel.LOW
    return ConfidenceLevel.VERY_LOW


def _view_from_confidence(score: int) -> str:
    if score >= 75:
        return "Constructive"
    if score >= 55:
        return "Balanced"
    return "Unclear"


def _fit_from_rating(rating: str) -> str:
    mapping = {
        "Excellent Alignment": "Excellent Fit",
        "Strong Alignment": "Strong Fit",
        "Balanced": "Moderate Fit",
        "Limited Alignment": "Limited Fit",
        "Misaligned": "Poor Fit",
    }
    return mapping.get(rating, "Moderate Fit")


def _section_summaries(sections: tuple, title: str) -> tuple[str, ...]:
    for section in sections:
        if section.title == title:
            return tuple(item.summary for item in section.observations[:4])
    return ("Not enough information for a high-confidence assessment.",)


def _first_section_summary(sections: tuple, title: str) -> str:
    return _section_summaries(sections, title)[0]


def _missing_from_sections(sections: tuple) -> tuple[str, ...]:
    missing = _section_summaries(sections, "Missing Information")
    return missing or ("No major missing information was detected.",)


def _material_questions_from_sections(sections: tuple) -> tuple[str, ...]:
    return _material_questions(_section_summaries(sections, "Optional Follow-up Questions"))


def _remove_quoted_text(text: str) -> str:
    without_double_quotes = re.sub(r'"[^"]*"', " ", text)
    without_single_quotes = re.sub(r"'[^']*'", " ", without_double_quotes)
    return without_single_quotes


def _normalize(text: str) -> str:
    return text.lower().replace("-", " ")


def _render_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]


FORBIDDEN_LANGUAGE = (
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


ATLAS_LANGUAGE_PRINCIPLES = (
    "Atlas should reduce uncertainty, not create it.",
    "Atlas simplifies the decision, not the truth.",
    "Atlas filters information for the user, but never hides it.",
    "Every Atlas Rating must be explainable.",
    "Atlas only asks questions when the answer could materially change the conclusion.",
    "Atlas changes its mind when evidence changes.",
)
