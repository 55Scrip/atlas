"""The operator command for current share-count evidence: explicit tickers,
three counted and logged SEC requests per filer, a filing located by its
filing date, idempotent reruns, fetch-once, and writes to its own two tables
only. A file database and a fake SEC serving the real trimmed instances --
no network, and never Alpha Vantage."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.inspection import inspect as sa_inspect

import atlas.dev.backfill_current_share_evidence as command
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.canonical_security_gate.factory import build_identity_gate, build_listing_mic_reader
from atlas.alpha.security_share_evidence.repository import SqlAlchemySecurityShareEvidenceRepository
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import ingest
from atlas.business_data_providers.sec_edgar_share_classes import FetchedInstance

FIXTURES = Path(__file__).resolve().parents[1] / "business_data_providers" / "fixtures" / "cover_shares"
NOW = datetime(2026, 9, 14, tzinfo=timezone.utc)
ALPHABET, SALESFORCE = "0001652044", "0001108524"
SUBMISSIONS = {  # CIK -> (accession, form, filing date): what SEC submissions list
    ALPHABET: [("0001652044-26-000071", "10-Q", "2026-07-23"), ("0001652044-26-000018", "10-K", "2026-02-05"),
               ("0001652044-26-000080", "8-K", "2026-08-01")],
    SALESFORCE: [("0001108524-26-000190", "10-Q", "2026-08-27"), ("0001108524-26-000199", "10-Q/A", "2026-09-02")],
}
LISTINGS = (("GOOG", "XNAS"), ("GOOGL", "XNAS"), ("CRM", "XNYS"))
CIKS = {"GOOG": ALPHABET, "GOOGL": ALPHABET, "CRM": SALESFORCE}


def _doc(ticker, kind, identifier, metadata, *, published, reference, provider="sec_edgar"):
    return ingest(RawBusinessDocument(
        identifier=f"{ticker}:{identifier}", company=ticker, source_kind=kind, published_at=published,
        provider_id=provider, raw_reference=reference,
        content_hash=hashlib.sha256(json.dumps([ticker, identifier, metadata], sort_keys=True).encode()).hexdigest(),
        period_start=date(2025, 1, 1), period_end=published.date(), language="en", metadata=metadata,
    ), evaluated_at=NOW).record


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "atlas.db"
    engine = create_engine(f"sqlite:///{path}", future=True)
    create_business_record_table(engine)
    records = SqlAlchemyBusinessRecordRepository(engine)
    for ticker, cik in CIKS.items():
        records.add(_doc(ticker, "financial_statement", "fy2025",
                         {"sec_cik": cik, "sec_accession": f"{cik}-26-000001", "sec_form": "10-K", "revenue": 1.0},
                         published=datetime(2026, 2, 5, tzinfo=timezone.utc), reference="https://data.sec.gov/x"))
    records.add(_doc("CRM", "market_data_snapshot", "quote", {"share_price": 250.0, "shares_outstanding": 819_000_000.0},
                     published=datetime(2026, 9, 11, tzinfo=timezone.utc), provider="alpha_vantage",
                     reference="https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=CRM"))
    build_identity_gate(engine)
    with engine.begin() as c:
        for i, (ticker, mic) in enumerate(LISTINGS):
            c.execute(text("INSERT INTO canonical_security_listings (id, canonical_security_id, ticker, exchange_mic, "
                           "currency, relationship, security_type) VALUES (:i, :s, :t, :m, 'USD', 'NATIVE', 'COMMON_STOCK')"),
                      {"i": f"l{i}", "s": f"s{i}", "t": ticker, "m": mic})
    return path


class _FakeSec:
    def __init__(self, *, fail=()):
        self.requests, self.fail = [], set(fail)

    def fetch_submissions(self, *, cik, on_request=None):
        self.requests.append(("submissions", cik))
        rows = SUBMISSIONS[cik]
        return {"filings": {"recent": {"accessionNumber": [r[0] for r in rows], "form": [r[1] for r in rows],
                                       "filingDate": [r[2] for r in rows], "reportDate": ["" for _ in rows]}}}

    def fetch_instance(self, *, cik, accession, on_request=None):
        for resource in ("index", "instance"):
            on_request()
            self.requests.append((resource, accession))
            if accession in self.fail and resource == "instance":
                raise TimeoutError("instance timed out")
        return FetchedInstance(cik, accession, "x_htm.xml", f"https://www.sec.gov/{accession}/x_htm.xml",
                               (FIXTURES / f"{accession}.xml").read_text(), 2)


def _run(monkeypatch, capsys, database, *args, provider=None):
    provider = provider or _FakeSec()
    monkeypatch.setattr(command, "get_default_share_class_provider", lambda: provider)
    monkeypatch.setattr(sys, "argv", ["cmd", "--database", str(database), *args])
    assert command.main() == 0
    return provider, capsys.readouterr().out


def _evidence(database):
    engine = create_engine(f"sqlite:///{database}", future=True)
    return SqlAlchemySecurityShareEvidenceRepository(engine, listing_mics=build_listing_mic_reader(engine))


def _tables(database) -> dict[str, list]:
    with sqlite3.connect(database) as c:
        names = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return {n: sorted(map(repr, c.execute(f'SELECT * FROM "{n}"').fetchall())) for n in names}


def test_tickers_are_required(monkeypatch, database):
    monkeypatch.setattr(sys, "argv", ["cmd", "--database", str(database)])
    with pytest.raises(SystemExit):
        command.main()


def test_dry_run_asks_nothing_and_writes_nothing(monkeypatch, capsys, database):
    before = _tables(database)
    provider, out = _run(monkeypatch, capsys, database, "--tickers", "GOOG,GOOGL,CRM", "--dry-run", "--as-of", "2026-09-14")
    assert provider.requests == [] and "up to 6 keyless requests" in out and "Alpha Vantage: 0" in out
    assert _tables(database) == before


def test_run_records_each_filer_once_and_writes_only_its_own_tables(monkeypatch, capsys, database, tmp_path):
    before = _tables(database)
    saved = tmp_path / "fetched"
    provider, out = _run(monkeypatch, capsys, database, "--tickers", "GOOG,GOOGL,CRM", "--as-of", "2026-09-14",
                         "--save-fetched", str(saved))
    assert [r[0] for r in provider.requests] == ["submissions", "index", "instance"] * 2
    assert "attempted 6  failed 0" in out and "recorded 2" in out
    log = json.loads((saved / "requests.json").read_text())
    assert [(e["cik"], e["resource"], e["status"]) for e in log] == [  # filers in CIK order
        (SALESFORCE, "submissions", "ok"), (SALESFORCE, "filing_index", "ok"), (SALESFORCE, "instance", "ok"),
        (ALPHABET, "submissions", "ok"), (ALPHABET, "filing_index", "ok"), (ALPHABET, "instance", "ok")]
    assert all(e["timestamp"] and e["purpose"] for e in log)
    after = _tables(database)
    assert set(after) - set(before) == {"current_share_filings", "current_share_observations"}
    assert {n: rows for n, rows in after.items() if n in before} == before  # nothing else touched
    joined = _evidence(database).current_joined(CIKS)
    assert [(e.class_member, e.shares) for e in joined["GOOG"]] == [("goog:CapitalClassCMember", 5_527_000_000.0)]
    assert [(e.class_member, e.shares) for e in joined["GOOGL"]] == [("us-gaap:CommonClassAMember", 5_868_000_000.0)]
    assert [(e.as_of, e.filing_date) for e in joined["CRM"]] == [(date(2026, 8, 20), date(2026, 8, 27))]
    assert "provider      819.0M  ratio 0.9951" in out  # the provider is printed beside SEC, never written


def test_a_rerun_locates_the_same_filing_and_fetches_no_instance(monkeypatch, capsys, database):
    _run(monkeypatch, capsys, database, "--tickers", "GOOG,CRM", "--as-of", "2026-09-14")
    before = _tables(database)
    rerun, out = _run(monkeypatch, capsys, database, "--tickers", "GOOG,CRM", "--as-of", "2026-09-14")
    assert rerun.requests == [("submissions", SALESFORCE), ("submissions", ALPHABET)]
    assert "already recorded 2" in out and _tables(database) == before


def test_a_filing_after_the_as_of_date_is_never_located(monkeypatch, capsys, database):
    provider, out = _run(monkeypatch, capsys, database, "--tickers", "CRM", "--as-of", "2026-08-26")
    assert provider.requests == [("submissions", SALESFORCE)] and "no original 10-K/10-Q filed by 2026-08-26" in out
    assert _evidence(database).current_evidence_for_issuers(frozenset({SALESFORCE}))[SALESFORCE] == ()


def test_a_failed_request_is_logged_and_the_filing_retried_next_run(monkeypatch, capsys, database, tmp_path):
    saved = tmp_path / "fetched"
    _, out = _run(monkeypatch, capsys, database, "--tickers", "CRM", "--save-fetched", str(saved),
                  provider=_FakeSec(fail={"0001108524-26-000190"}))
    assert "attempted 3  failed 1" in out and "TimeoutError" in out
    assert json.loads((saved / "requests.json").read_text())[-1]["status"] == "TimeoutError"
    retry, out = _run(monkeypatch, capsys, database, "--tickers", "CRM")
    assert [r[0] for r in retry.requests] == ["submissions", "index", "instance"] and "recorded 1" in out


def test_max_requests_stops_between_filers(monkeypatch, capsys, database):
    provider, out = _run(monkeypatch, capsys, database, "--tickers", "GOOG,CRM", "--max-requests", "5")
    assert len(provider.requests) == 3 and "stopped: max-requests reached" in out


def test_fetch_once_then_apply_elsewhere_with_no_request(monkeypatch, capsys, database, tmp_path):
    saved = tmp_path / "fetched"
    other = tmp_path / "other.db"
    other.write_bytes(database.read_bytes())
    _run(monkeypatch, capsys, database, "--tickers", "GOOG,GOOGL,CRM", "--save-fetched", str(saved))

    def no_provider():
        raise AssertionError("--from-fetched must not build a provider")

    monkeypatch.setattr(command, "get_default_share_class_provider", no_provider)
    monkeypatch.setattr(sys, "argv", ["cmd", "--database", str(other), "--tickers", "GOOG,GOOGL,CRM",
                                      "--from-fetched", str(saved)])
    assert command.main() == 0
    assert "recorded 2" in capsys.readouterr().out
    manifest = json.loads((saved / "manifest.json").read_text())

    def facts(path):  # everything but when it was recorded
        return {replace(e, recorded_at=NOW) for cik in (ALPHABET, SALESFORCE)
                for e in _evidence(path).current_evidence_for_issuers(frozenset({cik}))[cik]}

    assert facts(other) == facts(database) and len(facts(other)) == 4
    crm = next(e for e in facts(other) if e.issuer_cik == SALESFORCE)
    assert crm.retrieved_at.isoformat() == manifest["0001108524-26-000190"]["retrieved_at"]  # the fetch's own time


def test_provider_shares_reads_the_latest_quote_only(database):
    records = SqlAlchemyBusinessRecordRepository(create_engine(f"sqlite:///{database}", future=True))
    shares, written = command.provider_shares(records.get_by_company("CRM"))
    assert shares == 819_000_000.0 and written is not None
    assert command.provider_shares(records.get_by_company("GOOG")) == (None, None)
    assert not sa_inspect(create_engine(f"sqlite:///{database}")).has_table("current_share_filings")
