"""Current share-count evidence (Current Share-Count Evidence v1): the
eligibility of one count, the append-only store and its identity join, the
temporal reader, and the provider cross-check. In-memory SQLite; the
end-to-end controls run the real trimmed corpus instances through the
write bridge."""
from __future__ import annotations

import math
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.security_share_evidence import (
    COVER_PARSER_VERSION,
    FilingRefused,
    ShareClassFilingSource,
    current_evidence_from_instance,
)
from atlas.alpha.security_share_evidence.current import (
    PROVIDER_FRESHNESS_UNDETERMINED,
    CurrentShareStatus,
    cross_check,
    read_current_shares,
)
from atlas.alpha.security_share_evidence.models import (
    CURRENT_COVER_SHARE_COUNT,
    HISTORICAL_PERIOD_END_SHARE_COUNT,
    CurrentShareCountEvidence,
    CurrentShareFiling,
    CurrentShareScope,
    SecurityShareCountObservation,
    ShareClassLinkKind,
)
from atlas.alpha.security_share_evidence.repository import SqlAlchemySecurityShareEvidenceRepository
from atlas.alpha.security_share_evidence.table import (
    create_current_share_evidence_tables,
    create_security_share_evidence_tables,
)
from atlas.business_data_providers.sec_edgar_share_classes import FetchedInstance
from tests.unit.alpha.security_share_evidence.test_repository import filing as historical_filing
from tests.unit.alpha.security_share_evidence.test_repository import listing_mics
from tests.unit.alpha.security_share_evidence.test_repository import observation as historical_observation

FIXTURES = Path(__file__).resolve().parents[2] / "business_data_providers" / "fixtures" / "cover_shares"
NOW = datetime(2026, 9, 14, tzinfo=timezone.utc)
RETRIEVED = datetime(2026, 9, 14, 17, 5, tzinfo=timezone.utc)
CIK = "0000000001"
PROVEN = ShareClassLinkKind.PROVEN_BY_SHARED_DIMENSION
LINKED, CONFLICT, AMBIGUOUS, MISSING = (CurrentShareStatus.LINKED, CurrentShareStatus.CONFLICT,
                                        CurrentShareStatus.AMBIGUOUS, CurrentShareStatus.MISSING)


def current(**overrides) -> CurrentShareCountEvidence:
    base = dict(
        issuer_cik=CIK, accession="0000000001-26-000007", form="10-Q", filing_date=date(2026, 8, 5),
        document_period_end=date(2026, 6, 30), as_of=date(2026, 7, 20), scope=CurrentShareScope.ISSUER,
        class_axis=None, class_member=None, shares=500.0, unit="shares", decimals="INF", conflict=False,
        concept="dei:EntityCommonStockSharesOutstanding", context_id="c-2", link_kind=PROVEN,
        cover_title="Common Stock", cover_symbol="AAA", cover_exchange="NASDAQ", cover_mic="XNAS",
        parser_version=COVER_PARSER_VERSION, retrieved_at=RETRIEVED, recorded_at=NOW,
    )
    base.update(overrides)
    return CurrentShareCountEvidence(**base)


def current_filing(evidence, **overrides) -> CurrentShareFiling:
    e = evidence[0]
    base = dict(
        issuer_cik=e.issuer_cik, accession=e.accession, form=e.form, filing_date=e.filing_date,
        document_period_end=e.document_period_end, fiscal_period="Q22026", instance_url="https://www.sec.gov/x_htm.xml",
        cover_rows=1, share_classes_reported=False, counts=len(evidence),
        proven=sum(1 for x in evidence if x.link_kind is PROVEN), ambiguous=0, no_link=0, conflicts=0,
        parser_version=e.parser_version, retrieved_at=e.retrieved_at, recorded_at=e.recorded_at,
    )
    base.update(overrides)
    return CurrentShareFiling(**base)


def _engine(*, tables=True):
    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool,
                           connect_args={"check_same_thread": False})
    if tables:
        create_current_share_evidence_tables(engine)
    return engine


def _repository(engine=None, listings=(("AAA", "XNAS"), ("BBB", "XNAS"))):
    return SqlAlchemySecurityShareEvidenceRepository(engine or _engine(), listing_mics=listing_mics(listings))


def _record(repo, *evidence):
    return repo.record_current_filing(current_filing(list(evidence)), tuple(evidence))


def _reading(repo, ticker="AAA", cik=CIK, on=date(2026, 9, 14)):
    return read_current_shares(ticker, repo.current_joined({ticker: cik})[ticker],
                               repo.current_evidence_for_issuers(frozenset({cik}))[cik], evaluated_on=on)


# -- eligibility of one count ---------------------------------------------------------------------------


class TestEligibility:
    def test_a_proven_positive_single_valued_share_count_dated_by_its_filing_is_usable(self):
        assert current().usable

    @pytest.mark.parametrize("change", [
        {"shares": 0.0}, {"shares": -5.0}, {"shares": None}, {"shares": math.nan}, {"shares": math.inf},
        {"conflict": True, "shares": None}, {"unit": "usd"}, {"link_kind": ShareClassLinkKind.AMBIGUOUS},
        {"link_kind": ShareClassLinkKind.NO_LINK}, {"as_of": date(2026, 8, 6)},  # dated after its own filing
    ])
    def test_anything_else_is_not(self, change):
        assert not current(**change).usable

    def test_the_two_evidence_types_are_distinct(self):
        assert current().evidence_type == CURRENT_COVER_SHARE_COUNT
        assert historical_observation().evidence_type == HISTORICAL_PERIOD_END_SHARE_COUNT
        assert CURRENT_COVER_SHARE_COUNT != HISTORICAL_PERIOD_END_SHARE_COUNT


# -- the store ---------------------------------------------------------------------------------------------


class TestStore:
    def test_round_trip_keeps_all_three_dates_apart(self):
        repo = _repository()
        e = current()
        assert _record(repo, e)
        (back,) = repo.current_evidence_for_issuers(frozenset({CIK}))[CIK]
        assert back == e
        assert (back.as_of, back.filing_date, back.retrieved_at.date()) == (date(2026, 7, 20), date(2026, 8, 5), date(2026, 9, 14))
        assert repo.current_processed((e.accession, "other")) == {e.accession: frozenset({COVER_PARSER_VERSION})}

    def test_recording_again_is_a_no_op(self):
        repo = _repository()
        e = current()
        assert _record(repo, e) is True
        assert _record(repo, replace(e, shares=999.0, recorded_at=RETRIEVED)) is False
        assert repo.current_evidence_for_issuers(frozenset({CIK}))[CIK] == (e,)

    def test_append_only_inserts_and_never_updates_or_deletes(self):
        engine = _engine()
        repo = _repository(engine)
        statements = []
        event.listen(engine, "before_cursor_execute", lambda *a: statements.append(a[2].split()[0].upper()))
        _record(repo, current())
        _record(repo, current())
        _record(repo, current(parser_version="cover_share_counts_v2"))
        assert set(statements) <= {"SELECT", "INSERT", "PRAGMA"} and "INSERT" in statements
        versions = {e.parser_version for e in repo.current_evidence_for_issuers(frozenset({CIK}))[CIK]}
        assert versions == {COVER_PARSER_VERSION, "cover_share_counts_v2"}  # a new version adds, the old stays

    def test_evidence_of_another_filing_is_refused_and_nothing_is_written(self):
        repo = _repository()
        with pytest.raises(ValueError):
            repo.record_current_filing(current_filing([current()]), (current(), current(accession="other", context_id="c-3")))
        assert repo.current_evidence_for_issuers(frozenset({CIK}))[CIK] == ()

    def test_reading_never_creates_a_table(self):
        engine = _engine(tables=False)
        repo = _repository(engine)
        assert repo.current_processed(("a",)) == {} and repo.current_joined({"AAA": CIK}) == {"AAA": ()}
        assert repo.current_evidence_for_issuers(frozenset({CIK})) == {CIK: ()}
        assert not sa_inspect(engine).get_table_names()

    def test_the_join_needs_proof_symbol_mic_and_filer(self):
        repo = _repository()
        _record(repo, current(context_id="c-1"), current(context_id="c-2", cover_mic="XNYS", shares=1.0),
                current(context_id="c-3", cover_symbol="BBB", shares=2.0),
                current(context_id="c-4", link_kind=ShareClassLinkKind.AMBIGUOUS, cover_symbol=None, cover_mic=None))
        joined = repo.current_joined({"AAA": CIK, "BBB": CIK, "CCC": CIK})
        assert [e.context_id for e in joined["AAA"]] == ["c-1"]
        assert [e.context_id for e in joined["BBB"]] == ["c-3"]
        assert joined["CCC"] == ()
        assert repo.current_joined({"AAA": "0000000002"})["AAA"] == ()  # another filer's symbol is not this one
        assert SqlAlchemySecurityShareEvidenceRepository(repo._engine).current_joined({"AAA": CIK}) == {"AAA": ()}

    def test_current_and_historical_evidence_never_meet(self):
        engine = _engine()
        create_security_share_evidence_tables(engine)
        repo = _repository(engine)
        rows = (historical_observation(cover_symbol="AAA", period_end=date(2026, 6, 30), filing_date=date(2026, 8, 5)),)
        repo.record_filing(historical_filing(list(rows)), rows)
        assert repo.current_joined({"AAA": CIK})["AAA"] == ()
        assert _reading(repo).status is MISSING  # a period-end count never satisfies the current reader
        _record(repo, current())
        assert repo.observations_for_issuer(CIK) == rows


# -- the reader --------------------------------------------------------------------------------------------


class TestReader:
    def test_a_count_is_visible_from_its_filing_date_on(self):
        repo = _repository()
        _record(repo, current())
        assert _reading(repo, on=date(2026, 8, 4)).status is MISSING  # filed tomorrow: not yet known
        on_the_day = _reading(repo, on=date(2026, 8, 5))
        assert (on_the_day.status, on_the_day.as_of_age_days, on_the_day.filing_age_days) == (LINKED, 16, 0)
        later = _reading(repo, on=date(2026, 9, 14))
        assert (later.evidence.shares, later.as_of_age_days, later.filing_age_days) == (500.0, 56, 40)

    def test_the_filing_date_never_stands_in_for_the_as_of_date(self):
        repo = _repository()
        _record(repo, current(as_of=date(2026, 7, 20), filing_date=date(2026, 8, 5)))
        reading = _reading(repo, on=date(2026, 9, 1))
        assert reading.evidence.as_of == date(2026, 7, 20) and reading.as_of_age_days == 43

    def test_the_latest_as_of_date_wins(self):
        repo = _repository()
        _record(repo, current())
        _record(repo, current(accession="0000000001-26-000011", filing_date=date(2026, 11, 4),
                              as_of=date(2026, 10, 28), shares=520.0))
        assert _reading(repo, on=date(2026, 9, 14)).evidence.shares == 500.0  # the later filing is invisible
        assert _reading(repo, on=date(2026, 11, 4)).evidence.shares == 520.0

    def test_disagreement_on_the_latest_date_is_withheld(self):
        repo = _repository()
        _record(repo, current(as_of=date(2026, 6, 1), shares=480.0, accession="0000000001-26-000004",
                              filing_date=date(2026, 6, 5)))
        _record(repo, current())
        _record(repo, current(accession="0000000001-26-000008", filing_date=date(2026, 8, 6), shares=501.0))
        reading = _reading(repo)
        assert (reading.status, reading.evidence) == (CONFLICT, None)  # never the older date, never either value

    @pytest.mark.parametrize("change", [{"conflict": True, "shares": None}, {"shares": 0.0}, {"shares": -1.0}])
    def test_an_unusable_latest_count_is_withheld(self, change):
        repo = _repository()
        _record(repo, current(**change))
        assert _reading(repo).status is CONFLICT and _reading(repo).evidence is None

    def test_ambiguous_is_not_missing(self):
        repo = _repository()
        _record(repo, current(link_kind=ShareClassLinkKind.AMBIGUOUS, cover_symbol=None, cover_mic=None))
        assert _reading(repo).status is AMBIGUOUS
        assert _reading(repo, on=date(2026, 8, 1)).status is MISSING  # not yet filed
        assert _reading(repo, cik="0000000009").status is MISSING

    def test_a_period_end_observation_handed_to_the_reader_is_ignored(self):
        period_end = historical_observation(cover_symbol="AAA", period_end=date(2026, 6, 30), filing_date=date(2026, 8, 5))
        reading = read_current_shares("AAA", (period_end,), (period_end,), evaluated_on=date(2026, 9, 14))
        assert reading.status is MISSING


# -- the provider cross-check ------------------------------------------------------------------------------


class TestCrossCheck:
    def test_a_mismatch_is_reported_and_the_sec_reading_is_untouched(self):
        repo = _repository()
        _record(repo, current())
        reading = _reading(repo)
        before = replace(reading)
        check = cross_check(reading, 560.0, NOW)
        assert (check.sec_shares, check.provider_shares, round(check.ratio, 4), check.difference) == (500.0, 560.0, 1.12, 60.0)
        assert reading == before and reading.evidence.shares == 500.0
        assert _reading(repo).evidence.shares == 500.0  # nothing was written back

    def test_provider_freshness_is_never_claimed(self):
        repo = _repository()
        _record(repo, current())
        for written in (NOW, datetime(2024, 1, 1, tzinfo=timezone.utc), None):
            assert cross_check(_reading(repo), 500.0, written).provider_freshness == PROVIDER_FRESHNESS_UNDETERMINED

    def test_nothing_to_compare_is_no_ratio(self):
        repo = _repository()
        _record(repo, current(link_kind=ShareClassLinkKind.AMBIGUOUS, cover_symbol=None, cover_mic=None))
        check = cross_check(_reading(repo), 500.0, NOW)
        assert (check.sec_status, check.sec_shares, check.ratio, check.difference) == (AMBIGUOUS, None, None, None)
        repo2 = _repository()
        _record(repo2, current())
        assert cross_check(_reading(repo2), None, None).ratio is None


# -- end to end: real corpus filings through the bridge ----------------------------------------------------


CORPUS = {  # ticker -> (CIK, accession, form, filing date, MIC)
    "CRM": ("0001108524", "0001108524-26-000190", "10-Q", date(2026, 8, 27), "XNYS"),
    "UNP": ("0000100885", "0000100885-26-000250", "10-Q", date(2026, 7, 23), "XNYS"),
    "MA": ("0001141391", "0001141391-26-000083", "10-Q", date(2026, 7, 30), "XNYS"),
    "V": ("0001403161", "0001403161-26-000104", "10-Q", date(2026, 7, 29), "XNYS"),
    "GOOG": ("0001652044", "0001652044-26-000071", "10-Q", date(2026, 7, 23), "XNAS"),
    "GOOGL": ("0001652044", "0001652044-26-000071", "10-Q", date(2026, 7, 23), "XNAS"),
    "META": ("0001326801", "0001628280-26-050705", "10-Q", date(2026, 7, 30), "XNAS"),
    "CRWD": ("0001535527", "0001535527-26-000031", "10-Q", date(2026, 8, 27), "XNAS"),
    "MSFT": ("0000789019", "0001193125-26-323660", "10-K", date(2026, 7, 29), "XNAS"),
}


def _source(ticker) -> ShareClassFilingSource:
    cik, accession, form, filed, _ = CORPUS[ticker]
    return ShareClassFilingSource(cik, accession, form, filed)


def _fetched(source: ShareClassFilingSource, text: str | None = None) -> FetchedInstance:
    xml = text if text is not None else (FIXTURES / f"{source.accession}.xml").read_text()
    return FetchedInstance(source.issuer_cik, source.accession, "x_htm.xml", "https://www.sec.gov/x_htm.xml", xml, 2)


@pytest.fixture
def corpus():
    repo = _repository(listings=tuple((t, v[4]) for t, v in CORPUS.items()))
    for source in {_source(t) for t in CORPUS}:
        repo.record_current_filing(*current_evidence_from_instance(source, _fetched(source), retrieved_at=RETRIEVED,
                                                                   recorded_at=NOW))

    def read(ticker, on=date(2026, 9, 14)):
        cik = CORPUS[ticker][0]
        return read_current_shares(ticker, repo.current_joined({ticker: cik})[ticker],
                                   repo.current_evidence_for_issuers(frozenset({cik}))[cik], evaluated_on=on)

    return repo, read


class TestCorpus:
    def test_the_bridge_keeps_three_dates_and_the_parser_version(self):
        filing, evidence = current_evidence_from_instance(_source("CRM"), _fetched(_source("CRM")),
                                                          retrieved_at=RETRIEVED, recorded_at=NOW)
        (e,) = evidence
        assert (e.as_of, e.filing_date, e.retrieved_at, e.document_period_end) == (
            date(2026, 8, 20), date(2026, 8, 27), RETRIEVED, date(2026, 7, 31))
        assert (filing.fiscal_period, filing.proven, e.parser_version, e.scope, e.cover_mic, e.decimals) == (
            "Q22027", 1, COVER_PARSER_VERSION, CurrentShareScope.ISSUER, "XNYS", "-6")  # rounded to millions

    def test_single_class_issuers_link_to_their_own_count(self, corpus):
        _, read = corpus
        assert read("CRM").evidence.shares == 823_000_000.0 and read("CRM").evidence.as_of == date(2026, 8, 20)
        assert read("UNP").evidence.shares == 594_075_498.0 and read("UNP").evidence.as_of == date(2026, 7, 17)

    def test_goog_is_class_c_googl_is_class_a_and_class_b_reaches_neither(self, corpus):
        _, read = corpus
        goog, googl = read("GOOG").evidence, read("GOOGL").evidence
        assert (goog.class_member, goog.shares) == ("goog:CapitalClassCMember", 5_527_000_000.0)
        assert (googl.class_member, googl.shares) == ("us-gaap:CommonClassAMember", 5_868_000_000.0)
        assert "us-gaap:CommonClassBMember" not in {goog.class_member, googl.class_member}

    def test_no_reading_is_ever_an_issuer_wide_aggregate(self, corpus):
        repo, read = corpus
        alphabet = repo.current_evidence_for_issuers(frozenset({"0001652044"}))["0001652044"]
        total = sum(e.shares for e in alphabet)
        assert total == 12_230_000_000.0 and {read("GOOG").evidence.shares, read("GOOGL").evidence.shares} == {
            5_527_000_000.0, 5_868_000_000.0}
        visa = repo.current_evidence_for_issuers(frozenset({"0001403161"}))["0001403161"]
        assert read("V").evidence.shares == 1_704_112_694.0 < sum(e.shares for e in visa)
        assert read("MA").evidence.shares == 869_464_115.0 and read("MA").evidence.class_member == "us-gaap:CommonClassAMember"

    def test_an_issuer_aggregate_beside_class_counts_never_becomes_a_class_count(self):
        """Synthetic, on the real Mastercard cover: an added undimensioned
        count (class A + class B) is ambiguous, and MA still reads class A."""
        source = _source("MA")
        aggregate = ('<ns0:context id="agg"><ns0:entity><ns0:identifier scheme="http://www.sec.gov/CIK">0001141391'
                     '</ns0:identifier></ns0:entity><ns0:period><ns0:instant>2026-07-27</ns0:instant></ns0:period>'
                     '</ns0:context><dei:EntityCommonStockSharesOutstanding contextRef="agg" decimals="INF" '
                     'unitRef="shares">876009940</dei:EntityCommonStockSharesOutstanding></ns0:xbrl>')
        text = (FIXTURES / f"{source.accession}.xml").read_text().replace("</ns0:xbrl>", aggregate)
        repo = _repository(listings=(("MA", "XNYS"),))
        filing, evidence = current_evidence_from_instance(source, _fetched(source, text), retrieved_at=RETRIEVED,
                                                          recorded_at=NOW)
        assert {(e.scope, e.link_kind) for e in evidence if e.shares == 876_009_940.0} == {
            (CurrentShareScope.ISSUER, ShareClassLinkKind.AMBIGUOUS)}
        repo.record_current_filing(filing, evidence)
        reading = read_current_shares("MA", repo.current_joined({"MA": source.issuer_cik})["MA"],
                                      evidence, evaluated_on=date(2026, 9, 14))
        assert (reading.status, reading.evidence.shares) == (LINKED, 869_464_115.0)

    @pytest.mark.parametrize("ticker", ["META", "CRWD", "MSFT"])
    def test_unproven_filers_stay_ambiguous(self, corpus, ticker):
        _, read = corpus
        assert read(ticker).status is AMBIGUOUS and read(ticker).evidence is None

    def test_before_the_filing_date_the_filing_does_not_exist(self, corpus):
        _, read = corpus
        assert read("GOOG", on=date(2026, 7, 22)).status is MISSING
        assert read("GOOG", on=date(2026, 7, 23)).status is LINKED
        assert read("META", on=date(2026, 7, 29)).status is MISSING

    @pytest.mark.parametrize("change", [
        {"issuer_cik": "0001141391"},  # another filer
        {"form": "10-K"},              # not the form it was located as
    ])
    def test_an_instance_that_is_not_the_located_filing_is_refused(self, change):
        source = replace(_source("CRM"), **change)
        with pytest.raises(FilingRefused):
            current_evidence_from_instance(source, _fetched(_source("CRM")), retrieved_at=RETRIEVED, recorded_at=NOW)

    @pytest.mark.parametrize("text_change", [
        (">false</dei:AmendmentFlag>", ">true</dei:AmendmentFlag>"),
        (">10-Q</dei:DocumentType>", ">8-K</dei:DocumentType>"),
    ])
    def test_amendments_and_non_periodic_documents_are_refused(self, text_change):
        text = (FIXTURES / f"{_source('CRM').accession}.xml").read_text()
        assert text_change[0] in text
        with pytest.raises(FilingRefused):
            current_evidence_from_instance(_source("CRM"), _fetched(_source("CRM"), text.replace(*text_change, 1)),
                                           retrieved_at=RETRIEVED, recorded_at=NOW)
