"""Tests for the atlas.capabilities.portfolio_intelligence stub (Sprint 112).

Confirms new Blueprint-aligned types are importable, instantiable, deterministic,
and free of provider/legacy dependencies. No production callers are migrated yet.
"""

from __future__ import annotations


def test_portfolio_intelligence_capability_is_importable() -> None:
    import atlas.capabilities.portfolio_intelligence as pkg
    assert pkg is not None


def test_portfolio_fit_input_is_importable() -> None:
    from atlas.capabilities.portfolio_intelligence import PortfolioFitInput
    assert PortfolioFitInput is not None


def test_portfolio_fit_result_is_importable() -> None:
    from atlas.capabilities.portfolio_intelligence import PortfolioFitResult
    assert PortfolioFitResult is not None


def test_portfolio_fit_dimension_is_importable() -> None:
    from atlas.capabilities.portfolio_intelligence import PortfolioFitDimension
    assert PortfolioFitDimension is not None


def test_portfolio_fit_input_instantiates_with_valid_data() -> None:
    from atlas.capabilities.portfolio_intelligence import PortfolioFitInput
    fit_input = PortfolioFitInput(
        ticker="NVDA",
        company="NVIDIA",
        sector="Semiconductors",
        country="United States",
        market_cap=3_000_000_000_000.0,
        quality_score=88,
        risk_score=72,
    )
    assert fit_input.ticker == "NVDA"
    assert fit_input.company == "NVIDIA"
    assert fit_input.sector == "Semiconductors"
    assert fit_input.country == "United States"
    assert fit_input.market_cap == 3_000_000_000_000.0
    assert fit_input.quality_score == 88
    assert fit_input.risk_score == 72


def test_portfolio_fit_result_instantiates_with_valid_data() -> None:
    from atlas.capabilities.portfolio_intelligence import PortfolioFitDimension, PortfolioFitResult

    dim = PortfolioFitDimension(score=80, note="Within expected range.")
    result = PortfolioFitResult(
        ticker="NVDA",
        company="NVIDIA",
        fit_score=75,
        diversification=dim,
        sector_concentration=dim,
        country_concentration=dim,
        market_cap_concentration=dim,
        overlap=dim,
        quality_impact=dim,
        risk_impact=dim,
        summary="Portfolio fit analysis for NVDA.",
    )
    assert result.ticker == "NVDA"
    assert result.fit_score == 75
    assert result.diversification.score == 80
    assert result.summary == "Portfolio fit analysis for NVDA."


def test_portfolio_fit_input_is_frozen() -> None:
    from atlas.capabilities.portfolio_intelligence import PortfolioFitInput
    import pytest
    fit_input = PortfolioFitInput(
        ticker="AAPL",
        company="Apple",
        sector="Consumer Electronics",
        country="United States",
        market_cap=3_000_000_000_000.0,
        quality_score=86,
        risk_score=70,
    )
    with pytest.raises((AttributeError, TypeError)):
        fit_input.ticker = "MSFT"  # type: ignore[misc]


def test_portfolio_fit_result_is_frozen() -> None:
    from atlas.capabilities.portfolio_intelligence import PortfolioFitDimension, PortfolioFitResult
    import pytest
    dim = PortfolioFitDimension(score=70, note="Moderate.")
    result = PortfolioFitResult(
        ticker="AAPL",
        company="Apple",
        fit_score=70,
        diversification=dim,
        sector_concentration=dim,
        country_concentration=dim,
        market_cap_concentration=dim,
        overlap=dim,
        quality_impact=dim,
        risk_impact=dim,
        summary="Test.",
    )
    with pytest.raises((AttributeError, TypeError)):
        result.fit_score = 99  # type: ignore[misc]


def test_portfolio_fit_input_is_deterministic() -> None:
    from atlas.capabilities.portfolio_intelligence import PortfolioFitInput
    a = PortfolioFitInput(
        ticker="MSFT", company="Microsoft", sector="Software",
        country="United States", market_cap=3_400_000_000_000.0,
        quality_score=90, risk_score=78,
    )
    b = PortfolioFitInput(
        ticker="MSFT", company="Microsoft", sector="Software",
        country="United States", market_cap=3_400_000_000_000.0,
        quality_score=90, risk_score=78,
    )
    assert a == b


def test_capability_does_not_import_legacy_portfolio() -> None:
    """Sprint 112: new capability must not import atlas.analysis.portfolio."""
    import ast
    from pathlib import Path
    cap_root = Path(__file__).resolve().parent.parent / "atlas" / "capabilities" / "portfolio_intelligence"
    for py_file in cap_root.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "atlas.analysis.portfolio" not in node.module, (
                    f"{py_file.name} must not import from atlas.analysis.portfolio — "
                    "capability layer must stay independent of legacy analysis"
                )


def test_capability_does_not_import_providers() -> None:
    """Sprint 112: new capability must not import provider modules."""
    import ast
    from pathlib import Path
    cap_root = Path(__file__).resolve().parent.parent / "atlas" / "capabilities" / "portfolio_intelligence"
    for py_file in cap_root.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("atlas.providers"), (
                    f"{py_file.name} must not import from atlas.providers — "
                    "capability types must be provider-free"
                )


def test_existing_portfolio_legacy_imports_unchanged() -> None:
    """Sprint 112/133: active boundary types remain importable; CompanyPortfolioProfile deleted Sprint 133."""
    from atlas.analysis.portfolio import Portfolio
    assert Portfolio is not None
