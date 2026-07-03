"""Sprint 168: Dashboard package audit checkpoint guardrails.

Verifies:
- atlas/dashboard/ contains exactly 2 modules (init + engine)
- atlas.dashboard.__all__ exports exactly 6 expected symbols
- All 6 exports are importable
- DashboardEngine has a .build() method
- atlas/dashboard/ has no imports from deleted closed-track modules
- atlas/dashboard/ does not import YahooFinanceProvider or MockCompanyAnalysisProvider directly
- atlas dashboard CLI command imports expected symbols
- atlas.reasoning remains deleted
- Closed cleanup tracks remain closed
"""

import ast
import importlib
from pathlib import Path


# ── Package inventory ─────────────────────────────────────────────────────────

def test_sprint168_dashboard_package_two_modules_only() -> None:
    """Sprint 168: atlas/dashboard/ must contain exactly 2 modules (init + engine)."""
    import atlas.dashboard as _pkg

    pkg_dir = Path(_pkg.__file__).parent
    py_files = {
        f.stem
        for f in pkg_dir.glob("*.py")
        if f.name != "__init__.py" and not f.name.startswith("_")
    }
    expected = {"engine"}
    assert py_files == expected, (
        f"atlas/dashboard/ module set mismatch. "
        f"Extra: {py_files - expected}. Missing: {expected - py_files}."
    )


# ── Export health ─────────────────────────────────────────────────────────────

def test_sprint168_dashboard_all_has_six_exports() -> None:
    """Sprint 168: atlas.dashboard.__all__ must contain exactly 6 exports."""
    import atlas.dashboard as pkg

    expected = {
        "DashboardCard",
        "DashboardEngine",
        "DashboardInput",
        "DashboardSection",
        "DashboardSummary",
        "render_dashboard",
    }
    actual = set(pkg.__all__)
    assert actual == expected, (
        f"atlas.dashboard.__all__ mismatch. Extra: {actual - expected}. Missing: {expected - actual}."
    )


def test_sprint168_all_exports_importable() -> None:
    """Sprint 168: every symbol in atlas.dashboard.__all__ must be importable."""
    import atlas.dashboard as pkg

    for name in pkg.__all__:
        assert hasattr(pkg, name), f"atlas.dashboard.{name} in __all__ but not importable"


# ── DashboardEngine contract ──────────────────────────────────────────────────

def test_sprint168_dashboard_engine_has_build_method() -> None:
    """Sprint 168: DashboardEngine must have a .build() method."""
    from atlas.dashboard import DashboardEngine

    assert callable(getattr(DashboardEngine, "build", None)), (
        "DashboardEngine must have a callable .build() method"
    )


# ── Provider boundary: cleanest of any audited package ───────────────────────

def test_sprint168_dashboard_does_not_import_concrete_providers() -> None:
    """Sprint 168: atlas/dashboard/ must not import MockCompanyAnalysisProvider or YahooFinanceProvider.
    Provider selection belongs at the CLI layer only."""
    dashboard_dir = Path("atlas/dashboard")
    for py_file in dashboard_dir.glob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        assert "MockCompanyAnalysisProvider" not in source, (
            f"{py_file}: MockCompanyAnalysisProvider must not be imported in atlas/dashboard/ "
            "— provider instantiation belongs at the CLI layer"
        )
        assert "YahooFinanceProvider" not in source, (
            f"{py_file}: YahooFinanceProvider must not be imported in atlas/dashboard/ "
            "— network access must remain CLI opt-in only"
        )


# ── Boundary: no stale closed-track imports ───────────────────────────────────

def test_sprint168_dashboard_has_no_deleted_module_imports() -> None:
    """Sprint 168: atlas/dashboard/ must not import from deleted closed-track modules."""
    deleted_prefixes = {
        "atlas.reasoning",
        "atlas.analysis.portfolio",
        "atlas.analysis.comparison",
        "atlas.analysis.memory",
        "atlas.analysis.scoring",
        "atlas.analysis.watchlist",
    }
    dashboard_dir = Path("atlas/dashboard")
    for py_file in dashboard_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for prefix in deleted_prefixes:
                    assert not node.module.startswith(prefix), (
                        f"{py_file}: stale import from deleted module {node.module}"
                    )


# ── CLI dashboard command active ──────────────────────────────────────────────

def test_sprint168_cli_dashboard_show_imports_dashboard_engine() -> None:
    """Sprint 168: atlas/cli/main.py must import DashboardEngine for atlas dashboard show."""
    source = Path("atlas/cli/main.py").read_text(encoding="utf-8")
    assert "DashboardEngine" in source, (
        "atlas/cli/main.py must import DashboardEngine for atlas dashboard show"
    )
    assert "render_dashboard" in source, (
        "atlas/cli/main.py must import render_dashboard"
    )


# ── Closed cleanup track guardrails ───────────────────────────────────────────

def test_sprint168_reasoning_package_deleted() -> None:
    """Sprint 168: atlas.reasoning must not be importable — deleted Sprint 153."""
    try:
        importlib.import_module("atlas.reasoning")
        assert False, "atlas.reasoning must not be importable after Sprint 153 deletion"
    except ModuleNotFoundError:
        pass


def test_sprint168_principles_removed_checks_gone() -> None:
    """Sprint 168: removed principles checks must remain absent."""
    import atlas.principles as pkg

    for removed in ("check_reasoning_report", "check_intelligence_report", "check_suitability_assessment"):
        assert not hasattr(pkg, removed), (
            f"{removed} must not be in atlas.principles after Sprint 152/157 removal"
        )


def test_sprint168_analysis_cleanup_track_closed() -> None:
    """Sprint 168: deleted atlas.analysis modules must remain not importable."""
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
