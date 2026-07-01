"""Sprint 89: Retirement confirmation for atlas portfolio analyze migration tests.

Sprint 46 extended `atlas portfolio analyze` to also print a Portfolio Domain
summary. Sprint 79 deprecated the command entirely. Sprint 89 retired the
command body — it is no longer a registered CLI command.

These tests confirm the retired behavior and that the underlying engine and
domain adapter still work independently (they are still used by active callers).
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from atlas.adapters.portfolio import legacy_portfolio_to_domain_portfolio
from atlas.analysis.portfolio import Portfolio as LegacyPortfolio
from atlas.cli.main import app
from atlas.domains.portfolio import ConcentrationLevel, portfolio_summary

runner = CliRunner()


def _write_portfolio(tmp_path: Path, positions: list[dict]) -> Path:
    import json

    path = tmp_path / "portfolio.json"
    path.write_text(json.dumps({"positions": positions}))
    return path


def _single_holding_positions() -> list[dict]:
    return [
        {
            "ticker": "NVDA",
            "company": "NVIDIA",
            "sector": "Semiconductors",
            "country": "USA",
            "market_cap": 1_000_000,
            "weight": 1.0,
            "quality_score": 90,
            "risk_score": 50,
        }
    ]


def _multi_holding_positions() -> list[dict]:
    return [
        {
            "ticker": "NVDA",
            "company": "NVIDIA",
            "sector": "Semiconductors",
            "country": "USA",
            "market_cap": 1_000_000,
            "weight": 0.4,
            "quality_score": 90,
            "risk_score": 50,
        },
        {
            "ticker": "TSM",
            "company": "TSMC",
            "sector": "Semiconductors",
            "country": "Taiwan",
            "market_cap": 600_000,
            "weight": 0.35,
            "quality_score": 85,
            "risk_score": 40,
        },
        {
            "ticker": "MSFT",
            "company": "Microsoft",
            "sector": "Software",
            "country": "USA",
            "market_cap": 2_500_000,
            "weight": 0.25,
            "quality_score": 88,
            "risk_score": 30,
        },
    ]


# ── Sprint 89: all CLI invocations of `atlas portfolio analyze` must fail ────

def test_analyze_rejects_empty_portfolio_same_as_before(tmp_path: Path) -> None:
    # Sprint 89: command body retired — no longer a valid CLI command
    path = _write_portfolio(tmp_path, [])
    result = runner.invoke(app, ["portfolio", "analyze", str(path), "AAPL"])
    assert result.exit_code != 0


def test_analyze_output_still_contains_original_fit_score_sections(tmp_path: Path) -> None:
    # Sprint 89: command body retired — no longer a valid CLI command
    path = _write_portfolio(tmp_path, _single_holding_positions())
    result = runner.invoke(app, ["portfolio", "analyze", str(path), "AAPL"])
    assert result.exit_code != 0


def test_analyze_output_now_appends_portfolio_domain_summary(tmp_path: Path) -> None:
    # Sprint 89: command body retired — no longer a valid CLI command
    path = _write_portfolio(tmp_path, _multi_holding_positions())
    result = runner.invoke(app, ["portfolio", "analyze", str(path), "AAPL"])
    assert result.exit_code != 0


def test_analyze_domain_summary_matches_independent_domain_calculation(tmp_path: Path) -> None:
    # Sprint 89: command body retired — domain summary now accessed via atlas portfolio summary
    path = _write_portfolio(tmp_path, _multi_holding_positions())
    result = runner.invoke(app, ["portfolio", "analyze", str(path), "AAPL"])
    assert result.exit_code != 0


def test_analyze_with_single_holding(tmp_path: Path) -> None:
    # Sprint 89: command body retired — no longer a valid CLI command
    path = _write_portfolio(tmp_path, _single_holding_positions())
    result = runner.invoke(app, ["portfolio", "analyze", str(path), "AAPL"])
    assert result.exit_code != 0


def test_analyze_is_deterministic_across_repeated_runs(tmp_path: Path) -> None:
    # Sprint 89: retired command consistently fails on both invocations
    path = _write_portfolio(tmp_path, _multi_holding_positions())
    first = runner.invoke(app, ["portfolio", "analyze", str(path), "AAPL"])
    second = runner.invoke(app, ["portfolio", "analyze", str(path), "AAPL"])
    assert first.exit_code != 0
    assert second.exit_code != 0


def test_analyze_default_provider_makes_no_network_call(tmp_path: Path, monkeypatch) -> None:
    # Sprint 89: command body retired — no provider call possible; exit_code != 0
    import atlas.providers.yahoo as yahoo_module

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("urlopen should not be called")

    monkeypatch.setattr(yahoo_module, "urlopen", _fail_if_called)

    path = _write_portfolio(tmp_path, _single_holding_positions())
    result = runner.invoke(app, ["portfolio", "analyze", str(path), "AAPL"])
    assert result.exit_code != 0


def test_analyze_unknown_provider_still_fails_cleanly(tmp_path: Path) -> None:
    # Sprint 89: command body retired — no longer a valid CLI command
    path = _write_portfolio(tmp_path, _single_holding_positions())
    result = runner.invoke(
        app, ["portfolio", "analyze", str(path), "AAPL", "--provider", "bogus"]
    )
    assert result.exit_code != 0


# ── Underlying engine and adapter still work independently ───────────────────

def test_legacy_portfolio_loads_from_json(tmp_path: Path) -> None:
    """atlas.analysis.portfolio.Portfolio must still load from JSON (used by portfolio review)."""
    path = _write_portfolio(tmp_path, _single_holding_positions())
    portfolio = LegacyPortfolio.from_json_file(path)
    assert len(portfolio.positions) == 1
    assert portfolio.positions[0].ticker == "NVDA"


def test_domain_adapter_still_converts_legacy_portfolio() -> None:
    """The portfolio adapter bridge must still work — used by atlas portfolio summary."""
    import json
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump({"positions": _single_holding_positions()}, f)
        tmp = Path(f.name)
    legacy = LegacyPortfolio.from_json_file(tmp)
    domain = legacy_portfolio_to_domain_portfolio(legacy)
    summary = portfolio_summary(domain)
    assert summary.number_of_holdings == 1
    tmp.unlink()
