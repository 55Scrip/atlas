"""Senior preferred claims on fiscal-year free cash flow (common_attributable_fcf_v1).

The VST, Alphabet and Visa controls use the terms their own filings state
(as persisted in Atlas's class-rights evidence)."""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from atlas.alpha.class_rights_evidence.models import ClassRightsObservation, EvidenceStrength, RightKind
from atlas.alpha.issuer_equity.claims import ClaimStatus, FiscalYear, compose_senior_claims

NOW = datetime(2026, 9, 11, tzinfo=timezone.utc)
S, F = EvidenceStrength.STRUCTURED_FILING, EvidenceStrength.FILING_STATEMENT
A, B, C = "us-gaap:SeriesAPreferredStockMember", "us-gaap:SeriesBPreferredStockMember", "us-gaap:SeriesCPreferredStockMember"


def right(kind, *, subject=None, value=None, start, end=None, strength=S, accession="0001692819-26-000019"):
    end = end or start
    return ClassRightsObservation(
        issuer_cik="0001692819", accession=accession, form="10-Q", filing_date=date(2026, 8, 10),
        observation_key=f"{kind.value}|{subject}|{value}|{start}|{end}|{strength.value}", kind=kind, strength=strength,
        subject_member=subject, subject_label=None, target_member=None, target_label=None, related_members=(),
        related_labels=(), value=value, value_low=None, value_high=None, unit=None, decimals=None,
        equity_kind="preferred", effective_from=start, effective_to=end, concept="c", context_id="ctx", excerpt=None,
        parser_version="series_terms_v1", retrieved_at=NOW, recorded_at=NOW)


def year(y):
    return FiscalYear(date(y, 1, 1), date(y, 12, 31))


def vst_rights():
    """VST's three senior non-convertible series, as its 2026-08-10 10-Q tabulates them."""
    q2 = date(2026, 6, 30)
    out = []
    for member, onset, reset, rate, issued, outstanding in (
            (A, date(2021, 10, 15), date(2026, 10, 15), 0.08, 1_000_000, 1_000_000),
            (B, date(2021, 12, 10), date(2026, 12, 15), 0.07, 1_000_000, 1_000_000),
            (C, date(2023, 12, 29), date(2029, 1, 15), 0.08875, 476_081, 476_066)):
        out += [
            right(RightKind.SERIES_ISSUED_ON, subject=member, value=issued, start=onset, strength=F),
            right(RightKind.PREFERRED_DIVIDEND_RATE, subject=member, value=rate, start=onset,
                  end=date(reset.year, reset.month, reset.day - 1), strength=F),
            right(RightKind.DIVIDEND_RATE_RESETS_ON, subject=member, start=reset, strength=F),
            right(RightKind.PREFERRED_SHARES_ISSUED, subject=member, value=issued, start=q2),
            right(RightKind.PREFERRED_SHARES_OUTSTANDING, subject=member, value=outstanding, start=q2),
            right(RightKind.LIQUIDATION_PREFERENCE, subject=member, value=1000.0, start=q2),
        ]
    out += [right(RightKind.PREFERRED_SHARES_OUTSTANDING, value=2_476_066, start=date(2025, 12, 31)),
            right(RightKind.PREFERRED_SHARES_OUTSTANDING, value=2_476_066, start=q2)]
    return tuple(out)


class TestVstControl:
    def test_claims_begin_at_each_series_own_issuance(self):
        claims = compose_senior_claims(vst_rights(), (year(2019), year(2020)))
        assert all(c.status is ClaimStatus.NONE and c.high == 0 for c in claims.values())

    def test_fy2025_claim_is_the_full_year_contractual_dividend(self):
        c = compose_senior_claims(vst_rights(), (year(2025),))[year(2025)]
        assert c.status is ClaimStatus.QUANTIFIED
        assert c.low == pytest.approx(80e6 + 70e6 + 476_066 * 1000 * 0.08875)
        assert c.high == pytest.approx(80e6 + 70e6 + 476_081 * 1000 * 0.08875)
        assert (c.low / 1e6, c.high / 1e6) == pytest.approx((192.2509, 192.2522), abs=1e-3)

    def test_series_c_accrues_only_its_last_days_of_fy2023(self):
        c = compose_senior_claims(vst_rights(), (year(2023),))[year(2023)]
        series_c = next(s for s in c.series if s.member == C)
        assert series_c.accrual_days == (2, 3)  # Dec 29-31, the issue day possibly excluded
        assert series_c.high < 0.4e6  # a few days, never a full year's 42.25M
        assert (c.low / 1e6, c.high / 1e6) == pytest.approx((150.2315, 150.3521), abs=1e-3)

    def test_fixed_rate_does_not_run_past_its_floating_reset(self):
        c = compose_senior_claims(vst_rights(), (FiscalYear(date(2026, 1, 1), date(2026, 12, 31)),))
        claim = next(iter(c.values()))
        assert claim.status is ClaimStatus.UNQUANTIFIED
        assert f"rate_unproven:{A}" in claim.reasons  # Series A floats from 2026-10-15; no rate is invented

    def test_order_of_evidence_never_matters(self):
        years = (year(2023), year(2024), year(2025))
        assert compose_senior_claims(vst_rights(), years) == compose_senior_claims(tuple(reversed(vst_rights())), years)


class TestAlphabetMandatoryConvertibleControl:
    def rights(self):
        member = "us-gaap:ConvertiblePreferredStockMember"
        zeros = [right(RightKind.PREFERRED_SHARES_OUTSTANDING, value=0.0, start=date(y, 12, 31), accession=f"a{y}")
                 for y in (2021, 2022, 2024, 2025)]
        return tuple(zeros + [
            right(RightKind.PREFERRED_DIVIDEND_RATE, subject=member, value=0.0625, start=date(2026, 6, 5)),
            right(RightKind.LIQUIDATION_PREFERENCE, subject=member, value=1000.0, start=date(2026, 6, 5)),
            right(RightKind.CONVERSION_RATIO_RANGE, subject="goog:SeriesAMandatoryConvertiblePreferredStockMember",
                  start=date(2026, 6, 5)),
            right(RightKind.PREFERRED_SHARES_OUTSTANDING, value=19_000_000, start=date(2026, 6, 30)),
            # a rate reported for a period in which nothing was outstanding creates no claim
            right(RightKind.PREFERRED_DIVIDEND_RATE, value=0.0625, start=date(2025, 1, 1), end=date(2025, 12, 31)),
        ])

    def test_the_2026_claim_never_touches_fy2025_or_earlier(self):
        claims = compose_senior_claims(self.rights(), tuple(year(y) for y in range(2020, 2026)))
        assert all(c.status is ClaimStatus.NONE for c in claims.values())

    def test_fy2026_is_not_quantified_before_its_terms_are(self):
        c = compose_senior_claims(self.rights(), (year(2026),))[year(2026)]
        assert c.status is ClaimStatus.UNQUANTIFIED  # onset only bracketed, the rate only at issuance


class TestParticipatingPreferred:
    def test_as_converted_preferred_claims_nothing(self):
        rights = (
            right(RightKind.AS_CONVERTED_SHARES, subject=A, value=7_000_000, start=date(2025, 9, 30)),
            right(RightKind.PREFERRED_SHARES_OUTSTANDING, subject=A, value=1_000, start=date(2025, 9, 30)),
            right(RightKind.PREFERRED_DIVIDEND_RATE, subject=A, value=0.05, start=date(2020, 1, 1), end=date(2025, 12, 31)),
            right(RightKind.LIQUIDATION_PREFERENCE, subject=A, value=1000.0, start=date(2025, 9, 30)),
        )
        assert compose_senior_claims(rights, (year(2025),))[year(2025)].status is ClaimStatus.NONE

    def test_an_aggregate_preferred_member_is_not_a_series(self):
        d = date(2021, 9, 30)
        rights = (
            right(RightKind.AS_CONVERTED_SHARES, subject=B, value=1.0, start=d),
            right(RightKind.AS_CONVERTED_SHARES, subject=C, value=1.0, start=d),
            right(RightKind.PREFERRED_SHARES_OUTSTANDING, subject=B, value=2e6, start=d),
            right(RightKind.PREFERRED_SHARES_OUTSTANDING, subject=C, value=3e6, start=d),
            right(RightKind.PREFERRED_SHARES_OUTSTANDING, subject="us-gaap:PreferredStockMember", value=5e6, start=d),
        )
        assert compose_senior_claims(rights, (year(2021),))[year(2021)].status is ClaimStatus.NONE


class TestTermination:
    def rights(self, *, ended=None, zero_on=None):
        out = [right(RightKind.SERIES_ISSUED_ON, subject=A, value=1e6, start=date(2020, 1, 1), strength=F),
               right(RightKind.PREFERRED_DIVIDEND_RATE, subject=A, value=0.10, start=date(2020, 1, 1),
                     end=date(2030, 12, 31), strength=F),
               right(RightKind.PREFERRED_SHARES_OUTSTANDING, subject=A, value=1e6, start=date(2022, 12, 31)),
               right(RightKind.LIQUIDATION_PREFERENCE, subject=A, value=100.0, start=date(2022, 12, 31))]
        if ended:
            out.append(right(RightKind.SERIES_TERMINATED_ON, subject=A, start=ended, strength=F))
        if zero_on:
            out.append(right(RightKind.PREFERRED_SHARES_OUTSTANDING, subject=A, value=0.0, start=zero_on))
        return tuple(out)

    def test_a_dated_end_stops_the_claim_mid_year(self):
        c = compose_senior_claims(self.rights(ended=date(2023, 7, 1)), (year(2023), year(2024)))
        assert c[year(2024)].status is ClaimStatus.NONE
        assert 0.49 < c[year(2023)].low / 10e6 <= c[year(2023)].high / 10e6 < 0.51

    def test_an_affirmative_zero_ends_it_between_the_evidence(self):
        c = compose_senior_claims(self.rights(zero_on=date(2023, 12, 31)), (year(2023), year(2024)))
        assert c[year(2024)].status is ClaimStatus.NONE
        assert c[year(2023)].status is ClaimStatus.QUANTIFIED
        assert c[year(2023)].low == 0 and c[year(2023)].high == pytest.approx(10e6)  # ended somewhere in 2023

    def test_unknown_termination_widens_the_interval_never_guesses(self):
        c = compose_senior_claims(self.rights(), (year(2023),))[year(2023)]
        assert c.low == 0 and c.high == pytest.approx(10e6)  # last seen outstanding at 2022-12-31


class TestUnquantified:
    def test_unknown_onset_is_unquantified(self):
        rights = (right(RightKind.PREFERRED_SHARES_OUTSTANDING, subject=A, value=1e6, start=date(2024, 12, 31)),
                  right(RightKind.PREFERRED_DIVIDEND_RATE, subject=A, value=0.05, start=date(2024, 1, 1), end=date(2024, 12, 31)),
                  right(RightKind.LIQUIDATION_PREFERENCE, subject=A, value=100.0, start=date(2024, 12, 31)))
        c = compose_senior_claims(rights, (year(2023),))[year(2023)]
        assert c.status is ClaimStatus.UNQUANTIFIED and f"onset_unknown:{A}" in c.reasons

    def test_conflicting_issuance_dates_are_unquantified(self):
        rights = (right(RightKind.SERIES_ISSUED_ON, subject=A, value=1.0, start=date(2020, 1, 1), strength=F),
                  right(RightKind.SERIES_ISSUED_ON, subject=A, value=1.0, start=date(2020, 2, 1), strength=F))
        assert compose_senior_claims(rights, (year(2021),))[year(2021)].status is ClaimStatus.UNQUANTIFIED

    def test_no_preferred_evidence_is_no_claim(self):
        assert compose_senior_claims((), (year(2025),))[year(2025)].status is ClaimStatus.NONE
