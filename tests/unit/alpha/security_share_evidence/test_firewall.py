"""The decision firewall around security-level share-class evidence: a closed
set of importers, and a Case whose decision analysis is identical with and
without the evidence -- only the descriptive `historical_market_cap` reads it."""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

from atlas.alpha.investment_case.historical_market_cap import ShareCountScope
from atlas.alpha.security_share_evidence.repository import SqlAlchemySecurityShareEvidenceRepository
from atlas.alpha.security_share_evidence.table import create_security_share_evidence_tables
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import ingest
from tests.unit.alpha.security_share_evidence.test_repository import CIK, filing, listing_mics, observation

ROOT = Path(__file__).resolve().parents[4]
NOW = datetime(2026, 9, 11, 12, tzinfo=timezone.utc)

#: Every module allowed to import the evidence package: its own package, the
#: operator's write path, and the one descriptive reader with its wiring.
_ALLOWED_IMPORTERS = {
    "atlas/alpha/security_share_evidence/dependencies.py",
    "atlas/alpha/security_share_evidence/repository.py",
    "atlas/alpha/security_share_evidence/table.py",
    "atlas/alpha/security_share_evidence/current.py",
    "atlas/alpha/business_data_refresh/security_share_evidence.py",
    "atlas/dev/backfill_security_share_evidence.py",
    "atlas/dev/backfill_current_share_evidence.py",
    "atlas/alpha/issuer_equity/reader.py",
    "atlas/dev/backfill_class_rights_evidence.py",
    "atlas/alpha/investment_case/historical_market_cap.py",
    "atlas/alpha/investment_case/service.py",
    "atlas/alpha/investment_case/api/dependencies.py",
}


def _importers(module_fragment: str, *, skip: str = "") -> set[str]:
    return {str(p.relative_to(ROOT)) for p in (ROOT / "atlas").rglob("*.py")
            if p.name != skip and any(line.lstrip().startswith(("from ", "import ")) and module_fragment in line
                                      for line in p.read_text().splitlines())}


def test_only_the_write_path_and_the_descriptive_reader_import_it():
    importers = _importers("security_share_evidence")
    assert importers <= _ALLOWED_IMPORTERS, importers - _ALLOWED_IMPORTERS
    assert not [p for p in importers if p.startswith(("atlas/analysis_engine", "atlas/decision_engine", "atlas/core"))]


def test_current_share_evidence_is_read_only_by_its_operator_command():
    """Current Share-Count Evidence v1 is descriptive and diagnostic: no
    Case, valuation, decision, brief or memory path reads it."""
    assert _importers("security_share_evidence.current", skip="current.py") == {
        "atlas/dev/backfill_current_share_evidence.py"}
    readers = {str(p.relative_to(ROOT)) for p in (ROOT / "atlas").rglob("*.py")
               if any(name in p.read_text() for name in ("current_joined", "current_evidence_for_issuers",
                                                         "record_current_filing", "current_share_observations",
                                                         "current_share_filings"))}
    # The issuer common-equity composer's reader is itself descriptive and
    # firewalled (`tests/unit/alpha/class_rights_evidence/test_firewall.py`).
    assert readers == {"atlas/alpha/security_share_evidence/repository.py",
                       "atlas/alpha/security_share_evidence/table.py",
                       "atlas/dev/backfill_current_share_evidence.py",
                       "atlas/alpha/issuer_equity/reader.py"}, readers


def test_the_share_class_adapter_is_reached_only_through_business_data_refresh():
    # The sibling class-rights adapter reuses the same XBRL plumbing.
    assert _importers("sec_edgar_share_classes", skip="sec_edgar_share_classes.py") == {
        "atlas/alpha/business_data_refresh/security_share_evidence.py",
        "atlas/business_data_providers/sec_edgar_class_rights.py"}


def _statement(ticker: str) -> RawBusinessDocument:
    metadata = {"sec_cik": CIK, "sec_form": "10-K", "sec_accession": "0000000001-26-000001",
                "free_cash_flow": 10.0, "revenue": 100.0, "net_income": 8.0, "shares_outstanding": 150.0,
                "currency": "USD"}
    return RawBusinessDocument(
        identifier=f"{ticker}:FY:2025-12-31", company=ticker, source_kind="financial_statement",
        published_at=datetime(2026, 2, 5, tzinfo=timezone.utc), provider_id="sec_edgar",
        raw_reference="https://www.sec.gov/Archives/edgar/data/1/000000000126000001/",
        content_hash=hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest(),
        period_start=date(2025, 1, 1), period_end=date(2025, 12, 31), language="en", metadata=metadata,
    )


def _harness_with_evidence(monkeypatch):
    import atlas.alpha.investment_case.service as service_module
    from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
    from tests.unit.alpha.investment_case.test_service import _Harness, _new_engine

    monkeypatch.setattr(service_module, "_utc_now", lambda: NOW)
    harness = _Harness(_new_engine())
    harness.business_record_repository.add(ingest(_statement("AAA"), evaluated_at=NOW).record)
    create_security_share_evidence_tables(harness.engine)
    evidence = SqlAlchemySecurityShareEvidenceRepository(harness.engine, listing_mics=listing_mics())
    rows = (observation(period_end=date(2024, 12, 31), accession="0000000001-25-000001", filing_date=date(2025, 2, 5)),)
    evidence.record_filing(filing(list(rows)), rows)

    def service(with_evidence: bool) -> InvestmentCaseCompositionService:
        return InvestmentCaseCompositionService(
            harness.case_repository, harness.decision_repository, harness.observation_repository,
            harness.evidence_repository, harness.outcome_repository, harness.portfolio_store, harness.trade_log_store,
            harness.business_record_repository, watchlist_store=harness.watchlist_store,
            snapshot_repository=harness.snapshot_repository,
            security_share_repository=evidence if with_evidence else None,
        )

    return harness, service, rows


def test_the_decision_analysis_is_identical_with_and_without_the_evidence(monkeypatch):
    import atlas.alpha.investment_case.service as service_module

    harness, service, rows = _harness_with_evidence(monkeypatch)
    case_id = harness.add_to_watchlist("AAA")
    seen = []
    real = service_module.reconstruct_historical_market_caps

    def spy(*args, **kwargs):
        seen.append(kwargs["security_share_counts"])
        return real(*args, **kwargs)

    monkeypatch.setattr(service_module, "reconstruct_historical_market_caps", spy)
    without = service(False).build(case_id)
    with_evidence = service(True).build(case_id)
    assert seen == [(), rows]  # the evidence reaches only the descriptive reader
    assert with_evidence.canonical_analysis == without.canonical_analysis
    for name in ("financial_history", "market_snapshot", "historical_valuation", "growth_intelligence",
                 "financial_statement_intelligence", "capital_allocation_intelligence"):
        assert getattr(with_evidence, name) == getattr(without, name), name


def test_build_many_joins_each_holding_to_its_own_evidence(monkeypatch):
    import atlas.alpha.investment_case.service as service_module

    harness, service, rows = _harness_with_evidence(monkeypatch)
    (case_id,) = harness.import_holdings(("AAA",))
    seen = []
    real = service_module.reconstruct_historical_market_caps

    def spy(*args, **kwargs):
        seen.append(kwargs["security_share_counts"])
        return real(*args, **kwargs)

    monkeypatch.setattr(service_module, "reconstruct_historical_market_caps", spy)
    batch = service(True).build_many((case_id,))[case_id]
    single = service(True).build(case_id)
    assert seen == [rows, rows]
    assert batch.canonical_analysis == single.canonical_analysis == service(False).build(case_id).canonical_analysis
    if single.historical_market_cap is not None:
        assert single.historical_market_cap.share_count_scope is ShareCountScope.SECURITY
