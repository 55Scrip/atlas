"""Direction Selector (`docs/atlas_decision_engine/DE-008-Direction-Selection.md`;
"Recommendation Backend Step 3"; `DE-016` "Recommendation Integration
Design"/implementation sprint).

The first executable Direction Selector -- the capability
`atlas.analysis_engine.recommendation`'s own module docstring has named,
since ATLAS-020, as "gap 1: no Direction selector exists." This module
now supports six outcomes: `RecommendationDirection.HOLD`, `.TRIM`,
`.NO_ACTION`, `.BUY`, `.ADD`, and `None` (RecommendationWithheld --
`DE-008` §1's "not a seventh direction"; `None` is the absence of a
`RecommendationDirection`, never a fourth enum-shaped value).

**`RecommendationDirection.EXIT` remains structurally unreachable from
this module.** Not by a runtime check, an exception, or a TODO -- there
is no branch below that constructs it. `DE-008` §1's EXIT row requires
"a *specific, named* thesis dependency has failed, or Business Evaluation
has reversed." Neither trigger has a real, sufficient signal in this
codebase today -- see "On EXIT" below for the full reasoning (an earlier
version of this module treated ordinary Counter-Evidence as sufficient;
that was a genuine semantic error, found and corrected during pre-commit
review, not a design choice). When a real thesis-invalidation signal is
eventually built, EXIT becomes reachable by widening this module's own
logic, not by loosening `RecommendationDirection`'s definition.

**`RecommendationDirection.BUY`/`.ADD` are now genuinely reachable.**
`DE-008` §21 invariants 1/2 block both on **Valuation Support for Capital
Deployment** -- a prerequisite `DE-008` itself named but left
unspecified as a computable capability (`DE-008` §4, §24). `DE-015`
("Atlas Valuation Support Doctrine") closed that specification gap with
a real, computed `ValuationSupport.status`
(`atlas.analysis_engine.valuation.support`); the `DE-016` design sprint
proved the already-adopted `DE-008` matrix requires no amendment to
consume it -- only wiring. Per `DE-015` §18, this module reads only the
public `ValuationSupportStatus` enum (`SUPPORTED`/`NOT_SUPPORTED`/
`INSUFFICIENT_INPUT`) -- never `ValuationSupport.reasoning`, `.gap`, or
any of the private proof-path internals (scenario envelope, growth
observations, Net-Cash proof), which stay exactly as private as `DE-015`
requires (see `test_proof_boundary.py`).

`SUPPORTED` only ever *removes one blocking condition* inside the two
matrix cells `DE-008` §20 already marks as blocked purely by this missing
prerequisite (not-held: `UNDERVALUED`/`FAIRLY_VALUED` + no dampening;
held: `UNDERVALUED` + no dampening) -- it is read nowhere else in this
function, never overrides Business `WEAK`, never overrides dampening, and
never touches the already-independently-resolved `FAIRLY_VALUED`+held
(`HOLD`) or `EXPENSIVE` (`TRIM`/`NO_ACTION`) cells. `NOT_SUPPORTED` and
`INSUFFICIENT_INPUT` are deliberately not distinguished anywhere below --
both mean "the prerequisite is not established," identical to every
company's permanent state before `DE-015` was implemented (`DE-016`
Part 11: `DE-008` never names `NOT_SUPPORTED` as a TRIM/EXIT trigger, so
none is invented here).

**On EXIT.** The only candidate signal this codebase computes today for
"a thesis dependency has failed" is `ContradictionSummary
.observation_classifications` (`DE-002` §2.3's Counter-Evidence: at least
one Observation with real challenging Evidence linked to it) -- non-empty
whenever *any* Observation has been challenged at all, including a
`CONTRADICTED` Observation that also has supporting Evidence. This is
**not** a sufficient signal for thesis invalidation: `DE-004` §3's own
Medium-conviction pattern is *defined* as "genuine Counter-Evidence
exists and is not fully resolved" -- explicitly compatible with a
still-valid direction (HOLD, TRIM, or any other), not a forced EXIT.
Routing the identical fact to two different, contradictory conclusions
(a routine Medium-conviction qualifier everywhere else, an unconditional
kill-switch here) would be exactly the "hidden semantics" `DE-008`
exists to prevent. No other signal in this codebase distinguishes
"routine, still-open Counter-Evidence" from "the thesis has actually
failed" -- inventing that distinction (a count threshold, a severity
tier, a subset of `ObservationEpistemicStatus`) would itself be
fabricated doctrine, not an application of it. Until a real,
doctrine-grounded thesis-invalidation signal exists, EXIT stays
reserved-but-unreachable -- unlike BUY/ADD (see above), whose own missing
prerequisite (`DE-015`'s `ValuationSupport`) now exists.

**Pure derivation, nothing else.** `select_direction` reads only
already-computed analysis results, passed in as plain arguments -- the
caller is responsible for having already run Business Analysis, the
Valuation Engine, Risk, and Reasoning. This module:

- does not read `RecommendationResponse`, `HistoricalRecommendationSnapshot`,
  Execution Guidance, prior execution price, or the Investor's own
  `BUY/SELL/HOLD/WATCH/PASS` decision field (`DE-008` §16, §21 invariant
  10);
- does not compute Valuation -- `ValuationStatus` is an input, taken from
  the already-real `atlas.analysis_engine.valuation` pipeline, never
  recomputed here;
- does not compute Valuation Support for Capital Deployment --
  `ValuationSupportStatus` is an input, taken from the already-real
  `atlas.analysis_engine.valuation.support.evaluate_valuation_support`,
  never recomputed here, and only its public `status` is read (`DE-015`
  §18) -- never `.reasoning`, `.gap`, or any private proof-path content;
- does not compute Recommendation Conviction, and never branches on a
  Conviction *level* -- only on the same existence-floor facts
  (`EvaluationState` x4, `EvidenceCoverageLevel`)
  `recommendation_conviction.calculate_recommendation_conviction`
  independently checks for the identical reason (`DE-008` §4's hard
  gate). Checking the same primitive facts in two places is not a second
  Conviction computation: neither call reads the other's output, and
  neither ever inspects a Conviction *level* to decide anything
  (`DE-008` §21 invariant 8). This is why a caller can compute Direction
  and Conviction independently, in either order, and still never let one
  select the other;
- never mutates any input.

**Two categorical inputs this module derives itself**, documented as
their own small rule tables, because `DE-008` only ever speaks of a
monolithic "Business" column and a monolithic "Dampening" column, never
per-category `BusinessCategoryStatus` combination or per-source
dampening combination:

1. `_business_signal` -- combines the two `BusinessCategory` values this
   codebase can genuinely conclude today (`GROWTH`, `CAPITAL_ALLOCATION`;
   every other category is permanently `INSUFFICIENT_INPUT`/
   `NOT_EVALUATED`, see `atlas/analysis_engine/business.py`'s own module
   docstring) into one `_BusinessSignal`. See that function's own
   docstring for the three-rule table.
2. `dampening` -- `has_portfolio_dampening or
   has_high_financial_or_valuation_risk`, `DE-008` §12/§13's two named
   dampening sources, OR-combined per `DE-008` §10's own "reducing
   exposure can be triggered by ... Portfolio Context alone" structural
   rule. `has_portfolio_dampening` is always `False` at every real call
   site today -- `PortfolioFinding` (`atlas.decision_engine.contracts`)
   is permanently `INSUFFICIENT_INPUT` (Sprint 4 lock: no portfolio-wide
   data exists in `DecisionEngineInput` at all), so there is no honest
   portfolio-wide dampening signal to compute yet. The parameter exists,
   and is tested, so a future sprint that builds real Portfolio
   Intelligence factors only has to supply `True` sometimes, not widen
   this module's signature.

**One matrix gap `DE-008` does not enumerate, resolved here using
`DE-008`'s own reasoning tools, not a new principle:** when
`_business_signal` is `INSUFFICIENT` (neither Growth nor Capital
Allocation reaches a real conclusion), or when `valuation_status` is
`NOT_EVALUATED`/`INSUFFICIENT_INPUT` while Business is `POSITIVE` (the
matrix needs to know which of the three real `ValuationStatus` values
applies to pick a row), `select_direction` returns `None`
(RecommendationWithheld) rather than guessing. This is a direct
application of `DE-008` §19's own governing test: an "unknown, not yet
computed" Business or Valuation conclusion is not real, case-specific
evidence for any particular direction -- asserting `WEAK`, `POSITIVE`, or
a specific `ValuationStatus` here would be exactly the fabrication
`DE-004` §4 and this module's own "never fabricate missing information"
instruction forbid. This is structurally distinct from `DE-008`'s own
UNDERVALUED-blocks-BUY/ADD gap (a *known* Valuation Evidence value that
is insufficient for a *specific* direction) -- here there is no known
value to reason from at all.

"""
from __future__ import annotations

from enum import Enum

from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
from atlas.analysis_engine.recommendation import RecommendationDirection
from atlas.analysis_engine.valuation.contracts import ValuationStatus
from atlas.analysis_engine.valuation.support import ValuationSupportStatus
from atlas.decision_engine.contracts import EvaluationState, EvidenceCoverageLevel, HoldingLinkage

__all__ = ["select_direction"]


class _BusinessSignal(str, Enum):
    """Not part of this module's public surface -- `DE-008` never names a
    per-category Business aggregate; this is the minimal, internal
    combination `select_direction` needs from the two real
    `BusinessCategoryStatus` conclusions this codebase can produce today
    (`GROWTH`, `CAPITAL_ALLOCATION`)."""

    WEAK = "weak"
    POSITIVE = "positive"
    INSUFFICIENT = "insufficient"


_INCONCLUSIVE_BUSINESS_STATUSES = (
    BusinessCategoryStatus.NOT_EVALUATED,
    BusinessCategoryStatus.INSUFFICIENT_INPUT,
)

_INCONCLUSIVE_VALUATION_STATUSES = (
    ValuationStatus.NOT_EVALUATED,
    ValuationStatus.INSUFFICIENT_INPUT,
)

_NO_EVIDENCE_COVERAGE = (EvidenceCoverageLevel.NOT_APPLICABLE, EvidenceCoverageLevel.NONE)


def _business_signal(
    growth_status: BusinessCategoryStatus, capital_allocation_status: BusinessCategoryStatus
) -> _BusinessSignal:
    """Documented before use, `thesis_risk.py`/`business_risk.py`'s own
    convention. In this fixed order, first match wins:

    1. Either category is `WEAK` -> `WEAK`. A single genuine weakness is
       real, case-specific negative evidence -- the same "any negative
       signal is independently sufficient for caution" asymmetry `DE-008`
       §10's own Business x Valuation AND/OR rule already establishes,
       applied here within Business's own two real categories rather
       than invented fresh.
    2. Neither is `WEAK`, and at least one reaches `MODERATE` or `STRONG`
       -> `POSITIVE`. `DE-008`'s own Direction Matrix (`DE-008` §20)
       never distinguishes `MODERATE` from `STRONG` in any row -- every
       row reads "MODERATE/STRONG" as one case -- so no finer split is
       invented here either.
    3. Neither category reaches any real conclusion (`NOT_EVALUATED` or
       `INSUFFICIENT_INPUT`) -> `INSUFFICIENT`. Not knowing is not a
       negative signal (`business_risk.py`'s own rule 1, applied here
       identically) -- `select_direction` treats this as a
       RecommendationWithheld case, never a fabricated `WEAK`.
    """
    if growth_status is BusinessCategoryStatus.WEAK or capital_allocation_status is BusinessCategoryStatus.WEAK:
        return _BusinessSignal.WEAK
    if (
        growth_status not in _INCONCLUSIVE_BUSINESS_STATUSES
        or capital_allocation_status not in _INCONCLUSIVE_BUSINESS_STATUSES
    ):
        return _BusinessSignal.POSITIVE
    return _BusinessSignal.INSUFFICIENT


def select_direction(
    *,
    holding_linkage: HoldingLinkage,
    business_evaluation_state: EvaluationState,
    valuation_state: EvaluationState,
    portfolio_intelligence_state: EvaluationState,
    reasoning_state: EvaluationState,
    evidence_coverage: EvidenceCoverageLevel,
    growth_status: BusinessCategoryStatus,
    capital_allocation_status: BusinessCategoryStatus,
    valuation_status: ValuationStatus,
    valuation_support_status: ValuationSupportStatus,
    has_portfolio_dampening: bool,
    has_high_financial_or_valuation_risk: bool,
) -> RecommendationDirection | None:
    """Deterministic: identical inputs always produce an identical
    result (or identically `None`). Implements `DE-008` §18's
    conflict-resolution protocol for the six reachable outcomes (`DE-016`
    made BUY/ADD reachable; EXIT remains structurally unreachable -- see
    this module's own docstring).

    `valuation_support_status` (`DE-015`'s `ValuationSupportStatus`) is
    read in exactly two branches below -- the two `DE-008` §20 matrix
    cells that were `None` (RecommendationWithheld) purely because this
    prerequisite did not exist as a computed concept. `NOT_SUPPORTED` and
    `INSUFFICIENT_INPUT` are never distinguished from each other anywhere
    in this function -- both leave those two cells exactly as they were
    before `DE-015`.

    Returns `None` for RecommendationWithheld -- never a fourth
    `RecommendationDirection`-shaped value, matching `DE-008` §1's "not a
    seventh direction" and `RecommendationOutcomeKind`'s own two-branch
    shape.
    """
    # Stage 1 (DE-008 §18, §4): hard gate. The same existence-floor
    # facts `calculate_recommendation_conviction` independently checks
    # for the identical reason -- reading them here is not a second
    # Conviction computation (see module docstring).
    if (
        business_evaluation_state is not EvaluationState.EVALUATED
        or valuation_state is not EvaluationState.EVALUATED
        or portfolio_intelligence_state is not EvaluationState.EVALUATED
        or reasoning_state is not EvaluationState.EVALUATED
        or evidence_coverage in _NO_EVIDENCE_COVERAGE
    ):
        return None

    # Stage 2 (DE-008 §3, §18): position-state partition is implicit
    # below -- every branch checks `holding_linkage` before selecting a
    # held-only or unheld-only direction.

    # Stage 3 (DE-008 §9, §18): thesis integrity check. No branch here
    # returns EXIT -- see module docstring's "On EXIT" for why no signal
    # in this codebase today is sufficient to distinguish genuine thesis
    # invalidation from ordinary, still-open Counter-Evidence.

    business = _business_signal(growth_status, capital_allocation_status)
    dampening = has_portfolio_dampening or has_high_financial_or_valuation_risk

    # Stage 4 (DE-008 §18, §20): standalone attractiveness. Business
    # alone, when WEAK, is real negative evidence sufficient by itself
    # (DE-008 §10.2: "Business and Valuation are independent"),
    # regardless of Valuation Evidence or dampening.
    if business is _BusinessSignal.WEAK:
        return RecommendationDirection.TRIM if holding_linkage is HoldingLinkage.PRESENT else RecommendationDirection.NO_ACTION

    # Business status itself unknown -- not a negative signal, not a
    # positive one either. See module docstring's "one matrix gap DE-008
    # does not enumerate."
    if business is _BusinessSignal.INSUFFICIENT:
        return None

    # From here: business is POSITIVE (MODERATE/STRONG, DE-008's own
    # grouping) -- BUY/ADD's Business leg is satisfied. Whether the
    # Valuation Support for Capital Deployment leg is also satisfied is
    # read below, only inside the two cells DE-008 §20 marks as blocked
    # purely by that prerequisite.

    if valuation_status in _INCONCLUSIVE_VALUATION_STATUSES:
        return None

    valuation_support_established = valuation_support_status is ValuationSupportStatus.SUPPORTED

    if holding_linkage is HoldingLinkage.PRESENT:
        # DE-008 §20 "Held" table. (No thesis-invalidation branch exists
        # to exclude here -- see stage 3's own comment above.)
        if valuation_status is ValuationStatus.UNDERVALUED:
            if dampening:
                return RecommendationDirection.TRIM
            # DE-008 §7/§21 invariant 2: ADD requires the same standard
            # as BUY. UNDERVALUED + held + no dampening was blocked only
            # by the missing prerequisite (§20's own note: this cell does
            # not fall back to HOLD, since UNDERVALUED is HOLD's own
            # favorable extreme) -- never touches the FAIRLY_VALUED/HOLD
            # cell below, which was never blocked in the first place.
            return RecommendationDirection.ADD if valuation_support_established else None
        if valuation_status is ValuationStatus.FAIRLY_VALUED:
            # Unchanged by DE-016: FAIRLY_VALUED + held + no dampening
            # already satisfies HOLD's own criterion directly (DE-008
            # §10.2) and was never gated on Valuation Support for Capital
            # Deployment -- valuation_support_status is not read here.
            return RecommendationDirection.TRIM if dampening else RecommendationDirection.HOLD
        # ValuationStatus.EXPENSIVE -- unchanged; never reads
        # valuation_support_status (DE-008 §21 invariant 6 by extension:
        # a negative Valuation Evidence pole is TRIM's own,
        # self-sufficient trigger, independent of this prerequisite).
        return RecommendationDirection.TRIM

    # DE-008 §20 "Not held" table.
    if valuation_status in (ValuationStatus.UNDERVALUED, ValuationStatus.FAIRLY_VALUED):
        if dampening:
            return RecommendationDirection.NO_ACTION
        # DE-008 §21 invariant 1. Both UNDERVALUED and FAIRLY_VALUED are
        # treated identically here, per §20's own note: neither alone
        # constitutes Valuation Support for Capital Deployment, so
        # neither is ranked above the other now that the prerequisite is
        # a real, separate check.
        return RecommendationDirection.BUY if valuation_support_established else None
    # ValuationStatus.EXPENSIVE -- unchanged; never reads
    # valuation_support_status.
    return RecommendationDirection.NO_ACTION
