"""Sprint 179 guardrail tests for the legacy atlas/analysis/ package (company analysis surface).

Note: atlas/company_analysis/ does not exist as a standalone package.
The company analysis surface spans:
  - atlas/analysis/ (legacy scoring/investment-report layer, 5 active modules)
  - atlas/capabilities/company_analysis/ (Blueprint capability layer, 4 modules)

These tests guard the boundaries between these two layers and verify that
the Sprint 141 cleanup track remains closed (deleted modules still absent).
"""

import ast
import pathlib


# ── Legacy analysis layer — active modules importable ─────────────────────────

def test_analysis_company_analysis_module_importable():
    """Sprint 179: atlas.analysis.company_analysis module must be importable."""
    from atlas.analysis.company_analysis import (  # noqa: F401
        CompanyAnalysis,
        create_placeholder_company_analysis,
        GrowthAnalysis,
        MacroAnalysis,
        MoatAnalysis,
        QualityAnalysis,
        SentimentAnalysis,
        TechnicalAnalysis,
        ValuationAnalysis,
    )
    assert callable(create_placeholder_company_analysis)


def test_analysis_engine_module_importable():
    """Sprint 179: atlas.analysis.engine public symbols must be importable."""
    from atlas.analysis.engine import (  # noqa: F401
        AtlasInvestmentEngine,
        InvestmentReport,
        ScoreCategory,
        ThresholdRecommendationPolicy,
    )
    assert callable(AtlasInvestmentEngine)


def test_analysis_report_module_importable():
    """Sprint 179: atlas.analysis.report public symbols must be importable."""
    from atlas.analysis.report import (  # noqa: F401
        build_investment_report,
        render_investment_report,
    )
    assert callable(build_investment_report)
    assert callable(render_investment_report)


def test_analysis_explanation_module_importable():
    """Sprint 179: atlas.analysis.explanation public symbols must be importable."""
    from atlas.analysis.explanation import (  # noqa: F401
        InvestmentExplanation,
        explain_investment_report,
        render_investment_explanation,
    )
    assert callable(explain_investment_report)


def test_analysis_scores_module_importable():
    """Sprint 179: atlas.analysis.scores.clamp_score must be importable (active utility)."""
    from atlas.analysis.scores import clamp_score  # noqa: F401
    assert clamp_score(150) == 100
    assert clamp_score(-5) == 0
    assert clamp_score(72) == 72


# ── Capability layer — clean of legacy analysis imports ───────────────────────

def test_capability_company_analysis_does_not_import_atlas_analysis():
    """Sprint 179: atlas/capabilities/company_analysis/ must not import from atlas.analysis.

    The capability layer is Blueprint-aligned; it must not depend on the legacy analysis layer.
    """
    cap_dir = pathlib.Path("atlas/capabilities/company_analysis")
    for py_file in cap_dir.glob("*.py"):
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("atlas.analysis"), (
                    f"{py_file} imports from atlas.analysis — capability must not depend on "
                    f"legacy analysis layer: {node.module}"
                )


# ── Sprint 141 cleanup track — deleted modules remain absent ─────────────────

def test_sprint141_deleted_analysis_modules_remain_absent():
    """Sprint 179: 12 modules deleted in Sprint 141 must remain unimportable."""
    import importlib
    import pytest

    deleted = [
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
    ]
    for module_name in deleted:
        with pytest.raises(ImportError):
            importlib.import_module(module_name)


# ── Legacy analysis layer — no stale imports from deleted modules ─────────────

def test_analysis_does_not_import_deleted_analysis_submodules():
    """Sprint 179: active atlas/analysis/ modules must not import deleted submodules."""
    deleted = {
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
    analysis_dir = pathlib.Path("atlas/analysis")
    for py_file in analysis_dir.glob("*.py"):
        source = py_file.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module not in deleted, (
                    f"{py_file} imports deleted module: {node.module}"
                )


def test_analysis_does_not_import_deleted_reasoning():
    """Sprint 179: atlas/analysis/ must not import deleted atlas.reasoning."""
    analysis_dir = pathlib.Path("atlas/analysis")
    for py_file in analysis_dir.glob("*.py"):
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


# ── CompanyAnalysisProvider alias — stale, zero external callers ──────────────

def test_company_analysis_provider_alias_is_not_in_analysis_all():
    """Sprint 179: CompanyAnalysisProvider alias must not appear in atlas.analysis.__all__.

    The CompanyAnalysisProvider alias in atlas/analysis/company_analysis.py is a
    module-level import with zero external callers. It is not re-exported from
    atlas.analysis.__all__. This test guards that it was not inadvertently added.
    """
    import atlas.analysis as pkg
    assert "CompanyAnalysisProvider" not in pkg.__all__, (
        "CompanyAnalysisProvider must not be in atlas.analysis.__all__ — "
        "it is a stale alias with zero external callers"
    )


# ── atlas/analysis/ contains exactly the 5 expected active modules ────────────

def test_analysis_package_has_five_active_modules():
    """Sprint 179: atlas/analysis/ must contain exactly 5 active source modules after Sprint 141.

    Modules: company_analysis, engine, explanation, report, scores.
    """
    from pathlib import Path
    import atlas.analysis as pkg

    pkg_dir = Path(pkg.__file__).parent
    py_files = {
        f.stem
        for f in pkg_dir.glob("*.py")
        if f.name != "__init__.py" and not f.name.startswith("_")
    }
    expected = {"company_analysis", "engine", "explanation", "report", "scores"}
    assert py_files == expected, (
        f"atlas/analysis/ module set mismatch. "
        f"Expected: {sorted(expected)}. Found: {sorted(py_files)}"
    )
