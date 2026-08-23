"""Tests for DecisionDraft's own value objects (ADR-DD-001)."""
from __future__ import annotations

import uuid

from atlas.core.domain.decision_draft.value_objects import DraftId


class TestDraftId:
    def test_generates_a_fresh_uuid_by_default(self):
        first = DraftId()
        second = DraftId()
        assert first != second
        assert isinstance(first.value, uuid.UUID)

    def test_wraps_a_given_uuid(self):
        value = uuid.uuid4()
        draft_id = DraftId(value)
        assert draft_id.value == value

    def test_str_returns_the_uuid_string(self):
        value = uuid.uuid4()
        draft_id = DraftId(value)
        assert str(draft_id) == str(value)
