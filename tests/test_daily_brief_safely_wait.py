"""Sprint 64: Daily Brief 'What Can Safely Wait' section tests.

Verifies that:
- LOW priority items from detail sections are collected in What Can Safely Wait
- HIGH and MODERATE priority items do not appear there
- The section is omitted when no detail-section LOW items exist
- No-input behavior is preserved
- Multi-company behavior is deterministic and non-comparative
- Evidence gaps, Unresolved Questions, and What Deserves Attention are unchanged
- No recommendation language, no network calls
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from atlas.capabilities.daily_brief import (
    DailyBriefCapability,
    DailyBriefInput,
    DailyBriefPriority,
)
from atlas.capabilities.daily_brief.engine import (
    _collect_safely_wait_items,
    render_daily_brief_report,
)
from atlas.capabilities.daily_brief.models import (
    DailyBriefItem,
    DailyBriefSection,
    DailyBriefSummary,
    DailyBriefReport,
)
from atlas.cli.main import app

runner = CliRunner()

DEMO_DIR = Path(__file__).parent.parent / "examples" / "daily_brief_demo"
KNOWLEDGE = DEMO_DIR / "knowledge.json"
RESEARCH_INPUT = DEMO_DIR / "research_input.json"
WATCHLIST_INPUT = DEMO_DIR / "watchlist_input.json"

FORBIDDEN = (
    "buy", "sell", "strong buy", "strong sell", "urgent", "must act",
    "guaranteed", "risk-free", "price target", "outperform", "market-beating",
    "better investment", "worse investment", "entry", "exit",
)


# ── helpers ────────────────────────────────────────────────────────────────────


def _make_report_obj(ticker: str, unknown_count: int = 0) -> object:
    unknowns = tuple(
        SimpleNamespace(title=f"Unknown {i}", detail="") for i in range(unknown_count)
    )
    return SimpleNamespace(
        company=SimpleNamespace(ticker=ticker, name=ticker, id=ticker.lower()),
        unknowns=unknowns,
        evidence_links=(),
    )


def _make_brief_report(
    *,
    sections: tuple[DailyBriefSection, ...] = (),
    unknowns: tuple = (),
    evidence_gaps: tuple = (),
    next_research_steps: tuple = (),
) -> DailyBriefReport:
    return DailyBriefReport(
        title="Atlas Daily Brief",
        summary=DailyBriefSummary(
            bottom_line="Test.",
            overall_priority=DailyBriefPriority.LOW,
            item_count=0,
            has_meaningful_developments=False,
        ),
        sections=sections,
        unknowns=unknowns,
        evidence_gaps=evidence_gaps,
        next_research_steps=next_research_steps,
    )


def _item(title: str, detail: str, priority: DailyBriefPriority) -> DailyBriefItem:
    return DailyBriefItem(title=title, detail=detail, priority=priority)


# ── _collect_safely_wait_items unit tests ──────────────────────────────────────


def test_low_items_from_detail_sections_collected() -> None:
    low_item = _item("AMD", "Context available.", DailyBriefPriority.LOW)
    section = DailyBriefSection(title="Company Analysis Context", items=(low_item,))
    report = _make_brief_report(sections=(section,))
    result = _collect_safely_wait_items(report)
    assert low_item in result


def test_moderate_items_not_collected() -> None:
    mod_item = _item("AMD", "Observations.", DailyBriefPriority.MODERATE)
    section = DailyBriefSection(title="Company Analysis Context", items=(mod_item,))
    report = _make_brief_report(sections=(section,))
    result = _collect_safely_wait_items(report)
    assert mod_item not in result


def test_high_items_not_collected() -> None:
    high_item = _item("Concentration", "High concentration.", DailyBriefPriority.HIGH)
    section = DailyBriefSection(title="Portfolio Context", items=(high_item,))
    report = _make_brief_report(sections=(section,))
    result = _collect_safely_wait_items(report)
    assert high_item not in result


def test_what_deserves_attention_items_skipped() -> None:
    low_item = _item("Knowledge context", "9 nodes available.", DailyBriefPriority.LOW)
    section = DailyBriefSection(title="What Deserves Attention", items=(low_item,))
    report = _make_brief_report(sections=(section,))
    result = _collect_safely_wait_items(report)
    assert result == []


def test_empty_when_no_low_items_in_detail_sections() -> None:
    mod_item = _item("AMD", "Observations.", DailyBriefPriority.MODERATE)
    section = DailyBriefSection(title="Company Analysis Context", items=(mod_item,))
    report = _make_brief_report(sections=(section,))
    assert _collect_safely_wait_items(report) == []


def test_items_collected_in_section_order() -> None:
    item_a = _item("AMD", "Low.", DailyBriefPriority.LOW)
    item_b = _item("Steps", "Low.", DailyBriefPriority.LOW)
    sec_a = DailyBriefSection(title="Company Analysis Context", items=(item_a,))
    sec_b = DailyBriefSection(title="Watchlist Context", items=(item_b,))
    report = _make_brief_report(sections=(sec_a, sec_b))
    result = _collect_safely_wait_items(report)
    assert result == [item_a, item_b]


def test_mixed_priority_section_only_low_collected() -> None:
    low = _item("L", "low", DailyBriefPriority.LOW)
    mod = _item("M", "mod", DailyBriefPriority.MODERATE)
    section = DailyBriefSection(title="Watchlist Context", items=(mod, low))
    report = _make_brief_report(sections=(section,))
    result = _collect_safely_wait_items(report)
    assert result == [low]


# ── rendered output: section present / absent ──────────────────────────────────


def test_safely_wait_section_present_when_clean_company_reports(tmp_path: Path) -> None:
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
    assert "What Can Safely Wait" in result.stdout


def test_safely_wait_section_absent_when_company_has_unknowns(tmp_path: Path) -> None:
    ca = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca)])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert result.exit_code == 0
    # AMD ticker-only has unknowns (MODERATE) — no LOW company items → section absent
    assert "What Can Safely Wait" not in result.stdout


def test_safely_wait_absent_on_empty_input() -> None:
    result = runner.invoke(app, ["daily", "summary"])
    assert result.exit_code == 0
    assert "What Can Safely Wait" not in result.stdout


# ── no-input behavior preserved ───────────────────────────────────────────────


def test_no_input_still_shows_no_meaningful_developments() -> None:
    result = runner.invoke(app, ["daily", "summary"])
    assert result.exit_code == 0
    assert "No meaningful developments were identified" in result.stdout


# ── multi-company behavior ─────────────────────────────────────────────────────


def test_multi_company_clean_reports_appear_in_safely_wait(tmp_path: Path) -> None:
    research_out = tmp_path / "research.json"
    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
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
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(combined)])
    assert result.exit_code == 0
    assert "What Can Safely Wait" in result.stdout
    safely_wait_start = result.stdout.index("What Can Safely Wait")
    safely_wait_block = result.stdout[safely_wait_start:]
    assert "AMD" in safely_wait_block
    assert "NVDA" in safely_wait_block


def test_multi_company_safely_wait_does_not_compare_companies(tmp_path: Path) -> None:
    ca_amd = tmp_path / "ca_amd.json"
    ca_nvda = tmp_path / "ca_nvda.json"
    combined = tmp_path / "ca.json"
    research_out = tmp_path / "research.json"
    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD", "--company-name", "AMD Corporation",
        "--sector", "Semiconductors", "--country", "USA",
        "--business-description", "AMD designs CPUs.",
        "--knowledge", str(KNOWLEDGE), "--research", str(research_out),
        "--output", str(ca_amd),
    ])
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "NVDA", "--company-name", "NVIDIA Corporation",
        "--sector", "Semiconductors", "--country", "USA",
        "--business-description", "NVDA designs GPUs.",
        "--knowledge", str(KNOWLEDGE), "--research", str(research_out),
        "--output", str(ca_nvda),
    ])
    runner.invoke(app, ["company-analysis", "merge",
                        "--inputs", str(ca_amd), "--inputs", str(ca_nvda),
                        "--output", str(combined)])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(combined)])
    assert result.exit_code == 0
    output_lower = result.stdout.lower()
    assert "better" not in output_lower or "better than" not in output_lower
    assert "worse" not in output_lower
    assert "prefer" not in output_lower


def test_multi_company_safely_wait_is_deterministic(tmp_path: Path) -> None:
    ca_amd = tmp_path / "ca_amd.json"
    ca_nvda = tmp_path / "ca_nvda.json"
    combined = tmp_path / "ca.json"
    research_out = tmp_path / "research.json"
    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD", "--company-name", "AMD Corporation",
        "--sector", "Semiconductors", "--country", "USA",
        "--business-description", "AMD designs CPUs.",
        "--knowledge", str(KNOWLEDGE), "--research", str(research_out),
        "--output", str(ca_amd),
    ])
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "NVDA", "--company-name", "NVIDIA Corporation",
        "--sector", "Semiconductors", "--country", "USA",
        "--business-description", "NVDA designs GPUs.",
        "--knowledge", str(KNOWLEDGE), "--research", str(research_out),
        "--output", str(ca_nvda),
    ])
    runner.invoke(app, ["company-analysis", "merge",
                        "--inputs", str(ca_amd), "--inputs", str(ca_nvda),
                        "--output", str(combined)])
    r1 = runner.invoke(app, ["daily", "summary", "--company-analysis", str(combined)])
    r2 = runner.invoke(app, ["daily", "summary", "--company-analysis", str(combined)])
    assert r1.stdout == r2.stdout


# ── section ordering ───────────────────────────────────────────────────────────


def test_safely_wait_appears_after_next_research_steps(tmp_path: Path) -> None:
    research_out = tmp_path / "research.json"
    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    ca = tmp_path / "ca.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD", "--company-name", "AMD Corporation",
        "--sector", "Semiconductors", "--country", "USA",
        "--business-description", "AMD designs CPUs.",
        "--knowledge", str(KNOWLEDGE), "--research", str(research_out),
        "--output", str(ca),
    ])
    result = runner.invoke(app, [
        "daily", "summary", "--research", str(research_out), "--company-analysis", str(ca),
    ])
    assert result.exit_code == 0
    assert "What Can Safely Wait" in result.stdout
    assert "Suggested Next Research Steps" in result.stdout
    assert result.stdout.index("Suggested Next Research Steps") < result.stdout.index("What Can Safely Wait")


def test_safely_wait_appears_before_research_framing(tmp_path: Path) -> None:
    research_out = tmp_path / "research.json"
    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    ca = tmp_path / "ca.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD", "--company-name", "AMD Corporation",
        "--sector", "Semiconductors", "--country", "USA",
        "--business-description", "AMD designs CPUs.",
        "--knowledge", str(KNOWLEDGE), "--research", str(research_out),
        "--output", str(ca),
    ])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert result.exit_code == 0
    assert result.stdout.index("What Can Safely Wait") < result.stdout.index("Research Framing")


# ── existing sections unaffected ───────────────────────────────────────────────


def test_what_deserves_attention_unchanged(tmp_path: Path) -> None:
    ca = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca)])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert result.exit_code == 0
    assert "What Deserves Attention" in result.stdout


def test_evidence_gaps_unaffected(tmp_path: Path) -> None:
    ca = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca)])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert result.exit_code == 0
    assert "Evidence Gaps" in result.stdout
    assert "What Can Safely Wait" not in result.stdout  # ticker-only has unknowns → no safely wait


def test_no_evidence_gaps_with_full_metadata_and_safely_wait(tmp_path: Path) -> None:
    research_out = tmp_path / "research.json"
    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    ca = tmp_path / "ca.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD", "--company-name", "AMD Corporation",
        "--sector", "Semiconductors", "--country", "USA",
        "--business-description", "AMD designs CPUs.",
        "--knowledge", str(KNOWLEDGE), "--research", str(research_out),
        "--output", str(ca),
    ])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert result.exit_code == 0
    assert "Evidence Gaps" not in result.stdout
    assert "What Can Safely Wait" in result.stdout


# ── watchlist LOW items ────────────────────────────────────────────────────────


def test_watchlist_suggested_steps_appear_in_safely_wait(tmp_path: Path) -> None:
    watchlist_out = tmp_path / "watchlist.json"
    runner.invoke(app, ["watchlist", "intelligence", "--input", str(WATCHLIST_INPUT), "--output", str(watchlist_out)])
    result = runner.invoke(app, ["daily", "summary", "--watchlist", str(watchlist_out)])
    assert result.exit_code == 0
    # Suggested research steps are LOW priority → should be in safely wait
    assert "What Can Safely Wait" in result.stdout
    safely_wait_start = result.stdout.index("What Can Safely Wait")
    safely_wait_block = result.stdout[safely_wait_start:]
    assert "Suggested research steps" in safely_wait_block


# ── language safety ────────────────────────────────────────────────────────────


def test_no_forbidden_language_in_safely_wait_output(tmp_path: Path) -> None:
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
        "--business-description", "AMD designs CPUs.",
        "--knowledge", str(KNOWLEDGE), "--research", str(research_out),
        "--output", str(ca_amd),
    ])
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "NVDA", "--company-name", "NVIDIA Corporation",
        "--sector", "Semiconductors", "--country", "USA",
        "--business-description", "NVDA designs GPUs.",
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


# ── no network calls ───────────────────────────────────────────────────────────


def test_no_network_calls_when_safely_wait_present(tmp_path: Path, monkeypatch) -> None:
    import atlas.providers.yahoo as yahoo_module
    monkeypatch.setattr(
        yahoo_module, "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("network call")),
    )
    research_out = tmp_path / "research.json"
    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    ca = tmp_path / "ca.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD", "--company-name", "AMD Corporation",
        "--sector", "Semiconductors", "--country", "USA",
        "--business-description", "AMD designs CPUs.",
        "--knowledge", str(KNOWLEDGE), "--research", str(research_out),
        "--output", str(ca),
    ])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert result.exit_code == 0
    assert "What Can Safely Wait" in result.stdout
