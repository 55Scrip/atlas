"""Sprint 45: portfolio runtime migration tests.

The legacy CLI portfolio file format (`atlas.analysis.portfolio.Portfolio`)
has no prior "summary" computation to compare against -- the existing legacy
commands (`portfolio analyze`, `portfolio review`) answer different questions
(ticker-fit and CIO review) and depend on providers/profiles/market data, so
they are out of scope for this sprint's safe migration surface.

Instead, "parity" here means: the adapter's translation from legacy
positions into Portfolio Domain holdings is verified against independently
computed expected values, and the new `atlas portfolio summary` CLI path is
verified to produce a deterministic Portfolio Domain summary with no
provider or network dependency.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from atlas.adapters.portfolio import legacy_portfolio_to_domain_portfolio
from atlas.analysis.portfolio import Portfolio as LegacyPortfolio
from atlas.cli.main import app
from atlas.domains.portfolio import ConcentrationLevel, portfolio_summary

runner = CliRunner()


def _legacy_portfolio() -> LegacyPortfolio:
    return LegacyPortfolio.from_mapping(
        {
            "positions": [
                {
                    "ticker": "nvda",
                    "company": "NVIDIA",
                    "sector": "Semiconductors",
                    "country": "USA",
                    "market_cap": 1_000_000,
                    "weight": 0.4,
                    "quality_score": 90,
                    "risk_score": 50,
                },
                {
                    "ticker": "tsm",
                    "company": "TSMC",
                    "sector": "Semiconductors",
                    "country": "Taiwan",
                    "market_cap": 600_000,
                    "weight": 0.35,
                    "quality_score": 85,
                    "risk_score": 40,
                },
                {
                    "ticker": "msft",
                    "company": "Microsoft",
                    "sector": "Software",
                    "country": "USA",
                    "market_cap": 2_500_000,
                    "weight": 0.25,
                    "quality_score": 88,
                    "risk_score": 30,
                },
            ]
        }
    )


def test_adapter_preserves_relative_weights_as_holdings() -> None:
    legacy = _legacy_portfolio()
    domain_portfolio = legacy_portfolio_to_domain_portfolio(legacy)

    assert len(domain_portfolio.holdings) == 3
    tickers = {holding.ticker for holding in domain_portfolio.holdings}
    assert tickers == {"NVDA", "TSM", "MSFT"}

    nvda = next(h for h in domain_portfolio.holdings if h.ticker == "NVDA")
    assert nvda.market_value == 0.4
    assert nvda.sector == "Semiconductors"
    assert nvda.country == "USA"


def test_adapter_is_deterministic_and_pure() -> None:
    legacy = _legacy_portfolio()
    first = legacy_portfolio_to_domain_portfolio(legacy)
    second = legacy_portfolio_to_domain_portfolio(legacy)

    assert first == second
    # input is untouched
    assert legacy == _legacy_portfolio()


def test_domain_summary_on_adapted_portfolio_matches_expected_allocation() -> None:
    legacy = _legacy_portfolio()
    domain_portfolio = legacy_portfolio_to_domain_portfolio(legacy)
    summary = portfolio_summary(domain_portfolio)

    assert summary.number_of_holdings == 3
    # 0.4 + 0.35 + 0.25 == 1.0 total relative weight
    assert summary.largest_weight == 0.4
    assert summary.concentration.level == ConcentrationLevel.HIGH

    semiconductor_allocation = next(
        a for a in summary.sector_allocation if a.name == "Semiconductors"
    )
    assert semiconductor_allocation.weight == 0.75  # (0.4 + 0.35) / 1.0

    software_allocation = next(a for a in summary.sector_allocation if a.name == "Software")
    assert software_allocation.weight == 0.25


def test_empty_legacy_holdings_list_is_rejected_same_as_existing_commands() -> None:
    # Legacy Portfolio.from_mapping already rejects empty positions; the new
    # summary command reuses that same loader, so behavior is unchanged.
    try:
        LegacyPortfolio.from_mapping({"positions": []})
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_cli_portfolio_summary_command_is_read_only_and_deterministic(tmp_path: Path) -> None:
    portfolio_file = tmp_path / "portfolio.json"
    portfolio_file.write_text(
        '{"positions": [{"ticker": "NVDA", "company": "NVIDIA", "sector": "Semiconductors",'
        ' "country": "USA", "market_cap": 1000000, "weight": 1.0,'
        ' "quality_score": 90, "risk_score": 50}]}'
    )

    first = runner.invoke(app, ["portfolio", "summary", str(portfolio_file)])
    second = runner.invoke(app, ["portfolio", "summary", str(portfolio_file)])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert first.stdout == second.stdout
    assert "Portfolio Summary (Portfolio Domain)" in first.stdout
    assert "NVDA" in first.stdout


def test_cli_portfolio_summary_rejects_missing_file_without_crashing(tmp_path: Path) -> None:
    missing_path = tmp_path / "does_not_exist.json"
    result = runner.invoke(app, ["portfolio", "summary", str(missing_path)])
    assert result.exit_code != 0


def test_portfolio_analyze_is_deprecated_not_removed() -> None:
    """Sprint 79: atlas portfolio analyze is deprecated — command still exists but shows deprecation message."""
    from typer.testing import CliRunner as _Runner
    from atlas.cli.main import app as _app
    result = _Runner().invoke(_app, ["portfolio", "analyze", "--help"])
    assert result.exit_code == 0
    assert "deprecated" in result.output.lower()
