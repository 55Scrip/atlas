import ast
from datetime import UTC, datetime

from atlas.decision.memory import MemoryEntry, MemoryStore
from atlas.analysis.portfolio import Portfolio, PortfolioPosition
from atlas.capabilities.watchlist_intelligence import WatchlistInput, WatchlistInputItem
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
        watchlist=WatchlistInput(
            name="AI Watchlist",
            items=(WatchlistInputItem("NVDA"), WatchlistInputItem("AMD"), WatchlistInputItem("MSFT")),
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
    assert result.watchlist_intelligence is not None
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
    investment_engine = AtlasDecisionEngine().investment_engine
    report = investment_engine.analyze_ticker("NVDA", provider)
    store.save(MemoryEntry.from_report(ticker="NVDA", report=report, timestamp=datetime(2026, 1, 1, tzinfo=UTC)))
    store.save(MemoryEntry.from_report(ticker="NVDA", report=report, timestamp=datetime(2026, 2, 1, tzinfo=UTC)))
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


# --- Sprint 123: decision portfolio dependency audit ---

_DECISION_DIR = __import__("pathlib").Path(__file__).parent.parent / "atlas" / "decision"


def _source(filename: str) -> str:
    return (_DECISION_DIR / filename).read_text()


def _tree(filename: str) -> ast.Module:
    return ast.parse(_source(filename))


def _top_level_legacy_imports(filename: str) -> list[str]:
    """Return module names imported at top level (outside TYPE_CHECKING blocks)."""
    tree = _tree(filename)
    found = []
    for node in tree.body:
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                continue
        if isinstance(node, ast.ImportFrom) and node.module == "atlas.analysis.portfolio":
            found.append(node.module)
    return found


def test_sprint123_decision_context_no_runtime_portfolio_import():
    """decision_context.py must not import atlas.analysis.portfolio at runtime."""
    assert _top_level_legacy_imports("decision_context.py") == []


def test_sprint123_decision_context_future_annotations():
    """decision_context.py must declare from __future__ import annotations."""
    assert "from __future__ import annotations" in _source("decision_context.py")


def test_sprint123_decision_context_type_checking_guard():
    """Portfolio must appear inside an if TYPE_CHECKING: block in decision_context.py."""
    for node in _tree("decision_context.py").body:
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                for child in ast.walk(node):
                    if isinstance(child, ast.ImportFrom):
                        if any(alias.name == "Portfolio" for alias in child.names):
                            return
    raise AssertionError("Portfolio not found inside TYPE_CHECKING block in decision_context.py")


def test_sprint123_decision_result_no_runtime_portfolio_analysis_import():
    """decision_result.py must not import atlas.analysis.portfolio at runtime."""
    assert _top_level_legacy_imports("decision_result.py") == []


def test_sprint123_decision_result_future_annotations():
    """decision_result.py must declare from __future__ import annotations."""
    assert "from __future__ import annotations" in _source("decision_result.py")


def test_sprint123_decision_result_type_checking_guard():
    """A TYPE_CHECKING guard must be present in decision_result.py (updated by Sprint 124 to PortfolioFitResult)."""
    source = _source("decision_result.py")
    assert "TYPE_CHECKING" in source
    # Sprint 124 updated the guarded import from PortfolioAnalysis to PortfolioFitResult
    assert "PortfolioFitResult" in source


def test_sprint123_decision_engine_still_has_runtime_portfolio_coupling():
    """Sprint 124 migrated decision_engine.py — PortfolioIntelligenceEngine is gone, capability is in use."""
    source = _source("decision_engine.py")
    # Sprint 124 replaced PortfolioIntelligenceEngine with PortfolioIntelligenceCapability
    assert "PortfolioIntelligenceCapability" in source
    assert "atlas.analysis.portfolio" not in source


def test_sprint123_decision_behavior_unchanged_no_portfolio():
    """Decision engine still works without portfolio (core path unchanged)."""
    from atlas.decision import AtlasDecisionEngine, DecisionContext
    from atlas.providers import MockCompanyAnalysisProvider

    result = AtlasDecisionEngine().decide(
        "NVDA",
        MockCompanyAnalysisProvider(),
        DecisionContext(
            investment_horizon="long term",
            risk_profile="balanced",
            available_capital=10_000.0,
            cash_reserve_status="adequate",
        ),
    )
    assert result.ticker == "NVDA"
    assert result.portfolio_analysis is None
    assert result.portfolio_fit == 50


def test_sprint123_legacy_portfolio_module_still_active():
    """atlas.analysis.portfolio must still be importable (not deleted)."""
    import atlas.analysis.portfolio as legacy
    assert hasattr(legacy, "Portfolio")
    assert hasattr(legacy, "PortfolioAnalysis")
    assert hasattr(legacy, "PortfolioIntelligenceEngine")


def test_sprint123_capability_engine_still_clean():
    """Portfolio Intelligence capability engine must not import from atlas.analysis.portfolio."""
    cap_path = (
        __import__("pathlib").Path(__file__).parent.parent
        / "atlas" / "capabilities" / "portfolio_intelligence" / "engine.py"
    )
    assert "atlas.analysis.portfolio" not in cap_path.read_text()


# ---------------------------------------------------------------------------
# Sprint 124: Migrate decision_engine.py from PortfolioIntelligenceEngine
#             to PortfolioIntelligenceCapability
# ---------------------------------------------------------------------------

import pathlib as _pathlib

_DECISION_DIR = _pathlib.Path(__file__).parent.parent / "atlas" / "decision"


def _decision_source(name: str) -> str:
    return (_DECISION_DIR / name).read_text()


def _decision_tree(name: str) -> ast.Module:
    return ast.parse(_decision_source(name))


def _top_level_legacy_imports_decision(name: str) -> list[str]:
    """Return atlas.analysis.portfolio imports NOT inside a TYPE_CHECKING block."""
    results = []
    for node in _decision_tree(name).body:
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                continue
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if "atlas.analysis.portfolio" in module:
                results.append(module)
    return results


def test_sprint124_decision_engine_no_runtime_legacy_portfolio_import():
    """decision_engine.py must not runtime-import from atlas.analysis.portfolio."""
    assert _top_level_legacy_imports_decision("decision_engine.py") == []


def test_sprint124_decision_engine_no_portfolio_intelligence_engine():
    """PortfolioIntelligenceEngine (legacy) must not appear in decision_engine.py."""
    assert "PortfolioIntelligenceEngine" not in _decision_source("decision_engine.py")


def test_sprint124_decision_engine_uses_capability():
    """decision_engine.py must import PortfolioIntelligenceCapability."""
    assert "PortfolioIntelligenceCapability" in _decision_source("decision_engine.py")


def test_sprint124_decision_engine_uses_adapters():
    """decision_engine.py must import the portfolio adapters for domain conversion."""
    source = _decision_source("decision_engine.py")
    assert "legacy_portfolio_to_domain_portfolio" in source
    assert "portfolio_fit_input_from_profile" in source


def test_sprint124_decision_engine_fit_score_guard():
    """decision_engine.py must use fit_score < 55 as the poor-fit boundary."""
    source = _decision_source("decision_engine.py")
    assert "fit_score < 55" in source
    # portfolio_score must not appear in live code (comments are acceptable documentation)
    import re
    non_comment_lines = [
        line for line in source.splitlines()
        if not line.strip().startswith("#")
    ]
    assert not any("portfolio_score" in line for line in non_comment_lines)


def test_sprint124_decision_engine_no_recommendation_enum():
    """decision_engine.py must not use recommendation.value guard in live code."""
    import re
    source = _decision_source("decision_engine.py")
    non_comment_lines = [
        line for line in source.splitlines()
        if not line.strip().startswith("#")
    ]
    assert not any('recommendation.value' in line for line in non_comment_lines)


def test_sprint124_decision_result_portfolio_analysis_is_portfolio_fit_result():
    """decision_result.py portfolio_analysis annotation must be PortfolioFitResult."""
    source = _decision_source("decision_result.py")
    assert "PortfolioFitResult" in source
    assert "PortfolioAnalysis" not in source


def test_sprint124_capability_injection_works():
    """AtlasDecisionEngine accepts a PortfolioIntelligenceCapability via constructor."""
    from atlas.capabilities.portfolio_intelligence import PortfolioIntelligenceCapability

    cap = PortfolioIntelligenceCapability()
    engine = AtlasDecisionEngine(portfolio_fit_capability=cap)
    assert engine.portfolio_fit_capability is cap


def test_sprint124_portfolio_fit_result_stored_on_decision_result():
    """When portfolio is supplied, result.portfolio_analysis is a PortfolioFitResult."""
    from atlas.capabilities.portfolio_intelligence import PortfolioFitResult

    result = AtlasDecisionEngine().decide(
        "NVDA",
        MockCompanyAnalysisProvider(),
        DecisionContext(
            investment_horizon="long term",
            risk_profile="balanced",
            available_capital=10_000.0,
            cash_reserve_status="adequate",
            portfolio=_sample_portfolio(),
        ),
    )
    assert result.portfolio_analysis is not None
    assert isinstance(result.portfolio_analysis, PortfolioFitResult)


def test_sprint124_overlap_field_used_not_overlap_with_existing_holdings():
    """PortfolioFitResult.overlap is used; overlap_with_existing_holdings must not appear."""
    source = _decision_source("decision_engine.py")
    assert "overlap_with_existing_holdings" not in source
    assert ".overlap" in source


def test_sprint124_fit_score_not_final_reasoning():
    """decision_engine.py must use .summary (not .final_reasoning) from PortfolioFitResult."""
    source = _decision_source("decision_engine.py")
    assert "final_reasoning" not in source
    assert ".summary" in source
