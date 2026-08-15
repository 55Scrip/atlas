"""Sprint 20 -- ConfirmSecuritySelectionService, unit-level. Uses a
minimal in-memory fake `DecisionRepository` (this package's only
dependency on Core Decision) plus a real SQLite-backed confirmation
repository -- no mocks on the confirmation write/read path itself."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.security_confirmation.exceptions import (
    ConflictingConfirmationError,
    DecisionNotFoundError,
    UnsupportedDiscoverySourceError,
)
from atlas.alpha.security_confirmation.repository import SqlAlchemySecurityConfirmationRepository
from atlas.alpha.security_confirmation.service import (
    ConfirmSecuritySelectionRequest,
    ConfirmSecuritySelectionService,
)
from atlas.alpha.security_confirmation.table import create_security_confirmation_table


class _FakeDecisionRepository:
    def __init__(self, known_ids: set[str]) -> None:
        self._known_ids = known_ids

    def get(self, decision_id):
        return object() if str(decision_id) in self._known_ids else None

    def add(self, decision):
        raise NotImplementedError("This package never writes Decisions")

    def list_all(self):
        raise NotImplementedError


def _make_service(known_decision_ids: set[str]) -> ConfirmSecuritySelectionService:
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_security_confirmation_table(engine)
    return ConfirmSecuritySelectionService(
        _FakeDecisionRepository(known_decision_ids),
        SqlAlchemySecurityConfirmationRepository(engine),
        clock=lambda: datetime(2026, 8, 15, tzinfo=timezone.utc),
    )


def _nvidia_request(decision_id: str, ticker: str = "NVDA") -> ConfirmSecuritySelectionRequest:
    return ConfirmSecuritySelectionRequest(
        decision_id=decision_id,
        confirmed_ticker=ticker,
        confirmed_display_name="NVIDIA CORP",
        confirmed_cik=1045810,
        discovery_method="title_canonical",
        discovery_source="sec_company_tickers",
    )


class TestCreateConfirmation:
    def test_confirms_and_persists(self):
        decision_id = str(uuid.uuid4())
        service = _make_service({decision_id})
        selection = service.confirm(_nvidia_request(decision_id))
        assert selection.confirmed_ticker == "NVDA"
        assert selection.decision_id == decision_id
        fetched = service.get(decision_id)
        assert fetched == selection


class TestUnknownDecision:
    def test_raises_decision_not_found(self):
        service = _make_service(known_decision_ids=set())
        with pytest.raises(DecisionNotFoundError):
            service.confirm(_nvidia_request(str(uuid.uuid4())))

    def test_no_row_written_on_failure(self):
        decision_id = str(uuid.uuid4())
        service = _make_service(known_decision_ids=set())
        with pytest.raises(DecisionNotFoundError):
            service.confirm(_nvidia_request(decision_id))
        assert service.get(decision_id) is None


class TestUnsupportedSource:
    def test_raises_for_unknown_source(self):
        decision_id = str(uuid.uuid4())
        service = _make_service({decision_id})
        bad_request = ConfirmSecuritySelectionRequest(
            decision_id=decision_id,
            confirmed_ticker="NVDA",
            confirmed_display_name="NVIDIA CORP",
            confirmed_cik=1045810,
            discovery_method="title_canonical",
            discovery_source="some_other_provider",
        )
        with pytest.raises(UnsupportedDiscoverySourceError):
            service.confirm(bad_request)


class TestIdempotency:
    def test_same_ticker_resubmission_returns_existing_no_new_row(self):
        decision_id = str(uuid.uuid4())
        service = _make_service({decision_id})
        first = service.confirm(_nvidia_request(decision_id))
        second = service.confirm(_nvidia_request(decision_id))
        assert first.id == second.id

    def test_different_ticker_raises_conflict_and_does_not_replace(self):
        decision_id = str(uuid.uuid4())
        service = _make_service({decision_id})
        first = service.confirm(_nvidia_request(decision_id, ticker="NVDA"))
        with pytest.raises(ConflictingConfirmationError):
            service.confirm(_nvidia_request(decision_id, ticker="AVGO"))
        # the original confirmation must be untouched
        assert service.get(decision_id) == first


class TestMultiDecisionIsolation:
    def test_confirming_one_decision_never_affects_another(self):
        """Real-world analogue: an 'NVDA' Decision and an 'NVIDIA'
        Decision live in separate Cases (Sprint 16 finding) -- confirming
        one must never silently confirm or alter the other."""
        nvda_decision_id = str(uuid.uuid4())
        nvidia_decision_id = str(uuid.uuid4())
        service = _make_service({nvda_decision_id, nvidia_decision_id})

        service.confirm(_nvidia_request(nvidia_decision_id, ticker="NVDA"))

        assert service.get(nvda_decision_id) is None
        assert service.get(nvidia_decision_id) is not None


class TestTraceability:
    def test_confirmation_answers_all_required_audit_questions(self):
        """Which Decision? What ticker? What display name? Which
        discovery source/method? When? -- Sprint 20 Phase 35's own
        traceability requirement."""
        decision_id = str(uuid.uuid4())
        service = _make_service({decision_id})
        selection = service.confirm(_nvidia_request(decision_id))
        assert selection.decision_id == decision_id
        assert selection.confirmed_ticker == "NVDA"
        assert selection.confirmed_display_name == "NVIDIA CORP"
        assert selection.discovery_method == "title_canonical"
        assert selection.discovery_source == "sec_company_tickers"
        assert selection.confirmed_at is not None
