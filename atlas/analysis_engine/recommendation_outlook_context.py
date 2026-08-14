"""Recommendation/Outlook Context (Recommendation / Decision Intelligence
Sprint 1) -- the one, narrow, sanctioned relationship
`docs/atlas_decision_engine/DE-012-Atlas-Recommendation-Ontology.md` §8 and
`DE-014-Atlas-Outlook-Composition.md` permit between Recommendation and
Outlook: Recommendation's Direction reasoning MAY cite the current, already
-computed Outlook as informational context, never as a required or causal
input.

**This module computes nothing that feeds back into Direction selection,
Recommendation gating, or Recommendation Conviction.** It reads two already
-computed, already-final objects --
`atlas.analysis_engine.recommendation.RecommendationGateResult.recommendation`
and `atlas.analysis_engine.outlook.Outlook` -- and derives a purely
categorical fact about how they currently relate. Nothing here is called
by, or has any effect on, `atlas.analysis_engine.direction_selector
.select_direction`, `atlas.analysis_engine.recommendation
.evaluate_recommendation_gate`, or `atlas.analysis_engine
.recommendation_conviction.calculate_recommendation_conviction` -- those
three remain exactly as adopted, reading only their own pre-existing inputs.
Outlook and Recommendation stay `DE-012`/`DE-014`'s "shared-ancestor,
independently-computed" sibling conclusions; this module only observes and
names the relationship between two already-finished conclusions after the
fact.

**Why this exists.** `direction_selector.py`'s own module docstring (and
`DE-008` §21 invariant 11 / §23) establishes that BUY/ADD are structurally
unreachable because "Valuation Support for Capital Deployment" -- a
scenario-based forward value range -- does not exist as a computed concept
anywhere in this codebase (`ValuationMethodKind.SCENARIO_BEAR/BASE/BULL` is
permanently `INSUFFICIENT_INPUT` by deliberate design, see
`atlas/analysis_engine/valuation/scenarios.py`). Long-Term Expected Return
(Outlook) is a different, independently-computed concept -- a historical
-growth-and-yield-reversion range, not a scenario-based valuation -- and
cannot honestly substitute for the missing capability either (this was
weighed and explicitly rejected; see this sprint's own delivery report).
So Recommendation's Direction stays exactly as `direction_selector.py`
computes it regardless of what Outlook says. What Outlook *can* honestly
add is disclosure: whether its own, separately-derived prospective-return
sign happens to agree or disagree with the conclusion Recommendation
already, independently, reached.

**The comparison, in full.** Every direction `select_direction` can
actually construct today (`HOLD`, `TRIM`, `NO_ACTION`) already shares one
structural fact: none of them represents "Valuation Support for Capital
Deployment" being satisfied -- that is precisely why BUY/ADD are
unreachable. So this module does not need, and deliberately does not build,
a per-direction "how bullish is this direction" taxonomy (which would
invent distinctions `DE-008` itself never draws, exactly what `DE-008` §21
forbids). It asks one honest, sign-based question per horizon: does
Outlook's own independently-computed Expected Return range for that horizon
imply positive, negative, or straddling-zero prospective returns --
and does that sign agree with, or run against, the fact that Recommendation
did not find capital-deployment support?

    Recommendation is RecommendationWithheld, or this horizon's Expected
    Return is unavailable (a named `OutlookGapKind`)
        -> UNAVAILABLE

    Expected Return range straddles zero (bear-case loss, bull-case gain)
        -> MIXED (Outlook itself has no clear sign to compare)

    Expected Return range is entirely negative (high_percent < 0)
        -> CORROBORATES (Outlook's own, independent math also implies
           this is not an attractive time to hold/build a position --
           exactly the sanctioned example: "Recommendation is HOLD,
           valuation is currently restrictive, and the independently
           -computed Long-Term Outlook also implies weak prospective
           returns")

    Expected Return range is entirely positive (low_percent > 0)
        -> DIVERGES (Outlook's own, independent math implies attractive
           prospective returns even though Recommendation did not find
           Valuation Support for Capital Deployment -- a genuine,
           worth-surfacing tension, not a contradiction: two different,
           real questions -- "is a scenario-based case for deploying more
           capital right now established" and "does a historical growth
           -and-reversion range point up or down" -- can honestly diverge)

No numeric threshold anywhere in this rule: zero is not a chosen cutoff, it
is the only non-arbitrary boundary between "this range implies a gain" and
"this range implies a loss." `MIXED` is a real, disclosed outcome, not
collapsed into either side.

**Known limitation, disclosed rather than hidden.** Outlook and
Recommendation are correlated through shared upstream ancestry (both read
Business Analysis and Valuation), so `CORROBORATES` is not full independent
confirmation -- see this sprint's own adversarial findings for the exact
cases this produces. This module never claims independence beyond what
`DE-012`/`DE-014` themselves already establish.

**Computed per horizon, never blended into one fact.** Short-Term and
Long-Term Outlook answer different questions (a valuation re-rating vs. a
growth-and-reversion range) and are never combined into a single score or
a single relationship -- the same "no collapsing distinct signals into one
number" discipline this codebase already applies everywhere else."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.outlook import ExpectedReturnRange, Outlook
from atlas.analysis_engine.recommendation import ComputedDirectionalRecommendation
from atlas.decision_engine.contracts import RecommendationWithheld

__all__ = [
    "OutlookRecommendationRelationship",
    "RecommendationOutlookContext",
    "derive_recommendation_outlook_context",
]


class OutlookRecommendationRelationship(str, Enum):
    """A disclosed, categorical fact about two already-computed, sibling
    conclusions -- never a score, never a gate, never an input back into
    either conclusion. See this module's own docstring for the exact rule
    per value."""

    CORROBORATES = "corroborates"
    DIVERGES = "diverges"
    MIXED = "mixed"
    UNAVAILABLE = "unavailable"


class _ReturnSign(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    MIXED = "mixed"
    UNAVAILABLE = "unavailable"


def _return_sign(expected_return: ExpectedReturnRange | None) -> _ReturnSign:
    """Zero is the only boundary used, and it is not a chosen threshold --
    it is the line between a range that implies a gain and one that
    implies a loss. A range whose bear case still shows a loss and whose
    bull case still shows a gain (`low_percent <= 0 <= high_percent`,
    which also covers either bound landing exactly on zero) has no clear
    sign to report and is honestly `MIXED`, not rounded to either side."""
    if expected_return is None:
        return _ReturnSign.UNAVAILABLE
    if expected_return.low_percent > 0:
        return _ReturnSign.POSITIVE
    if expected_return.high_percent < 0:
        return _ReturnSign.NEGATIVE
    return _ReturnSign.MIXED


def _relationship(has_direction: bool, sign: _ReturnSign) -> OutlookRecommendationRelationship:
    if not has_direction or sign is _ReturnSign.UNAVAILABLE:
        return OutlookRecommendationRelationship.UNAVAILABLE
    if sign is _ReturnSign.MIXED:
        return OutlookRecommendationRelationship.MIXED
    if sign is _ReturnSign.NEGATIVE:
        return OutlookRecommendationRelationship.CORROBORATES
    return OutlookRecommendationRelationship.DIVERGES


@dataclass(frozen=True)
class RecommendationOutlookContext:
    """The only two facts this module ever produces. Both are always
    present (never optional fields) -- `UNAVAILABLE` is itself one of the
    four real `OutlookRecommendationRelationship` values, not an absent
    field, matching this codebase's own "named reason, never a silent
    gap" discipline."""

    short_term: OutlookRecommendationRelationship
    long_term: OutlookRecommendationRelationship

    def __post_init__(self) -> None:
        for field_name, value in (("short_term", self.short_term), ("long_term", self.long_term)):
            if not isinstance(value, OutlookRecommendationRelationship):
                raise AnalysisEngineContractError(
                    f"RecommendationOutlookContext.{field_name} must be an "
                    "OutlookRecommendationRelationship."
                )


def derive_recommendation_outlook_context(
    recommendation: RecommendationWithheld | ComputedDirectionalRecommendation,
    outlook: Outlook,
) -> RecommendationOutlookContext:
    """Deterministic: identical inputs always produce an identical
    result. Reads only `recommendation`'s own type (whether a Direction
    was reached at all -- never *which* direction, see this module's own
    docstring for why no per-direction taxonomy is built) and `outlook`'s
    two `expected_return` ranges. Never reads `outlook.scenarios`,
    `outlook.momentum`, or `outlook.conviction` -- this relationship is
    computed from the Expected Return range's own sign alone, the exact
    figure the sanctioned example ("Outlook also implies weak prospective
    returns") refers to."""
    has_direction = isinstance(recommendation, ComputedDirectionalRecommendation)
    return RecommendationOutlookContext(
        short_term=_relationship(has_direction, _return_sign(outlook.short_term.expected_return)),
        long_term=_relationship(has_direction, _return_sign(outlook.long_term.expected_return)),
    )
