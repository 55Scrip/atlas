"""Sprint 189: Watchlist package audit guardrails.

The watchlist surface in Atlas is distributed across three locations:

  atlas/capabilities/watchlist_intelligence/  — Blueprint capability (13 exports)
  atlas/adapters/watchlist.py                 — JSON adapter (2 public functions, 1 private)

There is no standalone atlas/watchlist/ package. The legacy atlas/analysis/watchlist.py
was deleted Sprint 101 — types migrated to atlas.capabilities.watchlist_intelligence.

These tests confirm:
  - all 13 watchlist_intelligence exports are importable
  - adapter functions are importable
  - no stale imports from deleted modules
  - no provider coupling in capability or adapter layer
  - no CLI coupling in capability or adapter layer
  - no upward dependency on atlas.watchlist_review from the capability
  - CompanyAnalysisProvider remains absent from atlas.analysis.company_analysis
  - legacy atlas.analysis.watchlist remains deleted
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WATCHLIST_INTELLIGENCE_DIR = REPO_ROOT / "atlas" / "capabilities" / "watchlist_intelligence"
ADAPTERS_WATCHLIST = REPO_ROOT / "atlas" / "adapters" / "watchlist.py"


# ── Export completeness ───────────────────────────────────────────────────────

def test_watchlist_intelligence_all_exports_importable() -> None:
    """All 13 watchlist_intelligence __all__ exports are importable."""
    from atlas.capabilities.watchlist_intelligence import (  # noqa: F401
        WatchlistEvidenceLink,
        WatchlistIntelligenceEngine,
        WatchlistIntelligenceInput,
        WatchlistIntelligenceReport,
        WatchlistInput,
        WatchlistInputItem,
        WatchlistItem,
        WatchlistObservation,
        WatchlistPriority,
        WatchlistQuestion,
        WatchlistSignal,
        WatchlistStatus,
        WatchlistUnknown,
    )


def test_watchlist_intelligence_all_has_exactly_13_exports() -> None:
    """__all__ has exactly 13 exports — no silent additions or removals."""
    from atlas.capabilities import watchlist_intelligence

    assert len(watchlist_intelligence.__all__) == 13, watchlist_intelligence.__all__


def test_watchlist_adapter_functions_importable() -> None:
    """watchlist_input_from_dict and assign_knowledge_facts are importable from adapter."""
    from atlas.adapters.watchlist import (  # noqa: F401
        assign_knowledge_facts,
        watchlist_input_from_dict,
    )

    assert callable(watchlist_input_from_dict)
    assert callable(assign_knowledge_facts)


# ── Stale import guardrails ───────────────────────────────────────────────────

def _source_imports(path: Path) -> list[str]:
    """Return a flat list of all imported module names in a Python file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def _watchlist_intelligence_sources() -> list[Path]:
    return list(WATCHLIST_INTELLIGENCE_DIR.glob("*.py"))


def test_watchlist_intelligence_does_not_import_deleted_reasoning() -> None:
    """No watchlist_intelligence module imports deleted atlas.reasoning."""
    for path in _watchlist_intelligence_sources():
        imports = _source_imports(path)
        stale = [m for m in imports if m.startswith("atlas.reasoning")]
        assert not stale, f"{path.name} imports deleted atlas.reasoning: {stale}"


def test_watchlist_adapter_does_not_import_deleted_reasoning() -> None:
    """atlas/adapters/watchlist.py does not import deleted atlas.reasoning."""
    imports = _source_imports(ADAPTERS_WATCHLIST)
    stale = [m for m in imports if m.startswith("atlas.reasoning")]
    assert not stale, f"Stale atlas.reasoning import in adapter: {stale}"


def test_watchlist_intelligence_does_not_import_deleted_analysis_submodules() -> None:
    """No watchlist_intelligence module imports deleted atlas.analysis.* submodules."""
    _DELETED = {
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
    for path in _watchlist_intelligence_sources():
        imports = _source_imports(path)
        stale = [m for m in imports if m in _DELETED]
        assert not stale, f"{path.name} imports deleted analysis module: {stale}"


def test_watchlist_adapter_does_not_import_deleted_analysis_submodules() -> None:
    """atlas/adapters/watchlist.py does not import deleted atlas.analysis.* submodules."""
    _DELETED = {
        "atlas.analysis.portfolio",
        "atlas.analysis.watchlist",
    }
    imports = _source_imports(ADAPTERS_WATCHLIST)
    stale = [m for m in imports if m in _DELETED]
    assert not stale, f"Adapter imports deleted analysis module: {stale}"


# ── Provider boundary ─────────────────────────────────────────────────────────

def test_watchlist_intelligence_does_not_import_providers() -> None:
    """watchlist_intelligence capability does not import atlas.providers."""
    for path in _watchlist_intelligence_sources():
        imports = _source_imports(path)
        provider_imports = [m for m in imports if m.startswith("atlas.providers")]
        assert not provider_imports, f"{path.name} imports atlas.providers: {provider_imports}"


def test_watchlist_adapter_does_not_import_providers() -> None:
    """atlas/adapters/watchlist.py does not import atlas.providers."""
    imports = _source_imports(ADAPTERS_WATCHLIST)
    provider_imports = [m for m in imports if m.startswith("atlas.providers")]
    assert not provider_imports, f"Watchlist adapter imports atlas.providers: {provider_imports}"


# ── CLI boundary ──────────────────────────────────────────────────────────────

def test_watchlist_intelligence_does_not_import_cli() -> None:
    """watchlist_intelligence capability does not import atlas.cli."""
    for path in _watchlist_intelligence_sources():
        imports = _source_imports(path)
        cli_imports = [m for m in imports if m.startswith("atlas.cli")]
        assert not cli_imports, f"{path.name} imports atlas.cli: {cli_imports}"


def test_watchlist_adapter_does_not_import_cli() -> None:
    """atlas/adapters/watchlist.py does not import atlas.cli."""
    imports = _source_imports(ADAPTERS_WATCHLIST)
    cli_imports = [m for m in imports if m.startswith("atlas.cli")]
    assert not cli_imports, f"Watchlist adapter imports atlas.cli: {cli_imports}"


# ── Watchlist / watchlist_review boundary ────────────────────────────────────

def test_watchlist_intelligence_does_not_depend_on_watchlist_review() -> None:
    """watchlist_intelligence capability does not import atlas.watchlist_review.

    Boundary: watchlist_review consumes watchlist_intelligence types — not the reverse.
    """
    for path in _watchlist_intelligence_sources():
        imports = _source_imports(path)
        upward = [m for m in imports if m.startswith("atlas.watchlist_review")]
        assert not upward, f"{path.name} imports atlas.watchlist_review (upward dep): {upward}"


def test_watchlist_adapter_does_not_depend_on_watchlist_review() -> None:
    """atlas/adapters/watchlist.py does not import atlas.watchlist_review."""
    imports = _source_imports(ADAPTERS_WATCHLIST)
    upward = [m for m in imports if m.startswith("atlas.watchlist_review")]
    assert not upward, f"Watchlist adapter imports atlas.watchlist_review: {upward}"


# ── Deleted module guards ─────────────────────────────────────────────────────

def test_legacy_analysis_watchlist_module_remains_deleted() -> None:
    """atlas/analysis/watchlist.py must remain deleted (deleted Sprint 101)."""
    deleted = REPO_ROOT / "atlas" / "analysis" / "watchlist.py"
    assert not deleted.exists(), "atlas/analysis/watchlist.py was re-created — must remain deleted"


def test_company_analysis_provider_remains_absent_from_analysis_company_analysis() -> None:
    """CompanyAnalysisProvider must not be a public attribute of atlas.analysis.company_analysis.

    Removed Sprint 180. The module contains a __getattr__ shim that references the name
    for a deprecated compatibility warning — but it must not be importable as a real attribute.
    """
    import atlas.analysis.company_analysis as mod

    assert not hasattr(mod, "CompanyAnalysisProvider"), (
        "CompanyAnalysisProvider must not exist in atlas.analysis.company_analysis — removed Sprint 180"
    )
