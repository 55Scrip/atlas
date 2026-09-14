"""The operator command for security-level share-class evidence: explicit
tickers, a plan from Atlas's own stored filings, two counted requests per
pending filing, per-filing completion, resume, and fetch-once. A file
database and a fake provider serving the real trimmed instances -- no network."""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.inspection import inspect as sa_inspect

import atlas.dev.backfill_security_share_evidence as command
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.canonical_security_gate.factory import build_identity_gate, build_listing_mic_reader
from atlas.alpha.security_share_evidence.repository import SqlAlchemySecurityShareEvidenceRepository
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import ingest
from atlas.business_data_providers.sec_edgar_share_classes import FetchedInstance

FIXTURES = Path(__file__).resolve().parents[1] / "business_data_providers" / "fixtures" / "share_classes"
NOW = datetime(2026, 9, 14, tzinfo=timezone.utc)
ALPHABET = "0001652044"
FILINGS = {  # accession -> filing date, as Atlas's statements record them
    "0001652044-19-000004": "2019-02-05", "0001652044-20-000008": "2020-02-04",
    "0001652044-23-000016": "2023-02-03", "0001652044-26-000018": "2026-02-05",
}


def _statement(ticker: str, accession: str, filed: str, *, cik=ALPHABET, form="10-K") -> object:
    metadata = {"sec_cik": cik, "sec_accession": accession, "sec_form": form, "free_cash_flow": 1.0}
    doc = RawBusinessDocument(
        identifier=f"{ticker}:FY:{accession}", company=ticker, source_kind="financial_statement",
        published_at=datetime.fromisoformat(filed).replace(tzinfo=timezone.utc), provider_id="sec_edgar",
        raw_reference="https://data.sec.gov/x", content_hash=hashlib.sha256(f"{ticker}{accession}".encode()).hexdigest(),
        period_start=date(2018, 1, 1), period_end=date(2018, 12, 31), language="en", metadata=metadata,
    )
    return ingest(doc, evaluated_at=NOW).record


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "atlas.db"
    engine = create_engine(f"sqlite:///{path}", future=True)
    create_business_record_table(engine)
    records = SqlAlchemyBusinessRecordRepository(engine)
    for ticker in ("GOOG", "GOOGL"):
        for accession, filed in FILINGS.items():
            records.add(_statement(ticker, accession, filed))
        records.add(_statement(ticker, "0001652044-16-000012", "2016-02-11"))  # before --since
    build_identity_gate(engine)  # the security master's tables
    with engine.begin() as c:
        for i, ticker in enumerate(("GOOG", "GOOGL")):
            c.execute(text("INSERT INTO canonical_security_listings (id, canonical_security_id, ticker, exchange_mic, "
                           "currency, relationship, security_type) VALUES (:i, :s, :t, 'XNAS', 'USD', 'NATIVE', 'COMMON_STOCK')"),
                      {"i": f"l{i}", "s": f"s{i}", "t": ticker})
    return path


class _FakeProvider:
    def __init__(self, *, fail=()):
        self.requests, self.fail = [], set(fail)

    def fetch_instance(self, *, cik, accession, on_request=None):
        for _ in range(2):
            on_request()
            self.requests.append(accession)
            if accession in self.fail and len([a for a in self.requests if a == accession]) == 2:
                raise TimeoutError("instance timed out")
        return FetchedInstance(cik, accession, "x_htm.xml", f"https://www.sec.gov/{accession}/x_htm.xml",
                               (FIXTURES / f"{accession}.xml").read_text(), 2)


def _run(monkeypatch, capsys, database, *args, provider=None):
    provider = provider or _FakeProvider()
    monkeypatch.setattr(command, "get_default_share_class_provider", lambda: provider)
    monkeypatch.setattr(sys, "argv", ["cmd", "--database", str(database), *args])
    assert command.main() == 0
    return provider, capsys.readouterr().out


def _evidence(database):
    engine = create_engine(f"sqlite:///{database}", future=True)
    return SqlAlchemySecurityShareEvidenceRepository(engine, listing_mics=build_listing_mic_reader(engine))


def test_tickers_are_required(monkeypatch, database):
    monkeypatch.setattr(sys, "argv", ["cmd", "--database", str(database)])
    with pytest.raises(SystemExit):
        command.main()


def test_plan_shares_one_filer_between_its_tickers():
    records = {t: tuple(_statement(t, a, f) for a, f in FILINGS.items()) for t in ("GOOG", "GOOGL")}
    records["GOOG"] += (_statement("GOOG", "0001652044-16-000012", "2016-02-11"),)
    (plan,), refusals = command.plan_issuers(records, date(2019, 1, 1))
    assert (plan.issuer_cik, plan.tickers, refusals) == (ALPHABET, ["GOOG", "GOOGL"], [])
    assert [f.accession for f in plan.filings] == list(FILINGS)


def test_a_ticker_with_two_filers_or_none_is_refused():
    two = (_statement("X", "0000000001-20-000001", "2020-02-01", cik="0000000001"),
           _statement("X", "0000000002-20-000001", "2020-02-01", cik="0000000002"))
    plans, refusals = command.plan_issuers({"X": two, "Y": ()}, date(2019, 1, 1))
    assert plans == [] and len(refusals) == 2


def test_dry_run_asks_nothing_and_writes_nothing(monkeypatch, capsys, database):
    provider, out = _run(monkeypatch, capsys, database, "--tickers", "GOOG,GOOGL", "--dry-run")
    assert provider.requests == [] and "8 requests planned" in out
    assert not sa_inspect(create_engine(f"sqlite:///{database}")).has_table("security_share_filings")


def test_run_records_each_filing_then_resumes_at_no_cost(monkeypatch, capsys, database):
    provider, out = _run(monkeypatch, capsys, database, "--tickers", "GOOG,GOOGL")
    assert len(provider.requests) == 8 and "attempted 8  succeeded 8  failed 0" in out
    joined = _evidence(database).proven_for_securities({"GOOG": ALPHABET, "GOOGL": ALPHABET})
    assert {o.class_member for o in joined["GOOG"]} == {"goog:CapitalClassCMember"}
    assert {o.class_member for o in joined["GOOGL"]} == {"us-gaap:CommonClassAMember"}
    rerun, out = _run(monkeypatch, capsys, database, "--tickers", "GOOGL")
    assert rerun.requests == [] and "0 requests planned" in out


def test_a_failed_request_is_counted_and_the_filing_retried_next_run(monkeypatch, capsys, database):
    failing = _FakeProvider(fail={"0001652044-23-000016"})
    _, out = _run(monkeypatch, capsys, database, "--tickers", "GOOG", provider=failing)
    assert "attempted 8  succeeded 7  failed 1" in out and "TimeoutError" in out
    retry, out = _run(monkeypatch, capsys, database, "--tickers", "GOOG")
    assert retry.requests == ["0001652044-23-000016"] * 2


def test_max_requests_stops_between_filings(monkeypatch, capsys, database):
    provider, out = _run(monkeypatch, capsys, database, "--tickers", "GOOG", "--max-requests", "5")
    assert len(provider.requests) == 4 and "stopped: max-requests reached" in out


def test_fetch_once_then_apply_elsewhere_with_no_request(monkeypatch, capsys, database, tmp_path):
    saved = tmp_path / "fetched"
    _run(monkeypatch, capsys, database, "--tickers", "GOOG", "--save-fetched", str(saved))
    assert len(json.loads((saved / "manifest.json").read_text())) == 4
    other = tmp_path / "other.db"
    other.write_bytes(database.read_bytes())
    engine = create_engine(f"sqlite:///{other}", future=True)
    with engine.begin() as c:
        c.exec_driver_sql("DROP TABLE security_share_observations")
        c.exec_driver_sql("DROP TABLE security_share_filings")
    replay, out = _run(monkeypatch, capsys, other, "--tickers", "GOOG", "--from-fetched", str(saved))
    assert replay.requests == [] and "recorded 4" in out
    def facts(path):  # everything but when it was recorded
        return {replace(o, recorded_at=NOW) for o in _evidence(path).observations_for_issuer(ALPHABET)}

    assert facts(other) == facts(database) and len(facts(other)) == 24
