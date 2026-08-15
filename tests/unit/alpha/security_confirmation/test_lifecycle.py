"""Sprint 22 -- Security Confirmation Correction, Revocation & Historical
Integrity. Uses the same in-memory-SQLite fixture pattern as
`test_service.py` (Sprint 20) -- isolated, disposable, never touches the
real `atlas.db` (ground rule 15).

Every test in this module uses a *fixed, non-advancing* clock
deliberately -- the exact adversarial condition `service.py`'s own
`_next_recorded_at` docstring describes: if the ordering logic were
wrong, these tests (not a real clock's natural microsecond variance)
are what would catch it.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool

from atlas.alpha.security_confirmation.exceptions import NoActiveConfirmationError
from atlas.alpha.security_confirmation.repository import SqlAlchemySecurityConfirmationRepository
from atlas.alpha.security_confirmation.service import (
    ConfirmSecuritySelectionRequest,
    ConfirmSecuritySelectionService,
)
from atlas.alpha.security_confirmation.table import create_security_confirmation_table, security_confirmations_table


class _FakeDecisionRepository:
    def __init__(self, known_ids: set[str]) -> None:
        self._known_ids = known_ids

    def get(self, decision_id):
        return object() if str(decision_id) in self._known_ids else None

    def add(self, decision):
        raise NotImplementedError("This package never writes Decisions")

    def list_all(self):
        raise NotImplementedError


def _make_service(known_decision_ids: set[str], engine=None) -> tuple[ConfirmSecuritySelectionService, "Engine"]:
    if engine is None:
        engine = create_engine(
            "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
        )
        create_security_confirmation_table(engine)
    service = ConfirmSecuritySelectionService(
        _FakeDecisionRepository(known_decision_ids),
        SqlAlchemySecurityConfirmationRepository(engine),
        clock=lambda: datetime(2026, 8, 15, tzinfo=timezone.utc),  # fixed, non-advancing
    )
    return service, engine


def _request(decision_id: str, ticker: str, display_name: str = "NVIDIA CORP", cik: int = 1045810):
    return ConfirmSecuritySelectionRequest(
        decision_id=decision_id,
        confirmed_ticker=ticker,
        confirmed_display_name=display_name,
        confirmed_cik=cik,
        discovery_method="title_canonical",
        discovery_source="sec_company_tickers",
    )


def _row_count(engine, decision_id: str) -> int:
    with engine.connect() as connection:
        rows = connection.execute(
            select(security_confirmations_table).where(security_confirmations_table.c.decision_id == decision_id)
        ).fetchall()
    return len(rows)


class TestWrongConfirmationCorrection:
    """Phase 22: confirm NVDA, realize it was wrong, correct to a
    different ticker -- the old event must survive, current state must
    change, and the Decision itself (simulated via the fake repository)
    is never touched by anything in this package."""

    def test_correct_appends_revoked_and_confirmed_events_never_deletes(self):
        decision_id = str(uuid.uuid4())
        service, engine = _make_service({decision_id})

        first = service.confirm(_request(decision_id, "NVDA"))
        assert _row_count(engine, decision_id) == 1

        corrected = service.correct(_request(decision_id, "AVGO", display_name="BROADCOM INC", cik=1730168))
        assert corrected.confirmed_ticker == "AVGO"
        assert _row_count(engine, decision_id) == 3  # confirmed(NVDA), revoked(NVDA), confirmed(AVGO)

        current = service.get(decision_id)
        assert current.confirmed_ticker == "AVGO"

        # the original confirmed(NVDA) row is still physically present, untouched
        with engine.connect() as connection:
            raw_rows = connection.execute(
                select(security_confirmations_table).where(security_confirmations_table.c.id == first.id)
            ).mappings().all()
        assert len(raw_rows) == 1
        assert raw_rows[0]["confirmed_ticker"] == "NVDA"

    def test_sibling_decision_unaffected_by_correction(self):
        nvidia_decision_id = str(uuid.uuid4())
        sibling_decision_id = str(uuid.uuid4())
        service, engine = _make_service({nvidia_decision_id, sibling_decision_id})

        service.confirm(_request(nvidia_decision_id, "NVDA"))
        service.confirm(_request(sibling_decision_id, "NVDA"))
        service.correct(_request(nvidia_decision_id, "AVGO", display_name="BROADCOM INC", cik=1730168))

        assert service.get(nvidia_decision_id).confirmed_ticker == "AVGO"
        assert service.get(sibling_decision_id).confirmed_ticker == "NVDA"  # untouched


class TestReconfirmation:
    """Phase 23: confirm, revoke, confirm the same ticker again --
    deterministic current state and a complete, ordered audit trail."""

    def test_revoke_then_reconfirm_same_ticker(self):
        decision_id = str(uuid.uuid4())
        service, engine = _make_service({decision_id})

        service.confirm(_request(decision_id, "NVDA"))
        assert service.get(decision_id) is not None

        service.revoke(decision_id)
        assert service.get(decision_id) is None  # current state: unconfirmed

        reconfirmed = service.confirm(_request(decision_id, "NVDA"))
        assert reconfirmed.confirmed_ticker == "NVDA"
        assert service.get(decision_id).confirmed_ticker == "NVDA"
        assert _row_count(engine, decision_id) == 3  # confirmed, revoked, confirmed

    def test_double_revoke_is_idempotent_no_duplicate_event(self):
        decision_id = str(uuid.uuid4())
        service, engine = _make_service({decision_id})

        service.confirm(_request(decision_id, "NVDA"))
        service.revoke(decision_id)
        assert _row_count(engine, decision_id) == 2

        service.revoke(decision_id)  # already unconfirmed -- must be a no-op
        assert _row_count(engine, decision_id) == 2
        assert service.get(decision_id) is None

    def test_revoke_when_never_confirmed_is_a_safe_no_op(self):
        decision_id = str(uuid.uuid4())
        service, engine = _make_service({decision_id})

        service.revoke(decision_id)
        assert _row_count(engine, decision_id) == 0
        assert service.get(decision_id) is None


class TestDifferentCandidateCorrection:
    """Phase 24: confirm A, correct to B -- no overwrite, no ambiguity
    about which is current."""

    def test_correct_to_different_candidate_no_overwrite(self):
        decision_id = str(uuid.uuid4())
        service, engine = _make_service({decision_id})

        service.confirm(_request(decision_id, "BRK-A", display_name="BERKSHIRE HATHAWAY INC", cik=1067983))
        corrected = service.correct(
            _request(decision_id, "BRK-B", display_name="BERKSHIRE HATHAWAY INC", cik=1067983)
        )
        assert corrected.confirmed_ticker == "BRK-B"
        assert service.get(decision_id).confirmed_ticker == "BRK-B"
        # both real events remain in the store
        assert _row_count(engine, decision_id) == 3

    def test_correct_with_same_ticker_is_a_noop_no_redundant_events(self):
        decision_id = str(uuid.uuid4())
        service, engine = _make_service({decision_id})

        first = service.confirm(_request(decision_id, "NVDA"))
        result = service.correct(_request(decision_id, "NVDA"))
        assert result == first
        assert _row_count(engine, decision_id) == 1  # no revoke+reconfirm pair written


class TestCorrectRequiresActiveConfirmation:
    """Phase 9/37: `correct` means "change an existing one," not
    "create a new one" -- calling it on an unconfirmed Decision must
    fail clearly rather than silently behaving like `confirm`."""

    def test_correct_without_prior_confirmation_raises(self):
        decision_id = str(uuid.uuid4())
        service, engine = _make_service({decision_id})

        with pytest.raises(NoActiveConfirmationError):
            service.correct(_request(decision_id, "NVDA"))
        assert _row_count(engine, decision_id) == 0

    def test_correct_after_revocation_raises(self):
        decision_id = str(uuid.uuid4())
        service, engine = _make_service({decision_id})

        service.confirm(_request(decision_id, "NVDA"))
        service.revoke(decision_id)

        with pytest.raises(NoActiveConfirmationError):
            service.correct(_request(decision_id, "AVGO"))


class TestBackwardCompatibleReadOfPreSprint22Rows:
    """Phase 6/36: a row written before Sprint 22 (no `event_type`
    column value -- simulated here by inserting one with NULL directly,
    exactly what `sync_table_schema`'s own ALTER TABLE leaves existing
    rows as) must still read back as an active, current confirmation."""

    def test_null_event_type_row_reads_as_confirmed(self):
        decision_id = str(uuid.uuid4())
        engine = create_engine(
            "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
        )
        create_security_confirmation_table(engine)
        with engine.begin() as connection:
            connection.execute(
                security_confirmations_table.insert().values(
                    id=str(uuid.uuid4()),
                    decision_id=decision_id,
                    confirmed_ticker="NVDA",
                    confirmed_display_name="NVIDIA CORP",
                    confirmed_cik=1045810,
                    discovery_method="title_canonical",
                    discovery_source="sec_company_tickers",
                    confirmed_at=datetime(2026, 8, 15, tzinfo=timezone.utc).isoformat(),
                    event_type=None,
                )
            )
        service, _ = _make_service({decision_id}, engine=engine)
        current = service.get(decision_id)
        assert current is not None
        assert current.confirmed_ticker == "NVDA"

    def test_pre_sprint22_row_can_be_revoked_and_corrected(self):
        """The exact real-world case: the live NVIDIA confirmation
        persisted in Sprint 20/21 predates `event_type` entirely --
        Sprint 22's new lifecycle must operate on it correctly."""
        decision_id = str(uuid.uuid4())
        engine = create_engine(
            "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
        )
        create_security_confirmation_table(engine)
        with engine.begin() as connection:
            connection.execute(
                security_confirmations_table.insert().values(
                    id=str(uuid.uuid4()),
                    decision_id=decision_id,
                    confirmed_ticker="NVDA",
                    confirmed_display_name="NVIDIA CORP",
                    confirmed_cik=1045810,
                    discovery_method="title_canonical",
                    discovery_source="sec_company_tickers",
                    confirmed_at=datetime(2026, 8, 15, tzinfo=timezone.utc).isoformat(),
                    event_type=None,
                )
            )
        service, _ = _make_service({decision_id}, engine=engine)

        corrected = service.correct(_request(decision_id, "AVGO", display_name="BROADCOM INC", cik=1730168))
        assert corrected.confirmed_ticker == "AVGO"
        assert service.get(decision_id).confirmed_ticker == "AVGO"


class TestConfirmStillConflictsOnPlainPost:
    """Ground rule / Phase 38: the plain `confirm()` contract must stay
    exactly as Sprint 20 built it -- a different ticker while one is
    active is still a 409-mapped conflict, never an implicit correction.
    Only the new, explicit `correct()` may change an active selection."""

    def test_confirm_different_ticker_while_active_still_conflicts(self):
        from atlas.alpha.security_confirmation.exceptions import ConflictingConfirmationError

        decision_id = str(uuid.uuid4())
        service, _ = _make_service({decision_id})
        service.confirm(_request(decision_id, "NVDA"))
        with pytest.raises(ConflictingConfirmationError):
            service.confirm(_request(decision_id, "AVGO"))
        assert service.get(decision_id).confirmed_ticker == "NVDA"
