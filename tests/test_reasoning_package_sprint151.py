"""Sprint 151: Reasoning package audit checkpoint guardrails.

Updated Sprint 152: check_reasoning_report() removed from atlas/principles/engine.py.
Updated Sprint 153: atlas/reasoning/ package deleted entirely.

Verifies:
- atlas/reasoning/ package is not importable (Sprint 153)
- atlas/principles/engine.py no longer references atlas.reasoning (Sprint 152)
- Closed cleanup tracks remain closed
"""

import importlib
from pathlib import Path


# ── Package deletion confirmed (Sprint 153) ───────────────────────────────────

def test_sprint153_atlas_reasoning_package_deleted() -> None:
    """Sprint 153: atlas.reasoning must not be importable."""
    try:
        importlib.import_module("atlas.reasoning")
        assert False, "atlas.reasoning must not be importable after Sprint 153 deletion"
    except ModuleNotFoundError:
        pass


# ── Sprint 152 guardrails ─────────────────────────────────────────────────────

def test_sprint152_principles_engine_no_longer_references_atlas_reasoning() -> None:
    """Sprint 152: atlas/principles/engine.py must not reference atlas.reasoning."""
    source = Path("atlas/principles/engine.py").read_text(encoding="utf-8")
    assert "atlas.reasoning" not in source, (
        "atlas/principles/engine.py must not reference atlas.reasoning after Sprint 152"
    )
    assert "check_reasoning_report" not in source, (
        "check_reasoning_report() must not exist in atlas/principles/engine.py after Sprint 152"
    )


def test_sprint152_check_reasoning_report_not_in_principles_all() -> None:
    """Sprint 152: check_reasoning_report must not be exported from atlas.principles."""
    import atlas.principles as pkg
    assert "check_reasoning_report" not in pkg.__all__, (
        "check_reasoning_report must not be in atlas.principles.__all__ after Sprint 152"
    )


# ── Closed cleanup track guardrails ───────────────────────────────────────────

def test_sprint151_analysis_cleanup_track_closed() -> None:
    """Sprint 151: deleted atlas.analysis modules must remain not importable."""
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


def test_sprint151_provider_cleanup_track_closed() -> None:
    """Sprint 151: stale Yahoo exports removed Sprint 146 must remain absent."""
    import atlas.providers as pkg
    for sym in ("YahooCompany", "YahooFinancials", "YahooMarketData"):
        assert sym not in pkg.__all__, (
            f"{sym} must not be in atlas.providers.__all__ after Sprint 146"
        )


def test_sprint151_portfolio_boundary_closed() -> None:
    """Sprint 151: Portfolio and PortfolioPosition remain in adapter; analysis.portfolio gone."""
    from atlas.adapters.portfolio import Portfolio, PortfolioPosition  # noqa: F401
    assert Portfolio is not None
    assert PortfolioPosition is not None
    try:
        importlib.import_module("atlas.analysis.portfolio")
        assert False, "atlas.analysis.portfolio must not be importable after Sprint 135"
    except ModuleNotFoundError:
        pass


def test_sprint151_adapter_does_not_import_portfolio_fit_input() -> None:
    """Sprint 151: stale PortfolioFitInput import removed Sprint 148 must remain absent."""
    source = Path("atlas/adapters/portfolio.py").read_text(encoding="utf-8")
    assert "PortfolioFitInput" not in source, (
        "atlas/adapters/portfolio.py must not import PortfolioFitInput — removed Sprint 148"
    )
