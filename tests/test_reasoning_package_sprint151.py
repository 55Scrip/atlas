"""Sprint 151: Reasoning package audit checkpoint guardrails.

Verifies:
- atlas/reasoning/ contains exactly the 2 expected modules
- atlas.reasoning.__all__ exports exactly the 7 expected symbols
- All 7 exports are importable
- ReasoningEngine is importable and produces a ReasoningReport
- atlas/reasoning/ has no provider imports
- atlas/reasoning/ has no imports from deleted analysis modules
- check_reasoning_report() still has zero external callers (blocker for Sprint 152)
- Closed cleanup tracks remain closed
"""

import ast
import importlib
from pathlib import Path


# ── Package inventory ─────────────────────────────────────────────────────────

def test_sprint151_reasoning_package_two_modules_only() -> None:
    """Sprint 151: atlas/reasoning/ must contain exactly 2 modules (init + engine)."""
    import atlas.reasoning as _pkg

    pkg_dir = Path(_pkg.__file__).parent
    py_files = {
        f.stem
        for f in pkg_dir.glob("*.py")
        if f.name != "__init__.py" and not f.name.startswith("_")
    }
    expected = {"engine"}
    assert py_files == expected, (
        f"atlas/reasoning/ module set mismatch. "
        f"Extra: {py_files - expected}. Missing: {expected - py_files}."
    )


# ── Export health ─────────────────────────────────────────────────────────────

def test_sprint151_reasoning_all_has_seven_exports() -> None:
    """Sprint 151: atlas.reasoning.__all__ must contain exactly 7 exports."""
    import atlas.reasoning as pkg

    expected = {
        "ContradictingFactor",
        "Evidence",
        "ReasoningEngine",
        "ReasoningInput",
        "ReasoningReport",
        "SupportingFactor",
        "render_reasoning_report",
    }
    actual = set(pkg.__all__)
    assert actual == expected, (
        f"atlas.reasoning.__all__ mismatch. Extra: {actual - expected}. Missing: {expected - actual}."
    )


def test_sprint151_all_exports_importable() -> None:
    """Sprint 151: every symbol in atlas.reasoning.__all__ must be importable."""
    import atlas.reasoning as pkg

    for name in pkg.__all__:
        assert hasattr(pkg, name), f"atlas.reasoning.{name} in __all__ but not importable"


# ── Engine contract ───────────────────────────────────────────────────────────

def test_sprint151_reasoning_engine_analyze_is_functional() -> None:
    """Sprint 151: ReasoningEngine.analyze must return a ReasoningReport from empty input."""
    from atlas.reasoning import ReasoningEngine, ReasoningInput, ReasoningReport

    engine = ReasoningEngine()
    result = engine.analyze(ReasoningInput())
    assert isinstance(result, ReasoningReport)
    assert isinstance(result.confidence, int)
    assert 0 <= result.confidence <= 100


# ── Boundary: no provider imports ─────────────────────────────────────────────

def test_sprint151_reasoning_has_no_provider_imports() -> None:
    """Sprint 151: atlas/reasoning/ must not import from atlas.providers."""
    reasoning_dir = Path("atlas/reasoning")
    for py_file in reasoning_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("atlas.providers"), (
                    f"{py_file}: must not import from atlas.providers"
                )


def test_sprint151_reasoning_has_no_deleted_analysis_imports() -> None:
    """Sprint 151: atlas/reasoning/ must not import from deleted atlas.analysis submodules."""
    deleted_mods = {
        "atlas.analysis.portfolio",
        "atlas.analysis.comparison",
        "atlas.analysis.memory",
        "atlas.analysis.scoring",
        "atlas.analysis.watchlist",
        "atlas.analysis.growth",
        "atlas.analysis.macro",
        "atlas.analysis.moat",
        "atlas.analysis.quality",
        "atlas.analysis.sentiment",
        "atlas.analysis.technicals",
        "atlas.analysis.valuation",
    }
    reasoning_dir = Path("atlas/reasoning")
    for py_file in reasoning_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in deleted_mods:
                assert False, f"{py_file}: stale import from deleted module {node.module}"


# ── Lazy import blocker still documented ──────────────────────────────────────

def test_sprint151_check_reasoning_report_has_zero_external_callers() -> None:
    """Sprint 151: check_reasoning_report() must have zero external callers.

    This is the blocker for Sprint 152. When this test passes, removing
    check_reasoning_report() from atlas/principles/engine.py is safe.
    """
    principles_source = Path("atlas/principles/engine.py").read_text(encoding="utf-8")
    assert "def check_reasoning_report" in principles_source, (
        "check_reasoning_report() must still exist in atlas/principles/engine.py "
        "until Sprint 152 removes it"
    )

    # Verify it has zero external callers (outside principles itself)
    external_callers = []
    for py_file in Path(".").rglob("*.py"):
        # Exclude principles itself, test files, and deprecations.py (which mentions it in strings)
        rel = str(py_file)
        if "atlas/principles" in rel or "tests/test_reason" in rel or "cli/deprecations" in rel:
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "check_reasoning_report" in source:
            external_callers.append(str(py_file))

    assert not external_callers, (
        f"check_reasoning_report() has external callers — Sprint 152 audit needed: "
        f"{external_callers}"
    )


def test_sprint151_lazy_import_in_principles_is_inside_check_reasoning_report() -> None:
    """Sprint 151: the lazy atlas.reasoning import must be inside check_reasoning_report() only."""
    source = Path("atlas/principles/engine.py").read_text(encoding="utf-8")
    # Confirm lazy import still present (blocks engine deletion until Sprint 152)
    assert "from atlas.reasoning import render_reasoning_report" in source, (
        "Expected lazy import of render_reasoning_report inside check_reasoning_report() — "
        "if gone, Sprint 152 work may already be done"
    )
    # Confirm it is NOT a top-level module import (it must be inside the function body)
    tree = ast.parse(source)
    top_level_imports = [
        node for node in ast.iter_child_nodes(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    for node in top_level_imports:
        if isinstance(node, ast.ImportFrom) and node.module == "atlas.reasoning":
            # TYPE_CHECKING guard imports don't count — they're inside an If block, not top-level
            assert False, (
                "atlas.reasoning is imported at top-level in atlas/principles/engine.py — "
                "it should only appear inside check_reasoning_report() body and TYPE_CHECKING block"
            )


# ── Closed cleanup track guardrails ───────────────────────────────────────────

def test_sprint151_analysis_cleanup_track_closed() -> None:
    """Sprint 151: deleted atlas.analysis modules must remain not importable."""
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


def test_sprint151_provider_cleanup_track_closed() -> None:
    """Sprint 151: stale Yahoo exports removed Sprint 146 must remain absent."""
    import atlas.providers as pkg
    for sym in ("YahooCompany", "YahooFinancials", "YahooMarketData"):
        assert sym not in pkg.__all__, (
            f"{sym} must not be in atlas.providers.__all__ after Sprint 146"
        )


def test_sprint151_portfolio_boundary_closed() -> None:
    """Sprint 151: Portfolio and PortfolioPosition remain in adapter; analysis.portfolio gone."""
    from atlas.adapters.portfolio import Portfolio, PortfolioPosition  # noqa: F401
    assert Portfolio is not None
    assert PortfolioPosition is not None
    try:
        importlib.import_module("atlas.analysis.portfolio")
        assert False, "atlas.analysis.portfolio must not be importable after Sprint 135"
    except ModuleNotFoundError:
        pass


def test_sprint151_adapter_does_not_import_portfolio_fit_input() -> None:
    """Sprint 151: stale PortfolioFitInput import removed Sprint 148 must remain absent."""
    source = Path("atlas/adapters/portfolio.py").read_text(encoding="utf-8")
    assert "PortfolioFitInput" not in source, (
        "atlas/adapters/portfolio.py must not import PortfolioFitInput — removed Sprint 148"
    )
