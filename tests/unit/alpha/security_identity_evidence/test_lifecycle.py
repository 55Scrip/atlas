"""Sprint 24 -- Security Identity Evidence lifecycle trustworthiness.

Sprint 23 built the write/read paths for evidence; this suite proves
the *lifecycle* around them is honest: repeated verification, evidence
that regresses, a provider failure after an earlier success, and --
critically -- what happens to evidence when the confirmation it is
about is revoked, corrected, or reconfirmed. All scenarios use
isolated in-memory SQLite (ground rule 13), never the real `atlas.db`.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool

from atlas.alpha.security_confirmation.repository import SqlAlchemySecurityConfirmationRepository
from atlas.alpha.security_confirmation.service import (
    ConfirmSecuritySelectionRequest,
    ConfirmSecuritySelectionService,
)
from atlas.alpha.security_confirmation.table import create_security_confirmation_table
from atlas.alpha.security_identity_evidence.openfigi_adapter import (
    OpenFigiMappingResult,
    OpenFigiMatch,
    OpenFigiProviderUnavailable,
)
from atlas.alpha.security_identity_evidence.repository import SqlAlchemySecurityIdentityEvidenceRepository
from atlas.alpha.security_identity_evidence.service import SecurityVerificationService
from atlas.alpha.security_identity_evidence.table import (
    create_security_identity_evidence_table,
    security_identity_evidence_table,
)

_FIXED_NOW = datetime(2026, 8, 16, 12, 0, 0, tzinfo=timezone.utc)


class _FakeDecisionRepository:
    def __init__(self, known_ids: set[str]) -> None:
        self._known_ids = known_ids

    def get(self, decision_id):
        return object() if str(decision_id) in self._known_ids else None

    def add(self, decision):
        raise NotImplementedError

    def list_all(self):
        raise NotImplementedError


def _new_engine():
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_security_confirmation_table(engine)
    create_security_identity_evidence_table(engine)
    return engine


def _confirm_service(engine, decision_id: str):
    return ConfirmSecuritySelectionService(
        _FakeDecisionRepository({decision_id}),
        SqlAlchemySecurityConfirmationRepository(engine),
        clock=lambda: _FIXED_NOW,
    )


def _verification_service(engine, provider):
    return SecurityVerificationService(
        SqlAlchemySecurityConfirmationRepository(engine),
        SqlAlchemySecurityIdentityEvidenceRepository(engine),
        provider=provider,
        clock=lambda: _FIXED_NOW,
    )


def _verified_provider(ticker: str, name: str):
    def provider(t):
        return OpenFigiMappingResult(matches=(OpenFigiMatch("FIGI_" + t, t, name, "US", "Common Stock", "Equity"),))

    return provider


def _not_verified_provider():
    return lambda ticker: OpenFigiMappingResult(matches=())


def _evidence_row_count(engine, confirmation_id: str) -> int:
    with engine.connect() as connection:
        rows = connection.execute(
            select(security_identity_evidence_table).where(
                security_identity_evidence_table.c.confirmation_id == confirmation_id
            )
        ).fetchall()
    return len(rows)


class TestRepeatedVerification:
    """Phase 5: verified -> provider_unavailable -> verified, three
    calls against the same confirmation."""

    def test_history_preserves_all_attempts_and_latest_is_the_last_call(self):
        engine = _new_engine()
        decision_id = str(uuid.uuid4())
        _confirm_service(engine, decision_id).confirm(
            ConfirmSecuritySelectionRequest(
                decision_id=decision_id,
                confirmed_ticker="NVDA",
                confirmed_display_name="NVIDIA CORP",
                confirmed_cik=1045810,
                discovery_method="ticker_exact",
                discovery_source="sec_company_tickers",
            )
        )

        def failing(ticker):
            raise OpenFigiProviderUnavailable("simulated outage")

        v1 = _verification_service(engine, _verified_provider("NVDA", "NVIDIA CORP")).verify(decision_id)
        v2 = _verification_service(engine, failing).verify(decision_id)
        v3 = _verification_service(engine, _verified_provider("NVDA", "NVIDIA CORP")).verify(decision_id)

        assert len({v1.id, v2.id, v3.id}) == 3  # three distinct rows, none overwritten
        assert _evidence_row_count(engine, v1.confirmation_id) == 3

        latest = _verification_service(engine, _not_verified_provider()).get_latest(v1.confirmation_id)
        assert latest.id == v3.id
        assert latest.status == "verified"


class TestEvidenceRegression:
    """Phase 6: a later attempt disagrees with an earlier one -- Atlas
    must show the honest, current state, not the historically-better one."""

    def test_latest_shows_regression_not_stale_success(self):
        engine = _new_engine()
        decision_id = str(uuid.uuid4())
        _confirm_service(engine, decision_id).confirm(
            ConfirmSecuritySelectionRequest(
                decision_id=decision_id,
                confirmed_ticker="NVDA",
                confirmed_display_name="NVIDIA CORP",
                confirmed_cik=1045810,
                discovery_method="ticker_exact",
                discovery_source="sec_company_tickers",
            )
        )
        first = _verification_service(engine, _verified_provider("NVDA", "NVIDIA CORP")).verify(decision_id)
        assert first.status == "verified"

        second = _verification_service(engine, _not_verified_provider()).verify(decision_id)
        assert second.status == "not_verified"

        latest = _verification_service(engine, _not_verified_provider()).get_latest(first.confirmation_id)
        assert latest.status == "not_verified"
        assert latest.id == second.id


class TestProviderFailureAfterSuccess:
    """Phase 7: a provider outage after an earlier success must read as
    its own honest state, never silently collapsed into "verified" or
    "not_verified"."""

    def test_outage_after_success_is_its_own_distinct_state(self):
        engine = _new_engine()
        decision_id = str(uuid.uuid4())
        _confirm_service(engine, decision_id).confirm(
            ConfirmSecuritySelectionRequest(
                decision_id=decision_id,
                confirmed_ticker="NVDA",
                confirmed_display_name="NVIDIA CORP",
                confirmed_cik=1045810,
                discovery_method="ticker_exact",
                discovery_source="sec_company_tickers",
            )
        )
        first = _verification_service(engine, _verified_provider("NVDA", "NVIDIA CORP")).verify(decision_id)
        assert first.status == "verified"

        def failing(ticker):
            raise OpenFigiProviderUnavailable("simulated outage")

        second = _verification_service(engine, failing).verify(decision_id)
        assert second.status == "provider_unavailable"
        assert second.status not in ("verified", "not_verified")  # never collapsed either direction

        latest = _verification_service(engine, failing).get_latest(first.confirmation_id)
        assert latest.status == "provider_unavailable"
        # earlier success remains permanently in history, just not "current"
        assert _evidence_row_count(engine, first.confirmation_id) == 2


class TestRevocationLifecycle:
    """Phase 8: a revoked confirmation must never continue to present
    as externally verified."""

    def test_revoked_confirmation_has_no_current_evidence_path(self):
        engine = _new_engine()
        decision_id = str(uuid.uuid4())
        confirm_service = _confirm_service(engine, decision_id)
        confirm_service.confirm(
            ConfirmSecuritySelectionRequest(
                decision_id=decision_id,
                confirmed_ticker="NVDA",
                confirmed_display_name="NVIDIA CORP",
                confirmed_cik=1045810,
                discovery_method="ticker_exact",
                discovery_source="sec_company_tickers",
            )
        )
        verify_service = _verification_service(engine, _verified_provider("NVDA", "NVIDIA CORP"))
        evidence = verify_service.verify(decision_id)
        assert evidence.status == "verified"

        confirm_service.revoke(decision_id)

        confirmation_repo = SqlAlchemySecurityConfirmationRepository(engine)
        assert confirmation_repo.get_by_decision_id(decision_id) is None  # no current confirmation at all

        from atlas.alpha.security_identity_evidence.exceptions import NoActiveConfirmationError

        with pytest.raises(NoActiveConfirmationError):
            verify_service.verify(decision_id)  # cannot manufacture new evidence for nothing

        # the old evidence row is untouched, permanent history -- just
        # unreachable through the "current confirmation" read path.
        assert _evidence_row_count(engine, evidence.confirmation_id) == 1


class TestCorrectionLifecycle:
    """Phase 9: correcting a confirmation must never let old evidence
    silently appear to belong to the new selection."""

    def test_evidence_stays_with_the_confirmation_it_was_about(self):
        engine = _new_engine()
        decision_id = str(uuid.uuid4())
        confirm_service = _confirm_service(engine, decision_id)
        selection_a = confirm_service.confirm(
            ConfirmSecuritySelectionRequest(
                decision_id=decision_id,
                confirmed_ticker="NVDA",
                confirmed_display_name="NVIDIA CORP",
                confirmed_cik=1045810,
                discovery_method="ticker_exact",
                discovery_source="sec_company_tickers",
            )
        )
        evidence_a = _verification_service(engine, _verified_provider("NVDA", "NVIDIA CORP")).verify(decision_id)
        assert evidence_a.confirmation_id == selection_a.id

        selection_b = confirm_service.correct(
            ConfirmSecuritySelectionRequest(
                decision_id=decision_id,
                confirmed_ticker="MSFT",
                confirmed_display_name="MICROSOFT CORP",
                confirmed_cik=789019,
                discovery_method="ticker_exact",
                discovery_source="sec_company_tickers",
            )
        )
        assert selection_b.id != selection_a.id  # a genuinely new confirmation event

        evidence_repo = SqlAlchemySecurityIdentityEvidenceRepository(engine)
        assert evidence_repo.get_latest(selection_b.id) is None  # B starts with no evidence
        assert evidence_repo.get_latest(selection_a.id).id == evidence_a.id  # A's evidence is untouched

        # the router-level read path: current confirmation is B, and
        # asking for evidence keyed to *that* id finds nothing -- A1
        # never leaks underneath B.
        confirmation_repo = SqlAlchemySecurityConfirmationRepository(engine)
        current = confirmation_repo.get_by_decision_id(decision_id)
        assert current.id == selection_b.id
        assert evidence_repo.get_latest(current.id) is None


class TestReconfirmationLifecycle:
    """Phase 10: reconfirming the same ticker after a revoke must not
    inherit the earlier confirmation's evidence, even though the
    ticker string is identical."""

    def test_same_ticker_reconfirmation_starts_with_no_evidence(self):
        engine = _new_engine()
        decision_id = str(uuid.uuid4())
        confirm_service = _confirm_service(engine, decision_id)
        request = ConfirmSecuritySelectionRequest(
            decision_id=decision_id,
            confirmed_ticker="NVDA",
            confirmed_display_name="NVIDIA CORP",
            confirmed_cik=1045810,
            discovery_method="ticker_exact",
            discovery_source="sec_company_tickers",
        )
        selection_a = confirm_service.confirm(request)
        evidence_a = _verification_service(engine, _verified_provider("NVDA", "NVIDIA CORP")).verify(decision_id)
        confirm_service.revoke(decision_id)
        selection_b = confirm_service.confirm(request)  # same ticker, fresh confirmation

        assert selection_b.id != selection_a.id
        assert selection_b.confirmed_ticker == selection_a.confirmed_ticker == "NVDA"

        evidence_repo = SqlAlchemySecurityIdentityEvidenceRepository(engine)
        assert evidence_repo.get_latest(selection_b.id) is None
        assert evidence_repo.get_latest(selection_a.id).id == evidence_a.id


class TestMultiDecisionIsolation:
    """Phase 21: evidence for one Decision's confirmation must never
    appear on a sibling Decision, even for the identical ticker."""

    def test_verifying_one_decision_never_populates_a_sibling(self):
        engine = _new_engine()
        first_id, second_id = str(uuid.uuid4()), str(uuid.uuid4())
        for decision_id in (first_id, second_id):
            _confirm_service(engine, decision_id).confirm(
                ConfirmSecuritySelectionRequest(
                    decision_id=decision_id,
                    confirmed_ticker="NVDA",
                    confirmed_display_name="NVIDIA CORP",
                    confirmed_cik=1045810,
                    discovery_method="ticker_exact",
                    discovery_source="sec_company_tickers",
                )
            )

        _verification_service(engine, _verified_provider("NVDA", "NVIDIA CORP")).verify(first_id)

        confirmation_repo = SqlAlchemySecurityConfirmationRepository(engine)
        evidence_repo = SqlAlchemySecurityIdentityEvidenceRepository(engine)
        second_confirmation = confirmation_repo.get_by_decision_id(second_id)
        assert evidence_repo.get_latest(second_confirmation.id) is None


class TestOrderingIntegrity:
    """Phase 23: two evidence rows written at the identical instant
    (a fixed clock, or a fast real one) must still resolve to a
    deterministic "latest" -- the actual last call, never an
    artifact of UUID comparison."""

    def test_latest_is_deterministic_under_a_fixed_clock(self):
        engine = _new_engine()
        decision_id = str(uuid.uuid4())
        _confirm_service(engine, decision_id).confirm(
            ConfirmSecuritySelectionRequest(
                decision_id=decision_id,
                confirmed_ticker="NVDA",
                confirmed_display_name="NVIDIA CORP",
                confirmed_cik=1045810,
                discovery_method="ticker_exact",
                discovery_source="sec_company_tickers",
            )
        )
        results = [
            _verified_provider("NVDA", "NVIDIA CORP"),
            _not_verified_provider(),
            _verified_provider("NVDA", "NVIDIA CORP"),
        ]
        last = None
        for provider in results:
            last = _verification_service(engine, provider).verify(decision_id)

        latest = _verification_service(engine, _not_verified_provider()).get_latest(last.confirmation_id)
        assert latest.id == last.id
        assert latest.status == last.status
