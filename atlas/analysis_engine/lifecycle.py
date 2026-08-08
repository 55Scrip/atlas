"""Investment Case Lifecycle (ATLAS-020, Phase 11).

Phase 11 asked for an **Automatic Investment Case Lifecycle**: manual
User Observations become optional rather than mandatory, and Atlas
instead derives where a Case stands from whatever it has actually
recorded — with an explicit instruction to document, plainly, whether
the mechanism should be removed entirely if it complicates the
architecture.

**Finding, before any design choice was made:** `atlas.core.domain.case
.entity.Case` carries only `id` and `recorded_at`. Its own docstring
states this is deliberate, cited authority, not an oversight: OE-002
§3.1 defines Case purely as an ownership boundary, and DO-REC-001 §8
explicitly forbids adding "further lifecycle, status, title,
description, or content" to it. There is no `CaseStatus` field
anywhere in Core, Alpha, or the frontend to formalize — Phase 11 is not
asking this sprint to name an existing state machine, it is asking
whether to invent a brand-new one.

**Verdict: do not add a stored status to `Case`, and do not build an
automatic Case-creation/promotion mechanism this sprint.** Two
independent reasons converge on this:

1. Storing a lifecycle status on `Case` would directly contradict
   DO-REC-001 §8's explicit prohibition — this package does not have
   standing to reopen that decision, and doing so silently (adding a
   field DO-REC-001 forbids, without amending DO-REC-001 itself) would
   repeat exactly the kind of undisclosed contradiction ATLAS-019
   flagged and fixed for the orphaned Decision Engine docs.
2. "Automatic" in the sprint's sense — Atlas creating or promoting a
   Case in response to new information without the investor acting —
   is a **write-side, event-triggered** operation. Every other module
   in `atlas.analysis_engine` (`conviction.py`, `recommendation.py`,
   `pipeline.py`) is a pure function over already-fetched, read-only
   data, matching this package's own boundary (`__init__.py`): reads
   only `atlas.core.domain` and `atlas.decision_engine`, never writes
   anything, never calls a repository, never listens for an event. No
   event-sourcing or write-triggered infrastructure exists anywhere in
   this codebase today for a Case-creation trigger to hook into.
   Building one inside this package would be exactly the kind of
   "motion without progress" `__init__.py` already declined for moving
   `atlas.decision_engine` wholesale — introducing real architectural
   weight (a new write path, a new trigger system) to serve a
   capability this sprint cannot honestly wire end-to-end anyway.

**What this sprint keeps, and what it changes:** User Observations stay
exactly as ATLAS-019 already concluded — optional, load-bearing input
to Evidence Quality, never mandatory, never removed. What Phase 11 asks
for that *is* honestly buildable today, without touching `Case` or
inventing a write path, is a **derived, recomputed-every-time Life
Stage** — the same pattern this whole package already uses for
Conviction: never stored, always a pure function of whatever
`DecisionEngineInput` already holds for a Case. `determine_life_stage`
below is that function. It answers "given what is on record right now,
how far along is this Case's evaluation" — it never creates, promotes,
or persists anything, and a caller may recompute it as often as it
recomputes Conviction, with the identical staleness guarantee (Phase 7:
recompute on `UpdateTrigger.NEW_DECISION_RECORDED` /
`NEW_OBSERVATION_RECORDED` / `NEW_OUTCOME_RECORDED`).

If a future sprint wants genuine Case *creation* automation (e.g.
auto-starting a Case when an investor records a first Observation about
a new holding), that decision belongs to `atlas.core.application`'s use
cases — the layer that already owns writes — informed by, but not
implemented inside, this package.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.decision_engine.contracts import DecisionEngineInput

__all__ = ["LifeStage", "LifeStageAssessment", "determine_life_stage"]


class LifeStage(str, Enum):
    """A derived, never-stored classification of how far a Case's own
    evaluation has progressed, from real record counts already present
    in `DecisionEngineInput` — never a status an investor sets, never a
    field written back to `Case`. Ordered roughly by how much is on
    record, but this is a classification, not a score: nothing here
    ranks a Case's *quality*, only how much has been recorded about it.
    """

    NO_ACTIVITY = "no_activity"
    """No Decision, Observation, or Outcome is recorded for this Case
    at all — Evidence alone, with nothing it is evidence *for*, is not
    counted (an Evidence item always exists to support/challenge an
    Observation; the presence check therefore only needs those three)."""

    OBSERVED = "observed"
    """At least one Observation is recorded; no Decision yet."""

    DECIDED = "decided"
    """At least one Decision is recorded; no Outcome reported yet."""

    REVIEWED = "reviewed"
    """At least one Outcome has been reported against a recorded
    Decision — the investor has closed the loop on at least one
    decision at least once."""


@dataclass(frozen=True)
class LifeStageAssessment:
    stage: LifeStage
    decision_count: int
    observation_count: int
    outcome_count: int


def determine_life_stage(engine_input: DecisionEngineInput) -> LifeStageAssessment:
    """Deterministic: a pure read of three tuple lengths already on
    `DecisionEngineInput`, evaluated in the fixed order
    Outcome -> Decision -> Observation -> none (first match wins), the
    same ordered-decision-table style `conviction.calculate_conviction`
    and `atlas.domains.portfolio.calculations.concentration_level`
    already established. No wall-clock read, no side effect, no write.
    """
    decision_count = len(engine_input.decisions)
    observation_count = len(engine_input.observations)
    outcome_count = len(engine_input.outcomes)

    if outcome_count > 0:
        stage = LifeStage.REVIEWED
    elif decision_count > 0:
        stage = LifeStage.DECIDED
    elif observation_count > 0:
        stage = LifeStage.OBSERVED
    else:
        stage = LifeStage.NO_ACTIVITY

    return LifeStageAssessment(
        stage=stage,
        decision_count=decision_count,
        observation_count=observation_count,
        outcome_count=outcome_count,
    )
