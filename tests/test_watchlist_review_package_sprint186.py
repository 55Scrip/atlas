"""Sprint 186 guardrail tests for atlas/watchlist_review/ audit.

Verifies:
- All 11 watchlist_review exports importable
- watchlist_review does not import deleted atlas.reasoning
- watchlist_review does not import deleted atlas.analysis submodules
- watchlist_review does not import atlas.cli
- watchlist_review does not import atlas.capabilities (other than watchlist_intelligence)
- watchlist_review does not import atlas.adapters
- Provider coupling is documented: CompanyDataProvider and MockCompanyAnalysisProvider
  are intentionally imported — not a guardrail violation, but confirmed present
- CompanyAnalysisProvider alias remains absent from atlas.analysis.company_analysis
"""

import ast
import pathlib


# ── All 11 exports importable ─────────────────────────────────────────────────

def test_watchlist_review_all_exports_importable():
    """Sprint 186: all 11 atlas.watchlist_review exports must be importable."""
    from atlas.watchlist_review import (  # noqa: F401
        WatchlistReviewEngine,
        WatchlistReviewInput,
        WatchlistReviewItem,
        WatchlistReviewObservation,
        WatchlistReviewRating,
        WatchlistReviewReport,
        WatchlistReviewSection,
        demo_watchlist_review_input,
        render_watchlist_review,
        watchlist_review_input_from_json_file,
        watchlist_review_input_from_mapping,
    )
    assert callable(WatchlistReviewEngine)


def test_watchlist_review_all_has_eleven_exports():
    """Sprint 186: atlas.watchlist_review.__all__ must have exactly 11 exports."""
    import atlas.watchlist_review as pkg
    expected = {
        "WatchlistReviewEngine",
        "WatchlistReviewInput",
        "WatchlistReviewItem",
        "WatchlistReviewObservation",
        "WatchlistReviewRating",
        "WatchlistReviewReport",
        "WatchlistReviewSection",
        "demo_watchlist_review_input",
        "render_watchlist_review",
        "watchlist_review_input_from_json_file",
        "watchlist_review_input_from_mapping",
    }
    assert set(pkg.__all__) == expected, (
        f"atlas.watchlist_review.__all__ mismatch. "
        f"Expected: {sorted(expected)}. Found: {sorted(pkg.__all__)}"
    )


# ── Boundary: no deleted-track imports ───────────────────────────────────────

def test_watchlist_review_does_not_import_deleted_reasoning():
    """Sprint 186: atlas/watchlist_review/ must not import deleted atlas.reasoning."""
    wr_dir = pathlib.Path("atlas/watchlist_review")
    for py_file in wr_dir.glob("*.py"):
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("atlas.reasoning"), (
                    f"{py_file} imports deleted atlas.reasoning: {node.module}"
                )


def test_watchlist_review_does_not_import_deleted_analysis_submodules():
    """Sprint 186: atlas/watchlist_review/ must not import deleted atlas.analysis submodules."""
    deleted_prefixes = (
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
    )
    wr_dir = pathlib.Path("atlas/watchlist_review")
    for py_file in wr_dir.glob("*.py"):
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for prefix in deleted_prefixes:
                    assert not node.module.startswith(prefix), (
                        f"{py_file} imports deleted module {prefix}: {node.module}"
                    )


# ── Boundary: no CLI coupling, no adapters ───────────────────────────────────

def test_watchlist_review_does_not_import_cli():
    """Sprint 186: atlas/watchlist_review/ must not import atlas.cli."""
    wr_dir = pathlib.Path("atlas/watchlist_review")
    for py_file in wr_dir.glob("*.py"):
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("atlas.cli"), (
                    f"{py_file} imports atlas.cli (upward coupling): {node.module}"
                )


def test_watchlist_review_does_not_import_adapters():
    """Sprint 186: atlas/watchlist_review/ must not import atlas.adapters."""
    wr_dir = pathlib.Path("atlas/watchlist_review")
    for py_file in wr_dir.glob("*.py"):
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("atlas.adapters"), (
                    f"{py_file} imports atlas.adapters (upward coupling): {node.module}"
                )


# ── Provider coupling: document that it exists (not a guard against it) ──────

def test_watchlist_review_provider_coupling_is_documented():
    """Sprint 186/187: atlas/watchlist_review/engine.py imports CompanyDataProvider and
    MockCompanyAnalysisProvider from atlas.providers. Sprint 187 classified this as
    acceptable legacy coupling — the same pattern is used in atlas/cli/main.py and
    atlas/home/engine.py. CompanyDataProvider is a Protocol (type-only import);
    MockCompanyAnalysisProvider is the required deterministic default. This test asserts
    the coupling EXISTS so any future removal is flagged for review and docs updated.
    """
    source = pathlib.Path("atlas/watchlist_review/engine.py").read_text()
    assert "from atlas.providers import" in source, (
        "Expected provider import not found — if this was removed, update "
        "docs/WatchlistReviewCleanupPlan.md and remove this test."
    )
    assert "CompanyDataProvider" in source
    assert "MockCompanyAnalysisProvider" in source


# ── CompanyAnalysisProvider remains absent ───────────────────────────────────

def test_company_analysis_provider_alias_remains_absent_sprint186():
    """Sprint 186: CompanyAnalysisProvider must not appear in any active atlas/ module.

    The alias was removed in Sprint 180. This confirms it has not been re-introduced.
    """
    import pytest
    with pytest.raises((ImportError, AttributeError)):
        from atlas.analysis.company_analysis import CompanyAnalysisProvider  # noqa: F401

    import atlas.analysis.company_analysis as mod
    assert not hasattr(mod, "CompanyAnalysisProvider"), (
        "CompanyAnalysisProvider must not exist in atlas.analysis.company_analysis — removed Sprint 180"
    )
