"""The operator command for class economic-rights evidence: explicit tickers
and accessions, one logged request per filing at the instance URL Atlas's
share evidence recorded, idempotent reruns, fetch-once, and writes to its
own two tables only. A file database and a fake SEC serving the real
trimmed filings -- no network, never Alpha Vantage."""
from __future__ import annotations

import json
import sqlite3
import sys
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

import atlas.dev.backfill_class_rights_evidence as command
from atlas.alpha.class_rights_evidence.models import RightKind
from atlas.alpha.class_rights_evidence.repository import SqlAlchemyClassRightsEvidenceRepository
from sqlalchemy import create_engine
from tests.unit.alpha.issuer_equity.test_reader import reader as _reader_fixture  # noqa: F401 -- the shared database

FIXTURES = Path(__file__).resolve().parents[1] / "business_data_providers" / "fixtures" / "class_rights"
NOW = datetime(2026, 9, 14, tzinfo=timezone.utc)
Q2, FY = "0001652044-26-000071", "0001652044-26-000018"


@pytest.fixture
def database(_reader_fixture, tmp_path):
    path = tmp_path / "atlas.db"
    with sqlite3.connect(path) as c:  # the fixture recorded Alphabet's and MA's rights: start without them
        c.execute("DELETE FROM class_rights_observations")
        c.execute("DELETE FROM class_rights_filings")
        c.execute("UPDATE current_share_filings SET instance_url = 'https://www.sec.gov/Archives/edgar/data/1652044/q2_htm.xml' "
                  "WHERE accession = ?", (Q2,))
        c.execute("UPDATE security_share_filings SET instance_url = 'https://www.sec.gov/Archives/edgar/data/1652044/fy_htm.xml' "
                  "WHERE accession = ?", (FY,))
    return path


class _FakeSec:
    def __init__(self, *, fail=()):
        self.requests, self.fail = [], set(fail)

    def fetch_instance_at(self, *, instance_url, on_request=None):
        on_request()
        self.requests.append(instance_url)
        if instance_url in self.fail:
            raise TimeoutError("instance timed out")
        return (FIXTURES / f"{Q2 if 'q2' in instance_url else FY}.xml").read_text()


def _run(monkeypatch, capsys, database, *args, provider=None):
    provider = provider or _FakeSec()
    monkeypatch.setattr(command, "get_default_class_rights_provider", lambda: provider)
    monkeypatch.setattr(sys, "argv", ["cmd", "--database", str(database), "--as-of", "2026-09-11", *args])
    code = command.main()
    return code, provider, capsys.readouterr().out


def _tables(path):
    with sqlite3.connect(path) as c:
        names = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return {n: sorted(map(repr, c.execute(f'SELECT * FROM "{n}"').fetchall())) for n in names}


def test_tickers_and_accessions_are_required(monkeypatch, database):
    for argv in (["--tickers", "GOOG"], ["--accessions", Q2]):
        monkeypatch.setattr(sys, "argv", ["cmd", "--database", str(database), *argv])
        with pytest.raises(SystemExit):
            command.main()


def test_dry_run_asks_nothing_and_writes_nothing(monkeypatch, capsys, database):
    before = _tables(database)
    code, provider, out = _run(monkeypatch, capsys, database, "--tickers", "GOOG", "--accessions", f"{Q2},{FY}", "--dry-run")
    assert code == 0 and provider.requests == [] and "2 keyless requests" in out and "Alpha Vantage: 0" in out
    assert _tables(database) == before


def test_accessions_outside_the_named_filers_or_share_evidence_are_refused(monkeypatch, capsys, database):
    code, provider, out = _run(monkeypatch, capsys, database, "--tickers", "MA", "--accessions", f"{Q2},0000000000-26-000001")
    assert provider.requests == [] and out.count("REFUSED") == 2


def test_one_logged_request_per_filing_then_a_rerun_asks_nothing(monkeypatch, capsys, database, tmp_path):
    before = _tables(database)
    saved = tmp_path / "fetched"
    code, provider, out = _run(monkeypatch, capsys, database, "--tickers", "GOOG,GOOGL", "--accessions", f"{Q2},{FY}",
                               "--save-fetched", str(saved))
    assert code == 0 and len(provider.requests) == 2 and "recorded 2" in out and "attempted 2  failed 0" in out
    log = json.loads((saved / "requests.json").read_text())
    assert [(e["accession"], e["resource"], e["status"]) for e in log] == [(Q2, "instance", "ok"), (FY, "instance", "ok")]
    after = _tables(database)
    assert set(after) == set(before)
    assert {n: r for n, r in after.items() if not n.startswith("class_rights")} == {
        n: r for n, r in before.items() if not n.startswith("class_rights")}  # nothing else touched
    assert "GOOG   issuer_equivalent" in out
    _, rerun, out = _run(monkeypatch, capsys, database, "--tickers", "GOOG", "--accessions", f"{Q2},{FY}")
    assert rerun.requests == [] and out.count(f"already recorded ({command.RIGHTS_PARSER_VERSION})") == 2
    assert "filings: recorded 0  already recorded 2" in out


def test_a_failed_request_is_logged_and_retried_next_run(monkeypatch, capsys, database):
    failing = _FakeSec(fail={"https://www.sec.gov/Archives/edgar/data/1652044/q2_htm.xml"})
    _, _, out = _run(monkeypatch, capsys, database, "--tickers", "GOOG", "--accessions", f"{Q2},{FY}", provider=failing)
    assert "attempted 2  failed 1" in out and "TimeoutError" in out
    _, retry, _ = _run(monkeypatch, capsys, database, "--tickers", "GOOG", "--accessions", f"{Q2},{FY}")
    assert retry.requests == ["https://www.sec.gov/Archives/edgar/data/1652044/q2_htm.xml"]


def test_the_request_cap_stops_before_any_request(monkeypatch, capsys, database):
    code, provider, out = _run(monkeypatch, capsys, database, "--tickers", "GOOG", "--accessions", f"{Q2},{FY}", "--max-requests", "1")
    assert code == 1 and provider.requests == [] and "STOPPED" in out


def test_fetch_once_then_apply_elsewhere_with_no_request(monkeypatch, capsys, database, tmp_path):
    other = tmp_path / "other.db"
    other.write_bytes(database.read_bytes())
    saved = tmp_path / "fetched"
    _run(monkeypatch, capsys, database, "--tickers", "GOOG", "--accessions", f"{Q2},{FY}", "--save-fetched", str(saved))

    def no_provider():
        raise AssertionError("--from-fetched must not build a provider")

    monkeypatch.setattr(command, "get_default_class_rights_provider", no_provider)
    monkeypatch.setattr(sys, "argv", ["cmd", "--database", str(other), "--tickers", "GOOG", "--accessions", f"{Q2},{FY}",
                                      "--from-fetched", str(saved)])
    assert command.main() == 0

    def facts(path):
        repo = SqlAlchemyClassRightsEvidenceRepository(create_engine(f"sqlite:///{path}"))
        return {replace(o, recorded_at=NOW) for o in repo.observations_for_issuers(frozenset({"0001652044"}))["0001652044"]}

    assert facts(other) == facts(database) and len(facts(other)) == 64
    # 52 rights facts, plus each class-axis share fact on its own (class_rights_v2).
    assert sum(1 for o in facts(other) if o.kind is RightKind.CLASS_AXIS_SHARE_FACT) == 12
