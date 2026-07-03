"""Sprint 164: Intelligence package audit checkpoint guardrails.

Verifies:
- atlas/intelligence/ contains exactly 2 modules (init + engine)
- atlas.intelligence.__all__ exports exactly 5 expected symbols
- All 5 exports are importable
- IntelligenceEngine has a .analyze() method
- atlas/intelligence/ has no imports from deleted closed-track modules
- atlas/intelligence/ does not import YahooFinanceProvider directly
- atlas intelligence CLI command imports expected symbols
- RiskAnalysis import remains intentional (runtime, not removed)
- atlas.reasoning remains deleted (distinct from domains.decision.ReasoningEngine)
- Closed cleanup tracks remain closed
"""

import ast
import importlib
from pathlib import Path


# ── Package inventory ─────────────────────────────────────────────────────────

def test_sprint164_intelligence_package_two_modules_only() -> None:
    """Sprint 164: atlas/intelligence/ must contain exactly 2 modules (init + engine)."""
    import atlas.intelligence as _pkg

    pkg_dir = Path(_pkg.__file__).parent
    py_files = {
        f.stem
        for f in pkg_dir.glob("*.py")
        if f.name != "__init__.py" and not f.name.startswith("_")
    }
    expected = {"engine"}
    assert py_files == expected, (
        f"atlas/intelligence/ module set mismatch. "
        f"Extra: {py_files - expected}. Missing: {expected - py_files}."
    )


# ── Export health ─────────────────────────────────────────────────────────────

def test_sprint164_intelligence_all_has_five_exports() -> None:
    """Sprint 164: atlas.intelligence.__all__ must contain exactly 5 exports."""
    import atlas.intelligence as pkg

    expected = {
        "IntelligenceContext",
        "IntelligenceEngine",
        "IntelligenceInput",
        "IntelligenceReport",
        "render_intelligence_report",
    }
    actual = set(pkg.__all__)
    assert actual == expected, (
        f"atlas.intelligence.__all__ mismatch. Extra: {actual - expected}. Missing: {expected - actual}."
    )


def test_sprint164_all_exports_importable() -> None:
    """Sprint 164: every symbol in atlas.intelligence.__all__ must be importable."""
    import atlas.intelligence as pkg

    for name in pkg.__all__:
        assert hasattr(pkg, name), f"atlas.intelligence.{name} in __all__ but not importable"


# ── IntelligenceEngine contract ───────────────────────────────────────────────

def test_sprint164_intelligence_engine_has_analyze_method() -> None:
    """Sprint 164: IntelligenceEngine must have a .analyze() method."""
    from atlas.intelligence import IntelligenceEngine

    assert callable(getattr(IntelligenceEngine, "analyze", None)), (
        "IntelligenceEngine must have a callable .analyze() method"
    )


# ── Boundary: no stale closed-track imports ───────────────────────────────────

def test_sprint164_intelligence_has_no_deleted_module_imports() -> None:
    """Sprint 164: atlas/intelligence/ must not import from deleted closed-track modules."""
    deleted_prefixes = {
        "atlas.reasoning",
        "atlas.analysis.portfolio",
        "atlas.analysis.comparison",
        "atlas.analysis.memory",
        "atlas.analysis.scoring",
        "atlas.analysis.watchlist",
    }
    intel_dir = Path("atlas/intelligence")
    for py_file in intel_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for prefix in deleted_prefixes:
                    assert not node.module.startswith(prefix), (
                        f"{py_file}: stale import from deleted module {node.module}"
                    )


def test_sprint164_intelligence_does_not_import_yahoo_finance_provider_directly() -> None:
    """Sprint 164: atlas/intelligence/ must not import YahooFinanceProvider directly."""
    intel_dir = Path("atlas/intelligence")
    for py_file in intel_dir.glob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        assert "YahooFinanceProvider" not in source, (
            f"{py_file}: YahooFinanceProvider must not be imported in atlas/intelligence/ "
            "— network access must remain CLI opt-in only"
        )


# ── RiskAnalysis dependency remains intentional ───────────────────────────────

def test_sprint164_intelligence_imports_risk_analysis() -> None:
    """Sprint 164: atlas/intelligence/engine.py must import RiskAnalysis from atlas.risk (intentional dependency)."""
    source = Path("atlas/intelligence/engine.py").read_text(encoding="utf-8")
    assert "from atlas.risk import RiskAnalysis" in source, (
        "atlas/intelligence/engine.py must import RiskAnalysis from atlas.risk — "
        "this is an intentional optional context dependency"
    )


# ── CLI intelligence command active ──────────────────────────────────────────

def test_sprint164_cli_intelligence_analyze_imports_intelligence_engine() -> None:
    """Sprint 164: atlas/cli/main.py must import IntelligenceEngine for atlas intelligence analyze."""
    source = Path("atlas/cli/main.py").read_text(encoding="utf-8")
    assert "IntelligenceEngine" in source, (
        "atlas/cli/main.py must import IntelligenceEngine for atlas intelligence analyze"
    )
    assert "render_intelligence_report" in source, (
        "atlas/cli/main.py must import render_intelligence_report"
    )


# ── Closed cleanup track guardrails ───────────────────────────────────────────

def test_sprint164_reasoning_package_deleted() -> None:
    """Sprint 164: atlas.reasoning must not be importable — deleted Sprint 153."""
    try:
        importlib.import_module("atlas.reasoning")
        assert False, "atlas.reasoning must not be importable after Sprint 153 deletion"
    except ModuleNotFoundError:
        pass


def test_sprint164_principles_removed_checks_gone() -> None:
    """Sprint 164: removed principles checks must remain absent."""
    import atlas.principles as pkg

    for removed in ("check_reasoning_report", "check_intelligence_report", "check_suitability_assessment"):
        assert not hasattr(pkg, removed), (
            f"{removed} must not be in atlas.principles after Sprint 152/157 removal"
        )


def test_sprint164_analysis_cleanup_track_closed() -> None:
    """Sprint 164: deleted atlas.analysis modules must remain not importable."""
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


def test_sprint164_stale_risk_size_deprecation_string_corrected() -> None:
    """Sprint 164: risk size removal_criteria must not reference atlas/reasoning engines (deleted Sprint 153)."""
    source = Path("atlas/cli/deprecations.py").read_text(encoding="utf-8")
    # The stale reference was 'atlas/reasoning engines' as a RiskAnalysis caller.
    # After Sprint 164 correction, it should reference the actual callers.
    assert "atlas/reasoning engines" not in source, (
        "atlas/cli/deprecations.py still contains stale 'atlas/reasoning engines' reference — "
        "should have been corrected in Sprint 164"
    )
    assert "atlas/conversation and atlas/intelligence engines" in source, (
        "atlas/cli/deprecations.py should now reference the correct callers: "
        "atlas/conversation and atlas/intelligence engines"
    )
