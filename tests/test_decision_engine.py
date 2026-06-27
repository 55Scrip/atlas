from datetime import UTC, datetime

from atlas.analysis.memory import MemoryEngine, MemoryStore
from atlas.analysis.portfolio import Portfolio, PortfolioPosition
from atlas.analysis.watchlist import Watchlist, WatchlistItem
from atlas.decision import (
    AtlasDecisionEngine,
    DecisionAction,
    DecisionContext,
    render_decision_result,
)
from atlas.providers import MockCompanyAnalysisProvider


def _sample_portfolio() -> Portfolio:
    return Portfolio(
        positions=(
            PortfolioPosition(
                ticker="AAPL",
                company="Apple",
                sector="Consumer Electronics",
                country="United States",
                market_cap=3_000_000_000_000,
                weight=0.25,
                quality_score=86,
                risk_score=72,
            ),
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


def test_decision_engine_produces_buy_when_context_is_complete_and_capital_is_safe():
    provider = MockCompanyAnalysisProvider()
    context = DecisionContext(
        portfolio=_sample_portfolio(),
        watchlist=Watchlist(
            name="AI Watchlist",
            items=(WatchlistItem("NVDA"), WatchlistItem("AMD"), WatchlistItem("MSFT")),
        ),
        investment_horizon="long term",
        risk_profile="balanced",
        available_capital=10_000,
        cash_reserve_status="adequate",
    )

    result = AtlasDecisionEngine().decide("NVDA", provider, context)

    assert result.action == DecisionAction.BUY
    assert result.has_enough_information is True
    assert result.portfolio_analysis is not None
    assert result.comparison_result is not None
    assert result.watchlist_analysis is not None
    assert "Concentration risk is explicit" in result.reasoning
    assert "uncertain" in result.uncertainty.lower()


def test_decision_engine_blocks_buy_when_capital_may_be_needed_soon():
    provider = MockCompanyAnalysisProvider()
    context = DecisionContext(
        portfolio=_sample_portfolio(),
        investment_horizon="short term",
        risk_profile="balanced",
        available_capital=5_000,
        cash_reserve_status="adequate",
    )

    result = AtlasDecisionEngine().decide("NVDA", provider, context)

    assert result.action == DecisionAction.AVOID
    assert result.capital_allocation_quality == 20
    assert "Capital safety blocks a buy decision" in result.reasoning
    assert "short-term liquidity" in result.next_best_action


def test_decision_engine_learns_more_when_required_context_is_missing():
    provider = MockCompanyAnalysisProvider()
    context = DecisionContext(
        investment_horizon="long term",
        risk_profile="balanced",
        available_capital=None,
        cash_reserve_status="unknown",
    )

    result = AtlasDecisionEngine().decide("NVDA", provider, context)

    assert result.action == DecisionAction.LEARN_MORE
    assert result.has_enough_information is False
    assert "incomplete" in result.reasoning
    assert "portfolio concentration" in result.uncertainty


def test_decision_engine_uses_memory_engine_when_history_exists(tmp_path):
    provider = MockCompanyAnalysisProvider()
    store = MemoryStore(tmp_path / "memory.json")
    memory_engine = MemoryEngine()
    investment_engine = AtlasDecisionEngine().investment_engine
    report = investment_engine.analyze_ticker("NVDA", provider)
    memory_engine.save(
        store=store,
        ticker="NVDA",
        report=report,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
    )
    memory_engine.save(
        store=store,
        ticker="NVDA",
        report=report,
        timestamp=datetime(2026, 2, 1, tzinfo=UTC),
    )
    context = DecisionContext(
        portfolio=_sample_portfolio(),
        historical_memory=store,
        investment_horizon="long term",
        risk_profile="balanced",
        available_capital=10_000,
        cash_reserve_status="adequate",
    )

    result = AtlasDecisionEngine().decide("NVDA", provider, context)

    assert result.memory_comparison is not None
    assert "recommendation is unchanged" in result.reasoning


def test_decision_renderer_includes_required_sections():
    provider = MockCompanyAnalysisProvider()
    context = DecisionContext(
        investment_horizon="long term",
        risk_profile="balanced",
        available_capital=10_000,
        cash_reserve_status="adequate",
    )
    result = AtlasDecisionEngine().decide("NVDA", provider, context)

    rendered = render_decision_result(result)

    assert "Atlas Decision" in rendered
    assert "Decision Quality" in rendered
    assert "Portfolio Fit" in rendered
    assert "Capital Allocation Quality" in rendered
    assert "Next Best Action" in rendered
    assert "What Could Change My Mind" in rendered
    assert "Uncertainty" in rendered
