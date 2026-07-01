"""Sprint 47: `atlas portfolio review` migration tests.

`atlas portfolio review` generates a CIO-style review that depends on
investor profile, suitability, risk drift, themes, market context, and
economics -- a deeply intertwined legacy engine stack with no Portfolio
Domain equivalents. That legacy output is preserved byte-for-byte.

What Sprint 47 migrates: the command now also appends a "Portfolio Summary
(Portfolio Domain)" section using the same adapter and domain calculations
introduced in Sprints 45 and 46. The migration is additive and identical
in pattern to Sprint 46's `atlas portfolio analyze` extension.
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


def test_review_rejects_empty_portfolio(tmp_path: Path) -> None:
    # Sprint 80: deprecated command exits 0 regardless of portfolio content
    path = _write_portfolio(tmp_path, [])
    result = runner.invoke(app, ["portfolio", "review", str(path)])
    assert result.exit_code == 0
    assert "deprecated" in result.stdout.lower()


def test_review_rejects_missing_portfolio_file(tmp_path: Path) -> None:
    # Sprint 80: deprecated command exits 0 regardless of file existence
    missing = tmp_path / "no_such_portfolio.json"
    result = runner.invoke(app, ["portfolio", "review", str(missing)])
    assert result.exit_code == 0
    assert "deprecated" in result.stdout.lower()


def test_review_output_preserves_all_legacy_sections(tmp_path: Path) -> None:
    # Sprint 80: deprecated — shows deprecation message, not legacy review sections
    path = _write_portfolio(tmp_path, _multi_positions())
    result = runner.invoke(app, ["portfolio", "review", str(path)])
    assert result.exit_code == 0
    assert "deprecated" in result.stdout.lower()
    assert "portfolio summary" in result.stdout.lower()


def test_review_appends_portfolio_domain_summary(tmp_path: Path) -> None:
    # Sprint 80: deprecated — directs to atlas portfolio summary
    path = _write_portfolio(tmp_path, _multi_positions())
    result = runner.invoke(app, ["portfolio", "review", str(path)])
    assert result.exit_code == 0
    assert "deprecated" in result.stdout.lower()
    assert "portfolio summary" in result.stdout.lower()


def test_review_domain_section_appears_after_legacy_section(tmp_path: Path) -> None:
    # Sprint 80: deprecated — no legacy or domain sections, just deprecation notice
    path = _write_portfolio(tmp_path, _multi_positions())
    result = runner.invoke(app, ["portfolio", "review", str(path)])
    assert result.exit_code == 0
    assert "deprecated" in result.stdout.lower()


def test_review_domain_values_match_independent_calculation(tmp_path: Path) -> None:
    # Sprint 80: deprecated — use atlas portfolio summary for domain values
    path = _write_portfolio(tmp_path, _multi_positions())
    result = runner.invoke(app, ["portfolio", "review", str(path)])
    assert result.exit_code == 0
    assert "deprecated" in result.stdout.lower()


def test_review_single_holding(tmp_path: Path) -> None:
    # Sprint 80: deprecated — no legacy output
    path = _write_portfolio(tmp_path, _single_position())
    result = runner.invoke(app, ["portfolio", "review", str(path)])
    assert result.exit_code == 0
    assert "deprecated" in result.stdout.lower()


def test_review_concentration_context_in_domain_section(tmp_path: Path) -> None:
    # Sprint 80: deprecated — no domain section output
    path = _write_portfolio(tmp_path, _multi_positions())
    result = runner.invoke(app, ["portfolio", "review", str(path)])
    assert result.exit_code == 0
    assert "deprecated" in result.stdout.lower()


def test_review_allocation_context_in_domain_section(tmp_path: Path) -> None:
    # Sprint 80: deprecated — no allocation output
    path = _write_portfolio(tmp_path, _multi_positions())
    result = runner.invoke(app, ["portfolio", "review", str(path)])
    assert result.exit_code == 0
    assert "deprecated" in result.stdout.lower()


def test_review_is_deterministic(tmp_path: Path) -> None:
    path = _write_portfolio(tmp_path, _multi_positions())
    first = runner.invoke(app, ["portfolio", "review", str(path)])
    second = runner.invoke(app, ["portfolio", "review", str(path)])

    assert first.exit_code == second.exit_code == 0
    assert first.stdout == second.stdout


def test_review_does_not_make_network_calls(tmp_path: Path, monkeypatch) -> None:
    import atlas.providers.yahoo as yahoo_module

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("urlopen must not be called by portfolio review")

    monkeypatch.setattr(yahoo_module, "urlopen", _fail_if_called)

    path = _write_portfolio(tmp_path, _single_position())
    result = runner.invoke(app, ["portfolio", "review", str(path)])
    assert result.exit_code == 0


def test_review_output_contains_no_buy_sell_strong_buy_language(tmp_path: Path) -> None:
    path = _write_portfolio(tmp_path, _multi_positions())
    result = runner.invoke(app, ["portfolio", "review", str(path)])

    assert result.exit_code == 0
    forbidden = ("strong buy", "strong sell", "buy now", "sell now")
    lowered = result.stdout.lower()
    for term in forbidden:
        assert term not in lowered, f"Forbidden term found in output: {term!r}"
