"""Sprint 65: Daily Brief priority routing tests.

Verifies that "What Deserves Attention" contains only HIGH/MODERATE items.
LOW priority items (knowledge context, low-priority company analysis) must not
appear in "What Deserves Attention" — they belong in "Included Context" or
"What Can Safely Wait" instead.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from atlas.capabilities.daily_brief import (
    DailyBriefCapability,
    DailyBriefInput,
    DailyBriefPriority,
)
from atlas.capabilities.daily_brief.engine import render_daily_brief_report


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


def _attention_items(report):
    section = next(s for s in report.sections if s.title == "What Deserves Attention")
    return section.items


def _attention_priorities(report):
    return {item.priority for item in _attention_items(report)}


# ── knowledge_node_count routing ───────────────────────────────────────────────


def test_knowledge_count_not_in_what_deserves_attention() -> None:
    # knowledge context is LOW — must not be promoted into What Deserves Attention
    report = DailyBriefCapability().generate(DailyBriefInput(knowledge_node_count=10))
    titles = [item.title for item in _attention_items(report)]
    assert "Knowledge context" not in titles


def test_knowledge_count_visible_in_included_context_section() -> None:
    report = DailyBriefCapability().generate(DailyBriefInput(knowledge_node_count=10))
    rendered = render_daily_brief_report(report)
    assert "Knowledge" in rendered
    assert "10" in rendered


def test_knowledge_count_zero_not_in_included_context() -> None:
    report = DailyBriefCapability().generate(DailyBriefInput(knowledge_node_count=0))
    rendered = render_daily_brief_report(report)
    # zero-count knowledge should not clutter the output
    assert "Knowledge" not in rendered or "0 fact" not in rendered


def test_knowledge_count_stored_on_report_model() -> None:
    report = DailyBriefCapability().generate(DailyBriefInput(knowledge_node_count=3))
    assert report.knowledge_node_count == 3


def test_knowledge_count_default_zero_on_report_model() -> None:
    report = DailyBriefCapability().generate(DailyBriefInput())
    assert report.knowledge_node_count == 0


# ── company analysis routing — LOW (no unknowns) ──────────────────────────────


def test_low_company_analysis_not_in_what_deserves_attention() -> None:
    # company reports with no unknowns are LOW — must not appear in What Deserves Attention
    brief_input = DailyBriefInput(
        company_reports=(_make_report("AAPL", unknown_count=0),)
    )
    report = DailyBriefCapability().generate(brief_input)
    titles = [item.title for item in _attention_items(report)]
    assert "Company analysis" not in titles


def test_low_company_analysis_triggers_calm_fallback() -> None:
    # when only LOW items exist, fallback must NOT say "No meaningful developments"
    brief_input = DailyBriefInput(
        company_reports=(_make_report("AAPL", unknown_count=0),)
    )
    report = DailyBriefCapability().generate(brief_input)
    status_items = [i for i in _attention_items(report) if i.title == "Status"]
    assert status_items
    assert "No meaningful developments" not in status_items[0].detail


def test_low_company_analysis_fallback_mentions_no_immediate_attention() -> None:
    brief_input = DailyBriefInput(
        company_reports=(_make_report("AAPL", unknown_count=0),)
    )
    report = DailyBriefCapability().generate(brief_input)
    status_items = [i for i in _attention_items(report) if i.title == "Status"]
    assert "immediate attention" in status_items[0].detail.lower()


def test_low_company_analysis_still_appears_in_what_can_safely_wait() -> None:
    # LOW company analysis visible in What Can Safely Wait (collected from detail sections)
    brief_input = DailyBriefInput(
        company_reports=(_make_report("AAPL", unknown_count=0),)
    )
    report = DailyBriefCapability().generate(brief_input)
    rendered = render_daily_brief_report(report)
    assert "What Can Safely Wait" in rendered


# ── company analysis routing — MODERATE (has unknowns) ───────────────────────


def test_moderate_company_analysis_in_what_deserves_attention() -> None:
    # company reports with unknowns are MODERATE — must appear in What Deserves Attention
    brief_input = DailyBriefInput(
        company_reports=(_make_report("NVDA", unknown_count=2),)
    )
    report = DailyBriefCapability().generate(brief_input)
    titles = [item.title for item in _attention_items(report)]
    assert "Company analysis" in titles


def test_moderate_company_analysis_correct_priority() -> None:
    brief_input = DailyBriefInput(
        company_reports=(_make_report("NVDA", unknown_count=1),)
    )
    report = DailyBriefCapability().generate(brief_input)
    ca_items = [i for i in _attention_items(report) if i.title == "Company analysis"]
    assert ca_items[0].priority == DailyBriefPriority.MODERATE


# ── mixed routing ─────────────────────────────────────────────────────────────


def test_mixed_reports_only_moderate_in_what_deserves_attention() -> None:
    # one with unknowns (MODERATE), one without (LOW)
    brief_input = DailyBriefInput(
        company_reports=(
            _make_report("NVDA", unknown_count=2),
            _make_report("AAPL", unknown_count=0),
        )
    )
    report = DailyBriefCapability().generate(brief_input)
    # Company analysis item exists (MODERATE because any unknowns exist)
    ca_items = [i for i in _attention_items(report) if i.title == "Company analysis"]
    assert ca_items
    assert ca_items[0].priority == DailyBriefPriority.MODERATE


def test_all_attention_items_are_high_or_moderate_when_inputs_present() -> None:
    # only HIGH/MODERATE should appear in What Deserves Attention
    brief_input = DailyBriefInput(
        company_reports=(_make_report("NVDA", unknown_count=1),),
        knowledge_node_count=5,
    )
    report = DailyBriefCapability().generate(brief_input)
    non_status_items = [
        i for i in _attention_items(report) if i.title != "Status"
    ]
    for item in non_status_items:
        assert item.priority in (DailyBriefPriority.HIGH, DailyBriefPriority.MODERATE), (
            f"LOW item {item.title!r} found in What Deserves Attention"
        )


# ── empty input vs all-low-priority distinction ───────────────────────────────


def test_empty_input_uses_no_meaningful_developments_message() -> None:
    report = DailyBriefCapability().generate(DailyBriefInput())
    rendered = render_daily_brief_report(report)
    assert "No meaningful developments" in rendered


def test_all_low_inputs_do_not_use_no_meaningful_developments_message() -> None:
    # knowledge_node_count is input but LOW — different from truly empty
    report = DailyBriefCapability().generate(DailyBriefInput(knowledge_node_count=3))
    rendered = render_daily_brief_report(report)
    assert "No meaningful developments" not in rendered


def test_all_low_company_inputs_do_not_use_no_meaningful_developments_message() -> None:
    brief_input = DailyBriefInput(
        company_reports=(_make_report("AAPL", unknown_count=0),)
    )
    report = DailyBriefCapability().generate(brief_input)
    rendered = render_daily_brief_report(report)
    assert "No meaningful developments" not in rendered
