from typer.testing import CliRunner

from atlas.cli.main import app
from atlas.comparison import (
    ComparisonRating,
    InvestmentComparisonEngine,
    InvestmentComparisonInput,
    render_investment_comparison,
)
from atlas.evidence import EvidenceClaim, EvidenceInput, EvidenceSource
from atlas.profile import InvestorProfileEngine, RiskTolerance
from atlas.providers import MockCompanyAnalysisProvider


def test_investment_comparison_includes_bottom_line_and_rating():
    report = InvestmentComparisonEngine().compare(_comparison_input(("NVDA", "MSFT")))
    rendered = render_investment_comparison(report)

    assert "Bottom Line" in rendered
    assert "Comparison Rating:" in rendered
    assert report.comparison_rating in set(ComparisonRating)


def test_each_candidate_includes_rating_view_fit_and_confidence():
    report = InvestmentComparisonEngine().compare(_comparison_input(("NVDA", "MSFT")))
    rendered = render_investment_comparison(report)

    assert "Atlas Rating:" in rendered
    assert "Atlas View:" in rendered
    assert "Atlas Fit:" in rendered
    assert "Confidence:" in rendered
    assert all(candidate.atlas_rating for candidate in report.candidates)
    assert all(candidate.atlas_view for candidate in report.candidates)
    assert all(candidate.atlas_fit for candidate in report.candidates)


def test_investment_comparison_avoids_buy_sell_hold_language():
    rendered = render_investment_comparison(
        InvestmentComparisonEngine().compare(_comparison_input(("NVDA", "MSFT")))
    )

    assert "Strong Buy" not in rendered
    assert "Strong Sell" not in rendered
    assert " Buy " not in rendered
    assert " Sell " not in rendered
    assert " Hold " not in rendered
    assert "Guaranteed" not in rendered
    assert "Risk-free" not in rendered
    assert "Sure thing" not in rendered


def test_investor_profile_affects_fit_language():
    engine = InvestorProfileEngine()
    profile = engine.update_profile(
        engine.create_default_profile(),
        risk_tolerance=RiskTolerance.CONSERVATIVE,
    )

    report = InvestmentComparisonEngine().compare(
        InvestmentComparisonInput(
            ideas=("NVDA", "MSFT"),
            provider=MockCompanyAnalysisProvider(),
            investor_profile=profile,
        )
    )
    rendered = render_investment_comparison(report)

    assert "conservative investor" in rendered.lower()
    assert "Investor Fit" in rendered


def test_evidence_quality_affects_confidence():
    strong = InvestmentComparisonEngine().compare(_comparison_input(("NVDA", "MSFT")))
    weak = InvestmentComparisonEngine().compare(
        InvestmentComparisonInput(
            ideas=("NVDA", "viral AI screenshot"),
            provider=MockCompanyAnalysisProvider(),
            evidence_inputs={
                "VIRAL AI SCREENSHOT": EvidenceInput(
                    claim=EvidenceClaim("A screenshot claims a dramatic shift."),
                    source=EvidenceSource.SCREENSHOT_WITHOUT_SOURCE,
                )
            },
        )
    )

    assert weak.confidence < strong.confidence
    weak_candidate = next(
        candidate for candidate in weak.candidates if "screenshot" in candidate.name
    )
    assert weak_candidate.confidence < 55


def test_missing_data_produces_uncertainty_language():
    report = InvestmentComparisonEngine().compare(
        _comparison_input(("NVDA", "unknown idea"))
    )
    rendered = render_investment_comparison(report)

    assert "not enough information for a high-confidence assessment" in rendered.lower()
    assert report.comparison_rating in {
        ComparisonRating.HIGHER_UNCERTAINTY,
        ComparisonRating.EVIDENCE_GAP,
        ComparisonRating.CLEARER_FIT,
    }


def test_social_media_idea_does_not_receive_high_confidence():
    report = InvestmentComparisonEngine().compare(
        InvestmentComparisonInput(
            ideas=("NVDA", "AI rumor"),
            provider=MockCompanyAnalysisProvider(),
            evidence_inputs={
                "AI RUMOR": EvidenceInput(
                    claim=EvidenceClaim("A social post claims a major development."),
                    source=EvidenceSource.SOCIAL_MEDIA_POST,
                )
            },
        )
    )
    rumor = next(candidate for candidate in report.candidates if candidate.name == "AI rumor")

    assert rumor.confidence < 60
    assert rumor.evidence_strength.value in {"Weak", "Very Weak", "Unverified", "Insufficient"}


def test_comparison_can_handle_two_and_three_candidates():
    two = InvestmentComparisonEngine().compare(_comparison_input(("NVDA", "MSFT")))
    three = InvestmentComparisonEngine().compare(_comparison_input(("NVDA", "MSFT", "AMD")))

    assert len(two.candidates) == 2
    assert len(three.candidates) == 3


def test_suggested_questions_are_only_material():
    report = InvestmentComparisonEngine().compare(_comparison_input(("NVDA", "unknown idea")))
    questions = _section_summaries(report, "Suggested Questions")

    assert questions
    assert all(
        any(marker in question.lower() for marker in ("role", "goal", "risk", "source"))
        for question in questions
    )


def test_progressive_transparency_sections_are_present():
    rendered = render_investment_comparison(
        InvestmentComparisonEngine().compare(_comparison_input(("NVDA", "MSFT")))
    )

    assert "Bottom Line" in rendered
    assert "Reasoning" in rendered
    assert "Full Reasoning" in rendered


def test_comparison_cli_works_for_demo_and_two_ideas():
    runner = CliRunner()
    demo = runner.invoke(app, ["compare"])
    two = runner.invoke(app, ["compare", "NVDA", "MSFT"])

    assert demo.exit_code == 0
    assert "Investment Comparison" in demo.output
    assert two.exit_code == 0
    assert "Investment Comparison" in two.output
    assert "NVDA" in two.output
    assert "MSFT" in two.output


def _comparison_input(ideas: tuple[str, ...]) -> InvestmentComparisonInput:
    return InvestmentComparisonInput(
        ideas=ideas,
        provider=MockCompanyAnalysisProvider(),
    )


def _section_summaries(report, title: str) -> tuple[str, ...]:
    for section in report.sections:
        if section.title == title:
            return tuple(item.summary for item in section.observations)
    return ()
