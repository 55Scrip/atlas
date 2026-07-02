"""Tests for PortfolioIntelligenceCapability engine (Sprint 113).

Covers:
- engine importability and architecture boundary
- all 7 dimensions: diversification, sector, country, market_cap, overlap, quality, risk
- aggregate fit score determinism
- schema gap dimensions return neutral/partial scores with notes
- no provider imports, no legacy portfolio imports
- existing legacy callers unchanged
"""

from __future__ import annotations

import pytest
from atlas.capabilities.portfolio_intelligence import (
    PortfolioFitDimension,
    PortfolioFitInput,
    PortfolioFitResult,
    PortfolioIntelligenceCapability,
)
from atlas.shared.entities import Holding, Portfolio


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_holding(
    ticker: str,
    sector: str = "Technology",
    country: str = "United States",
    weight: float = 0.10,
) -> Holding:
    return Holding(
        company_id=ticker.lower(),
        ticker=ticker,
        weight=weight,
        sector=sector,
        country=country,
    )


def _make_portfolio(*holdings: Holding) -> Portfolio:
    return Portfolio(id="test", name="Test Portfolio", holdings=tuple(holdings))


def _make_fit_input(
    ticker: str = "NVDA",
    sector: str = "Semiconductors",
    country: str = "United States",
    market_cap: float = 3_000_000_000_000.0,
    quality_score: int = 85,
    risk_score: int = 72,
) -> PortfolioFitInput:
    return PortfolioFitInput(
        ticker=ticker,
        company="Test Company",
        sector=sector,
        country=country,
        market_cap=market_cap,
        quality_score=quality_score,
        risk_score=risk_score,
    )


_ENGINE = PortfolioIntelligenceCapability()


# ---------------------------------------------------------------------------
# Importability and architecture boundary
# ---------------------------------------------------------------------------

def test_engine_is_importable() -> None:
    from atlas.capabilities.portfolio_intelligence import PortfolioIntelligenceCapability
    assert PortfolioIntelligenceCapability is not None


def test_engine_does_not_import_legacy_portfolio() -> None:
    import ast
    from pathlib import Path
    engine_file = Path(__file__).resolve().parent.parent / "atlas" / "capabilities" / "portfolio_intelligence" / "engine.py"
    tree = ast.parse(engine_file.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "atlas.analysis.portfolio" not in node.module, (
                "engine.py must not import from atlas.analysis.portfolio"
            )


def test_engine_does_not_import_providers() -> None:
    import ast
    from pathlib import Path
    engine_file = Path(__file__).resolve().parent.parent / "atlas" / "capabilities" / "portfolio_intelligence" / "engine.py"
    tree = ast.parse(engine_file.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("atlas.providers"), (
                "engine.py must not import from atlas.providers"
            )


def test_engine_does_not_import_cli() -> None:
    import ast
    from pathlib import Path
    engine_file = Path(__file__).resolve().parent.parent / "atlas" / "capabilities" / "portfolio_intelligence" / "engine.py"
    tree = ast.parse(engine_file.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("atlas.cli"), (
                "engine.py must not import from atlas.cli"
            )


# ---------------------------------------------------------------------------
# Engine returns correct types
# ---------------------------------------------------------------------------

def test_analyze_returns_portfolio_fit_result() -> None:
    portfolio = _make_portfolio(_make_holding("AAPL"))
    result = _ENGINE.analyze(portfolio, _make_fit_input())
    assert isinstance(result, PortfolioFitResult)


def test_result_fields_are_portfolio_fit_dimensions() -> None:
    portfolio = _make_portfolio(_make_holding("AAPL"))
    result = _ENGINE.analyze(portfolio, _make_fit_input())
    assert isinstance(result.diversification, PortfolioFitDimension)
    assert isinstance(result.sector_concentration, PortfolioFitDimension)
    assert isinstance(result.country_concentration, PortfolioFitDimension)
    assert isinstance(result.market_cap_concentration, PortfolioFitDimension)
    assert isinstance(result.overlap, PortfolioFitDimension)
    assert isinstance(result.quality_impact, PortfolioFitDimension)
    assert isinstance(result.risk_impact, PortfolioFitDimension)


def test_result_ticker_and_company_match_input() -> None:
    portfolio = _make_portfolio(_make_holding("AAPL"))
    fit_input = PortfolioFitInput(
        ticker="MSFT", company="Microsoft", sector="Software",
        country="United States", market_cap=3_000_000_000_000.0,
        quality_score=88, risk_score=65,
    )
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.ticker == "MSFT"
    assert result.company == "Microsoft"


def test_fit_score_is_clamped_between_0_and_100() -> None:
    portfolio = _make_portfolio(
        _make_holding("A", sector="Semiconductors", country="United States", weight=0.40),
        _make_holding("B", sector="Semiconductors", country="United States", weight=0.40),
    )
    fit_input = _make_fit_input(sector="Semiconductors", country="United States")
    result = _ENGINE.analyze(portfolio, fit_input)
    assert 0 <= result.fit_score <= 100


# ---------------------------------------------------------------------------
# Sector concentration
# ---------------------------------------------------------------------------

def test_sector_concentration_low_when_no_existing_sector_exposure() -> None:
    portfolio = _make_portfolio(_make_holding("AAPL", sector="Consumer Electronics"))
    fit_input = _make_fit_input(sector="Semiconductors")
    result = _ENGINE.analyze(portfolio, fit_input)
    # pro_forma = 0 + 0.05 = 0.05 < 0.25 preferred → score = 90
    assert result.sector_concentration.score == 90


def test_sector_concentration_penalized_when_concentrated() -> None:
    # 40% in Semiconductors already, adding 5% → 45% > preferred 25%
    portfolio = _make_portfolio(
        _make_holding("A", sector="Semiconductors", weight=0.20),
        _make_holding("B", sector="Semiconductors", weight=0.20),
    )
    fit_input = _make_fit_input(sector="Semiconductors")
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.sector_concentration.score < 90


def test_sector_concentration_at_hard_limit_returns_25() -> None:
    # 35% existing + 5% target = 40% == hard_limit → score = 25
    portfolio = _make_portfolio(
        _make_holding("A", sector="Semiconductors", weight=0.35),
    )
    fit_input = _make_fit_input(sector="Semiconductors", market_cap=100_000_000.0)
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.sector_concentration.score == 25


# ---------------------------------------------------------------------------
# Country concentration
# ---------------------------------------------------------------------------

def test_country_concentration_low_when_no_existing_country_exposure() -> None:
    portfolio = _make_portfolio(_make_holding("TSM", country="Taiwan"))
    fit_input = _make_fit_input(country="United States")
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.country_concentration.score == 90


def test_country_concentration_penalized_when_concentrated() -> None:
    # 60% US + 5% → 65% == hard_limit
    portfolio = _make_portfolio(
        _make_holding("A", country="United States", weight=0.30),
        _make_holding("B", country="United States", weight=0.30),
    )
    fit_input = _make_fit_input(country="United States")
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.country_concentration.score < 90


# ---------------------------------------------------------------------------
# Overlap with existing holdings
# ---------------------------------------------------------------------------

def test_overlap_score_is_low_for_direct_ticker_match() -> None:
    portfolio = _make_portfolio(_make_holding("NVDA", sector="Semiconductors"))
    fit_input = _make_fit_input(ticker="NVDA", sector="Semiconductors")
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.overlap.score == 20


def test_overlap_score_penalized_for_sector_overlap() -> None:
    portfolio = _make_portfolio(
        _make_holding("AMD", sector="Semiconductors"),
    )
    fit_input = _make_fit_input(ticker="NVDA", sector="Semiconductors")
    result = _ENGINE.analyze(portfolio, fit_input)
    # 1 sector overlap → 80 - 10 = 70
    assert result.overlap.score == 70


def test_overlap_score_high_when_no_overlap() -> None:
    portfolio = _make_portfolio(_make_holding("AAPL", sector="Consumer Electronics"))
    fit_input = _make_fit_input(ticker="NVDA", sector="Semiconductors")
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.overlap.score == 92


def test_overlap_score_decreases_with_more_sector_matches() -> None:
    portfolio = _make_portfolio(
        _make_holding("AMD", sector="Semiconductors"),
        _make_holding("INTC", sector="Semiconductors"),
        _make_holding("QCOM", sector="Semiconductors"),
    )
    fit_input = _make_fit_input(ticker="NVDA", sector="Semiconductors")
    result = _ENGINE.analyze(portfolio, fit_input)
    # 3 sector overlaps → 80 - 30 = 50, clamped
    assert result.overlap.score == 50


# ---------------------------------------------------------------------------
# Schema gap dimensions — neutral/partial scores
# ---------------------------------------------------------------------------

def test_market_cap_concentration_returns_neutral_with_note() -> None:
    portfolio = _make_portfolio(_make_holding("AAPL"))
    fit_input = _make_fit_input()
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.market_cap_concentration.score == 50
    assert "schema gap" in result.market_cap_concentration.note.lower()


def test_quality_impact_returns_partial_score_based_on_target() -> None:
    portfolio = _make_portfolio(_make_holding("AAPL"))
    # quality_score=90 → 50 + (90-50)*0.5 = 70
    fit_input = _make_fit_input(quality_score=90)
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.quality_impact.score == 70
    assert "schema gap" in result.quality_impact.note.lower()


def test_risk_impact_returns_partial_score_based_on_target() -> None:
    portfolio = _make_portfolio(_make_holding("AAPL"))
    # risk_score=80 → 50 + (80-50)*0.5 = 65
    fit_input = _make_fit_input(risk_score=80)
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.risk_impact.score == 65
    assert "schema gap" in result.risk_impact.note.lower()


def test_mega_cap_target_noted_in_market_cap_dimension() -> None:
    portfolio = _make_portfolio(_make_holding("AAPL"))
    fit_input = _make_fit_input(market_cap=3_000_000_000_000.0)
    result = _ENGINE.analyze(portfolio, fit_input)
    assert "mega-cap" in result.market_cap_concentration.note.lower()


def test_small_cap_target_noted_in_market_cap_dimension() -> None:
    portfolio = _make_portfolio(_make_holding("AAPL"))
    fit_input = _make_fit_input(market_cap=1_000_000_000.0)
    result = _ENGINE.analyze(portfolio, fit_input)
    assert "non-mega-cap" in result.market_cap_concentration.note.lower()


# ---------------------------------------------------------------------------
# Diversification
# ---------------------------------------------------------------------------

def test_diversification_penalized_by_sector_exposure() -> None:
    portfolio = _make_portfolio(
        _make_holding("A", sector="Semiconductors", country="Germany", weight=0.50),
    )
    # 50% semiconductor exposure → raw = 100 - round(0.50*55 + 0*25) = 100-28 = 72
    fit_input = _make_fit_input(sector="Semiconductors", country="France")
    result = _ENGINE.analyze(portfolio, fit_input)
    assert result.diversification.score < 100


def test_diversification_note_mentions_schema_gap() -> None:
    portfolio = _make_portfolio(_make_holding("AAPL"))
    result = _ENGINE.analyze(portfolio, _make_fit_input())
    assert "schema gap" in result.diversification.note.lower()


# ---------------------------------------------------------------------------
# Aggregate score determinism
# ---------------------------------------------------------------------------

def test_fit_score_is_deterministic() -> None:
    portfolio = _make_portfolio(
        _make_holding("AAPL", sector="Consumer Electronics", country="United States", weight=0.15),
        _make_holding("MSFT", sector="Software", country="United States", weight=0.15),
    )
    fit_input = _make_fit_input()
    r1 = _ENGINE.analyze(portfolio, fit_input)
    r2 = _ENGINE.analyze(portfolio, fit_input)
    assert r1 == r2


def test_empty_portfolio_produces_valid_result() -> None:
    portfolio = _make_portfolio()
    fit_input = _make_fit_input()
    result = _ENGINE.analyze(portfolio, fit_input)
    assert isinstance(result, PortfolioFitResult)
    assert 0 <= result.fit_score <= 100


def test_target_weight_normalization_handles_percent_format() -> None:
    portfolio = _make_portfolio(_make_holding("AAPL"))
    fit_input = _make_fit_input()
    r_decimal = _ENGINE.analyze(portfolio, fit_input, target_weight=0.05)
    r_percent = _ENGINE.analyze(portfolio, fit_input, target_weight=5.0)
    assert r_decimal == r_percent


# ---------------------------------------------------------------------------
# Existing legacy callers unchanged
# ---------------------------------------------------------------------------

def test_legacy_portfolio_intelligence_engine_still_importable() -> None:
    from atlas.analysis.portfolio import PortfolioIntelligenceEngine
    assert PortfolioIntelligenceEngine is not None


def test_legacy_portfolio_analysis_still_importable() -> None:
    from atlas.analysis.portfolio import PortfolioAnalysis
    assert PortfolioAnalysis is not None


def test_legacy_company_portfolio_profile_still_importable() -> None:
    from atlas.analysis.portfolio import CompanyPortfolioProfile
    assert CompanyPortfolioProfile is not None
