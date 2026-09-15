"""Which classes an issuer-level count spans: the count filing's own
class-axis share facts (class_rights_v2), never the boolean "classes
reported" alone. Synthetic shapes for every state, then AMD's and Moody's
real 10-Qs (trimmed, through the write bridge) as controls, then the
reader's temporal and duplicate guarantees over a file database."""
from __future__ import annotations

import ast
import random
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from atlas.alpha.business_data_refresh.class_rights_evidence import RightsFilingSource, rights_evidence_from_instance
from atlas.alpha.class_rights_evidence.models import RightKind
from atlas.alpha.class_rights_evidence.repository import SqlAlchemyClassRightsEvidenceRepository
from atlas.alpha.class_rights_evidence.table import create_class_rights_evidence_tables
from atlas.alpha.issuer_equity.composer import ClassCount, ClassInventoryState as S, class_inventory
from atlas.alpha.issuer_equity.reader import IssuerEquityReader
from atlas.business_data_providers.sec_edgar_share_classes import CountScope, parse_cover_share_counts
from tests.unit.alpha.issuer_equity.test_composer import EXACT, INSUFFICIENT, P, compose, count, price, right

ROOT = Path(__file__).resolve().parents[4]
FIXTURES = ROOT / "tests" / "unit" / "business_data_providers" / "fixtures" / "class_rights"
ACC = "0000000001-26-000001"
GENERIC = "us-gaap:CommonStockMember"
A, B, PREF, TAG = "x:ClassAMember", "x:ClassBMember", "x:SeriesAPreferredMember", "x:SomethingMember"
OUT, ISSUED = "us-gaap:CommonStockSharesOutstanding", "us-gaap:CommonStockSharesIssued"
PREF_OUT, REPURCHASED = "us-gaap:PreferredStockSharesOutstanding", "us-gaap:StockRepurchasedDuringPeriodShares"
NOW = datetime(2026, 9, 15, tzinfo=timezone.utc)


def axis(member, value=100.0, concept=OUT, *, on=P, start=None, kind="common", accession=ACC, others=()):
    """One class-axis share fact, as the parser records it."""
    o = right(RightKind.CLASS_AXIS_SHARE_FACT, subject=member, value=value, start=start or on, end=on, equity=kind,
              accession=accession, key=f"class_axis_share_fact|{concept}|{member}|{on}|{value}|{others}")
    return replace(o, concept=concept, related_labels=tuple(others), unit="shares", parser_version="class_rights_v2")


def inventory(facts, instant=P, accession=ACC):
    return class_inventory(tuple(facts), instant, accession)


class TestClassInventory:
    def test_one_common_class(self):
        inv = inventory([axis(A, 900.0), axis(GENERIC, 900.0, ISSUED)])
        assert (inv.state, inv.participating, inv.zero_share, inv.noncommon) == (S.SINGLE_COMMON_CLASS, (A,), (), ())

    def test_the_generic_member_is_the_common_stock_not_a_second_class(self):
        inv = inventory([axis(GENERIC, 1_000.0, ISSUED), axis(GENERIC, 5.0, REPURCHASED, start=date(2025, 10, 1), kind=None)])
        assert (inv.state, inv.participating) == (S.SINGLE_COMMON_CLASS, ())

    def test_multiple_common_classes(self):
        inv = inventory([axis(A, 900.0), axis(B, 100.0)])
        assert (inv.state, inv.participating) == (S.MULTIPLE_COMMON_CLASSES, (A, B))
        total = inventory([axis(A, 900.0), axis(B, 100.0), axis(GENERIC, 1_000.0)])  # the generic member: their total
        assert (total.state, total.participating, total.unexplained) == (S.MULTIPLE_COMMON_CLASSES, (A, B), ())

    def test_the_generic_member_beside_a_class_it_does_not_total_may_be_another_class(self):
        inv = inventory([axis(A, 900.0), axis(GENERIC, 1_000.0, ISSUED)])
        assert (inv.state, inv.participating, inv.unexplained) == (S.AMBIGUOUS_CLASS_AXIS, (A,), (GENERIC,))
        uncounted = inventory([axis(A, 900.0), axis(GENERIC, 5.0, REPURCHASED, start=date(2025, 10, 1), kind=None)])
        assert uncounted.state is S.AMBIGUOUS_CLASS_AXIS

    def test_common_plus_preferred_never_counts_preferred_as_common(self):
        inv = inventory([axis(A, 900.0), axis(PREF, 10.0, PREF_OUT, kind="preferred")])
        assert (inv.state, inv.participating, inv.noncommon) == (S.COMMON_PLUS_NONCOMMON, (A,), (PREF,))

    def test_a_member_only_on_concepts_that_count_nothing_is_ambiguous(self):
        inv = inventory([axis(A, 900.0), axis(TAG, 3.0, REPURCHASED, start=date(2025, 10, 1), kind=None)])
        assert (inv.state, inv.unexplained, inv.participating) == (S.AMBIGUOUS_CLASS_AXIS, (TAG,), (A,))

    def test_a_class_counted_at_zero_at_the_balance_sheet_contributes_nothing(self):
        inv = inventory([axis(A, 900.0, ISSUED), axis(B, 0.0), axis(B, 0.0, ISSUED)])
        assert (inv.state, inv.participating, inv.zero_share) == (S.SINGLE_COMMON_CLASS, (A,), (B,))

    def test_a_zero_at_an_earlier_date_proves_nothing_now(self):
        inv = inventory([axis(A, 900.0), axis(B, 0.0, on=date(2024, 12, 31))])
        assert (inv.state, inv.participating) == (S.MULTIPLE_COMMON_CLASSES, (A, B))

    def test_a_zero_under_a_further_dimension_proves_nothing(self):
        inv = inventory([axis(A, 900.0), axis(B, 0.0, others=("dei:LegalEntityAxis=x:SubsidiaryMember",))])
        assert (inv.state, inv.participating) == (S.MULTIPLE_COMMON_CLASSES, (A, B))

    def test_only_the_count_filings_own_facts_on_or_before_the_instant(self):
        own = [axis(A, 900.0)]
        later_filing = axis(B, 100.0, accession="0000000001-26-000099")
        after_instant = axis(B, 100.0, on=P + timedelta(days=1))
        assert inventory([*own, later_filing, after_instant]).state is S.SINGLE_COMMON_CLASS
        assert inventory([later_filing]).state is S.INSUFFICIENT_EVIDENCE
        assert inventory([], P).state is S.INSUFFICIENT_EVIDENCE

    def test_the_evidence_names_each_members_count_fact(self):
        facts = [axis(A, 900.0), axis(A, 900.0, ISSUED), axis(B, 0.0), axis(GENERIC, 900.0, ISSUED)]
        inv = inventory(facts)
        assert inv.evidence == (facts[3].observation_key, facts[0].observation_key, facts[2].observation_key)

    def test_order_never_matters(self):
        facts = [axis(A, 900.0), axis(B, 0.0), axis(PREF, 1.0, PREF_OUT, kind="preferred"), axis(GENERIC, 5.0, ISSUED)]
        shuffled = facts[:]
        random.Random(7).shuffle(shuffled)
        assert inventory(facts) == inventory(shuffled)


class TestIssuerLevelComposition:
    def _cap(self, facts=(), *, classes_reported=True, rights=()):
        return compose([count(None, 1_000)], [price("AAA", 10.0)], [*facts, *rights], classes_reported=classes_reported)

    def test_the_boolean_alone_proves_nothing(self):
        cap = self._cap()
        assert cap.quality is INSUFFICIENT and "class_structure_unrecorded" in cap.gaps

    def test_the_facts_decide_what_classes_reported_means(self):
        single = self._cap([axis(A, 1_000.0)])
        assert (single.quality, single.market_cap_low) == (EXACT, 10_000.0)
        (c,) = single.contributions
        assert c.treatment == "one_common_class_with_shares" and c.evidence[0] == "class_inventory:single_common_class"
        several = self._cap([axis(A, 900.0), axis(B, 100.0)])
        assert several.quality is INSUFFICIENT and several.market_cap_low is None
        assert {"class_inventory:multiple_common_classes", "issuer_level_count_spans_classes_of_unknown_economics"} <= set(several.gaps)

    def test_recorded_facts_overrule_a_kind_only_inventory(self):
        v1 = right(RightKind.CLASS_INVENTORY, subject=GENERIC, equity="common")
        assert self._cap(rights=[v1]).quality is EXACT  # a filing recorded before facts were kept: unchanged
        ambiguous = self._cap([axis(GENERIC, 1_000.0, ISSUED), axis(TAG, 3.0, REPURCHASED, start=date(2025, 10, 1), kind=None)],
                              rights=[v1])
        assert ambiguous.quality is INSUFFICIENT and "class_inventory:ambiguous_class_axis" in ambiguous.gaps

    def test_preferred_beside_one_common_class_is_not_added(self):
        cap = self._cap([axis(A, 1_000.0), axis(PREF, 50.0, PREF_OUT, kind="preferred")])
        assert (cap.quality, cap.market_cap_low, len(cap.contributions)) == (EXACT, 10_000.0, 1)

    def test_a_zero_share_class_is_reported_not_priced(self):
        cap = self._cap([axis(A, 1_000.0), axis(B, 0.0)])
        assert cap.quality is EXACT and f"zero_share_class:{B}" in cap.gaps and cap.market_cap_low == 10_000.0

    def test_a_filing_without_classes_is_unchanged(self):
        cap = self._cap([axis(A, 900.0), axis(B, 100.0)], classes_reported=False)
        assert cap.quality is EXACT and cap.contributions[0].treatment == "no_share_classes_reported"


# -- real controls -------------------------------------------------------------------------------------------

AMD = ("0000002488", "0000002488-26-000123", date(2026, 8, 5))
MCO = ("0001059556", "0001628280-26-049398", date(2026, 7, 23))


def _real(filing):
    cik, accession, filed = filing
    text = (FIXTURES / f"{accession}.xml").read_text()
    source = RightsFilingSource(cik, accession, "10-Q", filed, f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/x.xml")
    record, observations = rights_evidence_from_instance(source, text, retrieved_at=NOW, recorded_at=NOW)
    cover = parse_cover_share_counts(text)
    (issuer,) = [c for c in cover.counts if c.scope is CountScope.ISSUER and c.class_member is None]
    return record, observations, cover, ClassCount(None, issuer.shares, issuer.as_of, accession, filed)


def _compose_real(observations, cover, count_, symbol, px):
    from atlas.alpha.issuer_equity.composer import compose_issuer_common_equity_market_cap

    return compose_issuer_common_equity_market_cap(count_.accession[:10], count_.as_of + timedelta(days=5), (count_,),
                                                   {symbol: price(symbol, px)}, tuple(observations), case_symbol=symbol,
                                                   classes_reported=cover.share_classes_reported)


class TestAmdLike:
    def test_the_generic_common_member_alone_proves_one_class(self):
        _, observations, cover, issuer = _real(AMD)
        assert cover.share_classes_reported and (issuer.shares, issuer.as_of) == (1_632_475_042.0, date(2026, 7, 29))
        inv = class_inventory(observations, issuer.as_of, issuer.accession)
        assert (inv.state, inv.participating, inv.zero_share, inv.noncommon, inv.unexplained) == (S.SINGLE_COMMON_CLASS, (), (), (), ())
        (evidence,) = inv.evidence
        (fact,) = [o for o in observations if o.observation_key == evidence]
        assert (fact.subject_member, fact.concept, fact.effective_to, fact.value) == (
            GENERIC, ISSUED, date(2026, 6, 27), 1_632_000_000.0)
        cap = _compose_real(observations, cover, issuer, "ZZZ", 200.0)
        assert (cap.quality, cap.market_cap_low, cap.gaps) == (EXACT, 1_632_475_042.0 * 200.0, ())

    def test_a_second_common_class_in_the_same_filing_withholds_it(self):
        _, observations, cover, issuer = _real(AMD)
        second = replace(axis(B, 5.0, on=date(2026, 6, 27), accession=issuer.accession), issuer_cik=AMD[0])
        cap = _compose_real((*observations, second), cover, issuer, "ZZZ", 200.0)
        assert cap.quality is INSUFFICIENT and "class_inventory:ambiguous_class_axis" in cap.gaps
        both = replace(axis(A, 1_632_000_000.0 - 5.0, on=date(2026, 6, 27), accession=issuer.accession), issuer_cik=AMD[0])
        cap = _compose_real((*observations, second, both), cover, issuer, "ZZZ", 200.0)  # the generic member totals them
        assert cap.quality is INSUFFICIENT and "class_inventory:multiple_common_classes" in cap.gaps


class TestMcoLike:
    SERIES, NON_SERIES = "mco:SeriesCommonStockMember", "mco:NonSeriesCommonStockMember"

    def test_a_series_class_with_no_shares_leaves_one_common_class(self):
        _, observations, cover, issuer = _real(MCO)
        assert cover.share_classes_reported and (issuer.shares, issuer.as_of) == (173_200_000.0, date(2026, 6, 30))
        inv = class_inventory(observations, issuer.as_of, issuer.accession)
        assert (inv.state, inv.participating, inv.zero_share) == (S.SINGLE_COMMON_CLASS, (self.NON_SERIES,), (self.SERIES,))
        cap = _compose_real(observations, cover, issuer, "ZZZ", 500.0)
        assert (cap.quality, cap.market_cap_low) == (EXACT, 173_200_000.0 * 500.0)
        assert cap.gaps == (f"zero_share_class:{self.SERIES}",) and cap.senior_equity == ()  # its preferred: zero

    def test_the_series_class_holding_shares_withholds_it(self):
        _, observations, cover, issuer = _real(MCO)
        held = tuple(replace(o, value=1_000.0) if o.kind is RightKind.CLASS_AXIS_SHARE_FACT and o.subject_member == self.SERIES
                     and o.equity_kind == "common" else o for o in observations)
        cap = _compose_real(held, cover, issuer, "ZZZ", 500.0)
        assert cap.quality is INSUFFICIENT and "class_inventory:multiple_common_classes" in cap.gaps


class TestVstLike:
    """Vistra's 10-Q (`0001692819-26-000019`, recorded live under v1): its
    preferred series are non-common under either rule."""

    FILING = ("0001692819", "0001692819-26-000019", date(2026, 8, 10))
    PREFERRED = ("us-gaap:SeriesAPreferredStockMember", "us-gaap:SeriesBPreferredStockMember",
                 "us-gaap:SeriesCPreferredStockMember")

    def test_its_facts_prove_common_plus_preferred(self):
        _, observations, cover, issuer = _real(self.FILING)
        inv = class_inventory(observations, issuer.as_of, issuer.accession)
        assert (inv.state, inv.participating, inv.noncommon, inv.unexplained) == (S.COMMON_PLUS_NONCOMMON, (), self.PREFERRED, ())
        cap = _compose_real(observations, cover, issuer, "ZZZ", 100.0)
        assert cap.quality is EXACT and cap.contributions[0].treatment == "one_common_class_with_shares"
        assert "senior_equity_claims_on_free_cash_flow" in cap.gaps

    def test_its_live_v1_record_keeps_its_kind_only_inventory(self):
        _, observations, cover, issuer = _real(self.FILING)
        v1 = tuple(replace(o, parser_version="class_rights_v1") for o in observations
                   if o.kind is not RightKind.CLASS_AXIS_SHARE_FACT)
        cap = _compose_real(v1, cover, issuer, "ZZZ", 100.0)
        v2 = _compose_real(observations, cover, issuer, "ZZZ", 100.0)
        assert cap.quality is EXACT and cap.contributions[0].treatment == "one_common_class_in_inventory"
        assert (cap.market_cap_low, cap.senior_equity) == (v2.market_cap_low, v2.senior_equity)


# -- the reader: temporal and duplicate guarantees -----------------------------------------------------------


@pytest.fixture
def engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'ci.db'}")
    create_class_rights_evidence_tables(engine)
    return engine


class TestReader:
    def test_recording_the_same_filing_twice_writes_nothing_the_second_time(self, engine):
        repo = SqlAlchemyClassRightsEvidenceRepository(engine)
        record, observations, _, _ = _real(MCO)
        assert repo.record_filing(record, observations) is True
        assert repo.record_filing(record, observations) is False
        assert len(repo.observations_for_issuers(frozenset({MCO[0]}))[MCO[0]]) == len(observations) == 16

    def test_a_filing_read_again_by_a_later_parser_is_each_fact_once(self, engine):
        repo = SqlAlchemyClassRightsEvidenceRepository(engine)
        record, observations, _, issuer = _real(MCO)
        earlier = NOW - timedelta(days=30)
        v1 = tuple(replace(o, parser_version="class_rights_v1", recorded_at=earlier, retrieved_at=earlier)
                   for o in observations if o.kind is not RightKind.CLASS_AXIS_SHARE_FACT)
        repo.record_filing(replace(record, parser_version="class_rights_v1", observations=len(v1), recorded_at=earlier,
                                   retrieved_at=earlier), v1)
        repo.record_filing(record, observations)
        stored = repo.observations_for_issuers(frozenset({MCO[0]}))[MCO[0]]
        assert len(stored) == len(v1) + len(observations)  # append-only: both records kept
        read = IssuerEquityReader(engine, listing_mics=None).rights(MCO[0], date(2026, 9, 15))
        assert len(read) == len({o.observation_key for o in read}) == len(observations)
        # A fact recorded by both keeps its first record.
        assert {o.parser_version for o in read if o.kind is RightKind.CLASS_INVENTORY} == {"class_rights_v1"}
        assert {o.parser_version for o in read if o.kind is RightKind.CLASS_AXIS_SHARE_FACT} == {"class_rights_v2"}
        assert class_inventory(read, issuer.as_of, issuer.accession).state is S.SINGLE_COMMON_CLASS

    def test_a_filing_filed_after_the_evaluation_date_is_never_read(self, engine):
        repo = SqlAlchemyClassRightsEvidenceRepository(engine)
        record, observations, _, issuer = _real(MCO)
        repo.record_filing(record, observations)
        reader = IssuerEquityReader(engine, listing_mics=None)
        assert reader.rights(MCO[0], MCO[2] - timedelta(days=1)) == ()
        assert class_inventory(reader.rights(MCO[0], MCO[2] - timedelta(days=1)), issuer.as_of, issuer.accession).state \
            is S.INSUFFICIENT_EVIDENCE
        assert len(reader.rights(MCO[0], MCO[2])) == 16


def test_no_issuer_is_named_in_the_class_inventory_path():
    modules = ["atlas/alpha/issuer_equity/composer.py", "atlas/alpha/issuer_equity/reader.py",
               "atlas/business_data_providers/sec_edgar_class_rights.py", "atlas/alpha/class_rights_evidence/models.py",
               "atlas/alpha/business_data_refresh/class_rights_evidence.py"]
    names = ("AMD", "MCO", "Moody", "0000002488", "0001059556", "0000002488-26-000123", "0001628280-26-049398",
             "amd:", "mco:", "NonSeries", "SeriesCommon")
    for module in modules:
        tree = ast.parse((ROOT / module).read_text())
        literals = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        assert not [lit for lit in literals for name in names if name in lit], module
