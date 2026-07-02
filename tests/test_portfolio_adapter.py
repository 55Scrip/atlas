"""Sprint 117: Tests for atlas/adapters/portfolio.py — centralized portfolio adapters.

Covers both legacy_portfolio_to_domain_portfolio (centralized Sprint 114) and
portfolio_fit_input_from_profile (centralized Sprint 117).
"""

from __future__ import annotations

from atlas.adapters.portfolio import (
    legacy_portfolio_to_domain_portfolio,
    portfolio_fit_input_from_profile,
)
from atlas.analysis.portfolio import CompanyPortfolioProfile, Portfolio as LegacyPortfolio
from atlas.capabilities.portfolio_intelligence import PortfolioFitInput
from atlas.shared import Holding, Portfolio as SharedPortfolio


def _legacy_portfolio() -> LegacyPortfolio:
    return LegacyPortfolio.from_mapping(
        {
            "positions": [
                {
                    "ticker": "NVDA",
                    "company": "NVIDIA",
                    "sector": "Semiconductors",
                    "country": "United States",
                    "market_cap": 3_300_000_000_000,
                    "weight": 0.60,
                    "quality_score": 92,
                    "risk_score": 77,
                },
                {
                    "ticker": "MSFT",
                    "company": "Microsoft",
                    "sector": "Software",
                    "country": "United States",
                    "market_cap": 3_400_000_000_000,
                    "weight": 0.40,
                    "quality_score": 90,
                    "risk_score": 78,
                },
            ]
        }
    )


def _profile() -> CompanyPortfolioProfile:
    return CompanyPortfolioProfile(
        ticker="TSM",
        company="TSMC",
        sector="Semiconductors",
        country="Taiwan",
        market_cap=600_000_000_000.0,
        quality_score=88,
        risk_score=55,
    )


# ── legacy_portfolio_to_domain_portfolio ──────────────────────────────────────

def test_adapter_returns_shared_portfolio():
    result = legacy_portfolio_to_domain_portfolio(_legacy_portfolio())
    assert isinstance(result, SharedPortfolio)


def test_adapter_holding_count_matches_positions():
    result = legacy_portfolio_to_domain_portfolio(_legacy_portfolio())
    assert len(result.holdings) == 2


def test_adapter_preserves_ticker():
    result = legacy_portfolio_to_domain_portfolio(_legacy_portfolio())
    tickers = {h.ticker for h in result.holdings}
    assert tickers == {"NVDA", "MSFT"}


def test_adapter_preserves_sector():
    result = legacy_portfolio_to_domain_portfolio(_legacy_portfolio())
    sectors = {h.sector for h in result.holdings}
    assert "Semiconductors" in sectors
    assert "Software" in sectors


def test_adapter_preserves_weight():
    result = legacy_portfolio_to_domain_portfolio(_legacy_portfolio())
    nvda = next(h for h in result.holdings if h.ticker == "NVDA")
    assert nvda.weight == 0.60


def test_adapter_preserves_quality_score():
    result = legacy_portfolio_to_domain_portfolio(_legacy_portfolio())
    nvda = next(h for h in result.holdings if h.ticker == "NVDA")
    assert nvda.quality_score == 92


def test_adapter_preserves_risk_score():
    result = legacy_portfolio_to_domain_portfolio(_legacy_portfolio())
    nvda = next(h for h in result.holdings if h.ticker == "NVDA")
    assert nvda.risk_score == 77


def test_adapter_preserves_market_cap():
    result = legacy_portfolio_to_domain_portfolio(_legacy_portfolio())
    nvda = next(h for h in result.holdings if h.ticker == "NVDA")
    assert nvda.market_cap == 3_300_000_000_000.0


def test_adapter_preserves_country():
    result = legacy_portfolio_to_domain_portfolio(_legacy_portfolio())
    for h in result.holdings:
        assert h.country == "United States"


def test_adapter_is_deterministic():
    portfolio = _legacy_portfolio()
    first = legacy_portfolio_to_domain_portfolio(portfolio)
    second = legacy_portfolio_to_domain_portfolio(portfolio)
    assert first == second


# ── portfolio_fit_input_from_profile ─────────────────────────────────────────

def test_fit_input_from_profile_returns_portfolio_fit_input():
    result = portfolio_fit_input_from_profile(_profile())
    assert isinstance(result, PortfolioFitInput)


def test_fit_input_from_profile_preserves_ticker():
    result = portfolio_fit_input_from_profile(_profile())
    assert result.ticker == "TSM"


def test_fit_input_from_profile_preserves_company():
    result = portfolio_fit_input_from_profile(_profile())
    assert result.company == "TSMC"


def test_fit_input_from_profile_preserves_sector():
    result = portfolio_fit_input_from_profile(_profile())
    assert result.sector == "Semiconductors"


def test_fit_input_from_profile_preserves_country():
    result = portfolio_fit_input_from_profile(_profile())
    assert result.country == "Taiwan"


def test_fit_input_from_profile_preserves_market_cap():
    result = portfolio_fit_input_from_profile(_profile())
    assert result.market_cap == 600_000_000_000.0


def test_fit_input_from_profile_preserves_quality_score():
    result = portfolio_fit_input_from_profile(_profile())
    assert result.quality_score == 88


def test_fit_input_from_profile_preserves_risk_score():
    result = portfolio_fit_input_from_profile(_profile())
    assert result.risk_score == 55


def test_fit_input_from_profile_is_deterministic():
    profile = _profile()
    first = portfolio_fit_input_from_profile(profile)
    second = portfolio_fit_input_from_profile(profile)
    assert first == second


# ── architecture boundary: adapter does not import providers/CLI/network ──────

def test_adapter_module_has_no_provider_imports():
    import pathlib
    source = pathlib.Path("atlas/adapters/portfolio.py").read_text()
    assert "from atlas.providers" not in source
    assert "import atlas.providers" not in source


def test_adapter_module_has_no_cli_imports():
    import pathlib
    source = pathlib.Path("atlas/adapters/portfolio.py").read_text()
    assert "from atlas.cli" not in source


def test_capability_engine_does_not_import_legacy_portfolio():
    import pathlib
    source = pathlib.Path("atlas/capabilities/portfolio_intelligence/engine.py").read_text()
    assert "atlas.analysis.portfolio" not in source


# ── guardrail: deleted modules remain deleted ─────────────────────────────────

def test_watchlist_analysis_module_deleted():
    import importlib
    import pytest
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("atlas.analysis.watchlist")


def test_comparison_module_deleted():
    import importlib
    import pytest
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("atlas.analysis.comparison")


def test_memory_module_deleted():
    import importlib
    import pytest
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("atlas.analysis.memory")


def test_scoring_module_deleted():
    import importlib
    import pytest
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("atlas.analysis.scoring")


# ── legacy portfolio.py remains active ────────────────────────────────────────

def test_legacy_portfolio_module_still_importable():
    from atlas.analysis.portfolio import Portfolio  # noqa: F401
    assert Portfolio is not None


def test_legacy_company_portfolio_profile_still_importable():
    from atlas.analysis.portfolio import CompanyPortfolioProfile  # noqa: F401
    assert CompanyPortfolioProfile is not None


# ── no new caller migrated: conversation and dashboard pass ───────────────────

def test_conversation_engine_still_uses_adapter():
    import pathlib
    source = pathlib.Path("atlas/conversation/engine.py").read_text()
    assert "portfolio_fit_input_from_profile" in source
    assert "legacy_portfolio_to_domain_portfolio" in source


def test_dashboard_engine_still_uses_adapter():
    import pathlib
    source = pathlib.Path("atlas/dashboard/engine.py").read_text()
    assert "portfolio_fit_input_from_profile" in source
    assert "legacy_portfolio_to_domain_portfolio" in source


def test_portfolio_review_engine_still_uses_adapter():
    import pathlib
    source = pathlib.Path("atlas/portfolio_review/engine.py").read_text()
    assert "legacy_portfolio_to_domain_portfolio" in source
    # portfolio_review does not build PortfolioFitInput (structural-only path)
    assert "portfolio_fit_input_from_profile" not in source
