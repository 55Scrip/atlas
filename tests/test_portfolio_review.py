import json

from typer.testing import CliRunner

from atlas.analysis.portfolio import Portfolio
from atlas.cli.main import app
from atlas.portfolio_review import (
    PortfolioAlignmentRating,
    PortfolioReviewEngine,
    PortfolioReviewInput,
    render_portfolio_review,
)
from atlas.profile import InvestorProfileEngine


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
                    "quality_score": 92,
                    "risk_score": 77,
                },
                {
                    "ticker": "MSFT",
                    "company": "Microsoft",
                    "sector": "Software",
                    "country": "United States",
                    "market_cap": 3_400_000_000_000,
                    "weight": 0.28,
                    "quality_score": 90,
                    "risk_score": 78,
                },
                {
                    "ticker": "AAPL",
                    "company": "Apple",
                    "sector": "Consumer Electronics",
                    "country": "United States",
                    "market_cap": 3_000_000_000_000,
                    "weight": 0.18,
                    "quality_score": 86,
                    "risk_score": 72,
                },
            ]
        }
    )


def test_portfolio_review_builds_required_sections():
    profile = InvestorProfileEngine().create_default_profile(name="Review User")

    report = PortfolioReviewEngine().review(
        PortfolioReviewInput(portfolio=_portfolio(), investor_profile=profile)
    )

    section_titles = {section.title for section in report.sections}

    assert report.title == "Atlas Portfolio Review"
    assert report.bottom_line
    assert report.atlas_rating in set(PortfolioAlignmentRating)
    assert "Bottom Line" in section_titles
    assert "Atlas Rating" in section_titles
    assert "Portfolio Strengths" in section_titles
    assert "Main Risks" in section_titles
    assert "Investor Alignment" in section_titles
    assert "Theme Exposure" in section_titles
    assert "Market Context" in section_titles
    assert "What Atlas Is Monitoring" in section_titles
    assert "What Could Change Atlas' View" in section_titles
    assert "Missing Information" in section_titles
    assert "Optional Follow-up Questions" in section_titles


def test_portfolio_review_renderer_is_clear_and_guardrail_safe():
    report = PortfolioReviewEngine().review(PortfolioReviewInput(portfolio=_portfolio()))

    rendered = render_portfolio_review(report)

    assert "Atlas Portfolio Review" in rendered
    assert "Bottom Line" in rendered
    assert "Atlas Rating:" in rendered
    assert "current evidence suggests" in rendered.lower()
    assert "Strong Buy" not in rendered
    assert "Strong Sell" not in rendered
    assert "Buy" not in rendered
    assert "Sell" not in rendered
    assert "Guaranteed" not in rendered
    assert "Risk-free" not in rendered


def test_portfolio_review_mentions_concentration_and_alignment():
    report = PortfolioReviewEngine().review(PortfolioReviewInput(portfolio=_portfolio()))
    rendered = render_portfolio_review(report)

    assert "NVDA is 42.0% of the portfolio" in rendered
    assert "Investor Alignment" in rendered
    assert "Suitability is" in rendered
    assert "risk drift is" in rendered


def test_portfolio_review_cli_outputs_clean_text(tmp_path):
    portfolio_path = tmp_path / "portfolio.json"
    portfolio_path.write_text(
        json.dumps(
            {
                "positions": [
                    {
                        "ticker": "NVDA",
                        "company": "NVIDIA",
                        "sector": "Semiconductors",
                        "country": "United States",
                        "market_cap": 3_300_000_000_000,
                        "weight": 0.42,
                        "quality_score": 92,
                        "risk_score": 77,
                    },
                    {
                        "ticker": "MSFT",
                        "company": "Microsoft",
                        "sector": "Software",
                        "country": "United States",
                        "market_cap": 3_400_000_000_000,
                        "weight": 0.28,
                        "quality_score": 90,
                        "risk_score": 78,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(app, ["portfolio", "review", str(portfolio_path)])

    # Sprint 90: atlas portfolio review command body retired — no longer a valid command
    assert result.exit_code != 0
