"""Sprint 140: Analysis package release-candidate checkpoint guardrails.

Verifies:
- atlas/analysis/ contains exactly the 6 expected modules (no extras, none missing)
- atlas.analysis.__all__ contains exactly the 12 expected exports
- all previously deleted modules remain not importable
- all deleted legacy portfolio symbols are absent from the adapters namespace
- clamp_score is importable from atlas.analysis.scores
- explanation.py and report.py public symbols are importable
"""

import importlib


# ── Module inventory ──────────────────────────────────────────────────────────

def test_sprint140_analysis_package_six_modules_only() -> None:
    """Sprint 140: atlas/analysis/ must contain exactly 6 modules after Sprint 139."""
    from pathlib import Path
    import atlas.analysis as _pkg

    pkg_dir = Path(_pkg.__file__).parent
    py_files = {
        f.stem
        for f in pkg_dir.glob("*.py")
        if f.name != "__init__.py" and not f.name.startswith("_")
    }
    expected = {"company_analysis", "engine", "explanation", "report", "scores"}
    assert py_files == expected, (
        f"atlas/analysis/ module set mismatch. "
        f"Extra: {py_files - expected}. Missing: {expected - py_files}."
    )


def test_sprint140_explanation_module_importable() -> None:
    """Sprint 140: atlas.analysis.explanation must be importable."""
    from atlas.analysis.explanation import (  # noqa: F401
        InvestmentExplanation,
        explain_investment_report,
        render_investment_explanation,
    )


def test_sprint140_report_module_importable() -> None:
    """Sprint 140: atlas.analysis.report must be importable."""
    from atlas.analysis.report import (  # noqa: F401
        build_investment_report,
        render_investment_report,
    )


def test_sprint140_scores_module_importable() -> None:
    """Sprint 140: atlas.analysis.scores must be importable with clamp_score."""
    from atlas.analysis.scores import clamp_score  # noqa: F401
    assert clamp_score(150) == 100
    assert clamp_score(-5) == 0
    assert clamp_score(72) == 72


# ── Export health ─────────────────────────────────────────────────────────────

def test_sprint140_atlas_analysis_all_has_exactly_9_exports() -> None:
    """Sprint 193: atlas.analysis.__all__ must have exactly the 9 active exports.

    Sprint 140 established 12 exports. Sprint 193 removed 3 zero-caller provider
    re-exports (CompanyDataProvider, MockCompanyAnalysisProvider, YahooFinanceProvider)
    — no callers imported them from atlas.analysis root. Use atlas.providers directly.
    """
    import atlas.analysis as pkg

    expected = {
        "AtlasInvestmentEngine",
        "CompanyAnalysis",
        "InvestmentReport",
        "InvestmentExplanation",
        "ScoreCategory",
        "build_investment_report",
        "create_placeholder_company_analysis",
        "explain_investment_report",
        "render_investment_report",
    }
    actual = set(pkg.__all__)
    assert actual == expected, (
        f"atlas.analysis.__all__ mismatch. "
        f"Extra: {actual - expected}. Missing: {expected - actual}."
    )


def test_sprint140_all_exports_are_importable() -> None:
    """Sprint 140: every symbol in atlas.analysis.__all__ must be importable."""
    import atlas.analysis as pkg

    for name in pkg.__all__:
        assert hasattr(pkg, name), f"atlas.analysis.{name} listed in __all__ but not importable"


# ── Deleted module verification ───────────────────────────────────────────────

def test_sprint140_deleted_modules_not_importable() -> None:
    """Sprint 140: all historically deleted atlas.analysis modules must remain gone."""
    deleted = [
        "atlas.analysis.watchlist",
        "atlas.analysis.comparison",
        "atlas.analysis.memory",
        "atlas.analysis.scoring",
        "atlas.analysis.portfolio",
        "atlas.analysis.growth",
        "atlas.analysis.macro",
        "atlas.analysis.moat",
        "atlas.analysis.quality",
        "atlas.analysis.sentiment",
        "atlas.analysis.technicals",
        "atlas.analysis.valuation",
        "atlas.analysis.investment",
    ]
    for mod in deleted:
        try:
            importlib.import_module(mod)
            assert False, f"{mod} must not be importable — it was deleted"
        except ModuleNotFoundError:
            pass


# ── Deleted legacy portfolio symbols ─────────────────────────────────────────

def test_sprint140_deleted_portfolio_symbols_absent() -> None:
    """Sprint 140: deleted legacy portfolio types must not exist anywhere reachable."""
    import atlas.adapters.portfolio as ap

    deleted_symbols = [
        "PortfolioIntelligenceEngine",
        "PortfolioAnalysis",
        "PortfolioSignal",
        "PortfolioRecommendation",
        "CompanyPortfolioProfile",
    ]
    for sym in deleted_symbols:
        assert not hasattr(ap, sym), (
            f"{sym} must not be present in atlas.adapters.portfolio — it was deleted"
        )


def test_sprint140_portfolio_analysis_module_deleted() -> None:
    """Sprint 140: atlas.analysis.portfolio must not exist."""
    try:
        importlib.import_module("atlas.analysis.portfolio")
        assert False, "atlas.analysis.portfolio must not be importable after Sprint 135"
    except ModuleNotFoundError:
        pass
