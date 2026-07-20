"""Tests for Knowledge Reference value objects (DO-IMP-003)."""
from __future__ import annotations

import uuid

from atlas.core.domain.knowledge_reference.value_objects import KnowledgeReferenceId


class TestKnowledgeReferenceId:
    def test_generates_a_uuid_by_default(self):
        assert isinstance(KnowledgeReferenceId().value, uuid.UUID)

    def test_two_default_ids_are_different(self):
        assert KnowledgeReferenceId() != KnowledgeReferenceId()

    def test_equal_by_value(self):
        value = uuid.uuid4()
        assert KnowledgeReferenceId(value) == KnowledgeReferenceId(value)

    def test_str_returns_the_uuid_string(self):
        value = uuid.uuid4()
        assert str(KnowledgeReferenceId(value)) == str(value)
