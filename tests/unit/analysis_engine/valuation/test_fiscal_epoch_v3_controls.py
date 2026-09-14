"""fiscal_epoch_v3 production controls, pinned with the issuer yields Atlas's
own persisted evidence produces (the FISCAL_EPOCH_v3 shadow audit and the
migration rehearsal): each Case's current and prior issuer market caps and
senior claims, run through the production evaluator."""
from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest

from atlas.analysis_engine.valuation.cash_flow import evaluate_fcf_yield_relative, fiscal_epochs
from atlas.analysis_engine.valuation.contracts import HistoricalYieldPosition as P, ValuationDataGapKind as G
from atlas.analysis_engine.valuation.contracts import ValuationStatus as S
from atlas.analysis_engine.valuation.issuer_basis import (
    EpochDenominator,
    IssuerDenominatorQuality as Q,
    IssuerMarketCap,
    IssuerValuationBasis,
    SeniorClaim,
)
from tests.unit.analysis_engine.valuation._epochs import APPLICABLE, AS_OF, annual_history


def _run(fcf_by_year: dict[int, float], caps: dict[int, tuple[float, float]], claims=None, quality=Q.EXACT,
         current_date=None):
    """Fiscal years `fcf_by_year` (the last is current), each priced on its
    issuer market cap interval `caps[year]`."""
    business, market = annual_history(fcf_by_year, {y: 10.0 for y in fcf_by_year})
    statements = frozenset(f.source_record_id for f in business if f.source_record_id.startswith("stmt-"))
    epochs = fiscal_epochs(tuple(business), tuple(market), statement_record_ids=statements, industry=APPLICABLE,
                           evaluated_at=AS_OF)

    def cap(epoch, on=None):
        low, high = caps[int(epoch.fiscal_period[:4])]
        q = quality if low != high else Q.EXACT if quality is Q.BOUNDED else quality
        return IssuerMarketCap(on or date.fromisoformat(epoch.observed_on), 10.0, low, high,
                               Q.BOUNDED if low != high else q, "USD")

    basis = IssuerValuationBasis(
        current=cap(epochs.current, current_date),
        epochs=tuple(EpochDenominator(e.fiscal_period, e.observed_on, cap(e)) for e in epochs.prior_epochs),
        claims=tuple(SeniorClaim(f"{y}-12-31", lo, hi) for y, (lo, hi) in sorted((claims or {}).items())))
    return evaluate_fcf_yield_relative(tuple(business), tuple(market), statement_record_ids=statements,
                                       industry=APPLICABLE, evaluated_at=AS_OF, basis=basis)


def _point(fcf, yield_percent):
    cap = fcf / (yield_percent / 100)
    return (cap, cap)


class TestMastercard:
    """Issuer (class A listed + class B at filed parity) yields."""

    def test_hold_to_add_rests_on_a_current_yield_above_every_valid_prior(self):
        yields = {2020: 1.956, 2021: 2.561, 2022: 3.166, 2023: 2.618, 2024: 2.716, 2025: 3.265}
        f = _run({y: 100.0 for y in yields}, {y: _point(100.0, v) for y, v in yields.items()})
        assert f.fcf_yield_evidence.position is P.ABOVE_ALL_PRIOR and f.status is S.UNDERVALUED
        assert f.current_yield == pytest.approx(0.03265)
        assert f.current_yield / max(f.historical_yields) - 1 == pytest.approx(0.031, abs=0.001)


class TestVistra:
    def test_the_senior_preferred_claim_is_deducted_and_it_stays_expensive(self):
        fcf = {2019: 2023e6, 2020: 2078e6, 2023: 3777e6, 2024: 2485e6, 2025: 1318e6}
        caps = {2019: 9.378e9, 2020: 8.441e9, 2023: 19.168e9, 2024: 45.411e9, 2025: 50.922571785e9}
        claims = {2023: (150.2315e6, 150.3521e6), 2024: (192.2509e6, 192.2522e6), 2025: (192.2509e6, 192.2522e6)}
        f = _run(fcf, {y: (c, c) for y, c in caps.items()}, claims=claims)
        current = f.fcf_yield_evidence.current
        assert current.raw_free_cash_flow == 1318e6
        assert current.free_cash_flow == pytest.approx(1125.75e6, abs=0.01e6)
        assert f.current_yield == pytest.approx(0.02211, abs=1e-5)
        assert f.fcf_yield_evidence.position is P.BELOW_ALL_PRIOR and f.status is S.EXPENSIVE
        assert [e.free_cash_flow == e.raw_free_cash_flow for e in f.fcf_yield_evidence.prior_epochs] == [
            True, True, False, False]  # no claim before the 2021 / 2023 issuances


class TestVisa:
    def test_bounded_issuer_denominator_is_usable_because_both_ends_agree(self):
        fcf = {2021: 14.522e9, 2022: 17.878e9, 2024: 18.690e9, 2025: 21.577e9}
        caps = {2021: (418.172e9, 418.754e9), 2022: (456.122e9, 456.773e9), 2024: (624.327e9, 625.272e9),
                2025: (685.419e9, 686.515e9)}
        f = _run(fcf, caps, quality=Q.BOUNDED)
        current = f.fcf_yield_evidence.current
        assert (current.fcf_yield_low, current.fcf_yield_high) == pytest.approx((0.03143, 0.03148), abs=1e-5)
        assert f.fcf_yield_evidence.position is P.WITHIN_PRIOR_RANGE and f.status is S.FAIRLY_VALUED
        assert f.fcf_yield_evidence.withheld_reasons == ()


class TestUnionPacific:
    def test_fairly_valued_sits_just_inside_the_prior_range(self):
        yields = {2016: 4.662, 2017: 3.9, 2018: 3.7, 2019: 3.5, 2020: 3.4, 2021: 3.3, 2022: 3.2, 2023: 3.15,
                  2024: 3.086, 2025: 3.108}
        f = _run({y: 100.0 for y in yields}, {y: _point(100.0, v) for y, v in yields.items()})
        assert f.fcf_yield_evidence.position is P.WITHIN_PRIOR_RANGE and f.status is S.FAIRLY_VALUED
        assert f.current_yield / min(f.historical_yields) - 1 == pytest.approx(0.007, abs=0.001)  # near the boundary


class TestAlphabet:
    def test_goog_and_googl_are_withheld_on_a_stale_issuer_composition(self):
        yields = {2020: 3.127, 2021: 3.749, 2022: 5.179, 2023: 3.959, 2024: 3.482, 2025: 1.945}
        f = _run({y: 100.0 for y in yields}, {y: _point(100.0, v) for y, v in yields.items()},
                 current_date=date(2026, 2, 27))  # the last day both classes were priced, not the Case's own
        assert f.status is S.INSUFFICIENT_INPUT and f.current_yield is None
        assert f.fcf_yield_evidence.withheld_reasons == (G.CURRENT_ISSUER_PRICE_NOT_SYNCHRONIZED,)
        assert len(f.fcf_yield_evidence.prior_epochs) == 5  # history stays described
