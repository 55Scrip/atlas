"""Sprint 176 guardrail tests for atlas/capabilities/ package inventory.

Verifies:
- All capability subpackages importable
- All capability engines/key symbols importable
- No capability imports deleted atlas.reasoning
- No capability imports deleted atlas.analysis.* modules
- No capability performs direct provider/network access
- portfolio_intelligence subtrack remains closed (already covered by Sprint 170 tests)
- discovery and watchlist_intelligence cross-capability imports are stable
"""

import importlib
import importlib.util


# ── Subpackage importability ──────────────────────────────────────────────────

def test_capabilities_package_importable():
    import atlas.capabilities  # noqa: F401


def test_company_analysis_capability_importable():
    from atlas.capabilities.company_analysis import (  # noqa: F401
        CompanyAnalysisEngine,
        CompanyAnalysisInput,
        CompanyAnalysisReport,
        CompanyAnalysisConfidence,
        CompanyAnalysisSection,
        CompanyAnalysisObservation,
        CompanyAnalysisRisk,
        CompanyAnalysisUnknown,
        CompanyAnalysisEvidenceLink,
    )


def test_daily_brief_capability_importable():
    from atlas.capabilities.daily_brief import (  # noqa: F401
        DailyBriefCapability,
        build_daily_brief_input,
        DailyBriefInput,
        DailyBriefReport,
        DailyBriefSection,
        DailyBriefItem,
        DailyBriefPriority,
        DailyBriefSummary,
        DailyBriefObservation,
        DailyBriefUnknown,
        DailyBriefEvidenceLink,
    )


def test_discovery_capability_importable():
    from atlas.capabilities.discovery import (  # noqa: F401
        DiscoveryEngine,
        DiscoveryInput,
        DiscoveryReport,
        DiscoveryCandidate,
        DiscoveryPriority,
        DiscoveryReason,
        DiscoverySignal,
        DiscoveryUnknown,
        DiscoveryQuestion,
        DiscoveryContext,
        DiscoveryEvidenceLink,
    )


def test_watchlist_intelligence_capability_importable():
    from atlas.capabilities.watchlist_intelligence import (  # noqa: F401
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
        WatchlistEvidenceLink,
    )


def test_portfolio_intelligence_subtrack_still_closed():
    """Sprint 176: portfolio_intelligence subtrack remains closed and importable."""
    from atlas.capabilities.portfolio_intelligence import (  # noqa: F401
        PortfolioFitDimension,
        PortfolioFitInput,
        PortfolioFitResult,
        PortfolioIntelligenceCapability,
    )


# ── Stale import guardrails ───────────────────────────────────────────────────

def test_capabilities_do_not_import_deleted_reasoning():
    """No capability module imports deleted atlas.reasoning."""
    import ast
    import pathlib

    cap_dir = pathlib.Path("atlas/capabilities")
    for py_file in cap_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = ""
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name
                elif isinstance(node, ast.ImportFrom) and node.module:
                    module = node.module
                assert not module.startswith("atlas.reasoning"), (
                    f"{py_file} imports deleted atlas.reasoning: {module}"
                )


def test_capabilities_do_not_import_deleted_analysis_modules():
    """No capability module imports deleted atlas.analysis.* submodules."""
    import ast
    import pathlib

    # These specific analysis submodules were deleted in prior cleanup tracks
    deleted_analysis = {
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

    cap_dir = pathlib.Path("atlas/capabilities")
    for py_file in cap_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module not in deleted_analysis, (
                    f"{py_file} imports deleted module: {node.module}"
                )


# ── Provider boundary ─────────────────────────────────────────────────────────

def test_capabilities_do_not_import_providers_directly():
    """No capability module imports atlas.providers directly."""
    import ast
    import pathlib

    cap_dir = pathlib.Path("atlas/capabilities")
    for py_file in cap_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("atlas.providers"), (
                    f"{py_file} imports providers directly: {node.module}"
                )


def test_capabilities_do_not_import_requests_or_urlopen():
    """No capability module imports requests or urllib.request for network access."""
    import ast
    import pathlib

    cap_dir = pathlib.Path("atlas/capabilities")
    for py_file in cap_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in ("requests", "urllib.request"), (
                        f"{py_file} imports network module: {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert node.module not in ("requests", "urllib.request"), (
                    f"{py_file} imports network module: {node.module}"
                )


# ── Cross-capability dependency stability ─────────────────────────────────────

def test_discovery_engine_imports_company_analysis_and_watchlist_intelligence():
    """DiscoveryEngine has stable cross-capability deps on company_analysis and watchlist_intelligence."""
    from atlas.capabilities.company_analysis import CompanyAnalysisReport  # noqa: F401
    from atlas.capabilities.watchlist_intelligence import WatchlistIntelligenceReport  # noqa: F401
    from atlas.capabilities.discovery import DiscoveryEngine  # noqa: F401


def test_capabilities_top_level_all():
    """atlas/capabilities/__init__.py.__all__ lists 4 subpackage names."""
    import atlas.capabilities as pkg
    assert hasattr(pkg, "__all__"), "atlas.capabilities must define __all__"
    expected = {"company_analysis", "daily_brief", "discovery", "watchlist_intelligence"}
    actual = set(pkg.__all__)
    assert actual == expected, (
        f"atlas.capabilities.__all__ mismatch. Expected {expected}, got {actual}"
    )
