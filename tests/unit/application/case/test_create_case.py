"""Application-layer tests for CaseService (DO-IMP-001).

Exercises the service against a real (in-memory) SQLite repository, not
a fake, matching the convention used elsewhere in this codebase.
"""
from __future__ import annotations

import inspect

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.case.create_case import CaseService
from atlas.core.domain.case.exceptions import CaseNotFoundError
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.infrastructure.persistence.case.sqlalchemy_repository import (
    SqlAlchemyCaseRepository,
)
from atlas.core.infrastructure.persistence.case.table import create_case_table


@pytest.fixture
def service():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_case_table(engine)
    return CaseService(SqlAlchemyCaseRepository(engine))


class TestCreate:
    def test_creates_a_case(self, service):
        case = service.create()
        assert case.id is not None

    def test_each_call_creates_a_distinct_case(self, service):
        first = service.create()
        second = service.create()
        assert first.id != second.id


class TestRetrieveById:
    def test_returns_the_created_case(self, service):
        created = service.create()
        retrieved = service.get(created.id)
        assert retrieved == created

    def test_unknown_case_is_rejected(self, service):
        with pytest.raises(CaseNotFoundError):
            service.get(CaseId())


class TestCreatingACaseIsIsolated:
    def test_service_depends_on_nothing_but_its_own_repository(self):
        # Case is foundational: creating one must never implicitly create
        # a Decision, Outcome, Judgment, Evidence, Knowledge Reference, or
        # Reasoning Trace. CaseService's own constructor signature is the
        # proof — it accepts exactly one collaborator.
        signature = inspect.signature(CaseService.__init__)
        assert list(signature.parameters) == ["self", "repository"]
