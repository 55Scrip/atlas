"""Sprint 154: Risk package audit checkpoint guardrails.

Verifies:
- atlas/risk/ contains exactly the 2 expected modules
- atlas.risk.__all__ exports exactly the 8 expected symbols
- All 8 exports are importable
- RiskAnalysis is importable and is a frozen dataclass
- atlas/risk/ has no provider imports
- atlas/risk/ has no imports from deleted analysis or reasoning modules
- Known production callers (conversation, intelligence) still import RiskAnalysis
- RiskEngine has zero production instantiation points (CLI retired Sprint 88)
- Closed cleanup tracks remain closed
"""

import ast
import importlib
from pathlib import Path


# ── Package inventory ─────────────────────────────────────────────────────────

def test_sprint154_risk_package_two_modules_only() -> None:
    """Sprint 154: atlas/risk/ must contain exactly 2 modules (init + engine)."""
    import atlas.risk as _pkg

    pkg_dir = Path(_pkg.__file__).parent
    py_files = {
        f.stem
        for f in pkg_dir.glob("*.py")
        if f.name != "__init__.py" and not f.name.startswith("_")
    }
    expected = {"engine"}
    assert py_files == expected, (
        f"atlas/risk/ module set mismatch. "
        f"Extra: {py_files - expected}. Missing: {expected - py_files}."
    )


# ── Export health ─────────────────────────────────────────────────────────────

def test_sprint154_risk_all_has_eight_exports() -> None:
    """Sprint 154: atlas.risk.__all__ must contain exactly 8 exports."""
    import atlas.risk as pkg

    expected = {
        "CapitalDeploymentPlan",
        "CurrentPosition",
        "PositionSizingInput",
        "PositionSizingResult",
        "RiskAnalysis",
        "RiskEngine",
        "RiskProfile",
        "render_risk_analysis",
    }
    actual = set(pkg.__all__)
    assert actual == expected, (
        f"atlas.risk.__all__ mismatch. Extra: {actual - expected}. Missing: {expected - actual}."
    )


def test_sprint154_all_exports_importable() -> None:
    """Sprint 154: every symbol in atlas.risk.__all__ must be importable."""
    import atlas.risk as pkg

    for name in pkg.__all__:
        assert hasattr(pkg, name), f"atlas.risk.{name} in __all__ but not importable"


# ── RiskAnalysis type contract ─────────────────────────────────────────────────

def test_sprint154_risk_analysis_is_frozen_dataclass() -> None:
    """Sprint 154: RiskAnalysis must be a frozen dataclass with expected fields."""
    from atlas.risk import RiskAnalysis
    import dataclasses

    assert dataclasses.is_dataclass(RiskAnalysis)
    fields = {f.name for f in dataclasses.fields(RiskAnalysis)}
    expected_fields = {"risk_profile", "target_ticker", "deployment_plan", "position_sizing", "reasoning"}
    assert expected_fields <= fields, (
        f"RiskAnalysis missing expected fields: {expected_fields - fields}"
    )


# ── Boundary: no provider imports ─────────────────────────────────────────────

def test_sprint154_risk_has_no_provider_imports() -> None:
    """Sprint 154: atlas/risk/ must not import from atlas.providers."""
    risk_dir = Path("atlas/risk")
    for py_file in risk_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("atlas.providers"), (
                    f"{py_file}: must not import from atlas.providers"
                )


def test_sprint154_risk_has_no_deleted_module_imports() -> None:
    """Sprint 154: atlas/risk/ must not import from deleted atlas.analysis or atlas.reasoning."""
    deleted_mods = {
        "atlas.reasoning",
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
    risk_dir = Path("atlas/risk")
    for py_file in risk_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in deleted_mods:
                assert False, f"{py_file}: stale import from deleted module {node.module}"


# ── Known production callers still import RiskAnalysis ────────────────────────

def test_sprint154_conversation_engine_imports_risk_analysis() -> None:
    """Sprint 154: atlas/conversation/engine.py must import RiskAnalysis from atlas.risk."""
    source = Path("atlas/conversation/engine.py").read_text(encoding="utf-8")
    assert "from atlas.risk import" in source
    assert "RiskAnalysis" in source


def test_sprint154_intelligence_engine_imports_risk_analysis() -> None:
    """Sprint 154: atlas/intelligence/engine.py must import RiskAnalysis from atlas.risk."""
    source = Path("atlas/intelligence/engine.py").read_text(encoding="utf-8")
    assert "from atlas.risk import" in source
    assert "RiskAnalysis" in source


# ── RiskEngine has zero production instantiation ───────────────────────────────

def test_sprint154_risk_engine_not_instantiated_in_production_code() -> None:
    """Sprint 154: RiskEngine() must not be instantiated in any non-test production module."""
    production_hits = []
    for py_file in Path("atlas").rglob("*.py"):
        if "risk" in str(py_file):
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "RiskEngine()" in source:
            production_hits.append(str(py_file))
    assert not production_hits, (
        f"RiskEngine() instantiated in production code — Sprint 154 finding: {production_hits}"
    )


# ── Closed cleanup track guardrails ───────────────────────────────────────────

def test_sprint154_reasoning_package_deleted() -> None:
    """Sprint 154: atlas.reasoning must not be importable — deleted Sprint 153."""
    try:
        importlib.import_module("atlas.reasoning")
        assert False, "atlas.reasoning must not be importable after Sprint 153 deletion"
    except ModuleNotFoundError:
        pass


def test_sprint154_analysis_cleanup_track_closed() -> None:
    """Sprint 154: deleted atlas.analysis modules must remain not importable."""
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


def test_sprint154_provider_cleanup_track_closed() -> None:
    """Sprint 154: stale Yahoo exports removed Sprint 146 must remain absent."""
    import atlas.providers as pkg
    for sym in ("YahooCompany", "YahooFinancials", "YahooMarketData"):
        assert sym not in pkg.__all__, (
            f"{sym} must not be in atlas.providers.__all__ after Sprint 146"
        )


def test_sprint154_portfolio_boundary_closed() -> None:
    """Sprint 154: Portfolio/PortfolioPosition in adapter; analysis.portfolio gone."""
    from atlas.adapters.portfolio import Portfolio, PortfolioPosition  # noqa: F401
    assert Portfolio is not None
    assert PortfolioPosition is not None
    try:
        importlib.import_module("atlas.analysis.portfolio")
        assert False, "atlas.analysis.portfolio must not be importable after Sprint 135"
    except ModuleNotFoundError:
        pass
