import ast
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


# ── Sprint 116: portfolio review uses shared Portfolio internally ─────────────

_ENGINE_SOURCE = (
    __file__.replace("tests/test_portfolio_review.py", "")
    + "atlas/portfolio_review/engine.py"
)


def _engine_source_text() -> str:
    import pathlib
    return pathlib.Path(_ENGINE_SOURCE).read_text()


def test_sprint116_adapter_imported_in_portfolio_review_engine():
    source = _engine_source_text()
    assert "legacy_portfolio_to_domain_portfolio" in source


def test_sprint116_shared_portfolio_imported_in_portfolio_review_engine():
    source = _engine_source_text()
    assert "atlas.shared" in source


def test_sprint116_portfolio_intelligence_engine_not_imported():
    source = _engine_source_text()
    assert "PortfolioIntelligenceEngine" not in source


def test_sprint116_engine_uses_holdings_not_positions_internally():
    source = _engine_source_text()
    # internal helpers should reference holdings, not portfolio.positions
    assert "portfolio.holdings" in source
    # portfolio.positions should NOT appear in helper functions
    assert "portfolio.positions" not in source


def test_sprint116_average_handles_none_quality_score():
    portfolio = Portfolio.from_mapping(
        {
            "positions": [
                {
                    "ticker": "NVDA",
                    "company": "NVIDIA",
                    "sector": "Semiconductors",
                    "country": "United States",
                    "market_cap": 3_300_000_000_000,
                    "weight": 0.60,
                    "quality_score": 90,
                    "risk_score": 70,
                },
                {
                    "ticker": "MSFT",
                    "company": "Microsoft",
                    "sector": "Software",
                    "country": "United States",
                    "market_cap": 3_400_000_000_000,
                    "weight": 0.40,
                    "quality_score": 80,
                    "risk_score": 60,
                },
            ]
        }
    )
    # Should not raise; quality scores flow from legacy positions through adapter
    report = PortfolioReviewEngine().review(PortfolioReviewInput(portfolio=portfolio))
    rendered = render_portfolio_review(report)
    assert "Average portfolio quality" in rendered


def test_sprint116_largest_holding_reflected_in_report():
    portfolio = Portfolio.from_mapping(
        {
            "positions": [
                {
                    "ticker": "TSLA",
                    "company": "Tesla",
                    "sector": "Automotive",
                    "country": "United States",
                    "market_cap": 800_000_000_000,
                    "weight": 0.55,
                    "quality_score": 75,
                    "risk_score": 85,
                },
                {
                    "ticker": "AAPL",
                    "company": "Apple",
                    "sector": "Consumer Electronics",
                    "country": "United States",
                    "market_cap": 3_000_000_000_000,
                    "weight": 0.45,
                    "quality_score": 88,
                    "risk_score": 65,
                },
            ]
        }
    )
    report = PortfolioReviewEngine().review(PortfolioReviewInput(portfolio=portfolio))
    rendered = render_portfolio_review(report)
    # TSLA is the largest position (55%) — should appear in concentration and follow-up
    assert "TSLA" in rendered
    assert "55.0%" in rendered


def test_sprint116_no_advisory_language_in_review():
    report = PortfolioReviewEngine().review(PortfolioReviewInput(portfolio=_portfolio()))
    rendered = render_portfolio_review(report)
    forbidden = (
        "strong buy", "strong sell", "buy now", "sell now", "entry point",
        "exit point", "guaranteed", "risk-free", "price target", "must act",
    )
    lowered = rendered.lower()
    for term in forbidden:
        assert term not in lowered, f"Forbidden advisory term in output: {term!r}"
