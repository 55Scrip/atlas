"""The issuer valuation basis a Case's fiscal_epoch_v3 valuation is priced on
-- over the reader fixture's real Alphabet / Mastercard evidence."""
from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone

import pytest

from atlas.alpha.issuer_equity.valuation_basis import IssuerValuationBasisBuilder
from atlas.analysis_engine.valuation.contracts import (
    ShareCountMethod,
    ValuationDataGapKind as G,
    ValuationDecisionEligibility as E,
)
from atlas.analysis_engine.valuation.issuer_basis import IssuerDenominatorQuality as Q
from atlas.analysis_engine.valuation.models import FcfYieldEpochObservation, FcfYieldEvidence
from tests.unit.alpha.issuer_equity.test_reader import reader  # noqa: F401  (fixture)

NOW = datetime(2026, 9, 11, 12, tzinfo=timezone.utc)


def _epochs(observed: str, price: float = 1.0) -> FcfYieldEvidence:
    current = FcfYieldEpochObservation(
        fiscal_period="2025-12-31", available_from=date(2026, 2, 5), observed_on=observed, free_cash_flow=1e9,
        share_price=price, shares_outstanding=1.0, currency="USD", free_cash_flow_fact_id="s:free_cash_flow:2025-12-31",
        share_price_fact_id=f"q:share_price:{observed}", shares_outstanding_fact_id=f"q:shares_outstanding:{observed}")
    return FcfYieldEvidence(eligibility=E.INSUFFICIENT, minimum_prior_epochs=3,
                            share_count_method=ShareCountMethod.CURRENT_SHARE_COUNT_PROXY, current=current)


def _build(reader, ticker, observed):  # noqa: F811
    return IssuerValuationBasisBuilder(reader).build(ticker=ticker, every_version=(), records=(),
                                                     epochs=_epochs(observed), historical=None, evaluated_at=NOW)


class TestCurrentOnTheCasesOwnDate:
    def test_goog_is_not_synchronized_with_googl_on_its_own_date(self, reader):  # noqa: F811
        basis = _build(reader, "GOOG", "2026-08-21")
        assert basis.current is None and basis.current_gap is G.CURRENT_ISSUER_PRICE_NOT_SYNCHRONIZED

    def test_googl_likewise_and_the_february_composition_is_never_offered(self, reader):  # noqa: F811
        basis = _build(reader, "GOOGL", "2026-08-24")
        assert basis.current is None and basis.current_gap is G.CURRENT_ISSUER_PRICE_NOT_SYNCHRONIZED
        assert reader.current("GOOGL", date(2026, 9, 11)).economic_date == date(2026, 2, 27)  # exists, not used

    def test_goog_and_googl_converge_where_both_are_priced_the_same_day(self, reader):  # noqa: F811
        goog, googl = _build(reader, "GOOG", "2026-02-27"), _build(reader, "GOOGL", "2026-02-27")
        assert goog.current.market_cap_low == googl.current.market_cap_low
        assert goog.current.quality is Q.EQUIVALENT
        assert (goog.current.share_price, googl.current.share_price) == (311.43, 311.76)  # each its own price

    def test_mastercard_composes_on_its_own_date(self, reader):  # noqa: F811
        basis = _build(reader, "MA", "2026-08-24")
        assert basis.current.economic_date == date(2026, 8, 24) and basis.current.quality is Q.EQUIVALENT
        assert basis.current.market_cap_low == pytest.approx((869_464_115 + 6_545_825) * 599.86)

    def test_single_class_is_its_cover_count_times_its_price(self, reader):  # noqa: F811
        basis = _build(reader, "ONE", "2026-08-25")
        assert basis.current.quality is Q.EXACT
        assert basis.current.market_cap_low == pytest.approx(823_000_000 * 205.69)  # never the provider's 819M

    def test_a_share_basis_change_is_missing_denominator_evidence(self, reader):  # noqa: F811
        basis = _build(reader, "SPL", "2026-08-13")
        assert basis.current is None and basis.current_gap is G.DENOMINATOR_EVIDENCE_MISSING

    def test_an_unknown_issuer_is_missing_denominator_evidence(self, reader):  # noqa: F811
        basis = _build(reader, "NOPE", "2026-08-13")
        assert basis.current_gap is G.DENOMINATOR_EVIDENCE_MISSING

    def test_nothing_to_value_is_no_basis(self, reader):  # noqa: F811
        assert IssuerValuationBasisBuilder(reader).build(ticker="MA", every_version=(), records=(), epochs=None,
                                                         historical=None, evaluated_at=NOW) is None


# -- history and claims, over a stand-in reader -------------------------------------------------------------

from dataclasses import dataclass, field  # noqa: E402

from atlas.alpha.investment_case.historical_market_cap import (  # noqa: E402
    AlignmentQuality,
    HistoricalMarketCapEpoch,
    HistoricalMarketCapEvidence,
    SecurityScope,
    ShareCountScope,
)
from atlas.alpha.issuer_equity.composer import DenominatorQuality, IssuerCommonEquityMarketCap  # noqa: E402
from atlas.analysis_engine.business_data.models import BusinessRecord  # noqa: E402
from tests.unit.alpha.issuer_equity.test_claims import vst_rights  # noqa: E402


@dataclass
class _Reader:
    rights_: tuple = ()
    epoch_cap: float = 0.0
    calls: list = field(default_factory=list)

    def prime(self, company, records):
        pass

    def issuer_cik(self, ticker):
        return "0001692819"

    def rights(self, cik, evaluated_on):
        return self.rights_

    def price_series(self, symbol):
        from atlas.alpha.issuer_equity.composer import ListedPrice
        return {date(2026, 9, 8): ListedPrice(symbol, date(2026, 9, 8), 151.72, "r")}

    def on_date(self, ticker, on, evaluated_on):
        self.calls.append(("on_date", on))
        return IssuerCommonEquityMarketCap("0001692819", on, date(2026, 8, 3), "a", "USD", DenominatorQuality.ISSUER_EXACT,
                                           50.9e9, 50.9e9, (), (), (), ())

    def at_epoch(self, ticker, observed_on, accession, period_end, evaluated_on, *, factor=1.0):
        self.calls.append(("at_epoch", observed_on, accession, factor))
        return IssuerCommonEquityMarketCap("0001692819", observed_on, period_end, accession, "USD",
                                           DenominatorQuality.ISSUER_EQUIVALENT, self.epoch_cap, self.epoch_cap, (), (), (), ())


def _epoch(fy: int, observed: str, *, fcf=1e9, shares=300e6, price=10.0):
    return FcfYieldEpochObservation(
        fiscal_period=f"{fy}-12-31", available_from=date(fy + 1, 2, 20), observed_on=observed, free_cash_flow=fcf,
        share_price=price, shares_outstanding=shares, currency="USD",
        free_cash_flow_fact_id=f"stmt-{fy}:free_cash_flow:{fy}-12-31", share_price_fact_id=f"q{fy}:share_price:{observed}",
        shares_outstanding_fact_id=f"q{fy}:shares_outstanding:{observed}")


def _hist(epoch, *, raw=12.0, aligned=250e6, accession=None, quality=AlignmentQuality.FULLY_ALIGNED):
    return HistoricalMarketCapEpoch(
        fiscal_period=epoch.fiscal_period, observed_on=epoch.observed_on, quality=quality, gaps=(), currency="USD",
        free_cash_flow=epoch.free_cash_flow, proxy_market_cap=epoch.market_cap_proxy, raw_close=raw,
        aligned_share_count=aligned, market_cap=raw * aligned, cumulative_factor=1.0, share_count_accession=accession,
        share_count_scope=ShareCountScope.SECURITY if accession else ShareCountScope.ISSUER)


def _statement(fy: int) -> BusinessRecord:
    import hashlib
    from atlas.analysis_engine.business_data.models import RawBusinessDocument
    from atlas.analysis_engine.business_data.pipeline import ingest

    return ingest(RawBusinessDocument(
        identifier=f"stmt-{fy}", company="VST", source_kind="financial_statement",
        published_at=datetime(fy + 1, 2, 20, tzinfo=timezone.utc), provider_id="sec_edgar", raw_reference="x",
        content_hash=hashlib.sha256(str(fy).encode()).hexdigest(), period_start=date(fy, 1, 1), period_end=date(fy, 12, 31),
        language="en", metadata={"free_cash_flow": 1e9, "currency": "USD"}), evaluated_at=NOW).record


class TestHistoryAndClaims:
    def _build(self, reader, priors, hist, current=None):
        epochs = FcfYieldEvidence(eligibility=E.INSUFFICIENT if current is None else E.ELIGIBLE, minimum_prior_epochs=3,
                                  share_count_method=ShareCountMethod.CURRENT_SHARE_COUNT_PROXY,
                                  current=current, prior_epochs=tuple(priors),
                                  position=None if current is None else __import__(
                                      "atlas.analysis_engine.valuation.models", fromlist=["position_of"]).position_of(
                                      current.fcf_yield, tuple(p.fcf_yield for p in priors)))
        evidence = HistoricalMarketCapEvidence("raw_price_split_aligned_shares_v1", SecurityScope.SINGLE_SECURITY,
                                               tuple(hist), ())
        records = tuple(_statement(int(e.fiscal_period[:4])) for e in (*priors, *((current,) if current else ())))
        fixed = []
        for e in (*priors, *((current,) if current else ())):
            rid = next(r.id for r in records if r.period_end.year == int(e.fiscal_period[:4]))
            fixed.append(replace(e, free_cash_flow_fact_id=f"{rid}:free_cash_flow:{e.fiscal_period}"))
        evidence_epochs = replace(epochs, prior_epochs=tuple(fixed[:len(priors)]),
                                  current=fixed[-1] if current else None)
        return IssuerValuationBasisBuilder(reader).build(ticker="VST", every_version=records, records=records,
                                                         epochs=evidence_epochs, historical=evidence, evaluated_at=NOW)

    def test_single_class_history_is_the_raw_close_times_the_aligned_count_never_todays_count(self):
        priors = [_epoch(2023, "2024-02-29"), _epoch(2024, "2025-02-28")]
        basis = self._build(_Reader(), priors, [_hist(priors[0]), _hist(priors[1], raw=14.0)])
        caps = {e.fiscal_period: e.market_cap for e in basis.epochs}
        assert caps["2023-12-31"].market_cap_low == 12.0 * 250e6 and caps["2024-12-31"].market_cap_low == 14.0 * 250e6
        assert caps["2023-12-31"].share_price == 12.0  # the raw close, never the adjusted proxy price

    def test_class_count_history_is_the_issuer_composition_at_the_epoch(self):
        priors = [_epoch(2024, "2025-02-28")]
        reader = _Reader(epoch_cap=9e9)
        basis = self._build(reader, priors, [_hist(priors[0], accession="acc-1")])
        assert basis.epochs[0].market_cap.market_cap_low == 9e9 and basis.epochs[0].market_cap.quality is Q.EQUIVALENT
        assert ("at_epoch", date(2025, 2, 28), "acc-1", 1.0) in reader.calls

    def test_an_unaligned_epoch_is_withheld_with_its_reason(self):
        priors = [_epoch(2024, "2025-02-28")]
        basis = self._build(_Reader(), priors, [_hist(priors[0], quality=AlignmentQuality.INSUFFICIENT)])
        assert basis.epochs[0].market_cap is None and basis.epochs[0].gap is G.DENOMINATOR_EVIDENCE_MISSING

    def test_each_fiscal_year_gets_its_own_senior_claim(self):
        priors = [_epoch(2019, "2020-02-28"), _epoch(2023, "2024-02-29"), _epoch(2024, "2025-02-28")]
        current = _epoch(2025, "2026-09-08")
        basis = self._build(_Reader(rights_=vst_rights()), priors, [_hist(p) for p in priors], current)
        claims = {c.fiscal_period: (c.low / 1e6, c.high / 1e6) for c in basis.claims}
        assert "2019-12-31" not in claims  # before any series was issued
        assert claims["2023-12-31"] == pytest.approx((150.2315, 150.3521), abs=1e-3)
        assert claims["2025-12-31"] == pytest.approx((192.2509, 192.2522), abs=1e-3)
        assert basis.current.economic_date == date(2026, 9, 8) and basis.unquantified_claims == ()


@dataclass
class _GappedReader(_Reader):
    """The current composition insufficient, with the gaps given."""

    gaps: tuple = ()

    def on_date(self, ticker, on, evaluated_on):
        return IssuerCommonEquityMarketCap("0001692819", on, date(2026, 8, 3), "a", "USD",
                                           DenominatorQuality.INSUFFICIENT_EVIDENCE, None, None, (), (), (), self.gaps)


class TestCurrencyIsItsOwnReason:
    def _gap(self, *gaps):
        return IssuerValuationBasisBuilder(_GappedReader(gaps=gaps)).build(
            ticker="AAA", every_version=(), records=(), epochs=_epochs("2026-09-08"), historical=None,
            evaluated_at=NOW).current_gap

    def test_listed_prices_in_differing_or_unstated_currencies(self):
        assert self._gap("price_currency_mismatch") is G.CURRENT_ISSUER_PRICE_CURRENCY_UNPROVEN
        assert self._gap("price_currency_unproven:AAC") is G.CURRENT_ISSUER_PRICE_CURRENCY_UNPROVEN

    def test_an_unpriced_sibling_is_still_the_date(self):
        assert self._gap("no_price:AAC", "price_currency_unproven:AAB") is G.CURRENT_ISSUER_PRICE_NOT_SYNCHRONIZED

    def test_the_two_reasons_are_distinct(self):
        assert G.CURRENT_ISSUER_PRICE_CURRENCY_UNPROVEN is not G.CURRENT_ISSUER_PRICE_NOT_SYNCHRONIZED
        assert G.CURRENT_ISSUER_PRICE_CURRENCY_UNPROVEN is not G.CURRENCY_MISMATCH


class TestNoNetwork:
    def test_composing_a_basis_makes_no_network_attempt(self, reader, monkeypatch):  # noqa: F811
        import socket

        def refuse(*a, **k):
            raise AssertionError("network attempted while composing a valuation basis")

        monkeypatch.setattr(socket.socket, "connect", refuse)
        monkeypatch.setattr(socket, "getaddrinfo", refuse)
        for ticker, on in (("GOOG", "2026-08-21"), ("MA", "2026-08-24"), ("ONE", "2026-08-25")):
            _build(reader, ticker, on)
