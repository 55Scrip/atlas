"""Sprint 145: Provider boundary audit checkpoint guardrails.

Verifies:
- atlas/providers/ contains exactly the 4 expected modules
- atlas.providers.__all__ has exactly the 7 expected exports (including the 3 stale ones)
- CompanyDataProvider is importable
- MockCompanyAnalysisProvider implements both contract methods
- get_portfolio_profile returns PortfolioFitInput (Sprint 133 confirmed)
- providers do not import from deleted analysis modules
- deleted analysis/decision cleanup guardrails remain intact
"""

import importlib


# ── Module inventory ──────────────────────────────────────────────────────────

def test_sprint145_provider_package_four_modules_only() -> None:
    """Sprint 145: atlas/providers/ must contain exactly 4 modules."""
    from pathlib import Path
    import atlas.providers as _pkg

    pkg_dir = Path(_pkg.__file__).parent
    py_files = {
        f.stem
        for f in pkg_dir.glob("*.py")
        if f.name != "__init__.py" and not f.name.startswith("_")
    }
    expected = {"base", "mock", "yahoo"}
    assert py_files == expected, (
        f"atlas/providers/ module set mismatch. "
        f"Extra: {py_files - expected}. Missing: {expected - py_files}."
    )


# ── Export health ─────────────────────────────────────────────────────────────

def test_sprint145_atlas_providers_all_exports() -> None:
    """Sprint 145: atlas.providers.__all__ must contain the expected symbols."""
    import atlas.providers as pkg

    # The 4 intentional active exports
    active_exports = {
        "CompanyDataProvider",
        "MockCompanyAnalysisProvider",
        "YahooFinanceProvider",
        "YahooFinanceProviderError",
    }
    # The 3 stale implementation-detail exports (Sprint 146 removal targets)
    stale_exports = {"YahooCompany", "YahooFinancials", "YahooMarketData"}

    actual = set(pkg.__all__)
    assert active_exports <= actual, (
        f"Active exports missing from atlas.providers.__all__: {active_exports - actual}"
    )
    # Document the stale ones are still present pre-Sprint-146
    for sym in stale_exports:
        assert sym in actual, f"{sym} expected in __all__ until Sprint 146 removes it"


def test_sprint145_all_exports_importable() -> None:
    """Sprint 145: every symbol in atlas.providers.__all__ must be importable."""
    import atlas.providers as pkg

    for name in pkg.__all__:
        assert hasattr(pkg, name), f"atlas.providers.{name} in __all__ but not importable"


# ── Provider contract ─────────────────────────────────────────────────────────

def test_sprint145_mock_provider_get_company_analysis() -> None:
    """Sprint 145: MockCompanyAnalysisProvider.get_company_analysis must return CompanyAnalysis."""
    from atlas.providers.mock import MockCompanyAnalysisProvider
    from atlas.analysis.company_analysis import CompanyAnalysis

    provider = MockCompanyAnalysisProvider()
    result = provider.get_company_analysis("NVDA")
    assert isinstance(result, CompanyAnalysis)


def test_sprint145_mock_provider_get_portfolio_profile_returns_portfolio_fit_input() -> None:
    """Sprint 145: get_portfolio_profile must return PortfolioFitInput (Sprint 133 confirmed)."""
    from atlas.providers.mock import MockCompanyAnalysisProvider
    from atlas.capabilities.portfolio_intelligence import PortfolioFitInput

    provider = MockCompanyAnalysisProvider()
    result = provider.get_portfolio_profile("NVDA")
    assert isinstance(result, PortfolioFitInput)
    assert result.ticker == "NVDA"


# ── No stale imports from deleted modules ────────────────────────────────────

def test_sprint145_providers_have_no_stale_analysis_imports() -> None:
    """Sprint 145: provider modules must not import from deleted atlas.analysis submodules."""
    import ast
    from pathlib import Path

    deleted_mods = {
        "atlas.analysis.portfolio",
        "atlas.analysis.comparison",
        "atlas.analysis.memory",
        "atlas.analysis.growth",
        "atlas.analysis.macro",
        "atlas.analysis.moat",
        "atlas.analysis.quality",
        "atlas.analysis.sentiment",
        "atlas.analysis.technicals",
        "atlas.analysis.valuation",
    }

    providers_dir = Path("atlas/providers")
    for py_file in providers_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.ImportFrom) and node.module:
                    assert node.module not in deleted_mods, (
                        f"{py_file}: stale import from {node.module}"
                    )


# ── Closed-track guardrails remain intact ────────────────────────────────────

def test_sprint145_deleted_analysis_modules_remain_gone() -> None:
    """Sprint 145: historically deleted atlas.analysis modules must remain not importable."""
    deleted = [
        "atlas.analysis.portfolio",
        "atlas.analysis.comparison",
        "atlas.analysis.memory",
        "atlas.analysis.growth",
        "atlas.analysis.macro",
        "atlas.analysis.moat",
        "atlas.analysis.quality",
        "atlas.analysis.sentiment",
        "atlas.analysis.technicals",
        "atlas.analysis.valuation",
    ]
    for mod in deleted:
        try:
            importlib.import_module(mod)
            assert False, f"{mod} must not be importable"
        except ModuleNotFoundError:
            pass


def test_sprint145_deleted_decision_renderer_remains_gone() -> None:
    """Sprint 145: render_comparison_result deleted Sprint 143 must remain gone."""
    try:
        from atlas.decision.comparison import render_comparison_result  # noqa: F401
        assert False, "render_comparison_result must not exist after Sprint 143"
    except ImportError:
        pass
