"""Sprint 153: atlas/reasoning/ package deleted.

Sprint 82 deprecated atlas reason analyze; Sprint 87 retired the command body.
Sprint 152 removed check_reasoning_report() from atlas/principles/engine.py.
Sprint 153 deleted the atlas/reasoning/ package entirely.

These guardrails confirm:
- atlas.reasoning is no longer importable
- atlas/reasoning/ directory does not exist
- CLI command atlas reason analyze remains retired
- Closed migration guardrails from Sprint 118 and 131 remain valid
  (portfolio adapter still active, capability engine still clean)
"""

from __future__ import annotations

import importlib
from pathlib import Path

from typer.testing import CliRunner

from atlas.cli.main import app

runner = CliRunner()


# ── Package deletion confirmed ─────────────────────────────────────────────────

def test_sprint153_atlas_reasoning_not_importable() -> None:
    """Sprint 153: atlas.reasoning must not be importable — package deleted."""
    try:
        importlib.import_module("atlas.reasoning")
        assert False, "atlas.reasoning must not be importable after Sprint 153 deletion"
    except ModuleNotFoundError:
        pass


def test_sprint153_reasoning_directory_does_not_exist() -> None:
    """Sprint 153: atlas/reasoning/ directory must not exist."""
    assert not Path("atlas/reasoning").exists(), (
        "atlas/reasoning/ must not exist after Sprint 153 deletion"
    )


# ── CLI command remains retired ────────────────────────────────────────────────

def test_reasoning_cli_command_is_retired() -> None:
    """atlas reason analyze must not be a recognized subcommand."""
    result = runner.invoke(app, ["reason", "analyze"])
    assert result.exit_code != 0


# ── Sprint 118/131 migration guardrails (adapted for deletion) ─────────────────

def test_sprint118_capability_engine_still_no_legacy_portfolio_import() -> None:
    """Sprint 118: portfolio_intelligence capability engine must not import atlas.analysis.portfolio."""
    source = Path("atlas/capabilities/portfolio_intelligence/engine.py").read_text(encoding="utf-8")
    assert "atlas.analysis.portfolio" not in source


def test_sprint118_legacy_portfolio_module_remains_active() -> None:
    """Sprint 118: Portfolio and PortfolioPosition remain in atlas.adapters.portfolio."""
    from atlas.adapters.portfolio import Portfolio, PortfolioPosition  # noqa: F401
    assert Portfolio is not None
    assert PortfolioPosition is not None


def test_sprint132_portfolio_analysis_signal_recommendation_deleted() -> None:
    """Sprint 132: PortfolioAnalysis, PortfolioSignal, PortfolioRecommendation deleted."""
    import pytest
    with pytest.raises(ImportError):
        from atlas.adapters.portfolio import PortfolioAnalysis  # noqa: F401
    with pytest.raises(ImportError):
        from atlas.adapters.portfolio import PortfolioSignal  # noqa: F401
    with pytest.raises(ImportError):
        from atlas.adapters.portfolio import PortfolioRecommendation  # noqa: F401
