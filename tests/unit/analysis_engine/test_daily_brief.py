"""Tests for `atlas.analysis_engine.daily_brief` (Daily Brief v1).

Builds `ChangeIntelligence`/`ChangeFinding` values directly (the exact
shapes `atlas.analysis_engine.investment_case_change.compare_snapshots`
already produces and `tests/unit/analysis_engine
/test_investment_case_change.py` already exercises in full) -- this
file tests only the *distribution* layer on top: eligibility, headline
selection, ordering, and the overall summary. It never re-tests
Change Intelligence's own detection rules.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.analysis_engine.daily_brief import build_daily_brief, build_daily_brief_entry
from atlas.analysis_engine.investment_case_change import (
    ChangeCategory,
    ChangeDirection,
    ChangeFinding,
    ChangeIntelligence,
    ThesisImpact,
)

_T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
_T1 = datetime(2026, 2, 1, tzinfo=timezone.utc)


def _change(
    category: ChangeCategory,
    direction: ChangeDirection,
    *,
    dimension: str = "growth",
    previous_state: str = "moderate",
    current_state: str = "strong",
) -> ChangeFinding:
    return ChangeFinding(
        id=f"{category.value}:{dimension}",
        category=category,
        direction=direction,
        previous_state=previous_state,
        current_state=current_state,
        details={"dimension": dimension},
        evidence_references=(),
        source_finding_id=None,
    )


def _intelligence(
    *, is_baseline: bool = False, changes: tuple[ChangeFinding, ...] = (), thesis_impact: ThesisImpact = ThesisImpact.UNCHANGED
) -> ChangeIntelligence:
    return ChangeIntelligence(
        is_baseline=is_baseline,
        changes=changes,
        thesis_impact=thesis_impact,
        summary_narrative="irrelevant to this layer",
        previous_captured_at=None if is_baseline else _T0,
        current_captured_at=_T1,
    )


class TestBaselineIsExcluded:
    """Scenario: baseline never produces a Daily Brief entry."""

    def test_baseline_produces_no_entry(self):
        intelligence = _intelligence(is_baseline=True)
        assert build_daily_brief_entry("case-1", "META", intelligence) is None


class TestNoChangesIsExcluded:
    """Scenario: no changes."""

    def test_zero_changes_produces_no_entry(self):
        intelligence = _intelligence(is_baseline=False, changes=())
        assert build_daily_brief_entry("case-1", "AAPL", intelligence) is None


class TestOneCompanyChanged:
    def test_single_growth_change_produces_a_populated_entry(self):
        change = _change(ChangeCategory.GROWTH_CHANGED, ChangeDirection.NEGATIVE, previous_state="strong", current_state="moderate")
        intelligence = _intelligence(changes=(change,), thesis_impact=ThesisImpact.WEAKENED)
        entry = build_daily_brief_entry("case-1", "META", intelligence)
        assert entry is not None
        assert entry.case_id == "case-1"
        assert entry.ticker == "META"
        assert entry.headline == "Growth weakened."
        assert "Growth weakened from Strong to Moderate." in entry.change_summary
        assert entry.why_it_matters == "Overall, the Atlas Thesis has weakened, but remains intact."
        assert entry.thesis_impact is ThesisImpact.WEAKENED
        assert entry.changes == (change,)

    def test_single_growth_improvement_headline(self):
        change = _change(ChangeCategory.GROWTH_CHANGED, ChangeDirection.POSITIVE, previous_state="moderate", current_state="strong")
        entry = build_daily_brief_entry("case-1", "NVDA", _intelligence(changes=(change,), thesis_impact=ThesisImpact.STRENGTHENED))
        assert entry.headline == "Growth strengthened."

    def test_single_coverage_gain_headline(self):
        """Scenario: analytical coverage improved."""
        change = _change(
            ChangeCategory.ANALYTICAL_COVERAGE_CHANGED,
            ChangeDirection.NEUTRAL,
            dimension="capital_allocation",
            previous_state="insufficient_input",
            current_state="moderate",
        )
        entry = build_daily_brief_entry("case-1", "MSFT", _intelligence(changes=(change,), thesis_impact=ThesisImpact.UNCHANGED))
        assert entry.headline == "Atlas can now evaluate capital allocation."
        assert "Atlas can now evaluate" in entry.change_summary

    def test_single_coverage_loss_headline(self):
        change = _change(
            ChangeCategory.ANALYTICAL_COVERAGE_CHANGED,
            ChangeDirection.NEUTRAL,
            dimension="growth",
            previous_state="moderate",
            current_state="insufficient_input",
        )
        entry = build_daily_brief_entry("case-1", "TSLA", _intelligence(changes=(change,)))
        assert entry.headline == "Atlas can no longer evaluate growth."

    def test_single_financial_risk_increase_headline(self):
        change = _change(
            ChangeCategory.FINANCIAL_RISK_CHANGED,
            ChangeDirection.NEGATIVE,
            dimension="financial_risk",
            previous_state="moderate",
            current_state="high",
        )
        entry = build_daily_brief_entry("case-1", "AMD", _intelligence(changes=(change,), thesis_impact=ThesisImpact.WEAKENED))
        assert entry.headline == "Financial risk increased."

    def test_single_strength_added_headline(self):
        change = ChangeFinding(
            id="strength_added:growth",
            category=ChangeCategory.STRENGTH_ADDED,
            direction=ChangeDirection.POSITIVE,
            previous_state="absent",
            current_state="growth",
            details={"highlight_kind": "growth"},
            evidence_references=(),
            source_finding_id=None,
        )
        entry = build_daily_brief_entry("case-1", "GOOG", _intelligence(changes=(change,), thesis_impact=ThesisImpact.STRENGTHENED))
        assert entry.headline == "New strength identified."

    def test_single_open_question_resolved_headline(self):
        change = ChangeFinding(
            id="open_question_resolved:growth_mixed",
            category=ChangeCategory.OPEN_QUESTION_RESOLVED,
            direction=ChangeDirection.POSITIVE,
            previous_state="growth_mixed",
            current_state="absent",
            details={"open_question_origin": "growth_mixed"},
            evidence_references=(),
            source_finding_id=None,
        )
        entry = build_daily_brief_entry("case-1", "AAPL", _intelligence(changes=(change,), thesis_impact=ThesisImpact.STRENGTHENED))
        assert entry.headline == "Open question resolved."


class TestMultipleChangesForOneCompany:
    def test_multiple_changes_use_thesis_impact_headline(self):
        changes = (
            _change(ChangeCategory.GROWTH_CHANGED, ChangeDirection.NEGATIVE, previous_state="strong", current_state="moderate"),
            _change(
                ChangeCategory.FINANCIAL_RISK_CHANGED,
                ChangeDirection.NEGATIVE,
                dimension="financial_risk",
                previous_state="moderate",
                current_state="high",
            ),
        )
        entry = build_daily_brief_entry("case-1", "META", _intelligence(changes=changes, thesis_impact=ThesisImpact.WEAKENED))
        assert entry.headline == "Thesis weakened."
        assert entry.change_summary.count("\n") == 1  # two lines, one per change

    def test_mixed_signals_headline(self):
        changes = (
            _change(ChangeCategory.GROWTH_CHANGED, ChangeDirection.POSITIVE, previous_state="moderate", current_state="strong"),
            _change(
                ChangeCategory.FINANCIAL_RISK_CHANGED,
                ChangeDirection.NEGATIVE,
                dimension="financial_risk",
                previous_state="moderate",
                current_state="high",
            ),
        )
        entry = build_daily_brief_entry("case-1", "META", _intelligence(changes=changes, thesis_impact=ThesisImpact.MIXED))
        assert entry.headline == "Mixed signals."


class TestEmptyBrief:
    def test_no_entries_produces_the_exact_no_change_summary(self):
        brief = build_daily_brief((), generated_at=_T1)
        assert brief.entries == ()
        assert brief.summary == "No material analytical changes since your previous review."


class TestOrdering:
    """Scenario: ordering -- alphabetical by ticker, never an invented
    importance score."""

    def test_entries_are_sorted_alphabetically_by_ticker(self):
        growth_change = _change(ChangeCategory.GROWTH_CHANGED, ChangeDirection.NEGATIVE, previous_state="strong", current_state="moderate")
        entries = (
            build_daily_brief_entry("case-msft", "MSFT", _intelligence(changes=(growth_change,), thesis_impact=ThesisImpact.WEAKENED)),
            build_daily_brief_entry("case-aapl", "AAPL", _intelligence(changes=(growth_change,), thesis_impact=ThesisImpact.WEAKENED)),
            build_daily_brief_entry("case-meta", "META", _intelligence(changes=(growth_change,), thesis_impact=ThesisImpact.WEAKENED)),
        )
        brief = build_daily_brief(entries, generated_at=_T1)
        assert [e.ticker for e in brief.entries] == ["AAPL", "META", "MSFT"]

    def test_entries_without_a_ticker_sort_last(self):
        growth_change = _change(ChangeCategory.GROWTH_CHANGED, ChangeDirection.NEGATIVE, previous_state="strong", current_state="moderate")
        entries = (
            build_daily_brief_entry("case-none", None, _intelligence(changes=(growth_change,), thesis_impact=ThesisImpact.WEAKENED)),
            build_daily_brief_entry("case-aapl", "AAPL", _intelligence(changes=(growth_change,), thesis_impact=ThesisImpact.WEAKENED)),
        )
        brief = build_daily_brief(entries, generated_at=_T1)
        assert [e.ticker for e in brief.entries] == ["AAPL", None]


class TestOverallSummaryReflectsEntryCount:
    def test_single_entry_summary(self):
        growth_change = _change(ChangeCategory.GROWTH_CHANGED, ChangeDirection.NEGATIVE, previous_state="strong", current_state="moderate")
        entry = build_daily_brief_entry("case-1", "META", _intelligence(changes=(growth_change,), thesis_impact=ThesisImpact.WEAKENED))
        brief = build_daily_brief((entry,), generated_at=_T1)
        assert brief.summary == "1 company has a meaningful analytical change to review."

    def test_multiple_entries_summary(self):
        growth_change = _change(ChangeCategory.GROWTH_CHANGED, ChangeDirection.NEGATIVE, previous_state="strong", current_state="moderate")
        entries = (
            build_daily_brief_entry("case-1", "META", _intelligence(changes=(growth_change,), thesis_impact=ThesisImpact.WEAKENED)),
            build_daily_brief_entry("case-2", "AAPL", _intelligence(changes=(growth_change,), thesis_impact=ThesisImpact.WEAKENED)),
        )
        brief = build_daily_brief(entries, generated_at=_T1)
        assert brief.summary == "2 companies have meaningful analytical changes to review."
