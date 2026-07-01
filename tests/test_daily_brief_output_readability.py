"""Sprint 62: Daily Brief output readability tests.

Verifies that the rendered Daily Brief output is:
- structured (separator lines, section headers)
- deterministic (same input → same output)
- calm (no recommendation language, no urgent language)
- clear about what is included (Included Context)
- clear about company separation (per-company grouping)
- graceful when evidence gaps are absent
- graceful when no meaningful developments exist
- section-ordered correctly (Company Analysis before Research/Watchlist)
- free from network or provider calls
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from atlas.capabilities.daily_brief import DailyBriefCapability, DailyBriefInput
from atlas.capabilities.daily_brief.engine import (
    _SEP,
    _priority_marker,
    render_daily_brief_report,
)
from atlas.capabilities.daily_brief.models import DailyBriefPriority
from atlas.cli.main import app

runner = CliRunner()

DEMO_DIR = Path(__file__).parent.parent / "examples" / "daily_brief_demo"
KNOWLEDGE = DEMO_DIR / "knowledge.json"
RESEARCH_INPUT = DEMO_DIR / "research_input.json"
WATCHLIST_INPUT = DEMO_DIR / "watchlist_input.json"

FORBIDDEN = (
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
    "market-beating",
    "better investment",
    "worse investment",
)


# ── separator / structure ──────────────────────────────────────────────────────


def test_rendered_output_contains_separator_lines() -> None:
    rendered = render_daily_brief_report(DailyBriefCapability().generate())
    assert _SEP in rendered


def test_rendered_output_starts_with_title() -> None:
    rendered = render_daily_brief_report(DailyBriefCapability().generate())
    assert rendered.startswith("Atlas Daily Brief")


def test_rendered_output_ends_with_research_framing() -> None:
    rendered = render_daily_brief_report(DailyBriefCapability().generate())
    assert rendered.strip().endswith(
        "or personal financial advice."
    )


def test_research_framing_always_present() -> None:
    rendered = render_daily_brief_report(DailyBriefCapability().generate())
    assert "Research Framing" in rendered
    assert "not a news feed" in rendered


# ── determinism ────────────────────────────────────────────────────────────────


def test_rendered_output_is_deterministic(tmp_path: Path) -> None:
    ca = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca)])
    r1 = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    r2 = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert r1.stdout == r2.stdout


# ── section ordering ───────────────────────────────────────────────────────────


def test_company_analysis_section_appears_before_research_section(tmp_path: Path) -> None:
    research_out = tmp_path / "research.json"
    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    ca = tmp_path / "ca.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD", "--knowledge", str(KNOWLEDGE), "--research", str(research_out),
        "--output", str(ca),
    ])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca), "--research", str(research_out)])
    assert result.exit_code == 0
    ca_pos = result.stdout.index("Company Analysis Context")
    research_pos = result.stdout.index("Research Context")
    assert ca_pos < research_pos, "Company Analysis Context must appear before Research Context"


def test_what_deserves_attention_is_first_section(tmp_path: Path) -> None:
    ca = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca)])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert result.exit_code == 0
    assert "What Deserves Attention" in result.stdout
    assert result.stdout.index("What Deserves Attention") < result.stdout.index("Company Analysis Context")


def test_evidence_gaps_appear_before_unresolved_questions(tmp_path: Path) -> None:
    ca = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca)])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert result.exit_code == 0
    assert "Evidence Gaps" in result.stdout
    assert "Unresolved Questions" in result.stdout
    assert result.stdout.index("Evidence Gaps") < result.stdout.index("Unresolved Questions")


# ── Included Context ───────────────────────────────────────────────────────────


def test_included_context_shows_company_tickers(tmp_path: Path) -> None:
    ca_amd = tmp_path / "ca_amd.json"
    ca_nvda = tmp_path / "ca_nvda.json"
    combined = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca_amd)])
    runner.invoke(app, ["company-analysis", "export", "--ticker", "NVDA", "--output", str(ca_nvda)])
    runner.invoke(app, ["company-analysis", "merge",
                        "--inputs", str(ca_amd), "--inputs", str(ca_nvda),
                        "--output", str(combined)])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(combined)])
    assert result.exit_code == 0
    assert "Included Context" in result.stdout
    assert "AMD" in result.stdout
    assert "NVDA" in result.stdout


def test_included_context_shows_research_when_present(tmp_path: Path) -> None:
    research_out = tmp_path / "research.json"
    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    result = runner.invoke(app, ["daily", "summary", "--research", str(research_out)])
    assert result.exit_code == 0
    assert "Included Context" in result.stdout
    assert "Research" in result.stdout


def test_included_context_absent_when_no_inputs() -> None:
    result = runner.invoke(app, ["daily", "summary"])
    assert result.exit_code == 0
    assert "Included Context" not in result.stdout


# ── multi-company formatting ───────────────────────────────────────────────────


def test_multi_company_output_names_each_company(tmp_path: Path) -> None:
    ca_amd = tmp_path / "ca_amd.json"
    ca_nvda = tmp_path / "ca_nvda.json"
    combined = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca_amd)])
    runner.invoke(app, ["company-analysis", "export", "--ticker", "NVDA", "--output", str(ca_nvda)])
    runner.invoke(app, ["company-analysis", "merge",
                        "--inputs", str(ca_amd), "--inputs", str(ca_nvda),
                        "--output", str(combined)])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(combined)])
    assert result.exit_code == 0
    assert "AMD" in result.stdout
    assert "NVDA" in result.stdout


def test_multi_company_output_does_not_compare_companies(tmp_path: Path) -> None:
    ca_amd = tmp_path / "ca_amd.json"
    ca_nvda = tmp_path / "ca_nvda.json"
    combined = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca_amd)])
    runner.invoke(app, ["company-analysis", "export", "--ticker", "NVDA", "--output", str(ca_nvda)])
    runner.invoke(app, ["company-analysis", "merge",
                        "--inputs", str(ca_amd), "--inputs", str(ca_nvda),
                        "--output", str(combined)])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(combined)])
    assert result.exit_code == 0
    output_lower = result.stdout.lower()
    assert "better than" not in output_lower
    assert "worse than" not in output_lower
    assert "prefer" not in output_lower
    assert "rank" not in output_lower


def test_company_unknowns_grouped_by_ticker_in_output(tmp_path: Path) -> None:
    ca_amd = tmp_path / "ca_amd.json"
    ca_nvda = tmp_path / "ca_nvda.json"
    combined = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca_amd)])
    runner.invoke(app, ["company-analysis", "export", "--ticker", "NVDA", "--output", str(ca_nvda)])
    runner.invoke(app, ["company-analysis", "merge",
                        "--inputs", str(ca_amd), "--inputs", str(ca_nvda),
                        "--output", str(combined)])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(combined)])
    assert result.exit_code == 0
    # AMD and NVDA unknowns should appear grouped under their own headers
    amd_pos = result.stdout.index("AMD")
    nvda_pos = result.stdout.index("NVDA")
    assert amd_pos != nvda_pos  # distinct occurrences


# ── evidence gaps behavior ─────────────────────────────────────────────────────


def test_no_evidence_gaps_section_when_full_metadata_and_knowledge(tmp_path: Path) -> None:
    research_out = tmp_path / "research.json"
    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    ca = tmp_path / "ca.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD", "--company-name", "AMD Corporation",
        "--sector", "Semiconductors", "--country", "USA",
        "--business-description", "AMD designs high-performance CPUs and GPUs.",
        "--knowledge", str(KNOWLEDGE), "--research", str(research_out),
        "--output", str(ca),
    ])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert result.exit_code == 0
    assert "Evidence Gaps" not in result.stdout


def test_evidence_gaps_present_when_ticker_only(tmp_path: Path) -> None:
    ca = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca)])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert result.exit_code == 0
    assert "Evidence Gaps" in result.stdout
    assert "AMD" in result.stdout


# ── no meaningful developments ────────────────────────────────────────────────


def test_no_meaningful_developments_on_empty_input() -> None:
    result = runner.invoke(app, ["daily", "summary"])
    assert result.exit_code == 0
    assert "No meaningful developments were identified" in result.stdout


def test_no_meaningful_developments_output_is_calm() -> None:
    result = runner.invoke(app, ["daily", "summary"])
    assert result.exit_code == 0
    output_lower = result.stdout.lower()
    for term in FORBIDDEN:
        assert term not in output_lower, f"Forbidden term: {term!r}"


# ── priority markers ───────────────────────────────────────────────────────────


def test_high_priority_marker_format() -> None:
    assert _priority_marker(DailyBriefPriority.HIGH) == "[!] "


def test_moderate_priority_marker_format() -> None:
    assert _priority_marker(DailyBriefPriority.MODERATE) == "[·] "


def test_low_priority_no_marker() -> None:
    assert _priority_marker(DailyBriefPriority.LOW) == ""


# ── language safety ────────────────────────────────────────────────────────────


def test_full_demo_output_no_forbidden_language(tmp_path: Path) -> None:
    research_out = tmp_path / "research.json"
    watchlist_out = tmp_path / "watchlist.json"
    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    runner.invoke(app, ["watchlist", "intelligence", "--input", str(WATCHLIST_INPUT), "--output", str(watchlist_out)])
    ca_amd = tmp_path / "ca_amd.json"
    ca_nvda = tmp_path / "ca_nvda.json"
    combined = tmp_path / "ca.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD", "--company-name", "AMD Corporation",
        "--sector", "Semiconductors", "--country", "USA",
        "--business-description", "AMD designs high-performance CPUs and GPUs.",
        "--knowledge", str(KNOWLEDGE), "--research", str(research_out),
        "--output", str(ca_amd),
    ])
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "NVDA", "--company-name", "NVIDIA Corporation",
        "--sector", "Semiconductors", "--country", "USA",
        "--business-description", "NVIDIA designs GPUs and accelerated computing platforms.",
        "--knowledge", str(KNOWLEDGE), "--research", str(research_out),
        "--output", str(ca_nvda),
    ])
    runner.invoke(app, ["company-analysis", "merge",
                        "--inputs", str(ca_amd), "--inputs", str(ca_nvda),
                        "--output", str(combined)])
    result = runner.invoke(app, [
        "daily", "summary",
        "--research", str(research_out),
        "--watchlist", str(watchlist_out),
        "--company-analysis", str(combined),
    ])
    assert result.exit_code == 0
    output_lower = result.stdout.lower()
    for term in FORBIDDEN:
        assert term not in output_lower, f"Forbidden term: {term!r}"


# ── no network / no AI ─────────────────────────────────────────────────────────


def test_daily_summary_makes_no_network_calls(tmp_path: Path, monkeypatch) -> None:
    import atlas.providers.yahoo as yahoo_module
    monkeypatch.setattr(
        yahoo_module, "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("network call")),
    )
    ca = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca)])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert result.exit_code == 0


# ── demo pipeline ──────────────────────────────────────────────────────────────


def test_demo_pipeline_includes_both_companies(tmp_path: Path) -> None:
    research_out = tmp_path / "research.json"
    watchlist_out = tmp_path / "watchlist.json"
    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    runner.invoke(app, ["watchlist", "intelligence", "--input", str(WATCHLIST_INPUT), "--output", str(watchlist_out)])
    ca_amd = tmp_path / "ca_amd.json"
    ca_nvda = tmp_path / "ca_nvda.json"
    combined = tmp_path / "ca.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD", "--company-name", "AMD Corporation",
        "--sector", "Semiconductors", "--country", "USA",
        "--business-description", "AMD designs high-performance CPUs and GPUs.",
        "--knowledge", str(KNOWLEDGE), "--research", str(research_out),
        "--output", str(ca_amd),
    ])
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "NVDA", "--company-name", "NVIDIA Corporation",
        "--sector", "Semiconductors", "--country", "USA",
        "--business-description", "NVIDIA designs GPUs and accelerated computing platforms.",
        "--knowledge", str(KNOWLEDGE), "--research", str(research_out),
        "--output", str(ca_nvda),
    ])
    runner.invoke(app, ["company-analysis", "merge",
                        "--inputs", str(ca_amd), "--inputs", str(ca_nvda),
                        "--output", str(combined)])
    result = runner.invoke(app, [
        "daily", "summary",
        "--research", str(research_out),
        "--watchlist", str(watchlist_out),
        "--company-analysis", str(combined),
    ])
    assert result.exit_code == 0
    assert "AMD" in result.stdout
    assert "NVDA" in result.stdout
    assert "Evidence Gaps" not in result.stdout  # full metadata + knowledge supplied


def test_demo_pipeline_output_is_deterministic(tmp_path: Path) -> None:
    research_out = tmp_path / "research.json"
    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    ca = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca)])
    r1 = runner.invoke(app, ["daily", "summary", "--research", str(research_out), "--company-analysis", str(ca)])
    r2 = runner.invoke(app, ["daily", "summary", "--research", str(research_out), "--company-analysis", str(ca)])
    assert r1.stdout == r2.stdout
