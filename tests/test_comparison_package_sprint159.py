"""Sprint 159: Comparison package audit checkpoint guardrails.

Verifies:
- atlas/comparison/ contains exactly 2 modules
- atlas.comparison.__all__ exports exactly 9 expected symbols
- All 9 exports are importable
- InvestmentComparisonEngine is importable and has a .compare() method
- atlas/comparison/ has no imports from deleted atlas.reasoning or atlas.analysis.portfolio
- atlas/comparison/ does not import YahooFinanceProvider directly
- atlas compare CLI command is active
- Closed cleanup tracks remain closed
"""

import ast
import importlib
from pathlib import Path


# ── Package inventory ─────────────────────────────────────────────────────────

def test_sprint159_comparison_package_two_modules_only() -> None:
    """Sprint 159: atlas/comparison/ must contain exactly 2 modules (init + engine)."""
    import atlas.comparison as _pkg

    pkg_dir = Path(_pkg.__file__).parent
    py_files = {
        f.stem
        for f in pkg_dir.glob("*.py")
        if f.name != "__init__.py" and not f.name.startswith("_")
    }
    expected = {"engine"}
    assert py_files == expected, (
        f"atlas/comparison/ module set mismatch. "
        f"Extra: {py_files - expected}. Missing: {expected - py_files}."
    )


# ── Export health ─────────────────────────────────────────────────────────────

def test_sprint159_comparison_all_has_nine_exports() -> None:
    """Sprint 159: atlas.comparison.__all__ must contain exactly 9 exports."""
    import atlas.comparison as pkg

    expected = {
        "ComparisonRating",
        "InvestmentComparisonCandidate",
        "InvestmentComparisonEngine",
        "InvestmentComparisonInput",
        "InvestmentComparisonObservation",
        "InvestmentComparisonReport",
        "InvestmentComparisonSection",
        "demo_investment_comparison_input",
        "render_investment_comparison",
    }
    actual = set(pkg.__all__)
    assert actual == expected, (
        f"atlas.comparison.__all__ mismatch. Extra: {actual - expected}. Missing: {expected - actual}."
    )


def test_sprint159_all_exports_importable() -> None:
    """Sprint 159: every symbol in atlas.comparison.__all__ must be importable."""
    import atlas.comparison as pkg

    for name in pkg.__all__:
        assert hasattr(pkg, name), f"atlas.comparison.{name} in __all__ but not importable"


# ── InvestmentComparisonEngine contract ───────────────────────────────────────

def test_sprint159_investment_comparison_engine_has_compare_method() -> None:
    """Sprint 159: InvestmentComparisonEngine must have a .compare() method."""
    from atlas.comparison import InvestmentComparisonEngine

    assert callable(getattr(InvestmentComparisonEngine, "compare", None)), (
        "InvestmentComparisonEngine must have a callable .compare() method"
    )


# ── Boundary: no stale closed-track imports ───────────────────────────────────

def test_sprint159_comparison_has_no_deleted_module_imports() -> None:
    """Sprint 159: atlas/comparison/ must not import from deleted closed-track modules."""
    deleted_prefixes = {
        "atlas.reasoning",
        "atlas.analysis.portfolio",
        "atlas.analysis.comparison",
        "atlas.analysis.memory",
        "atlas.analysis.scoring",
        "atlas.analysis.watchlist",
    }
    comparison_dir = Path("atlas/comparison")
    for py_file in comparison_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for prefix in deleted_prefixes:
                    assert not node.module.startswith(prefix), (
                        f"{py_file}: stale import from deleted module {node.module}"
                    )


def test_sprint159_comparison_does_not_import_yahoo_finance_provider_directly() -> None:
    """Sprint 159: atlas/comparison/ must not import YahooFinanceProvider (network opt-in via CLI only)."""
    comparison_dir = Path("atlas/comparison")
    for py_file in comparison_dir.glob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        assert "YahooFinanceProvider" not in source, (
            f"{py_file}: YahooFinanceProvider must not be imported in atlas/comparison/ "
            "— network access must remain CLI opt-in only"
        )


# ── CLI comparison command active ─────────────────────────────────────────────

def test_sprint159_cli_compare_command_imports_comparison_engine() -> None:
    """Sprint 159: atlas/cli/main.py must import InvestmentComparisonEngine."""
    source = Path("atlas/cli/main.py").read_text(encoding="utf-8")
    assert "InvestmentComparisonEngine" in source, (
        "atlas/cli/main.py must import InvestmentComparisonEngine for atlas compare command"
    )
    assert "render_investment_comparison" in source, (
        "atlas/cli/main.py must import render_investment_comparison"
    )


# ── Closed cleanup track guardrails ───────────────────────────────────────────

def test_sprint159_reasoning_package_deleted() -> None:
    """Sprint 159: atlas.reasoning must not be importable — deleted Sprint 153."""
    try:
        importlib.import_module("atlas.reasoning")
        assert False, "atlas.reasoning must not be importable after Sprint 153 deletion"
    except ModuleNotFoundError:
        pass


def test_sprint159_principles_removed_checks_gone() -> None:
    """Sprint 159: removed principles checks must remain absent."""
    import atlas.principles as pkg

    for removed in ("check_reasoning_report", "check_intelligence_report", "check_suitability_assessment"):
        assert not hasattr(pkg, removed), (
            f"{removed} must not be in atlas.principles after Sprint 152/157 removal"
        )


def test_sprint159_analysis_cleanup_track_closed() -> None:
    """Sprint 159: deleted atlas.analysis modules must remain not importable."""
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
