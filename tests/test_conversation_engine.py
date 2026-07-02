import ast
import json
import pathlib

from typer.testing import CliRunner

from atlas.adapters.portfolio import Portfolio, PortfolioPosition
from atlas.capabilities.watchlist_intelligence import WatchlistInput, WatchlistInputItem
from atlas.cli.main import app
from atlas.conversation import (
    ConversationEngine,
    ConversationInput,
    ConversationIntent,
    IntentClassifier,
    render_conversation_response,
)
from atlas.providers import MockCompanyAnalysisProvider

_CONV_SOURCE = (
    pathlib.Path(__file__).parent.parent / "atlas" / "conversation" / "engine.py"
).read_text()
_CONV_TREE = ast.parse(_CONV_SOURCE)


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
    watchlist = WatchlistInput(
        name="AI Watchlist",
        items=(
            WatchlistInputItem("NVDA"),
            WatchlistInputItem("AMD"),
            WatchlistInputItem("MSFT"),
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


# ---------------------------------------------------------------------------
# Sprint 126: Remove stale legacy portfolio engine attribute from conversation
# ---------------------------------------------------------------------------

def _conv_top_level_legacy_imports() -> list[str]:
    """Return atlas.analysis.portfolio runtime imports (not inside TYPE_CHECKING)."""
    results = []
    for node in _CONV_TREE.body:
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                continue
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if "atlas.analysis.portfolio" in module:
                results.append(module)
    return results


def test_sprint126_conversation_engine_no_runtime_legacy_portfolio_import():
    """conversation/engine.py must not runtime-import from atlas.analysis.portfolio."""
    assert _conv_top_level_legacy_imports() == []


def test_sprint126_conversation_engine_no_portfolio_intelligence_engine():
    """PortfolioIntelligenceEngine must not appear in conversation/engine.py."""
    assert "PortfolioIntelligenceEngine" not in _CONV_SOURCE


def test_sprint126_conversation_engine_no_self_portfolio_engine():
    """self.portfolio_engine must not appear in conversation/engine.py."""
    assert "self.portfolio_engine" not in _CONV_SOURCE


def test_sprint126_conversation_engine_no_portfolio_engine_constructor_param():
    """portfolio_engine constructor parameter must not appear in conversation/engine.py."""
    non_comment_lines = [
        line for line in _CONV_SOURCE.splitlines()
        if not line.strip().startswith("#")
    ]
    assert not any(
        "portfolio_engine:" in line and "portfolio_fit_capability" not in line
        for line in non_comment_lines
    )


def test_sprint126_conversation_engine_portfolio_review_uses_capability():
    """conversation/engine.py _answer_portfolio_review must use portfolio_fit_capability."""
    assert "self.portfolio_fit_capability" in _CONV_SOURCE
    assert "portfolio_fit_input_from_profile" in _CONV_SOURCE
    assert "legacy_portfolio_to_domain_portfolio" in _CONV_SOURCE


def test_sprint126_conversation_engine_type_checking_guard_for_portfolio():
    """Portfolio must appear inside a TYPE_CHECKING block in conversation/engine.py."""
    assert "TYPE_CHECKING" in _CONV_SOURCE
    assert "from __future__ import annotations" in _CONV_SOURCE
    for node in _CONV_TREE.body:
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                for child in ast.walk(node):
                    if isinstance(child, ast.ImportFrom):
                        if any(alias.name == "Portfolio" for alias in child.names):
                            return
    raise AssertionError("Portfolio not found inside TYPE_CHECKING block in conversation/engine.py")


def test_sprint126_conversation_engine_no_portfolio_engine_kwarg_to_intelligence():
    """conversation/engine.py must not pass portfolio_engine= to IntelligenceEngine."""
    assert "portfolio_engine=self.portfolio_engine" not in _CONV_SOURCE


def test_sprint126_capability_injection_works():
    """ConversationEngine accepts a PortfolioIntelligenceCapability via constructor."""
    from atlas.capabilities.portfolio_intelligence import PortfolioIntelligenceCapability

    cap = PortfolioIntelligenceCapability()
    engine = ConversationEngine(portfolio_fit_capability=cap)
    assert engine.portfolio_fit_capability is cap


def test_sprint126_portfolio_review_returns_fit_score_from_capability():
    """_answer_portfolio_review must return fit_score from PortfolioIntelligenceCapability."""
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
    engine = ConversationEngine()
    response = engine.answer(
        ConversationInput(
            question="Review my portfolio",
            portfolio=portfolio,
            ticker="NVDA",
            provider=MockCompanyAnalysisProvider(),
        )
    )
    assert response.intent == ConversationIntent.PORTFOLIO_REVIEW
    assert any("/100" in r for r in (response.short_answer,))
