"""Tests for `atlas.analysis_engine.investment_case_history` (History
v1's pure module). Builds `AnalyticalSnapshot`/`ChangeIntelligence`
values directly -- the exact shapes `compare_snapshots` already
produces and `tests/unit/analysis_engine/test_investment_case_change.py`
already exercises in full -- this file tests only the cross-Case
merge/ordering layer on top, mirroring `test_daily_brief.py`'s own
"never re-test Change Intelligence's own detection rules" discipline.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.analysis_engine.investment_case_change import (
    AnalyticalSnapshot,
    ChangeIntelligence,
    ThesisImpact,
    compare_snapshots,
)
from atlas.analysis_engine.investment_case_history import (
    HistoricalAnalysisEntry,
    build_analytical_history,
)

_T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
_T1 = datetime(2026, 2, 1, tzinfo=timezone.utc)
_T2 = datetime(2026, 3, 1, tzinfo=timezone.utc)


def _snapshot(*, content_hash: str, captured_at: datetime) -> AnalyticalSnapshot:
    return AnalyticalSnapshot(
        business_category_states=(),
        risk_category_states=(),
        valuation_status="insufficient_input",
        valuation_finding_id="valuation_finding:fcf_yield_relative",
        current_yield=None,
        strength_kinds=(),
        risk_highlight_kinds=(),
        open_question_origins=(),
        atlas_thesis_narrative=None,
        atlas_thesis_posture=None,
        content_hash=content_hash,
        captured_at=captured_at,
    )


def _baseline(captured_at: datetime = _T0) -> ChangeIntelligence:
    return compare_snapshots(None, _snapshot(content_hash="unused", captured_at=captured_at))


def _entry(case_id: str, ticker: str | None, captured_at: datetime, content_hash: str) -> HistoricalAnalysisEntry:
    snapshot = _snapshot(content_hash=content_hash, captured_at=captured_at)
    return HistoricalAnalysisEntry(
        case_id=case_id, ticker=ticker, snapshot=snapshot, change_intelligence=_baseline(captured_at)
    )


class TestEmptyHistory:
    """Scenario 1: no entries anywhere produces an empty history."""

    def test_no_entries_produces_an_empty_history(self):
        history = build_analytical_history((), generated_at=_T1)
        assert history.entries == ()
        assert history.generated_at == _T1


class TestOrderingIsNewestFirst:
    """Scenario 4: multiple entries are ordered newest-first,
    deterministically."""

    def test_entries_are_ordered_by_captured_at_descending(self):
        entries = (
            _entry("case-1", "AAPL", _T0, "hash-a"),
            _entry("case-1", "AAPL", _T2, "hash-c"),
            _entry("case-1", "AAPL", _T1, "hash-b"),
        )
        history = build_analytical_history(entries, generated_at=_T2)
        assert [e.snapshot.captured_at for e in history.entries] == [_T2, _T1, _T0]

    def test_ordering_spans_multiple_cases(self):
        entries = (
            _entry("case-msft", "MSFT", _T0, "hash-msft"),
            _entry("case-aapl", "AAPL", _T2, "hash-aapl"),
            _entry("case-meta", "META", _T1, "hash-meta"),
        )
        history = build_analytical_history(entries, generated_at=_T2)
        assert [e.ticker for e in history.entries] == ["AAPL", "META", "MSFT"]

    def test_ties_break_deterministically_on_case_id_then_content_hash(self):
        entries = (
            _entry("case-b", "MSFT", _T0, "hash-2"),
            _entry("case-a", "AAPL", _T0, "hash-1"),
        )
        history = build_analytical_history(entries, generated_at=_T0)
        # Same captured_at for both -- stable secondary ordering by
        # case_id, never arbitrary/insertion-order-dependent.
        assert [e.case_id for e in history.entries] == ["case-a", "case-b"]

    def test_ordering_is_stable_across_repeated_calls(self):
        entries = (
            _entry("case-1", "AAPL", _T0, "hash-a"),
            _entry("case-1", "AAPL", _T1, "hash-b"),
        )
        first = build_analytical_history(entries, generated_at=_T1)
        second = build_analytical_history(entries, generated_at=_T1)
        assert [e.snapshot.content_hash for e in first.entries] == [e.snapshot.content_hash for e in second.entries]


class TestNoComputation:
    """This module never invents a status, direction, or thesis impact
    -- every value on a returned entry is exactly what the caller
    passed in."""

    def test_change_intelligence_is_passed_through_unmodified(self):
        change_intelligence = compare_snapshots(
            _snapshot(content_hash="hash-a", captured_at=_T0), _snapshot(content_hash="hash-b", captured_at=_T1)
        )
        entry = HistoricalAnalysisEntry(
            case_id="case-1",
            ticker="AAPL",
            snapshot=_snapshot(content_hash="hash-b", captured_at=_T1),
            change_intelligence=change_intelligence,
        )
        history = build_analytical_history((entry,), generated_at=_T1)
        assert history.entries[0].change_intelligence is change_intelligence
        assert history.entries[0].change_intelligence.thesis_impact is ThesisImpact.UNCHANGED
