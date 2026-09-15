"""SEC-Only Content Refresh v1 -- re-versioning stored statements from one
saved companyfacts payload.

What a reviewer cannot check by reading: that only additions ever become a
new version (any changed value, key, period, publication or source is
held), that identical content only gains provenance, that the stored version
and the Case's other records are never touched, that no request but the one
companyfacts fetch is ever made (no Alpha Vantage, no quote), that a replay
writes the very same rows and a re-run writes nothing. Real SEC adapter over
synthetic payloads, file SQLite; then Amazon's real saved payload (trimmed to
the concepts the adapter reads, proven to give identical documents) against
its real stored v1 statements.
"""
from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine

import atlas.business_data_providers.http as provider_http
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.sec_statement_content import (
    ContentKind,
    compare_statements,
    content_refresh_records,
    statement_documents,
)
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import SHARE_COUNT_PROVENANCE_KEYS, enrich_provenance, ingest
from atlas.analysis_engine.business_data.versioning import latest_versions
from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
from atlas.analysis_engine.valuation.facts import extract_valuation_facts_from_records
from atlas.dev import refresh_sec_statement_content as command
from atlas.dev.backfill_market_data_provenance import apply_sec
from tests.unit.business_data_providers.test_sec_edgar import _companyfacts, _instant_entry, _usd_entry

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).parent / "fixtures" / "sec_statement_content"
CIK = "0001234567"
LEGACY_AT = datetime(2026, 8, 10, tzinfo=timezone.utc)
FETCHED_AT = datetime(2026, 9, 15, 20, 5, 40, tzinfo=timezone.utc)
A21, A22 = "0001234567-21-000001", "0001234567-22-000001"


def _payload(*, revenue=1000.0, ocf=500.0, capex=100.0, equity=4000.0, periods=("2020",)):
    concepts = {"Revenues": [], "NetCashProvidedByUsedInOperatingActivities": [], "PaymentsToAcquirePropertyPlantAndEquipment": [],
                "CommonStockSharesOutstanding": [], "StockholdersEquity": []}
    for year in periods:
        y = int(year)
        filed, accn = f"{y + 1}-02-10", f"0001234567-{str(y + 1)[2:]}-000001"
        span = dict(start=f"{y}-01-01", end=f"{y}-12-31", filed=filed, accn=accn)
        concepts["Revenues"].append(_usd_entry(val=revenue, **span))
        concepts["NetCashProvidedByUsedInOperatingActivities"].append(_usd_entry(val=ocf, **span))
        concepts["PaymentsToAcquirePropertyPlantAndEquipment"].append(_usd_entry(val=capex, **span))
        concepts["CommonStockSharesOutstanding"] += [
            _instant_entry(end=f"{y}-12-31", val=90.0, filed=filed, accn=accn),
            _instant_entry(end=f"{y}-12-31", val=90.0, filed=f"{y + 2}-02-10", accn=f"0001234567-{str(y + 2)[2:]}-000001")]
        if equity is not None:
            concepts["StockholdersEquity"].append(_instant_entry(end=f"{y}-12-31", val=equity, filed=filed, accn=accn))
    return _companyfacts({k: v for k, v in concepts.items() if v}, units={"CommonStockSharesOutstanding": "shares"})


def _docs(ticker="SYN", payload=None):
    return statement_documents(ticker, CIK, payload or _payload())


def _legacy_document(doc, *, drop=("equity",), content_hash="legacy-v1", **metadata):
    """What an older adapter stored for the same statement: fewer keys, no
    share provenance, its own content hash."""
    kept = {k: v for k, v in doc.metadata.items() if k not in drop and k not in SHARE_COUNT_PROVENANCE_KEYS}
    return replace(doc, metadata={**kept, **metadata}, content_hash=content_hash)


@pytest.fixture
def repository(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'atlas.db'}", future=True)
    create_business_record_table(engine)
    return SqlAlchemyBusinessRecordRepository(engine)


def _store(repository, document, **identity):
    result = ingest(document, evaluated_at=LEGACY_AT, **identity)
    repository.add(result.record)
    return result.record


def _plan(repository, ticker="SYN", payload=None):
    return content_refresh_records(_docs(ticker, payload), tuple(repository.get_by_company(ticker)), evaluated_at=FETCHED_AT)


class TestClassification:
    def test_identical_content_gains_only_provenance(self, repository):
        (doc,) = _docs()
        stored = _store(repository, _legacy_document(doc, drop=(), content_hash=doc.content_hash))
        ((comparison, record),) = _plan(repository)
        assert comparison.kind is ContentKind.IDENTICAL and comparison.added == ()
        assert set(comparison.provenance_added) == set(SHARE_COUNT_PROVENANCE_KEYS)
        assert (record.content_hash, record.version.supersedes) == (stored.content_hash, stored.id)
        assert {k: v for k, v in record.metadata.items() if k not in SHARE_COUNT_PROVENANCE_KEYS} == dict(stored.metadata)

    def test_identical_content_is_exactly_the_existing_provenance_enrichment(self, repository):
        (doc,) = _docs()
        stored = _store(repository, _legacy_document(doc, drop=(), content_hash=doc.content_hash))
        ((_, record),) = _plan(repository)
        assert record == enrich_provenance(doc, head=stored, provenance_keys=SHARE_COUNT_PROVENANCE_KEYS, evaluated_at=FETCHED_AT)

    def test_additions_only_is_a_new_version_of_the_same_lineage(self, repository):
        (doc,) = _docs()
        stored = _store(repository, _legacy_document(doc))
        ((comparison, record),) = _plan(repository)
        assert (comparison.kind, comparison.added) == (ContentKind.ADDITIONS_ONLY, ("equity",))
        assert (record.lineage_id, record.version.version_number, record.version.supersedes) == (stored.lineage_id, 2, stored.id)
        assert record.content_hash == doc.content_hash and record.metadata["equity"] == 4000.0
        assert all(record.metadata[k] == v for k, v in stored.metadata.items())

    def test_the_new_version_carries_full_filing_provenance(self, repository):
        (doc,) = _docs()
        _store(repository, _legacy_document(doc))
        ((_, record),) = _plan(repository)
        assert {k: record.metadata[k] for k in SHARE_COUNT_PROVENANCE_KEYS} == {
            "shares_outstanding_filed": "2022-02-10", "shares_outstanding_accession": A22,
            "shares_outstanding_first_reported": 90.0, "shares_outstanding_first_reported_filed": "2021-02-10",
            "shares_outstanding_first_reported_accession": A21}

    def test_the_new_version_keeps_the_superseded_versions_identity(self, repository):
        (doc,) = _docs()
        stored = _store(repository, _legacy_document(doc), canonical_security_id="sec-1", resolution_version="r1",
                        identity_resolved_at=LEGACY_AT, provider_evidence_reference="ev-1")
        repository_record = replace(stored, canonical_issuer_id="iss-1")
        ((_, record),) = content_refresh_records(_docs(), (repository_record,), evaluated_at=FETCHED_AT)
        assert (record.canonical_security_id, record.resolution_version, record.identity_resolved_at,
                record.provider_evidence_reference, record.canonical_issuer_id) == ("sec-1", "r1", LEGACY_AT, "ev-1", "iss-1")

    @pytest.mark.parametrize("key, value", [("revenue", 999.0), ("free_cash_flow", 401.0), ("shares_outstanding", 91.0),
                                            ("currency", "EUR"), ("sec_accession", "0009999999-21-000001"),
                                            ("sec_form", "20-F")])
    def test_any_stored_value_changed_is_held(self, repository, key, value):
        (doc,) = _docs()
        _store(repository, _legacy_document(doc, **{key: value}))
        ((comparison, record),) = _plan(repository)
        assert comparison.kind is ContentKind.VALUE_CHANGED and record is None
        assert (key, value, doc.metadata[key]) in comparison.changed

    def test_a_stored_key_the_adapter_no_longer_returns_is_held(self, repository):
        (doc,) = _docs()
        _store(repository, _legacy_document(doc, retired_concept=1.0))
        ((comparison, record),) = _plan(repository)
        assert comparison.kind is ContentKind.VALUE_CHANGED and ("retired_concept", 1.0, None) in comparison.changed

    @pytest.mark.parametrize("field, value", [("published_at", datetime(2021, 3, 1, tzinfo=timezone.utc)),
                                              ("period_start", date(2020, 2, 1)),
                                              ("raw_reference", "https://www.sec.gov/Archives/edgar/data/1234567/other/")])
    def test_a_changed_period_publication_or_source_is_held(self, repository, field, value):
        (doc,) = _docs()
        _store(repository, replace(_legacy_document(doc), **{field: value}))
        ((comparison, record),) = _plan(repository)
        assert comparison.kind is ContentKind.VALUE_CHANGED and record is None

    def test_provenance_already_stored_that_differs_is_held(self, repository):
        (doc,) = _docs()
        _store(repository, _legacy_document(doc, shares_outstanding_filed="2021-03-01"))
        ((comparison, record),) = _plan(repository)
        assert comparison.kind is ContentKind.VALUE_CHANGED and record is None

    def test_different_content_with_nothing_added_is_held(self, repository):
        (doc,) = _docs()
        _store(repository, _legacy_document(doc, drop=(), content_hash="something-else"))
        ((comparison, record),) = _plan(repository)
        assert comparison.kind is ContentKind.VALUE_CHANGED and comparison.changed[0][0] == "content_hash"

    def test_a_period_atlas_holds_no_statement_for_is_held(self, repository):
        (doc2020, doc2021) = _docs(payload=_payload(periods=("2020", "2021")))
        _store(repository, _legacy_document(doc2020))
        plan = content_refresh_records((doc2020, doc2021), tuple(repository.get_by_company("SYN")), evaluated_at=FETCHED_AT)
        kinds = {c.period_end: (c.kind, r is None) for c, r in plan}
        assert kinds == {"2020-12-31": (ContentKind.ADDITIONS_ONLY, False), "2021-12-31": (ContentKind.NEW_PERIOD, True)}

    def test_comparison_is_deterministic_in_any_order(self, repository):
        docs = _docs(payload=_payload(periods=("2019", "2020")))
        for d in docs:
            _store(repository, _legacy_document(d))
        records = tuple(repository.get_by_company("SYN"))
        assert compare_statements(docs, records) == compare_statements(docs[::-1], records[::-1])
        assert content_refresh_records(docs, records, evaluated_at=FETCHED_AT) == \
            content_refresh_records(docs, records, evaluated_at=FETCHED_AT)


# -- the command ---------------------------------------------------------------------------------------------


class _Network:
    """Every outbound request the process makes: companyfacts is served, any
    other URL (Alpha Vantage, a ticker map, a filing index) fails the test."""

    def __init__(self, payloads):
        self.payloads, self.urls = payloads, []

    def get(self, url, headers=None, timeout=None):
        self.urls.append(url)
        for cik, payload in self.payloads.items():
            if url == f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json":
                return type("R", (), {"status_code": 200, "json": staticmethod(lambda p=payload: p), "text": ""})()
        raise AssertionError(f"unexpected request: {url}")


@pytest.fixture
def network(monkeypatch):
    net = _Network({CIK: _payload()})
    monkeypatch.setattr(provider_http.httpx, "get", net.get)
    return net


def _statement_for(ticker, doc):
    """The same statement filed for another company symbol (a control)."""
    return replace(doc, company=ticker, identifier=doc.identifier.replace("SYN", ticker))


def _seed(repository, *tickers):
    (doc,) = _docs()
    for ticker in tickers:
        legacy = _legacy_document(_statement_for(ticker, doc))
        _store(repository, legacy)
        quote = RawBusinessDocument(
            identifier=f"{ticker}:quote:2026-09-01", company=ticker, source_kind="market_data_snapshot",
            published_at=datetime(2026, 9, 1, tzinfo=timezone.utc), provider_id="alpha_vantage",
            raw_reference=f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}",
            content_hash=hashlib.sha256(ticker.encode()).hexdigest(), period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 1), language="en",
            metadata={"share_price": 10.0, "price_basis": "raw", "currency": "USD"})
        _store(repository, quote)


def _run(tmp_path, *args):
    return command.main(["--database", str(tmp_path / "atlas.db"), *args])


def _save_only(tmp_path):
    """The saved evidence a fetch would leave, without applying it."""
    command._save(tmp_path / "saved", CIK, ["SYN"], _payload(), FETCHED_AT)


class TestCommand:
    def test_save_makes_exactly_one_companyfacts_request_and_nothing_else(self, repository, network, tmp_path, capsys):
        _seed(repository, "SYN")
        assert _run(tmp_path, "--tickers", "SYN", "--save-fetched", str(tmp_path / "saved"), "--max-requests", "1") == 0
        assert network.urls == [f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK}.json"]
        manifest = json.loads((tmp_path / "saved" / "manifest.json").read_text())
        entry = manifest[CIK]
        assert entry["sha256"] == hashlib.sha256((tmp_path / "saved" / entry["file"]).read_bytes()).hexdigest()
        assert "Alpha Vantage requests made: 0" in capsys.readouterr().out

    def test_the_request_cap_stops_before_any_request(self, repository, network, tmp_path, capsys):
        _seed(repository, "SYN")
        assert _run(tmp_path, "--tickers", "SYN", "--save-fetched", str(tmp_path / "saved")) == 1
        assert network.urls == [] and "STOPPED" in capsys.readouterr().out

    def test_a_dry_run_asks_nothing_and_writes_nothing(self, repository, network, tmp_path):
        _seed(repository, "SYN")
        before = repository.get_by_company("SYN")
        assert _run(tmp_path, "--tickers", "SYN", "--save-fetched", str(tmp_path / "saved"), "--max-requests", "1",
                    "--dry-run") == 0
        assert network.urls == [] and repository.get_by_company("SYN") == before

    def test_a_replayed_dry_run_reports_the_plan_and_writes_nothing(self, repository, network, tmp_path, capsys):
        _seed(repository, "SYN")
        _run(tmp_path, "--tickers", "SYN", "--save-fetched", str(tmp_path / "saved"), "--max-requests", "1", "--dry-run")
        _save_only(tmp_path)
        before = repository.get_by_company("SYN")
        capsys.readouterr()
        assert _run(tmp_path, "--tickers", "SYN", "--from-fetched", str(tmp_path / "saved"), "--dry-run") == 0
        out = capsys.readouterr().out
        assert "additions_only 1" in out and "versions that would be written: 1" in out
        assert repository.get_by_company("SYN") == before

    def test_replay_asks_nothing_and_writes_the_same_rows(self, repository, network, tmp_path):
        _seed(repository, "SYN")
        _run(tmp_path, "--tickers", "SYN", "--save-fetched", str(tmp_path / "saved"), "--max-requests", "1")
        fetched = {r.id: r for r in repository.get_by_company("SYN")}
        other = tmp_path / "copy"
        other.mkdir()
        engine = create_engine(f"sqlite:///{other / 'atlas.db'}", future=True)
        create_business_record_table(engine)
        _seed(replica := SqlAlchemyBusinessRecordRepository(engine), "SYN")
        network.urls.clear()
        assert command.main(["--database", str(other / "atlas.db"), "--tickers", "SYN", "--from-fetched",
                             str(tmp_path / "saved")]) == 0
        assert network.urls == []
        assert {r.id: r for r in replica.get_by_company("SYN")} == fetched

    def test_a_tampered_saved_payload_stops(self, repository, network, tmp_path):
        _seed(repository, "SYN")
        _run(tmp_path, "--tickers", "SYN", "--save-fetched", str(tmp_path / "saved"), "--max-requests", "1")
        payload = tmp_path / "saved" / f"companyfacts_CIK{CIK}.json"
        payload.write_text(payload.read_text().replace("1000.0", "1001.0"))
        with pytest.raises(SystemExit, match="checksum"):
            _run(tmp_path, "--tickers", "SYN", "--from-fetched", str(tmp_path / "saved"))

    def test_append_only_and_a_rerun_writes_nothing(self, repository, network, tmp_path, capsys):
        _seed(repository, "SYN")
        legacy = {r.id: r for r in repository.get_by_company("SYN")}
        _run(tmp_path, "--tickers", "SYN", "--save-fetched", str(tmp_path / "saved"), "--max-requests", "1")
        after = {r.id: r for r in repository.get_by_company("SYN")}
        assert all(after[i] == r for i, r in legacy.items()) and len(after) == len(legacy) + 1
        capsys.readouterr()
        _run(tmp_path, "--tickers", "SYN", "--from-fetched", str(tmp_path / "saved"))
        out = capsys.readouterr().out
        assert "versions written: 0" in out and "identical 1" in out
        assert {r.id for r in repository.get_by_company("SYN")} == set(after)

    def test_only_the_named_tickers_statements_change_no_quote_no_control(self, repository, network, tmp_path):
        _seed(repository, "SYN", "CTL")  # CTL: a control with the same pending shape, not named
        control_before = repository.get_by_company("CTL")
        quotes_before = [r for r in repository.get_by_company("SYN") if r.document_type.value == "market_data_snapshot"]
        _run(tmp_path, "--tickers", "SYN", "--save-fetched", str(tmp_path / "saved"), "--max-requests", "1")
        assert repository.get_by_company("CTL") == control_before
        assert [r for r in repository.get_by_company("SYN") if r.document_type.value == "market_data_snapshot"] == quotes_before

    def test_every_input_a_stored_fact_gave_is_unchanged_by_additions(self, repository, network, tmp_path):
        _seed(repository, "SYN")

        def facts():
            heads = latest_versions(repository.get_by_company("SYN"))
            business = {(f.kind.value, f.period, f.value) for f in extract_facts_from_records(heads, evaluated_at=FETCHED_AT)}
            market = {(f.kind.value, f.period, f.value) for f in extract_valuation_facts_from_records(heads, evaluated_at=FETCHED_AT)}
            return business, market

        (business, market) = facts()
        _run(tmp_path, "--tickers", "SYN", "--save-fetched", str(tmp_path / "saved"), "--max-requests", "1")
        after_business, after_market = facts()
        # Every fact the stored version gave is given again, unchanged; only an
        # added concept may add facts of its own.
        assert business <= after_business and after_market == market
        assert not {(k, p) for k, p, _ in after_business - business} & {(k, p) for k, p, _ in business}

    def test_tickers_are_required(self, repository, tmp_path):
        with pytest.raises(SystemExit):
            command.main(["--database", str(tmp_path / "atlas.db"), "--from-fetched", str(tmp_path)])

    def test_a_ticker_with_no_single_filer_is_refused(self, repository, network, tmp_path, capsys):
        assert _run(tmp_path, "--tickers", "NONE", "--save-fetched", str(tmp_path / "saved"), "--max-requests", "1") == 0
        assert "REFUSED NONE" in capsys.readouterr().out and network.urls == []


class TestTheExistingProvenancePathStands:
    def test_identical_content_still_enriches_through_apply_sec(self, repository):
        (doc,) = _docs()
        _store(repository, _legacy_document(doc, drop=(), content_hash=doc.content_hash))
        outcome = apply_sec((doc,), repository.get_by_company("SYN"), add=repository.add, evaluated_at=FETCHED_AT)
        assert outcome.enriched == 1

    def test_additions_are_still_refused_by_the_provenance_enrichment(self, repository):
        (doc,) = _docs()
        _store(repository, _legacy_document(doc))
        outcome = apply_sec((doc,), repository.get_by_company("SYN"), add=repository.add, evaluated_at=FETCHED_AT)
        assert (outcome.enriched, outcome.held_content_changed) == (0, [doc.identifier])


# -- Amazon: its real saved payload against its real stored v1 statements --------------------------------------

AMZN_CIK = "0001018724"


def _amazon_heads(repository):
    for h in json.loads((FIXTURES / "amzn_statements_v1.json").read_text()):
        doc = RawBusinessDocument(
            identifier=h["identifier"], company=h["company"], source_kind="financial_statement",
            published_at=datetime.fromisoformat(h["published_at"]), provider_id=h["provider_id"],
            raw_reference=h["source_reference"], content_hash=h["content_hash"],
            period_start=date.fromisoformat(h["period_start"]), period_end=date.fromisoformat(h["period_end"]),
            language=h["language"], metadata=h["metadata"])
        record = _store(repository, doc)
        assert record.id == h["id"]  # the very lineage and version Atlas stores


class TestAmazon:
    def _plan(self, repository):
        payload = json.loads((FIXTURES / "companyfacts_CIK0001018724_trimmed.json").read_text())
        documents = statement_documents("AMZN", AMZN_CIK, payload)
        return content_refresh_records(documents, tuple(repository.get_by_company("AMZN")), evaluated_at=FETCHED_AT)

    def test_every_legacy_statement_is_additions_only(self, repository):
        _amazon_heads(repository)
        plan = self._plan(repository)
        assert len(plan) == 19 and {c.kind for c, _ in plan} == {ContentKind.ADDITIONS_ONLY}
        assert all(r is not None and r.version.version_number == 2 for _, r in plan)
        assert all(c.changed == () for c, _ in plan)

    def test_fcf_and_share_counts_are_unchanged_and_first_reports_are_filed(self, repository):
        _amazon_heads(repository)
        stored = {r.period_end: r for r in repository.get_by_company("AMZN")}
        first = {}
        for comparison, record in self._plan(repository):
            head = stored[record.period_end]
            assert record.metadata["free_cash_flow"] == head.metadata["free_cash_flow"]
            assert record.metadata.get("shares_outstanding") == head.metadata.get("shares_outstanding")
            if "shares_outstanding_first_reported_filed" in record.metadata:
                first[record.period_end.year] = record.metadata["shares_outstanding_first_reported_filed"]
        assert first[2010] == "2011-01-28" and first[2020] == "2021-02-03"
        assert all(first[y] < "2022-06-06" for y in range(2008, 2021))  # every pre-split count first filed pre-split

    def test_the_legacy_versions_survive(self, repository):
        _amazon_heads(repository)
        before = {r.id: r for r in repository.get_by_company("AMZN")}
        for _, record in self._plan(repository):
            repository.add(record)
        after = {r.id: r for r in repository.get_by_company("AMZN")}
        assert all(after[i] == r for i, r in before.items()) and len(after) == 38


def test_no_issuer_is_named_in_the_tool():
    names = ("AMZN", "AAPL", "Amazon", "Apple", "0001018724", "0000320193", "1018724")
    for module in ("atlas/alpha/business_data_refresh/sec_statement_content.py", "atlas/dev/refresh_sec_statement_content.py"):
        tree = ast.parse((ROOT / module).read_text())
        literals = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        assert not [lit for lit in literals for name in names if name in lit], module


def test_the_tool_reaches_no_market_data_provider():
    for module in ("atlas/alpha/business_data_refresh/sec_statement_content.py", "atlas/dev/refresh_sec_statement_content.py"):
        imported = {n.module for n in ast.walk(ast.parse((ROOT / module).read_text())) if isinstance(n, ast.ImportFrom)}
        assert not [m for m in imported if m and ("alpha_vantage" in m or "price_refresh" in m or m.endswith(".service"))], module
