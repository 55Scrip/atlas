"""Atlas Outlook v1 (Outlook Intelligence Sprint 1) -- the first real
data pipeline behind the Investment Case's Short-Term / Long-Term
Outlook panels, which have shown only honest "Not yet computed"
placeholders since the Figma-fidelity rebuild.

**Reuses, never re-derives.** Every input this module reads is already
computed elsewhere in `atlas.analysis_engine`: `business_analysis`,
`valuation_engine`, `risk_analysis`, `conviction`, and `synthesis` are
the exact same objects `pipeline.assemble_analysis` already assembled
for this run; `business_facts` is the same tuple already extracted for
Growth/Capital Allocation/Financial Risk. This module performs exactly
two kinds of new work: (1) a bounded, documented derivation of Expected
Return/Scenario ranges from `ValuationFinding.historical_yields` (itself
newly-exposed, not newly-computed -- see that field's own docstring),
and (2) a small, deterministic mapping from already-real categorical
findings onto a named `OutlookDriverKind` per horizon.

**Short-Term Expected Return -- valuation re-rating only, no forward
growth assumption.** `FCF_YIELD_RELATIVE` already relies on this
company's own historical FCF-yield range to classify
`UNDERVALUED`/`FAIRLY_VALUED`/`EXPENSIVE` (see `cash_flow.py`'s own
module docstring); this module quantifies the *same* assumption the
evaluator already makes, rather than inventing a new one.
`current_yield`/`historical_yields` are both FCF ÷ market_cap ratios for
the same, unchanged, most-recent Free Cash Flow fact, so `market_cap`
cancels out of their ratio: reverting to a target historical yield
`Y_target` implies `return = (current_yield / Y_target) - 1` regardless
of the company's actual price, share count, or FCF magnitude -- no
forward earnings, margin, or reinvestment assumption enters this
calculation at all. `Bull` reverts to this company's own lowest recorded
yield (its richest historical valuation -- the best real re-rating
outcome); `Bear` reverts to its highest recorded yield (its cheapest
historical valuation); `Base` reverts to the median. All three, and the
headline range they define, are always `None`/empty together, exactly
when `historical_yields` is empty (fewer than two valid market
observations) or the method itself never reached `FCF_YIELD_RELATIVE` a
real yield at all -- this module never fabricates a range the underlying
evaluator itself could not support.

**Long-Term Expected Return and Scenarios (Long-Term Expected Return
v1) are a real, evidence-gated multi-year model, not a placeholder.**
See the "Long-Term Expected Return v1 addenda" section below for the
full derivation -- unlike a forecast, every forward assumption it makes
is drawn from this company's own realized history under an explicit
eligibility gate, never invented. `OutlookGapKind
.NO_DURABLE_GROWTH_TRAJECTORY` names the honest outcome when that gate
is not met, exactly as before this real model existed.

**Outlook Conviction is a bounded derivation of the existing, adopted
`ConvictionAssessment`, never a second, independent recomputation.**
Calling `conviction.calculate_conviction` a second time with
horizon-scoped arguments would require deciding what `evidence_coverage`
means for "Short-Term evidentiary robustness" specifically -- but that
parameter's one adopted meaning, throughout this codebase, is investor
Decision/Observation coverage (Business Evaluation's own
`EvidenceCoverageLevel`), not company-data availability. Silently
repurposing it to mean something else for Outlook would be exactly the
"silently reinterpret existing conviction fields" the sprint's own
instruction forbids. Instead, `_outlook_conviction` never exceeds
case-wide `conviction.level` (evidence that cannot support a confident
case-wide conclusion cannot support a more confident Outlook one), and
additionally caps to `ConvictionLevel.INSUFFICIENT_EVIDENCE` when this
horizon's own specific data requirement is unmet (a real historical
yield range for Short-Term; a conclusive Growth *and* Capital Allocation
read for Long-Term) -- a documented cap on an existing field, not a
reinterpretation of what it measures.

**Momentum and What Changed are deliberately absent from this module.**
Both need a comparison against a *previous* analytical snapshot
(`atlas.analysis_engine.investment_case_change.ChangeIntelligence`),
which does not exist yet at the point `pipeline.assemble_analysis`
builds a `CanonicalAnalysis` -- the same "Core computes, Alpha persists
and compares" boundary `investment_case_change.py`'s own module
docstring already documents. `derive_outlook_momentum` is exported here,
pure and real, so the one caller that already holds a `ChangeIntelligence`
(`atlas.alpha.investment_case.api.schemas`, exactly where
`thesis_change`/`latest_changes` are already read today) can apply it
without a second momentum concept existing anywhere. "What Changed"
needs no new function at all: `AtlasOutlookSection` already renders the
same, real, case-wide `latestChanges` feed shared across both horizons
(its own file header already documents this as deliberate, not a gap).

**Semantic Hardening Pass addenda (post-v1):**

- **This is a re-rating range, not a forecast.** `ExpectedReturnRange`/
  `OutlookScenario` still hold Free Cash Flow fixed and vary only the
  market's own multiple -- they say nothing about revenue, margin, or
  earnings changing over the horizon. The type/field names are
  unchanged (renaming them ripples through the API, the frontend, and
  every test for no computational benefit), but every render-facing
  surface (`atlas.alpha.investment_case.api.schemas`, the frontend)
  must present this as a *valuation-implied* range, never as "Atlas
  predicts this return" -- see those modules' own docstrings for the
  exact wording adopted.
- **`OutlookAssumption.observation_count`** is the size of
  `historical_yields` a range/scenario was built from, always
  disclosed. This is the module's chosen answer to "can extreme
  min/max observations mislead": min/max legitimately *can* include a
  one-off anomaly, a crisis-period quarter, or a structurally different
  regime, and this module has no principled, non-arbitrary way to
  detect any of those (no percentile cutoff or winsorization is
  introduced -- Phase-appropriate discipline, matching
  `capital_allocation.py`'s own refusal to invent an unjustified
  ratio). Disclosing the sample size instead lets a reader weigh a
  two-observation range differently from an eight-observation one,
  without this module silently deciding for them.
- **`OutlookMomentumKind.MIXED`** is real, not collapsed into `STABLE`
  -- a genuinely mixed underlying trajectory (some dimensions
  strengthening, others weakening) is a different fact from a
  genuinely unchanged one, and `derive_outlook_momentum` now preserves
  that distinction (see its own docstring).

**Long-Term Expected Return v1 addenda (post-Semantic-Hardening):**

Answers exactly one question: "if this business develops approximately
as its own recent, real history suggests, and today's valuation
normalizes toward this company's own typical historical level, what
return range does today's price imply over 3-5 years?" Not a forecast,
not a price target, not probability-weighted.

**No Business Quality/Durability signal exists to gate on.** Every
`BusinessCategory` except Growth and Capital Allocation is permanently
`INSUFFICIENT_INPUT` in this codebase (Durability has no evaluator at
all -- re-confirmed this sprint, not assumed from a prior one). The
substitute eligibility gate is `_business_trajectory_eligible`: Growth's
own full-history status is not `WEAK`, **and** both Revenue's and Free
Cash Flow's most recent `_RECENT_WINDOW_SIZE`-period trend
(`growth.classify_metric_trend`, reused verbatim -- Revenue's via
`synthesis.growth.recent_trend`, already computed; FCF's newly computed
here the identical way) are `STRONG_METRIC`, **and** Financial Risk is
not `HIGH`. This is a real, disclosed proxy for "recent, durable
positive trajectory with no contradicting evidence" -- Part 4's own
example condition, applied with the only real signals available, never
silently presented as if it read a genuine Business Quality/Durability
finding.

**The growth assumption is a realized-history range, never an
extrapolated point.** Given eligibility, every consecutive-period FCF
growth rate across the company's *full* available history is computed
(`_realized_growth_rates`; a rate is only computed between two positive
values, mirroring `cash_flow.py`'s own refusal to compute a yield from
non-positive Free Cash Flow -- a rate spanning a zero-or-negative value
inverts into a sign that means nothing for forward compounding). Bear
uses the minimum realized rate, Base the median, Bull the maximum --
the exact same "historical distribution as range, never collapsed to a
point" discipline Short-Term already established for FCF yield, applied
here to FCF growth instead. Revenue growth is computed identically and
disclosed as a corroborating Key Driver, but does not enter the return
arithmetic directly -- one growth lever (FCF) drives the compounding,
avoiding two independently-uncertain growth rates compounding into a
false-precision combination.

**Margins and share count are deliberately excluded from the return
math.** Margin: no principled forward-expansion rule exists (Part 6's
own instruction: hold flat or omit; this module omits it entirely
rather than assert an unstated flat assumption inside a formula).
Share count: real, multi-period `SHARES_OUTSTANDING` history exists,
but inspecting real AAPL data during this sprint found undetected stock
-split discontinuities (a ~7x jump between consecutive periods) that
would corrupt any naive CAGR into a fabricated "massive dilution"
signal with no principled, non-arbitrary way to detect or correct a
split boundary. Excluded from v1's return arithmetic for exactly this
reason; capital allocation's real (buyback-vs-issuance, debt trend)
signals still populate Key Drivers, informationally, unaffected.

**Terminal valuation reuses the same historical FCF-yield distribution
as Short-Term, but conservatively: the median only, shared across all
three scenarios, never the historical extremes.** Part 8's own demand
is to test regime comparability before treating history as
interchangeable with a future terminal valuation; this module has no
mechanism to assess whether the historical regime that produced the
*extremes* is comparable to the business 3-5 years out, so it never
uses them for the terminal assumption. The median is the least extreme,
most defensible single terminal yield available given that limitation.
Scenarios therefore differ on one real, coherent, disclosed business
assumption (the FCF growth rate) -- never a second, undisclosed swing
in the terminal multiple -- directly satisfying Part 11's "no Bull =
highest number, Bear = lowest number" rule.

**The return formula, like Short-Term's, reduces to a pure ratio --
Free Cash Flow, price, and share count never need to be read as
absolute dollar figures.** `current_yield`/`terminal_yield` already
encode the entire current-vs-future market-cap relationship; compounding
a real growth rate `g` over `years` and re-rating from `current_yield`
to `terminal_yield` gives a total-return multiple of
`((1+g)**years) * (current_yield/terminal_yield)`, annualized as that
multiple's own `years`-th root minus one. `years` is fixed at
`LONG_TERM_COMPOUNDING_YEARS` (documented, not hidden) as the single
internal compounding duration within the stated 3-5-year range shown to
the reader via `horizon_months_low`/`horizon_months_high` -- Part 10's
own "prefer representing the range consistently... document clearly
if an exact duration is needed internally."

**Basis is `ANNUALIZED`, never `CUMULATIVE`, for Long-Term** -- the
opposite of Short-Term's `CUMULATIVE` re-rating-only figure, and always
explicit on `ExpectedReturnRange.basis` per Part 9's own instruction
never to let a caller infer it.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, replace as _dataclass_replace
from datetime import datetime
from enum import Enum

from atlas.analysis_engine.business_contracts import BusinessAnalysisResult, BusinessCategory
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus as BizStatus
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.conviction import ConvictionAssessment, ConvictionLevel
from atlas.analysis_engine.growth import MetricTrend, classify_metric_trend
from atlas.analysis_engine.investment_case_change import ThesisImpact
from atlas.analysis_engine.investment_case_synthesis import InvestmentCaseSynthesis
from atlas.analysis_engine.risk.contracts import RiskStatus
from atlas.analysis_engine.risk.models import RiskAnalysisResult
from atlas.analysis_engine.valuation.contracts import ValuationMethodKind
from atlas.analysis_engine.valuation.contracts import ValuationStatus as ValStatus
from atlas.analysis_engine.valuation.models import ValuationEngineResult

__all__ = [
    "OutlookHorizon",
    "ReturnBasis",
    "OutlookGapKind",
    "OutlookAssumptionKind",
    "OutlookAssumption",
    "ExpectedReturnRange",
    "ScenarioKind",
    "OutlookScenario",
    "OutlookMomentumKind",
    "OutlookDriverKind",
    "OutlookDriver",
    "DriverDirection",
    "HorizonOutlook",
    "Outlook",
    "build_outlook",
    "derive_outlook_momentum",
]

#: Short-Term's own approximate horizon, named once here rather than
#: scattered across call sites -- matches the sprint brief's own
#: "approximately 6-12 months" framing exactly. Structured (months, not
#: a free-text label) so a caller/frontend renders its own localized
#: label rather than parsing one.
SHORT_TERM_HORIZON_MONTHS = (6, 12)
#: Long-Term's own approximate horizon -- "approximately 3-5 years,"
#: expressed in months for the identical unit `ExpectedReturnRange`
#: already carries for Short-Term, so a caller never needs a second unit
#: system to compare the two.
LONG_TERM_HORIZON_MONTHS = (36, 60)
#: The single internal compounding duration Long-Term's return
#: arithmetic actually uses -- the midpoint of the stated 3-5-year
#: range, documented here rather than hidden inside a formula (Part 10).
#: The reader always sees the honest 3-5-year range via
#: `horizon_months_low`/`horizon_months_high`; this is only the exponent
#: the growth-compounding/annualization math needs internally.
LONG_TERM_COMPOUNDING_YEARS = 4
#: Mirrors `investment_case_synthesis._RECENT_WINDOW_SIZE` exactly --
#: the same "most recent N periods" window, reused for the identical
#: reason, applied to Free Cash Flow instead of Revenue (see
#: `_recent_fcf_trend`).
_RECENT_WINDOW_SIZE = 4


class OutlookHorizon(str, Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"


class ReturnBasis(str, Enum):
    """Never left implicit -- Part 4's own explicit instruction ("Do not
    allow the frontend to infer units"). Short-Term always constructs
    `CUMULATIVE` (a single re-rating event, not a repeating annual
    rate); Long-Term always constructs `ANNUALIZED` (a real multi-year
    compounding of a realized growth rate plus a terminal re-rating,
    smoothed to a single annual-equivalent figure) -- see
    `outlook.py`'s own module docstring for the exact derivation."""

    CUMULATIVE = "cumulative"
    ANNUALIZED = "annualized"


class OutlookGapKind(str, Enum):
    """Why an Expected Return range or a scenario set is honestly
    `None`/empty -- the same "named reason, never a silent gap"
    discipline every other closed gap taxonomy in this codebase already
    follows (`ValuationDataGapKind`, `BusinessDataGapKind`)."""

    NO_HISTORICAL_VALUATION_RANGE = "no_historical_valuation_range"
    """Fewer than two valid historical FCF-yield observations exist for
    this company -- there is nothing to build a re-rating range from.
    Mirrors `ValuationDataGapKind.INSUFFICIENT_HISTORICAL_VALUATION_PERIODS`
    one layer up."""
    VALUATION_NOT_CONCLUSIVE = "valuation_not_conclusive"
    """`FCF_YIELD_RELATIVE` itself has no current yield at all (missing
    market price, missing share count, missing Free Cash Flow, or a
    non-positive Free Cash Flow) -- there is no starting point to
    re-rate from."""
    NO_DURABLE_GROWTH_TRAJECTORY = "no_durable_growth_trajectory"
    """Long-Term's own eligibility gate (`_business_trajectory_eligible`)
    was not met: full-history Growth is `WEAK`, or Revenue's or Free Cash
    Flow's most recent `_RECENT_WINDOW_SIZE`-period trend is not
    `STRONG_METRIC`, or Financial Risk is `HIGH`, or fewer than two
    realized FCF growth-rate observations exist even once eligible (e.g.
    Free Cash Flow was never positive in two consecutive periods). This
    is a genuine, honest outcome -- a real company's own real historical
    volatility, not a modeling limitation -- and this module never
    loosens the gate or extrapolates through it to avoid reporting it."""


class OutlookAssumptionKind(str, Enum):
    """What kind of forward assumption underlies an Expected Return
    range or scenario -- always named, never implicit."""

    HISTORICAL_FCF_YIELD_REVERSION = "historical_fcf_yield_reversion"
    """The range assumes the market re-rates this company's FCF yield
    toward a point within its own recorded historical range, with the
    most recent known Free Cash Flow held fixed. No forward growth,
    discount-rate, or terminal-multiple assumption is made. Short-Term
    only."""

    HISTORICAL_GROWTH_WITH_TERMINAL_REVERSION = "historical_growth_with_terminal_reversion"
    """The range assumes Free Cash Flow compounds at a rate drawn from
    this company's own realized historical FCF growth-rate distribution
    (`growth_rate`) for `horizon_years`, and that the market then values
    that larger Free Cash Flow at this company's own historical median
    FCF yield (`target_fcf_yield`, held constant across Bull/Base/Bear --
    see this module's own docstring for why). Long-Term only."""


@dataclass(frozen=True)
class OutlookAssumption:
    """Fully structured, fully numeric -- no free-text "why" field,
    matching this codebase's own "status is the conclusion" discipline.
    A caller renders language from `kind` plus these real numbers,
    never from a string this module wrote.

    `observation_count` (Semantic Hardening Pass) is how many valid
    historical FCF-yield observations `target_fcf_yield` was drawn
    from -- always the full `len(historical_yields)`, identical across
    a horizon's Bull/Base/Bear/range assumptions since all three read
    the same set. Disclosed rather than filtered: see this module's own
    docstring for why a small sample (and therefore a `target_fcf_yield`
    that could be a single anomalous, crisis-period, or structurally
    incomparable observation) is surfaced as a real number for the
    reader to weigh, not silently trusted or silently suppressed.

    `growth_rate`/`horizon_years`/`growth_observation_count` (Long-Term
    Expected Return v1) are `None` for every Short-Term assumption --
    Short-Term makes no growth assumption at all -- and always populated
    together for Long-Term. `growth_observation_count` is the number of
    realized YoY FCF growth-rate observations the growth range was drawn
    from, the identical disclosure discipline `observation_count` already
    established for the yield distribution, applied to the growth
    distribution."""

    kind: OutlookAssumptionKind
    current_fcf_yield: float
    target_fcf_yield: float
    observation_count: int
    growth_rate: float | None = None
    horizon_years: int | None = None
    growth_observation_count: int | None = None


@dataclass(frozen=True)
class ExpectedReturnRange:
    """Part 4's own explicit requirements, all present: a real range
    (never a point), an explicit `basis` (never left for the frontend to
    infer), and an explicit horizon. `low_percent`/`high_percent` are
    fractional returns (e.g. `0.15` for +15%), consistent with
    `ValuationFinding.current_yield`'s own unit convention.

    **Semantic Hardening Pass: this is a valuation-implied re-rating
    range, not a forecast.** Free Cash Flow is held fixed at its most
    recent known value; only the market's own FCF multiple varies
    across `assumption.target_fcf_yield`. It says nothing about
    revenue, margin, or earnings changing over the horizon. Every
    render-facing caller (the API schema, the frontend) must present
    this under a label that says "valuation-implied" or "re-rating,"
    never bare "Expected Return" -- the field/class name here stays
    unchanged (a rename would ripple through the API and frontend for
    no computational benefit), but the *presented* concept is narrower
    than the name alone suggests, and every presentation layer must
    say so explicitly."""

    low_percent: float
    high_percent: float
    basis: ReturnBasis
    horizon_months_low: int
    horizon_months_high: int
    assumption: OutlookAssumption


class ScenarioKind(str, Enum):
    BULL = "bull"
    BASE = "base"
    BEAR = "bear"


@dataclass(frozen=True)
class OutlookScenario:
    """One named, assumption-based, non-probability-weighted scenario
    (Part 5). `return_percent` is this scenario's own single implied
    return -- the three scenarios' own values are exactly what define
    the headline `ExpectedReturnRange` above, so "a range, never a
    point" is satisfied at the range level without contradicting each
    scenario legitimately being one specific, named assumption's
    implied outcome.

    **Semantic Hardening Pass: these are valuation scenarios, not
    complete Bull/Base/Bear investment scenarios.** All three this
    sprint share `driver=OutlookDriverKind.VALUATION_RERATING` --
    nothing about the underlying business (growth, margin, capital
    allocation) differs between them, only the assumed target FCF
    yield does. `assumption` (never omitted) is what makes this
    honest: every render-facing caller must show it -- at minimum
    `assumption.target_fcf_yield` and `assumption.observation_count`
    -- next to `return_percent`, never the bare number alone, so a
    reader can see which specific yield this scenario assumed and
    how many historical observations that assumption drew from. A
    future sprint that differentiates Bull/Base/Bear by real business
    assumptions (not just valuation) should give that scenario a
    different `driver`, not leave it `VALUATION_RERATING` while
    quietly implying more."""

    kind: ScenarioKind
    return_percent: float
    assumption: OutlookAssumption
    driver: "OutlookDriverKind"


class OutlookMomentumKind(str, Enum):
    """Part 7's own candidate meaning, adopted verbatim: whether Atlas's
    own underlying view is strengthening, weakening, or stable --
    **never** stock-price or technical momentum (Part 7's own explicit
    prohibition). `MIXED` (Semantic Hardening Pass) is real, not folded
    into `STABLE` -- see `derive_outlook_momentum`'s own docstring."""

    STRENGTHENING = "strengthening"
    STABLE = "stable"
    WEAKENING = "weakening"
    MIXED = "mixed"
    UNAVAILABLE = "unavailable"


class OutlookDriverKind(str, Enum):
    """A closed, real set -- one member per already-computed categorical
    finding this module can honestly point to as a driver. No member
    here is ever constructed from a finding that is itself
    `INSUFFICIENT_INPUT`/`NOT_EVALUATED` (see `_drivers` below)."""

    VALUATION_RERATING = "valuation_rerating"
    REVENUE_TREND = "revenue_trend"
    GROWTH = "growth"
    CAPITAL_ALLOCATION = "capital_allocation"
    FINANCIAL_RISK = "financial_risk"
    BUSINESS_RISK = "business_risk"
    VALUATION_RISK = "valuation_risk"
    FCF_GROWTH_TREND = "fcf_growth_trend"
    """Long-Term only. The same recent-window `classify_metric_trend`
    read as `REVENUE_TREND`, applied to Free Cash Flow instead --
    Long-Term's real growth lever, disclosed as a driver in addition to
    (never instead of) the Revenue trend."""
    DEBT_TREND = "debt_trend"
    """Long-Term only. Full-history `classify_metric_trend` over
    `TOTAL_DEBT` -- informational corroboration for the capital
    structure Long-Term's return math otherwise excludes (see this
    module's own docstring on why share count is excluded from the
    arithmetic itself). Calibration Sprint: also the eligibility gate's
    balance-sheet-deterioration check -- see `_business_trajectory_eligible`."""
    MARGIN_TREND = "margin_trend"
    """Long-Term only (Calibration Sprint). Full-history
    `classify_metric_trend` over the OPERATING_INCOME/REVENUE ratio --
    informational corroboration only (Part 7's "smallest defensible
    role"): never a gate, never an input to the return arithmetic, never
    a projected forward expansion. A stable-or-improving margin trend is
    real, disclosed evidence that FCF volatility is more likely timing
    noise than eroding unit economics; it does not by itself change
    eligibility or the computed range."""
    MOAT = "moat"
    """Long-Term only (Calibration Phase 6). Never constructed by
    `build_outlook` itself -- this module cannot import
    `atlas.alpha.business_quality_assessment` (the same one-way Core/
    alpha boundary Conviction's own `is_thesis_stale` parameter already
    respects). Constructed one layer up, by
    `atlas.alpha.business_quality_assessment.derive_outlook_quality
    _drivers`, from that package's own real `MoatAssessment.level` --
    reused here purely as a shared, closed-vocabulary type so the
    alpha-layer-computed driver and every Core-computed driver above
    serialize into one consistent `key_drivers` list. Informational
    only, exactly like `CAPITAL_ALLOCATION` above: never a gate, never
    an input to the return arithmetic."""
    REINVESTMENT_OPPORTUNITY = "reinvestment_opportunity"
    """Long-Term only (Calibration Phase 6). Same boundary and reuse
    pattern as `MOAT` above, from that package's own real
    `ReinvestmentAssessment.level`. Informational only."""


class DriverDirection(str, Enum):
    """Reuses the identical three-way vocabulary
    `investment_case_change.ChangeDirection` already established for the
    same "never a numeric score" reason -- not imported directly only
    because that type's own docstring scopes it to *changes between two
    snapshots*, a different concept from "which way does this
    already-known finding point," even though the values are the same
    shape.

    Public (Calibration Phase 6) so `atlas.alpha.business_quality
    _assessment.derive_outlook_quality_drivers` can construct real
    `OutlookDriver`s of kind `MOAT`/`REINVESTMENT_OPPORTUNITY` without
    reinventing this vocabulary one layer up -- the same "widen an
    existing module's public surface, not a new module" precedent
    `investment_case_synthesis.derive_case_open_questions`'s own
    promotion already established."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class OutlookDriver:
    kind: OutlookDriverKind
    direction: DriverDirection
    source_finding_id: str | None


@dataclass(frozen=True)
class HorizonOutlook:
    horizon: OutlookHorizon
    expected_return: ExpectedReturnRange | None
    expected_return_gap: OutlookGapKind | None
    scenarios: tuple[OutlookScenario, ...]
    scenarios_gap: OutlookGapKind | None
    conviction: ConvictionLevel
    """"Outlook Conviction" -- see `_outlook_conviction`'s own
    docstring for the exact rule. Precisely: case-wide
    `ConvictionAssessment.level`, capped to `INSUFFICIENT_EVIDENCE`
    when this horizon's own data requirement is unmet, never
    otherwise recomputed. Not an independently modeled per-horizon
    Conviction -- every render-facing caller must say so (a short,
    fixed disclosure next to the value, not buried in a tooltip only),
    per the Semantic Hardening Pass."""
    momentum: OutlookMomentumKind
    key_drivers: tuple[OutlookDriver, ...]

    def __post_init__(self) -> None:
        if (self.expected_return is None) != (self.expected_return_gap is not None):
            raise ValueError("HorizonOutlook must carry exactly one of expected_return/expected_return_gap.")
        if (not self.scenarios) != (self.scenarios_gap is not None):
            raise ValueError("HorizonOutlook must carry exactly one of scenarios/scenarios_gap.")


@dataclass(frozen=True)
class Outlook:
    short_term: HorizonOutlook
    long_term: HorizonOutlook
    generated_at: datetime


def _rerating_return(current_yield: float, target_yield: float) -> float:
    """`market_cap = FCF / yield`, and `FCF` is unchanged between
    `current_yield` and any historical yield being reverted to (both are
    ratios against the identical, most recent Free Cash Flow fact) -- so
    `FCF` cancels out of the ratio of the two implied market caps,
    leaving a return expressible from the two yields alone, independent
    of the company's actual price, share count, or FCF magnitude. See
    this module's own docstring for the full derivation."""
    return (current_yield / target_yield) - 1.0


def _short_term_valuation(
    fcf_finding_current_yield: float | None,
    historical_yields: tuple[float, ...],
) -> tuple[ExpectedReturnRange | None, OutlookGapKind | None, tuple[OutlookScenario, ...], OutlookGapKind | None]:
    if fcf_finding_current_yield is None:
        gap = OutlookGapKind.VALUATION_NOT_CONCLUSIVE
        return None, gap, (), gap
    if len(historical_yields) < 2:
        gap = OutlookGapKind.NO_HISTORICAL_VALUATION_RANGE
        return None, gap, (), gap

    current_yield = fcf_finding_current_yield
    low_yield = min(historical_yields)
    high_yield = max(historical_yields)
    median_yield = statistics.median(historical_yields)

    def _assumption(target_yield: float) -> OutlookAssumption:
        return OutlookAssumption(
            kind=OutlookAssumptionKind.HISTORICAL_FCF_YIELD_REVERSION,
            current_fcf_yield=current_yield,
            target_fcf_yield=target_yield,
            observation_count=len(historical_yields),
        )

    #: Lower yield <-> richer valuation <-> higher implied price, so
    #: reverting toward the *lowest* recorded yield is the Bull case;
    #: reverting toward the *highest* is Bear. See `_rerating_return`'s
    #: own docstring for the underlying market-cap identity.
    bull_return = _rerating_return(current_yield, low_yield)
    base_return = _rerating_return(current_yield, median_yield)
    bear_return = _rerating_return(current_yield, high_yield)

    scenarios = (
        OutlookScenario(
            kind=ScenarioKind.BULL,
            return_percent=bull_return,
            assumption=_assumption(low_yield),
            driver=OutlookDriverKind.VALUATION_RERATING,
        ),
        OutlookScenario(
            kind=ScenarioKind.BASE,
            return_percent=base_return,
            assumption=_assumption(median_yield),
            driver=OutlookDriverKind.VALUATION_RERATING,
        ),
        OutlookScenario(
            kind=ScenarioKind.BEAR,
            return_percent=bear_return,
            assumption=_assumption(high_yield),
            driver=OutlookDriverKind.VALUATION_RERATING,
        ),
    )

    expected_return = ExpectedReturnRange(
        low_percent=min(bull_return, base_return, bear_return),
        high_percent=max(bull_return, base_return, bear_return),
        basis=ReturnBasis.CUMULATIVE,
        horizon_months_low=SHORT_TERM_HORIZON_MONTHS[0],
        horizon_months_high=SHORT_TERM_HORIZON_MONTHS[1],
        assumption=_assumption(median_yield),
    )
    return expected_return, None, scenarios, None


def _facts_sorted(business_facts: tuple[BusinessFact, ...], kind: BusinessFactKind) -> list[BusinessFact]:
    return sorted((f for f in business_facts if f.kind is kind), key=lambda f: f.period)


def _recent_trend(facts_sorted_asc: list[BusinessFact]) -> MetricTrend | None:
    """Identical shape to `investment_case_synthesis._recent_revenue_trend`,
    applied to whatever `kind` the caller already filtered/sorted by --
    see that function's own precedent for the `_RECENT_WINDOW_SIZE`
    window and the `< 2` insufficiency check."""
    recent = facts_sorted_asc[-_RECENT_WINDOW_SIZE:]
    if len(recent) < 2:
        return None
    trend, _supporting, _contradicting = classify_metric_trend(recent)
    return trend


def _rolling_cagr_observations(
    facts_sorted_asc: list[BusinessFact], *, years: int
) -> tuple[tuple[str, str, float], ...]:
    """Calibration Sprint: replaces the old single-period YoY delta with
    a rolling `years`-period CAGR -- `(start_period, end_period, rate)`
    for every pair of facts exactly `years` apart in the sorted sequence
    where both are positive (same non-positive-value exclusion as
    Short-Term's own yield math, for the same "do not invert into a
    meaningless sign" reason). A single noisy year can no longer swing
    the whole distribution the way a raw YoY delta could -- each
    observation already smooths `years` worth of working-capital/capex
    /timing noise, the same horizon the forward range itself compounds
    over, so the comparison is apples-to-apples."""
    observations: list[tuple[str, str, float]] = []
    for i in range(len(facts_sorted_asc) - years):
        start, end = facts_sorted_asc[i], facts_sorted_asc[i + years]
        if start.value > 0 and end.value > 0:
            rate = (end.value / start.value) ** (1.0 / years) - 1.0
            observations.append((start.period, end.period, rate))
    return tuple(observations)


def _revenue_periods(revenue_facts_sorted_asc: list[BusinessFact]) -> frozenset[str]:
    return frozenset(f.period for f in revenue_facts_sorted_asc)


def _revenue_corroborated_growth_rates(
    fcf_cagr_observations: tuple[tuple[str, str, float], ...], revenue_periods: frozenset[str]
) -> tuple[float, ...]:
    """Part 4/6's real, non-arbitrary answer to "extreme historical
    growth can be mathematically correct but economically indefensible":
    a rolling FCF CAGR window is only used as a forward assumption when
    Revenue -- the structurally steadier of the two real metrics this
    company reports -- has an *actual reported fact at both endpoints*
    of that same rolling span. This is not a percentile cutoff, winsorization,
    or invented "reasonable maximum growth": it is the direct, literal
    meaning of "corroborated by real evidence." Deliberately an exact
    per-period membership check, not an earliest-to-latest bounds check
    -- this codebase's own real ingestion has genuine multi-year Revenue
    gaps (MSFT's real 2011-2015 stretch, discovered during this
    Calibration Sprint's own live verification) where Free Cash Flow was
    still captured; a bounds check would silently treat an FCF window
    spanning that exact gap as "corroborated" when no Revenue evidence
    for those specific years exists at all. An ancient hypergrowth
    -launch-era FCF window with no contemporaneous Revenue fact (AAPL's
    own pre-2016 Revenue ingestion gap is exactly this shape) is excluded
    because there is nothing to corroborate it with, not because the
    number looked too large. Revenue's own growth rate is never blended
    into the FCF rate -- only its *presence* at the window's endpoints
    gates which FCF observations are trustworthy (Part 6's "preserve the
    tension, do not average" instruction)."""
    return tuple(
        rate for start, end, rate in fcf_cagr_observations if start in revenue_periods and end in revenue_periods
    )


def _business_trajectory_eligible(
    *,
    growth_status: BizStatus,
    debt_trend: MetricTrend | None,
    corroborated_observation_count: int,
) -> bool:
    """Calibration Sprint eligibility gate -- replaces the v1 condition
    (both Revenue's and Free Cash Flow's own recent window
    `STRONG_METRIC`) after Part 1's own adversarial test proved that
    condition was not economically justified: real AAPL and MSFT history
    shows genuinely durable, high-quality businesses with non-monotonic
    recent Free Cash Flow driven by capex cycles and working-capital
    timing, not deteriorating cash-generation capacity (see this
    module's own docstring). Three real, evidence-based conditions,
    still the only real proxy for the Business Quality/Durability
    finding this codebase has no evaluator for -- never presented as one:

    1. Full-history Growth status is not `WEAK` -- the same floor v1
       used, unchanged. A `WEAK` classification means *both* Revenue and
       Free Cash Flow contracted in every period on record; no
       corroboration mechanism should override a business that has never
       once grown on either metric.
    2. `TOTAL_DEBT`'s own full-history trend is not `STRONG_METRIC`
       (consistently, monotonically escalating every period) -- a
       narrower, more precise signal than the old blanket "Financial
       Risk not HIGH" condition, which conflated genuine balance-sheet
       deterioration with a deliberate capital-allocation *choice*
       (`financial_risk.py`'s own `capital_allocation_signal: WEAK ->
       HIGH` rule fires for a company that is a net debt-funded share
       repurchaser, real behavior real mega-caps exhibit deliberately,
       not a distress signal on its own). Reuses `debt_trend_signal`'s
       own already-adopted classification verbatim -- never a second
       trend algorithm.
    3. At least two revenue-corroborated rolling-CAGR observations exist
       (`_revenue_corroborated_growth_rates`) -- the same "at least two"
       floor Short-Term already requires of its own historical-yield
       range, reused rather than a new number invented for this gate."""
    if growth_status is BizStatus.WEAK:
        return False
    if debt_trend is MetricTrend.STRONG_METRIC:
        return False
    if corroborated_observation_count < 2:
        return False
    return True


def _annualized_return(*, current_yield: float, terminal_yield: float, growth_rate: float, years: int) -> float:
    """`((1+g)**years) * (current_yield/terminal_yield)` is the total
    -return multiple; its own `years`-th root minus one annualizes it.
    `total_multiple` is provably positive given this module's own
    construction (`current_yield`/`terminal_yield` are always positive
    FCF-yield ratios; `growth_rate` is always `> -1.0` since
    `_rolling_cagr_observations` only ever divides two positive values),
    so the `<= 0` branch below is defensive documentation, not a
    reachable path -- kept for the same reason `cash_flow.py` still
    guards already-impossible-by-construction states explicitly."""
    total_multiple = ((1.0 + growth_rate) ** years) * (current_yield / terminal_yield)
    if total_multiple <= 0:
        return -1.0
    return total_multiple ** (1.0 / years) - 1.0


def _exclude_future_dated(facts_sorted_asc: list[BusinessFact], *, as_of: datetime) -> list[BusinessFact]:
    """Calibration Sprint: a `period` ending after `as_of` cannot be a
    *realized* historical observation by definition -- there is no
    principled sense in which "realized growth" can include a period
    that has not happened yet. Not an arbitrary cutoff: a real
    data-integrity bug surfaced during this sprint's own live AAPL
    verification (a stray test record with `period_end=2027-09-26`,
    dated more than a year past `generated_at`, sitting in the same
    production database every other live check in this program has
    used) silently inflated one rolling-CAGR observation's endpoint.
    This guard makes that class of contamination structurally
    unable to reach the growth-rate math, independent of whether the
    contaminating record itself is ever cleaned up."""
    cutoff = as_of.date().isoformat()
    return [f for f in facts_sorted_asc if f.period <= cutoff]


def _long_term_valuation(
    *,
    growth_status: BizStatus,
    business_facts: tuple[BusinessFact, ...],
    debt_trend: MetricTrend | None,
    fcf_finding_current_yield: float | None,
    historical_yields: tuple[float, ...],
    generated_at: datetime,
) -> tuple[
    ExpectedReturnRange | None,
    OutlookGapKind | None,
    tuple[OutlookScenario, ...],
    OutlookGapKind | None,
    MetricTrend | None,
]:
    """Long-Term Expected Return, Calibration Sprint. Returns
    `(expected_return, expected_return_gap, scenarios, scenarios_gap,
    recent_fcf_trend)` -- `recent_fcf_trend` is returned alongside
    (informational only, post-calibration -- see
    `_business_trajectory_eligible`'s own docstring for why it no longer
    gates) so `build_outlook` can pass it into `_long_term_drivers`
    without recomputing. See this module's own Calibration Sprint
    docstring addenda for the full derivation (eligibility gate,
    revenue-corroborated rolling-CAGR range, median terminal yield, the
    return formula -- unchanged from v1)."""
    fcf_facts = _exclude_future_dated(
        _facts_sorted(business_facts, BusinessFactKind.FREE_CASH_FLOW), as_of=generated_at
    )
    revenue_facts = _exclude_future_dated(
        _facts_sorted(business_facts, BusinessFactKind.REVENUE), as_of=generated_at
    )
    recent_fcf_trend = _recent_trend(fcf_facts)

    years = LONG_TERM_COMPOUNDING_YEARS
    fcf_cagr_observations = _rolling_cagr_observations(fcf_facts, years=years)
    revenue_periods = _revenue_periods(revenue_facts)
    corroborated_rates = _revenue_corroborated_growth_rates(fcf_cagr_observations, revenue_periods)

    eligible = _business_trajectory_eligible(
        growth_status=growth_status,
        debt_trend=debt_trend,
        corroborated_observation_count=len(corroborated_rates),
    )
    if not eligible:
        gap = OutlookGapKind.NO_DURABLE_GROWTH_TRAJECTORY
        return None, gap, (), gap, recent_fcf_trend

    if fcf_finding_current_yield is None:
        gap = OutlookGapKind.VALUATION_NOT_CONCLUSIVE
        return None, gap, (), gap, recent_fcf_trend
    if len(historical_yields) < 2:
        gap = OutlookGapKind.NO_HISTORICAL_VALUATION_RANGE
        return None, gap, (), gap, recent_fcf_trend

    current_yield = fcf_finding_current_yield
    terminal_yield = statistics.median(historical_yields)

    growth_low = min(corroborated_rates)
    growth_median = statistics.median(corroborated_rates)
    growth_high = max(corroborated_rates)

    def _assumption(growth_rate: float) -> OutlookAssumption:
        return OutlookAssumption(
            kind=OutlookAssumptionKind.HISTORICAL_GROWTH_WITH_TERMINAL_REVERSION,
            current_fcf_yield=current_yield,
            target_fcf_yield=terminal_yield,
            observation_count=len(historical_yields),
            growth_rate=growth_rate,
            horizon_years=years,
            growth_observation_count=len(corroborated_rates),
        )

    def _return_for(growth_rate: float) -> float:
        return _annualized_return(
            current_yield=current_yield, terminal_yield=terminal_yield, growth_rate=growth_rate, years=years
        )

    #: Higher realized FCF growth is unambiguously the Bull case here --
    #: unlike Short-Term's yield-only scenarios, growth and terminal
    #: yield are not the same lever, so there is no valuation-direction
    #: inversion to account for (contrast `_short_term_valuation`'s own
    #: comment on why its own low/high yield mapping is inverted).
    bull_return = _return_for(growth_high)
    base_return = _return_for(growth_median)
    bear_return = _return_for(growth_low)

    scenarios = (
        OutlookScenario(
            kind=ScenarioKind.BULL,
            return_percent=bull_return,
            assumption=_assumption(growth_high),
            driver=OutlookDriverKind.FCF_GROWTH_TREND,
        ),
        OutlookScenario(
            kind=ScenarioKind.BASE,
            return_percent=base_return,
            assumption=_assumption(growth_median),
            driver=OutlookDriverKind.FCF_GROWTH_TREND,
        ),
        OutlookScenario(
            kind=ScenarioKind.BEAR,
            return_percent=bear_return,
            assumption=_assumption(growth_low),
            driver=OutlookDriverKind.FCF_GROWTH_TREND,
        ),
    )

    expected_return = ExpectedReturnRange(
        low_percent=min(bull_return, base_return, bear_return),
        high_percent=max(bull_return, base_return, bear_return),
        basis=ReturnBasis.ANNUALIZED,
        horizon_months_low=LONG_TERM_HORIZON_MONTHS[0],
        horizon_months_high=LONG_TERM_HORIZON_MONTHS[1],
        assumption=_assumption(growth_median),
    )
    return expected_return, None, scenarios, None, recent_fcf_trend


def _status_direction_business(status: BizStatus) -> DriverDirection | None:
    return {
        BizStatus.STRONG: DriverDirection.POSITIVE,
        BizStatus.MODERATE: DriverDirection.NEUTRAL,
        BizStatus.WEAK: DriverDirection.NEGATIVE,
    }.get(status)


def _status_direction_risk(status: RiskStatus) -> DriverDirection | None:
    #: Higher risk is the adverse direction -- mirrors
    #: `investment_case_change._risk_category_changes`'s own
    #: "higher rank = closer to HIGH = worse" rule exactly.
    return {
        RiskStatus.LOW: DriverDirection.POSITIVE,
        RiskStatus.MODERATE: DriverDirection.NEUTRAL,
        RiskStatus.HIGH: DriverDirection.NEGATIVE,
    }.get(status)


def _trend_direction(trend: MetricTrend) -> DriverDirection:
    return {
        MetricTrend.STRONG_METRIC: DriverDirection.POSITIVE,
        MetricTrend.WEAK_METRIC: DriverDirection.NEGATIVE,
        MetricTrend.MIXED_METRIC: DriverDirection.NEUTRAL,
    }[trend]


def _short_term_drivers(
    *,
    fcf_status: ValStatus,
    fcf_finding_id: str,
    synthesis: InvestmentCaseSynthesis,
    financial_risk_status: RiskStatus | None,
    financial_risk_finding_id: str | None,
) -> tuple[OutlookDriver, ...]:
    drivers: list[OutlookDriver] = []

    if fcf_status not in (ValStatus.NOT_EVALUATED, ValStatus.INSUFFICIENT_INPUT):
        direction = {
            ValStatus.UNDERVALUED: DriverDirection.POSITIVE,
            ValStatus.EXPENSIVE: DriverDirection.NEGATIVE,
            ValStatus.FAIRLY_VALUED: DriverDirection.NEUTRAL,
        }[fcf_status]
        drivers.append(OutlookDriver(OutlookDriverKind.VALUATION_RERATING, direction, fcf_finding_id))

    recent_trend = synthesis.growth.recent_trend
    if recent_trend is not None:
        drivers.append(
            OutlookDriver(OutlookDriverKind.REVENUE_TREND, _trend_direction(recent_trend.trend), None)
        )

    if financial_risk_status is not None and financial_risk_status is not RiskStatus.INSUFFICIENT_INPUT:
        direction = _status_direction_risk(financial_risk_status)
        if direction is not None:
            drivers.append(OutlookDriver(OutlookDriverKind.FINANCIAL_RISK, direction, financial_risk_finding_id))

    return tuple(drivers)


def _operating_margin_trend(business_facts: tuple[BusinessFact, ...], *, generated_at: datetime) -> MetricTrend | None:
    """Calibration Sprint (Part 7): full-history `classify_metric_trend`
    over the OPERATING_INCOME/REVENUE ratio for every period where both
    are real facts -- informational only (see
    `OutlookDriverKind.MARGIN_TREND`'s own docstring for why this never
    gates or enters the arithmetic). Synthesizes a same-period margin
    "fact" purely for the classifier's own consecutive-delta comparison;
    no persisted `BusinessFact` of this derived kind exists anywhere
    else, so its `id`/`source_record_id`/`provenance` are placeholders
    -- `classify_metric_trend` only reads `.value`/`.period`, and this
    function never surfaces the synthesized fact's identity fields to a
    caller (the driver it feeds carries `source_finding_id=None`, an
    explicit "no single evaluated Finding backs this" signal, exactly
    like `FCF_GROWTH_TREND`/`DEBT_TREND` already do)."""
    cutoff = generated_at.date().isoformat()
    revenue_by_period = {
        f.period: f.value for f in business_facts if f.kind is BusinessFactKind.REVENUE and f.period <= cutoff
    }
    op_income_by_period = {
        f.period: f.value
        for f in business_facts
        if f.kind is BusinessFactKind.OPERATING_INCOME and f.period <= cutoff
    }
    common_periods = sorted(set(revenue_by_period) & set(op_income_by_period))
    margin_facts = [
        _dataclass_replace(
            next(f for f in business_facts if f.kind is BusinessFactKind.REVENUE and f.period == period),
            kind=BusinessFactKind.OPERATING_INCOME,
            value=op_income_by_period[period] / revenue_by_period[period],
        )
        for period in common_periods
        if revenue_by_period[period] != 0
    ]
    if len(margin_facts) < 2:
        return None
    trend, _supporting, _contradicting = classify_metric_trend(margin_facts)
    return trend


def _long_term_drivers(
    *,
    growth_status: BizStatus,
    growth_finding_id: str,
    capital_allocation_status: BizStatus,
    capital_allocation_finding_id: str,
    business_risk_status: RiskStatus | None,
    business_risk_finding_id: str | None,
    valuation_risk_status: RiskStatus | None,
    valuation_risk_finding_id: str | None,
    fcf_status: ValStatus,
    fcf_finding_id: str,
    recent_fcf_trend: MetricTrend | None,
    debt_trend: MetricTrend | None,
    margin_trend: MetricTrend | None,
) -> tuple[OutlookDriver, ...]:
    drivers: list[OutlookDriver] = []

    if growth_status is not BizStatus.INSUFFICIENT_INPUT:
        direction = _status_direction_business(growth_status)
        if direction is not None:
            drivers.append(OutlookDriver(OutlookDriverKind.GROWTH, direction, growth_finding_id))

    if recent_fcf_trend is not None:
        drivers.append(OutlookDriver(OutlookDriverKind.FCF_GROWTH_TREND, _trend_direction(recent_fcf_trend), None))

    if capital_allocation_status is not BizStatus.INSUFFICIENT_INPUT:
        direction = _status_direction_business(capital_allocation_status)
        if direction is not None:
            drivers.append(
                OutlookDriver(OutlookDriverKind.CAPITAL_ALLOCATION, direction, capital_allocation_finding_id)
            )

    if debt_trend is not None:
        #: Inverted vs. `_trend_direction`: consistently *rising* debt
        #: (`STRONG_METRIC` under `classify_metric_trend`'s own
        #: all-positive-deltas definition) is the adverse direction here,
        #: mirroring `financial_risk.py`'s own escalation-only debt-trend
        #: read, not `_trend_direction`'s growth-is-good convention.
        debt_direction = {
            MetricTrend.STRONG_METRIC: DriverDirection.NEGATIVE,
            MetricTrend.WEAK_METRIC: DriverDirection.POSITIVE,
            MetricTrend.MIXED_METRIC: DriverDirection.NEUTRAL,
        }[debt_trend]
        drivers.append(OutlookDriver(OutlookDriverKind.DEBT_TREND, debt_direction, None))

    if margin_trend is not None:
        drivers.append(OutlookDriver(OutlookDriverKind.MARGIN_TREND, _trend_direction(margin_trend), None))

    if fcf_status not in (ValStatus.NOT_EVALUATED, ValStatus.INSUFFICIENT_INPUT):
        direction = {
            ValStatus.UNDERVALUED: DriverDirection.POSITIVE,
            ValStatus.EXPENSIVE: DriverDirection.NEGATIVE,
            ValStatus.FAIRLY_VALUED: DriverDirection.NEUTRAL,
        }[fcf_status]
        drivers.append(OutlookDriver(OutlookDriverKind.VALUATION_RERATING, direction, fcf_finding_id))

    if business_risk_status is not None and business_risk_status is not RiskStatus.INSUFFICIENT_INPUT:
        direction = _status_direction_risk(business_risk_status)
        if direction is not None:
            drivers.append(OutlookDriver(OutlookDriverKind.BUSINESS_RISK, direction, business_risk_finding_id))

    if valuation_risk_status is not None and valuation_risk_status is not RiskStatus.INSUFFICIENT_INPUT:
        direction = _status_direction_risk(valuation_risk_status)
        if direction is not None:
            drivers.append(OutlookDriver(OutlookDriverKind.VALUATION_RISK, direction, valuation_risk_finding_id))

    return tuple(drivers)


def _outlook_conviction(case_conviction: ConvictionAssessment, *, data_sufficient: bool) -> ConvictionLevel:
    """Never exceeds case-wide Conviction; forced to
    `INSUFFICIENT_EVIDENCE` when this horizon's own data requirement is
    unmet. See this module's own docstring for why this is a bounded
    derivation, not a second `calculate_conviction` call."""
    if not data_sufficient:
        return ConvictionLevel.INSUFFICIENT_EVIDENCE
    return case_conviction.level


def build_outlook(
    *,
    business_analysis: BusinessAnalysisResult,
    valuation_engine: ValuationEngineResult,
    risk_analysis: RiskAnalysisResult,
    conviction: ConvictionAssessment,
    synthesis: InvestmentCaseSynthesis,
    business_facts: tuple[BusinessFact, ...],
    generated_at: datetime,
) -> Outlook:
    """Deterministic: identical inputs always produce a deeply equal
    `Outlook`. Reads only already-computed stage results -- no
    `BusinessRecord`, no raw provider data, no wall-clock read beyond
    the caller-supplied `generated_at` every sibling stage already uses
    the same way. `business_facts` (Long-Term Expected Return v1) is the
    same already-extracted tuple `pipeline.assemble_analysis` already
    passes into Growth/Capital Allocation/Financial Risk/`synthesis` --
    re-read here for Long-Term's own recent-FCF-trend and realized
    -growth-rate computations, never re-extracted.

    `momentum` is always `OutlookMomentumKind.UNAVAILABLE` on the object
    this function returns -- see this module's own docstring for why,
    and `derive_outlook_momentum` for the caller-side function that
    fills it in once a `ChangeIntelligence` exists.
    """
    fcf_finding = next(f for f in valuation_engine.findings if f.kind is ValuationMethodKind.FCF_YIELD_RELATIVE)
    growth_finding = next(f for f in business_analysis.findings if f.kind is BusinessCategory.GROWTH)
    capital_allocation_finding = next(
        f for f in business_analysis.findings if f.kind is BusinessCategory.CAPITAL_ALLOCATION
    )
    financial_risk_finding = next(
        (f for f in risk_analysis.findings if f.category is RiskCategory.FINANCIAL_RISK), None
    )
    business_risk_finding = next((f for f in risk_analysis.findings if f.category is RiskCategory.BUSINESS_RISK), None)
    valuation_risk_finding = next(
        (f for f in risk_analysis.findings if f.category is RiskCategory.VALUATION_RISK), None
    )

    short_expected_return, short_return_gap, short_scenarios, short_scenarios_gap = _short_term_valuation(
        fcf_finding.current_yield, fcf_finding.historical_yields
    )
    short_drivers = _short_term_drivers(
        fcf_status=fcf_finding.status,
        fcf_finding_id=fcf_finding.id,
        synthesis=synthesis,
        financial_risk_status=financial_risk_finding.status if financial_risk_finding else None,
        financial_risk_finding_id=financial_risk_finding.id if financial_risk_finding else None,
    )
    short_term = HorizonOutlook(
        horizon=OutlookHorizon.SHORT_TERM,
        expected_return=short_expected_return,
        expected_return_gap=short_return_gap,
        scenarios=short_scenarios,
        scenarios_gap=short_scenarios_gap,
        conviction=_outlook_conviction(conviction, data_sufficient=short_expected_return is not None),
        momentum=OutlookMomentumKind.UNAVAILABLE,
        key_drivers=short_drivers,
    )

    debt_facts = _exclude_future_dated(_facts_sorted(business_facts, BusinessFactKind.TOTAL_DEBT), as_of=generated_at)
    debt_trend = None
    if len(debt_facts) >= 2:
        debt_trend, _supporting, _contradicting = classify_metric_trend(debt_facts)

    long_expected_return, long_return_gap, long_scenarios, long_scenarios_gap, recent_fcf_trend = (
        _long_term_valuation(
            growth_status=growth_finding.status,
            business_facts=business_facts,
            debt_trend=debt_trend,
            fcf_finding_current_yield=fcf_finding.current_yield,
            historical_yields=fcf_finding.historical_yields,
            generated_at=generated_at,
        )
    )
    margin_trend = _operating_margin_trend(business_facts, generated_at=generated_at)
    long_drivers = _long_term_drivers(
        growth_status=growth_finding.status,
        growth_finding_id=growth_finding.id,
        capital_allocation_status=capital_allocation_finding.status,
        capital_allocation_finding_id=capital_allocation_finding.id,
        business_risk_status=business_risk_finding.status if business_risk_finding else None,
        business_risk_finding_id=business_risk_finding.id if business_risk_finding else None,
        valuation_risk_status=valuation_risk_finding.status if valuation_risk_finding else None,
        valuation_risk_finding_id=valuation_risk_finding.id if valuation_risk_finding else None,
        fcf_status=fcf_finding.status,
        fcf_finding_id=fcf_finding.id,
        recent_fcf_trend=recent_fcf_trend,
        debt_trend=debt_trend,
        margin_trend=margin_trend,
    )
    long_term = HorizonOutlook(
        horizon=OutlookHorizon.LONG_TERM,
        expected_return=long_expected_return,
        expected_return_gap=long_return_gap,
        scenarios=long_scenarios,
        scenarios_gap=long_scenarios_gap,
        conviction=_outlook_conviction(conviction, data_sufficient=long_expected_return is not None),
        momentum=OutlookMomentumKind.UNAVAILABLE,
        key_drivers=long_drivers,
    )

    return Outlook(short_term=short_term, long_term=long_term, generated_at=generated_at)


def derive_outlook_momentum(thesis_impact: ThesisImpact | None, *, is_baseline: bool) -> OutlookMomentumKind:
    """Pure. `thesis_impact=None` (no `ChangeIntelligence` at all -- no
    snapshot repository wired) and `is_baseline=True` (this Case's first
    recorded analysis, nothing to compare against) both honestly produce
    `UNAVAILABLE` -- momentum describes a trajectory, and neither case
    has one yet.

    **Semantic Hardening Pass: `ThesisImpact.MIXED` maps to
    `OutlookMomentumKind.MIXED`, not `STABLE`.** `UNCHANGED` (genuinely
    no dimension moved) and `MIXED` (some dimensions strengthened, others
    weakened) are different underlying facts -- collapsing both onto
    `STABLE` would erase that difference for a reader deciding how much
    to trust the trajectory. No already-adopted rule resolves `MIXED`
    into a single direction (`investment_case_change._thesis_impact`'s
    own logic keeps it a distinct fourth outcome precisely because
    "one weakening component does NOT necessarily mean thesis
    invalidated" -- nor does it mean strengthened, nor unchanged), so
    this function preserves the same four-way distinction one level
    down rather than inventing a resolution rule that does not exist
    upstream."""
    if is_baseline or thesis_impact is None:
        return OutlookMomentumKind.UNAVAILABLE
    return {
        ThesisImpact.STRENGTHENED: OutlookMomentumKind.STRENGTHENING,
        ThesisImpact.WEAKENED: OutlookMomentumKind.WEAKENING,
        ThesisImpact.UNCHANGED: OutlookMomentumKind.STABLE,
        ThesisImpact.MIXED: OutlookMomentumKind.MIXED,
    }[thesis_impact]
