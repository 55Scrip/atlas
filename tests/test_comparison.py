from dataclasses import replace

from typer.testing import CliRunner

from atlas.analysis.comparison import ComparisonEngine, render_comparison_result
from atlas.analysis.company_analysis import MockCompanyAnalysisProvider
from atlas.analysis.growth import GrowthAnalysis
from atlas.analysis.quality import QualityAnalysis
from atlas.analysis.valuation import ValuationAnalysis
from atlas.cli.main import app


def test_comparison_engine_ranks_required_categories():
    provider = MockCompanyAnalysisProvider()
    nvda = provider.get_company_analysis("NVDA")
    amd = replace(
        provider.get_company_analysis("AMD"),
        quality=QualityAnalysis(
            score=82,
            summary="AMD quality is good but below the strongest peers.",
            strengths=("Focused execution",),
            weaknesses=("Lower margin profile",),
        ),
        growth=GrowthAnalysis(
            score=88,
            summary="AMD has a solid growth profile.",
            strengths=("AI accelerator opportunity",),
            weaknesses=("Execution risk",),
        ),
        valuation=ValuationAnalysis(
            score=84,
            summary="AMD has the most attractive valuation in this comparison.",
            strengths=("Better entry multiple",),
            weaknesses=("Lower certainty",),
        ),
    )
    msft = replace(
        provider.get_company_analysis("MSFT"),
        quality=QualityAnalysis(
            score=88,
            summary="Microsoft quality is excellent but slightly below NVIDIA here.",
            strengths=("Durable margins",),
            weaknesses=("Scale limits upside",),
        ),
        growth=GrowthAnalysis(
            score=89,
            summary="Microsoft growth is durable but less explosive.",
            strengths=("Cloud and AI demand",),
            weaknesses=("Scale moderates growth",),
        ),
    )

    result = ComparisonEngine().compare({"NVDA": nvda, "AMD": amd, "MSFT": msft})

    assert result.best_overall.winner.ticker == "NVDA"
    assert result.best_quality.winner.ticker == "NVDA"
    assert result.best_growth.winner.ticker == "NVDA"
    assert result.best_valuation.winner.ticker == "AMD"
    assert result.lowest_risk.winner.ticker == "AMD"
    assert result.final_conclusion.startswith("If Atlas could choose only one")


def test_render_comparison_result_includes_rankings_and_metrics():
    provider = MockCompanyAnalysisProvider()
    result = ComparisonEngine().compare(
        {
            "NVDA": provider.get_company_analysis("NVDA"),
            "MSFT": provider.get_company_analysis("MSFT"),
        }
    )

    rendered = render_comparison_result(result)

    assert "Company Comparison" in rendered
    assert "Best Overall" in rendered
    assert "Best Quality" in rendered
    assert "Best Valuation" in rendered
    assert "Best Growth" in rendered
    assert "Lowest Risk" in rendered
    assert "If Atlas could choose only one" in rendered


def test_comparison_engine_requires_at_least_two_companies():
    provider = MockCompanyAnalysisProvider()

    try:
        ComparisonEngine().compare({"NVDA": provider.get_company_analysis("NVDA")})
    except ValueError as exc:
        assert "at least two companies" in str(exc)
    else:
        raise AssertionError("ComparisonEngine should reject single-company comparisons")


def test_compare_cli_outputs_comparison_report():
    runner = CliRunner()

    result = runner.invoke(app, ["compare", "NVDA", "AMD", "MSFT"])

    assert result.exit_code == 0
    assert "Investment Comparison" in result.output
    assert "NVDA" in result.output
    assert "AMD" in result.output
    assert "MSFT" in result.output
    assert "Comparison Rating" in result.output
    assert "Full Reasoning" in result.output
