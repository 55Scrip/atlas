"""FCF Yield evaluator (ATLAS-024; temporal alignment ATLAS-032; fiscal
epochs in Valuation Observation Integrity) -- Atlas's one real Valuation
method: today's free cash flow yield against the same company's own yields
in earlier fiscal years. Chosen over P/E, EV/EBITDA or a DCF because it
needs the fewest unsupported assumptions: free cash flow is already a
`BusinessFact`, and a share price and share count are the minimum needed to
form a market capitalisation.

**The comparison itself is unchanged.** Current yield strictly above every
prior yield -> `UNDERVALUED`; strictly below every one -> `EXPENSIVE`;
otherwise `FAIRLY_VALUED`. No universal yield level appears anywhere: cheap
and expensive are always relative to the company's own history. What this
module changed is *which* observations are compared, and when the
comparison may decide anything.

**1. Eligible free cash flow.** Only facts from annual financial statements
(`statement_record_ids`) for periods that have ended by `evaluated_at` --
the same two source gates as Financial Risk v2. A verification record, an
annual-report estimate or a future fiscal year is excluded and named in
`FcfYieldEvidence.excluded`. Two eligible facts for one period is an
ambiguity and drops that period rather than choosing.

**2. When a fiscal year became known.** A statement record's `published_at`
is the filing that last carried it -- for a comparative figure, a 10-K two
years later. Pairing on that date made a 2018 price meet 2016 cash flow.
Instead, a fiscal year's figures are *available from* the earliest annual
statement filing Atlas holds that is dated after that fiscal year ended.
Annual reports are filed once a year, after the year closes, and each
carries the latest year it reports, so the first filing after a period end
is that year's own report whenever Atlas holds it (every filing date comes
from Atlas's own statement records -- never inferred from the period end).
If that report is missing, the next filing is later still: availability
can arrive late, never early. On the persisted corpus every availability
falls 24-107 days after its period end. Restated comparatives are used at
their restated value -- a disclosed limitation.

**3. Fiscal epochs.** A market observation belongs to the latest fiscal
year available on its own date (no look-ahead by construction: a fiscal
year is never paired with a price from before it was public). All
observations of one fiscal year form one epoch and count once, however
often the price was refreshed:

- the **current** observation is the latest market observation, priced
  against the fiscal year it belongs to -- the newest fundamentals known
  today, never a stale one borrowed from an older filing;
- each **prior** epoch is represented by its earliest observation: the
  market's first price after that year's figures were published -- the
  same "first close on or after the filing" the market-data backfill
  samples. Because it is the first, a later refresh can never replace or
  add to it. A prior observation must also be taken within 52 weeks of its
  fiscal year end -- the shortest fiscal year -- so it can never be a
  price from after the following year closed, even where Atlas is missing
  that year's report;
- the current fiscal year never appears in its own history.

**4. Decision eligibility.** At least `MINIMUM_PRIOR_EPOCHS` prior fiscal
epochs before the comparison may classify (`ELIGIBLE`). With fewer, the
position against the prior epochs is still described (`LIMITED`), but
`status` stays `INSUFFICIENT_INPUT` -- thin history is never allowed to
look like a real `FAIRLY_VALUED`, `UNDERVALUED` or `EXPENSIVE`. On the
corrected corpus every gate from two to four prior epochs selects exactly
the same Cases; three sits in the middle of that stable range. This is a
policy, not a statistical truth.

**5. Applicability.** Banks, dealers and insurers get `NOT_APPLICABLE`
(`valuation.applicability`), never a yield.

**6. The issuer basis (fiscal_epoch_v3).** The epochs above are method-
independent; what each is priced on is not. In production every epoch is
priced on the issuer basis (`issuer_basis`): the issuer's common-equity
market capitalisation on the observation's own date (raw prices, period
share counts aligned to the raw price's share basis, multi-class issuers
composed class by class, same-date sibling prices) over the free cash flow
attributable to common equity (OCF − capex, less the contractual claims of
senior non-participating preferred accrued over the fiscal year). Atlas's
free cash flow is levered cash flow to all equity claimants -- after interest,
before preferred dividends and distributions to noncontrolling interests --
never FCFE. Noncontrolling interests are unmeasured: a disclosed limitation,
never assumed to be zero. An epoch the basis cannot price is left out; a
current observation it cannot price (no composition on the Case's own date, a
stale sibling price, an unquantified claim, bounds that disagree) withholds
the valuation with its reason. There is no fallback: `fiscal_epoch_v2`'s
provider proxy (adjusted price times today's provider share count,
`ShareCountMethod.CURRENT_SHARE_COUNT_PROXY`) is kept only as
`evaluate_fcf_yield_relative_v2`, to interpret history persisted under it and
for migration comparisons.

A mismatch between the free cash flow currency and the share price currency
(an ADR over foreign-currency statements) forms no observation: dividing
one by the other would mix an exchange rate into the yield.

**Staleness.** No wall-clock threshold for "too old to be current" is owned
anywhere in this codebase, so none is invented here;
`ValuationDataGapKind.STALE_MARKET_DATA` stays reserved.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from datetime import date, datetime

from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.valuation.applicability import fcf_yield_applies
from atlas.analysis_engine.valuation.contracts import (
    ShareCountMethod,
    ValuationDataGapKind,
    ValuationDecisionEligibility,
    ValuationFactExclusionReason,
    ValuationMethodKind,
    severity_for_valuation_status,
)
from atlas.analysis_engine.valuation.facts import ValuationFact, ValuationFactKind
from atlas.analysis_engine.valuation.issuer_basis import (
    COMMON_FCF_NUMERATOR_METHODOLOGY,
    ISSUER_MARKET_CAP_METHODOLOGY,
    NCI_TREATMENT,
    IssuerMarketCap,
    IssuerValuationBasis,
    SeniorClaim,
)
from atlas.analysis_engine.valuation.models import (
    FcfYieldEpochObservation,
    FcfYieldEvidence,
    FcfYieldExclusion,
    ValuationFinding,
    position_of,
)
from atlas.decision_engine.contracts import EvidenceCoverageLevel

__all__ = [
    "FCF_YIELD_METHODOLOGY",
    "FISCAL_EPOCH_V2",
    "MINIMUM_PRIOR_EPOCHS",
    "SHARE_COUNT_METHOD",
    "VALUATION_METHODOLOGY",
    "evaluate_fcf_yield_relative",
    "evaluate_fcf_yield_relative_v2",
    "fiscal_epochs",
]

#: The fiscal-epoch construction in production.
FCF_YIELD_METHODOLOGY = "fiscal_epoch_v3"
#: The retired provider-proxy construction: history persisted under it keeps
#: this identity and is never compared with v3 on valuation.
FISCAL_EPOCH_V2 = "fiscal_epoch_v2"

#: What "the same valuation measurement" means to change intelligence and the
#: Decision Layer: the epoch construction with the denominator and numerator
#: it composes -- any one of them changing is a new ruler, never company news.
VALUATION_METHODOLOGY = f"{FCF_YIELD_METHODOLOGY}+{ISSUER_MARKET_CAP_METHODOLOGY}+{COMMON_FCF_NUMERATOR_METHODOLOGY}"

#: Prior fiscal epochs required before the comparison may classify.
MINIMUM_PRIOR_EPOCHS = 3

#: How every production observation's market capitalisation is formed.
SHARE_COUNT_METHOD = ShareCountMethod.ISSUER_COMMON_EQUITY_MARKET_CAP

#: 52 weeks, the shortest fiscal year: a prior epoch's observation taken
#: within this many days of its fiscal year end precedes the following
#: fiscal year's close, and therefore its report.
_PRIOR_EPOCH_WINDOW_DAYS = 364

_ALL_CONSUMERS = (
    Consumer.PORTFOLIO_PAGE,
    Consumer.INVESTMENT_CASE_PAGE,
    Consumer.DISCOVERY,
    Consumer.HISTORY,
)


def _iso_date(period: str) -> date | None:
    """Periods originate from a provider's own dates, so this succeeds for
    real data; anything else fails closed and takes no part."""
    try:
        return date.fromisoformat(period)
    except ValueError:
        return None


def _single_by_period(facts: list, kind) -> dict[str, object]:
    """One fact per period, or none: two facts of one kind for one period
    that disagree are an ambiguity, never resolved by input order."""
    grouped: dict[str, list] = {}
    for fact in facts:
        if fact.kind is kind:
            grouped.setdefault(fact.period, []).append(fact)
    resolved = {}
    for period, group in grouped.items():
        if len({(fact.value, fact.unit) for fact in group}) == 1:
            resolved[period] = min(group, key=lambda fact: fact.id)
    return resolved


def _eligible_free_cash_flow(
    business_facts: tuple[BusinessFact, ...], *, statement_record_ids: frozenset[str], cutoff: date
) -> tuple[dict[str, BusinessFact], tuple[FcfYieldExclusion, ...]]:
    eligible: list[BusinessFact] = []
    excluded: list[FcfYieldExclusion] = []
    for fact in sorted(business_facts, key=lambda f: (f.period, f.id)):
        if fact.kind is not BusinessFactKind.FREE_CASH_FLOW:
            continue
        period_end = _iso_date(fact.period)
        if period_end is None:
            continue
        if period_end > cutoff:
            excluded.append(FcfYieldExclusion(fact.id, ValuationFactExclusionReason.FUTURE_PERIOD))
        elif fact.source_record_id not in statement_record_ids:
            excluded.append(FcfYieldExclusion(fact.id, ValuationFactExclusionReason.NOT_A_FINANCIAL_STATEMENT))
        else:
            eligible.append(fact)
    return _single_by_period(eligible, BusinessFactKind.FREE_CASH_FLOW), tuple(excluded)


def _statement_filing_dates(
    business_facts: tuple[BusinessFact, ...], *, statement_record_ids: frozenset[str], evaluated_at: datetime
) -> list[date]:
    """Every annual-statement filing date Atlas holds, up to `evaluated_at`."""
    return sorted({
        fact.published_at.date()
        for fact in business_facts
        if fact.source_record_id in statement_record_ids and fact.published_at <= evaluated_at
    })


def _available_from(period_end: date, filing_dates: list[date]) -> date | None:
    """The earliest statement filing dated after the period end."""
    index = bisect_right(filing_dates, period_end)
    return filing_dates[index] if index < len(filing_dates) else None


def _epoch(fiscal_period: str, available_from: date, observed_on: str, fcf: BusinessFact, price, shares):
    return FcfYieldEpochObservation(
        fiscal_period=fiscal_period,
        available_from=available_from,
        observed_on=observed_on,
        free_cash_flow=fcf.value,
        share_price=price.value,
        shares_outstanding=shares.value,
        currency=price.unit,
        free_cash_flow_fact_id=fcf.id,
        share_price_fact_id=price.id,
        shares_outstanding_fact_id=shares.id,
    )


@dataclass(frozen=True)
class _Epochs:
    """The fiscal epochs, before any valuation: which fiscal year each market
    observation belongs to and which observation represents it. Priced here
    on the provider proxy -- the only pricing the facts alone carry; the
    issuer basis re-prices the same epochs."""

    applies: bool | None
    excluded: tuple[FcfYieldExclusion, ...]
    missing: tuple[ValuationDataGapKind, ...]
    current: FcfYieldEpochObservation | None = None
    prior: tuple[FcfYieldEpochObservation, ...] = ()
    consolidated: tuple[str, ...] = ()
    #: Gaps that explain an absent current observation.
    no_current_gaps: tuple[ValuationDataGapKind, ...] = ()


def _fiscal_epochs(
    business_facts: tuple[BusinessFact, ...],
    valuation_facts: tuple[ValuationFact, ...],
    *,
    statement_record_ids: frozenset[str],
    industry: str | None,
    evaluated_at: datetime,
) -> _Epochs:
    applies = fcf_yield_applies(industry)
    if applies is False:
        return _Epochs(False, (), (ValuationDataGapKind.VALUATION_METHOD_NOT_APPLICABLE,))

    cutoff = evaluated_at.date()
    fcf_by_period, excluded = _eligible_free_cash_flow(
        business_facts, statement_record_ids=statement_record_ids, cutoff=cutoff
    )
    price_by_period = _single_by_period(list(valuation_facts), ValuationFactKind.SHARE_PRICE)
    shares_by_period = _single_by_period(list(valuation_facts), ValuationFactKind.SHARES_OUTSTANDING)

    missing: list[ValuationDataGapKind] = []
    if not any(f.kind is BusinessFactKind.FREE_CASH_FLOW for f in business_facts):
        missing.append(ValuationDataGapKind.MISSING_FREE_CASH_FLOW_HISTORY)
    if not price_by_period:
        missing.append(ValuationDataGapKind.MISSING_MARKET_PRICE)
    if not shares_by_period:
        missing.append(ValuationDataGapKind.MISSING_SHARE_COUNT)
    if applies is None:
        # Only worth naming when there is something to value: with an
        # input missing, that gap already says why nothing was valued.
        if not missing:
            missing.append(ValuationDataGapKind.VALUATION_APPLICABILITY_UNKNOWN)
        return _Epochs(None, excluded, tuple(missing))

    filing_dates = _statement_filing_dates(
        business_facts, statement_record_ids=statement_record_ids, evaluated_at=evaluated_at
    )
    # Fiscal years in order, each with the date it first became public.
    fiscal_years: list[tuple[str, date]] = []
    for period in sorted(fcf_by_period):
        available = _available_from(date.fromisoformat(period), filing_dates)
        if available is not None:
            fiscal_years.append((period, available))

    market_dates = sorted(
        (observed, period)
        for period in set(price_by_period) & set(shares_by_period)
        if (observed := _iso_date(period)) is not None and observed <= cutoff
    )

    # Each market observation belongs to the latest fiscal year public on
    # its date. Availability rises with the fiscal year, so a single pass
    # with a moving pointer assigns every observation.
    epochs: dict[str, list[str]] = {}
    unpaired = False
    pointer = -1
    for observed, period in market_dates:
        while pointer + 1 < len(fiscal_years) and fiscal_years[pointer + 1][1] <= observed:
            pointer += 1
        if pointer < 0:
            unpaired = True
            continue
        epochs.setdefault(fiscal_years[pointer][0], []).append(period)
    available_by_year = dict(fiscal_years)

    non_positive = False
    currency_mismatch = False

    def observe(fiscal_period: str, market_period: str) -> FcfYieldEpochObservation | None:
        nonlocal non_positive, currency_mismatch
        fcf, price, shares = fcf_by_period[fiscal_period], price_by_period[market_period], shares_by_period[market_period]
        if fcf.value <= 0:
            non_positive = True
            return None
        if fcf.unit != price.unit:
            currency_mismatch = True
            return None
        if price.value <= 0 or shares.value <= 0:
            return None
        return _epoch(fiscal_period, available_by_year[fiscal_period], market_period, fcf, price, shares)

    current: FcfYieldEpochObservation | None = None
    current_year: str | None = None
    if market_dates and epochs:
        latest_period = market_dates[-1][1]
        current_year = next((year for year, periods in epochs.items() if latest_period in periods), None)
        if current_year is not None:
            current = observe(current_year, latest_period)

    prior: list[FcfYieldEpochObservation] = []
    consolidated: list[str] = []
    for fiscal_period in sorted(epochs):
        periods = sorted(epochs[fiscal_period])
        if fiscal_period == current_year:
            if current is not None:
                consolidated.extend(periods[:-1])
            continue
        window_end = date.fromisoformat(fiscal_period).toordinal() + _PRIOR_EPOCH_WINDOW_DAYS
        in_window = [p for p in periods if date.fromisoformat(p).toordinal() <= window_end]
        if not in_window:
            continue
        observation = observe(fiscal_period, in_window[0])
        if observation is not None:
            prior.append(observation)
            consolidated.extend(p for p in periods if p != in_window[0])
    if current_year is not None:
        prior = [epoch for epoch in prior if epoch.fiscal_period < current_year]

    no_current: list[ValuationDataGapKind] = []
    if current is None:
        if non_positive:
            no_current.append(ValuationDataGapKind.CASH_FLOW_NOT_POSITIVE)
        if currency_mismatch:
            no_current.append(ValuationDataGapKind.CURRENCY_MISMATCH)
        if unpaired or (market_dates and fcf_by_period and not fiscal_years):
            no_current.append(ValuationDataGapKind.NO_ELIGIBLE_FUNDAMENTALS_AS_OF_OBSERVATION)
        if not fcf_by_period and ValuationDataGapKind.MISSING_FREE_CASH_FLOW_HISTORY not in missing:
            no_current.append(ValuationDataGapKind.MISSING_FREE_CASH_FLOW_HISTORY)
    return _Epochs(True, excluded, tuple(missing), current, tuple(prior), tuple(sorted(consolidated)), tuple(no_current))


def _not_applicable_finding(evaluated_at: datetime, method: ShareCountMethod) -> ValuationFinding:
    evidence = FcfYieldEvidence(
        eligibility=ValuationDecisionEligibility.NOT_APPLICABLE,
        minimum_prior_epochs=MINIMUM_PRIOR_EPOCHS,
        share_count_method=method,
    )
    return _finding(
        evidence, [ValuationDataGapKind.VALUATION_METHOD_NOT_APPLICABLE], evaluated_at,
        confidence=EvidenceCoverageLevel.NOT_APPLICABLE,
    )


def fiscal_epochs(
    business_facts: tuple[BusinessFact, ...],
    valuation_facts: tuple[ValuationFact, ...],
    *,
    statement_record_ids: frozenset[str],
    industry: str | None,
    evaluated_at: datetime,
) -> FcfYieldEvidence | None:
    """The fiscal epochs the issuer basis is asked to price: the same current
    and prior observations every construction compares, each still priced on
    the provider proxy (`fiscal_epoch_v2`'s own evidence). A description of
    *which* observations exist -- never a valuation. `None` when the method
    does not apply or its applicability is unknown."""
    epochs = _fiscal_epochs(business_facts, valuation_facts, statement_record_ids=statement_record_ids,
                            industry=industry, evaluated_at=evaluated_at)
    if not epochs.applies:
        return None
    return _proxy_evidence(epochs)


def _proxy_evidence(epochs: _Epochs) -> FcfYieldEvidence:
    current, prior = epochs.current, epochs.prior
    if current is not None and prior:
        eligibility = (
            ValuationDecisionEligibility.ELIGIBLE if len(prior) >= MINIMUM_PRIOR_EPOCHS
            else ValuationDecisionEligibility.LIMITED
        )
        position = position_of(current.fcf_yield, tuple(epoch.fcf_yield for epoch in prior))
    else:
        eligibility = ValuationDecisionEligibility.INSUFFICIENT
        position = None
    return FcfYieldEvidence(
        eligibility=eligibility,
        minimum_prior_epochs=MINIMUM_PRIOR_EPOCHS,
        share_count_method=ShareCountMethod.CURRENT_SHARE_COUNT_PROXY,
        current=current,
        prior_epochs=prior,
        position=position,
        consolidated_observations=epochs.consolidated,
        excluded=epochs.excluded,
    )


def evaluate_fcf_yield_relative_v2(
    business_facts: tuple[BusinessFact, ...],
    valuation_facts: tuple[ValuationFact, ...],
    *,
    statement_record_ids: frozenset[str],
    industry: str | None,
    evaluated_at: datetime,
) -> ValuationFinding:
    """`fiscal_epoch_v2` -- the retired provider-proxy construction (adjusted
    price times today's provider share count), kept callable only to
    interpret history persisted under it and for migration comparisons.
    Production never calls it (`evaluate_valuation` is v3 only)."""
    epochs = _fiscal_epochs(business_facts, valuation_facts, statement_record_ids=statement_record_ids,
                            industry=industry, evaluated_at=evaluated_at)
    if epochs.applies is False:
        return _not_applicable_finding(evaluated_at, ShareCountMethod.CURRENT_SHARE_COUNT_PROXY)
    missing = list(epochs.missing)
    if epochs.applies is None:
        return _finding(_insufficient_evidence(epochs.excluded, ShareCountMethod.CURRENT_SHARE_COUNT_PROXY), missing,
                        evaluated_at, business_facts=business_facts, valuation_facts=valuation_facts)
    evidence = _proxy_evidence(epochs)
    if evidence.eligibility is ValuationDecisionEligibility.ELIGIBLE:
        return _finding(evidence, missing, evaluated_at)
    if evidence.current is not None:
        missing.append(ValuationDataGapKind.INSUFFICIENT_HISTORICAL_VALUATION_PERIODS)
    else:
        missing.extend(epochs.no_current_gaps)
    return _finding(evidence, list(dict.fromkeys(missing)), evaluated_at, business_facts=business_facts,
                    valuation_facts=valuation_facts)


def _issuer_epoch(epoch: FcfYieldEpochObservation, cap: IssuerMarketCap, claim: SeniorClaim | None
                  ) -> FcfYieldEpochObservation | ValuationDataGapKind:
    """One epoch re-priced on the issuer basis, or why it cannot be."""
    if cap.economic_date != date.fromisoformat(epoch.observed_on) or cap.economic_date < epoch.available_from:
        return ValuationDataGapKind.TEMPORAL_EVIDENCE_GAP
    if cap.currency != epoch.currency:
        return ValuationDataGapKind.CURRENCY_MISMATCH
    low, high = (claim.low, claim.high) if claim is not None else (0.0, 0.0)
    raw = epoch.free_cash_flow
    if raw - high <= 0:
        return ValuationDataGapKind.CASH_FLOW_NOT_POSITIVE
    middle = (cap.market_cap_low + cap.market_cap_high) / 2
    return FcfYieldEpochObservation(
        fiscal_period=epoch.fiscal_period,
        available_from=epoch.available_from,
        observed_on=epoch.observed_on,
        free_cash_flow=raw - (low + high) / 2,
        share_price=cap.share_price,
        shares_outstanding=middle / cap.share_price,
        currency=epoch.currency,
        free_cash_flow_fact_id=epoch.free_cash_flow_fact_id,
        share_price_fact_id=epoch.share_price_fact_id,
        shares_outstanding_fact_id=None,
        market_cap_low=cap.market_cap_low,
        market_cap_high=cap.market_cap_high,
        raw_free_cash_flow=raw,
        senior_claim_low=low,
        senior_claim_high=high,
        denominator_quality=cap.quality.value,
    )


def _reprice(epoch: FcfYieldEpochObservation, cap: IssuerMarketCap | ValuationDataGapKind,
             basis: IssuerValuationBasis) -> FcfYieldEpochObservation | ValuationDataGapKind:
    if isinstance(cap, ValuationDataGapKind):
        return cap
    claim = basis.claim_for(epoch.fiscal_period)
    if isinstance(claim, ValuationDataGapKind):
        return claim
    return _issuer_epoch(epoch, cap, claim)


def evaluate_fcf_yield_relative(
    business_facts: tuple[BusinessFact, ...],
    valuation_facts: tuple[ValuationFact, ...],
    *,
    statement_record_ids: frozenset[str],
    industry: str | None,
    evaluated_at: datetime,
    basis: IssuerValuationBasis | None,
) -> ValuationFinding:
    """`fiscal_epoch_v3` -- the production FCF-yield evaluator. Deterministic
    and independent of input order. The fiscal epochs are the ones every
    construction compares (`fiscal_epochs`); each is priced on `basis`, the
    issuer's common equity on the observation's own date, over the free cash
    flow attributable to common equity. An epoch the basis cannot price is
    left out; a current observation it cannot price -- or no basis at all --
    withholds the valuation (`FcfYieldEvidence.withheld_reasons`). Nothing
    here ever prices an observation on the provider proxy."""
    method = ShareCountMethod.ISSUER_COMMON_EQUITY_MARKET_CAP
    epochs = _fiscal_epochs(business_facts, valuation_facts, statement_record_ids=statement_record_ids,
                            industry=industry, evaluated_at=evaluated_at)
    if epochs.applies is False:
        return _not_applicable_finding(evaluated_at, method)
    missing = list(epochs.missing)
    if epochs.applies is None:
        return _finding(_insufficient_evidence(epochs.excluded, method), missing, evaluated_at,
                        business_facts=business_facts, valuation_facts=valuation_facts)

    withheld: list[ValuationDataGapKind] = []
    prior: list[FcfYieldEpochObservation] = []
    current: FcfYieldEpochObservation | None = None
    if basis is None:
        if epochs.current is not None:
            withheld.append(ValuationDataGapKind.DENOMINATOR_EVIDENCE_MISSING)
    else:
        for epoch in epochs.prior:
            priced = _reprice(epoch, basis.denominator_for(epoch.fiscal_period, epoch.observed_on), basis)
            if not isinstance(priced, ValuationDataGapKind):
                prior.append(priced)
        if epochs.current is not None:
            cap = basis.current if basis.current is not None else (
                basis.current_gap or ValuationDataGapKind.DENOMINATOR_EVIDENCE_MISSING)
            if isinstance(cap, IssuerMarketCap) and cap.economic_date != date.fromisoformat(epochs.current.observed_on):
                # Strict current timing: a composition from another date is not
                # current evidence, however recent.
                cap = ValuationDataGapKind.CURRENT_ISSUER_PRICE_NOT_SYNCHRONIZED
            priced = _reprice(epochs.current, cap, basis)
            if isinstance(priced, ValuationDataGapKind):
                withheld.append(priced)
            else:
                current = priced

    position = None
    if current is not None and prior and not withheld:
        # Both ends of every interval must place today's yield the same way.
        at_cheapest = position_of(current.fcf_yield_high, tuple(p.fcf_yield_low for p in prior))
        at_dearest = position_of(current.fcf_yield_low, tuple(p.fcf_yield_high for p in prior))
        if at_cheapest is at_dearest:
            position = position_of(current.fcf_yield, tuple(p.fcf_yield for p in prior))
        else:
            withheld.append(ValuationDataGapKind.BOUNDED_DENOMINATOR_DISAGREEMENT)
    if withheld:
        eligibility = ValuationDecisionEligibility.INSUFFICIENT
    elif current is None or not prior:
        eligibility = ValuationDecisionEligibility.INSUFFICIENT
    elif len(prior) < MINIMUM_PRIOR_EPOCHS:
        eligibility = ValuationDecisionEligibility.LIMITED
    else:
        eligibility = ValuationDecisionEligibility.ELIGIBLE
    evidence = FcfYieldEvidence(
        eligibility=eligibility,
        minimum_prior_epochs=MINIMUM_PRIOR_EPOCHS,
        share_count_method=method,
        current=current,
        prior_epochs=tuple(prior),
        position=position,
        consolidated_observations=epochs.consolidated,
        excluded=epochs.excluded,
        withheld_reasons=tuple(dict.fromkeys(withheld)),
        numerator_method=COMMON_FCF_NUMERATOR_METHODOLOGY,
        nci_treatment=basis.nci_treatment if basis is not None else NCI_TREATMENT,
    )
    if eligibility is ValuationDecisionEligibility.ELIGIBLE:
        return _finding(evidence, missing, evaluated_at)
    missing.extend(withheld)
    if epochs.current is None:
        missing.extend(epochs.no_current_gaps)
    elif len(prior) < MINIMUM_PRIOR_EPOCHS:
        # One Case may lack both a current denominator and enough history:
        # every blocker is named, never only the first.
        missing.append(ValuationDataGapKind.INSUFFICIENT_HISTORICAL_VALUATION_PERIODS)
    return _finding(evidence, list(dict.fromkeys(missing)), evaluated_at, business_facts=business_facts,
                    valuation_facts=valuation_facts)


def _insufficient_evidence(excluded: tuple[FcfYieldExclusion, ...], method: ShareCountMethod) -> FcfYieldEvidence:
    return FcfYieldEvidence(
        eligibility=ValuationDecisionEligibility.INSUFFICIENT,
        minimum_prior_epochs=MINIMUM_PRIOR_EPOCHS,
        share_count_method=method,
        excluded=excluded,
    )


def _coverage(business_facts, valuation_facts) -> EvidenceCoverageLevel:
    present = sum((
        any(f.kind is BusinessFactKind.FREE_CASH_FLOW for f in business_facts),
        any(f.kind is ValuationFactKind.SHARE_PRICE for f in valuation_facts),
        any(f.kind is ValuationFactKind.SHARES_OUTSTANDING for f in valuation_facts),
    ))
    if present == 0:
        return EvidenceCoverageLevel.NOT_APPLICABLE
    return EvidenceCoverageLevel.NONE if present == 3 else EvidenceCoverageLevel.PARTIAL


def _finding(
    evidence: FcfYieldEvidence,
    missing: list[ValuationDataGapKind],
    evaluated_at: datetime,
    *,
    business_facts: tuple[BusinessFact, ...] = (),
    valuation_facts: tuple[ValuationFact, ...] = (),
    confidence: EvidenceCoverageLevel | None = None,
) -> ValuationFinding:
    status = evidence.decision_status
    eligible = evidence.eligibility is ValuationDecisionEligibility.ELIGIBLE
    # What the comparison rested on: nothing is compared without a current
    # observation, so prior epochs alone support nothing.
    epochs = (evidence.current, *evidence.prior_epochs) if evidence.current is not None else ()
    supporting = tuple(sorted({fact_id for epoch in epochs for fact_id in epoch.fact_ids}))
    dependencies = tuple(sorted(evidence.current.fact_ids)) if evidence.current is not None else ()
    if confidence is None:
        confidence = EvidenceCoverageLevel.FULL if eligible else _coverage(business_facts, valuation_facts)
    return ValuationFinding(
        id=f"valuation_finding:{ValuationMethodKind.FCF_YIELD_RELATIVE.value}",
        kind=ValuationMethodKind.FCF_YIELD_RELATIVE,
        status=status,
        severity=severity_for_valuation_status(status),
        supporting_facts=supporting,
        contradicting_facts=(),
        assumptions=(),
        missing_evidence=tuple(missing),
        confidence=confidence,
        provenance=Provenance(
            source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
            source_references=supporting,
            dependencies=dependencies,
            update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
            consumers=_ALL_CONSUMERS,
            computed_at=evaluated_at,
        ),
        evaluated_at=evaluated_at,
        current_yield=evidence.current.fcf_yield if evidence.current is not None else None,
        historical_yields=tuple(sorted(evidence.prior_yields)) if eligible else (),
        fcf_yield_evidence=evidence,
    )
