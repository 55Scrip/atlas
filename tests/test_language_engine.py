from typer.testing import CliRunner

from atlas.analysis.portfolio import Portfolio
from atlas.cli.main import app
from atlas.language import (
    AtlasConfidence,
    AtlasFit,
    AtlasLanguageEngine,
    AtlasRating,
    AtlasRationale,
    AtlasThesis,
    AtlasView,
    ConfidenceLevel,
    ReasoningDepth,
    render_atlas_language_report,
)
from atlas.portfolio_review import PortfolioReviewEngine, PortfolioReviewInput
from atlas.profile import InvestorProfileEngine


def test_language_engine_flags_forbidden_instruction_language():
    warnings = AtlasLanguageEngine().guardrail_warnings(
        "Buy this. It is guaranteed and risk-free."
    )

    assert any("buy" in warning.lower() for warning in warnings)
    assert any("guaranteed" in warning.lower() for warning in warnings)
    assert any("risk free" in warning.lower() for warning in warnings)


def test_language_report_ratings_are_not_recommendations():
    report = AtlasLanguageEngine().example_report()
    rendered = render_atlas_language_report(report)

    assert report.rating.is_recommendation is False
    assert "Rating Type: Contextual assessment, not an investment instruction." in rendered


def test_confidence_includes_uncertainty_and_missing_information():
    report = AtlasLanguageEngine().example_report()

    assert report.confidence.uncertainty_drivers
    assert report.confidence.missing_information
    assert report.confidence.confidence_level == ConfidenceLevel.HIGH


def test_follow_up_questions_are_only_kept_when_material():
    report = AtlasLanguageEngine().build_report(
        rating=AtlasRating("Balanced", "A contextual assessment."),
        view=AtlasView("Balanced", "Current evidence is mixed."),
        fit=AtlasFit("Moderate Fit", "The fit depends on context."),
        confidence=AtlasConfidence(
            overall_confidence=62,
            confidence_level=ConfidenceLevel.MODERATE,
            key_confidence_drivers=("The core context is present.",),
            uncertainty_drivers=("Some assumptions remain.",),
            missing_information=("Exact liquidity needs are missing.",),
        ),
        thesis=AtlasThesis(
            current_thesis="Current evidence suggests a balanced view.",
            supporting_evidence=("The profile is available.",),
            counter_arguments=("Important facts may be missing.",),
            what_could_change_view=("A material risk profile change.",),
            what_atlas_is_monitoring=("Profile drift.",),
        ),
        rationale=AtlasRationale(
            bottom_line="Current evidence suggests a balanced view.",
            key_reasons=("The available context is relevant.",),
            main_risk="The main risk is incomplete context.",
            optional_follow_up_questions=(
                "What is your favorite color?",
                "Has your investment horizon changed?",
            ),
        ),
    )

    assert report.rationale.optional_follow_up_questions == (
        "Has your investment horizon changed?",
    )


def test_progressive_transparency_has_all_reasoning_depths():
    report = AtlasLanguageEngine().example_report()
    rendered = render_atlas_language_report(report)

    assert report.reasoning_depths == (
        ReasoningDepth.BOTTOM_LINE,
        ReasoningDepth.REASONING,
        ReasoningDepth.FULL_REASONING,
    )
    assert "Bottom Line" in rendered
    assert "Reasoning" in rendered
    assert "Full Reasoning" in rendered


def test_portfolio_review_can_use_language_layer():
    review = PortfolioReviewEngine().review(
        PortfolioReviewInput(
            portfolio=_portfolio(),
            investor_profile=InvestorProfileEngine().create_default_profile(),
        )
    )

    assert review.language_report is not None
    assert review.language_report.rating.value == review.atlas_rating.value
    assert "Portfolio Review Engine" in review.language_report.engines_used


def test_language_cli_explain_outputs_example_report():
    result = CliRunner().invoke(app, ["language", "explain"])

    assert result.exit_code == 0
    assert "Atlas Language Report" in result.output
    assert "Atlas Rating" in result.output
    assert "Show Full Reasoning" in result.output


def _portfolio() -> Portfolio:
    return Portfolio.from_mapping(
        {
            "positions": [
                {
                    "ticker": "NVDA",
                    "company": "NVIDIA",
                    "sector": "Semiconductors",
                    "country": "United States",
                    "market_cap": 3_300_000_000_000,
                    "weight": 0.42,
                    "quality_score": 91,
                    "risk_score": 38,
                },
                {
                    "ticker": "MSFT",
                    "company": "Microsoft",
                    "sector": "Software",
                    "country": "United States",
                    "market_cap": 3_400_000_000_000,
                    "weight": 0.35,
                    "quality_score": 90,
                    "risk_score": 30,
                },
                {
                    "ticker": "AAPL",
                    "company": "Apple",
                    "sector": "Consumer Technology",
                    "country": "United States",
                    "market_cap": 3_000_000_000_000,
                    "weight": 0.23,
                    "quality_score": 86,
                    "risk_score": 32,
                },
            ]
        }
    )
