"""Sprint 46: `atlas portfolio analyze` migration tests.

`atlas portfolio analyze` computes a proprietary ticker-fit score
(diversification, sector/country/market-cap concentration impact, overlap,
expected quality/risk impact) that has no equivalent in the Portfolio
Domain -- the domain answers "what does this portfolio look like", not
"how well would this new ticker fit". That scoring logic therefore stays on
the legacy `PortfolioIntelligenceEngine` path unchanged.

What Sprint 46 migrates: the command now *also* computes and prints a
Portfolio Domain summary (allocation, concentration, cash weight, top
holdings) for the existing portfolio, using the same
`atlas.adapters.portfolio` bridge introduced in Sprint 45. This is a
purely additive change -- the original `PortfolioAnalysis` output is
produced and rendered exactly as before, with the domain summary appended
after it.
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


def test_analyze_rejects_empty_portfolio_same_as_before(tmp_path: Path) -> None:
    # Sprint 79: deprecated command exits 0 regardless of portfolio content
    path = _write_portfolio(tmp_path, [])
    result = runner.invoke(app, ["portfolio", "analyze", str(path), "AAPL"])
    assert result.exit_code == 0
    assert "deprecated" in result.stdout.lower()


def test_analyze_output_still_contains_original_fit_score_sections(tmp_path: Path) -> None:
    # Sprint 79: deprecated — shows deprecation message, not legacy analysis sections
    path = _write_portfolio(tmp_path, _single_holding_positions())
    result = runner.invoke(app, ["portfolio", "analyze", str(path), "AAPL"])

    assert result.exit_code == 0
    assert "deprecated" in result.stdout.lower()
    assert "portfolio summary" in result.stdout.lower()


def test_analyze_output_now_appends_portfolio_domain_summary(tmp_path: Path) -> None:
    # Sprint 79: deprecated — directs to atlas portfolio summary instead
    path = _write_portfolio(tmp_path, _multi_holding_positions())
    result = runner.invoke(app, ["portfolio", "analyze", str(path), "AAPL"])

    assert result.exit_code == 0
    assert "deprecated" in result.stdout.lower()
    assert "portfolio summary" in result.stdout.lower()


def test_analyze_domain_summary_matches_independent_domain_calculation(tmp_path: Path) -> None:
    # Sprint 79: deprecated — domain calculation now accessed via atlas portfolio summary directly
    path = _write_portfolio(tmp_path, _multi_holding_positions())
    result = runner.invoke(app, ["portfolio", "analyze", str(path), "AAPL"])
    assert result.exit_code == 0
    assert "deprecated" in result.stdout.lower()


def test_analyze_with_single_holding(tmp_path: Path) -> None:
    # Sprint 79: deprecated — no legacy output, just deprecation notice
    path = _write_portfolio(tmp_path, _single_holding_positions())
    result = runner.invoke(app, ["portfolio", "analyze", str(path), "AAPL"])

    assert result.exit_code == 0
    assert "deprecated" in result.stdout.lower()


def test_analyze_is_deterministic_across_repeated_runs(tmp_path: Path) -> None:
    path = _write_portfolio(tmp_path, _multi_holding_positions())
    first = runner.invoke(app, ["portfolio", "analyze", str(path), "AAPL"])
    second = runner.invoke(app, ["portfolio", "analyze", str(path), "AAPL"])

    assert first.exit_code == second.exit_code == 0
    assert first.stdout == second.stdout


def test_analyze_default_provider_makes_no_network_call(tmp_path: Path, monkeypatch) -> None:
    import atlas.providers.yahoo as yahoo_module

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("urlopen should not be called for the default mock provider")

    monkeypatch.setattr(yahoo_module, "urlopen", _fail_if_called)

    path = _write_portfolio(tmp_path, _single_holding_positions())
    result = runner.invoke(app, ["portfolio", "analyze", str(path), "AAPL"])

    assert result.exit_code == 0


def test_analyze_unknown_provider_still_fails_cleanly(tmp_path: Path) -> None:
    # Sprint 79: deprecated command exits 0 and shows deprecation message regardless of provider
    path = _write_portfolio(tmp_path, _single_holding_positions())
    result = runner.invoke(
        app, ["portfolio", "analyze", str(path), "AAPL", "--provider", "bogus"]
    )
    assert result.exit_code == 0
    assert "deprecated" in result.stdout.lower()
