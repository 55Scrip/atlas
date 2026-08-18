"""Sprint O Phases 6/8/11/14 -- end-to-end proof that `refresh_company_data`
never creates a `BusinessRecord` without first passing the Identity
Gate, that every `BusinessRecord` created in an allowed run carries
correct `CanonicalSecurity` provenance, and that the MC/EVO collision
patterns block at this, the real production boundary -- not only
inside the gate's own unit tests.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.service import refresh_company_data
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.canonical_security_gate.factory import build_identity_gate
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.analysis_engine.business_data.models import RawBusinessDocument

_NOW = datetime(2026, 8, 18, tzinfo=timezone.utc)
_RESOLUTION_ALGORITHM_VERSION = "1.0.0"  # atlas.alpha.canonical_security_resolution.service's own constant


def _engine() -> Engine:
    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})
    create_business_record_table(engine)
    return engine


def _gate(engine: Engine) -> CanonicalSecurityIdentityGate:
    return build_identity_gate(engine)


@dataclass(frozen=True)
class _FundamentalsProvider:
    ticker: str

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        if company_identifier != self.ticker:
            return ()
        return (
            RawBusinessDocument(
                identifier=f"{company_identifier}:FY:2025",
                company=company_identifier,
                source_kind="financial_statement",
                published_at=evaluated_at,
                provider_id="sec_edgar",
                raw_reference="https://example.test/fs",
                content_hash="fs-hash",
                language="en",
                metadata={"revenue": 100.0},
            ),
        )


@dataclass(frozen=True)
class _IdentityProvider:
    ticker: str
    company_name: str
    exchange: str | None = "NASDAQ"
    country: str | None = "USA"
    currency: str | None = "USD"
    security_type: str | None = "COMMON_STOCK"
    provider_id: str = "alpha_vantage"

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        return ()

    def fetch_company_profile(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        if company_identifier != self.ticker:
            return ()
        metadata = {"name": self.company_name}
        if self.exchange is not None:
            metadata["exchange"] = self.exchange
        if self.country is not None:
            metadata["country"] = self.country
        if self.currency is not None:
            metadata["currency"] = self.currency
        if self.security_type is not None:
            metadata["security_type"] = self.security_type
        return (
            RawBusinessDocument(
                identifier=f"{company_identifier}:profile:{self.provider_id}",
                company=company_identifier,
                source_kind="company_profile",
                published_at=evaluated_at,
                provider_id=self.provider_id,
                raw_reference=f"https://example.test/{self.provider_id}",
                content_hash=f"hash-{self.provider_id}-{company_identifier}",
                language="en",
                metadata=metadata,
            ),
        )


class TestNoBusinessRecordWithoutCanonicalSecurity:
    def test_auto_accept_allows_creation_and_stamps_provenance_on_every_record(self) -> None:
        engine = _engine()
        repository = SqlAlchemyBusinessRecordRepository(engine)
        providers = (_FundamentalsProvider("AAPL"), _IdentityProvider("AAPL", "Apple Inc."))
        summary = refresh_company_data("AAPL", providers, repository, identity_gate=_gate(engine))

        assert summary.identity_gate_outcome == "AUTO_ACCEPT"
        records = repository.get_by_company("AAPL")
        assert len(records) == 2  # fundamentals + identity/profile
        for record in records:
            assert record.canonical_security_id is not None
            assert record.resolution_version == _RESOLUTION_ALGORITHM_VERSION
            assert record.identity_resolved_at is not None  # refresh_company_data's own wall clock, not injectable
            assert record.provider_evidence_reference is not None
        # Every record in this run shares the exact same identity.
        assert len({r.canonical_security_id for r in records}) == 1

    def test_manual_confirmation_blocks_every_document_including_fundamentals(self) -> None:
        engine = _engine()
        repository = SqlAlchemyBusinessRecordRepository(engine)
        # No security_type -> MEDIUM confidence -> MANUAL_CONFIRMATION.
        providers = (_FundamentalsProvider("AAPL"), _IdentityProvider("AAPL", "Apple Inc.", security_type=None))
        summary = refresh_company_data("AAPL", providers, repository, identity_gate=_gate(engine))

        assert summary.identity_gate_outcome == "MANUAL_CONFIRMATION"
        assert summary.new_records == 0
        assert repository.get_by_company("AAPL") == ()

    def test_no_identity_source_at_all_blocks_before_any_provider_is_called(self) -> None:
        engine = _engine()
        repository = SqlAlchemyBusinessRecordRepository(engine)
        summary = refresh_company_data("AAPL", (_FundamentalsProvider("AAPL"),), repository, identity_gate=_gate(engine))

        assert summary.identity_gate_outcome == "NO_MATCH"
        assert summary.fetched_documents == 0
        assert repository.get_by_company("AAPL") == ()


class TestCollisionsBlockAtTheProductionBoundary:
    def test_mc_collision_creates_no_business_record_for_either_claimed_identity(self) -> None:
        engine = _engine()
        repository = SqlAlchemyBusinessRecordRepository(engine)
        providers = (
            _FundamentalsProvider("MC"),
            _IdentityProvider("MC", "LVMH", provider_id="alpha_vantage"),
            _IdentityProvider("MC", "Moelis & Co", exchange=None, country=None, currency=None, security_type=None, provider_id="sec_edgar"),
        )
        summary = refresh_company_data("MC", providers, repository, identity_gate=_gate(engine))

        assert summary.identity_gate_outcome == "AMBIGUOUS"
        assert repository.get_by_company("MC") == ()

    def test_evo_collision_creates_no_business_record_for_either_claimed_identity(self) -> None:
        engine = _engine()
        repository = SqlAlchemyBusinessRecordRepository(engine)
        providers = (
            _FundamentalsProvider("EVO"),
            _IdentityProvider("EVO", "Evotec SE", provider_id="alpha_vantage"),
            _IdentityProvider("EVO", "Evolution AB", exchange=None, country=None, currency=None, security_type=None, provider_id="sec_edgar"),
        )
        summary = refresh_company_data("EVO", providers, repository, identity_gate=_gate(engine))

        assert summary.identity_gate_outcome == "AMBIGUOUS"
        assert repository.get_by_company("EVO") == ()


class TestExistingIdentityReusedAcrossRuns:
    def test_a_second_refresh_of_the_same_ticker_reuses_the_first_canonical_security(self) -> None:
        engine = _engine()
        repository = SqlAlchemyBusinessRecordRepository(engine)
        gate = _gate(engine)
        providers = (_FundamentalsProvider("AAPL"), _IdentityProvider("AAPL", "Apple Inc."))

        first_summary = refresh_company_data("AAPL", providers, repository, identity_gate=gate)
        first_id = {r.canonical_security_id for r in repository.get_by_company("AAPL")}

        # A later run for the same company (e.g. a restated fundamental).
        second_providers = (_FundamentalsProvider("AAPL"), _IdentityProvider("AAPL", "Apple Inc."))
        second_summary = refresh_company_data("AAPL", second_providers, repository, identity_gate=gate)
        second_id = {r.canonical_security_id for r in repository.get_by_company("AAPL")}

        assert first_summary.identity_gate_outcome == "AUTO_ACCEPT"
        assert second_summary.identity_gate_outcome == "AUTO_ACCEPT"
        assert first_id == second_id  # same CanonicalSecurity, never duplicated
        assert len(first_id) == 1
