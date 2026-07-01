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
    path = _write_portfolio(tmp_path, [])
    result = runner.invoke(app, ["portfolio", "review", str(path)])
    assert result.exit_code == 1
    assert "Portfolio review failed" in result.stdout


def test_review_rejects_missing_portfolio_file(tmp_path: Path) -> None:
    missing = tmp_path / "no_such_portfolio.json"
    result = runner.invoke(app, ["portfolio", "review", str(missing)])
    assert result.exit_code == 1


def test_review_output_preserves_all_legacy_sections(tmp_path: Path) -> None:
    path = _write_portfolio(tmp_path, _multi_positions())
    result = runner.invoke(app, ["portfolio", "review", str(path)])

    assert result.exit_code == 0
    # All original PortfolioReviewReport sections must still appear.
    expected_sections = [
        "Atlas Portfolio Review",
        "Bottom Line",
        "Atlas Rating",
        "Portfolio Strengths",
        "Main Risks",
        "Investor Alignment",
        "Theme Exposure",
        "Market Context",
        "What Atlas Is Monitoring",
        "What Could Change Atlas' View",
        "Missing Information",
        "Optional Follow-up Questions",
        "Research Framing",
    ]
    for section in expected_sections:
        assert section in result.stdout, f"Missing legacy section: {section!r}"


def test_review_appends_portfolio_domain_summary(tmp_path: Path) -> None:
    path = _write_portfolio(tmp_path, _multi_positions())
    result = runner.invoke(app, ["portfolio", "review", str(path)])

    assert result.exit_code == 0
    assert "Portfolio Summary (Portfolio Domain)" in result.stdout
    assert "Sector Allocation" in result.stdout
    assert "Country Allocation" in result.stdout
    assert "Top Holdings" in result.stdout


def test_review_domain_section_appears_after_legacy_section(tmp_path: Path) -> None:
    path = _write_portfolio(tmp_path, _multi_positions())
    result = runner.invoke(app, ["portfolio", "review", str(path)])

    assert result.exit_code == 0
    research_framing_index = result.stdout.index("Research Framing")
    domain_index = result.stdout.index("Portfolio Summary (Portfolio Domain)")
    assert domain_index > research_framing_index


def test_review_domain_values_match_independent_calculation(tmp_path: Path) -> None:
    positions = _multi_positions()
    path = _write_portfolio(tmp_path, positions)

    legacy_portfolio = LegacyPortfolio.from_mapping({"positions": positions})
    expected = portfolio_summary(legacy_portfolio_to_domain_portfolio(legacy_portfolio))

    result = runner.invoke(app, ["portfolio", "review", str(path)])

    assert result.exit_code == 0
    assert f"Largest weight: {expected.largest_weight:.1%}" in result.stdout
    assert f"Concentration: {expected.concentration.level.value}" in result.stdout
    assert expected.concentration.level == ConcentrationLevel.HIGH


def test_review_single_holding(tmp_path: Path) -> None:
    path = _write_portfolio(tmp_path, _single_position())
    result = runner.invoke(app, ["portfolio", "review", str(path)])

    assert result.exit_code == 0
    assert "Number of holdings: 1" in result.stdout
    assert "Largest weight: 100.0%" in result.stdout


def test_review_concentration_context_in_domain_section(tmp_path: Path) -> None:
    path = _write_portfolio(tmp_path, _multi_positions())
    result = runner.invoke(app, ["portfolio", "review", str(path)])

    assert result.exit_code == 0
    assert "Concentration:" in result.stdout


def test_review_allocation_context_in_domain_section(tmp_path: Path) -> None:
    path = _write_portfolio(tmp_path, _multi_positions())
    result = runner.invoke(app, ["portfolio", "review", str(path)])

    assert result.exit_code == 0
    assert "Semiconductors" in result.stdout
    assert "75.0%" in result.stdout


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
