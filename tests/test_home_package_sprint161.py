"""Sprint 161: Home package audit checkpoint guardrails.

Verifies:
- atlas/home/ contains exactly 2 modules
- atlas.home.__all__ exports exactly 7 expected symbols
- All 7 exports are importable
- AtlasHomeEngine is importable and has a .build() method
- atlas/home/ has no imports from deleted atlas.reasoning or atlas.analysis.portfolio
- atlas/home/ does not import YahooFinanceProvider directly
- atlas home CLI command imports expected symbols
- Closed cleanup tracks remain closed
"""

import ast
import importlib
from pathlib import Path


# ── Package inventory ─────────────────────────────────────────────────────────

def test_sprint161_home_package_two_modules_only() -> None:
    """Sprint 161: atlas/home/ must contain exactly 2 modules (init + engine)."""
    import atlas.home as _pkg

    pkg_dir = Path(_pkg.__file__).parent
    py_files = {
        f.stem
        for f in pkg_dir.glob("*.py")
        if f.name != "__init__.py" and not f.name.startswith("_")
    }
    expected = {"engine"}
    assert py_files == expected, (
        f"atlas/home/ module set mismatch. "
        f"Extra: {py_files - expected}. Missing: {expected - py_files}."
    )


# ── Export health ─────────────────────────────────────────────────────────────

def test_sprint161_home_all_has_seven_exports() -> None:
    """Sprint 161: atlas.home.__all__ must contain exactly 7 exports."""
    import atlas.home as pkg

    expected = {
        "AtlasHomeEngine",
        "AtlasHomeInput",
        "AtlasHomeMonitoring",
        "AtlasHomeOutput",
        "AtlasHomePriority",
        "AtlasHomeSummary",
        "render_atlas_home",
    }
    actual = set(pkg.__all__)
    assert actual == expected, (
        f"atlas.home.__all__ mismatch. Extra: {actual - expected}. Missing: {expected - actual}."
    )


def test_sprint161_all_exports_importable() -> None:
    """Sprint 161: every symbol in atlas.home.__all__ must be importable."""
    import atlas.home as pkg

    for name in pkg.__all__:
        assert hasattr(pkg, name), f"atlas.home.{name} in __all__ but not importable"


# ── AtlasHomeEngine contract ───────────────────────────────────────────────────

def test_sprint161_atlas_home_engine_has_build_method() -> None:
    """Sprint 161: AtlasHomeEngine must have a .build() method."""
    from atlas.home import AtlasHomeEngine

    assert callable(getattr(AtlasHomeEngine, "build", None)), (
        "AtlasHomeEngine must have a callable .build() method"
    )


# ── Boundary: no stale closed-track imports ───────────────────────────────────

def test_sprint161_home_has_no_deleted_module_imports() -> None:
    """Sprint 161: atlas/home/ must not import from deleted closed-track modules."""
    deleted_prefixes = {
        "atlas.reasoning",
        "atlas.analysis.portfolio",
        "atlas.analysis.comparison",
        "atlas.analysis.memory",
        "atlas.analysis.scoring",
        "atlas.analysis.watchlist",
    }
    home_dir = Path("atlas/home")
    for py_file in home_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for prefix in deleted_prefixes:
                    assert not node.module.startswith(prefix), (
                        f"{py_file}: stale import from deleted module {node.module}"
                    )


def test_sprint161_home_does_not_import_yahoo_finance_provider_directly() -> None:
    """Sprint 161: atlas/home/ must not import YahooFinanceProvider (network opt-in via CLI only)."""
    home_dir = Path("atlas/home")
    for py_file in home_dir.glob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        assert "YahooFinanceProvider" not in source, (
            f"{py_file}: YahooFinanceProvider must not be imported in atlas/home/ "
            "— network access must remain CLI opt-in only"
        )


# ── CLI home command active ────────────────────────────────────────────────────

def test_sprint161_cli_home_command_imports_home_engine() -> None:
    """Sprint 161: atlas/cli/main.py must import AtlasHomeEngine for atlas home command."""
    source = Path("atlas/cli/main.py").read_text(encoding="utf-8")
    assert "AtlasHomeEngine" in source, (
        "atlas/cli/main.py must import AtlasHomeEngine for atlas home command"
    )
    assert "render_atlas_home" in source, (
        "atlas/cli/main.py must import render_atlas_home"
    )


# ── Closed cleanup track guardrails ───────────────────────────────────────────

def test_sprint161_reasoning_package_deleted() -> None:
    """Sprint 161: atlas.reasoning must not be importable — deleted Sprint 153."""
    try:
        importlib.import_module("atlas.reasoning")
        assert False, "atlas.reasoning must not be importable after Sprint 153 deletion"
    except ModuleNotFoundError:
        pass


def test_sprint161_principles_removed_checks_gone() -> None:
    """Sprint 161: removed principles checks must remain absent."""
    import atlas.principles as pkg

    for removed in ("check_reasoning_report", "check_intelligence_report", "check_suitability_assessment"):
        assert not hasattr(pkg, removed), (
            f"{removed} must not be in atlas.principles after Sprint 152/157 removal"
        )


def test_sprint161_analysis_cleanup_track_closed() -> None:
    """Sprint 161: deleted atlas.analysis modules must remain not importable."""
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
