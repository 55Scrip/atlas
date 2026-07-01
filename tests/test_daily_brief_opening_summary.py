"""Sprint 63: Daily Brief Opening Summary alignment tests.

Verifies that the 'What Deserves Attention' section surfaces company analysis
signals so the Opening Summary is consistent with what the brief contains.

Key invariants:
- No-input behavior is unchanged.
- Company reports with unknowns → MODERATE item in What Deserves Attention.
- Company reports without unknowns → LOW item in What Deserves Attention.
- Multi-company behavior is deterministic and non-comparative.
- No recommendation language, no network calls.
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
    _company_analysis_opening_item,
    render_daily_brief_report,
)
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
    "entry",
    "exit",
)


# ── helpers ────────────────────────────────────────────────────────────────────


def _make_report(ticker: str, unknown_count: int = 0) -> object:
    unknowns = tuple(
        SimpleNamespace(title=f"Unknown {i}", detail="") for i in range(unknown_count)
    )
    return SimpleNamespace(
        company=SimpleNamespace(ticker=ticker, name=ticker, id=ticker.lower()),
        unknowns=unknowns,
        evidence_links=(),
    )


# ── _company_analysis_opening_item unit tests ──────────────────────────────────


def test_single_report_with_unknowns_is_moderate() -> None:
    item = _company_analysis_opening_item((_make_report("AMD", unknown_count=2),))
    assert item.priority == DailyBriefPriority.MODERATE


def test_single_report_without_unknowns_is_low() -> None:
    item = _company_analysis_opening_item((_make_report("AMD", unknown_count=0),))
    assert item.priority == DailyBriefPriority.LOW


def test_single_report_with_unknowns_detail_mentions_observations() -> None:
    item = _company_analysis_opening_item((_make_report("AMD", unknown_count=1),))
    assert "observations" in item.detail.lower() or "review" in item.detail.lower()


def test_single_report_without_unknowns_detail_mentions_available() -> None:
    item = _company_analysis_opening_item((_make_report("AMD", unknown_count=0),))
    assert "available" in item.detail.lower() or "review" in item.detail.lower()


def test_multi_report_partial_unknowns_is_moderate() -> None:
    reports = (_make_report("AMD", unknown_count=2), _make_report("NVDA", unknown_count=0))
    item = _company_analysis_opening_item(reports)
    assert item.priority == DailyBriefPriority.MODERATE


def test_multi_report_no_unknowns_is_low() -> None:
    reports = (_make_report("AMD", unknown_count=0), _make_report("NVDA", unknown_count=0))
    item = _company_analysis_opening_item(reports)
    assert item.priority == DailyBriefPriority.LOW


def test_multi_report_detail_mentions_count() -> None:
    reports = (_make_report("AMD", unknown_count=1), _make_report("NVDA", unknown_count=0))
    item = _company_analysis_opening_item(reports)
    assert "1" in item.detail and "2" in item.detail


def test_item_title_is_company_analysis() -> None:
    item = _company_analysis_opening_item((_make_report("AMD"),))
    assert item.title == "Company analysis"


# ── What Deserves Attention section ───────────────────────────────────────────


def test_company_reports_with_unknowns_appear_in_what_deserves_attention() -> None:
    brief_input = DailyBriefInput(
        company_reports=(_make_report("AMD", unknown_count=3),)
    )
    report = DailyBriefCapability().generate(brief_input)
    attention = next(s for s in report.sections if s.title == "What Deserves Attention")
    titles = [item.title for item in attention.items]
    assert "Company analysis" in titles


def test_company_reports_without_unknowns_do_not_appear_in_what_deserves_attention() -> None:
    # Sprint 65: LOW priority company analysis (no unknowns) should not be promoted
    # into What Deserves Attention — it belongs in What Can Safely Wait instead.
    brief_input = DailyBriefInput(
        company_reports=(_make_report("AMD", unknown_count=0),)
    )
    report = DailyBriefCapability().generate(brief_input)
    attention = next(s for s in report.sections if s.title == "What Deserves Attention")
    titles = [item.title for item in attention.items]
    assert "Company analysis" not in titles


def test_company_with_unknowns_raises_attention_priority_to_moderate() -> None:
    brief_input = DailyBriefInput(
        company_reports=(_make_report("AMD", unknown_count=2),)
    )
    report = DailyBriefCapability().generate(brief_input)
    attention = next(s for s in report.sections if s.title == "What Deserves Attention")
    ca_item = next(i for i in attention.items if i.title == "Company analysis")
    assert ca_item.priority == DailyBriefPriority.MODERATE


def test_fallback_status_item_when_only_low_priority_reports_present() -> None:
    # Sprint 65: when company reports exist but all are LOW priority (no unknowns),
    # the opening section shows a calm fallback — not "No meaningful developments"
    # (which implies no inputs at all) but "no immediate attention" phrasing.
    brief_input = DailyBriefInput(
        company_reports=(_make_report("AMD", unknown_count=0),)
    )
    report = DailyBriefCapability().generate(brief_input)
    attention = next(s for s in report.sections if s.title == "What Deserves Attention")
    status_items = [i for i in attention.items if i.title == "Status"]
    assert status_items  # fallback fires when no HIGH/MODERATE items
    assert "No meaningful developments" not in status_items[0].detail
    assert "immediate attention" in status_items[0].detail.lower()


def test_what_deserves_attention_not_no_developments_when_company_reports_present() -> None:
    brief_input = DailyBriefInput(
        company_reports=(_make_report("AMD", unknown_count=0),)
    )
    report = DailyBriefCapability().generate(brief_input)
    rendered = render_daily_brief_report(report)
    # The attention section should not show "No meaningful developments" when
    # company reports are present
    attention_start = rendered.index("What Deserves Attention")
    next_sep = rendered.find("─────", attention_start + 1)
    attention_block = rendered[attention_start:next_sep] if next_sep != -1 else rendered[attention_start:]
    assert "No meaningful developments" not in attention_block


# ── Opening Summary consistency ────────────────────────────────────────────────


def test_opening_summary_mentions_company_reports(tmp_path: Path) -> None:
    ca = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca)])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert result.exit_code == 0
    # Opening Summary (before first separator after it) should mention company analysis
    lines = result.stdout.splitlines()
    summary_lines = []
    in_summary = False
    for line in lines:
        if line.strip() == "Opening Summary":
            in_summary = True
            continue
        if in_summary and line.startswith("─"):
            break
        if in_summary:
            summary_lines.append(line)
    summary_text = " ".join(summary_lines).lower()
    assert "company analysis" in summary_text or "report" in summary_text


def test_opening_summary_consistent_with_what_deserves_attention(tmp_path: Path) -> None:
    ca = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca)])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert result.exit_code == 0
    # If What Deserves Attention has a moderate company analysis item, Overall priority
    # should not be low
    assert "overall priority: low" not in result.stdout.lower()


def test_opening_summary_not_no_developments_when_company_reports_present(tmp_path: Path) -> None:
    ca = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca)])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert result.exit_code == 0
    # The What Deserves Attention section should not show the "no developments"
    # fallback when a company analysis report is present
    assert "Status: No meaningful developments" not in result.stdout


# ── no-input behavior preserved ───────────────────────────────────────────────


def test_no_input_still_shows_no_meaningful_developments() -> None:
    result = runner.invoke(app, ["daily", "summary"])
    assert result.exit_code == 0
    assert "No meaningful developments were identified" in result.stdout


def test_no_input_priority_is_low() -> None:
    result = runner.invoke(app, ["daily", "summary"])
    assert result.exit_code == 0
    assert "overall priority: low" in result.stdout.lower()


# ── multi-company behavior ─────────────────────────────────────────────────────


def test_multi_company_with_unknowns_opening_item_is_moderate() -> None:
    reports = (
        _make_report("AMD", unknown_count=2),
        _make_report("NVDA", unknown_count=1),
    )
    brief_input = DailyBriefInput(company_reports=reports)
    report = DailyBriefCapability().generate(brief_input)
    attention = next(s for s in report.sections if s.title == "What Deserves Attention")
    ca_item = next(i for i in attention.items if i.title == "Company analysis")
    assert ca_item.priority == DailyBriefPriority.MODERATE


def test_multi_company_no_unknowns_not_in_what_deserves_attention() -> None:
    # Sprint 65: LOW priority company analysis (no unknowns) must not appear
    # in What Deserves Attention — it belongs in What Can Safely Wait instead.
    reports = (
        _make_report("AMD", unknown_count=0),
        _make_report("NVDA", unknown_count=0),
    )
    brief_input = DailyBriefInput(company_reports=reports)
    report = DailyBriefCapability().generate(brief_input)
    attention = next(s for s in report.sections if s.title == "What Deserves Attention")
    ca_items = [i for i in attention.items if i.title == "Company analysis"]
    assert not ca_items  # LOW company analysis not in What Deserves Attention
    # _company_analysis_opening_item still produces LOW for this case (unit-testable separately)
    assert _company_analysis_opening_item(reports).priority == DailyBriefPriority.LOW


def test_multi_company_opening_is_deterministic() -> None:
    brief_input = DailyBriefInput(
        company_reports=(
            _make_report("AMD", unknown_count=2),
            _make_report("NVDA", unknown_count=0),
        )
    )
    r1 = render_daily_brief_report(DailyBriefCapability().generate(brief_input))
    r2 = render_daily_brief_report(DailyBriefCapability().generate(brief_input))
    assert r1 == r2


def test_multi_company_does_not_compare_companies(tmp_path: Path) -> None:
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
    assert "better" not in output_lower or "better than" not in output_lower
    assert "worse" not in output_lower
    assert "prefer" not in output_lower
    assert "rank" not in output_lower


# ── evidence gaps behavior preserved ──────────────────────────────────────────


def test_no_evidence_gaps_when_full_metadata_and_knowledge(tmp_path: Path) -> None:
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


def test_evidence_gaps_present_with_ticker_only(tmp_path: Path) -> None:
    ca = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca)])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert result.exit_code == 0
    assert "Evidence Gaps" in result.stdout


# ── language safety ────────────────────────────────────────────────────────────


def test_no_forbidden_language_ticker_only(tmp_path: Path) -> None:
    ca = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca)])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert result.exit_code == 0
    output_lower = result.stdout.lower()
    for term in FORBIDDEN:
        assert term not in output_lower, f"Forbidden term found: {term!r}"


def test_no_forbidden_language_full_demo(tmp_path: Path) -> None:
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
        assert term not in output_lower, f"Forbidden term found: {term!r}"


# ── no network calls ───────────────────────────────────────────────────────────


def test_no_network_calls_with_company_analysis(tmp_path: Path, monkeypatch) -> None:
    import atlas.providers.yahoo as yahoo_module
    monkeypatch.setattr(
        yahoo_module, "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("network call")),
    )
    ca = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca)])
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert result.exit_code == 0
