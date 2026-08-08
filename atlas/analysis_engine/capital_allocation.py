"""Capital Allocation evaluator v1 (ATLAS-023, Phase 6) -- Atlas's
second real Business Analysis category evaluator, from `BusinessFact`s
only.

**The rule table, documented before it was implemented:**

Two independent signals, each computed from the *sum* of a fact kind's
values across every available period (v1 reasons about aggregate
capital deployed, not a period-by-period trend the way Growth does):

- **`capital_return`** -- compares total `SHARE_BUYBACKS` against total
  `SHARE_ISSUANCE`. `POSITIVE` if buybacks exceed issuance (net capital
  returned to shareholders, non-dilutive), `NEGATIVE` if issuance
  exceeds buybacks (net dilution), `FLAT` if equal.
- **`leverage`** -- compares total `DEBT_REPAYMENT` against total
  `DEBT_ISSUANCE`. `POSITIVE` if repayment exceeds issuance
  (deleveraging), `NEGATIVE` if issuance exceeds repayment (increasing
  leverage), `FLAT` if equal.

**Both signals require facts on *both* sides of their comparison to be
computable at all.** If Atlas has buyback facts but zero issuance
facts, `capital_return` is `INSUFFICIENT` -- absence of an issuance
fact is never treated as "zero issuance"; that would be inferring a
number no source data stated. Same for `leverage`.

Status, in this fixed order, first match wins:

1. Both signals `INSUFFICIENT` -> `INSUFFICIENT_INPUT`.
2. Either signal `NEGATIVE` -> `WEAK` -- adverse capital allocation
   behavior on even one computable signal is disqualifying; a `WEAK`
   result is never offset by the other signal being positive (that
   would be exactly the "hidden weighting" this sprint forbids).
3. Both signals computable and `POSITIVE` -> `STRONG` -- requires
   *both* independent signals to corroborate, the same "more than one
   signal must agree for the top tier" bar `growth.py` applies.
4. Anything else (one signal computable and positive while the other is
   `INSUFFICIENT`, or either signal `FLAT`) -> `MODERATE`.

**`CAPITAL_EXPENDITURE` and `DIVIDENDS` are informational only in v1.**
Their presence or absence is always recorded in `missing_evidence`, but
neither drives `status` -- doing so would require an arbitrary
payout-ratio or reinvestment-rate cutoff this sprint has no principled
way to justify. A future sprint that wants to use them needs to derive
and document a real rule first, not inherit one from here.

`confidence` reuses `EvidenceCoverageLevel` the same way `growth.py`
does, over the two signals: `FULL` (both computable), `PARTIAL` (one
computable), `NONE` (some of the six relevant fact kinds exist but
neither signal reaches computability), `NOT_APPLICABLE` (none of the
six kinds have any fact at all).
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
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
from atlas.decision_engine.contracts import EvidenceCoverageLevel

__all__ = ["evaluate_capital_allocation"]

_ALL_RELEVANT_KINDS = (
    BusinessFactKind.CAPITAL_EXPENDITURE,
    BusinessFactKind.SHARE_BUYBACKS,
    BusinessFactKind.SHARE_ISSUANCE,
    BusinessFactKind.DIVIDENDS,
    BusinessFactKind.DEBT_ISSUANCE,
    BusinessFactKind.DEBT_REPAYMENT,
)

_ALL_CONSUMERS = (
    Consumer.PORTFOLIO_PAGE,
    Consumer.INVESTMENT_CASE_PAGE,
    Consumer.DISCOVERY,
    Consumer.HISTORY,
)


class _Signal(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    FLAT = "flat"
    INSUFFICIENT = "insufficient"


def _facts_by_kind(facts: tuple[BusinessFact, ...]) -> dict[BusinessFactKind, list[BusinessFact]]:
    grouped: dict[BusinessFactKind, list[BusinessFact]] = {kind: [] for kind in _ALL_RELEVANT_KINDS}
    for fact in facts:
        if fact.kind in grouped:
            grouped[fact.kind].append(fact)
    return grouped


def _compare(
    positive_side: list[BusinessFact], negative_side: list[BusinessFact]
) -> tuple[_Signal, tuple[str, ...], tuple[str, ...]]:
    """`positive_side` is the fact kind whose total being larger drives
    `POSITIVE` (buybacks for `capital_return`, repayment for
    `leverage`); `negative_side` is its counterpart."""
    if not positive_side or not negative_side:
        return _Signal.INSUFFICIENT, (), ()

    positive_total = sum(fact.value for fact in positive_side)
    negative_total = sum(fact.value for fact in negative_side)
    all_ids = tuple(sorted(fact.id for fact in (*positive_side, *negative_side)))

    if positive_total > negative_total:
        return _Signal.POSITIVE, all_ids, ()
    if negative_total > positive_total:
        return _Signal.NEGATIVE, (), all_ids
    return _Signal.FLAT, (), ()


def _confidence(computable_count: int, any_facts_at_all: bool) -> EvidenceCoverageLevel:
    if computable_count == 2:
        return EvidenceCoverageLevel.FULL
    if computable_count == 1:
        return EvidenceCoverageLevel.PARTIAL
    if any_facts_at_all:
        return EvidenceCoverageLevel.NONE
    return EvidenceCoverageLevel.NOT_APPLICABLE


def evaluate_capital_allocation(facts: tuple[BusinessFact, ...], *, evaluated_at: datetime) -> BusinessFinding:
    """Deterministic: identical `facts` always produce a deeply equal
    `BusinessFinding`. Reads only `BusinessFact`."""
    grouped = _facts_by_kind(facts)
    any_facts_at_all = any(grouped.values())

    capital_return, cr_supporting, cr_contradicting = _compare(
        grouped[BusinessFactKind.SHARE_BUYBACKS], grouped[BusinessFactKind.SHARE_ISSUANCE]
    )
    leverage, lev_supporting, lev_contradicting = _compare(
        grouped[BusinessFactKind.DEBT_REPAYMENT], grouped[BusinessFactKind.DEBT_ISSUANCE]
    )

    signals = (capital_return, leverage)
    computable_count = sum(1 for signal in signals if signal is not _Signal.INSUFFICIENT)

    missing: list[BusinessDataGapKind] = []
    if capital_return is _Signal.INSUFFICIENT:
        missing.append(BusinessDataGapKind.MISSING_BUYBACK_DATA)
    if leverage is _Signal.INSUFFICIENT:
        missing.append(BusinessDataGapKind.MISSING_DEBT_DATA)
    if not grouped[BusinessFactKind.CAPITAL_EXPENDITURE]:
        missing.append(BusinessDataGapKind.MISSING_CAPEX_DATA)
    if not grouped[BusinessFactKind.DIVIDENDS]:
        missing.append(BusinessDataGapKind.MISSING_DIVIDEND_DATA)

    if computable_count == 0:
        status = Status.INSUFFICIENT_INPUT
    elif _Signal.NEGATIVE in signals:
        status = Status.WEAK
    elif capital_return is _Signal.POSITIVE and leverage is _Signal.POSITIVE:
        status = Status.STRONG
    else:
        status = Status.MODERATE

    supporting_ids = tuple(sorted({*cr_supporting, *lev_supporting}))
    contradicting_ids = tuple(sorted({*cr_contradicting, *lev_contradicting}))
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
