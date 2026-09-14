"""The reader: count sets from share evidence, same-date sibling prices, the
current economic date, the share-basis guard -- over a file database with
the real Alphabet and Mastercard rights evidence (trimmed filings through
the write bridge) and share counts/prices shaped as Atlas stores them."""
from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from atlas.alpha.business_data_refresh.class_rights_evidence import RightsFilingSource, rights_evidence_from_instance
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.canonical_security_gate.factory import build_identity_gate, build_listing_mic_reader
from atlas.alpha.class_rights_evidence.repository import SqlAlchemyClassRightsEvidenceRepository
from atlas.alpha.class_rights_evidence.table import create_class_rights_evidence_tables
from atlas.alpha.issuer_equity.composer import DenominatorQuality, issuer_fcf_yield
from atlas.alpha.issuer_equity.reader import IssuerEquityReader
from atlas.alpha.security_share_evidence.models import ShareClassLinkKind
from atlas.alpha.security_share_evidence.repository import SqlAlchemySecurityShareEvidenceRepository
from atlas.alpha.security_share_evidence.table import create_current_share_evidence_tables, create_security_share_evidence_tables
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import ingest
from tests.unit.alpha.security_share_evidence.test_current import current, current_filing
from tests.unit.alpha.security_share_evidence.test_repository import filing as annual_filing
from tests.unit.alpha.security_share_evidence.test_repository import observation

FIXTURES = Path(__file__).resolve().parents[2] / "business_data_providers" / "fixtures" / "class_rights"
NOW = datetime(2026, 9, 11, tzinfo=timezone.utc)
EVAL = date(2026, 9, 11)
ALPHABET, MA_CIK, SINGLE, SPLIT = "0001652044", "0001141391", "0000000007", "0000000009"
PROVEN, NO_LINK = ShareClassLinkKind.PROVEN_BY_SHARED_DIMENSION, ShareClassLinkKind.NO_LINK
A, B, C = "us-gaap:CommonClassAMember", "us-gaap:CommonClassBMember", "goog:CapitalClassCMember"


def _doc(ticker, kind, identifier, metadata, on, reference):
    return ingest(RawBusinessDocument(
        identifier=f"{ticker}:{identifier}", company=ticker, source_kind=kind,
        published_at=datetime.combine(on, datetime.min.time(), tzinfo=timezone.utc), provider_id="x",
        raw_reference=reference, content_hash=hashlib.sha256(json.dumps([ticker, identifier, metadata]).encode()).hexdigest(),
        period_start=on, period_end=on, language="en", metadata=metadata), evaluated_at=NOW).record


def _statement(ticker, cik):
    return _doc(ticker, "financial_statement", "fy", {"sec_cik": cik, "sec_form": "10-K", "revenue": 1.0}, date(2025, 12, 31),
                "https://data.sec.gov/x")


def _quote(ticker, on, px, provider_shares=None):
    meta = {"share_price": px, "price_basis": "raw"}
    if provider_shares:
        meta["shares_outstanding"] = provider_shares  # the provider's value: never the issuer denominator
    return _doc(ticker, "market_data_snapshot", f"q{on}", meta, on,
                f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}")


def _bar(ticker, on, raw, adjusted):
    return _doc(ticker, "market_data_snapshot", f"m{on}", {"share_price": adjusted, "raw_close": raw, "dividend_amount": 0.0,
                "price_basis": "split_and_dividend_adjusted"}, on,
                f"https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol={ticker}")


def _annual(cik, accession, filed, period, rows):
    obs = tuple(observation(issuer_cik=cik, accession=accession, filing_date=filed, period_end=period, class_member=m,
                            shares=s, link_kind=PROVEN if sym else NO_LINK, cover_symbol=sym, cover_mic="XNAS" if sym else None,
                            context_id=f"c{i}") for i, (m, s, sym) in enumerate(rows))
    return annual_filing(list(obs), issuer_cik=cik, accession=accession, filing_date=filed), obs


def _cover(cik, accession, filed, as_of, rows, *, classes_reported):
    ev = tuple(current(issuer_cik=cik, accession=accession, filing_date=filed, as_of=as_of, class_member=m, shares=s,
                       link_kind=PROVEN if sym else ShareClassLinkKind.AMBIGUOUS, cover_symbol=sym,
                       cover_mic="XNAS" if sym else None, context_id=f"k{i}", scope=current().scope if m is None else
                       type(current().scope)("class")) for i, (m, s, sym) in enumerate(rows))
    return current_filing(list(ev), share_classes_reported=classes_reported), ev


def _rights(repo, cik, accession, form, filed):
    src = RightsFilingSource(cik, accession, form, filed, "https://www.sec.gov/Archives/edgar/data/1/x_htm.xml")
    repo.record_filing(*rights_evidence_from_instance(src, (FIXTURES / f"{accession}.xml").read_text(), retrieved_at=NOW, recorded_at=NOW))


@pytest.fixture
def reader(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'atlas.db'}", future=True)
    create_business_record_table(engine)
    create_security_share_evidence_tables(engine)
    create_current_share_evidence_tables(engine)
    create_class_rights_evidence_tables(engine)
    build_identity_gate(engine)
    records = SqlAlchemyBusinessRecordRepository(engine)
    for ticker, cik in (("GOOG", ALPHABET), ("GOOGL", ALPHABET), ("MA", MA_CIK), ("ONE", SINGLE), ("SPL", SPLIT)):
        records.add(_statement(ticker, cik))
    with engine.begin() as c:
        for i, t in enumerate(("GOOG", "GOOGL", "MA", "ONE", "SPL")):
            c.execute(text("INSERT INTO canonical_security_listings (id, canonical_security_id, ticker, exchange_mic, currency, "
                           "relationship, security_type) VALUES (:i, :s, :t, 'XNAS', 'USD', 'NATIVE', 'COMMON_STOCK')"),
                      {"i": f"l{i}", "s": f"s{i}", "t": t})
    # Alphabet: synchronized monthly bars on 2026-02-27; asynchronous quotes later
    for r in (_bar("GOOG", date(2026, 2, 27), 311.43, 311.43), _bar("GOOGL", date(2026, 2, 27), 311.76, 311.76),
              _quote("GOOG", date(2026, 8, 21), 341.75), _quote("GOOGL", date(2026, 8, 24), 348.06),
              _quote("MA", date(2026, 8, 24), 599.86), _quote("ONE", date(2026, 8, 25), 205.69, provider_shares=819_000_000.0),
              _bar("SPL", date(2026, 2, 27), 800.0, 200.0), _quote("SPL", date(2026, 8, 13), 225.0)):
        records.add(r)
    shares = SqlAlchemySecurityShareEvidenceRepository(engine)
    shares.record_filing(*_annual(ALPHABET, "0001652044-26-000018", date(2026, 2, 5), date(2025, 12, 31),
                                  [(A, 5_822e6, "GOOGL"), (B, 837e6, None), (C, 5_429e6, "GOOG")]))
    shares.record_current_filing(*_cover(ALPHABET, "0001652044-26-000071", date(2026, 7, 23), date(2026, 7, 15),
                                         [(A, 5_868e6, "GOOGL"), (B, 835e6, None), (C, 5_527e6, "GOOG")], classes_reported=True))
    shares.record_current_filing(*_cover(MA_CIK, "0001141391-26-000083", date(2026, 7, 30), date(2026, 7, 27),
                                         [(A, 869_464_115, "MA"), (B, 6_545_825, None)], classes_reported=True))
    shares.record_current_filing(*_cover(SINGLE, "0000000007-26-000001", date(2026, 8, 27), date(2026, 8, 20),
                                         [(None, 823_000_000, "ONE")], classes_reported=False))
    # a split between the latest count Atlas can pair and the price: 250 before, 1,000 after
    shares.record_filing(*_annual(SPLIT, "0000000009-26-000001", date(2026, 3, 5), date(2026, 1, 31),
                                  [("x:ClassAMember", 250e6, None), ("x:ClassBMember", 0.0, None)]))
    shares.record_current_filing(*_cover(SPLIT, "0000000009-26-000002", date(2026, 8, 27), date(2026, 8, 20),
                                         [(None, 1_000e6, None)], classes_reported=True))
    rights = SqlAlchemyClassRightsEvidenceRepository(engine)
    _rights(rights, ALPHABET, "0001652044-26-000018", "10-K", date(2026, 2, 5))
    _rights(rights, MA_CIK, "0001141391-26-000013", "10-K", date(2026, 2, 11))
    return IssuerEquityReader(engine, listing_mics=build_listing_mic_reader(engine))


class TestAlphabet:
    def test_one_issuer_value_on_the_latest_date_both_classes_have_a_price(self, reader):
        goog, googl = reader.current("GOOG", EVAL), reader.current("GOOGL", EVAL)
        assert goog.economic_date == googl.economic_date == date(2026, 2, 27)  # not the 08-21 / 08-24 quotes
        assert goog.market_cap_low == googl.market_cap_low == pytest.approx(5_822e6 * 311.76 + 837e6 * 311.76 + 5_429e6 * 311.43)
        assert goog.quality is DenominatorQuality.ISSUER_EQUIVALENT
        assert goog.count_instant == date(2025, 12, 31)  # the cover counts post-date the price: not paired

    def test_listed_classes_keep_their_own_prices_and_b_converts_into_a(self, reader):
        cap = reader.current("GOOG", EVAL)
        by = {c.member: c for c in cap.contributions}
        assert (by[A].symbol, by[A].price, by[C].symbol, by[C].price) == ("GOOGL", 311.76, "GOOG", 311.43)
        assert (by[B].symbol, by[B].proxy_from_security, by[B].treatment) == (None, "GOOGL", "filed_conversion_or_parity")

    def test_the_two_securities_stay_distinct(self, reader):
        cap = reader.current("GOOG", EVAL)
        assert {c.symbol for c in cap.contributions if c.symbol} == {"GOOG", "GOOGL"}


class TestOthers:
    def test_mastercard_b_priced_from_a_by_filed_conversion_with_the_carry_shown(self, reader):
        cap = reader.current("MA", EVAL)
        assert cap.quality is DenominatorQuality.ISSUER_EQUIVALENT
        assert cap.market_cap_low == pytest.approx((869_464_115 + 6_545_825) * 599.86)
        assert "rights_carried_forward:208d" in cap.gaps

    def test_a_single_class_issuer_reduces_to_price_times_its_cover_count(self, reader):
        cap = reader.current("ONE", EVAL)
        assert (cap.quality, cap.market_cap_low) == (DenominatorQuality.ISSUER_EXACT, 823_000_000 * 205.69)
        y = issuer_fcf_yield(14_000_000_000.0, cap)
        assert y.yield_low == y.yield_high == pytest.approx(14e9 / (823e6 * 205.69))

    def test_a_count_is_never_paired_with_a_price_across_a_share_basis_change(self, reader):
        cap = reader.current("SPL", EVAL)
        assert cap.quality is DenominatorQuality.INSUFFICIENT_EVIDENCE
        assert cap.gaps == ("share_basis_change_between_count_and_price",)


class TestVistraSeniorEquity:
    def test_outstanding_preferred_from_the_filing_is_a_senior_claim_never_common(self, tmp_path):
        from atlas.alpha.issuer_equity.composer import ClassCount, ListedPrice, compose_issuer_common_equity_market_cap

        engine = create_engine(f"sqlite:///{tmp_path / 'v.db'}")
        create_class_rights_evidence_tables(engine)
        repo = SqlAlchemyClassRightsEvidenceRepository(engine)
        _rights(repo, "0001692819", "0001692819-26-000019", "10-Q", date(2026, 8, 10))
        rights = repo.observations_for_issuers(frozenset({"0001692819"}))["0001692819"]
        cap = compose_issuer_common_equity_market_cap(
            "0001692819", date(2026, 9, 8), (ClassCount(None, 335_635_195, date(2026, 8, 3), "0001692819-26-000019", date(2026, 8, 10)),),
            {"VST": ListedPrice("VST", date(2026, 9, 8), 151.72, "r")}, rights, case_symbol="VST", classes_reported=True)
        assert cap.quality is DenominatorQuality.ISSUER_EXACT and cap.market_cap_low == pytest.approx(335_635_195 * 151.72)
        senior = [(s.member, s.shares, round(s.annual_dividend)) for s in cap.senior_equity]
        assert senior == [("us-gaap:SeriesAPreferredStockMember", 1_000_000.0, 80_000_000),
                          ("us-gaap:SeriesBPreferredStockMember", 1_000_000.0, 70_000_000),
                          ("us-gaap:SeriesCPreferredStockMember", 476_066.0, round(476_066 * 1000 * 0.08875))]  # outstanding, not issued
