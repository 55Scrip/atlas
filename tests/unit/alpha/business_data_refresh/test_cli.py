"""Tests for `atlas.alpha.business_data_refresh.cli.main` (ATLAS-031,
Phase 40) -- the thin CLI wrapper, exercised end to end against an
isolated in-memory engine and fake providers (never the real `atlas.db`
file, never the live network -- Phase 32).

Sprint O: `main()` defaults `identity_gate` to a real gate built on the
same `engine` when none is passed, so these tests need no gate
plumbing of their own -- only `_identity_provider`, a
`CompanyProfileProvider`-only fake (see `test_service.py`'s identical
helper) added alongside whatever fundamentals fake each test already
used, wherever a test's premise requires records to actually persist.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.cli import main
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.core.infrastructure.persistence.decision.table import create_decision_table

_EVALUATED_AT = datetime(2026, 8, 9, tzinfo=timezone.utc)


@dataclass(frozen=True)
class _FakeProvider:
    documents: tuple[RawBusinessDocument, ...] = ()

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        return tuple(d for d in self.documents if d.company == company_identifier)


@dataclass(frozen=True)
class _IdentityProvider:
    """See `test_service.py`'s identically-named/shaped fixture for
    the full rationale."""

    tickers: tuple[str, ...]

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        return ()

    def fetch_company_profile(
        self, *, company_identifier: str, evaluated_at: datetime
    ) -> tuple[RawBusinessDocument, ...]:
        if company_identifier not in self.tickers:
            return ()
        return (
            RawBusinessDocument(
                identifier=f"{company_identifier}:identity-profile",
                company=company_identifier,
                source_kind="company_profile",
                published_at=evaluated_at,
                provider_id="alpha_vantage",
                raw_reference="https://example.test/identity-profile",
                content_hash=f"identity-hash-{company_identifier}",
                language="en",
                metadata={
                    "name": f"{company_identifier} Inc.",
                    "exchange": "NASDAQ",
                    "country": "USA",
                    "currency": "USD",
                    "security_type": "COMMON_STOCK",
                },
            ),
        )


def _identity_provider(*tickers: str) -> _IdentityProvider:
    return _IdentityProvider(tickers=tuple(tickers))


def _new_engine():
    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})
    create_decision_table(engine)
    return engine


def _doc(company: str) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=f"{company}:FY:2023",
        company=company,
        source_kind="financial_statement",
        published_at=_EVALUATED_AT,
        provider_id="fake",
        raw_reference="https://example.test",
        content_hash="hash-1",
        language="en",
        metadata={"revenue": 100.0, "currency": "USD"},
    )


class TestCliMain:
    def test_no_ticker_prints_usage_and_returns_two(self, capsys):
        exit_code = main(ticker=None, engine=_new_engine(), providers=())
        assert exit_code == 2
        assert "Usage:" in capsys.readouterr().out

    def test_successful_refresh_returns_zero_and_persists(self, capsys):
        engine = _new_engine()
        exit_code = main(
            ticker="AAPL", engine=engine, providers=(_FakeProvider(documents=(_doc("AAPL"),)), _identity_provider("AAPL"))
        )
        assert exit_code == 0

        captured = capsys.readouterr()
        assert "New records:          2" in captured.out  # fundamentals + identity/profile
        assert "Provider errors:      0" in captured.out

        repository = SqlAlchemyBusinessRecordRepository(engine)
        assert len(repository.get_by_company("AAPL")) == 2

    def test_creates_the_table_on_a_fresh_engine_without_error(self):
        exit_code = main(ticker="AAPL", engine=_new_engine(), providers=())
        assert exit_code == 0  # no providers, no documents, no errors -- a clean, empty run

    def test_rerun_is_idempotent_through_the_cli_too(self, capsys):
        engine = _new_engine()
        provider = _FakeProvider(documents=(_doc("AAPL"),))
        identity = _identity_provider("AAPL")
        main(ticker="AAPL", engine=engine, providers=(provider, identity))
        capsys.readouterr()

        exit_code = main(ticker="AAPL", engine=engine, providers=(provider, identity))
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "New records:          0" in captured.out
        assert "Duplicates skipped:   2" in captured.out  # fundamentals + identity/profile both repeat

    def test_ticker_is_uppercased(self):
        engine = _new_engine()
        main(
            ticker="aapl", engine=engine, providers=(_FakeProvider(documents=(_doc("AAPL"),)), _identity_provider("AAPL"))
        )
        repository = SqlAlchemyBusinessRecordRepository(engine)
        assert len(repository.get_by_company("AAPL")) == 2

    def test_provider_failure_returns_nonzero_exit_code(self, capsys):
        @dataclass(frozen=True)
        class _FailingProvider:
            def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
                raise RuntimeError("simulated failure")

        exit_code = main(
            ticker="AAPL", engine=_new_engine(), providers=(_FailingProvider(), _identity_provider("AAPL"))
        )
        assert exit_code == 1
        assert "simulated failure" in capsys.readouterr().out
