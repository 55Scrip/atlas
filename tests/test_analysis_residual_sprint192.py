"""Sprint 192: Residual analysis surface audit guardrails.

atlas/analysis/ is a legacy residual runtime layer preserved by Sprint 141.
It is NOT the same as the Sprint 141 main analysis cleanup track, which is closed.

Surviving modules (5 .py files, 652 lines total):
  atlas/analysis/__init__.py         (26 lines) — re-exports 12 public symbols
  atlas/analysis/company_analysis.py (159 lines) — CompanyAnalysis, placeholder analyses
  atlas/analysis/engine.py           (229 lines) — AtlasInvestmentEngine, InvestmentReport, scorers
  atlas/analysis/explanation.py      (198 lines) — InvestmentExplanation, explain/render
  atlas/analysis/report.py            (38 lines) — build_investment_report, render_investment_report
  atlas/analysis/scores.py             (2 lines) — clamp_score (shared utility, not in __all__)

All 12 __all__ exports are active. No stale exports. No dead modules.

These tests confirm:
  - all 12 __all__ exports are importable
  - deleted Sprint 141 analysis modules remain absent
  - residual analysis does not import from deleted analysis modules
  - residual analysis does not import from atlas.capabilities.company_analysis
  - atlas.capabilities.company_analysis does not import from atlas.analysis
  - clamp_score remains importable (active shared utility)
  - provider re-exports in __init__.py remain importable
  - MockCompanyAnalysisProvider __getattr__ shim is live (4 test callers)
  - CompanyAnalysisProvider remains absent from active namespace
  - atlas.domains does not import from atlas.analysis
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_DIR = REPO_ROOT / "atlas" / "analysis"
CAPABILITY_CA_DIR = REPO_ROOT / "atlas" / "capabilities" / "company_analysis"
DOMAINS_DIR = REPO_ROOT / "atlas" / "domains"


# ── Export completeness ───────────────────────────────────────────────────────

def test_analysis_residual_all_exports_importable() -> None:
    """All 12 atlas.analysis __all__ exports are importable."""
    from atlas.analysis import (  # noqa: F401
        AtlasInvestmentEngine,
        CompanyAnalysis,
        CompanyDataProvider,
        InvestmentExplanation,
        InvestmentReport,
        MockCompanyAnalysisProvider,
        ScoreCategory,
        YahooFinanceProvider,
        build_investment_report,
        create_placeholder_company_analysis,
        explain_investment_report,
        render_investment_report,
    )


def test_analysis_residual_all_has_exactly_12_exports() -> None:
    """__all__ has exactly 12 exports — no silent additions or removals."""
    import atlas.analysis as pkg

    assert len(pkg.__all__) == 12, pkg.__all__


def test_clamp_score_importable_from_scores() -> None:
    """clamp_score is importable from atlas.analysis.scores (active shared utility)."""
    from atlas.analysis.scores import clamp_score  # noqa: F401

    assert callable(clamp_score)


# ── Deleted Sprint 141 analysis modules remain absent ────────────────────────

_DELETED_MODULES = [
    "atlas/analysis/portfolio.py",
    "atlas/analysis/growth.py",
    "atlas/analysis/macro.py",
    "atlas/analysis/moat.py",
    "atlas/analysis/quality.py",
    "atlas/analysis/sentiment.py",
    "atlas/analysis/technicals.py",
    "atlas/analysis/valuation.py",
]


def test_deleted_analysis_modules_remain_absent() -> None:
    """All Sprint 141 deleted analysis modules remain absent."""
    for rel_path in _DELETED_MODULES:
        full = REPO_ROOT / rel_path
        assert not full.exists(), f"{rel_path} was re-created — must remain absent"


# ── Stale import guard — residual analysis surface ───────────────────────────

def _source_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(a.name for a in node.names)
    return modules


_DELETED_ANALYSIS_SUBMODULES = {
    "atlas.analysis.portfolio",
    "atlas.analysis.growth",
    "atlas.analysis.macro",
    "atlas.analysis.moat",
    "atlas.analysis.quality",
    "atlas.analysis.sentiment",
    "atlas.analysis.technicals",
    "atlas.analysis.valuation",
    "atlas.analysis.comparison",
    "atlas.analysis.memory",
    "atlas.analysis.scoring",
    "atlas.analysis.watchlist",
    "atlas.reasoning",
}


def test_residual_analysis_does_not_import_deleted_submodules() -> None:
    """No surviving atlas/analysis/ module imports from deleted analysis submodules."""
    for path in ANALYSIS_DIR.glob("*.py"):
        imports = _source_imports(path)
        stale = [m for m in imports if m in _DELETED_ANALYSIS_SUBMODULES]
        assert not stale, f"{path.name} imports deleted module: {stale}"


# ── Capability boundary — bidirectional separation ───────────────────────────

def test_residual_analysis_does_not_import_company_analysis_capability() -> None:
    """atlas/analysis/ does not import from atlas.capabilities.company_analysis.

    The two layers are separate: legacy residual (InvestmentReport) vs
    Blueprint capability (CompanyAnalysisReport). No cross-imports.
    """
    for path in ANALYSIS_DIR.glob("*.py"):
        imports = _source_imports(path)
        cap_imports = [m for m in imports if m.startswith("atlas.capabilities.company_analysis")]
        assert not cap_imports, (
            f"{path.name} imports atlas.capabilities.company_analysis: {cap_imports}"
        )


def test_company_analysis_capability_does_not_import_residual_analysis() -> None:
    """atlas/capabilities/company_analysis/ does not import from atlas.analysis.

    Boundary verified in Sprint 182. Confirmed stable Sprint 192.
    """
    for path in CAPABILITY_CA_DIR.glob("*.py"):
        imports = _source_imports(path)
        analysis_imports = [m for m in imports if m.startswith("atlas.analysis")]
        assert not analysis_imports, (
            f"capability/{path.name} imports atlas.analysis: {analysis_imports}"
        )


# ── Domains boundary — domains must not import legacy analysis ────────────────

def test_domains_do_not_import_residual_analysis() -> None:
    """atlas/domains/ must not import from atlas.analysis (legacy layer).

    Domains are the canonical Blueprint layer — they must not depend on legacy runtime.
    """
    for path in DOMAINS_DIR.rglob("*.py"):
        imports = _source_imports(path)
        analysis_imports = [m for m in imports if m.startswith("atlas.analysis")]
        assert not analysis_imports, (
            f"domains/{path.relative_to(DOMAINS_DIR)} imports atlas.analysis: {analysis_imports}"
        )


# ── CompanyAnalysisProvider remains absent from active namespace ──────────────

def test_company_analysis_provider_remains_absent() -> None:
    """CompanyAnalysisProvider must not be a public attribute of atlas.analysis.company_analysis.

    Removed Sprint 180. __getattr__ shim may reference the name but must not expose it.
    """
    import atlas.analysis.company_analysis as mod

    assert not hasattr(mod, "CompanyAnalysisProvider"), (
        "CompanyAnalysisProvider must not exist in atlas.analysis.company_analysis — removed Sprint 180"
    )


# ── __getattr__ shim for MockCompanyAnalysisProvider is live ─────────────────

def test_mock_company_analysis_provider_importable_via_company_analysis_shim() -> None:
    """MockCompanyAnalysisProvider is importable from atlas.analysis.company_analysis via __getattr__.

    4 test files use this import path. The shim must remain live.
    """
    from atlas.analysis.company_analysis import MockCompanyAnalysisProvider  # noqa: F401

    assert MockCompanyAnalysisProvider is not None
