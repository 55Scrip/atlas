"""Tests for `atlas.alpha.daily_brief_change_log.case_baseline`.

Covers Daily Brief RC-3's own Phase 3: the first synthesis of a newly
added company establishes its baseline, without fabricating a previous
state.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.daily_brief_change_log.case_baseline import CaseBaselineStore, create_daily_brief_case_baseline_table

_USER = "00000000-0000-0000-0000-000000000001"
_NOW = datetime(2026, 8, 27, 9, 0, tzinfo=timezone.utc)


@pytest.fixture
def store() -> CaseBaselineStore:
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_daily_brief_case_baseline_table(engine)
    return CaseBaselineStore(engine)


class TestMarkSeenAndGetNew:
    def test_a_case_never_seen_before_is_reported_as_newly_seen(self, store: CaseBaselineStore):
        newly_seen = store.mark_seen_and_get_new(_USER, frozenset({"case-nvda"}), now=_NOW)
        assert newly_seen == {"case-nvda"}

    def test_the_same_case_is_never_reported_as_newly_seen_twice(self, store: CaseBaselineStore):
        store.mark_seen_and_get_new(_USER, frozenset({"case-nvda"}), now=_NOW)
        second_pass = store.mark_seen_and_get_new(_USER, frozenset({"case-nvda"}), now=_NOW)
        assert second_pass == frozenset()

    def test_only_the_genuinely_unseen_cases_in_a_mixed_batch_are_reported(self, store: CaseBaselineStore):
        store.mark_seen_and_get_new(_USER, frozenset({"case-nvda"}), now=_NOW)
        result = store.mark_seen_and_get_new(_USER, frozenset({"case-nvda", "case-amd"}), now=_NOW)
        assert result == {"case-amd"}

    def test_an_empty_case_id_set_is_a_harmless_no_op(self, store: CaseBaselineStore):
        assert store.mark_seen_and_get_new(_USER, frozenset(), now=_NOW) == frozenset()

    def test_different_users_have_independent_baselines_for_the_same_case_id(self, store: CaseBaselineStore):
        store.mark_seen_and_get_new(_USER, frozenset({"case-nvda"}), now=_NOW)
        other_user = "00000000-0000-0000-0000-000000000002"
        result = store.mark_seen_and_get_new(other_user, frozenset({"case-nvda"}), now=_NOW)
        assert result == {"case-nvda"}
