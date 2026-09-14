"""Aligned historical market capitalisation -- descriptive evidence only
(Aligned Historical Market Cap).

`fiscal_epoch_v2` prices each prior fiscal epoch as the split- and
dividend-adjusted close times *today's* share count
(`CURRENT_SHARE_COUNT_PROXY`). That proxy is what Atlas decides on, and it
stays so. This module reconstructs, beside it, what each epoch's market
capitalisation actually was -- the raw close times the period-end share
count *on the raw close's own share basis* -- wherever persisted evidence
can prove it, and withholds it everywhere else.

**Descriptive, never decision-facing.** The result lives on the
`InvestmentCaseComposition`, never on `CanonicalAnalysis`: valuation
position, status, ValuationRisk, Valuation Support, sensitivity,
recommendation, change intelligence and the Decision Layer never see it,
and `atlas.analysis_engine` cannot import it (architecture boundary). It
reads the decision's own epochs -- one construction, as
`historical_valuation.py` does -- and never adds an epoch, removes one or
mixes its values into them.

**The share basis, from Atlas's own evidence.** For one stored monthly bar,
`R = raw_close / adjusted_close` is every later split and dividend
adjustment. Between two adjacent stored observations the step
`R(earlier) / R(later)` is the adjustment accrued in between: dividend
drift alone stays within a few percent a year, a split moves it by the
split factor. On the persisted corpus every step is either within
0.99..1.042 or at least 3.0, nothing in between (`SMALL_STEP`,
`LARGE_STEP`). A large step is a *basis event*, known only to lie between
its two observations -- never dated more precisely than the evidence does.
Its factor is the step divided by the company's local dividend drift.

SEC share-count restatements narrow an event and give its exact factor:
when a later filing reports a period's count at the event factor times its
first report, the event lies between those two filings; when it reports the
same count, the event lies outside them.

**Aligning a count.** A period-end count is on the share basis prevailing
when it was filed (every restatement in the corpus agrees; none
contradicts). Each basis event between the count's filing and the price
observation is reversed: divided out when the count was filed after the
event and the price observed before it, multiplied in for the opposite
order. An event whose order relative to either date cannot be proven --
including one that coincides with a date to the day -- withholds the epoch.
The share count is the first-reported one where Atlas holds its filing (the
count as known then); its later revisions are kept as provenance, never
substituted silently.

**Bounded mode.** Without the count's own filing date, the filing still lies
after the period end and no later than the company's most recent annual
filing Atlas holds. If no basis event can fall anywhere between the price
observation and that whole interval, the count and the price share one
basis whatever the true filing date was: `FULLY_ALIGNED_BOUNDED`, never
called exact. The count used is then the latest reported one.

**Scope.** A share count that belongs to an issuer with more than one listed
security (`shared_issuer`), or a foreign filer's, is never multiplied by
one security's price: `SECURITY_SCOPE_UNSAFE`.

**Security-level counts** (Security-Level Share-Class Evidence v1). When
the Case's own security has class counts that annual filings link to its
trading symbol through a shared XBRL dimension
(`atlas.alpha.security_share_evidence`), those -- and only those -- are
the Case's share counts (`ShareCountScope.SECURITY`): one source per Case,
never mixed with the issuer-level count, which for a multi-class issuer
spans securities the price does not. They align by exactly the same rules:
first-reported where its filing is known, restatements narrowing basis
events. A shared issuer's epoch with no security-level count stays
`SECURITY_SCOPE_UNSAFE`; a foreign filer stays unsafe whatever it links.
Only observations filed by the Case's evaluation date are read. The result
is that one security's market capitalisation -- the scope the decision's
own proxy already has (the provider's per-listing share count) -- never an
issuer total: no class is ever added to or allocated from another.

Pure and deterministic: identical records give identical evidence, in any
order; conflicting duplicates withhold rather than choose.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from enum import Enum
from math import prod

from atlas.alpha.security_share_evidence.models import SecurityShareCountObservation, ShareClassLinkKind
from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.valuation.contracts import ValuationDecisionEligibility
from atlas.analysis_engine.valuation.facts import PriceBasis, market_price_provenance
from atlas.analysis_engine.valuation.models import FcfYieldEpochObservation, FcfYieldEvidence

__all__ = [
    "HISTORICAL_MARKET_CAP_METHODOLOGY",
    "SMALL_STEP",
    "LARGE_STEP",
    "RESTATEMENT_MATCH_TOLERANCE",
    "UNCHANGED_COUNT_TOLERANCE",
    "AlignmentGap",
    "AlignmentQuality",
    "BasisEvent",
    "BasisEventStatus",
    "EndpointKind",
    "FactorSource",
    "HistoricalMarketCapEpoch",
    "HistoricalMarketCapEvidence",
    "SecurityScope",
    "ShareCountScope",
    "ShareCountSource",
    "derive_basis_events",
    "reconstruct_historical_market_caps",
]

#: The descriptive construction's own identity. Not `FCF_YIELD_METHODOLOGY`:
#: `fiscal_epoch_v2` stays the decision-active method.
HISTORICAL_MARKET_CAP_METHODOLOGY = "raw_price_split_aligned_shares_v1"

#: A step inside this band is dividend drift (and price rounding). The
#: corpus's own maximum drift step is 1.042; its minimum 0.99999.
SMALL_STEP = (0.99, 1.06)
#: A step at least this large (or at most its inverse) is a discrete basis
#: event. Below the smallest conventional forward split (5:4 = 1.25); the
#: corpus's smallest such step is 3.0. Anything between the two bands is
#: ambiguous and withholds every epoch it could touch.
LARGE_STEP = 1.20
#: A restatement ratio names an event's factor within this relative
#: tolerance: reported counts are rounded to thousands or millions
#: (< 0.25% in the corpus) and a price-only factor carries one year's
#: dividend-drift uncertainty (< 1% in the corpus).
RESTATEMENT_MATCH_TOLERANCE = 0.02
#: A restatement ratio within this of 1 means "same share basis": rounding
#: moves counts by < 0.25%; genuine value corrections in the corpus are
#: 2.8% and more.
UNCHANGED_COUNT_TOLERANCE = 0.01
#: Dividend drift is estimated from this many nearest small steps.
_DRIFT_NEIGHBOURS = 4
_MONTHLY_ENDPOINT = "TIME_SERIES_MONTHLY_ADJUSTED"


class SecurityScope(str, Enum):
    SINGLE_SECURITY = "single_security"
    SHARED_ISSUER = "shared_issuer"
    FOREIGN_FILER = "foreign_filer"


class AlignmentQuality(str, Enum):
    #: The count's own filing is known and no basis event lies between it
    #: and the price observation.
    FULLY_ALIGNED = "fully_aligned"
    #: The count's own filing is known and every basis event between it and
    #: the price observation is located and reversed.
    BASIS_EVENT_REVERSED = "basis_event_reversed"
    #: Only bounds on the count's filing are known, and no basis event can
    #: lie between them and the price observation.
    FULLY_ALIGNED_BOUNDED = "fully_aligned_bounded"
    AMBIGUOUS = "ambiguous"
    INSUFFICIENT = "insufficient"
    SECURITY_SCOPE_UNSAFE = "security_scope_unsafe"


ALIGNED_QUALITIES = frozenset({
    AlignmentQuality.FULLY_ALIGNED,
    AlignmentQuality.BASIS_EVENT_REVERSED,
    AlignmentQuality.FULLY_ALIGNED_BOUNDED,
})


class AlignmentGap(str, Enum):
    MISSING_RAW_PRICE = "missing_raw_price"
    MISSING_PERIOD_SHARES = "missing_period_shares"
    #: No filing date for the count, and a basis event could lie inside the
    #: interval its filing is known to fall in.
    MISSING_SHARE_PROVENANCE = "missing_share_provenance"
    #: The stored observations do not cover the whole interval between the
    #: count's filing and the price observation.
    PRICE_HISTORY_DOES_NOT_SPAN = "price_history_does_not_span"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    #: A basis event's order relative to the count's filing or the price
    #: observation cannot be proven (it coincides with one of them).
    EVENT_AT_WINDOW_BOUNDARY = "event_at_window_boundary"
    #: A basis event's interval straddles the count's filing or the price.
    EVENT_STRADDLES_WINDOW = "event_straddles_window"
    AMBIGUOUS_STEP = "ambiguous_step"
    CONTRADICTED_EVENT = "contradicted_event"
    SHARED_ISSUER = "shared_issuer"
    FOREIGN_FILER = "foreign_filer"


class ShareCountSource(str, Enum):
    FIRST_REPORTED = "first_reported"
    LATEST_REPORTED = "latest_reported"


class ShareCountScope(str, Enum):
    #: The issuer-level period-end count on Atlas's stored SEC statement.
    ISSUER = "issuer"
    #: This security's own class count, linked to its trading symbol inside
    #: the filing that reports it (`PROVEN_BY_SHARED_DIMENSION`).
    SECURITY = "security"


class EndpointKind(str, Enum):
    #: A stored monthly close: the event is after (or on or before) that close.
    PRICE_OBSERVATION = "price_observation"
    #: A filing whose share basis is known from a restatement.
    FILING = "filing"


class FactorSource(str, Enum):
    PRICE_STEP = "price_step"
    SHARE_RESTATEMENT = "share_restatement"


class BasisEventStatus(str, Enum):
    LOCATED = "located"
    AMBIGUOUS = "ambiguous"
    CONTRADICTED = "contradicted"


@dataclass(frozen=True)
class BasisEvent:
    """A split-like change of share basis, known to lie strictly after
    `after` and on or before `on_or_before` -- never more precisely.
    `factor` > 1 is a forward split's shares-per-old-share."""

    after: date
    after_kind: EndpointKind
    on_or_before: date
    on_or_before_kind: EndpointKind
    step: float
    drift: float
    factor: float
    factor_source: FactorSource
    status: BasisEventStatus
    price_record_ids: tuple[str, str]
    statement_record_ids: tuple[str, ...] = ()

    @property
    def price_factor(self) -> float:
        """The factor from price evidence alone -- independent of any
        restatement, so the two can be compared."""
        return self.step / self.drift


@dataclass(frozen=True)
class HistoricalMarketCapEpoch:
    """One decision epoch's reconstructed market capitalisation, or the
    reason it is withheld. `proxy_market_cap` is the decision's own value
    for the same epoch, shown beside it -- never replaced by it."""

    fiscal_period: str
    observed_on: str
    quality: AlignmentQuality
    gaps: tuple[AlignmentGap, ...]
    currency: str
    free_cash_flow: float
    proxy_market_cap: float
    price_record_id: str | None = None
    raw_close: float | None = None
    adjusted_close: float | None = None
    statement_record_id: str | None = None
    share_count: float | None = None
    share_count_source: ShareCountSource | None = None
    share_count_filed: date | None = None
    share_count_filed_bounds: tuple[date, date] | None = None
    first_reported_share_count: float | None = None
    latest_reported_share_count: float | None = None
    basis_events: tuple[BasisEvent, ...] = ()
    cumulative_factor: float | None = None
    aligned_share_count: float | None = None
    market_cap: float | None = None
    #: The latest restatement of the same count, placed on the raw-price basis
    #: by the same rule (`None` when it is the first report, or not placeable).
    latest_reported_aligned_share_count: float | None = None
    latest_reported_basis_events: tuple[BasisEvent, ...] = ()
    #: Where the count came from. For `SECURITY`, the class member and the
    #: filings (first and latest report) whose own cover links it.
    share_count_scope: ShareCountScope = ShareCountScope.ISSUER
    share_count_class_member: str | None = None
    share_count_accession: str | None = None
    first_reported_share_count_accession: str | None = None
    latest_reported_share_count_accession: str | None = None

    @property
    def share_count_revision(self) -> float | None:
        """Latest restated count over the first report, both on the raw-price
        basis: 1.0 when a restatement only changed the split basis; any other
        value is an economic revision the first report did not know."""
        if self.aligned_share_count and self.latest_reported_aligned_share_count:
            return self.latest_reported_aligned_share_count / self.aligned_share_count
        return None

    @property
    def aligned_fcf_yield(self) -> float | None:
        """A reconstructed historical observation -- not the decision anchor."""
        return self.free_cash_flow / self.market_cap if self.market_cap else None


@dataclass(frozen=True)
class HistoricalMarketCapEvidence:
    methodology: str
    security_scope: SecurityScope
    epochs: tuple[HistoricalMarketCapEpoch, ...]
    basis_events: tuple[BasisEvent, ...]
    share_count_scope: ShareCountScope = ShareCountScope.ISSUER

    @property
    def aligned_epoch_count(self) -> int:
        return sum(e.quality in ALIGNED_QUALITIES for e in self.epochs)

    @property
    def exactly_aligned_epoch_count(self) -> int:
        return sum(e.quality in (AlignmentQuality.FULLY_ALIGNED, AlignmentQuality.BASIS_EVENT_REVERSED)
                   for e in self.epochs)


# -- evidence gathering ------------------------------------------------------------------------------------


@dataclass(frozen=True)
class _Price:
    on: date
    raw: float
    adjusted: float
    record_id: str


@dataclass(frozen=True)
class _Count:
    record_id: str
    period: date
    latest: float
    latest_filed: date | None
    first: float | None
    first_filed: date | None
    class_member: str | None = None
    first_accession: str | None = None
    latest_accession: str | None = None


def _day(value) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _prices(records: tuple[BusinessRecord, ...]) -> tuple[dict[date, _Price], frozenset[date], dict[str, _Price]]:
    """Every stored monthly bar with a recorded raw close, by date (and by
    record). Two different bars for one date are a conflict: the date is
    dropped."""
    by_day: dict[date, set[_Price]] = {}
    for record in records:
        if record.document_type is not SourceKind.MARKET_DATA_SNAPSHOT or _MONTHLY_ENDPOINT not in (record.source_reference or ""):
            continue
        p = market_price_provenance(record)
        if (p is None or not p.basis_recorded or p.basis is not PriceBasis.SPLIT_AND_DIVIDEND_ADJUSTED
                or p.raw_close is None or not p.share_price or p.raw_close <= 0 or p.share_price <= 0):
            continue
        on = _day(p.observed_on)
        if on is not None:
            by_day.setdefault(on, set()).add(_Price(on, p.raw_close, p.share_price, record.id))
    conflicts = frozenset(d for d, v in by_day.items() if len({(x.raw, x.adjusted) for x in v}) > 1)
    by_record = {x.record_id: x for v in by_day.values() for x in v}
    return ({d: min(v, key=lambda x: x.record_id) for d, v in by_day.items() if d not in conflicts},
            conflicts, by_record)


def _counts(records: tuple[BusinessRecord, ...]) -> dict[str, _Count | None]:
    """Period-end share counts with their SEC provenance, by record id;
    `None` marks a period whose statements disagree."""
    by_period: dict[date, set[_Count]] = {}
    for record in records:
        if record.document_type is not SourceKind.FINANCIAL_STATEMENT or record.period_end is None:
            continue
        m = record.metadata
        latest = m.get("shares_outstanding")
        if not isinstance(latest, (int, float)) or isinstance(latest, bool) or latest <= 0:
            continue
        first = m.get("shares_outstanding_first_reported")
        by_period.setdefault(record.period_end, set()).add(_Count(
            record_id=record.id, period=record.period_end, latest=float(latest),
            latest_filed=_day(m.get("shares_outstanding_filed")) if m.get("shares_outstanding_filed") else None,
            first=float(first) if isinstance(first, (int, float)) and not isinstance(first, bool) and first > 0 else None,
            first_filed=_day(m.get("shares_outstanding_first_reported_filed")) if m.get("shares_outstanding_first_reported_filed") else None,
        ))
    out: dict[str, _Count | None] = {}
    for period, counts in by_period.items():
        values = {(c.latest, c.latest_filed, c.first, c.first_filed) for c in counts}
        for c in counts:
            out[c.record_id] = c if len(values) == 1 else None
    return out


def _security_counts(
    observations: tuple[SecurityShareCountObservation, ...], as_of: date | None
) -> dict[date, _Count | None]:
    """The security's own class counts by period end: the first filing's
    report and the latest filing's (a restatement between them is basis
    evidence, as for issuer counts). `None` marks a period a filing
    reports in disagreeing values -- withheld, never chosen between. Each
    observation was linked inside its own filing; nothing here links."""
    by_period: dict[date, list[SecurityShareCountObservation]] = {}
    for o in observations:
        if o.link_kind is not ShareClassLinkKind.PROVEN_BY_SHARED_DIMENSION:
            continue  # only a link its own filing proves
        if as_of is not None and o.filing_date > as_of:
            continue  # not yet filed when the Case is evaluated
        if o.filing_date <= o.period_end:
            continue  # a period-end count cannot be filed by its period end
        by_period.setdefault(o.period_end, []).append(o)
    out: dict[date, _Count | None] = {}
    for period, reported in by_period.items():
        by_filing: dict[str, set[float | None]] = {}
        for o in reported:
            by_filing.setdefault(o.accession, set()).add(o.shares if o.usable else None)
        if any(len(values) > 1 or None in values for values in by_filing.values()):
            out[period] = None
            continue
        ordered = sorted(reported, key=lambda o: (o.filing_date, o.accession))
        first, latest = ordered[0], ordered[-1]
        out[period] = _Count(
            record_id=f"{first.issuer_cik}/{first.cover_symbol}/{period.isoformat()}", period=period,
            latest=float(latest.shares), latest_filed=latest.filing_date,
            first=float(first.shares), first_filed=first.filing_date,
            class_member=latest.class_member, first_accession=first.accession, latest_accession=latest.accession,
        )
    return out


def _step_class(step: float) -> str:
    if SMALL_STEP[0] <= step <= SMALL_STEP[1]:
        return "small"
    if step >= LARGE_STEP or step <= 1 / LARGE_STEP:
        return "large"
    return "ambiguous"


def derive_basis_events(records: tuple[BusinessRecord, ...]) -> tuple[BasisEvent, ...]:
    """Every non-dividend step in the company's stored raw/adjusted history,
    located as narrowly as the evidence allows."""
    prices, _, _ = _prices(records)
    return _events(prices, tuple(c for c in _counts(records).values() if c is not None))


def _events(prices: dict[date, _Price], counts: tuple[_Count, ...]) -> tuple[BasisEvent, ...]:
    series = [prices[d] for d in sorted(prices)]
    steps = [(a, b, (a.raw / a.adjusted) / (b.raw / b.adjusted)) for a, b in zip(series, series[1:])]
    small = [(i, s) for i, (_, _, s) in enumerate(steps) if _step_class(s) == "small"]
    events: list[BasisEvent] = []
    for i, (a, b, step) in enumerate(steps):
        kind = _step_class(step)
        if kind == "small":
            continue
        near = sorted(small, key=lambda x: (abs(x[0] - i), x[0]))[:_DRIFT_NEIGHBOURS]
        drifts = sorted(s for _, s in near)
        drift = drifts[len(drifts) // 2] if drifts else 1.0
        event = BasisEvent(
            after=a.on, after_kind=EndpointKind.PRICE_OBSERVATION, on_or_before=b.on,
            on_or_before_kind=EndpointKind.PRICE_OBSERVATION, step=step, drift=drift, factor=step / drift,
            factor_source=FactorSource.PRICE_STEP,
            status=BasisEventStatus.LOCATED if kind == "large" else BasisEventStatus.AMBIGUOUS,
            price_record_ids=(a.record_id, b.record_id),
        )
        events.append(_narrow(event, counts) if kind == "large" else event)
    return tuple(events)


def _narrow(event: BasisEvent, counts: tuple[_Count, ...]) -> BasisEvent:
    """Restatements of one period's count between two filings: a ratio at the
    event factor puts the event between them; an unchanged count, outside."""
    after, after_kind = event.after, event.after_kind
    before, before_kind = event.on_or_before, event.on_or_before_kind
    factor, source, supporting = event.factor, event.factor_source, []
    status = event.status
    for c in sorted(counts, key=lambda c: (c.period, c.record_id)):
        if c.first is None or c.first_filed is None or c.latest_filed is None or c.first_filed >= c.latest_filed:
            continue
        a, b, ratio = c.first_filed, c.latest_filed, c.latest / c.first
        if not (after < b and a < before):
            continue
        if abs(ratio / factor - 1) <= RESTATEMENT_MATCH_TOLERANCE:
            if a > after or (a == after and after_kind is EndpointKind.PRICE_OBSERVATION):
                after, after_kind = a, EndpointKind.FILING
            if b < before or (b == before and before_kind is EndpointKind.PRICE_OBSERVATION):
                before, before_kind = b, EndpointKind.FILING
            factor, source = ratio, FactorSource.SHARE_RESTATEMENT
            supporting.append(c.record_id)
        elif abs(ratio - 1) <= UNCHANGED_COUNT_TOLERANCE:
            supporting.append(c.record_id)
            if a <= after and b >= before:
                status = BasisEventStatus.CONTRADICTED
            elif a <= after < b:
                after, after_kind = b, EndpointKind.FILING
            elif a < before <= b:
                before, before_kind = a, EndpointKind.FILING
    if after >= before:
        status = BasisEventStatus.CONTRADICTED
    return BasisEvent(after, after_kind, before, before_kind, event.step, event.drift, factor, source, status,
                      event.price_record_ids, tuple(supporting))


# -- ordering -----------------------------------------------------------------------------------------------

_BEFORE, _AFTER, _UNKNOWN = "before", "after", "unknown"


def _versus_price(e: BasisEvent, on: date) -> str:
    """Is the event before or after the close on `on` (itself a stored observation)?"""
    if e.on_or_before <= on:
        return _BEFORE
    if e.after > on or (e.after == on and e.after_kind is EndpointKind.PRICE_OBSERVATION):
        return _AFTER
    return _UNKNOWN


def _versus_filing(e: BasisEvent, filed: date) -> str:
    """Is the event reflected in a filing dated `filed`?"""
    if e.on_or_before < filed or (e.on_or_before == filed and e.on_or_before_kind is EndpointKind.FILING):
        return _BEFORE
    if e.after >= filed:
        return _AFTER
    return _UNKNOWN


def _unordered_gap(e: BasisEvent, unordered: tuple[date, ...]) -> AlignmentGap:
    """`unordered`: the dates the event could not be ordered against."""
    return (AlignmentGap.EVENT_AT_WINDOW_BOUNDARY if {e.after, e.on_or_before} & set(unordered)
            else AlignmentGap.EVENT_STRADDLES_WINDOW)


def _status_gap(e: BasisEvent) -> AlignmentGap | None:
    return {BasisEventStatus.AMBIGUOUS: AlignmentGap.AMBIGUOUS_STEP,
            BasisEventStatus.CONTRADICTED: AlignmentGap.CONTRADICTED_EVENT}.get(e.status)


# -- alignment ----------------------------------------------------------------------------------------------


def _record_id_of(fact_id: str) -> str:
    """Fact ids are `<record id>:<kind>:<period>`."""
    return fact_id.rsplit(":", 2)[0]


def reconstruct_historical_market_caps(
    evidence: FcfYieldEvidence | None,
    business_records: tuple[BusinessRecord, ...],
    *,
    shared_issuer: bool,
    security_share_counts: tuple[SecurityShareCountObservation, ...] = (),
    as_of: date | None = None,
) -> HistoricalMarketCapEvidence | None:
    """`business_records` are the Case's latest versions (the same ones the
    decision read). `security_share_counts` are the proven class-count
    observations joined to this Case's own security (by CIK, symbol and
    MIC -- see `security_share_evidence.repository`); only those filed by
    `as_of` are read. `None` when the FCF-yield method formed no evidence
    or does not apply (banks, dealers, insurers) -- nothing to describe."""
    if evidence is None or evidence.eligibility is ValuationDecisionEligibility.NOT_APPLICABLE:
        return None
    forms = {r.metadata.get("sec_form") for r in business_records
             if r.document_type is SourceKind.FINANCIAL_STATEMENT and r.metadata.get("sec_form")}
    scope = (SecurityScope.SHARED_ISSUER if shared_issuer
             else SecurityScope.FOREIGN_FILER if forms - {"10-K"} else SecurityScope.SINGLE_SECURITY)
    prices, conflicts, price_by_record = _prices(business_records)
    security_counts = _security_counts(security_share_counts, as_of)
    share_scope = ShareCountScope.SECURITY if security_counts else ShareCountScope.ISSUER
    counts = _counts(business_records) if share_scope is ShareCountScope.ISSUER else {}
    period_counts = security_counts if share_scope is ShareCountScope.SECURITY else counts
    events = _events(prices, tuple(c for c in period_counts.values() if c is not None))
    statements = {r.id: r for r in business_records if r.document_type is SourceKind.FINANCIAL_STATEMENT}
    latest_annual_filing = max(
        (d for r in statements.values() if (d := _day(r.published_at)) is not None), default=None
    )
    span = (min(prices), max(prices)) if prices else None
    epochs = tuple(
        _align_epoch(epoch, scope, share_scope, price_by_record, conflicts, counts, security_counts, statements,
                     events, latest_annual_filing, span)
        for epoch in evidence.prior_epochs
    )
    return HistoricalMarketCapEvidence(HISTORICAL_MARKET_CAP_METHODOLOGY, scope, epochs, events, share_scope)


def _align_epoch(epoch: FcfYieldEpochObservation, scope, share_scope, price_by_record, conflicts, counts,
                 security_counts, statements, events, latest_annual_filing, span) -> HistoricalMarketCapEpoch:
    base = dict(fiscal_period=epoch.fiscal_period, observed_on=epoch.observed_on, currency=epoch.currency,
                free_cash_flow=epoch.free_cash_flow, proxy_market_cap=epoch.market_cap_proxy,
                share_count_scope=share_scope)

    def withheld(quality, *gaps, **known):
        return HistoricalMarketCapEpoch(quality=quality, gaps=tuple(gaps), **base, **known)

    period = _day(epoch.fiscal_period)
    if scope is SecurityScope.FOREIGN_FILER:
        return withheld(AlignmentQuality.SECURITY_SCOPE_UNSAFE, AlignmentGap.FOREIGN_FILER)
    if scope is SecurityScope.SHARED_ISSUER and (share_scope is ShareCountScope.ISSUER or period not in security_counts):
        # The issuer's count spans securities this price does not; without
        # this security's own count for the period there is nothing to use.
        return withheld(AlignmentQuality.SECURITY_SCOPE_UNSAFE, AlignmentGap.SHARED_ISSUER)

    on = _day(epoch.observed_on)
    price = price_by_record.get(_record_id_of(epoch.share_price_fact_id))
    statement_id = _record_id_of(epoch.free_cash_flow_fact_id)
    if share_scope is ShareCountScope.SECURITY:
        count, conflicted = security_counts.get(period), period in security_counts and security_counts[period] is None
    else:
        count, conflicted = counts.get(statement_id), statement_id in counts and counts[statement_id] is None
    if on in conflicts or conflicted:
        return withheld(AlignmentQuality.AMBIGUOUS, AlignmentGap.CONFLICTING_EVIDENCE)
    known = dict(statement_record_id=statement_id if statement_id in statements else None)
    if count is not None and count.class_member is not None:
        known.update(share_count_class_member=count.class_member,
                     first_reported_share_count_accession=count.first_accession,
                     latest_reported_share_count_accession=count.latest_accession)
    missing = []
    if price is None or price.on != on:
        missing.append(AlignmentGap.MISSING_RAW_PRICE)
    else:
        known.update(price_record_id=price.record_id, raw_close=price.raw, adjusted_close=price.adjusted)
    if count is None:
        missing.append(AlignmentGap.MISSING_PERIOD_SHARES)
    else:
        known.update(first_reported_share_count=count.first, latest_reported_share_count=count.latest)
    if missing:
        return withheld(AlignmentQuality.INSUFFICIENT, *missing, **known)

    first = latest = None
    if count.first is not None and count.first_filed is not None:
        first = _align_exact(epoch, on, count.first, ShareCountSource.FIRST_REPORTED, count.first_filed,
                             events, span, base, dict(known, share_count_accession=count.first_accession))
    if count.latest_filed is not None and (first is None or count.latest_filed != count.first_filed):
        latest = _align_exact(epoch, on, count.latest, ShareCountSource.LATEST_REPORTED, count.latest_filed,
                              events, span, base, dict(known, share_count_accession=count.latest_accession))
    if first is None and latest is None:
        return _align_bounded(on, count, latest_annual_filing, events, span, base, known)
    if first is not None and (first.quality in ALIGNED_QUALITIES or latest is None
                              or latest.quality not in ALIGNED_QUALITIES):
        if latest is None:
            return first
        # The later restatement, placed on the same basis by the same rule:
        # agreement confirms the basis; a difference is an economic revision
        # the first report did not know -- kept beside it, never substituted.
        return replace(first, latest_reported_aligned_share_count=latest.aligned_share_count,
                       latest_reported_basis_events=latest.basis_events)
    # The first report cannot be placed, its later restatement can: used, and
    # labelled as the latest report (it may carry later economic revisions).
    return latest


def _spans(span, *dates: date) -> bool:
    return span is not None and span[0] <= min(dates) and max(dates) <= span[1]


def _align_exact(epoch, on, shares, source, filed, events, span, base, known) -> HistoricalMarketCapEpoch:
    known.update(share_count=shares, share_count_source=source, share_count_filed=filed)
    if not _spans(span, on, filed):
        return HistoricalMarketCapEpoch(quality=AlignmentQuality.INSUFFICIENT,
                                        gaps=(AlignmentGap.PRICE_HISTORY_DOES_NOT_SPAN,), **base, **known)
    applied: list[tuple[BasisEvent, int]] = []
    for e in events:
        at_price, at_filing = _versus_price(e, on), _versus_filing(e, filed)
        if at_price == at_filing != _UNKNOWN:
            continue
        unordered = tuple(d for d, at in ((on, at_price), (filed, at_filing)) if at == _UNKNOWN)
        gap = _status_gap(e) or (_unordered_gap(e, unordered) if unordered else None)
        if gap is not None:
            return HistoricalMarketCapEpoch(quality=AlignmentQuality.AMBIGUOUS, gaps=(gap,), **base, **known)
        # filed after the event, priced before it: the count is on the later basis -> divide.
        applied.append((e, -1 if at_filing == _BEFORE else 1))
    cumulative = prod(e.factor ** sign for e, sign in applied) if applied else 1.0
    aligned = shares * cumulative
    return HistoricalMarketCapEpoch(
        quality=AlignmentQuality.BASIS_EVENT_REVERSED if applied else AlignmentQuality.FULLY_ALIGNED,
        gaps=(), **base, **known, basis_events=tuple(e for e, _ in applied), cumulative_factor=cumulative,
        aligned_share_count=aligned, market_cap=known["raw_close"] * aligned,
    )


def _align_bounded(on, count: _Count, latest_annual_filing, events, span, base, known) -> HistoricalMarketCapEpoch:
    lower, upper = count.period, latest_annual_filing
    known.update(share_count=count.latest, share_count_source=ShareCountSource.LATEST_REPORTED,
                 share_count_filed_bounds=(lower, upper) if upper else None)
    if upper is None or not _spans(span, on, lower, upper):
        return HistoricalMarketCapEpoch(quality=AlignmentQuality.INSUFFICIENT,
                                        gaps=(AlignmentGap.PRICE_HISTORY_DOES_NOT_SPAN,), **base, **known)
    for e in events:
        at_price = _versus_price(e, on)
        # the count's filing is after the period end and no later than `upper`.
        before_every_filing = e.on_or_before <= lower
        after_every_filing = e.after >= upper
        if (at_price == _BEFORE and before_every_filing) or (at_price == _AFTER and after_every_filing):
            continue
        gap = _status_gap(e)
        return HistoricalMarketCapEpoch(
            quality=AlignmentQuality.AMBIGUOUS if gap else AlignmentQuality.INSUFFICIENT,
            gaps=(gap or AlignmentGap.MISSING_SHARE_PROVENANCE,), **base, **known)
    return HistoricalMarketCapEpoch(
        quality=AlignmentQuality.FULLY_ALIGNED_BOUNDED, gaps=(), **base, **known, cumulative_factor=1.0,
        aligned_share_count=count.latest, market_cap=known["raw_close"] * count.latest,
    )
