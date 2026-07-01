"""Sprint 90: Retirement confirmation for atlas portfolio review migration tests.

Sprint 47 extended `atlas portfolio review` to also append a Portfolio Domain summary.
Sprint 80 deprecated the command entirely. Sprint 90 retired the command body — it is
no longer a registered CLI command.

These tests confirm the retired CLI behavior and that the underlying legacy engine and
domain adapter still work independently (the legacy engine is still used by AtlasHomeEngine).
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from atlas.adapters.portfolio import legacy_portfolio_to_domain_portfolio
from atlas.analysis.portfolio import Portfolio as LegacyPortfolio
from atlas.cli.main import app
from atlas.domains.portfolio import ConcentrationLevel, portfolio_summary

runner = CliRunner()


def _write_portfolio(tmp_path: Path, positions: list[dict]) -> Path:
    path = tmp_path / "portfolio.json"
    path.write_text(json.dumps({"positions": positions}))
    return path


def _single_position() -> list[dict]:
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


def _multi_positions() -> list[dict]:
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


# ── Sprint 90: all CLI invocations of `atlas portfolio review` must fail ─────

def test_review_rejects_empty_portfolio(tmp_path: Path) -> None:
    # Sprint 90: command body retired — no longer a valid CLI command
    path = _write_portfolio(tmp_path, [])
    result = runner.invoke(app, ["portfolio", "review", str(path)])
    assert result.exit_code != 0


def test_review_rejects_missing_portfolio_file(tmp_path: Path) -> None:
    # Sprint 90: command body retired — no longer a valid CLI command
    missing = tmp_path / "no_such_portfolio.json"
    result = runner.invoke(app, ["portfolio", "review", str(missing)])
    assert result.exit_code != 0


def test_review_output_preserves_all_legacy_sections(tmp_path: Path) -> None:
    # Sprint 90: command body retired — no longer a valid CLI command
    path = _write_portfolio(tmp_path, _multi_positions())
    result = runner.invoke(app, ["portfolio", "review", str(path)])
    assert result.exit_code != 0


def test_review_appends_portfolio_domain_summary(tmp_path: Path) -> None:
    # Sprint 90: command body retired — no longer a valid CLI command
    path = _write_portfolio(tmp_path, _multi_positions())
    result = runner.invoke(app, ["portfolio", "review", str(path)])
    assert result.exit_code != 0


def test_review_domain_section_appears_after_legacy_section(tmp_path: Path) -> None:
    # Sprint 90: command body retired — no longer a valid CLI command
    path = _write_portfolio(tmp_path, _multi_positions())
    result = runner.invoke(app, ["portfolio", "review", str(path)])
    assert result.exit_code != 0


def test_review_domain_values_match_independent_calculation(tmp_path: Path) -> None:
    # Sprint 90: command body retired — use atlas portfolio summary for domain values
    path = _write_portfolio(tmp_path, _multi_positions())
    result = runner.invoke(app, ["portfolio", "review", str(path)])
    assert result.exit_code != 0


def test_review_single_holding(tmp_path: Path) -> None:
    # Sprint 90: command body retired — no longer a valid CLI command
    path = _write_portfolio(tmp_path, _single_position())
    result = runner.invoke(app, ["portfolio", "review", str(path)])
    assert result.exit_code != 0


def test_review_concentration_context_in_domain_section(tmp_path: Path) -> None:
    # Sprint 90: command body retired — no longer a valid CLI command
    path = _write_portfolio(tmp_path, _multi_positions())
    result = runner.invoke(app, ["portfolio", "review", str(path)])
    assert result.exit_code != 0


def test_review_allocation_context_in_domain_section(tmp_path: Path) -> None:
    # Sprint 90: command body retired — no longer a valid CLI command
    path = _write_portfolio(tmp_path, _multi_positions())
    result = runner.invoke(app, ["portfolio", "review", str(path)])
    assert result.exit_code != 0


def test_review_is_deterministic(tmp_path: Path) -> None:
    # Sprint 90: retired command consistently fails on both invocations
    path = _write_portfolio(tmp_path, _multi_positions())
    first = runner.invoke(app, ["portfolio", "review", str(path)])
    second = runner.invoke(app, ["portfolio", "review", str(path)])
    assert first.exit_code != 0
    assert second.exit_code != 0


def test_review_does_not_make_network_calls(tmp_path: Path, monkeypatch) -> None:
    # Sprint 90: command body retired — no provider call possible; exit_code != 0
    import atlas.providers.yahoo as yahoo_module

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("urlopen must not be called by portfolio review")

    monkeypatch.setattr(yahoo_module, "urlopen", _fail_if_called)

    path = _write_portfolio(tmp_path, _single_position())
    result = runner.invoke(app, ["portfolio", "review", str(path)])
    assert result.exit_code != 0


def test_review_output_contains_no_buy_sell_strong_buy_language(tmp_path: Path) -> None:
    # Sprint 90: retired command — output is empty; forbidden language check is trivially satisfied
    path = _write_portfolio(tmp_path, _multi_positions())
    result = runner.invoke(app, ["portfolio", "review", str(path)])
    assert result.exit_code != 0
    forbidden = ("strong buy", "strong sell", "buy now", "sell now")
    lowered = result.stdout.lower()
    for term in forbidden:
        assert term not in lowered, f"Forbidden term found in output: {term!r}"


# ── Underlying legacy engine still works independently ───────────────────────

def test_legacy_portfolio_review_engine_still_works() -> None:
    """The legacy PortfolioReviewEngine must still function — AtlasHomeEngine uses it."""
    from atlas.portfolio_review import PortfolioReviewEngine, PortfolioReviewInput
    import json
    import tempfile

    positions = _single_position()
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump({"positions": positions}, f)
        tmp = Path(f.name)

    portfolio = LegacyPortfolio.from_json_file(tmp)
    report = PortfolioReviewEngine().review(PortfolioReviewInput(portfolio=portfolio))
    assert report is not None
    tmp.unlink()


def test_domain_adapter_still_works() -> None:
    """The portfolio adapter bridge must still work — used by atlas portfolio summary."""
    import json
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump({"positions": _single_position()}, f)
        tmp = Path(f.name)

    legacy = LegacyPortfolio.from_json_file(tmp)
    domain = legacy_portfolio_to_domain_portfolio(legacy)
    summary = portfolio_summary(domain)
    assert summary.number_of_holdings == 1
    tmp.unlink()
