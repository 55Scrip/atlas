"""Capital Allocation evaluator v2 (ATLAS-023, Phase 6; redesigned
Calibration Phase 4 -- Conviction & Capital Allocation Repair) --
Atlas's second real Business Analysis category evaluator, from
`BusinessFact`s only.

**Calibration Phase 4 investigation (confirmed weaknesses in v1):**
Read directly from v1's own source: (1) `DIVIDENDS` was collected but
never scored -- a real, current dividend counted for nothing. (2) A
single `NEGATIVE` signal (of only two, `capital_return`/`leverage`)
unconditionally forced `WEAK`, never offset by the other signal being
positive regardless of magnitude or age -- one stale debt-issuance
fact from a decade ago could disqualify an otherwise excellent
allocator forever. (3) Facts were summed across a company's *entire*
available history with no recency weighting. (4) No cash-generation
check existed at all -- a company funding its capital returns from
strong free cash flow and one issuing debt to fund them read
identically. (5) `leverage` compared static repayment-vs-issuance
totals, never a *trend* -- a company actively deleveraging since a
one-time acquisition-funded debt raise was indistinguishable from one
with chronically worsening leverage. See
`docs/Calibration-Phase-4-Conviction-And-Capital-Allocation-Redesign.md`
for the full investigation and design this module implements.

**The v2 rule table, documented before it was implemented:**

Four independently-computed signals, each `POSITIVE`/`NEGATIVE`/
`INSUFFICIENT` (a true tie is `INSUFFICIENT` -- no invented tie-break):

1. **`capital_return`** -- compares total `SHARE_BUYBACKS` against
   total `SHARE_ISSUANCE`, unchanged comparison logic, but computed
   only over each fact kind's own most recent 3 available periods (a
   trailing window, not the full history) -- a concrete, disclosed,
   general parameter, not a per-company tune. `POSITIVE` if
   windowed buybacks exceed windowed issuance, `NEGATIVE` if reversed,
   `INSUFFICIENT` if either windowed side has zero facts (never
   inferred as zero) or the two totals tie.
2. **`leverage_trend`** -- reuses `atlas.analysis_engine.growth
   .classify_metric_trend` verbatim over the full available
   `TOTAL_DEBT` history, the identical reuse
   `atlas.analysis_engine.risk.financial_risk._debt_trend_signal`
   already established -- never a second trend algorithm. Falling debt
   in every consecutive period -> `POSITIVE` (debt reduction improves
   the score); rising in every period -> `NEGATIVE`; fewer than two
   periods or a mixed trend -> `INSUFFICIENT`, never guessed. A trend
   over debt's *direction*, not its *level*, is what naturally stops
   one old acquisition-funded raise from permanently damning the
   category: if the company has been deleveraging since, the trend
   reads `POSITIVE`, not `NEGATIVE`.
3. **`dividend`** -- `POSITIVE` when the most recent available
   `DIVIDENDS` fact is greater than zero; `INSUFFICIENT` when no
   `DIVIDENDS` fact exists at all or the most recent one is zero.
   Deliberately never `NEGATIVE` -- declining to pay a dividend is a
   legitimate capital allocation strategy (reinvestment, buybacks-only),
   not a penalized one; this only ever rewards a real, current
   dividend, never punishes its absence.
4. **`cash_generation`** -- mirrors `atlas.analysis_engine.risk
   .financial_risk._cash_generation_signal`'s exact rule, re-expressed
   locally to avoid a new cross-evaluator (business-to-risk) dependency:
   most recent `FREE_CASH_FLOW` fact positive -> `POSITIVE`; negative
   -> `NEGATIVE`; no fact -> `INSUFFICIENT`.

**Combination rule** -- replaces v1's "any negative disqualifies" with
"negatives must genuinely outweigh positives," and requires real
multi-signal corroboration for the top tier:

    positive_count = count of POSITIVE among the four signals
    negative_count = count of NEGATIVE among the four signals
    computable_count = positive_count + negative_count

    if computable_count == 0:                        INSUFFICIENT_INPUT
    elif negative_count > positive_count:             WEAK
    elif positive_count >= 2 and negative_count == 0: STRONG
    else:                                              MODERATE

A single negative signal against a single positive now reads
`MODERATE` (mixed, honest), not `WEAK` (disqualified). `STRONG` now
requires at least two independently-corroborating positive signals and
zero negatives -- a higher, more deliberate bar than v1's own `STRONG`,
which needed only two signals to agree with nothing to disagree.

**`CAPITAL_EXPENDITURE` and `SHARES_OUTSTANDING` remain
informational-only, as in v1.** No principled scoring rule for them
was designed this sprint, and inventing one without evidence would
violate this sprint's own core principle -- every calibration must be
evidence-driven, never invented to move a number.

**What this does not do:** no debt fact is ever tagged "acquisition" or
"distress" -- Atlas has no such data and this sprint adds no new
provider or classification. `leverage_trend` is the general, honest
substitute: it cannot tell *why* debt was raised, but it can tell
whether the company has been deleveraging since, which is the closest
a fact-only evaluator can honestly get without fabricating intent.

`confidence` reuses `EvidenceCoverageLevel` the same way `growth.py`
does, generalized from two signals to four: `FULL` (all four
computable), `PARTIAL` (one to three computable), `NONE` (some of the
seven relevant fact kinds exist but zero signals reach computability),
`NOT_APPLICABLE` (none of the seven kinds have any fact at all).
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from atlas.analysis_engine.business_contracts import (
    BusinessCategory,
    BusinessDataGapKind,
    BusinessFinding,
    severity_for_status,
)
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus as Status
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.growth import MetricTrend, classify_metric_trend
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
from atlas.decision_engine.contracts import EvidenceCoverageLevel

__all__ = ["evaluate_capital_allocation"]

_ALL_RELEVANT_KINDS = (
    BusinessFactKind.CAPITAL_EXPENDITURE,
    BusinessFactKind.SHARE_BUYBACKS,
    BusinessFactKind.SHARE_ISSUANCE,
    BusinessFactKind.DIVIDENDS,
    BusinessFactKind.SHARES_OUTSTANDING,
    BusinessFactKind.TOTAL_DEBT,
    BusinessFactKind.FREE_CASH_FLOW,
)

_ALL_CONSUMERS = (
    Consumer.PORTFOLIO_PAGE,
    Consumer.INVESTMENT_CASE_PAGE,
    Consumer.DISCOVERY,
    Consumer.HISTORY,
)

_RECENCY_WINDOW = 3


class _Signal(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    INSUFFICIENT = "insufficient"


def _facts_by_kind(facts: tuple[BusinessFact, ...]) -> dict[BusinessFactKind, list[BusinessFact]]:
    grouped: dict[BusinessFactKind, list[BusinessFact]] = {kind: [] for kind in _ALL_RELEVANT_KINDS}
    for fact in facts:
        if fact.kind in grouped:
            grouped[fact.kind].append(fact)
    return grouped


def _most_recent(facts: list[BusinessFact], window: int = _RECENCY_WINDOW) -> list[BusinessFact]:
    return sorted(facts, key=lambda fact: fact.period, reverse=True)[:window]


def _capital_return_signal(
    buyback_facts: list[BusinessFact], issuance_facts: list[BusinessFact]
) -> tuple[_Signal, tuple[str, ...], tuple[str, ...]]:
    """Unchanged buybacks-vs-issuance comparison, now computed only
    over each side's own most recent `_RECENCY_WINDOW` periods -- an
    old, one-time issuance no longer weighs as much as sustained,
    recent buyback activity."""
    recent_buybacks = _most_recent(buyback_facts)
    recent_issuance = _most_recent(issuance_facts)
    if not recent_buybacks or not recent_issuance:
        return _Signal.INSUFFICIENT, (), ()

    buyback_total = sum(fact.value for fact in recent_buybacks)
    issuance_total = sum(fact.value for fact in recent_issuance)
    all_ids = tuple(sorted(fact.id for fact in (*recent_buybacks, *recent_issuance)))

    if buyback_total > issuance_total:
        return _Signal.POSITIVE, all_ids, ()
    if issuance_total > buyback_total:
        return _Signal.NEGATIVE, (), all_ids
    return _Signal.INSUFFICIENT, (), ()


def _leverage_trend_signal(debt_facts: list[BusinessFact]) -> tuple[_Signal, tuple[str, ...], tuple[str, ...]]:
    """Reuses `growth.classify_metric_trend` verbatim over the full
    `TOTAL_DEBT` history -- the identical reuse
    `financial_risk._debt_trend_signal` already established. Falling
    debt in every period (`WEAK_METRIC` in that function's own
    growth-neutral vocabulary) is a real positive here; rising in every
    period (`STRONG_METRIC`) is a real negative; fewer than two periods
    or a mixed trend is honestly `INSUFFICIENT`, never guessed."""
    sorted_debt = sorted(debt_facts, key=lambda fact: fact.period)
    if len(sorted_debt) < 2:
        return _Signal.INSUFFICIENT, (), ()
    trend, supporting, contradicting = classify_metric_trend(sorted_debt)
    if trend is MetricTrend.WEAK_METRIC:  # consistently falling debt
        return _Signal.POSITIVE, supporting, ()
    if trend is MetricTrend.STRONG_METRIC:  # consistently rising debt
        return _Signal.NEGATIVE, (), contradicting
    return _Signal.INSUFFICIENT, (), ()  # mixed trend: no clean signal either way


def _dividend_signal(dividend_facts: list[BusinessFact]) -> tuple[_Signal, tuple[str, ...]]:
    """Deliberately never `NEGATIVE` -- declining to pay a dividend is a
    legitimate strategy, not a penalized one. Only rewards a real,
    current dividend."""
    if not dividend_facts:
        return _Signal.INSUFFICIENT, ()
    most_recent = max(dividend_facts, key=lambda fact: fact.period)
    if most_recent.value > 0:
        return _Signal.POSITIVE, (most_recent.id,)
    return _Signal.INSUFFICIENT, ()


def _cash_generation_signal(fcf_facts: list[BusinessFact]) -> tuple[_Signal, tuple[str, ...]]:
    """Mirrors `financial_risk._cash_generation_signal`'s exact rule,
    re-expressed locally to avoid a new cross-evaluator dependency."""
    if not fcf_facts:
        return _Signal.INSUFFICIENT, ()
    most_recent = max(fcf_facts, key=lambda fact: fact.period)
    if most_recent.value > 0:
        return _Signal.POSITIVE, (most_recent.id,)
    if most_recent.value < 0:
        return _Signal.NEGATIVE, (most_recent.id,)
    return _Signal.INSUFFICIENT, ()


def _confidence(computable_count: int, any_facts_at_all: bool) -> EvidenceCoverageLevel:
    if computable_count == 4:
        return EvidenceCoverageLevel.FULL
    if computable_count > 0:
        return EvidenceCoverageLevel.PARTIAL
    if any_facts_at_all:
        return EvidenceCoverageLevel.NONE
    return EvidenceCoverageLevel.NOT_APPLICABLE


def evaluate_capital_allocation(facts: tuple[BusinessFact, ...], *, evaluated_at: datetime) -> BusinessFinding:
    """Deterministic: identical `facts` always produce a deeply equal
    `BusinessFinding`. Reads only `BusinessFact`."""
    grouped = _facts_by_kind(facts)
    any_facts_at_all = any(grouped.values())

    capital_return, cr_supporting, cr_contradicting = _capital_return_signal(
        grouped[BusinessFactKind.SHARE_BUYBACKS], grouped[BusinessFactKind.SHARE_ISSUANCE]
    )
    leverage_trend, lev_supporting, lev_contradicting = _leverage_trend_signal(grouped[BusinessFactKind.TOTAL_DEBT])
    dividend, div_supporting = _dividend_signal(grouped[BusinessFactKind.DIVIDENDS])
    cash_generation, cash_ids = _cash_generation_signal(grouped[BusinessFactKind.FREE_CASH_FLOW])
    cash_supporting = cash_ids if cash_generation is _Signal.POSITIVE else ()
    cash_contradicting = cash_ids if cash_generation is _Signal.NEGATIVE else ()

    signals = (capital_return, leverage_trend, dividend, cash_generation)
    positive_count = sum(1 for signal in signals if signal is _Signal.POSITIVE)
    negative_count = sum(1 for signal in signals if signal is _Signal.NEGATIVE)
    computable_count = positive_count + negative_count

    missing: list[BusinessDataGapKind] = []
    if capital_return is _Signal.INSUFFICIENT:
        missing.append(BusinessDataGapKind.MISSING_BUYBACK_DATA)
    if leverage_trend is _Signal.INSUFFICIENT:
        missing.append(BusinessDataGapKind.MISSING_DEBT_DATA)
    if dividend is _Signal.INSUFFICIENT:
        missing.append(BusinessDataGapKind.MISSING_DIVIDEND_DATA)
    if cash_generation is _Signal.INSUFFICIENT:
        missing.append(BusinessDataGapKind.MISSING_CASH_FLOW_DATA)
    if not grouped[BusinessFactKind.CAPITAL_EXPENDITURE]:
        missing.append(BusinessDataGapKind.MISSING_CAPEX_DATA)
    if not grouped[BusinessFactKind.SHARES_OUTSTANDING]:
        missing.append(BusinessDataGapKind.MISSING_SHARE_COUNT_HISTORY)

    if computable_count == 0:
        status = Status.INSUFFICIENT_INPUT
    elif negative_count > positive_count:
        status = Status.WEAK
    elif positive_count >= 2 and negative_count == 0:
        status = Status.STRONG
    else:
        status = Status.MODERATE

    supporting_ids = tuple(sorted({*cr_supporting, *lev_supporting, *div_supporting, *cash_supporting}))
    contradicting_ids = tuple(sorted({*cr_contradicting, *lev_contradicting, *cash_contradicting}))
    all_considered_ids = tuple(
        sorted({fact.id for kind_facts in grouped.values() for fact in kind_facts})
    )

    return BusinessFinding(
        id="business_finding:capital_allocation",
        kind=BusinessCategory.CAPITAL_ALLOCATION,
        status=status,
        severity=severity_for_status(status),
        supporting_evidence=supporting_ids,
        contradicting_evidence=contradicting_ids,
        missing_evidence=tuple(missing),
        confidence=_confidence(computable_count, any_facts_at_all),
        provenance=Provenance(
            source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
            source_references=tuple(sorted({*supporting_ids, *contradicting_ids})),
            dependencies=all_considered_ids,
            update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
            consumers=_ALL_CONSUMERS,
            computed_at=evaluated_at,
        ),
        updated_at=evaluated_at,
    )
