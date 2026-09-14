"""Historical Market-Data Backfill -- the operator command that fills in
provenance on observations Atlas already holds.

What a reviewer cannot check by reading: that a finished company costs no
request, that only stored months are touched, that a revision or a new
month is held rather than written, that the budget gate and the provider's
own daily rejection stop the run, that re-running writes nothing, and that
no valuation input moves. Real adapters over fake fetchers, in-memory
SQLite, no network.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import fields, replace
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.provider_state import (
    ALPHA_VANTAGE_PROVIDER_NAME,
    ProviderAvailability,
    ProviderAvailabilityStore,
    ProviderBudgetGate,
)
from atlas.alpha.business_data_refresh.quota import AlphaVantageQuotaTracker
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import (
    SHARE_COUNT_PROVENANCE_KEYS,
    IngestedRecord,
    ProvenanceEnrichmentRefused,
    enrich_provenance,
    ingest,
)
from atlas.analysis_engine.business_data.versioning import latest_versions
from atlas.analysis_engine.valuation.contracts import ValuationDecisionEligibility
from atlas.analysis_engine.valuation.facts import (
    PriceBasis,
    extract_valuation_facts_from_records,
    market_price_provenance,
)
from atlas.business_data_providers.alpha_vantage import AlphaVantageMarketDataProvider
from atlas.business_data_providers.sec_edgar import SecEdgarFundamentalsProvider
from atlas.dev.backfill_market_data_provenance import (
    CORE,
    MULTI_CLASS,
    PRICE_ONLY,
    apply,
    apply_prices,
    apply_sec,
    classify,
    fetch,
    is_price_complete,
    Fetched,
    load_fetched,
    plan_prices,
    plan_sec,
    restrict,
    save_fetched,
)
from tests.unit.business_data_providers.test_market_data_provenance import _BAR_2012_10, _BAR_2014_05
from tests.unit.business_data_providers.test_sec_edgar import _TICKER_MAP, _companyfacts, _instant_entry, _usd_entry
from tests.unit.business_data_providers.test_sec_edgar import _fake_fetcher as _sec_fetcher

LEGACY_AT = datetime(2026, 8, 10, tzinfo=timezone.utc)
NOW = datetime(2026, 9, 14, tzinfo=timezone.utc)
SERIES = {"2012-10-31": _BAR_2012_10, "2014-05-30": _BAR_2014_05}
SHARES = {"AAPL": 14_594_180_000.0, "NVDA": 24_221_000_000.0}
_DAILY_REJECTION = {
    "Information": "We have detected your API key as XXXX and our standard API rate limit is 25 requests per day."
}


def _engine():
    return create_engine("sqlite://", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})


@pytest.fixture
def repository():
    engine = _engine()
    create_business_record_table(engine)
    return SqlAlchemyBusinessRecordRepository(engine)


@pytest.fixture
def counter():
    engine = _engine()
    quota = AlphaVantageQuotaTracker(engine)
    gate = ProviderBudgetGate(quota, ProviderAvailabilityStore(engine), provider_name=ALPHA_VANTAGE_PROVIDER_NAME)
    return quota, gate


class _Fetcher:
    """Alpha Vantage over canned series per ticker; logs every endpoint."""

    def __init__(self, series_by_ticker: dict[str, dict], *, reject: set[str] = frozenset()):
        self.series_by_ticker = series_by_ticker
        self.reject = reject
        self.calls: list[tuple[str, str]] = []

    def __call__(self, url, headers):
        function = url.split("function=")[1].split("&")[0]
        ticker = url.split("symbol=")[1].split("&")[0]
        self.calls.append((function, ticker))
        if ticker in self.reject:
            return _DAILY_REJECTION
        if function == "TIME_SERIES_MONTHLY_ADJUSTED":
            return {"Monthly Adjusted Time Series": self.series_by_ticker[ticker]}
        if function == "OVERVIEW":
            return {"Symbol": ticker, "Currency": "USD", "SharesOutstanding": str(int(SHARES.get(ticker, 1_000_000_000.0)))}
        raise AssertionError(f"unexpected request: {function}")


def _av(fetcher, quota=None):
    return AlphaVantageMarketDataProvider(
        fetcher, sleeper=lambda s: None, api_key="k", on_request=quota.record_call if quota else None
    )


def _legacy(doc):
    """`doc` as written before provenance: no basis, no raw close, no dividend."""
    metadata = {k: v for k, v in doc.metadata.items() if k not in ("price_basis", "raw_close", "dividend_amount")}
    content_hash = hashlib.sha256(
        json.dumps({"date": doc.period_start.isoformat(), **metadata}, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return type(doc)(**{**doc.__dict__, "metadata": metadata, "content_hash": content_hash})


def _store(repository, doc, *, evaluated_at=LEGACY_AT, **identity):
    result = ingest(doc, existing_records=repository.get_by_company(doc.company), evaluated_at=evaluated_at)
    assert isinstance(result, IngestedRecord), result
    record = replace(result.record, **identity)
    repository.add(record)
    return record


def _legacy_history(repository, ticker="AAPL", series=SERIES, **identity):
    """Monthly snapshots as the historical stage wrote them before provenance."""
    documents = _av(_Fetcher({ticker: series})).fetch_historical_snapshots(
        company_identifier=ticker, filing_dates=tuple(date.fromisoformat(d) for d in series), evaluated_at=LEGACY_AT
    )
    return [_store(repository, _legacy(d), **identity) for d in documents]


def _raw(ticker, kind, identifier, metadata, *, period_end=date(2024, 12, 31)):
    return RawBusinessDocument(
        identifier=f"{ticker}:{identifier}", company=ticker, source_kind=kind,
        published_at=datetime(2025, 2, 1, tzinfo=timezone.utc), provider_id="sec_edgar",
        raw_reference=f"https://example.test/{ticker}/{identifier}",
        content_hash=hashlib.sha256(json.dumps([ticker, identifier, metadata], sort_keys=True).encode()).hexdigest(),
        period_start=period_end, period_end=period_end, language="en", metadata=metadata,
    )


def _statements(repository, ticker, *, counts=3, form="10-K", issuer=None):
    for year in range(2021, 2025):
        metadata = {"sec_form": form, "revenue": 1.0}
        if year - 2021 < counts:
            metadata["shares_outstanding"] = 1_000.0
        _store(repository, _raw(ticker, "financial_statement", f"fy{year}", metadata, period_end=date(year, 12, 31)),
               canonical_issuer_id=issuer)


def _profile(repository, ticker, industry="SEMICONDUCTORS"):
    _store(repository, _raw(ticker, "company_profile", "profile", {"industry": industry}))


def _core(repository, ticker="AAPL", **identity):
    _statements(repository, ticker)
    _profile(repository, ticker)
    return _legacy_history(repository, ticker, **identity)


def _plan(repository, ticker="AAPL", **kwargs):
    records = repository.get_by_company(ticker)
    return plan_prices(ticker, records, category=classify(ticker, records, issuer_companies=lambda i: {ticker}), **kwargs)


def _monthly_heads(repository, ticker="AAPL"):
    return sorted(
        (r for r in latest_versions(repository.get_by_company(ticker)) if "MONTHLY" in (r.source_reference or "")),
        key=lambda r: r.period_end,
    )


def _valuation_inputs(repository, ticker="AAPL"):
    facts = extract_valuation_facts_from_records(latest_versions(repository.get_by_company(ticker)), evaluated_at=NOW)
    return sorted((f.kind.value, f.value, f.unit, f.period) for f in facts)


# -- completion ---------------------------------------------------------------------------------------------


class TestCompletion:
    def _fresh(self, bar):
        (doc,) = _av(_Fetcher({"AAPL": {"2012-10-31": bar}})).fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date(2012, 10, 31),), evaluated_at=NOW
        )
        return ingest(doc, evaluated_at=NOW).record

    def test_a_legacy_month_is_pending(self, repository):
        (legacy, _) = _legacy_history(repository)
        assert not is_price_complete(legacy)
        assert market_price_provenance(legacy).basis is PriceBasis.SPLIT_AND_DIVIDEND_ADJUSTED  # still readable

    def test_an_explicit_zero_dividend_is_complete(self):
        record = self._fresh(_BAR_2012_10)
        assert record.metadata["dividend_amount"] == 0.0
        assert is_price_complete(record)

    def test_a_month_without_a_raw_close_stays_pending(self):
        assert not is_price_complete(self._fresh({k: v for k, v in _BAR_2012_10.items() if k != "4. close"}))

    def test_a_month_without_a_dividend_field_stays_pending(self):
        assert not is_price_complete(self._fresh({k: v for k, v in _BAR_2012_10.items() if k != "7. dividend amount"}))


# -- eligibility --------------------------------------------------------------------------------------------


class TestEligibility:
    def _classify(self, repository, ticker, issuers=None):
        issuers = issuers or {}
        return classify(ticker, repository.get_by_company(ticker), issuer_companies=lambda i: issuers.get(i, {ticker}))

    def test_a_domestic_single_class_company_with_counts_is_core(self, repository):
        _core(repository)
        assert self._classify(repository, "AAPL") == CORE

    def test_a_multi_class_issuer_is_refused_even_when_only_an_earlier_version_names_it(self, repository):
        _core(repository, "GOOGL")
        (statement,) = [r for r in repository.get_by_company("GOOGL") if r.identifier == "GOOGL:fy2021"]
        repository.add(replace(statement, id=statement.id.replace(":v1", ":v0"), canonical_issuer_id="issuer-1"))
        assert self._classify(repository, "GOOGL", {"issuer-1": {"GOOG", "GOOGL"}}) == "multi_class"

    def test_a_foreign_listing_is_refused(self, repository):
        _statements(repository, "TSM", form="20-F")
        _profile(repository, "TSM")
        _legacy_history(repository, "TSM")
        assert self._classify(repository, "TSM") == "foreign_listing"

    def test_a_bank_is_refused(self, repository):
        _statements(repository, "JPM")
        _profile(repository, "JPM", "BANKS - DIVERSIFIED")
        _legacy_history(repository, "JPM")
        assert self._classify(repository, "JPM") == "not_applicable"

    def test_a_company_without_monthly_prices_has_nothing_to_backfill(self, repository):
        _statements(repository, "AVGO")
        _profile(repository, "AVGO")
        assert self._classify(repository, "AVGO") == "no_price_history"

    def test_prices_without_share_counts_are_price_only(self, repository):
        _statements(repository, "V", counts=2)
        _profile(repository, "V", "CREDIT SERVICES")
        _legacy_history(repository, "V")
        assert self._classify(repository, "V") == PRICE_ONLY

    def test_price_only_is_refused_unless_asked_for(self, repository):
        _statements(repository, "V", counts=2)
        _profile(repository, "V", "CREDIT SERVICES")
        _legacy_history(repository, "V")
        assert _plan(repository, "V").refusal and _plan(repository, "V").calls == 0
        assert _plan(repository, "V", allow_price_only=True).calls == 1


# -- the plan -----------------------------------------------------------------------------------------------


class TestPlan:
    def test_a_pending_company_costs_exactly_one_request(self, repository):
        _core(repository)
        plan = _plan(repository)
        assert (plan.months, plan.complete, len(plan.pending), plan.calls) == (2, 0, 2, 1)
        assert plan.pending == (date(2012, 10, 31), date(2014, 5, 30))
        assert (plan.known_currency, plan.known_shares_outstanding) == ("USD", SHARES["AAPL"])

    def test_a_complete_company_costs_nothing(self, repository, counter):
        _core(repository)
        fetcher = _Fetcher({"AAPL": SERIES})
        apply(fetch([_plan(repository)], [], providers=(_av(fetcher),), gate=counter[1], max_calls=5, fetched_at=NOW),
              repository)
        plan = _plan(repository)
        assert (plan.complete, plan.pending, plan.calls) == (2, (), 0)

    def test_stored_months_that_disagree_on_the_share_count_are_refused(self, repository):
        _core(repository)
        head = _monthly_heads(repository)[0]
        repository.add(replace(head, id=f"{head.lineage_id}:v2", metadata={**head.metadata, "shares_outstanding": 1.0},
                               version=replace(head.version, version_number=2, supersedes=head.id)))
        plan = _plan(repository)
        assert plan.refusal and plan.calls == 0


class TestMultiClassOptIn:
    """A security of a multi-class issuer: its bars are its own, so its price
    provenance may be backfilled -- only when the operator names it."""

    def _multi_class_plan(self, repository, **kwargs):
        _core(repository)
        (statement,) = [r for r in repository.get_by_company("AAPL") if r.identifier == "AAPL:fy2021"]
        repository.add(replace(statement, id=statement.id.replace(":v1", ":v0"), canonical_issuer_id="issuer-1"))
        records = repository.get_by_company("AAPL")
        category = classify("AAPL", records, issuer_companies={"issuer-1": {"AAPL", "AAPL.B"}}.get)
        return category, plan_prices("AAPL", records, category=category, **kwargs)

    def test_refused_without_the_opt_in(self, repository):
        category, plan = self._multi_class_plan(repository)
        assert category == MULTI_CLASS and plan.refusal and plan.calls == 0

    def test_planned_with_it_and_still_one_request(self, repository):
        _, plan = self._multi_class_plan(repository, allow_multi_class=True)
        assert (plan.refusal, plan.calls, plan.known_shares_outstanding) == (None, 1, SHARES["AAPL"])

    def test_the_opt_in_opens_nothing_else(self, repository):
        _core(repository)
        records = repository.get_by_company("AAPL")
        plan = plan_prices("AAPL", records, category="foreign_listing", allow_multi_class=True)
        assert plan.refusal == "foreign_listing"
        assert plan_sec("AAPL", records, category=MULTI_CLASS).refusal == MULTI_CLASS


# -- the price backfill -------------------------------------------------------------------------------------


def _run(repository, gate, fetcher, tickers=("AAPL",), *, quota=None, max_calls=13):
    plans = [_plan(repository, t) for t in tickers]
    fetched = fetch(plans, [], providers=(_av(fetcher, quota),), gate=gate, max_calls=max_calls, fetched_at=NOW)
    apply(fetched, repository)
    return fetched


class TestPriceBackfill:
    def test_aapl_replay_adds_the_raw_close_and_dividend_beside_the_unchanged_price(self, repository, counter):
        legacy = _core(repository)
        before = _valuation_inputs(repository)
        _run(repository, counter[1], _Fetcher({"AAPL": SERIES}))
        heads = _monthly_heads(repository)
        assert [h.version.version_number for h in heads] == [2, 2]
        assert [h.version.supersedes for h in heads] == [r.id for r in legacy]
        p = [market_price_provenance(h) for h in heads]
        assert [(x.share_price, x.raw_close, x.dividend_amount, x.basis_recorded) for x in p] == [
            (17.881, 595.32, 0.0, True), (19.8081, 633.0, 3.29, True),
        ]
        assert all(x.retrieved_at == NOW for x in p)
        assert _valuation_inputs(repository) == before

    def test_one_monthly_request_and_never_overview(self, repository, counter):
        _core(repository)
        fetcher = _Fetcher({"AAPL": SERIES})
        _run(repository, counter[1], fetcher)
        assert fetcher.calls == [("TIME_SERIES_MONTHLY_ADJUSTED", "AAPL")]

    def test_the_legacy_version_stays_stored_and_readable(self, repository, counter):
        legacy = _core(repository)
        _run(repository, counter[1], _Fetcher({"AAPL": SERIES}))
        stored = {r.id: r for r in repository.get_by_company("AAPL")}
        for record in legacy:
            assert stored[record.id].metadata == record.metadata
            assert market_price_provenance(stored[record.id]).basis is PriceBasis.SPLIT_AND_DIVIDEND_ADJUSTED

    def test_a_revised_adjusted_close_is_held_not_written(self, repository):
        _core(repository)
        revised = {**SERIES, "2012-10-31": {**_BAR_2012_10, "5. adjusted close": "17.8810"}}
        revised["2014-05-30"] = {**_BAR_2014_05, "5. adjusted close": "19.7908"}
        documents = _av(_Fetcher({"AAPL": revised})).fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=_plan(repository).pending, evaluated_at=NOW,
            known_currency="USD", known_shares_outstanding=SHARES["AAPL"],
        )
        outcome = apply_prices(documents, repository.get_by_company("AAPL"), add=repository.add, evaluated_at=NOW)
        assert (outcome.new_versions, outcome.held_revisions) == (1, [("2014-05-30", 19.8081, 19.7908)])
        assert _monthly_heads(repository)[1].version.version_number == 1

    def test_a_month_atlas_does_not_hold_is_never_added(self, repository):
        _core(repository)
        documents = _av(_Fetcher({"AAPL": {**SERIES, "2012-11-30": _BAR_2012_10}})).fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date(2012, 11, 1),), evaluated_at=NOW,
            known_currency="USD", known_shares_outstanding=SHARES["AAPL"],
        )
        outcome = apply_prices(documents, repository.get_by_company("AAPL"), add=repository.add, evaluated_at=NOW)
        assert (outcome.new_versions, outcome.held_new_observations) == (0, ["AAPL:historical_snapshot:2012-11-30"])
        assert len(_monthly_heads(repository)) == 2

    def test_re_running_writes_nothing_and_requests_nothing(self, repository, counter):
        _core(repository)
        fetched = _run(repository, counter[1], _Fetcher({"AAPL": SERIES}))
        rows = {r.id for r in repository.get_by_company("AAPL")}
        apply(fetched, repository)  # the same documents again
        assert {r.id for r in repository.get_by_company("AAPL")} == rows
        fetcher = _Fetcher({"AAPL": SERIES})
        assert _run(repository, counter[1], fetcher).av_requests == 0 and fetcher.calls == []

    def test_a_stopped_run_resumes_with_only_what_is_still_pending(self, repository, counter):
        _core(repository, "AAPL")
        _core(repository, "NVDA")
        fetcher = _Fetcher({"AAPL": SERIES, "NVDA": SERIES})
        first = _run(repository, counter[1], fetcher, ("AAPL", "NVDA"), max_calls=1)
        assert (first.av_requests, first.stopped) == (1, "max-calls reached")
        assert [p.calls for p in (_plan(repository, "AAPL"), _plan(repository, "NVDA"))] == [0, 1]
        _run(repository, counter[1], fetcher, ("AAPL", "NVDA"))
        assert fetcher.calls == [("TIME_SERIES_MONTHLY_ADJUSTED", "AAPL"), ("TIME_SERIES_MONTHLY_ADJUSTED", "NVDA")]

    def test_nvda_backfill_keeps_its_identity_through_a_round_trip(self, repository, counter):
        _statements(repository, "NVDA")
        _profile(repository, "NVDA")
        _legacy_history(repository, "NVDA", canonical_security_id="sec-nvda", canonical_issuer_id="iss-nvda")
        before = _valuation_inputs(repository, "NVDA")
        _run(repository, counter[1], _Fetcher({"NVDA": SERIES}), ("NVDA",))
        for head in _monthly_heads(repository, "NVDA"):
            assert (head.canonical_security_id, head.canonical_issuer_id) == ("sec-nvda", "iss-nvda")
            assert head.metadata["shares_outstanding"] == SHARES["NVDA"]
            assert is_price_complete(head)
        assert _valuation_inputs(repository, "NVDA") == before

    def test_current_quotes_are_never_planned_or_touched(self, repository, counter):
        _core(repository)
        quote = _raw("AAPL", "market_data_snapshot", "quote", {"share_price": 230.0, "currency": "USD"})
        quote = type(quote)(**{**quote.__dict__, "provider_id": "alpha_vantage",
                               "raw_reference": "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL"})
        stored = _store(repository, quote)
        assert _plan(repository).months == 2
        _run(repository, counter[1], _Fetcher({"AAPL": SERIES}))
        assert [r for r in repository.get_by_company("AAPL") if r.lineage_id == stored.lineage_id] == [stored]


# -- the budget ---------------------------------------------------------------------------------------------


class TestBudget:
    def test_every_request_lands_in_the_shared_daily_counter(self, repository, counter):
        quota, gate = counter
        _core(repository, "AAPL")
        _core(repository, "NVDA")
        fetched = _run(repository, gate, _Fetcher({"AAPL": SERIES, "NVDA": SERIES}), ("AAPL", "NVDA"), quota=quota)
        assert fetched.av_requests == quota.calls_used_today() == 2

    def test_no_request_is_made_once_the_counter_is_spent(self, repository, counter):
        quota, gate = counter
        for _ in range(25):
            quota.record_call()
        _core(repository)
        fetcher = _Fetcher({"AAPL": SERIES})
        fetched = _run(repository, gate, fetcher, quota=quota)
        assert (fetched.av_requests, fetched.stopped, fetcher.calls) == (0, "budget gate: locally_exhausted", [])

    def test_the_providers_daily_rejection_stops_the_run_and_is_remembered(self, repository, counter):
        quota, gate = counter
        _core(repository, "AAPL")
        _core(repository, "NVDA")
        fetcher = _Fetcher({"AAPL": SERIES, "NVDA": SERIES}, reject={"AAPL"})
        fetched = _run(repository, gate, fetcher, ("AAPL", "NVDA"), quota=quota)
        assert (fetched.av_requests, fetched.stopped) == (1, "provider daily quota exhausted")
        assert fetcher.calls == [("TIME_SERIES_MONTHLY_ADJUSTED", "AAPL")]
        assert gate.current_state() is ProviderAvailability.PROVIDER_DAILY_EXHAUSTED
        assert not gate.has_budget()
        assert all(not is_price_complete(h) for h in _monthly_heads(repository))


# -- SEC share-count provenance -----------------------------------------------------------------------------


def _sec_docs():
    companyfacts = _companyfacts(
        {
            "Revenues": [_usd_entry(start="2012-09-30", end="2013-09-28", val=1000.0, filed="2013-10-30")],
            "CommonStockSharesOutstanding": [
                _instant_entry(end="2013-09-28", val=899_213_000.0, filed="2013-10-30", accn="0001193125-13-416534"),
                _instant_entry(end="2013-09-28", val=6_294_494_000.0, filed="2014-10-27", accn="0001193125-14-383437"),
            ],
        },
        units={"CommonStockSharesOutstanding": "shares"},
    )
    fetcher = _sec_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
    return SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=NOW)


def _without_count_provenance(doc):
    return type(doc)(**{**doc.__dict__, "metadata": {k: v for k, v in doc.metadata.items() if k not in SHARE_COUNT_PROVENANCE_KEYS}})


class TestSecEnrichment:
    def test_a_stored_statement_gains_its_filing_provenance_with_the_same_content_hash(self, repository):
        (doc,) = _sec_docs()
        legacy = _store(repository, _without_count_provenance(doc))
        before = _valuation_inputs(repository)
        outcome = apply_sec((doc,), repository.get_by_company("AAPL"), add=repository.add, evaluated_at=NOW)
        assert outcome.enriched == 1
        (head,) = latest_versions(repository.get_by_company("AAPL"))
        assert (head.id, head.version.supersedes, head.content_hash) == (f"{legacy.lineage_id}:v2", legacy.id, legacy.content_hash)
        assert {k: head.metadata[k] for k in SHARE_COUNT_PROVENANCE_KEYS} == {k: doc.metadata[k] for k in SHARE_COUNT_PROVENANCE_KEYS}
        assert head.metadata["shares_outstanding"] == legacy.metadata["shares_outstanding"] == 6_294_494_000.0
        assert _valuation_inputs(repository) == before

    def test_enrichment_is_append_only(self, repository):
        (doc,) = _sec_docs()
        legacy = _store(repository, _without_count_provenance(doc))
        apply_sec((doc,), repository.get_by_company("AAPL"), add=repository.add, evaluated_at=NOW)
        stored = {r.id: r for r in repository.get_by_company("AAPL")}
        assert stored[legacy.id] == legacy

    def test_an_enriched_statement_is_skipped_on_a_re_run(self, repository):
        (doc,) = _sec_docs()
        _store(repository, _without_count_provenance(doc))
        apply_sec((doc,), repository.get_by_company("AAPL"), add=repository.add, evaluated_at=NOW)
        again = apply_sec((doc,), repository.get_by_company("AAPL"), add=repository.add, evaluated_at=NOW)
        assert (again.enriched, again.already_complete) == (0, 1)
        records = repository.get_by_company("AAPL")
        assert plan_sec("AAPL", records, category=CORE).calls == 0

    def test_a_restated_statement_is_held_never_rewritten(self, repository):
        (doc,) = _sec_docs()
        stored = _without_count_provenance(doc)
        _store(repository, type(stored)(**{**stored.__dict__, "content_hash": "restated-since"}))
        outcome = apply_sec((doc,), repository.get_by_company("AAPL"), add=repository.add, evaluated_at=NOW)
        assert (outcome.enriched, outcome.held_content_changed) == (0, [doc.identifier])
        assert len(repository.get_by_company("AAPL")) == 1

    def test_a_first_report_the_sec_does_not_give_stays_missing(self, repository):
        (doc,) = _sec_docs()
        _store(repository, _without_count_provenance(doc))
        partial = {k: v for k, v in doc.metadata.items() if not k.startswith("shares_outstanding_first_reported")}
        apply_sec((type(doc)(**{**doc.__dict__, "metadata": partial}),), repository.get_by_company("AAPL"),
                  add=repository.add, evaluated_at=NOW)
        (head,) = latest_versions(repository.get_by_company("AAPL"))
        assert "shares_outstanding_filed" in head.metadata
        assert not [k for k in head.metadata if k.startswith("shares_outstanding_first_reported")]


class TestEnrichProvenanceRefusals:
    def _head(self):
        (doc,) = _sec_docs()
        return doc, ingest(_without_count_provenance(doc), evaluated_at=LEGACY_AT).record

    def test_different_content_is_refused(self):
        doc, head = self._head()
        with pytest.raises(ProvenanceEnrichmentRefused, match="content differs"):
            enrich_provenance(type(doc)(**{**doc.__dict__, "content_hash": "other"}), head=head,
                              provenance_keys=SHARE_COUNT_PROVENANCE_KEYS, evaluated_at=NOW)

    def test_a_different_document_is_refused(self):
        doc, head = self._head()
        with pytest.raises(ProvenanceEnrichmentRefused, match="lineage"):
            enrich_provenance(type(doc)(**{**doc.__dict__, "identifier": "AAPL:other"}), head=head,
                              provenance_keys=SHARE_COUNT_PROVENANCE_KEYS, evaluated_at=NOW)

    def test_a_changed_value_outside_the_provenance_keys_is_refused(self):
        doc, head = self._head()
        with pytest.raises(ProvenanceEnrichmentRefused, match="non-provenance"):
            enrich_provenance(type(doc)(**{**doc.__dict__, "metadata": {**doc.metadata, "shares_outstanding": 1.0}}),
                              head=head, provenance_keys=SHARE_COUNT_PROVENANCE_KEYS, evaluated_at=NOW)

    def test_stored_provenance_is_never_overwritten(self):
        doc, head = self._head()
        head = replace(head, metadata={**head.metadata, "shares_outstanding_filed": "2015-01-01"})
        with pytest.raises(ProvenanceEnrichmentRefused, match="already stored"):
            enrich_provenance(doc, head=head, provenance_keys=SHARE_COUNT_PROVENANCE_KEYS, evaluated_at=NOW)

    def test_a_descriptive_key_the_stored_version_lacks_is_neither_required_nor_written(self):
        """A later adapter describes the statement more fully (`sec_taxonomy`,
        outside the content hash): nothing `head` holds changes, so the
        provenance is added -- and the extra key is not."""
        doc, head = self._head()
        head = replace(head, metadata={k: v for k, v in head.metadata.items() if k != "sec_taxonomy"})
        assert "sec_taxonomy" in doc.metadata
        enriched = enrich_provenance(doc, head=head, provenance_keys=SHARE_COUNT_PROVENANCE_KEYS, evaluated_at=NOW)
        assert "sec_taxonomy" not in enriched.metadata
        assert SHARE_COUNT_PROVENANCE_KEYS <= set(enriched.metadata)

    def test_a_key_the_stored_version_holds_must_be_repeated(self):
        doc, head = self._head()
        head = replace(head, metadata={**head.metadata, "sec_form": "10-K/A"})
        with pytest.raises(ProvenanceEnrichmentRefused, match="non-provenance"):
            enrich_provenance(doc, head=head, provenance_keys=SHARE_COUNT_PROVENANCE_KEYS, evaluated_at=NOW)

    def test_nothing_to_add_is_no_version(self):
        doc, _ = self._head()
        complete = ingest(doc, evaluated_at=LEGACY_AT).record
        assert enrich_provenance(doc, head=complete, provenance_keys=SHARE_COUNT_PROVENANCE_KEYS, evaluated_at=NOW) is None


# -- fetch once, apply twice --------------------------------------------------------------------------------


def test_saved_documents_apply_exactly_like_the_fetched_ones(repository, counter, tmp_path):
    engine = _engine()
    create_business_record_table(engine)
    other = SqlAlchemyBusinessRecordRepository(engine)
    for target in (repository, other):
        _core(target)
    fetched = fetch([_plan(repository)], [], providers=(_av(_Fetcher({"AAPL": SERIES})),), gate=counter[1],
                    max_calls=13, fetched_at=NOW)
    path = tmp_path / "fetched.json"
    save_fetched(fetched, str(path))
    loaded = load_fetched(str(path))
    assert loaded.av_requests == 0 and loaded.fetched_at == NOW
    assert loaded.prices == fetched.prices
    apply(fetched, repository)
    apply(loaded, other)
    rows = lambda repo: sorted((r.id, r.content_hash, dict(r.metadata), r.version.created_at) for r in repo.get_by_company("AAPL"))
    assert rows(repository) == rows(other)


def test_a_saved_fetch_applies_only_what_the_run_planned(monkeypatch, repository, counter, tmp_path, capsys):
    """`--from-fetched` with named `--tickers`: a company the saved file holds
    but the run did not name (or refused) is never written -- so
    `--accept-price-revisions` cannot reach it."""
    import sys

    import atlas.dev.backfill_market_data_provenance as command

    engine = _engine()
    create_business_record_table(engine)
    target = SqlAlchemyBusinessRecordRepository(engine)
    for ticker in ("AAPL", "NVDA"):
        _core(repository, ticker)
        _core(target, ticker)
    fetched = fetch([_plan(repository, "AAPL"), _plan(repository, "NVDA")], [],
                    providers=(_av(_Fetcher({"AAPL": SERIES, "NVDA": SERIES})),), gate=counter[1], max_calls=13,
                    fetched_at=NOW)
    path = tmp_path / "fetched.json"
    save_fetched(fetched, str(path))
    before = {t: sorted(r.id for r in target.get_by_company(t)) for t in ("AAPL", "NVDA")}
    monkeypatch.setattr(command, "create_engine", lambda *a, **k: engine)
    counter_engine = _engine()
    monkeypatch.setattr(command, "get_decision_engine", lambda: counter_engine)
    monkeypatch.setattr(sys, "argv", ["cmd", "--database", "x.db", "--tickers", "NVDA", "--prices",
                                      "--from-fetched", str(path), "--accept-price-revisions"])
    assert command.main() == 0
    out = capsys.readouterr().out
    assert "not applied: AAPL" in out and "Alpha Vantage   : 0 planned -- saved documents" in out
    assert sorted(r.id for r in target.get_by_company("AAPL")) == before["AAPL"]
    assert sorted(r.id for r in target.get_by_company("NVDA")) != before["NVDA"]


def test_restrict_keeps_only_the_planned_companies():
    saved = Fetched(fetched_at=NOW, prices={"A": (), "B": ()}, sec={"A": (), "C": ()})
    kept = restrict(saved, prices=["A"], sec=[])
    assert (list(kept.prices), list(kept.sec), kept.fetched_at) == (["A"], [], NOW)
    assert list(saved.prices) == ["A", "B"]  # the loaded fetch itself is untouched


# -- Held Historical Price Revision Acceptance ---------------------------------------------------------------

from atlas.dev.backfill_market_data_provenance import (  # noqa: E402
    RevisionKind,
    classify_price_revision,
    select_companies,
)


def _rescaled(series: dict, factor: float) -> dict:
    """The provider's history after a later dividend: every adjusted close
    rescaled by one factor and re-quoted to four decimals; raw closes untouched."""
    return {day: {**bar, "5. adjusted close": f"{float(bar['5. adjusted close']) * factor:.4f}"} for day, bar in series.items()}


def _nvda_pairs():
    from tests.unit.alpha.investment_case.test_historical_market_cap import CORPUS as REAL

    return [(b["legacy_adjusted"], b["adjusted"]) for b in REAL["NVDA"]["monthly"] if "legacy_adjusted" in b]


class TestRevisionClassification:
    def test_the_real_nvda_rescale_is_uniform_within_quote_rounding(self):
        """Adjusted closes from $0.30 to $177: least squares on the quotes
        finds the one factor; a median of ratios would be pulled by the
        noisy sub-dollar quotes."""
        r = classify_price_revision(_nvda_pairs())
        assert (r.kind, r.months) == (RevisionKind.UNIFORM_RESCALE, 17)
        assert r.factor == pytest.approx(0.998856, abs=2e-6) and r.max_residual <= 1e-4
        assert r.dividend_consistent and r.acceptable

    def test_near_uniform_is_not_accepted(self):
        r = classify_price_revision([(100.0, 99.80), (200.0, 199.70), (300.0, 299.40)])
        assert r.kind is RevisionKind.NEAR_UNIFORM_RESCALE and not r.acceptable

    def test_non_uniform_is_not_accepted(self):
        r = classify_price_revision([(100.0, 99.0), (200.0, 199.9)])
        assert r.kind is RevisionKind.NON_UNIFORM_REVISION and not r.acceptable

    def test_the_dividend_band_is_the_descriptive_drift_band(self):
        from atlas.alpha.investment_case.historical_market_cap import SMALL_STEP
        from atlas.dev.backfill_market_data_provenance import DIVIDEND_DRIFT_STEP

        assert DIVIDEND_DRIFT_STEP == SMALL_STEP[1]

    def test_one_month_cannot_show_uniformity(self):
        assert classify_price_revision([(100.0, 99.8)]).kind is RevisionKind.AMBIGUOUS

    def test_a_split_sized_or_upward_rescale_is_never_dividend_consistent(self):
        assert not classify_price_revision([(100.0, 50.0), (200.0, 100.0)]).acceptable
        assert not classify_price_revision([(100.0, 100.2), (200.0, 200.4)]).acceptable


def _alphabet_pairs(ticker: str) -> list[tuple[float, float]]:
    """(stored, revised) adjusted closes for GOOG or GOOGL's 11 held months
    (GOOG / GOOGL Held Historical Price Revision Acceptance), from the
    persisted corpus the descriptive tests rebuild."""
    corpus = json.loads((Path(__file__).resolve().parents[1] / "alpha" / "investment_case" / "fixtures"
                         / "historical_market_cap_corpus.json").read_text())
    return [(b["legacy_adjusted"], b["adjusted"]) for b in corpus[ticker]["monthly"]]


class TestAlphabetRevision:
    """Real controls: each class's revision is one uniform rescale within
    quote rounding, of the size and direction of one dividend adjustment."""

    @pytest.mark.parametrize("ticker, factor", [("GOOG", 0.9993442), ("GOOGL", 0.9993504)])
    def test_each_class_is_one_uniform_dividend_sized_rescale(self, ticker, factor):
        r = classify_price_revision(_alphabet_pairs(ticker))
        assert (r.kind, r.months, r.acceptable) == (RevisionKind.UNIFORM_RESCALE, 11, True)
        assert r.factor == pytest.approx(factor, abs=1e-7) and r.max_residual <= 1e-4

    def test_the_two_classes_differ_by_more_than_rounding_and_less_than_a_tenth_of_a_basis_point(self):
        """Diagnostic, never forced equal: one per-share adjustment on two
        classes trading at different prices gives two factors."""
        goog, googl = (classify_price_revision(_alphabet_pairs(t)).factor for t in ("GOOG", "GOOGL"))
        assert 1.5e-6 < abs(goog - googl) < 1e-5

    @pytest.mark.parametrize("ticker", ["GOOG", "GOOGL"])
    def test_one_perturbed_month_is_refused(self, ticker):
        pairs = _alphabet_pairs(ticker)
        uneven = [(o, n * 1.01) if i == 3 else (o, n) for i, (o, n) in enumerate(pairs)]
        assert classify_price_revision(uneven).kind is RevisionKind.NON_UNIFORM_REVISION
        nearly = [(o, n * 1.0003) if i == 3 else (o, n) for i, (o, n) in enumerate(pairs)]
        r = classify_price_revision(nearly)
        assert r.kind is RevisionKind.NEAR_UNIFORM_RESCALE and not r.acceptable


class TestHeldRevisionAcceptance:
    REVISED = _rescaled(SERIES, 0.998)

    def _fetch(self, repository, counter, *, accept, fetcher=None):
        fetcher = fetcher or _Fetcher({"AAPL": self.REVISED})
        fetched = fetch([_plan(repository)], [], providers=(_av(fetcher),), gate=counter[1], max_calls=13, fetched_at=NOW)
        documents = fetched.prices["AAPL"]
        return fetcher, apply_prices(documents, repository.get_by_company("AAPL"), add=repository.add,
                                     evaluated_at=NOW, accept_revisions=accept)

    def test_by_default_a_uniform_rescale_is_still_held(self, repository, counter):
        _core(repository)
        _, outcome = self._fetch(repository, counter, accept=False)
        assert (outcome.new_versions, len(outcome.held_revisions)) == (0, 2)
        assert outcome.revision.kind is RevisionKind.UNIFORM_RESCALE
        assert all(not is_price_complete(h) for h in _monthly_heads(repository))

    def test_explicit_acceptance_writes_the_revised_price_as_a_new_version(self, repository, counter):
        legacy = _core(repository)
        fetcher, outcome = self._fetch(repository, counter, accept=True)
        assert fetcher.calls == [("TIME_SERIES_MONTHLY_ADJUSTED", "AAPL")]  # one request, no OVERVIEW
        assert (outcome.new_versions, len(outcome.accepted_revisions), outcome.held_revisions) == (2, 2, [])
        heads = _monthly_heads(repository)
        assert [h.metadata["share_price"] for h in heads] == [17.8452, 19.7685]
        assert [h.version.supersedes for h in heads] == [r.id for r in legacy]
        for head in heads:
            p = market_price_provenance(head)
            assert (p.basis, p.basis_recorded) == (PriceBasis.SPLIT_AND_DIVIDEND_ADJUSTED, True)
            assert p.raw_close is not None and p.dividend_amount is not None and p.retrieved_at == NOW
        stored = {r.id: r for r in repository.get_by_company("AAPL")}
        assert all(stored[r.id] == r for r in legacy)  # the stored version stays, unchanged

    def test_valuation_reads_the_accepted_version(self, repository, counter):
        from atlas.analysis_engine.valuation.facts import ValuationFactKind, extract_valuation_facts_from_records

        _core(repository)
        self._fetch(repository, counter, accept=True)
        facts = extract_valuation_facts_from_records(latest_versions(repository.get_by_company("AAPL")), evaluated_at=NOW)
        prices = {f.period: f.value for f in facts if f.kind is ValuationFactKind.SHARE_PRICE}
        assert prices == {"2012-10-31": 17.8452, "2014-05-30": 19.7685}

    def test_a_non_uniform_revision_is_held_even_when_accepting(self, repository, counter):
        _core(repository)
        uneven = {**self.REVISED, "2014-05-30": {**SERIES["2014-05-30"], "5. adjusted close": "19.5000"}}
        _, outcome = self._fetch(repository, counter, accept=True, fetcher=_Fetcher({"AAPL": uneven}))
        assert outcome.revision.kind is RevisionKind.NON_UNIFORM_REVISION
        assert (outcome.new_versions, len(outcome.held_revisions)) == (0, 2)

    def test_a_revision_of_anything_but_the_price_is_never_accepted(self, repository, counter):
        _core(repository)
        head = _monthly_heads(repository)[0]
        repository.add(replace(head, id=f"{head.lineage_id}:v2", metadata={**head.metadata, "shares_outstanding": 1.0},
                               version=replace(head.version, version_number=2, supersedes=head.id)))
        plan = _plan(repository)
        assert plan.refusal  # the stored months no longer agree on the share count: refused before any request
        documents = _av(_Fetcher({"AAPL": self.REVISED})).fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date(2012, 10, 31), date(2014, 5, 30)), evaluated_at=NOW,
            known_currency="USD", known_shares_outstanding=SHARES["AAPL"],
        )
        outcome = apply_prices(documents, repository.get_by_company("AAPL"), add=repository.add, evaluated_at=NOW,
                               accept_revisions=True)
        assert ("2012-10-31", 17.881, 17.8452) not in outcome.accepted_revisions
        assert _monthly_heads(repository)[0].metadata["shares_outstanding"] == 1.0

    def test_a_second_run_plans_no_request(self, repository, counter):
        _core(repository)
        self._fetch(repository, counter, accept=True)
        assert _plan(repository).calls == 0

    def test_acceptance_writes_only_price_snapshots(self, repository, counter):
        _core(repository)
        before = {r.id for r in repository.get_by_company("AAPL")}
        self._fetch(repository, counter, accept=True)
        added = [r for r in repository.get_by_company("AAPL") if r.id not in before]
        assert added and {r.document_type.value for r in added} == {"market_data_snapshot"}

    def test_only_the_named_companies_are_selected(self):
        categories = {"AAPL": CORE, "MSFT": CORE, "NVDA": CORE, "V": PRICE_ONLY}
        assert select_companies(["MSFT", "NVDA"], categories, allow_price_only=False) == ["MSFT", "NVDA"]
        assert select_companies(None, categories, allow_price_only=False) == ["AAPL", "MSFT", "NVDA"]


class TestRevisionIsNotCompanyNews:
    """A uniform rescale of the adjusted history moves historical yields but
    is no company change: the analytical snapshot and the decision-memory
    identity carry no price or yield."""

    def _analysis(self, scale):
        from tests.unit.analysis_engine.valuation._issuer_basis import assemble_fixture_analysis as assemble_analysis
        from tests.unit.analysis_engine._fixtures import run_minimal

        def rec(kind, ident, day, published, ref="ref://x", **metadata):
            doc = RawBusinessDocument(
                identifier=ident, company="ACME", source_kind=kind, published_at=published, provider_id="p",
                raw_reference=ref, content_hash=f"{ident}-{sorted(metadata.items())}", language="en",
                period_start=day, period_end=day, metadata=metadata,
            )
            return ingest(doc, evaluated_at=NOW).record

        monthly = "https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol=ACME"
        records = [rec("company_profile", "ACME:profile", date(2025, 1, 1), NOW, industry="SEMICONDUCTORS")]
        for y, fcf in zip(range(2019, 2025), (10, 11, 12, 13, 14, 15)):
            records.append(rec("financial_statement", f"ACME:FY:{y}", date(y, 12, 31),
                               datetime(y + 1, 2, 10, tzinfo=timezone.utc), free_cash_flow=float(fcf), currency="USD"))
            records.append(rec("market_data_snapshot", f"ACME:m:{y + 1}", date(y + 1, 2, 28),
                               datetime(y + 1, 2, 28, tzinfo=timezone.utc), ref=monthly, currency="USD",
                               share_price=round(100.0 * 1.1 ** (y - 2019) * scale, 4), shares_outstanding=10.0))
        records.append(rec("market_data_snapshot", "ACME:quote", date(2026, 9, 10), datetime(2026, 9, 10, tzinfo=timezone.utc),
                           ref="https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=ACME",
                           currency="USD", share_price=150.0, shares_outstanding=10.0))
        engine_input, output = run_minimal()
        return assemble_analysis(engine_input, output, is_thesis_stale=False, business_records=tuple(records), generated_at=NOW)

    def test_a_uniform_rescale_moves_yields_but_creates_no_change_event(self):
        from atlas.analysis_engine.investment_case_change import capture_snapshot, compare_snapshots

        before, after = self._analysis(1.0), self._analysis(0.998)
        fb, fa = (next(f for f in a.valuation_engine.findings if f.fcf_yield_evidence is not None) for a in (before, after))
        assert fb.fcf_yield_evidence.eligibility is ValuationDecisionEligibility.ELIGIBLE
        assert fb.status is fa.status and fb.fcf_yield_evidence.prior_yields != fa.fcf_yield_evidence.prior_yields
        sb, sa = capture_snapshot(before), capture_snapshot(after)
        assert sb.content_hash == sa.content_hash and compare_snapshots(sb, sa).changes == ()

    def test_the_decision_memory_identity_carries_no_price_or_yield(self):
        from atlas.alpha.decision_memory.engine import DecisionSnapshotInputs

        assert not [f.name for f in fields(DecisionSnapshotInputs) if "yield" in f.name or "price" in f.name]
