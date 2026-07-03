"""Sprint 170: Portfolio intelligence capability audit checkpoint guardrails.

Verifies:
- atlas/capabilities/portfolio_intelligence/ contains exactly 3 modules
- atlas.capabilities.portfolio_intelligence.__all__ exports exactly 4 symbols
- All 4 exports are importable
- PortfolioIntelligenceCapability has an .analyze() method
- atlas/capabilities/portfolio_intelligence/ has no imports from deleted closed-track modules
- atlas/capabilities/portfolio_intelligence/ has no provider imports (cleanest boundary)
- atlas.reasoning remains deleted
- Closed cleanup tracks remain closed
"""

import ast
import importlib
from pathlib import Path


# ── Package inventory ─────────────────────────────────────────────────────────

def test_sprint170_portfolio_intelligence_capability_three_modules() -> None:
    """Sprint 170: atlas/capabilities/portfolio_intelligence/ must contain exactly 3 modules."""
    import atlas.capabilities.portfolio_intelligence as _pkg

    pkg_dir = Path(_pkg.__file__).parent
    py_files = {
        f.stem
        for f in pkg_dir.glob("*.py")
        if f.name != "__init__.py" and not f.name.startswith("_")
    }
    expected = {"engine", "models"}
    assert py_files == expected, (
        f"atlas/capabilities/portfolio_intelligence/ module set mismatch. "
        f"Extra: {py_files - expected}. Missing: {expected - py_files}."
    )


# ── Export health ─────────────────────────────────────────────────────────────

def test_sprint170_portfolio_intelligence_all_has_four_exports() -> None:
    """Sprint 170: atlas.capabilities.portfolio_intelligence.__all__ must have exactly 4 exports."""
    import atlas.capabilities.portfolio_intelligence as pkg

    expected = {
        "PortfolioFitDimension",
        "PortfolioFitInput",
        "PortfolioFitResult",
        "PortfolioIntelligenceCapability",
    }
    actual = set(pkg.__all__)
    assert actual == expected, (
        f"atlas.capabilities.portfolio_intelligence.__all__ mismatch. "
        f"Extra: {actual - expected}. Missing: {expected - actual}."
    )


def test_sprint170_all_exports_importable() -> None:
    """Sprint 170: every symbol in atlas.capabilities.portfolio_intelligence.__all__ must be importable."""
    import atlas.capabilities.portfolio_intelligence as pkg

    for name in pkg.__all__:
        assert hasattr(pkg, name), (
            f"atlas.capabilities.portfolio_intelligence.{name} in __all__ but not importable"
        )


# ── PortfolioIntelligenceCapability contract ──────────────────────────────────

def test_sprint170_portfolio_intelligence_capability_has_analyze_method() -> None:
    """Sprint 170: PortfolioIntelligenceCapability must have a callable .analyze() method."""
    from atlas.capabilities.portfolio_intelligence import PortfolioIntelligenceCapability

    assert callable(getattr(PortfolioIntelligenceCapability, "analyze", None)), (
        "PortfolioIntelligenceCapability must have a callable .analyze() method"
    )


# ── Provider boundary ─────────────────────────────────────────────────────────

def test_sprint170_portfolio_intelligence_has_no_provider_imports() -> None:
    """Sprint 170: atlas/capabilities/portfolio_intelligence/ must not import any provider class.
    PortfolioIntelligenceCapability is local-only and deterministic."""
    pkg_dir = Path("atlas/capabilities/portfolio_intelligence")
    for py_file in pkg_dir.glob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        assert "MockCompanyAnalysisProvider" not in source, (
            f"{py_file}: MockCompanyAnalysisProvider must not appear in capabilities/portfolio_intelligence/"
        )
        assert "YahooFinanceProvider" not in source, (
            f"{py_file}: YahooFinanceProvider must not appear in capabilities/portfolio_intelligence/"
        )
        assert "CompanyDataProvider" not in source, (
            f"{py_file}: CompanyDataProvider must not appear in capabilities/portfolio_intelligence/ "
            "— provider coupling lives at CLI layer only"
        )


# ── Boundary: no stale closed-track imports ───────────────────────────────────

def test_sprint170_portfolio_intelligence_has_no_deleted_module_imports() -> None:
    """Sprint 170: atlas/capabilities/portfolio_intelligence/ must not import from deleted modules."""
    deleted_prefixes = {
        "atlas.reasoning",
        "atlas.analysis.portfolio",
        "atlas.analysis.comparison",
        "atlas.analysis.memory",
        "atlas.analysis.scoring",
        "atlas.analysis.watchlist",
    }
    pkg_dir = Path("atlas/capabilities/portfolio_intelligence")
    for py_file in pkg_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for prefix in deleted_prefixes:
                    assert not node.module.startswith(prefix), (
                        f"{py_file}: stale import from deleted module {node.module}"
                    )


# ── Closed cleanup track guardrails ───────────────────────────────────────────

def test_sprint170_reasoning_package_deleted() -> None:
    """Sprint 170: atlas.reasoning must not be importable — deleted Sprint 153."""
    try:
        importlib.import_module("atlas.reasoning")
        assert False, "atlas.reasoning must not be importable after Sprint 153 deletion"
    except ModuleNotFoundError:
        pass


def test_sprint170_legacy_portfolio_intelligence_engine_deleted() -> None:
    """Sprint 170: PortfolioIntelligenceEngine must not be importable from atlas.analysis.portfolio."""
    try:
        from atlas.analysis.portfolio import PortfolioIntelligenceEngine  # noqa: F401
        assert False, (
            "PortfolioIntelligenceEngine must not be importable — deleted Sprint 128"
        )
    except (ImportError, ModuleNotFoundError):
        pass


def test_sprint170_principles_removed_checks_gone() -> None:
    """Sprint 170: removed principles checks must remain absent."""
    import atlas.principles as pkg

    for removed in ("check_reasoning_report", "check_intelligence_report", "check_suitability_assessment"):
        assert not hasattr(pkg, removed), (
            f"{removed} must not be in atlas.principles after Sprint 152/157 removal"
        )


def test_sprint170_analysis_cleanup_track_closed() -> None:
    """Sprint 170: deleted atlas.analysis modules must remain not importable."""
    deleted = [
        "atlas.analysis.portfolio",
        "atlas.analysis.comparison",
        "atlas.analysis.memory",
        "atlas.analysis.watchlist",
        "atlas.analysis.growth",
        "atlas.analysis.scoring",
    ]
    for mod in deleted:
        try:
            importlib.import_module(mod)
            assert False, f"{mod} must not be importable (deleted in analysis cleanup track)"
        except ModuleNotFoundError:
            pass
