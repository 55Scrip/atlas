"""Tests for `atlas.alpha.daily_brief_change_log.store.DailyBriefChangeLogStore`.

Covers Daily Brief 2.0's own required scenarios 10-13: new unseen
change, seen change, archived change, and a persistent recommendation
the user never acted on (never re-logged as a second "new" item).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.daily_brief_change_log.eligibility import EligibleChange
from atlas.alpha.daily_brief_change_log.store import DEFAULT_ARCHIVE_AFTER, DailyBriefChangeLogStore
from atlas.alpha.daily_brief_change_log.table import create_daily_brief_change_log_table

_USER = "00000000-0000-0000-0000-000000000001"
_NOW = datetime(2026, 8, 27, 9, 0, tzinfo=timezone.utc)


def _change(**overrides) -> EligibleChange:
    defaults = dict(
        ticker="NVDA",
        case_id="case-nvda",
        reason_code="investment_decision_transition",
        value="reduce",
        secondary_value="hold",
        label=None,
        headline="NVDA: Investment decision changed from hold to reduce.",
        priority_rank=0,
    )
    defaults.update(overrides)
    return EligibleChange(**defaults)


@pytest.fixture
def store() -> DailyBriefChangeLogStore:
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_daily_brief_change_log_table(engine)
    return DailyBriefChangeLogStore(engine)


class TestRecordIfNew:
    def test_a_genuinely_new_change_is_recorded_as_unseen(self, store: DailyBriefChangeLogStore):
        recorded = store.record_if_new(_USER, (_change(),), now=_NOW)
        assert len(recorded) == 1
        assert recorded[0].seen_at is None
        assert recorded[0].detected_at == _NOW

        live = store.list_recent(_USER, now=_NOW)
        assert len(live) == 1
        assert live[0].ticker == "NVDA"
        assert live[0].value == "reduce"

    def test_the_same_transition_recorded_twice_is_not_duplicated(self, store: DailyBriefChangeLogStore):
        """Phase 4/15's own 'persistent recommendation ignored by the
        user' case: Atlas still recommends Reduce a day later -- the
        SAME natural key must never produce a second row. (A later
        assertion within this store's own 72-hour archive window --
        archival past that window is `TestArchival`'s own concern.)"""
        store.record_if_new(_USER, (_change(),), now=_NOW)
        second_call = store.record_if_new(_USER, (_change(),), now=_NOW + timedelta(hours=20))
        assert second_call == ()  # nothing NEW was recorded the second time
        assert len(store.list_recent(_USER, now=_NOW + timedelta(hours=20))) == 1

    def test_detected_at_is_never_bumped_forward_by_a_later_no_op_call(self, store: DailyBriefChangeLogStore):
        store.record_if_new(_USER, (_change(),), now=_NOW)
        store.record_if_new(_USER, (_change(),), now=_NOW + timedelta(hours=20))
        live = store.list_recent(_USER, now=_NOW + timedelta(hours=20))
        assert live[0].detected_at == _NOW

    def test_a_genuinely_different_transition_for_the_same_ticker_is_a_new_row(self, store: DailyBriefChangeLogStore):
        """Phase 18's own 'user updates portfolio later, or Atlas's
        view genuinely moves again' case -- a different `value`
        (Reduce -> Exit) is a different natural key, logged fresh."""
        store.record_if_new(_USER, (_change(value="reduce", secondary_value="hold"),), now=_NOW)
        store.record_if_new(_USER, (_change(value="exit", secondary_value="reduce"),), now=_NOW + timedelta(days=3))
        live = store.list_recent(_USER, now=_NOW + timedelta(days=3))
        assert len(live) == 2
        assert {entry.value for entry in live} == {"reduce", "exit"}

    def test_two_different_tickers_are_both_recorded(self, store: DailyBriefChangeLogStore):
        store.record_if_new(_USER, (_change(ticker="NVDA"), _change(ticker="AZN", case_id="case-azn")), now=_NOW)
        live = store.list_recent(_USER, now=_NOW)
        assert {entry.ticker for entry in live} == {"NVDA", "AZN"}


class TestSeenLifecycle:
    def test_a_newly_recorded_change_is_unseen(self, store: DailyBriefChangeLogStore):
        store.record_if_new(_USER, (_change(),), now=_NOW)
        entry = store.list_recent(_USER, now=_NOW)[0]
        assert entry.seen_at is None

    def test_marking_seen_sets_seen_at(self, store: DailyBriefChangeLogStore):
        recorded = store.record_if_new(_USER, (_change(),), now=_NOW)
        seen_at = _NOW + timedelta(hours=2)
        store.mark_seen(_USER, (recorded[0].id,), now=seen_at)
        entry = store.list_recent(_USER, now=seen_at)[0]
        assert entry.seen_at == seen_at

    def test_marking_seen_twice_does_not_move_the_original_seen_at(self, store: DailyBriefChangeLogStore):
        """'Do not confuse seen with resolved': re-viewing an already-
        seen change must not reset its own seen timestamp."""
        recorded = store.record_if_new(_USER, (_change(),), now=_NOW)
        first_seen = _NOW + timedelta(hours=1)
        store.mark_seen(_USER, (recorded[0].id,), now=first_seen)
        store.mark_seen(_USER, (recorded[0].id,), now=_NOW + timedelta(hours=5))
        entry = store.list_recent(_USER, now=_NOW + timedelta(hours=5))[0]
        assert entry.seen_at == first_seen

    def test_a_seen_change_stays_visible_in_list_recent(self, store: DailyBriefChangeLogStore):
        recorded = store.record_if_new(_USER, (_change(),), now=_NOW)
        store.mark_seen(_USER, (recorded[0].id,), now=_NOW + timedelta(hours=1))
        assert len(store.list_recent(_USER, now=_NOW + timedelta(hours=1))) == 1

    def test_marking_an_unknown_id_seen_is_a_harmless_no_op(self, store: DailyBriefChangeLogStore):
        store.mark_seen(_USER, ("does-not-exist",), now=_NOW)  # must not raise


class TestArchival:
    def test_a_change_within_the_archive_window_is_live(self, store: DailyBriefChangeLogStore):
        store.record_if_new(_USER, (_change(),), now=_NOW)
        just_inside = _NOW + DEFAULT_ARCHIVE_AFTER - timedelta(minutes=1)
        assert len(store.list_recent(_USER, now=just_inside)) == 1

    def test_a_change_past_the_archive_window_leaves_the_live_list(self, store: DailyBriefChangeLogStore):
        store.record_if_new(_USER, (_change(),), now=_NOW)
        just_outside = _NOW + DEFAULT_ARCHIVE_AFTER + timedelta(minutes=1)
        assert store.list_recent(_USER, now=just_outside) == ()

    def test_a_custom_archive_window_is_respected(self, store: DailyBriefChangeLogStore):
        store.record_if_new(_USER, (_change(),), now=_NOW)
        assert store.list_recent(_USER, now=_NOW + timedelta(hours=25), archive_after=timedelta(hours=24)) == ()
        assert len(store.list_recent(_USER, now=_NOW + timedelta(hours=23), archive_after=timedelta(hours=24))) == 1
