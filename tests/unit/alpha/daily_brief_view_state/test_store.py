"""Tests for `atlas.alpha.daily_brief_view_state.store.DailyBriefViewStateStore`."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.daily_brief_view_state.store import DailyBriefViewStateStore
from atlas.alpha.daily_brief_view_state.table import create_daily_brief_view_state_table

_USER = "00000000-0000-0000-0000-000000000001"
_FIRST_VIEW = datetime(2026, 8, 25, 21, 14, tzinfo=timezone.utc)
_SECOND_VIEW = datetime(2026, 8, 26, 9, 30, tzinfo=timezone.utc)


@pytest.fixture
def store() -> DailyBriefViewStateStore:
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_daily_brief_view_state_table(engine)
    return DailyBriefViewStateStore(engine)


class TestGet:
    def test_a_user_who_has_never_viewed_gets_a_real_none_not_an_error(self, store: DailyBriefViewStateStore):
        state = store.get(_USER)
        assert state.user_id == _USER
        assert state.last_viewed_at is None


class TestMarkViewed:
    def test_first_call_creates_the_row(self, store: DailyBriefViewStateStore):
        state = store.mark_viewed(_USER, now=_FIRST_VIEW)
        assert state.last_viewed_at == _FIRST_VIEW
        assert store.get(_USER).last_viewed_at == _FIRST_VIEW

    def test_second_call_overwrites_rather_than_duplicating(self, store: DailyBriefViewStateStore):
        store.mark_viewed(_USER, now=_FIRST_VIEW)
        store.mark_viewed(_USER, now=_SECOND_VIEW)
        assert store.get(_USER).last_viewed_at == _SECOND_VIEW

    def test_defaults_to_the_real_wall_clock_when_now_is_not_given(self, store: DailyBriefViewStateStore):
        before = datetime.now(timezone.utc)
        state = store.mark_viewed(_USER)
        after = datetime.now(timezone.utc)
        assert before <= state.last_viewed_at <= after
