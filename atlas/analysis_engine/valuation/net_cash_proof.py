"""Net-Cash proof path (`DE-015` §15) -- the independent, current-state
proof path. Fully compliant with Candidate A's own "never extrapolate"
principle: no growth rate, no terminal yield, no horizon, no forward
content of any kind anywhere in this module.

**Required real facts only.** `CASH` and `TOTAL_DEBT`
(`BusinessFactKind`, already real and ingested -- `business_facts
/contracts.py`'s own docstring for `CASH` names this exact use: "the
numerator a future principled net-cash-position rule would need") and
current market capitalization, derived the identical way
`cash_flow.py` already derives it (`SHARE_PRICE` x `SHARES_OUTSTANDING`,
`ValuationFactKind`). **No additional balance-sheet capability is
invented** -- no inventory, receivables, PP&E, or sum-of-the-parts, per
the explicit instruction not to expand this path.

**Proof criterion.** `net_cash = CASH - TOTAL_DEBT`. `market_cap <
net_cash` -> `ESTABLISHES_SUPPORT` (a real, non-speculative fact: today's
entire market price is below the company's own readily available cash
net of debt). Being priced *above* net cash establishes nothing --
`DOES_NOT_ESTABLISH`, never `ESTABLISHES_NON_SUPPORT`: the ordinary case
for almost every real company carries no negative implication on its own.
"""
from __future__ import annotations

from datetime import datetime

from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.valuation.facts import ValuationFact, ValuationFactKind
from atlas.analysis_engine.valuation.proof import PathProof, ProofVerdict

__all__ = ["PATH_NAME", "evaluate_net_cash_proof"]

PATH_NAME = "net_cash"


def _most_recent_eligible(
    facts: tuple[BusinessFact, ...], kind: BusinessFactKind, *, as_of: datetime
) -> BusinessFact | None:
    """The most recent real fact of `kind` (by `period`) among those
    whose `published_at` is on or before `as_of` -- the identical
    no-look-ahead rule `cash_flow.py::_eligible_fcf_as_of` already
    applies to Free Cash Flow, generalized to any kind. A current-state
    claim must never be built from a fact Atlas could not have actually
    known about at `as_of`."""
    eligible = [f for f in facts if f.kind is kind and f.published_at.date() <= as_of.date()]
    if not eligible:
        return None
    return max(eligible, key=lambda f: (f.period, f.published_at, f.id))


def _current_market_cap(valuation_facts: tuple[ValuationFact, ...], *, as_of: datetime) -> float | None:
    """The most recent real market observation (a period where both
    `SHARE_PRICE` and `SHARES_OUTSTANDING` exist) not after `as_of` --
    the identical `market_periods` construction `cash_flow.py` already
    uses for the same two `ValuationFactKind` members."""
    cutoff = as_of.date().isoformat()
    price_by_period = {
        f.period: f for f in valuation_facts if f.kind is ValuationFactKind.SHARE_PRICE and f.period <= cutoff
    }
    shares_by_period = {
        f.period: f for f in valuation_facts if f.kind is ValuationFactKind.SHARES_OUTSTANDING and f.period <= cutoff
    }
    common_periods = sorted(set(price_by_period) & set(shares_by_period))
    if not common_periods:
        return None
    most_recent = common_periods[-1]
    market_cap = price_by_period[most_recent].value * shares_by_period[most_recent].value
    if market_cap <= 0:
        return None
    return market_cap


def evaluate_net_cash_proof(
    business_facts: tuple[BusinessFact, ...],
    valuation_facts: tuple[ValuationFact, ...],
    *,
    generated_at: datetime,
) -> PathProof:
    """Deterministic: identical inputs always produce an identical
    `PathProof`."""
    cash_fact = _most_recent_eligible(business_facts, BusinessFactKind.CASH, as_of=generated_at)
    if cash_fact is None:
        return PathProof(path_name=PATH_NAME, verdict=ProofVerdict.DOES_NOT_ESTABLISH, evidence_summary="missing_cash")

    debt_fact = _most_recent_eligible(business_facts, BusinessFactKind.TOTAL_DEBT, as_of=generated_at)
    if debt_fact is None:
        return PathProof(path_name=PATH_NAME, verdict=ProofVerdict.DOES_NOT_ESTABLISH, evidence_summary="missing_debt")

    market_cap = _current_market_cap(valuation_facts, as_of=generated_at)
    if market_cap is None:
        return PathProof(
            path_name=PATH_NAME, verdict=ProofVerdict.DOES_NOT_ESTABLISH, evidence_summary="missing_current_market_cap"
        )

    net_cash = cash_fact.value - debt_fact.value
    evidence = f"market_cap={market_cap:.2f};net_cash={net_cash:.2f}"

    if market_cap < net_cash:
        return PathProof(path_name=PATH_NAME, verdict=ProofVerdict.ESTABLISHES_SUPPORT, evidence_summary=evidence)
    return PathProof(path_name=PATH_NAME, verdict=ProofVerdict.DOES_NOT_ESTABLISH, evidence_summary=evidence)
