"""Sprint 156: Principles package audit checkpoint guardrails.

Verifies:
- atlas/principles/ contains exactly 2 modules
- atlas.principles.__all__ exports exactly 11 expected symbols
- All 11 exports are importable
- PrinciplesEngine and PrinciplesCheck are importable and correct types
- atlas/principles/ has no provider imports
- atlas/principles/ has no imports from deleted atlas.reasoning
- check_reasoning_report is not in atlas.principles (removed Sprint 152)
- Known production callers still import PrinciplesEngine
- atlas principles check CLI command path imports expected symbols
- Closed cleanup tracks remain closed
"""

import ast
import importlib
from pathlib import Path


# ── Package inventory ─────────────────────────────────────────────────────────

def test_sprint156_principles_package_two_modules_only() -> None:
    """Sprint 156: atlas/principles/ must contain exactly 2 modules (init + engine)."""
    import atlas.principles as _pkg

    pkg_dir = Path(_pkg.__file__).parent
    py_files = {
        f.stem
        for f in pkg_dir.glob("*.py")
        if f.name != "__init__.py" and not f.name.startswith("_")
    }
    expected = {"engine"}
    assert py_files == expected, (
        f"atlas/principles/ module set mismatch. "
        f"Extra: {py_files - expected}. Missing: {expected - py_files}."
    )


# ── Export health ─────────────────────────────────────────────────────────────

def test_sprint156_principles_all_has_eleven_exports() -> None:
    """Sprint 156: atlas.principles.__all__ must contain exactly 11 exports."""
    import atlas.principles as pkg

    expected = {
        "AtlasPrinciple",
        "PrincipleCategory",
        "PrincipleEvaluation",
        "PrinciplesCheck",
        "PrinciplesEngine",
        "PrinciplesResult",
        "check_conversation_response",
        "check_intelligence_report",
        "check_suitability_assessment",
        "check_text_against_principles",
        "render_principles_check",
    }
    actual = set(pkg.__all__)
    assert actual == expected, (
        f"atlas.principles.__all__ mismatch. Extra: {actual - expected}. Missing: {expected - actual}."
    )


def test_sprint156_all_exports_importable() -> None:
    """Sprint 156: every symbol in atlas.principles.__all__ must be importable."""
    import atlas.principles as pkg

    for name in pkg.__all__:
        assert hasattr(pkg, name), f"atlas.principles.{name} in __all__ but not importable"


# ── Sprint 152 removal verification ───────────────────────────────────────────

def test_sprint156_check_reasoning_report_not_in_principles() -> None:
    """Sprint 156: check_reasoning_report must not exist in atlas.principles (removed Sprint 152)."""
    import atlas.principles as pkg

    assert not hasattr(pkg, "check_reasoning_report"), (
        "check_reasoning_report must not be exported from atlas.principles after Sprint 152"
    )
    assert "check_reasoning_report" not in pkg.__all__, (
        "check_reasoning_report must not be in atlas.principles.__all__ after Sprint 152"
    )


def test_sprint156_principles_engine_has_no_reasoning_references() -> None:
    """Sprint 156: atlas/principles/engine.py must not reference atlas.reasoning."""
    source = Path("atlas/principles/engine.py").read_text(encoding="utf-8")
    assert "atlas.reasoning" not in source, (
        "atlas/principles/engine.py must not reference atlas.reasoning after Sprint 152"
    )
    assert "check_reasoning_report" not in source, (
        "check_reasoning_report must not exist in atlas/principles/engine.py after Sprint 152"
    )


# ── Boundary: no provider imports ─────────────────────────────────────────────

def test_sprint156_principles_has_no_provider_imports() -> None:
    """Sprint 156: atlas/principles/ must not import from atlas.providers."""
    principles_dir = Path("atlas/principles")
    for py_file in principles_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("atlas.providers"), (
                    f"{py_file}: must not import from atlas.providers"
                )


# ── Known production callers still import PrinciplesEngine ────────────────────

def test_sprint156_comparison_engine_imports_principles_engine() -> None:
    """Sprint 156: atlas/comparison/engine.py must import PrinciplesEngine."""
    source = Path("atlas/comparison/engine.py").read_text(encoding="utf-8")
    assert "from atlas.principles import" in source
    assert "PrinciplesEngine" in source


def test_sprint156_dashboard_engine_imports_principles_engine() -> None:
    """Sprint 156: atlas/dashboard/engine.py must import PrinciplesEngine."""
    source = Path("atlas/dashboard/engine.py").read_text(encoding="utf-8")
    assert "from atlas.principles import" in source
    assert "PrinciplesEngine" in source


def test_sprint156_cli_imports_principles_engine_and_renderer() -> None:
    """Sprint 156: atlas/cli/main.py must import PrinciplesEngine and render_principles_check."""
    source = Path("atlas/cli/main.py").read_text(encoding="utf-8")
    assert "PrinciplesEngine" in source
    assert "render_principles_check" in source


# ── Closed cleanup track guardrails ───────────────────────────────────────────

def test_sprint156_reasoning_package_deleted() -> None:
    """Sprint 156: atlas.reasoning must not be importable — deleted Sprint 153."""
    try:
        importlib.import_module("atlas.reasoning")
        assert False, "atlas.reasoning must not be importable after Sprint 153 deletion"
    except ModuleNotFoundError:
        pass


def test_sprint156_analysis_cleanup_track_closed() -> None:
    """Sprint 156: deleted atlas.analysis modules must remain not importable."""
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


def test_sprint156_provider_cleanup_track_closed() -> None:
    """Sprint 156: stale Yahoo exports removed Sprint 146 must remain absent."""
    import atlas.providers as pkg

    for sym in ("YahooCompany", "YahooFinancials", "YahooMarketData"):
        assert sym not in pkg.__all__, (
            f"{sym} must not be in atlas.providers.__all__ after Sprint 146"
        )
