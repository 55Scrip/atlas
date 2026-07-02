"""Sprint 142: Decision package inventory checkpoint guardrails.

Verifies:
- atlas/decision/ contains exactly the 7 expected modules
- atlas.decision.__all__ has exactly the 5 expected exports
- all 5 exports are importable
- comparison.py and memory.py active symbols are importable
- render_comparison_result is importable but has no production callers (dead function)
- deleted analysis modules that comparison/memory replaced remain not importable
"""

import importlib


# ── Module inventory ──────────────────────────────────────────────────────────

def test_sprint142_decision_package_seven_modules_only() -> None:
    """Sprint 142: atlas/decision/ must contain exactly 7 modules."""
    from pathlib import Path
    import atlas.decision as _pkg

    pkg_dir = Path(_pkg.__file__).parent
    py_files = {
        f.stem
        for f in pkg_dir.glob("*.py")
        if f.name != "__init__.py" and not f.name.startswith("_")
    }
    expected = {
        "comparison",
        "decision_context",
        "decision_engine",
        "decision_renderer",
        "decision_result",
        "memory",
    }
    assert py_files == expected, (
        f"atlas/decision/ module set mismatch. "
        f"Extra: {py_files - expected}. Missing: {expected - py_files}."
    )


# ── Export health ─────────────────────────────────────────────────────────────

def test_sprint142_atlas_decision_all_has_exactly_5_exports() -> None:
    """Sprint 142: atlas.decision.__all__ must have exactly the 5 expected exports."""
    import atlas.decision as pkg

    expected = {
        "AtlasDecisionEngine",
        "DecisionAction",
        "DecisionContext",
        "DecisionResult",
        "render_decision_result",
    }
    actual = set(pkg.__all__)
    assert actual == expected, (
        f"atlas.decision.__all__ mismatch. "
        f"Extra: {actual - expected}. Missing: {expected - actual}."
    )


def test_sprint142_all_exports_importable() -> None:
    """Sprint 142: every symbol in atlas.decision.__all__ must be importable."""
    import atlas.decision as pkg

    for name in pkg.__all__:
        assert hasattr(pkg, name), f"atlas.decision.{name} listed in __all__ but not importable"


# ── Active comparison symbols ─────────────────────────────────────────────────

def test_sprint142_comparison_active_symbols_importable() -> None:
    """Sprint 142: active comparison symbols (types + compare_tickers) must be importable."""
    from atlas.decision.comparison import (  # noqa: F401
        ComparisonCandidate,
        ComparisonRanking,
        ComparisonResult,
        compare_tickers,
    )


def test_sprint142_render_comparison_result_is_importable() -> None:
    """Sprint 142: render_comparison_result exists but has zero external callers — dead function."""
    from atlas.decision.comparison import render_comparison_result  # noqa: F401


# ── Active memory symbols ─────────────────────────────────────────────────────

def test_sprint142_memory_symbols_importable() -> None:
    """Sprint 142: all active memory symbols must be importable."""
    from atlas.decision.memory import (  # noqa: F401
        MemoryComparison,
        MemoryEntry,
        MemoryStore,
        compare_memory,
        render_memory_comparison,
        render_memory_entries,
        save_ticker,
    )


# ── Replaced module guardrails ────────────────────────────────────────────────

def test_sprint142_replaced_analysis_modules_still_gone() -> None:
    """Sprint 142: atlas.analysis.comparison and atlas.analysis.memory must remain deleted."""
    for mod in ("atlas.analysis.comparison", "atlas.analysis.memory"):
        try:
            importlib.import_module(mod)
            assert False, f"{mod} must not be importable — it was deleted and replaced by atlas.decision"
        except ModuleNotFoundError:
            pass
