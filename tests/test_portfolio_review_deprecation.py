"""Sprint 90: Tests confirming atlas portfolio review has been retired.

Sprint 80 deprecated the command; Sprint 90 removed the command body.
`atlas portfolio review` is no longer a registered CLI command.

The underlying `atlas.portfolio_review` engine remains on disk:
- PortfolioReviewEngine (legacy) is still imported and instantiated by
  atlas/home/engine.py (AtlasHomeEngine). Engine deletion deferred until
  AtlasHomeEngine is retired or migrated to use the Blueprint-aligned
  atlas.domains.portfolio.review.PortfolioReviewEngine.

Note: atlas/domains/portfolio/review.py defines its own PortfolioReviewEngine
(Blueprint-aligned). This is a completely separate class from the legacy one
at atlas.portfolio_review. The naming collision is intentional — the domain
class is the forward-looking replacement.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from typer.testing import CliRunner

from atlas.cli.deprecations import all_deprecated_commands, all_retired_commands
from atlas.cli.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = REPO_ROOT / "atlas" / "cli" / "main.py"
HOME_ENGINE_PATH = REPO_ROOT / "atlas" / "home" / "engine.py"

runner = CliRunner()


def _fake_portfolio_path(tmp_path: Path) -> Path:
    p = tmp_path / "portfolio.json"
    p.write_text(
        json.dumps({
            "positions": [{
                "ticker": "NVDA",
                "company": "NVIDIA",
                "sector": "Semiconductors",
                "country": "United States",
                "market_cap": 3_000_000_000_000,
                "weight": 0.5,
                "quality_score": 90,
                "risk_score": 70,
            }]
        }),
        encoding="utf-8",
    )
    return p


def test_portfolio_review_command_is_no_longer_registered(tmp_path) -> None:
    """atlas portfolio review must not be a recognized subcommand of atlas portfolio."""
    result = runner.invoke(app, ["portfolio", "review", str(_fake_portfolio_path(tmp_path))])
    assert result.exit_code != 0


def test_portfolio_review_command_is_not_in_active_registry() -> None:
    assert "atlas portfolio review" not in all_deprecated_commands()


def test_portfolio_review_command_is_in_retired_registry() -> None:
    assert "atlas portfolio review" in all_retired_commands()


def test_portfolio_review_command_function_removed_from_cli() -> None:
    """The portfolio_review_command function must not exist in the CLI source."""
    source = CLI_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    func_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert "portfolio_review_command" not in func_names, (
        "portfolio_review_command function should have been removed in Sprint 90"
    )


def test_portfolio_summary_command_is_unaffected(tmp_path) -> None:
    """atlas portfolio summary must remain functional and not deprecated."""
    result = runner.invoke(app, ["portfolio", "summary", str(_fake_portfolio_path(tmp_path))])
    assert result.exit_code == 0
    assert "deprecated" not in result.output.lower()


def test_portfolio_analyze_remains_retired(tmp_path) -> None:
    """Sprint 89: atlas portfolio analyze must remain retired."""
    result = runner.invoke(app, ["portfolio", "analyze", str(_fake_portfolio_path(tmp_path)), "NVDA"])
    assert result.exit_code != 0


def test_legacy_portfolio_review_engine_remains_importable() -> None:
    """atlas.portfolio_review must still be importable — AtlasHomeEngine still uses it."""
    from atlas.portfolio_review import PortfolioReviewEngine, PortfolioReviewInput
    assert PortfolioReviewEngine is not None
    assert PortfolioReviewInput is not None


def test_home_engine_caller_remains() -> None:
    """atlas/home/engine.py must still import PortfolioReviewEngine — engine deletion blocker."""
    assert HOME_ENGINE_PATH.exists(), "Expected atlas/home/engine.py to exist"
    source = HOME_ENGINE_PATH.read_text(encoding="utf-8")
    assert "PortfolioReviewEngine" in source, (
        "atlas/home/engine.py should still import PortfolioReviewEngine "
        "(documents engine deletion blocker)"
    )
    assert "from atlas.portfolio_review" in source, (
        "atlas/home/engine.py should still import from atlas.portfolio_review"
    )


def test_portfolio_review_engine_module_remains_on_disk() -> None:
    """atlas.portfolio_review engine must still exist — AtlasHomeEngine depends on it."""
    import importlib
    mod = importlib.import_module("atlas.portfolio_review")
    assert hasattr(mod, "PortfolioReviewEngine"), (
        "atlas.portfolio_review.PortfolioReviewEngine must still be importable"
    )


def test_blueprint_portfolio_review_engine_is_unaffected() -> None:
    """The Blueprint-aligned PortfolioReviewEngine in atlas.domains.portfolio is unaffected."""
    from atlas.domains.portfolio import PortfolioReviewEngine
    assert PortfolioReviewEngine is not None


# ── Confirm remaining deprecated commands still work ─────────────────────────

def test_daily_brief_is_retired() -> None:
    result = runner.invoke(app, ["daily", "brief"])
    assert result.exit_code != 0


def test_evidence_assess_is_retired() -> None:
    result = runner.invoke(app, ["evidence", "assess"])
    assert result.exit_code != 0


def test_reason_analyze_is_retired() -> None:
    result = runner.invoke(app, ["reason", "analyze"])
    assert result.exit_code != 0


def test_risk_size_is_retired(tmp_path) -> None:
    p = tmp_path / "r.json"
    p.write_text(json.dumps({"ticker": "NVDA"}), encoding="utf-8")
    result = runner.invoke(app, ["risk", "size", str(p)])
    assert result.exit_code != 0


def test_watchlist_analyze_is_retired(tmp_path) -> None:
    p = tmp_path / "w.json"
    p.write_text(json.dumps({"name": "Test", "tickers": ["NVDA"]}), encoding="utf-8")
    result = runner.invoke(app, ["watchlist", "analyze", str(p)])
    assert result.exit_code != 0
