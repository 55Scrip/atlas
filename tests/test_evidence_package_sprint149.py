"""Sprint 149: Evidence package audit checkpoint guardrails.

Verifies:
- atlas/evidence/ contains exactly the 2 expected modules
- atlas.evidence.__all__ exports exactly the 9 expected symbols
- All 9 exports are importable
- EvidenceQualityEngine is importable and functional
- atlas/evidence/ has no provider imports
- atlas/evidence/ has no imports from deleted analysis modules
- Three known production callers still import expected evidence symbols
- Closed cleanup tracks remain closed
"""

import ast
import importlib
from pathlib import Path


# ── Package inventory ─────────────────────────────────────────────────────────

def test_sprint149_evidence_package_two_modules_only() -> None:
    """Sprint 149: atlas/evidence/ must contain exactly 2 modules (init + engine)."""
    import atlas.evidence as _pkg

    pkg_dir = Path(_pkg.__file__).parent
    py_files = {
        f.stem
        for f in pkg_dir.glob("*.py")
        if f.name != "__init__.py" and not f.name.startswith("_")
    }
    expected = {"engine"}
    assert py_files == expected, (
        f"atlas/evidence/ module set mismatch. "
        f"Extra: {py_files - expected}. Missing: {expected - py_files}."
    )


# ── Export health ─────────────────────────────────────────────────────────────

def test_sprint149_evidence_all_has_nine_exports() -> None:
    """Sprint 149: atlas.evidence.__all__ must contain exactly 9 exports."""
    import atlas.evidence as pkg

    expected = {
        "EvidenceAction",
        "EvidenceAssessment",
        "EvidenceClaim",
        "EvidenceInput",
        "EvidenceQualityEngine",
        "EvidenceRationale",
        "EvidenceSource",
        "EvidenceStrength",
        "render_evidence_assessment",
    }
    actual = set(pkg.__all__)
    assert actual == expected, (
        f"atlas.evidence.__all__ mismatch. Extra: {actual - expected}. Missing: {expected - actual}."
    )


def test_sprint149_all_exports_importable() -> None:
    """Sprint 149: every symbol in atlas.evidence.__all__ must be importable."""
    import atlas.evidence as pkg

    for name in pkg.__all__:
        assert hasattr(pkg, name), f"atlas.evidence.{name} in __all__ but not importable"


# ── Engine contract ───────────────────────────────────────────────────────────

def test_sprint149_evidence_quality_engine_assess_is_functional() -> None:
    """Sprint 149: EvidenceQualityEngine.assess must return an EvidenceAssessment."""
    from atlas.evidence import (
        EvidenceAssessment,
        EvidenceClaim,
        EvidenceInput,
        EvidenceQualityEngine,
        EvidenceSource,
    )

    engine = EvidenceQualityEngine()
    result = engine.assess(
        EvidenceInput(
            claim=EvidenceClaim("Revenue disclosed in audited annual report."),
            source=EvidenceSource.AUDITED_ANNUAL_REPORT,
        )
    )
    assert isinstance(result, EvidenceAssessment)
    assert result.confidence_impact != 0


# ── Boundary: no provider imports ─────────────────────────────────────────────

def test_sprint149_evidence_has_no_provider_imports() -> None:
    """Sprint 149: atlas/evidence/ must not import from atlas.providers."""
    evidence_dir = Path("atlas/evidence")
    for py_file in evidence_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("atlas.providers"), (
                    f"{py_file}: must not import from atlas.providers"
                )


def test_sprint149_evidence_has_no_deleted_analysis_imports() -> None:
    """Sprint 149: atlas/evidence/ must not import from deleted atlas.analysis submodules."""
    deleted_mods = {
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
    evidence_dir = Path("atlas/evidence")
    for py_file in evidence_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in deleted_mods:
                assert False, f"{py_file}: stale import from deleted module {node.module}"


# ── Known production callers still import expected symbols ────────────────────

def test_sprint149_comparison_engine_imports_evidence() -> None:
    """Sprint 149: atlas/comparison/engine.py must import EvidenceQualityEngine from atlas.evidence."""
    source = Path("atlas/comparison/engine.py").read_text(encoding="utf-8")
    assert "from atlas.evidence import" in source
    assert "EvidenceQualityEngine" in source


def test_sprint149_decision_journal_imports_evidence() -> None:
    """Sprint 149: atlas/decision_journal/engine.py must import EvidenceQualityEngine from atlas.evidence."""
    source = Path("atlas/decision_journal/engine.py").read_text(encoding="utf-8")
    assert "from atlas.evidence import" in source
    assert "EvidenceQualityEngine" in source


def test_sprint149_watchlist_review_imports_evidence() -> None:
    """Sprint 149: atlas/watchlist_review/engine.py must import EvidenceQualityEngine from atlas.evidence."""
    source = Path("atlas/watchlist_review/engine.py").read_text(encoding="utf-8")
    assert "from atlas.evidence import" in source
    assert "EvidenceQualityEngine" in source


# ── Closed cleanup track guardrails ───────────────────────────────────────────

def test_sprint149_analysis_cleanup_track_closed() -> None:
    """Sprint 149: deleted atlas.analysis modules must remain not importable."""
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


def test_sprint149_provider_cleanup_track_closed() -> None:
    """Sprint 149: stale Yahoo exports removed Sprint 146 must remain absent."""
    import atlas.providers as pkg
    for sym in ("YahooCompany", "YahooFinancials", "YahooMarketData"):
        assert sym not in pkg.__all__, (
            f"{sym} must not be in atlas.providers.__all__ after Sprint 146"
        )


def test_sprint149_portfolio_boundary_closed() -> None:
    """Sprint 149: Portfolio and PortfolioPosition remain in adapter; analysis.portfolio gone."""
    from atlas.adapters.portfolio import Portfolio, PortfolioPosition  # noqa: F401
    assert Portfolio is not None
    assert PortfolioPosition is not None
    try:
        importlib.import_module("atlas.analysis.portfolio")
        assert False, "atlas.analysis.portfolio must not be importable after Sprint 135"
    except ModuleNotFoundError:
        pass
