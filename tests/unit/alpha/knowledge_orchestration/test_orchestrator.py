"""Tests for `atlas.alpha.knowledge_orchestration.orchestrator` (Phase
4) -- real `refresh_company_data`/real SQLite persistence, fake
providers (no network), mirroring `tests/unit/alpha/business_data_
refresh/test_service.py`'s own fixture conventions exactly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.canonical_security_gate.factory import build_identity_gate
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.alpha.coverage.models import DimensionCoverageLevel
from atlas.alpha.evidence_quality.models import EvidenceFreshness
from atlas.alpha.knowledge_coverage.models import KnowledgeDomain
from atlas.alpha.knowledge_orchestration.dependency import resolve_order
from atlas.alpha.knowledge_orchestration.orchestrator import run_orchestrated_acquisition
from atlas.alpha.knowledge_orchestration.planner import plan_acquisition
from atlas.alpha.knowledge_strategy.completion import ResearchCompletionOutcome
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from tests.unit.alpha.knowledge_orchestration.test_planner import _coverage, _domain_coverage

_EVALUATED_AT = datetime(2026, 8, 22, tzinfo=timezone.utc)
_UNAVAILABLE = DimensionCoverageLevel.UNAVAILABLE


@dataclass(frozen=True)
class _FakeIdentityProvider:
    """Acts as the `"alpha_vantage"` role -- a `CompanyProfileProvider`
    whose profile document already carries every field the real
    Identity Gate needs to reach `AUTO_ACCEPT` (same fields
    `business_data_refresh/test_service.py::_profile_doc` already
    establishes)."""

    provider_id: str = "alpha_vantage"
    call_count: list = field(default_factory=list)

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        return ()

    def fetch_company_profile(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        self.call_count.append(company_identifier)
        return (
            RawBusinessDocument(
                identifier=f"{company_identifier}:profile", company=company_identifier, source_kind="company_profile",
                published_at=_EVALUATED_AT, provider_id="alpha_vantage", raw_reference="https://example.test/profile",
                content_hash="profile-hash", language="en",
                metadata={
                    "name": "Test Co", "sector": "Technology", "exchange": "NASDAQ", "country": "USA",
                    "currency": "USD", "security_type": "COMMON_STOCK",
                },
            ),
        )


@dataclass(frozen=True)
class _FakeFundamentalsProvider:
    """Acts as the `"sec_edgar"` role -- a plain `fetch()`-only
    provider, deliberately NOT implementing `CompanyProfileProvider`,
    to prove the orchestrator (not this fake) is what satisfies the
    Identity Gate requirement."""

    provider_id: str = "sec_edgar"
    call_count: list = field(default_factory=list)

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        self.call_count.append(company_identifier)
        return (
            RawBusinessDocument(
                identifier=f"{company_identifier}:FY:2025", company=company_identifier, source_kind="financial_statement",
                published_at=_EVALUATED_AT, provider_id="sec_edgar", raw_reference="https://example.test/10k",
                content_hash="fy-hash", language="en", metadata={"revenue": 1000.0, "currency": "USD"},
            ),
        )


@dataclass(frozen=True)
class _FakeFilingsProvider:
    provider_id: str = "sec_edgar_filings"
    call_count: list = field(default_factory=list)

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        self.call_count.append(company_identifier)
        return (
            RawBusinessDocument(
                identifier=f"{company_identifier}:FILING:0001", company=company_identifier, source_kind="company_filing",
                published_at=_EVALUATED_AT, provider_id="sec_edgar_filings", raw_reference="https://example.test/filing",
                content_hash="filing-hash", language="en",
                metadata={"form_type": "10-K", "accession_number": "0001"},
            ),
        )


@pytest.fixture
def engine() -> Engine:
    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})
    create_business_record_table(engine)
    return engine


@pytest.fixture
def repository(engine) -> SqlAlchemyBusinessRecordRepository:
    return SqlAlchemyBusinessRecordRepository(engine)


@pytest.fixture
def identity_gate(engine) -> CanonicalSecurityIdentityGate:
    return build_identity_gate(engine)


def _brand_new_coverage():
    return _coverage(
        (
            _domain_coverage(KnowledgeDomain.COMPANY_PROFILE, level=_UNAVAILABLE),
            _domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=_UNAVAILABLE),
            _domain_coverage(KnowledgeDomain.VALUATION, level=_UNAVAILABLE),
            _domain_coverage(KnowledgeDomain.REGULATORY_FILINGS, level=_UNAVAILABLE),
        )
    )


class TestFullOrchestrationLoop:
    def test_a_brand_new_case_acquires_every_planned_domain(self, repository, identity_gate):
        coverage = _brand_new_coverage()
        plan = plan_acquisition(coverage)
        providers_by_id = {
            "alpha_vantage": _FakeIdentityProvider(),
            "sec_edgar": _FakeFundamentalsProvider(),
            "sec_edgar_filings": _FakeFilingsProvider(),
        }
        outcome = run_orchestrated_acquisition("AAPL", plan, coverage, providers_by_id, repository, identity_gate=identity_gate)

        assert set(outcome.acquired_domains) == {
            KnowledgeDomain.COMPANY_PROFILE, KnowledgeDomain.FINANCIAL_HISTORY, KnowledgeDomain.REGULATORY_FILINGS,
        }
        assert outcome.should_reanalyze is True  # FINANCIAL_HISTORY is CRITICAL
        # VALUATION (Decision Relevance CRITICAL) is still missing --
        # the fake identity provider's plain `fetch()` never returns
        # market-data documents -- and no provider error was raised, so
        # this is honestly "nothing more to do right now," not a block.
        assert outcome.research_completion.outcome is ResearchCompletionOutcome.AWAIT_FUTURE_EXTERNAL_INFORMATION

    def test_identity_provider_is_included_alongside_every_identity_requiring_step(self, repository, identity_gate):
        """The load-bearing proof: `sec_edgar`/`sec_edgar_filings` are
        plain `fetch()`-only fakes with no `CompanyProfileProvider`
        capability of their own -- if the orchestrator did not include
        the identity provider alongside them, the Identity Gate would
        return `NO_MATCH` and zero records would be written."""
        coverage = _brand_new_coverage()
        plan = plan_acquisition(coverage)
        fundamentals = _FakeFundamentalsProvider()
        filings = _FakeFilingsProvider()
        providers_by_id = {"alpha_vantage": _FakeIdentityProvider(), "sec_edgar": fundamentals, "sec_edgar_filings": filings}
        outcome = run_orchestrated_acquisition("AAPL", plan, coverage, providers_by_id, repository, identity_gate=identity_gate)

        sec_edgar_step = next(s for s in outcome.steps if s.item.provider_id == "sec_edgar")
        filings_step = next(s for s in outcome.steps if s.item.provider_id == "sec_edgar_filings")
        assert sec_edgar_step.summary.identity_gate_outcome == "AUTO_ACCEPT"
        assert sec_edgar_step.domain_acquired is True
        assert filings_step.summary.identity_gate_outcome == "AUTO_ACCEPT"
        assert filings_step.domain_acquired is True

    def test_without_orchestrator_logic_a_lone_identity_requiring_provider_fails_the_gate(self, repository, identity_gate):
        """Negative control proving the dependency really is real: a
        raw `refresh_company_data` call with ONLY the fundamentals
        provider (no identity provider alongside it) is blocked."""
        from atlas.alpha.business_data_refresh.service import refresh_company_data

        summary = refresh_company_data("AAPL", (_FakeFundamentalsProvider(),), repository, identity_gate=identity_gate)
        assert summary.identity_gate_outcome != "AUTO_ACCEPT"
        assert summary.new_records == 0

    def test_an_already_complete_case_runs_nothing(self, repository, identity_gate):
        from atlas.alpha.evidence_quality.models import EvidenceFreshness as _F

        coverage = _coverage(
            (
                _domain_coverage(KnowledgeDomain.COMPANY_PROFILE, level=DimensionCoverageLevel.AVAILABLE, freshness=_F.FRESH),
                _domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=DimensionCoverageLevel.AVAILABLE, freshness=_F.FRESH),
                _domain_coverage(KnowledgeDomain.VALUATION, level=DimensionCoverageLevel.AVAILABLE, freshness=_F.FRESH),
                _domain_coverage(KnowledgeDomain.REGULATORY_FILINGS, level=DimensionCoverageLevel.AVAILABLE, freshness=_F.FRESH),
            )
        )
        plan = plan_acquisition(coverage)
        providers_by_id = {
            "alpha_vantage": _FakeIdentityProvider(), "sec_edgar": _FakeFundamentalsProvider(), "sec_edgar_filings": _FakeFilingsProvider(),
        }
        outcome = run_orchestrated_acquisition("AAPL", plan, coverage, providers_by_id, repository, identity_gate=identity_gate)
        assert outcome.steps == ()
        assert outcome.acquired_domains == ()
        assert outcome.should_reanalyze is False
        assert outcome.research_completion.outcome is ResearchCompletionOutcome.DECISION_READY

    def test_ordered_items_respect_dependency_order(self, repository, identity_gate):
        coverage = _brand_new_coverage()
        plan = plan_acquisition(coverage)
        ordered = resolve_order(plan.items, coverage)
        provider_order = [i.provider_id for i in ordered]
        assert provider_order.index("alpha_vantage") < provider_order.index("sec_edgar")
        assert provider_order.index("alpha_vantage") < provider_order.index("sec_edgar_filings")
