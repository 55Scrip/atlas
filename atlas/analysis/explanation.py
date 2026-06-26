from dataclasses import dataclass

from atlas.analysis.engine import InvestmentReport, ScoreCategory


@dataclass(frozen=True)
class InvestmentExplanation:
    bull_case: str
    bear_case: str
    key_strengths: tuple[str, ...]
    key_risks: tuple[str, ...]
    valuation_concern: str
    mind_changers: tuple[str, ...]
    confidence_explanation: str


class ExplanationEngine:
    def explain(self, report: InvestmentReport) -> InvestmentExplanation:
        strongest_categories = _rank_categories(report, reverse=True)
        weakest_categories = _rank_categories(report, reverse=False)
        key_strengths = tuple(
            _category_strength(label, category)
            for label, category in strongest_categories[:3]
        )
        key_risks = _key_risks(report, weakest_categories)

        return InvestmentExplanation(
            bull_case=_bull_case(report, strongest_categories),
            bear_case=_bear_case(report, weakest_categories),
            key_strengths=key_strengths,
            key_risks=key_risks,
            valuation_concern=_valuation_concern(report.valuation),
            mind_changers=_mind_changers(report),
            confidence_explanation=_confidence_explanation(report),
        )


def explain_investment_report(report: InvestmentReport) -> InvestmentExplanation:
    return ExplanationEngine().explain(report)


def render_investment_explanation(explanation: InvestmentExplanation) -> str:
    return "\n".join(
        [
            "Explanation",
            "",
            "Bull Case",
            explanation.bull_case,
            "",
            "Bear Case",
            explanation.bear_case,
            "",
            "Key Strengths",
            *_format_bullets(explanation.key_strengths),
            "",
            "Key Risks",
            *_format_bullets(explanation.key_risks),
            "",
            "Valuation Concern",
            explanation.valuation_concern,
            "",
            "What Could Change Atlas' Mind",
            *_format_bullets(explanation.mind_changers),
            "",
            "Confidence Explanation",
            explanation.confidence_explanation,
        ]
    )


def _rank_categories(
    report: InvestmentReport,
    reverse: bool,
) -> tuple[tuple[str, ScoreCategory], ...]:
    categories = (
        ("Quality", report.quality),
        ("Growth", report.growth),
        ("Valuation", report.valuation),
        ("Financial Strength", report.financial_strength),
        ("Risk", report.risk),
    )
    return tuple(sorted(categories, key=lambda item: item[1].score, reverse=reverse))


def _bull_case(
    report: InvestmentReport,
    strongest_categories: tuple[tuple[str, ScoreCategory], ...],
) -> str:
    primary_label, primary_category = strongest_categories[0]
    secondary_label, secondary_category = strongest_categories[1]
    return (
        f"The bull case for {report.company} is that Atlas rates it {report.atlas_score}/100 "
        f"with a {report.overall_recommendation} recommendation. The strongest support comes "
        f"from {primary_label.lower()} ({primary_category.score}/100) and "
        f"{secondary_label.lower()} ({secondary_category.score}/100). "
        f"{primary_category.reasoning}"
    )


def _bear_case(
    report: InvestmentReport,
    weakest_categories: tuple[tuple[str, ScoreCategory], ...],
) -> str:
    primary_label, primary_category = weakest_categories[0]
    secondary_label, secondary_category = weakest_categories[1]
    return (
        f"The bear case is that {primary_label.lower()} ({primary_category.score}/100) "
        f"and {secondary_label.lower()} ({secondary_category.score}/100) are the weakest "
        f"parts of the report. {primary_category.reasoning}"
    )


def _category_strength(label: str, category: ScoreCategory) -> str:
    return f"{label}: {category.score}/100. {category.reasoning}"


def _category_risk(label: str, category: ScoreCategory) -> str:
    return f"{label}: {category.score}/100. {category.reasoning}"


def _key_risks(
    report: InvestmentReport,
    weakest_categories: tuple[tuple[str, ScoreCategory], ...],
) -> tuple[str, ...]:
    risk_candidates = [
        ("Valuation", report.valuation),
        ("Risk", report.risk),
    ]
    for label, category in weakest_categories:
        if label in {"Valuation", "Risk"}:
            continue
        if category.score < 80:
            risk_candidates.append((label, category))
    if len(risk_candidates) < 3:
        risk_candidates.append(
            (
                "Evidence Quality",
                ScoreCategory(
                    score=report.confidence,
                    reasoning=(
                        "Atlas should keep validating the inputs behind this recommendation "
                        "because confidence is not certainty."
                    ),
                    confidence=report.confidence,
                ),
            )
        )
    return tuple(_category_risk(label, category) for label, category in risk_candidates[:3])


def _valuation_concern(valuation: ScoreCategory) -> str:
    if valuation.score >= 80:
        return (
            f"Valuation is not the main constraint at {valuation.score}/100, but Atlas should "
            "still test whether expectations are too optimistic."
        )
    if valuation.score >= 60:
        return (
            f"Valuation is a moderate concern at {valuation.score}/100. "
            f"{valuation.reasoning}"
        )
    return (
        f"Valuation is a major concern at {valuation.score}/100. Atlas should require "
        "a larger margin of safety before becoming more constructive."
    )


def _mind_changers(report: InvestmentReport) -> tuple[str, ...]:
    weakest_label, weakest_category = _rank_categories(report, reverse=False)[0]
    return (
        (
            f"Atlas would become more constructive if {weakest_label.lower()} improved "
            f"materially from {weakest_category.score}/100."
        ),
        (
            "Atlas would become less constructive if quality, growth, or financial "
            "strength deteriorated enough to pull the Atlas Score below the current band."
        ),
        (
            "Atlas would revisit the recommendation if new evidence changed the confidence "
            "behind the weakest category."
        ),
    )


def _confidence_explanation(report: InvestmentReport) -> str:
    category_confidences = (
        report.quality.confidence,
        report.growth.confidence,
        report.valuation.confidence,
        report.financial_strength.confidence,
        report.risk.confidence,
    )
    lowest_confidence = min(category_confidences)
    if report.confidence >= 80:
        confidence_level = "high"
    elif report.confidence >= 60:
        confidence_level = "moderate"
    else:
        confidence_level = "low"
    return (
        f"Atlas confidence is {confidence_level} at {report.confidence}/100. "
        f"The lowest category confidence is {lowest_confidence}/100, so the explanation "
        "should be treated as evidence-based but still dependent on improving the least "
        "certain inputs."
    )


def _format_bullets(items: tuple[str, ...]) -> list[str]:
    return [f"- {item}" for item in items]
