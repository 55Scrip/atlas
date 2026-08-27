"""Tests for `atlas.alpha.daily_brief_change_log.synthesis`.

Covers Daily Brief 2.0's own required scenario 15: multiple new
changes from the same company collapsing to one message.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from atlas.alpha.daily_brief_change_log.models import ChangeLogEntry
from atlas.alpha.daily_brief_change_log.synthesis import group_by_ticker

_NOW = datetime(2026, 8, 27, 9, 0, tzinfo=timezone.utc)


def _entry(**overrides) -> ChangeLogEntry:
    defaults = dict(
        id="id-1",
        user_id="u1",
        ticker="NVDA",
        case_id="case-nvda",
        reason_code="investment_decision_transition",
        value="reduce",
        secondary_value="hold",
        label=None,
        headline="NVDA: Investment decision changed from hold to reduce.",
        priority_rank=0,
        detected_at=_NOW,
        seen_at=None,
    )
    defaults.update(overrides)
    return ChangeLogEntry(**defaults)


class TestOneCompanyOneMessage:
    def test_a_single_change_for_a_ticker_produces_one_group_with_zero_additional(self):
        groups = group_by_ticker((_entry(),))
        assert len(groups) == 1
        assert groups[0].ticker == "NVDA"
        assert groups[0].additional_count == 0

    def test_four_changes_for_one_ticker_collapse_to_one_group(self):
        """This sprint's own explicit rule: AMD must never show as four
        separate items (CEO appointed / understands more / evidence
        changed / confidence increased) -- here, four *eligible*
        changes for one ticker still collapse to one primary message."""
        entries = (
            _entry(id="id-1", reason_code="investment_decision_transition", priority_rank=0),
            _entry(id="id-2", reason_code="recommendation_conviction_transition", priority_rank=2),
            _entry(id="id-3", reason_code="business_quality", priority_rank=4),
            _entry(id="id-4", reason_code="monitoring_change", priority_rank=5),
        )
        groups = group_by_ticker(entries)
        assert len(groups) == 1
        assert groups[0].additional_count == 3

    def test_the_most_severe_reason_code_wins_the_primary_slot(self):
        """The recommendation transition itself (rank 0) must win over
        a conviction-only shift (rank 2), regardless of insertion order
        or recency."""
        entries = (
            _entry(id="low-severity", reason_code="monitoring_change", priority_rank=5, detected_at=_NOW),
            _entry(id="high-severity", reason_code="investment_decision_transition", priority_rank=0, detected_at=_NOW - timedelta(hours=1)),
        )
        groups = group_by_ticker(entries)
        assert groups[0].primary.id == "high-severity"
        assert groups[0].additional_count == 1

    def test_a_tie_in_severity_is_broken_by_earliest_detected_at(self):
        entries = (
            _entry(id="later", reason_code="assumption_status", priority_rank=1, detected_at=_NOW),
            _entry(id="earlier", reason_code="case_condition_status", priority_rank=1, detected_at=_NOW - timedelta(hours=3)),
        )
        groups = group_by_ticker(entries)
        assert groups[0].primary.id == "earlier"

    def test_different_tickers_produce_separate_groups(self):
        entries = (_entry(id="a", ticker="NVDA"), _entry(id="b", ticker="AZN", case_id="case-azn"))
        groups = group_by_ticker(entries)
        assert {g.ticker for g in groups} == {"NVDA", "AZN"}
        assert all(g.additional_count == 0 for g in groups)

    def test_groups_are_ordered_by_the_primary_entrys_own_recency(self):
        entries = (
            _entry(id="a", ticker="OLD", detected_at=_NOW - timedelta(hours=5)),
            _entry(id="b", ticker="NEW", case_id="case-new", detected_at=_NOW),
        )
        groups = group_by_ticker(entries)
        assert [g.ticker for g in groups] == ["NEW", "OLD"]


class TestNewVsSeen:
    def test_a_group_is_new_when_its_primary_entry_is_unseen(self):
        groups = group_by_ticker((_entry(seen_at=None),))
        assert groups[0].is_new is True

    def test_a_group_is_not_new_once_its_primary_entry_is_seen(self):
        groups = group_by_ticker((_entry(seen_at=_NOW),))
        assert groups[0].is_new is False

    def test_the_group_is_new_only_by_the_primary_entrys_own_seen_state_not_a_lower_ranked_one(self):
        """A group must never show as NEW merely because some
        non-primary, lower-severity fact for the same ticker happens
        to be unseen."""
        entries = (
            _entry(id="primary", reason_code="investment_decision_transition", priority_rank=0, seen_at=_NOW),
            _entry(id="secondary", reason_code="monitoring_change", priority_rank=5, seen_at=None),
        )
        groups = group_by_ticker(entries)
        assert groups[0].primary.id == "primary"
        assert groups[0].is_new is False
