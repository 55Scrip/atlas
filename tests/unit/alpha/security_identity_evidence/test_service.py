"""Sprint 23 -- SecurityVerificationService, unit-level. Isolated
in-memory SQLite for both the confirmation and evidence tables (never
the real `atlas.db`, ground rule 15); a plain fake `provider` callable
injected in place of the real OpenFIGI HTTP call, matching every other
provider adapter's own test pattern in this codebase."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.security_confirmation.repository import SqlAlchemySecurityConfirmationRepository
from atlas.alpha.security_confirmation.service import (
    ConfirmSecuritySelectionRequest,
    ConfirmSecuritySelectionService,
)
from atlas.alpha.security_confirmation.table import create_security_confirmation_table
from atlas.alpha.security_identity_evidence.exceptions import NoActiveConfirmationError
from atlas.alpha.security_identity_evidence.openfigi_adapter import (
    OpenFigiMappingResult,
    OpenFigiMatch,
    OpenFigiProviderUnavailable,
)
from atlas.alpha.security_identity_evidence.repository import SqlAlchemySecurityIdentityEvidenceRepository
from atlas.alpha.security_identity_evidence.service import SecurityVerificationService
from atlas.alpha.security_identity_evidence.table import create_security_identity_evidence_table


class _FakeDecisionRepository:
    def __init__(self, known_ids: set[str]) -> None:
        self._known_ids = known_ids

    def get(self, decision_id):
        return object() if str(decision_id) in self._known_ids else None

    def add(self, decision):
        raise NotImplementedError

    def list_all(self):
        raise NotImplementedError


def _make_confirmed_decision(ticker: str = "NVDA", display_name: str = "NVIDIA CORP", engine=None):
    if engine is None:
        engine = create_engine(
            "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
        )
        create_security_confirmation_table(engine)
        create_security_identity_evidence_table(engine)
    decision_id = str(uuid.uuid4())
    confirm_service = ConfirmSecuritySelectionService(
        _FakeDecisionRepository({decision_id}),
        SqlAlchemySecurityConfirmationRepository(engine),
        clock=lambda: datetime(2026, 8, 16, tzinfo=timezone.utc),
    )
    confirm_service.confirm(
        ConfirmSecuritySelectionRequest(
            decision_id=decision_id,
            confirmed_ticker=ticker,
            confirmed_display_name=display_name,
            confirmed_cik=1045810,
            discovery_method="title_canonical",
            discovery_source="sec_company_tickers",
        )
    )
    return decision_id, engine


def _make_verification_service(engine, provider):
    return SecurityVerificationService(
        SqlAlchemySecurityConfirmationRepository(engine),
        SqlAlchemySecurityIdentityEvidenceRepository(engine),
        provider=provider,
        clock=lambda: datetime(2026, 8, 16, tzinfo=timezone.utc),
    )


class TestVerifiedStatus:
    def test_matching_name_produces_verified(self):
        decision_id, engine = _make_confirmed_decision("NVDA", "NVIDIA CORP")

        def fake_provider(ticker):
            assert ticker == "NVDA"
            return OpenFigiMappingResult(
                matches=(
                    OpenFigiMatch(
                        figi="BBG000BBQCY0",
                        ticker="NVDA",
                        name="NVIDIA CORP",
                        exch_code="US",
                        security_type="Common Stock",
                        market_sector="Equity",
                    ),
                )
            )

        service = _make_verification_service(engine, fake_provider)
        evidence = service.verify(decision_id)
        assert evidence.status == "verified"
        assert evidence.provider_identifier == "BBG000BBQCY0"
        assert evidence.verified_ticker == "NVDA"
        assert evidence.verified_name == "NVIDIA CORP"
        assert evidence.exchange == "US"
        assert evidence.provider == "openfigi"

    def test_name_corroboration_uses_canonicalization_not_exact_string(self):
        """A real, honest case: OpenFIGI's own title casing/punctuation
        need not byte-match SEC's -- the same canonicalize transform
        Sprint 19 already proved is reused here, not a second
        heuristic."""
        decision_id, engine = _make_confirmed_decision("NVDA", "NVIDIA CORP")

        def fake_provider(ticker):
            return OpenFigiMappingResult(
                matches=(
                    OpenFigiMatch(
                        figi="BBG000BBQCY0",
                        ticker="NVDA",
                        name="Nvidia Corp.",  # different case/punctuation
                        exch_code="US",
                        security_type="Common Stock",
                        market_sector="Equity",
                    ),
                )
            )

        service = _make_verification_service(engine, fake_provider)
        evidence = service.verify(decision_id)
        assert evidence.status == "verified"


class TestNotVerifiedStatus:
    def test_zero_matches_is_not_verified(self):
        decision_id, engine = _make_confirmed_decision("NVDA", "NVIDIA CORP")
        service = _make_verification_service(engine, lambda ticker: OpenFigiMappingResult(matches=()))
        evidence = service.verify(decision_id)
        assert evidence.status == "not_verified"
        assert evidence.provider_identifier is None

    def test_mismatched_name_is_not_verified(self):
        decision_id, engine = _make_confirmed_decision("NVDA", "NVIDIA CORP")

        def fake_provider(ticker):
            return OpenFigiMappingResult(
                matches=(
                    OpenFigiMatch(
                        figi="SOME_OTHER_FIGI",
                        ticker="NVDA",
                        name="SOMETHING COMPLETELY UNRELATED INC",
                        exch_code="US",
                        security_type="Common Stock",
                        market_sector="Equity",
                    ),
                )
            )

        service = _make_verification_service(engine, fake_provider)
        evidence = service.verify(decision_id)
        assert evidence.status == "not_verified"
        # the mismatched match's own data is still recorded -- an
        # honest "this is what we found and it disagreed", not
        # discarded.
        assert evidence.provider_identifier == "SOME_OTHER_FIGI"


class TestAmbiguousStatus:
    def test_multiple_matches_is_ambiguous_never_silently_picks_one(self):
        decision_id, engine = _make_confirmed_decision("BRK-A", "BERKSHIRE HATHAWAY INC")

        def fake_provider(ticker):
            return OpenFigiMappingResult(
                matches=(
                    OpenFigiMatch("FIGI_A", "BRK-A", "BERKSHIRE HATHAWAY INC", "US", "Common Stock", "Equity"),
                    OpenFigiMatch("FIGI_B", "BRK-A", "BERKSHIRE HATHAWAY INC", "LN", "Common Stock", "Equity"),
                )
            )

        service = _make_verification_service(engine, fake_provider)
        evidence = service.verify(decision_id)
        assert evidence.status == "ambiguous"
        assert evidence.provider_identifier is None


class TestProviderUnavailableStatus:
    def test_provider_exception_persists_provider_unavailable_never_raises(self):
        decision_id, engine = _make_confirmed_decision("NVDA", "NVIDIA CORP")

        def failing_provider(ticker):
            raise OpenFigiProviderUnavailable("simulated network failure")

        service = _make_verification_service(engine, failing_provider)
        evidence = service.verify(decision_id)  # must not raise
        assert evidence.status == "provider_unavailable"
        assert evidence.provider_identifier is None


class TestNoActiveConfirmation:
    def test_verify_without_confirmation_raises(self):
        engine = create_engine(
            "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
        )
        create_security_confirmation_table(engine)
        create_security_identity_evidence_table(engine)
        service = _make_verification_service(engine, lambda ticker: OpenFigiMappingResult(matches=()))
        with pytest.raises(NoActiveConfirmationError):
            service.verify(str(uuid.uuid4()))


class TestEvidenceLifecycle:
    def test_multiple_verify_calls_append_never_overwrite(self):
        decision_id, engine = _make_confirmed_decision("NVDA", "NVIDIA CORP")
        service = _make_verification_service(engine, lambda ticker: OpenFigiMappingResult(matches=()))

        first = service.verify(decision_id)
        second = service.verify(decision_id)
        assert first.id != second.id  # two distinct, both-persisted events

    def test_get_latest_returns_most_recent(self):
        decision_id, engine = _make_confirmed_decision("NVDA", "NVIDIA CORP")

        # first attempt: provider unavailable
        service_a = _make_verification_service(
            engine, lambda ticker: (_ for _ in ()).throw(OpenFigiProviderUnavailable("x"))
        )
        first = service_a.verify(decision_id)
        assert first.status == "provider_unavailable"

        # second attempt (later): succeeds
        def fake_provider(ticker):
            return OpenFigiMappingResult(
                matches=(OpenFigiMatch("F1", "NVDA", "NVIDIA CORP", "US", "Common Stock", "Equity"),)
            )

        service_b = SecurityVerificationService(
            SqlAlchemySecurityConfirmationRepository(engine),
            SqlAlchemySecurityIdentityEvidenceRepository(engine),
            provider=fake_provider,
            clock=lambda: datetime(2026, 8, 16, 0, 0, 1, tzinfo=timezone.utc),  # strictly later
        )
        second = service_b.verify(decision_id)

        latest = service_b.get_latest(first.confirmation_id)
        assert latest.id == second.id
        assert latest.status == "verified"


class TestUnsupportedDiscoverySource:
    def test_confirmation_with_unrecognized_source_is_unsupported(self):
        """Simulates a confirmation whose `discovery_source` this
        package does not recognize -- constructed by writing directly
        to the confirmation table (bypassing the service's own closed
        allow-list, which real confirmations can never violate today),
        the same "simulate an edge case that valid writes can't
        currently produce" technique Sprint 22's own backward-
        compatibility test already used."""
        from atlas.alpha.security_confirmation.table import security_confirmations_table

        engine = create_engine(
            "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
        )
        create_security_confirmation_table(engine)
        create_security_identity_evidence_table(engine)
        decision_id = str(uuid.uuid4())
        with engine.begin() as connection:
            connection.execute(
                security_confirmations_table.insert().values(
                    id=str(uuid.uuid4()),
                    decision_id=decision_id,
                    confirmed_ticker="XXXX",
                    confirmed_display_name="SOME FUTURE PROVIDER RESULT",
                    confirmed_cik=None,
                    discovery_method="future_method",
                    discovery_source="some_future_source",
                    confirmed_at=datetime(2026, 8, 16, tzinfo=timezone.utc).isoformat(),
                    event_type="confirmed",
                )
            )
        service = _make_verification_service(engine, lambda ticker: OpenFigiMappingResult(matches=()))
        evidence = service.verify(decision_id)
        assert evidence.status == "unsupported"
