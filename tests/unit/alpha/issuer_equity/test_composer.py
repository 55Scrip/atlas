"""The issuer common-equity composer, pure: synthetic counts, prices and
rights evidence for every path it takes (the real-filing controls are in
`test_reader.py`)."""
from __future__ import annotations

import math
from datetime import date, datetime, timezone

import pytest

from atlas.alpha.class_rights_evidence.models import ClassRightsObservation, EvidenceStrength, RightKind
from atlas.alpha.issuer_equity.composer import (
    ISSUER_EQUITY_METHODOLOGY,
    ClassCount,
    DenominatorQuality,
    ListedPrice,
    compose_issuer_common_equity_market_cap,
    issuer_fcf_yield,
)

EXACT, EQUIVALENT = DenominatorQuality.ISSUER_EXACT, DenominatorQuality.ISSUER_EQUIVALENT
BOUNDED, INSUFFICIENT = DenominatorQuality.ISSUER_BOUNDED, DenominatorQuality.INSUFFICIENT_EVIDENCE
NOW = datetime(2026, 9, 11, tzinfo=timezone.utc)
P = date(2025, 12, 31)
ON = date(2026, 2, 27)
A, B, C = "x:ClassAMember", "x:ClassBMember", "x:ClassCMember"


def right(kind, *, subject=None, target=None, related=(), labels=(), value=None, low=None, high=None, strength=None,
          accession="0000000001-26-000001", start=date(2023, 1, 1), end=P, equity=None, decimals=None, key=None):
    strength = strength or (EvidenceStrength.FILING_STATEMENT if kind in (
        RightKind.ECONOMIC_PARITY, RightKind.CONVERTIBLE_INTO) else EvidenceStrength.STRUCTURED_FILING)
    return ClassRightsObservation(
        issuer_cik="0000000001", accession=accession, form="10-K", filing_date=date(2026, 2, 5),
        observation_key=key or f"{kind.value}|{subject}|{target}|{related}|{value}|{start}|{end}", kind=kind,
        strength=strength, subject_member=subject, subject_label=None, target_member=target, target_label=None,
        related_members=tuple(related), related_labels=tuple(labels), value=value, value_low=low, value_high=high,
        unit=None, decimals=decimals, equity_kind=equity, effective_from=start, effective_to=end, concept="c",
        context_id="ctx", excerpt=None, parser_version="class_rights_v1", retrieved_at=NOW, recorded_at=NOW)


def count(member, shares, symbol=None, *, as_of=P, accession="0000000001-26-000001"):
    return ClassCount(member, shares, as_of, accession, date(2026, 2, 5), symbol, "XNAS" if symbol else None)


def price(symbol, value, on=ON):
    return ListedPrice(symbol, on, value, f"r-{symbol}")


def compose(counts, prices, rights=(), *, case="AAA", **kw):
    return compose_issuer_common_equity_market_cap("0000000001", ON, tuple(counts), {p.symbol: p for p in prices},
                                                   tuple(rights), case_symbol=case, **kw)


class TestSingleClass:
    def test_reduces_exactly_to_price_times_shares(self):
        cap = compose([count(None, 823_000_000)], [price("AAA", 205.69)], classes_reported=False)
        assert (cap.quality, cap.market_cap_low, cap.market_cap_high) == (EXACT, 823_000_000 * 205.69, 823_000_000 * 205.69)
        assert cap.methodology == ISSUER_EQUITY_METHODOLOGY and cap.is_point

    def test_classes_reported_without_a_recorded_inventory_is_withheld(self):
        cap = compose([count(None, 100)], [price("AAA", 10)], classes_reported=True)
        assert cap.quality is INSUFFICIENT and "class_structure_unrecorded" in cap.gaps

    def test_an_inventory_of_only_preferred_series_leaves_one_common_class(self):
        inv = right(RightKind.CLASS_INVENTORY, subject="x:SeriesAPreferredMember", equity="preferred")
        cap = compose([count(None, 100)], [price("AAA", 10)], [inv], classes_reported=True)
        assert cap.quality is EXACT and cap.market_cap_low == 1000

    def test_every_other_class_zero_collapses_to_the_listed_one_with_the_carry_disclosed(self):
        cap = compose([count(None, 1_000, as_of=date(2026, 8, 20))], [price("AAA", 10)], classes_reported=True,
                      class_breakdown=((A, 250.0, date(2026, 1, 31)), (B, 0.0, date(2026, 1, 31))))
        assert cap.quality is EXACT and cap.market_cap_low == 10_000
        assert any(g.startswith("class_breakdown_carried_forward:") for g in cap.gaps)

    def test_a_zero_class_history_is_not_a_zero_class_now(self):
        """A class that had shares in the breakdown is never assumed away."""
        cap = compose([count(None, 1_000)], [price("AAA", 10)], classes_reported=True,
                      class_breakdown=((A, 250.0, P), (B, 12.0, P)))
        assert cap.quality is INSUFFICIENT


class TestListedSiblings:
    def test_each_listed_class_takes_its_own_price(self):
        cap = compose([count(A, 100, "AAA"), count(C, 50, "AAC")], [price("AAA", 10.0), price("AAC", 9.0)])
        assert (cap.quality, cap.market_cap_low) == (EXACT, 100 * 10.0 + 50 * 9.0)

    def test_a_listed_sibling_without_a_price_on_the_date_withholds(self):
        cap = compose([count(A, 100, "AAA"), count(C, 50, "AAC")], [price("AAA", 10.0)])
        assert cap.quality is INSUFFICIENT and "no_price:AAC" in cap.gaps

    def test_counts_from_two_filings_or_instants_are_never_mixed(self):
        cap = compose([count(A, 100, "AAA"), count(C, 50, "AAC", as_of=date(2025, 9, 30))], [price("AAA", 10), price("AAC", 9)])
        assert cap.quality is INSUFFICIENT and "counts_not_from_one_filing_and_instant" in cap.gaps


class TestUnlisted:
    def test_filed_conversion_with_a_stated_ratio_prices_at_the_target(self):
        cap = compose([count(A, 100, "AAA"), count(B, 7)], [price("AAA", 10.0)],
                      [right(RightKind.CONVERTIBLE_INTO, subject=B, target=A, value=1.0)])
        b = next(c for c in cap.contributions if c.member == B)
        assert (cap.quality, b.proxy_from_security, b.ratio_low, cap.market_cap_low) == (EQUIVALENT, "AAA", 1.0, 1070.0)

    def test_parity_with_two_listed_classes_and_a_conversion_target_prices_at_the_target(self):
        rights = [right(RightKind.ECONOMIC_PARITY, related=(A, B, C)), right(RightKind.CONVERTIBLE_INTO, subject=B, target=A)]
        cap = compose([count(A, 100, "AAA"), count(B, 10), count(C, 90, "AAC")], [price("AAA", 10.0), price("AAC", 9.0)], rights)
        assert (cap.quality, cap.market_cap_low) == (EQUIVALENT, 100 * 10 + 10 * 10 + 90 * 9)

    def test_parity_with_two_listed_classes_and_no_target_is_bounded_between_their_prices(self):
        cap = compose([count(A, 100, "AAA"), count(B, 10), count(C, 90, "AAC")], [price("AAA", 10.0), price("AAC", 9.0)],
                      [right(RightKind.ECONOMIC_PARITY, related=(A, B, C))])
        assert cap.quality is BOUNDED
        assert (cap.market_cap_low, cap.market_cap_high) == (1000 + 90 + 810, 1000 + 100 + 810)

    def test_per_class_eps_alone_is_bounded_by_the_reported_precision(self):
        eps = [right(RightKind.EARNINGS_PER_SHARE, subject=B, value=10.91, decimals="2", strength=EvidenceStrength.ACCOUNTING_CORROBORATION),
               right(RightKind.EARNINGS_PER_SHARE, subject=A, value=10.91, decimals="2", strength=EvidenceStrength.ACCOUNTING_CORROBORATION)]
        cap = compose([count(A, 100, "AAA"), count(B, 10)], [price("AAA", 10.0)], eps)
        b = next(c for c in cap.contributions if c.member == B)
        assert cap.quality is BOUNDED and b.evidence_strength == "accounting_corroboration"
        assert b.ratio_low == pytest.approx(10.905 / 10.915) and b.ratio_high == pytest.approx(10.915 / 10.905)
        assert cap.market_cap_low < 1100 < cap.market_cap_high

    def test_an_unlisted_class_without_rights_evidence_is_never_omitted(self):
        cap = compose([count(A, 100, "AAA"), count(B, 7)], [price("AAA", 10.0)])
        assert cap.quality is INSUFFICIENT and cap.market_cap_low is None
        assert f"no_rights_evidence:{B}" in cap.gaps

    def test_voting_alone_is_not_economic_evidence(self):
        cap = compose([count(A, 100, "AAA"), count(B, 7)], [price("AAA", 10.0)],
                      [right(RightKind.VOTES_PER_SHARE, subject=B, value=10.0), right(RightKind.NON_VOTING, subject=B)])
        assert cap.quality is INSUFFICIENT

    def test_a_class_with_no_shares_contributes_nothing(self):
        cap = compose([count(A, 100, "AAA"), count(B, 0)], [price("AAA", 10.0)])
        assert cap.quality is EXACT and f"zero_shares:{B}" in cap.excluded

    def test_an_aggregate_member_is_excluded_never_added_beside_its_parts(self):
        rights = [right(RightKind.CONVERTIBLE_INTO, subject=m, target=A, value=1.0) for m in (B, C)]
        cap = compose([count(A, 100, "AAA"), count(B, 5), count(C, 120), count("x:BAndCMember", 125)], [price("AAA", 10)], rights)
        assert "aggregate:x:BAndCMember" in cap.excluded and cap.market_cap_low == (100 + 5 + 120) * 10


class TestStructuredConversion:
    def _visa_like(self, *, rate_instant=P, count_accession="0000000001-26-000001"):
        rights = [
            right(RightKind.AS_CONVERTED_SHARES, subject=A, value=100.0, start=rate_instant, end=rate_instant),
            right(RightKind.CONVERSION_RATE, subject=C, value=4.0, start=rate_instant, end=rate_instant),
            right(RightKind.CLASS_INVENTORY, subject="x:SeriesBPreferredMember", equity="preferred"),
            right(RightKind.AS_CONVERTED_SHARES, subject="x:SeriesBPreferredMember", value=2_000_000.0, decimals="-6",
                  start=rate_instant, end=rate_instant),
        ]
        counts = [count(A, 100, "AAA", accession=count_accession), count(C, 10, accession=count_accession)]
        return counts, rights

    def test_rate_into_the_as_converted_numeraire_and_participating_preferred_as_converted(self):
        counts, rights = self._visa_like()
        cap = compose(counts, [price("AAA", 2.0)], rights)
        c = next(x for x in cap.contributions if x.member == C)
        pref = next(x for x in cap.contributions if x.equity_kind == "participating_preferred")
        assert (c.treatment, c.ratio_low, c.contribution_low) == ("structured_conversion_rate", 4.0, 80.0)
        assert (pref.equivalent_shares_low, pref.equivalent_shares_high) == (1_500_000, 2_500_000)  # reported in millions
        assert cap.quality is BOUNDED and cap.market_cap_low == 200 + 80 + 3_000_000

    def test_a_rate_from_another_filing_and_another_instant_is_not_carried(self):
        counts, rights = self._visa_like(rate_instant=date(2024, 12, 31), count_accession="0000000001-26-000009")
        cap = compose(counts, [price("AAA", 2.0)], rights)
        assert cap.quality is INSUFFICIENT


class TestTemporal:
    def test_a_statement_carries_forward_with_its_days_disclosed(self):
        cap = compose([count(A, 100, "AAA", as_of=date(2026, 7, 27)), count(B, 7, as_of=date(2026, 7, 27))], [price("AAA", 10.0)],
                      [right(RightKind.CONVERTIBLE_INTO, subject=B, target=A, value=1.0)])
        assert cap.quality is EQUIVALENT and "rights_carried_forward:208d" in cap.gaps

    def test_a_later_statement_never_proves_an_earlier_date(self):
        cap = compose([count(A, 100, "AAA", as_of=date(2019, 12, 31)), count(B, 7, as_of=date(2019, 12, 31))], [price("AAA", 10.0)],
                      [right(RightKind.CONVERTIBLE_INTO, subject=B, target=A, value=1.0, start=date(2020, 1, 1))])
        assert cap.quality is INSUFFICIENT


class TestPreferred:
    def test_senior_preferred_stays_out_of_common_equity_and_is_reported_against_the_numerator(self):
        rights = [right(RightKind.PREFERRED_SHARES_OUTSTANDING, subject="x:SeriesAMember", value=1_000_000.0, start=P, end=P),
                  right(RightKind.LIQUIDATION_PREFERENCE, subject="x:SeriesAMember", value=1000.0, start=P, end=P),
                  right(RightKind.PREFERRED_DIVIDEND_RATE, subject="x:SeriesAMember", value=0.08, start=date(2025, 1, 1), end=P),
                  right(RightKind.CLASS_INVENTORY, subject="x:SeriesAMember", equity="preferred")]
        cap = compose([count(None, 100)], [price("AAA", 10)], rights, classes_reported=True)
        assert cap.market_cap_low == 1000 and "senior_equity_claims_on_free_cash_flow" in cap.gaps
        (senior,) = cap.senior_equity
        assert senior.annual_dividend == pytest.approx(80_000_000.0)


class TestPreferredBesideClasses:
    SERIES = "x:SeriesAPreferredMember"

    def _rights(self, *, participating):
        rights = [right(RightKind.CLASS_INVENTORY, subject=self.SERIES, equity="preferred"),
                  right(RightKind.PREFERRED_SHARES_OUTSTANDING, subject=self.SERIES, value=1_000.0, start=P, end=P),
                  right(RightKind.LIQUIDATION_PREFERENCE, subject=self.SERIES, value=1000.0, start=P, end=P),
                  right(RightKind.PREFERRED_DIVIDEND_RATE, subject=self.SERIES, value=0.05, start=date(2025, 1, 1), end=P)]
        if participating:
            rights += [right(RightKind.AS_CONVERTED_SHARES, subject=A, value=100.0, start=P, end=P),
                       right(RightKind.AS_CONVERTED_SHARES, subject=self.SERIES, value=40.0, start=P, end=P)]
        return rights

    def test_non_participating_preferred_is_never_common(self):
        cap = compose([count(A, 100, "AAA")], [price("AAA", 10.0)], self._rights(participating=False))
        assert cap.market_cap_low == 1000 and [c.member for c in cap.contributions] == [A]
        assert [s.member for s in cap.senior_equity] == [self.SERIES]

    def test_participating_preferred_enters_as_converted_and_is_not_also_senior(self):
        cap = compose([count(A, 100, "AAA")], [price("AAA", 10.0)], self._rights(participating=True))
        assert cap.market_cap_low == 1000 + 400 and cap.senior_equity == ()

    def test_participating_preferred_beside_an_issuer_level_count_is_withheld(self):
        cap = compose([count(None, 100)], [price("AAA", 10.0)], self._rights(participating=True), classes_reported=True)
        assert cap.quality is INSUFFICIENT and "participating_preferred_beside_issuer_level_count" in cap.gaps


class TestNoListedClass:
    def test_one_parity_group_lets_the_case_listing_price_every_class(self):
        cap = compose([count(A, 100), count(B, 20)], [price("AAA", 10.0)], [right(RightKind.ECONOMIC_PARITY, related=(A, B))])
        assert (cap.quality, cap.market_cap_low) == (EQUIVALENT, 1200.0)
        assert "listed_class_unproven_within_parity_group" in cap.gaps

    def test_without_parity_two_unlinked_classes_are_withheld(self):
        cap = compose([count(A, 100), count(B, 20)], [price("AAA", 10.0)])
        assert cap.quality is INSUFFICIENT


class TestYield:
    def test_a_bounded_cap_inverts_into_a_yield_interval(self):
        cap = compose([count(A, 100, "AAA"), count(B, 10), count(C, 90, "AAC")], [price("AAA", 10.0), price("AAC", 9.0)],
                      [right(RightKind.ECONOMIC_PARITY, related=(A, B, C))])
        y = issuer_fcf_yield(95.0, cap)
        assert (y.yield_low, y.yield_high) == (95.0 / cap.market_cap_high, 95.0 / cap.market_cap_low)
        assert y.yield_low < y.yield_high

    def test_no_yield_without_a_denominator(self):
        cap = compose([count(A, 100, "AAA"), count(B, 7)], [price("AAA", 10.0)])
        y = issuer_fcf_yield(95.0, cap)
        assert (y.yield_low, y.yield_high) == (None, None) and not math.isnan(y.free_cash_flow)


class TestPerClassRates:
    def test_each_class_takes_its_own_rate(self):
        rights = [right(RightKind.AS_CONVERTED_SHARES, subject=A, value=100.0, start=P, end=P),
                  right(RightKind.CONVERSION_RATE, subject="x:B1Member", value=1.5445, start=P, end=P),
                  right(RightKind.CONVERSION_RATE, subject="x:B2Member", value=1.5014, start=P, end=P)]
        cap = compose([count(A, 100, "AAA"), count("x:B1Member", 10), count("x:B2Member", 20)], [price("AAA", 1.0)], rights)
        by = {c.member: c.ratio_low for c in cap.contributions}
        assert by == {A: 1.0, "x:B1Member": 1.5445, "x:B2Member": 1.5014}
        assert cap.market_cap_low == pytest.approx(100 + 15.445 + 30.028)


class TestDeterminism:
    def test_identical_under_shuffled_classes_rights_and_decoy_evidence(self):
        import random

        counts = [count(A, 100, "AAA"), count(B, 10), count(C, 90, "AAC"), count("x:BAndCMember", 100)]
        rights = [right(RightKind.ECONOMIC_PARITY, related=(A, B, C)), right(RightKind.CONVERTIBLE_INTO, subject=B, target=A),
                  right(RightKind.EARNINGS_PER_SHARE, subject=B, value=1.0, decimals="2", strength=EvidenceStrength.ACCOUNTING_CORROBORATION)]
        decoys = [right(RightKind.CONVERTIBLE_INTO, subject=B, target=C, value=3.0, start=date(2027, 1, 1), end=date(2027, 12, 31),
                        accession="0000000001-27-000001")]  # a later filing: never applies backward
        prices = [price("AAA", 10.0), price("AAC", 9.0)]
        reference = compose(counts, prices, rights)
        rng = random.Random(3)
        for _ in range(5):
            c, r, p = counts[:], rights + decoys, prices[:]
            rng.shuffle(c), rng.shuffle(r), rng.shuffle(p)
            assert compose(c, p, r) == reference
