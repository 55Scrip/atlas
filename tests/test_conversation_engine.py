import json

from typer.testing import CliRunner

from atlas.analysis.portfolio import Portfolio, PortfolioPosition
from atlas.analysis.watchlist import Watchlist, WatchlistItem
from atlas.cli.main import app
from atlas.conversation import (
    ConversationEngine,
    ConversationInput,
    ConversationIntent,
    IntentClassifier,
    render_conversation_response,
)
from atlas.providers import MockCompanyAnalysisProvider


def test_intent_classifier_recognizes_initial_questions():
    classifier = IntentClassifier()

    assert classifier.classify("Analyze Nvidia") == ConversationIntent.COMPANY_ANALYSIS
    assert classifier.classify("Review my portfolio") == ConversationIntent.PORTFOLIO_REVIEW
    assert classifier.classify("What is the next bottleneck in AI?") == (
        ConversationIntent.THEME_RESEARCH
    )
    assert classifier.classify("How healthy is the market?") == (
        ConversationIntent.MARKET_HEALTH
    )
    assert classifier.classify("How risky is this company?") == (
        ConversationIntent.RISK_ASSESSMENT
    )
    assert classifier.classify("What themes are attractive?") == (
        ConversationIntent.THEME_RESEARCH
    )
    assert classifier.classify("What should I monitor?") == (
        ConversationIntent.GENERAL_INVESTMENT_GUIDANCE
    )


def test_conversation_engine_answers_company_analysis_with_existing_engines():
    response = ConversationEngine().answer(
        ConversationInput(
            question="Analyze Nvidia",
            provider=MockCompanyAnalysisProvider(),
        )
    )

    assert response.intent == ConversationIntent.COMPANY_ANALYSIS
    assert "NVDA" in response.short_answer
    assert "Intelligence Engine" in response.engines_used
    assert "Investment Engine" in response.engines_used
    assert response.confidence > 0


def test_conversation_engine_answers_theme_bottleneck_question():
    response = ConversationEngine().answer(
        ConversationInput(question="What is the next bottleneck in AI?")
    )

    assert response.intent == ConversationIntent.THEME_RESEARCH
    assert "AI infrastructure" in response.short_answer
    assert "Electricity supply" in response.short_answer
    assert "Theme Engine" in response.engines_used


def test_conversation_engine_answers_market_health_question():
    response = ConversationEngine().answer(
        ConversationInput(question="How healthy is the market?")
    )

    assert response.intent == ConversationIntent.MARKET_HEALTH
    assert "Fragile" in response.short_answer
    assert "Market Health Engine" in response.engines_used


def test_conversation_engine_uses_portfolio_context_when_available():
    portfolio = Portfolio(
        positions=(
            PortfolioPosition(
                ticker="MSFT",
                company="Microsoft",
                sector="Software",
                country="United States",
                market_cap=3_400_000_000_000,
                weight=0.20,
                quality_score=90,
                risk_score=78,
            ),
        )
    )

    response = ConversationEngine().answer(
        ConversationInput(
            question="Review my portfolio",
            provider=MockCompanyAnalysisProvider(),
            portfolio=portfolio,
            ticker="NVDA",
        )
    )

    assert response.intent == ConversationIntent.PORTFOLIO_REVIEW
    assert "portfolio fit" in response.short_answer.lower()
    assert "Portfolio Engine" in response.engines_used


def test_conversation_engine_reports_missing_portfolio_context():
    response = ConversationEngine().answer(ConversationInput(question="Review my portfolio"))

    assert response.intent == ConversationIntent.PORTFOLIO_REVIEW
    assert "needs portfolio context" in response.short_answer
    assert response.confidence == 52


def test_conversation_engine_answers_watchlist_review():
    watchlist = Watchlist(
        name="AI Watchlist",
        items=(
            WatchlistItem("NVDA"),
            WatchlistItem("AMD"),
            WatchlistItem("MSFT"),
        ),
    )

    response = ConversationEngine().answer(
        ConversationInput(
            question="Review my watchlist",
            provider=MockCompanyAnalysisProvider(),
            watchlist=watchlist,
        )
    )

    assert response.intent == ConversationIntent.WATCHLIST_REVIEW
    assert "AI Watchlist" in response.short_answer
    assert "highlights" in response.short_answer
    assert "Watchlist Intelligence Engine" in response.engines_used


def test_conversation_renderer_includes_required_sections():
    response = ConversationEngine().answer(
        ConversationInput(question="How risky is this company?", ticker="NVDA")
    )

    rendered = render_conversation_response(response)

    assert "Short Answer" in rendered
    assert "Supporting Reasoning" in rendered
    assert "Engines Used" in rendered
    assert "Confidence" in rendered
    assert "Suggested Follow-up Questions" in rendered
    assert "not personalized financial advice" in rendered


def test_conversation_cli_outputs_response():
    runner = CliRunner()

    result = runner.invoke(app, ["ask", "How healthy is the market?"])

    assert result.exit_code == 0
    assert "Atlas Conversation Response" in result.output
    assert "Intent: Market Health" in result.output


def test_conversation_cli_accepts_portfolio_context(tmp_path):
    portfolio_path = tmp_path / "portfolio.json"
    portfolio_path.write_text(
        json.dumps(
            {
                "positions": [
                    {
                        "ticker": "MSFT",
                        "company": "Microsoft",
                        "sector": "Software",
                        "country": "United States",
                        "market_cap": 3400000000000,
                        "weight": 0.2,
                        "quality_score": 90,
                        "risk_score": 78,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["ask", "Review my portfolio", "--portfolio", str(portfolio_path), "--ticker", "NVDA"],
    )

    assert result.exit_code == 0
    assert "Intent: Portfolio Review" in result.output
    assert "Portfolio Engine" in result.output
