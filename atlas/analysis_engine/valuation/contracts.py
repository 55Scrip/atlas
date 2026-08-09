"""Shared Valuation vocabulary (ATLAS-024, Phase 10/12) --
`ValuationStatus`, `ValuationMethodKind`, `ValuationDataGapKind`,
`ValuationAssumptionKind`, and `severity_for_valuation_status`.

Mirrors `atlas.analysis_engine.business_contracts`'s own reason for
existing: `facts.py`, `cash_flow.py`, `scenarios.py`, and `pipeline.py`
all need this shared vocabulary without importing each other back and
forth.
"""
from __future__ import annotations

from enum import Enum

from atlas.analysis_engine.findings import FindingSeverity

__all__ = [
    "ValuationStatus",
    "ValuationMethodKind",
    "ValuationDataGapKind",
    "ValuationAssumptionKind",
    "severity_for_valuation_status",
]


class ValuationStatus(str, Enum):
    """Categorical, five levels, never numeric -- Phase 10's own list,
    applied verbatim, deliberately structured the same way
    `atlas.analysis_engine.business_contracts.BusinessCategoryStatus`
    is (a `NOT_EVALUATED`/`INSUFFICIENT_INPUT` pair plus exactly three
    real categorical outcomes) for consistency across sibling
    evaluators, even though the outcome vocabulary itself is
    valuation-specific. `NOT_EVALUATED` is reserved, never constructed
    -- every method this sprint ships has a real evaluator (even the
    scenario ones, which honestly return `INSUFFICIENT_INPUT` rather
    than never running at all)."""

    NOT_EVALUATED = "not_evaluated"
    INSUFFICIENT_INPUT = "insufficient_input"
    UNDERVALUED = "undervalued"
    FAIRLY_VALUED = "fairly_valued"
    EXPENSIVE = "expensive"


class ValuationMethodKind(str, Enum):
    """Which method produced a given `ValuationFinding` -- mirrors
    `atlas.analysis_engine.business_contracts.BusinessCategory`'s own
    role for `BusinessFinding`: `ValuationEngineResult.findings` always
    names all four, every run, never a partial list."""

    FCF_YIELD_RELATIVE = "fcf_yield_relative"
    """Phase 6/7's real v1 method -- current FCF yield vs. this
    company's own historical FCF-yield range. The only method this
    sprint can genuinely evaluate."""

    SCENARIO_BEAR = "scenario_bear"
    SCENARIO_BASE = "scenario_base"
    SCENARIO_BULL = "scenario_bull"
    """Phase 8's scenario structure -- real, tested, always
    `INSUFFICIENT_INPUT` this sprint (see `scenarios.py`'s own module
    docstring for why fabricating forward assumptions is refused)."""


class ValuationDataGapKind(str, Enum):
    """Why a method could not reach a real `UNDERVALUED`/`FAIRLY_VALUED`/
    `EXPENSIVE` conclusion -- Phase 12's own named-reason requirement,
    the same discipline
    `atlas.analysis_engine.business_contracts.BusinessDataGapKind`
    already established for its sibling package."""

    MISSING_MARKET_PRICE = "missing_market_price"
    MISSING_SHARE_COUNT = "missing_share_count"
    MISSING_FREE_CASH_FLOW_HISTORY = "missing_free_cash_flow_history"
    INSUFFICIENT_HISTORICAL_VALUATION_PERIODS = "insufficient_historical_valuation_periods"
    """Fewer than two periods where both a market snapshot and a
    Free Cash Flow fact share the same period -- there is nothing to
    compute a historical *range* from, even though a single current
    yield might be computable."""

    STALE_MARKET_DATA = "stale_market_data"
    """Reserved, not currently constructed (ATLAS-032). The original
    ATLAS-024 check compared a market snapshot's `period` against the
    most recent Free Cash Flow fact's `period` -- the same period-vs-
    period confusion ATLAS-032 removed from the rest of this method, so
    it was retired rather than reimplemented. A genuine "this market
    snapshot is too old" signal needs a real, owned wall-clock
    threshold, which does not exist anywhere in this codebase yet;
    see `cash_flow.py`'s own module docstring. A future sprint that
    defines and owns such a threshold should construct this member,
    not invent a new one."""

    NO_ELIGIBLE_FUNDAMENTALS_AS_OF_OBSERVATION = "no_eligible_fundamentals_as_of_observation"
    """(ATLAS-032) Free Cash Flow, market price, and share count facts
    all exist, but no Free Cash Flow fact was published on or before
    any known market observation -- the no-look-ahead rule excluded
    every candidate pairing rather than using a fundamental the market
    could not yet have known about. Distinct from
    `MISSING_FREE_CASH_FLOW_HISTORY` (no FCF fact exists at all): here
    the data exists, it is simply not yet eligible for any observation
    Atlas has. The case this is expected to matter for is a historical
    market observation that predates a company's earliest known filing."""

    CASH_FLOW_NOT_POSITIVE = "cash_flow_not_positive"
    """The current period's Free Cash Flow is zero or negative -- a
    yield computed from it would invert into a meaningless sign, not a
    genuine cheap/expensive signal (Phase 17's own "negative EPS"
    example, applied to FCF instead). The data is not missing; it
    simply cannot support this method honestly."""

    MISSING_SCENARIO_ASSUMPTIONS = "missing_scenario_assumptions"
    """No forward assumption was explicitly supplied for this scenario
    -- always true this sprint, for all three scenario methods; see
    `scenarios.py`."""


class ValuationAssumptionKind(str, Enum):
    """Reserved -- named now so a future scenario-assumption input
    mechanism does not need to widen this enum, the same "reserve the
    name, never construct it yet" discipline
    `atlas.analysis_engine.business_data.sources.SourceKind
    .MARKET_DATA_SNAPSHOT`'s own siblings already established. No code
    in this sprint ever constructs a `ValuationFinding` with a non-empty
    `assumptions` tuple -- `FCF_YIELD_RELATIVE` needs none (it compares
    only real historical facts), and the scenario methods have none
    supplied yet (see `ValuationDataGapKind.MISSING_SCENARIO_ASSUMPTIONS`)."""

    GROWTH_RATE_ASSUMPTION = "growth_rate_assumption"
    DISCOUNT_RATE_ASSUMPTION = "discount_rate_assumption"
    TERMINAL_MULTIPLE_ASSUMPTION = "terminal_multiple_assumption"


def severity_for_valuation_status(status: ValuationStatus) -> FindingSeverity:
    """Deterministic, mechanical mapping -- severity describes how much
    attention a gap deserves, never an investment opinion. `EXPENSIVE`
    is `ATTENTION`, not `MATERIAL`: an expensive valuation is a real,
    attention-worthy fact, but (per this sprint's own "Business Quality
    and Valuation must stay independent" rule) it is never treated as
    more urgent than, say, a `WEAK` Growth finding -- both are
    `ATTENTION`-severity facts about different questions, not ranked
    against each other."""
    if status in (ValuationStatus.NOT_EVALUATED, ValuationStatus.INSUFFICIENT_INPUT):
        return FindingSeverity.ATTENTION
    if status is ValuationStatus.EXPENSIVE:
        return FindingSeverity.ATTENTION
    return FindingSeverity.INFO
