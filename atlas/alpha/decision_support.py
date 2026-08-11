"""Decision Support presentation layer (Workspace Migration, Phase 1).

**Not a second recommendation/decision engine.** This module computes
nothing new -- it translates the already-computed, already-tested
`atlas.analysis_engine.recommendation.RecommendationGateResult`
(`ComputedDirectionalRecommendation` | `RecommendationWithheld`, wired
into every `CanonicalAnalysis` since "Recommendation Backend Step 3")
into Atlas's own evidence-support language for the two product surfaces
the approved Workspace Migration Review
(`docs/Atlas-Alpha-Workspace-Migration-Review.md` §11.1, Decision Log
#1) names: Investment Case's header sentence and Portfolio's Holdings
table Action column.

Whether a direction is reachable at all remains
`atlas.analysis_engine.direction_selector.select_direction`'s exclusive
decision -- today only `RecommendationDirection.HOLD`/`.TRIM`/
`.NO_ACTION` are ever constructed; `.BUY`/`.ADD`/`.EXIT` are structurally
unreachable (see that module's own docstring for why). This module
defines statements for all six `RecommendationDirection` members anyway,
so it needs no follow-up edit if a future sprint widens
`select_direction`'s reachable set -- it would simply start being
exercised for the currently-dormant branches.

**The raw `RecommendationDirection` member names (`BUY`, `ADD`, `HOLD`,
`TRIM`, `EXIT`) are never sent to the API or rendered anywhere in the
product** -- only this module's `DecisionSupportLevel`/`badge_label`/
`statement`. Decision Log #1: Atlas states what current evidence
supports, in Atlas's own voice, never as an imperative command.

**`DecisionSupportLevel` has one more member than the review's own
six-state table: `NO_ACTION_SUPPORTED`.** The review's table did not
anticipate `RecommendationDirection.NO_ACTION` -- a real, reachable
outcome for a security the investor does not currently hold, and
semantically distinct from `INSUFFICIENT_EVIDENCE`:

- `NO_ACTION_SUPPORTED` means Business Analysis and Valuation both
  reached a genuine conclusion, and that conclusion does not support
  initiating a position -- a real, evaluated "no" the same way
  `ValuationStatus.EXPENSIVE` is a real, evaluated "no," never an
  absence of information.
- `INSUFFICIENT_EVIDENCE` means no such conclusion was reachable at
  all -- `select_direction`'s own hard gate (an `EvaluationState` not
  `EVALUATED`, or `EvidenceCoverageLevel.NONE`/`.NOT_APPLICABLE`, or
  Business/Valuation themselves inconclusive) never even ran.

Collapsing these two into one badge would silently discard a real
distinction the backend already computes -- the same "missing is not
the same as negative" doctrine `atlas.analysis_engine.risk` and
`atlas.analysis_engine.direction_selector` themselves already enforce.

The exact sentence wording below is this module's own product-facing
copy (per explicit product direction), not a byte-for-byte reuse of
`atlas.analysis_engine.recommendation._DIRECTION_STATEMENTS` --  that
private table is Recommendation's own internal, ATLAS-020-era wording
for its three reachable directions; this module's wording is the
Workspace Migration Review's finalized six-state copy plus one addition
for `NO_ACTION_SUPPORTED`. Both describe the identical underlying
decision; only the words differ.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.analysis_engine.recommendation import RecommendationDirection, RecommendationGateResult
from atlas.decision_engine.contracts import RecommendationWithheld

__all__ = ["DecisionSupportLevel", "DecisionSupportView", "describe_recommendation"]


class DecisionSupportLevel(str, Enum):
    ENTRY_SUPPORTED = "entry_supported"
    INCREASE_SUPPORTED = "increase_supported"
    THESIS_INTACT = "thesis_intact"
    REDUCTION_SUPPORTED = "reduction_supported"
    EXIT_SUPPORTED = "exit_supported"
    NO_ACTION_SUPPORTED = "no_action_supported"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


_DIRECTION_LEVEL: dict[RecommendationDirection, DecisionSupportLevel] = {
    RecommendationDirection.BUY: DecisionSupportLevel.ENTRY_SUPPORTED,
    RecommendationDirection.ADD: DecisionSupportLevel.INCREASE_SUPPORTED,
    RecommendationDirection.HOLD: DecisionSupportLevel.THESIS_INTACT,
    RecommendationDirection.TRIM: DecisionSupportLevel.REDUCTION_SUPPORTED,
    RecommendationDirection.EXIT: DecisionSupportLevel.EXIT_SUPPORTED,
    RecommendationDirection.NO_ACTION: DecisionSupportLevel.NO_ACTION_SUPPORTED,
}

#: Short, non-imperative badge labels -- Migration Review §8's own
#: working examples ("Entry supported" / "Thesis intact" / "Insufficient
#: evidence"), extended to all seven levels.
_LEVEL_BADGE_LABEL: dict[DecisionSupportLevel, str] = {
    DecisionSupportLevel.ENTRY_SUPPORTED: "Entry supported",
    DecisionSupportLevel.INCREASE_SUPPORTED: "Increase supported",
    DecisionSupportLevel.THESIS_INTACT: "Thesis intact",
    DecisionSupportLevel.REDUCTION_SUPPORTED: "Reduction supported",
    DecisionSupportLevel.EXIT_SUPPORTED: "Exit supported",
    DecisionSupportLevel.NO_ACTION_SUPPORTED: "No action supported",
    DecisionSupportLevel.INSUFFICIENT_EVIDENCE: "Insufficient evidence",
}

#: Full evidence-support sentence -- Migration Review §11.1's exact
#: six-state table, plus `NO_ACTION_SUPPORTED`'s own honest, distinct
#: statement.
_LEVEL_STATEMENT: dict[DecisionSupportLevel, str] = {
    DecisionSupportLevel.ENTRY_SUPPORTED: "Current evidence supports initiating a position.",
    DecisionSupportLevel.INCREASE_SUPPORTED: "Current evidence supports increasing exposure.",
    DecisionSupportLevel.THESIS_INTACT: "Current thesis remains intact.",
    DecisionSupportLevel.REDUCTION_SUPPORTED: "Current evidence supports reducing exposure.",
    DecisionSupportLevel.EXIT_SUPPORTED: "Current evidence supports exiting the position.",
    DecisionSupportLevel.NO_ACTION_SUPPORTED: "Current evidence does not support initiating a position in this security.",
    DecisionSupportLevel.INSUFFICIENT_EVIDENCE: "Current evidence is insufficient to support any portfolio action.",
}


@dataclass(frozen=True)
class DecisionSupportView:
    """What the product ever renders. `level` is the only field a
    frontend should branch on (e.g. for badge tone); `badge_label`/
    `statement` are the only text ever shown to an investor."""

    level: DecisionSupportLevel
    badge_label: str
    statement: str


def describe_recommendation(gate_result: RecommendationGateResult) -> DecisionSupportView:
    """Deterministic: reads `gate_result.recommendation` only, never
    recomputes it. `RecommendationWithheld` (no `direction` field, by
    construction -- see that type's own docstring) always maps to
    `INSUFFICIENT_EVIDENCE`, regardless of *why* it was withheld --
    `RecommendationWithheld.reason`/`.missing_evaluations` remain
    available on the domain object for diagnostics, but this module
    deliberately never branches on them: the Migration Review specifies
    one fixed sentence for this state, not a reason-dependent one."""
    recommendation = gate_result.recommendation
    if isinstance(recommendation, RecommendationWithheld):
        level = DecisionSupportLevel.INSUFFICIENT_EVIDENCE
    else:
        level = _DIRECTION_LEVEL[recommendation.direction]
    return DecisionSupportView(
        level=level,
        badge_label=_LEVEL_BADGE_LABEL[level],
        statement=_LEVEL_STATEMENT[level],
    )
