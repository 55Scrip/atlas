"""Sprint 147: Portfolio boundary caller audit checkpoint guardrails.

Verifies:
- atlas.analysis.portfolio remains not importable (deleted Sprint 135)
- Portfolio and PortfolioPosition are importable from atlas.adapters.portfolio
- Portfolio and PortfolioPosition are NOT importable from atlas.analysis
- No production source file imports from atlas.analysis.portfolio
- legacy_portfolio_to_domain_portfolio is importable from atlas.adapters.portfolio
- Adapter does not import from deleted analysis modules
- Adapter does not import from atlas.analysis.portfolio
- Closed cleanup tracks remain closed
"""

import ast
import importlib
from pathlib import Path


# ── Deleted module remains gone ───────────────────────────────────────────────

def test_sprint147_analysis_portfolio_remains_deleted() -> None:
    """Sprint 147: atlas.analysis.portfolio must not be importable (deleted Sprint 135)."""
    try:
        importlib.import_module("atlas.analysis.portfolio")
        assert False, "atlas.analysis.portfolio must not be importable after Sprint 135"
    except ModuleNotFoundError:
        pass


# ── Adapter boundary importability ───────────────────────────────────────────

def test_sprint147_portfolio_importable_from_adapter() -> None:
    """Sprint 147: Portfolio must be importable from atlas.adapters.portfolio."""
    from atlas.adapters.portfolio import Portfolio  # noqa: F401
    assert Portfolio is not None


def test_sprint147_portfolio_position_importable_from_adapter() -> None:
    """Sprint 147: PortfolioPosition must be importable from atlas.adapters.portfolio."""
    from atlas.adapters.portfolio import PortfolioPosition  # noqa: F401
    assert PortfolioPosition is not None


def test_sprint147_legacy_adapter_importable() -> None:
    """Sprint 147: legacy_portfolio_to_domain_portfolio must be importable from atlas.adapters.portfolio."""
    from atlas.adapters.portfolio import legacy_portfolio_to_domain_portfolio  # noqa: F401
    assert legacy_portfolio_to_domain_portfolio is not None


def test_sprint147_portfolio_not_importable_from_atlas_analysis() -> None:
    """Sprint 147: Portfolio must NOT be importable from atlas.analysis after Sprint 135."""
    try:
        from atlas.analysis import Portfolio  # noqa: F401
        assert False, "Portfolio must not be importable from atlas.analysis after Sprint 135"
    except (ImportError, ModuleNotFoundError):
        pass


def test_sprint147_portfolio_position_not_importable_from_atlas_analysis() -> None:
    """Sprint 147: PortfolioPosition must NOT be importable from atlas.analysis after Sprint 135."""
    try:
        from atlas.analysis import PortfolioPosition  # noqa: F401
        assert False, "PortfolioPosition must not be importable from atlas.analysis after Sprint 135"
    except (ImportError, ModuleNotFoundError):
        pass


# ── Zero production imports from deleted module ───────────────────────────────

def test_sprint147_no_production_code_imports_analysis_portfolio() -> None:
    """Sprint 147: zero production source files may import from atlas.analysis.portfolio."""
    production_dirs = [Path("atlas")]
    for prod_dir in production_dirs:
        for py_file in prod_dir.rglob("*.py"):
            source = py_file.read_text(encoding="utf-8")
            if "atlas.analysis.portfolio" not in source:
                continue
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == "atlas.analysis.portfolio":
                    assert False, (
                        f"{py_file}: active import from atlas.analysis.portfolio found — "
                        "module was deleted Sprint 135"
                    )


# ── Adapter does not import stale symbols ─────────────────────────────────────

def test_sprint147_adapter_does_not_import_analysis_portfolio() -> None:
    """Sprint 147: atlas/adapters/portfolio.py must not import from atlas.analysis.portfolio."""
    source = Path("atlas/adapters/portfolio.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "atlas.analysis.portfolio":
            assert False, "atlas/adapters/portfolio.py must not import atlas.analysis.portfolio"


def test_sprint147_adapter_does_not_import_deleted_portfolio_symbols() -> None:
    """Sprint 147: adapter must not import deleted symbols (PortfolioAnalysis, CompanyPortfolioProfile, etc.)."""
    source = Path("atlas/adapters/portfolio.py").read_text(encoding="utf-8")
    deleted_symbols = [
        "PortfolioAnalysis",
        "PortfolioSignal",
        "PortfolioRecommendation",
        "CompanyPortfolioProfile",
        "portfolio_fit_input_from_profile",
        "PortfolioIntelligenceEngine",
    ]
    for sym in deleted_symbols:
        assert sym not in source, (
            f"atlas/adapters/portfolio.py must not reference deleted symbol {sym}"
        )


# ── Closed cleanup track guardrails remain intact ─────────────────────────────

def test_sprint147_analysis_cleanup_track_closed() -> None:
    """Sprint 147: atlas/analysis/ cleanup track closed Sprint 141 — deleted modules remain gone."""
    deleted = [
        "atlas.analysis.portfolio",
        "atlas.analysis.comparison",
        "atlas.analysis.memory",
        "atlas.analysis.watchlist",
        "atlas.analysis.growth",
        "atlas.analysis.macro",
        "atlas.analysis.moat",
        "atlas.analysis.quality",
        "atlas.analysis.sentiment",
        "atlas.analysis.technicals",
        "atlas.analysis.valuation",
        "atlas.analysis.scoring",
    ]
    for mod in deleted:
        try:
            importlib.import_module(mod)
            assert False, f"{mod} must not be importable (deleted in analysis cleanup track)"
        except ModuleNotFoundError:
            pass


def test_sprint147_decision_cleanup_track_closed() -> None:
    """Sprint 147: render_comparison_result deleted Sprint 143 must remain gone."""
    try:
        from atlas.decision.comparison import render_comparison_result  # noqa: F401
        assert False, "render_comparison_result must not exist after Sprint 143"
    except ImportError:
        pass


def test_sprint147_provider_cleanup_track_closed() -> None:
    """Sprint 147: stale Yahoo exports removed Sprint 146 must remain absent from atlas.providers."""
    import atlas.providers as pkg
    for sym in ("YahooCompany", "YahooFinancials", "YahooMarketData"):
        assert sym not in pkg.__all__, (
            f"{sym} must not be in atlas.providers.__all__ after Sprint 146"
        )


# ── Sprint 148 guardrail ─────────────────────────────────────────────────────

def test_sprint148_adapter_does_not_import_portfolio_fit_input() -> None:
    """Sprint 148: stale PortfolioFitInput import removed — must not appear in adapter source."""
    source = Path("atlas/adapters/portfolio.py").read_text(encoding="utf-8")
    assert "PortfolioFitInput" not in source, (
        "atlas/adapters/portfolio.py must not import PortfolioFitInput — "
        "it was unused and removed in Sprint 148"
    )
