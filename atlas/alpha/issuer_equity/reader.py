"""Inputs for the issuer common-equity composer, from persisted evidence --
read-only, on demand (nothing in Case composition calls it).

**Count sets.** Class counts come from Atlas's share evidence: each current
filing's cover counts (dated by their own instant) and each annual filing's
period-end class counts. A set is one filing at one instant -- never mixed.
A class is "listed" only where that filing's own cover proves it is an
Atlas listing (symbol and MIC); every other class, including a linked-but-
unlisted one, must be priced through rights evidence.

**Prices.** A security's raw price by date: a current quote as traded, a
monthly bar's recorded raw close -- never an adjusted close. Two records
disagreeing for one date drop the date.

**The current economic date** is the latest date, on or before the
evaluation date, on which the Case's own security and every listed sibling
class of the chosen count set all have a price; the count set is the latest
one dated by that date and filed by the evaluation date (what Atlas knows
when it evaluates). No sibling price is ever taken from another day, and a
count is never multiplied by a price across a share-basis change: a stored
price step, or a later count a split-sized factor away, withholds the pair.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date

from sqlalchemy.engine import Engine

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.class_rights_evidence.repository import SqlAlchemyClassRightsEvidenceRepository
from atlas.alpha.investment_case.historical_market_cap import LARGE_STEP, derive_basis_events
from atlas.alpha.issuer_equity.composer import (
    ClassCount,
    IssuerCommonEquityMarketCap,
    ListedPrice,
    _sums_of_others,
    compose_issuer_common_equity_market_cap,
)
from atlas.alpha.security_share_evidence.models import ShareClassLinkKind
from atlas.alpha.security_share_evidence.repository import ListingMics, SqlAlchemySecurityShareEvidenceRepository
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.business_data.versioning import latest_versions
from atlas.analysis_engine.valuation.facts import PriceBasis, market_price_provenance

__all__ = ["CountSet", "IssuerEquityReader"]

_PROVEN = ShareClassLinkKind.PROVEN_BY_SHARED_DIMENSION
_MAX_DATES = 60


def _total(count_set: "CountSet") -> float:
    """The set's total common shares: its issuer-level count, or the sum of
    its classes without aggregate members."""
    level = [c for c in count_set.counts if c.member is not None]
    if not level:
        return sum(c.shares for c in count_set.counts)
    aggregates = _sums_of_others(level)
    return sum(c.shares for c in level if c.member not in aggregates)


def _same_basis(a: float, b: float) -> bool:
    """Two totals on one share basis: a later count a split-sized step away
    means a basis change lies after the earlier count."""
    return a > 0 and b > 0 and 1 / LARGE_STEP < b / a < LARGE_STEP


class CountSet:
    def __init__(self, instant: date, filing_date: date, accession: str, counts: tuple[ClassCount, ...],
                 classes_reported: bool) -> None:
        self.instant, self.filing_date, self.accession = instant, filing_date, accession
        self.counts, self.classes_reported = counts, classes_reported


class IssuerEquityReader:
    def __init__(self, engine: Engine, *, listing_mics: ListingMics | None) -> None:
        self._shares = SqlAlchemySecurityShareEvidenceRepository(engine, listing_mics=listing_mics)
        self._rights = SqlAlchemyClassRightsEvidenceRepository(engine)
        self._records = SqlAlchemyBusinessRecordRepository(engine)
        self._listing_mics = listing_mics

    # -- identity ------------------------------------------------------------------------------------------

    def issuer_cik(self, ticker: str) -> str | None:
        ciks = {f"{int(r.metadata['sec_cik']):010d}" for r in self._records.get_by_company(ticker)
                if r.document_type is SourceKind.FINANCIAL_STATEMENT and str(r.metadata.get("sec_cik") or "").isdigit()}
        return ciks.pop() if len(ciks) == 1 else None

    def _listed(self, symbol: str | None, mic: str | None) -> str | None:
        if not symbol or not mic or self._listing_mics is None:
            return None
        return symbol if mic in self._listing_mics((symbol,)).get(symbol, frozenset()) else None

    # -- prices --------------------------------------------------------------------------------------------

    def price_series(self, symbol: str) -> dict[date, ListedPrice]:
        by_day: dict[date, set[ListedPrice]] = {}
        for record in latest_versions(self._records.get_by_company(symbol)):
            p = market_price_provenance(record)
            if p is None:
                continue
            raw = (p.share_price if p.basis is PriceBasis.RAW
                   else p.raw_close if p.basis is PriceBasis.SPLIT_AND_DIVIDEND_ADJUSTED else None)
            if not raw or raw <= 0:
                continue
            on = date.fromisoformat(str(p.observed_on)[:10])
            by_day.setdefault(on, set()).add(ListedPrice(symbol, on, float(raw), record.id))
        return {d: min(v, key=lambda x: x.record_id) for d, v in by_day.items() if len({x.price for x in v}) == 1}

    # -- counts --------------------------------------------------------------------------------------------

    def count_sets(self, issuer_cik: str) -> list[CountSet]:
        sets: dict[tuple[str, date], list[ClassCount]] = {}
        filed: dict[tuple[str, date], date] = {}
        for o in self._shares.current_evidence_for_issuers(frozenset({issuer_cik})).get(issuer_cik, ()):
            if o.conflict or o.shares is None:
                continue
            symbol = self._listed(o.cover_symbol, o.cover_mic) if o.link_kind is _PROVEN else None
            key = (o.accession, o.as_of)
            sets.setdefault(key, []).append(ClassCount(o.class_member, o.shares, o.as_of, o.accession, o.filing_date,
                                                       symbol, o.cover_mic if symbol else None))
            filed[key] = o.filing_date
        for o in self._shares.observations_for_issuer(issuer_cik):
            if o.conflict or o.shares is None:
                continue
            symbol = self._listed(o.cover_symbol, o.cover_mic) if o.link_kind is _PROVEN else None
            key = (o.accession, o.period_end)
            sets.setdefault(key, []).append(ClassCount(o.class_member, o.shares, o.period_end, o.accession,
                                                       o.filing_date, symbol, o.cover_mic if symbol else None))
            filed[key] = o.filing_date
        flags = self._shares.current_classes_reported(tuple(sorted({a for a, _ in sets})))
        out = []
        for (accession, instant), counts in sets.items():
            class_level = tuple(c for c in counts if c.member is not None)
            chosen = class_level or tuple(counts)
            out.append(CountSet(instant, filed[(accession, instant)], accession, tuple(sorted(chosen, key=lambda c: c.member or "")),
                                flags.get(accession, bool(class_level))))
        return sorted(out, key=lambda s: (s.instant, s.filing_date, s.accession))

    # -- compositions --------------------------------------------------------------------------------------

    def _compose(self, cik, on, chosen: CountSet, sets, case_symbol, prices, rights, factor=1.0):
        counts = tuple(ClassCount(c.member, c.shares * factor, c.as_of, c.accession, c.filing_date, c.symbol, c.mic)
                       for c in chosen.counts)
        breakdown = ()
        if all(c.member is None for c in counts):
            earlier = [s for s in sets if s.instant <= chosen.instant and any(c.member for c in s.counts)]
            if earlier:
                latest = earlier[-1]
                breakdown = tuple((c.member, c.shares, c.as_of) for c in latest.counts if c.member)
        return compose_issuer_common_equity_market_cap(
            cik, on, counts, prices, rights, case_symbol=case_symbol, classes_reported=chosen.classes_reported,
            class_breakdown=breakdown)

    def _basis_events(self, ticker: str):
        return derive_basis_events(latest_versions(self._records.get_by_company(ticker)))

    def current(self, ticker: str, evaluated_on: date) -> IssuerCommonEquityMarketCap | None:
        cik = self.issuer_cik(ticker)
        if cik is None:
            return None
        sets = self.count_sets(cik)
        rights = self._rights.observations_for_issuers(frozenset({cik}), filed_by=evaluated_on)[cik]
        own = self.price_series(ticker)
        series: dict[str, dict[date, ListedPrice]] = {ticker: own}
        first = None
        events = None
        for on in sorted((d for d in own if d <= evaluated_on), reverse=True)[:_MAX_DATES]:
            usable = [s for s in sets if s.instant <= on and s.filing_date <= evaluated_on]
            if not usable:
                continue
            chosen = usable[-1]
            if events is None:
                events = self._basis_events(ticker)
            later = [s for s in sets if s.instant > chosen.instant and s.filing_date <= evaluated_on]
            if (any(e.after < on and e.on_or_before > chosen.instant for e in events)
                    or any(not _same_basis(_total(chosen), _total(s)) for s in later)):
                # A share-basis change may lie between the count and the price:
                # never multiplied together.
                composed = compose_issuer_common_equity_market_cap(
                    cik, on, (), {}, (), case_symbol=ticker)
                composed = replace(composed, count_instant=chosen.instant, count_accession=chosen.accession,
                                   gaps=("share_basis_change_between_count_and_price",))
                first = first or composed
                continue
            symbols = {c.symbol for c in chosen.counts if c.symbol and c.shares > 0} | {ticker}
            for symbol in symbols - set(series):
                series[symbol] = self.price_series(symbol)
            prices = {s: series[s][on] for s in symbols if on in series[s]}
            composed = self._compose(cik, on, chosen, sets, ticker, prices, rights)
            first = first or composed
            if len(prices) == len(symbols):
                return composed
        return first

    def at_epoch(self, ticker: str, observed_on: date, count_accession: str, period_end: date, evaluated_on: date,
                 *, factor: float = 1.0) -> IssuerCommonEquityMarketCap | None:
        """One historical epoch: the count set is the class counts the Case's
        own aligned count came from (same filing, same period end), on the
        epoch's own basis factor; every listed class priced on the epoch's own date."""
        cik = self.issuer_cik(ticker)
        if cik is None:
            return None
        sets = self.count_sets(cik)
        chosen = next((s for s in sets if s.accession == count_accession and s.instant == period_end), None)
        if chosen is None:
            return None
        rights = self._rights.observations_for_issuers(frozenset({cik}), filed_by=evaluated_on)[cik]
        symbols = {c.symbol for c in chosen.counts if c.symbol and c.shares > 0} | {ticker}
        prices = {s: p for s in symbols if (p := self.price_series(s).get(observed_on)) is not None}
        return self._compose(cik, observed_on, chosen, sets, ticker, prices, rights, factor)
