"""The issuer basis for one Case's fiscal_epoch_v3 valuation, composed from
persisted evidence only (`atlas.analysis_engine.valuation.issuer_basis`).

For each fiscal epoch the Case's FCF-yield valuation will compare:

- **prior epochs** -- the epoch's aligned historical market capitalisation
  (`historical_market_cap`: raw close × period share count on the raw close's
  own share basis). A single-listing issuer's issuer-level count is its whole
  common equity, so that product is exact. Where the Case's count is a class
  count (a multi-class issuer), the issuer's common equity is composed class
  by class at the epoch -- the same filing's counts, every listed class's own
  raw price that day, rights that held then (`IssuerEquityReader.at_epoch`).
  An epoch neither can price is absent, with its reason.
- **the current observation** -- the issuer composition on exactly the Case's
  own current market date (`IssuerEquityReader.on_date`). A listed sibling
  class unpriced that day is `CURRENT_ISSUER_PRICE_NOT_SYNCHRONIZED`; listed
  classes whose prices do not state one currency are
  `CURRENT_ISSUER_PRICE_CURRENCY_UNPROVEN`; any other insufficiency is
  `DENOMINATOR_EVIDENCE_MISSING`. A composition from another date is never
  offered as current.
- **senior claims** -- each epoch's fiscal year, from the issuer's rights
  evidence filed by the evaluation date (`claims.compose_senior_claims`).

Nothing here decides; the evaluator applies the basis. Deterministic.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy.engine import Engine

from atlas.alpha.investment_case.historical_market_cap import ALIGNED_QUALITIES, HistoricalMarketCapEvidence
from atlas.alpha.issuer_equity.claims import ClaimStatus, FiscalYear, compose_senior_claims
from atlas.alpha.issuer_equity.composer import DenominatorQuality, IssuerCommonEquityMarketCap
from atlas.alpha.issuer_equity.reader import IssuerEquityReader
from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.valuation.contracts import ValuationDataGapKind
from atlas.analysis_engine.valuation.issuer_basis import (
    EpochDenominator,
    IssuerDenominatorQuality,
    IssuerMarketCap,
    IssuerValuationBasis,
    SeniorClaim,
)
from atlas.analysis_engine.valuation.models import FcfYieldEvidence

__all__ = ["IssuerValuationBasisBuilder"]

_QUALITY = {
    DenominatorQuality.ISSUER_EXACT: IssuerDenominatorQuality.EXACT,
    DenominatorQuality.ISSUER_EQUIVALENT: IssuerDenominatorQuality.EQUIVALENT,
    DenominatorQuality.ISSUER_BOUNDED: IssuerDenominatorQuality.BOUNDED,
}


def _record_id(fact_id: str) -> str:
    """Fact ids are `<record id>:<kind>:<period>`."""
    return fact_id.rsplit(":", 2)[0]


class IssuerValuationBasisBuilder:
    def __init__(self, reader: IssuerEquityReader) -> None:
        self._reader = reader

    @classmethod
    def from_engine(cls, engine: Engine) -> "IssuerValuationBasisBuilder":
        from atlas.alpha.canonical_security_gate.factory import build_listing_mic_reader

        return cls(IssuerEquityReader(engine, listing_mics=build_listing_mic_reader(engine)))

    def build(self, *, ticker: str, every_version: tuple[BusinessRecord, ...], records: tuple[BusinessRecord, ...],
              epochs: FcfYieldEvidence | None, historical: HistoricalMarketCapEvidence | None,
              evaluated_at: datetime) -> IssuerValuationBasis | None:
        """`records` are the latest versions the valuation reads; `epochs` its
        fiscal epochs (`fiscal_epochs_for_records`); `historical` their aligned
        market capitalisations. `None` when there is nothing to value."""
        if epochs is None or (epochs.current is None and not epochs.prior_epochs):
            return None
        reader = self._reader
        reader.prime(ticker, every_version)
        cik = reader.issuer_cik(ticker)
        if cik is None:
            return IssuerValuationBasis(current_gap=ValuationDataGapKind.DENOMINATOR_EVIDENCE_MISSING)
        evaluated_on = evaluated_at.date()

        current, current_gap = None, None
        if epochs.current is not None:
            current, current_gap = self._current(ticker, epochs, evaluated_on)

        aligned = {(e.fiscal_period, e.observed_on): e for e in (historical.epochs if historical else ())}
        denominators = []
        for epoch in epochs.prior_epochs:
            he = aligned.get((epoch.fiscal_period, epoch.observed_on))
            cap = self._prior(ticker, epoch, he, evaluated_on)
            denominators.append(EpochDenominator(epoch.fiscal_period, epoch.observed_on,
                                                 cap if isinstance(cap, IssuerMarketCap) else None,
                                                 cap if isinstance(cap, ValuationDataGapKind) else None))

        by_id = {r.id: r for r in records}
        years = {}
        for epoch in (*epochs.prior_epochs, *((epochs.current,) if epochs.current else ())):
            end = date.fromisoformat(epoch.fiscal_period)
            record = by_id.get(_record_id(epoch.free_cash_flow_fact_id))
            start = record.period_start if record is not None and record.period_start is not None else None
            years[epoch.fiscal_period] = FiscalYear(start if start and start <= end else end - timedelta(days=364), end)
        composed = compose_senior_claims(reader.rights(cik, evaluated_on), tuple(years.values()))
        claims, unquantified = [], []
        for period, year in sorted(years.items()):
            c = composed[year]
            if c.status is ClaimStatus.QUANTIFIED:
                claims.append(SeniorClaim(period, c.low, c.high, c.evidence))
            elif c.status is ClaimStatus.UNQUANTIFIED:
                unquantified.append(period)
        return IssuerValuationBasis(current=current, current_gap=current_gap, epochs=tuple(denominators),
                                    claims=tuple(claims), unquantified_claims=tuple(unquantified))

    def _current(self, ticker, epochs: FcfYieldEvidence, evaluated_on: date):
        on = date.fromisoformat(epochs.current.observed_on)
        composition = self._reader.on_date(ticker, on, evaluated_on)
        if composition is None:
            return None, ValuationDataGapKind.DENOMINATOR_EVIDENCE_MISSING
        if composition.quality not in _QUALITY:
            unpriced = {g.split(":", 1)[1] for g in composition.gaps if g.startswith("no_price:")}
            if unpriced - {ticker}:
                return None, ValuationDataGapKind.CURRENT_ISSUER_PRICE_NOT_SYNCHRONIZED
            if any(g.startswith(("price_currency_unproven:", "price_currency_mismatch")) for g in composition.gaps):
                return None, ValuationDataGapKind.CURRENT_ISSUER_PRICE_CURRENCY_UNPROVEN
            return None, ValuationDataGapKind.DENOMINATOR_EVIDENCE_MISSING
        own = self._reader.price_series(ticker).get(on)
        if own is None:
            return None, ValuationDataGapKind.DENOMINATOR_EVIDENCE_MISSING
        return self._market_cap(composition, own.price, epochs.current.currency), None

    def _prior(self, ticker, epoch, he, evaluated_on: date) -> IssuerMarketCap | ValuationDataGapKind:
        if he is None or he.quality not in ALIGNED_QUALITIES or not he.raw_close or not he.market_cap:
            return ValuationDataGapKind.DENOMINATOR_EVIDENCE_MISSING
        observed = date.fromisoformat(epoch.observed_on)
        if he.share_count_accession is None:
            # A single listing's issuer-level count is its whole common equity.
            return IssuerMarketCap(observed, he.raw_close, he.market_cap, he.market_cap, IssuerDenominatorQuality.EXACT,
                                   epoch.currency, tuple(i for i in (he.statement_record_id, he.price_record_id) if i))
        composition = self._reader.at_epoch(ticker, observed, he.share_count_accession,
                                            date.fromisoformat(epoch.fiscal_period), evaluated_on,
                                            factor=he.cumulative_factor or 1.0)
        if composition is None or composition.quality not in _QUALITY:
            return ValuationDataGapKind.DENOMINATOR_EVIDENCE_MISSING
        return self._market_cap(composition, he.raw_close, epoch.currency)

    @staticmethod
    def _market_cap(composition: IssuerCommonEquityMarketCap, price: float, currency: str) -> IssuerMarketCap:
        evidence = (f"count:{composition.count_accession}@{composition.count_instant.isoformat()}"
                    if composition.count_instant else f"count:{composition.count_accession}",)
        evidence += tuple(sorted({e for c in composition.contributions for e in c.evidence}))
        return IssuerMarketCap(composition.economic_date, price, composition.market_cap_low, composition.market_cap_high,
                               _QUALITY[composition.quality], currency, evidence)
