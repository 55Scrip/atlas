"""Sprint 48: Daily Brief capability tests.

Tests for the new Blueprint-aligned `atlas.capabilities.daily_brief` capability.
The legacy `atlas.daily_brief` engine and `atlas daily brief` CLI command are
left completely untouched; these tests cover only the new capability path.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from atlas.adapters.portfolio import legacy_portfolio_to_domain_portfolio
from atlas.analysis.portfolio import Portfolio as LegacyPortfolio
from atlas.capabilities.daily_brief import (
    DailyBriefCapability,
    DailyBriefInput,
    DailyBriefPriority,
    DailyBriefReport,
)
from atlas.capabilities.daily_brief.engine import render_daily_brief_report
from atlas.cli.main import app
from atlas.domains.portfolio import portfolio_summary

runner = CliRunner()

FORBIDDEN_LANGUAGE = (
    "buy",
    "sell",
    "strong buy",
    "strong sell",
    "urgent",
    "must act",
    "guaranteed",
    "risk-free",
    "price target",
    "outperform",
)


# ── helpers ────────────────────────────────────────────────────────────────────


def _make_portfolio_summary(weight: float = 0.4):
    legacy = LegacyPortfolio.from_mapping(
        {
            "positions": [
                {
                    "ticker": "NVDA",
                    "company": "NVIDIA",
                    "sector": "Semiconductors",
                    "country": "USA",
                    "market_cap": 1_000_000,
                    "weight": weight,
                    "quality_score": 90,
                    "risk_score": 50,
                },
                {
                    "ticker": "MSFT",
                    "company": "Microsoft",
                    "sector": "Software",
                    "country": "USA",
                    "market_cap": 2_500_000,
                    "weight": round(1.0 - weight, 2),
                    "quality_score": 88,
                    "risk_score": 30,
                },
            ]
        }
    )
    return portfolio_summary(legacy_portfolio_to_domain_portfolio(legacy))


def _write_portfolio(tmp_path: Path, large_weight: float = 0.4) -> Path:
    path = tmp_path / "portfolio.json"
    path.write_text(
        json.dumps(
            {
                "positions": [
                    {
                        "ticker": "NVDA",
                        "company": "NVIDIA",
                        "sector": "Semiconductors",
                        "country": "USA",
                        "market_cap": 1_000_000,
                        "weight": large_weight,
                        "quality_score": 90,
                        "risk_score": 50,
                    },
                    {
                        "ticker": "MSFT",
                        "company": "Microsoft",
                        "sector": "Software",
                        "country": "USA",
                        "market_cap": 2_500_000,
                        "weight": round(1.0 - large_weight, 2),
                        "quality_score": 88,
                        "risk_score": 30,
                    },
                ]
            }
        )
    )
    return path


# ── model and capability tests ─────────────────────────────────────────────────


def test_capability_generates_report_with_no_input() -> None:
    report = DailyBriefCapability().generate()
    assert isinstance(report, DailyBriefReport)
    assert report.title == "Atlas Daily Brief"
    assert report.summary is not None
    assert report.sections


def test_no_meaningful_developments_on_empty_input() -> None:
    report = DailyBriefCapability().generate(DailyBriefInput())
    assert not report.summary.has_meaningful_developments
    assert report.summary.overall_priority == DailyBriefPriority.LOW
    rendered = render_daily_brief_report(report)
    assert "No meaningful developments were identified" in rendered


def test_deterministic_output_with_same_input() -> None:
    brief_input = DailyBriefInput(
        portfolio_summary=_make_portfolio_summary(),
        open_research_questions=("What is the TAM?", "Who are the main competitors?"),
        knowledge_node_count=5,
    )
    first = render_daily_brief_report(DailyBriefCapability().generate(brief_input))
    second = render_daily_brief_report(DailyBriefCapability().generate(brief_input))
    assert first == second


def test_sections_are_ordered_deterministically() -> None:
    report = DailyBriefCapability().generate(
        DailyBriefInput(portfolio_summary=_make_portfolio_summary())
    )
    titles = [s.title for s in report.sections]
    assert titles[0] == "What Deserves Attention"
    assert "Portfolio Context" in titles
    assert titles.index("What Deserves Attention") < titles.index("Portfolio Context")


def test_open_research_questions_surface_as_unknowns() -> None:
    questions = ("What is the TAM?", "Who owns the supply chain?")
    report = DailyBriefCapability().generate(
        DailyBriefInput(open_research_questions=questions)
    )
    assert report.summary.has_meaningful_developments
    assert len(report.unknowns) == len(questions)
    assert report.unknowns[0].question == questions[0]


def test_open_research_questions_generate_moderate_priority_item() -> None:
    report = DailyBriefCapability().generate(
        DailyBriefInput(open_research_questions=("Question A",))
    )
    attention_section = next(s for s in report.sections if s.title == "What Deserves Attention")
    priorities = {item.priority for item in attention_section.items}
    assert DailyBriefPriority.MODERATE in priorities


def test_high_concentration_portfolio_raises_priority_to_high() -> None:
    summary = _make_portfolio_summary(weight=0.7)
    report = DailyBriefCapability().generate(DailyBriefInput(portfolio_summary=summary))
    assert report.summary.overall_priority == DailyBriefPriority.HIGH
    attention = next(s for s in report.sections if s.title == "What Deserves Attention")
    high_items = [i for i in attention.items if i.priority == DailyBriefPriority.HIGH]
    assert high_items


def test_low_concentration_portfolio_does_not_raise_to_high() -> None:
    # 5 equal-weight positions → largest position = 20% → ConcentrationLevel.LOW
    positions = [
        {"ticker": f"T{i}", "company": f"Co{i}", "sector": "Software",
         "country": "USA", "market_cap": 100_000, "weight": 0.2,
         "quality_score": 80, "risk_score": 40}
        for i in range(5)
    ]
    legacy = LegacyPortfolio.from_mapping({"positions": positions})
    low_conc_summary = portfolio_summary(legacy_portfolio_to_domain_portfolio(legacy))
    report = DailyBriefCapability().generate(DailyBriefInput(portfolio_summary=low_conc_summary))
    assert report.summary.overall_priority != DailyBriefPriority.HIGH


def test_portfolio_context_section_included_when_summary_provided() -> None:
    report = DailyBriefCapability().generate(
        DailyBriefInput(portfolio_summary=_make_portfolio_summary())
    )
    assert any(s.title == "Portfolio Context" for s in report.sections)


def test_portfolio_context_section_omitted_when_no_summary() -> None:
    report = DailyBriefCapability().generate(DailyBriefInput())
    assert not any(s.title == "Portfolio Context" for s in report.sections)


def test_knowledge_node_count_surfaces_in_included_context() -> None:
    # Sprint 65: knowledge context moved out of What Deserves Attention (LOW priority)
    # and into Included Context so it remains visible without claiming attention.
    report = DailyBriefCapability().generate(DailyBriefInput(knowledge_node_count=7))
    rendered = render_daily_brief_report(report)
    assert "7" in rendered
    assert "Knowledge" in rendered
    # Knowledge should NOT appear in the What Deserves Attention section
    opening = next(s for s in report.sections if s.title == "What Deserves Attention")
    detail_text = " ".join(item.detail for item in opening.items)
    assert "knowledge" not in detail_text.lower()


def test_next_research_steps_populated_from_questions() -> None:
    report = DailyBriefCapability().generate(
        DailyBriefInput(open_research_questions=("Q1", "Q2"))
    )
    assert report.next_research_steps
    assert any("2" in step for step in report.next_research_steps)


def test_no_forbidden_language_in_rendered_output() -> None:
    report = DailyBriefCapability().generate(
        DailyBriefInput(
            portfolio_summary=_make_portfolio_summary(weight=0.7),
            open_research_questions=("What is the moat?",),
            knowledge_node_count=3,
        )
    )
    rendered = render_daily_brief_report(report).lower()
    for term in FORBIDDEN_LANGUAGE:
        assert term not in rendered, f"Forbidden term found: {term!r}"


def test_rendered_output_always_ends_with_research_framing() -> None:
    rendered = render_daily_brief_report(DailyBriefCapability().generate())
    assert "Research Framing" in rendered
    assert "not a news feed" in rendered
    assert "not personalized" not in rendered or "not a" in rendered


def test_capability_makes_no_network_calls(monkeypatch) -> None:
    import atlas.providers.yahoo as yahoo_module

    def _fail(*args, **kwargs):
        raise AssertionError("urlopen must not be called by DailyBriefCapability")

    monkeypatch.setattr(yahoo_module, "urlopen", _fail)
    DailyBriefCapability().generate(
        DailyBriefInput(portfolio_summary=_make_portfolio_summary())
    )


def test_capability_does_not_import_providers_at_module_level() -> None:
    import atlas.capabilities.daily_brief.engine as engine_module
    import atlas.capabilities.daily_brief.models as models_module

    for module in (engine_module, models_module):
        src = Path(module.__file__).read_text()
        assert "atlas.providers" not in src, f"{module.__file__} imports atlas.providers"
        assert "urllib" not in src, f"{module.__file__} imports urllib"


# ── CLI command tests ──────────────────────────────────────────────────────────


def test_cli_daily_summary_no_args_succeeds() -> None:
    result = runner.invoke(app, ["daily", "summary"])
    assert result.exit_code == 0
    assert "Atlas Daily Brief" in result.stdout
    assert "No meaningful developments" in result.stdout


def test_cli_daily_summary_with_portfolio_succeeds(tmp_path: Path) -> None:
    path = _write_portfolio(tmp_path, large_weight=0.4)
    result = runner.invoke(app, ["daily", "summary", "--portfolio", str(path)])
    assert result.exit_code == 0
    assert "Atlas Daily Brief" in result.stdout
    assert "Portfolio Context" in result.stdout


def test_cli_daily_summary_high_concentration_portfolio(tmp_path: Path) -> None:
    path = _write_portfolio(tmp_path, large_weight=0.7)
    result = runner.invoke(app, ["daily", "summary", "--portfolio", str(path)])
    assert result.exit_code == 0
    assert "high" in result.stdout.lower()


def test_cli_daily_summary_missing_portfolio_fails_cleanly(tmp_path: Path) -> None:
    result = runner.invoke(app, ["daily", "summary", "--portfolio", str(tmp_path / "nope.json")])
    assert result.exit_code == 1
    assert "Daily summary failed" in result.stdout


def test_cli_daily_summary_is_deterministic(tmp_path: Path) -> None:
    path = _write_portfolio(tmp_path)
    first = runner.invoke(app, ["daily", "summary", "--portfolio", str(path)])
    second = runner.invoke(app, ["daily", "summary", "--portfolio", str(path)])
    assert first.exit_code == second.exit_code == 0
    assert first.stdout == second.stdout


def test_cli_legacy_daily_brief_is_retired() -> None:
    """Sprint 85: atlas daily brief command body retired — no longer a valid command."""
    result = runner.invoke(app, ["daily", "brief"])
    assert result.exit_code != 0
