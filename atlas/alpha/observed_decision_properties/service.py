"""`build_observed_decision_properties` -- the one function this package
exposes. Pure read: takes a `DecisionRepository`, returns a
deterministic tuple of `ObservedDecisionProperty`. Never writes
anything, never persists a projection (Sprint 12 Phase 15/Sprint 13
ground rule: recompute-on-demand only).

**Deliberately does not use `DecisionTimelineQuery`.** That query's own
`build()` issues one `list_by_decision_id`/`list_by_outcome_id`/
`list_by_evaluation_id` round trip per Decision to assemble
`review_chains` -- real, already-documented N+1 behavior (Sprint 10/11).
`SameSubjectAndTypeStrategy`/`SameConfidenceStrategy` never read
`entry.review_chains` at all (confirmed by direct grep in Sprint 11/12:
zero references to `outcome`/`review_chains` in either strategy). Paying
that query cost here would be a genuine, avoidable defect in this new
endpoint's own path, not a reuse of anything the strategies actually
need -- so this module builds the minimal `DecisionTimeline` the two
strategies do require directly from `DecisionRepository.list_all()`,
with every `review_chains` deliberately left `()`. The strategy classes
themselves are imported and run completely unmodified; no grouping
logic is duplicated.

Ordering matches `DecisionTimelineQuery.build()`'s own convention
exactly (`decided_at` ascending, then `id.value`) even though this
module does not call that class, so results stay comparable to it and
to the existing CLI output.
"""
from __future__ import annotations

from atlas.core.application.pattern_recognition.recognized_pattern import RecognizedPattern
from atlas.core.application.pattern_recognition.strategies import (
    SameConfidenceStrategy,
    SameSubjectAndTypeStrategy,
)
from atlas.core.application.decision_timeline.timeline import DecisionTimeline, DecisionTimelineEntry
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.repository import DecisionRepository

from atlas.alpha.observed_decision_properties.models import ObservedDecisionProperty, ObservedPropertyScope

__all__ = ["build_observed_decision_properties"]

#: Sprint 12 Phase 12's own "safest first contract": no statistical
#: sufficiency rule was justified by that sprint's audit -- only that
#: the recognition floor (>=2) identifies recurrence but never behavioral
#: generalization. Rather than improvise a threshold Sprint 12 explicitly
#: warned against inventing, every v1 property is unconditionally
#: flagged. A future, evidence-based sufficiency rule can replace this
#: constant without changing the field's meaning to a consumer.
_SAMPLE_SIZE_WARNING_V1 = True

#: Structural, not computed: neither `SameSubjectAndTypeStrategy` nor
#: `SameConfidenceStrategy` reads an Outcome, so this is never derived
#: by inspecting Outcome data (Sprint 13 Phase 11's own explicit
#: instruction) -- it is a fixed fact about which algorithm produced
#: every v1 property.
_OUTCOME_AWARE_V1 = False

_SCOPE_BY_STRATEGY = {
    SameSubjectAndTypeStrategy.name: ObservedPropertyScope.SINGLE_COMPANY,
    SameConfidenceStrategy.name: ObservedPropertyScope.PORTFOLIO_WIDE,
}


def _build_minimal_timeline(decisions: list[Decision]) -> DecisionTimeline:
    ordered = sorted(decisions, key=lambda d: (d.decided_at, d.id.value))
    entries = tuple(DecisionTimelineEntry(decision=d, review_chains=()) for d in ordered)
    return DecisionTimeline(entries=entries)


def _factual_description(pattern: RecognizedPattern, observed_count: int) -> str:
    """Regenerated from `matching_key` (structured, strategy-owned) --
    never `pattern.description` passed through verbatim (Sprint 12
    Phase 5: the public wire contract must not silently inherit legacy
    CLI wording). Level 0 only: a literal restatement of a count and
    the structured values that produced it, nothing else."""
    if pattern.strategy_name == SameSubjectAndTypeStrategy.name:
        subject, decision_type = pattern.matching_key
        return f"You recorded {observed_count} {decision_type} Decisions for {subject}."
    if pattern.strategy_name == SameConfidenceStrategy.name:
        (confidence,) = pattern.matching_key
        return f"Confidence {confidence} appears in {observed_count} recorded Decisions."
    # Unreachable while only the two known strategies run below; a
    # future third strategy must add its own branch here explicitly
    # rather than fall through to a guessed description.
    raise ValueError(f"No factual-description rule defined for strategy {pattern.strategy_name!r}")


def _total_eligible_decisions(pattern: RecognizedPattern, all_decisions: list[Decision]) -> int:
    """Sprint 12 Phase 7's denominator contract, chosen for semantic
    honesty over convenience:

    - `same_subject_and_type`: every Decision recorded for that same
      subject, regardless of type -- so the resulting proportion
      answers "of everything you decided about this company, what
      share was this type," a real question. The alternative (Decisions
      matching subject *and* type) would trivially equal
      `observed_count` itself, since that pair is exactly how the
      Pattern's own membership is defined -- a proportion of 1.0 always,
      which carries no information.
    - `same_confidence`: every recorded Decision. `Confidence` is a
      required field on `Decision` (see `Decision.__post_init__`'s own
      invariant) -- there is no Decision with no confidence value to
      exclude, so "all Decisions with a confidence value" and "all
      Decisions" are the same set.
    """
    if pattern.strategy_name == SameSubjectAndTypeStrategy.name:
        subject, _decision_type = pattern.matching_key
        return sum(1 for d in all_decisions if d.subject.value == subject)
    if pattern.strategy_name == SameConfidenceStrategy.name:
        return len(all_decisions)
    raise ValueError(f"No denominator rule defined for strategy {pattern.strategy_name!r}")


def _project(pattern: RecognizedPattern, all_decisions: list[Decision]) -> ObservedDecisionProperty:
    by_id = {d.id: d for d in all_decisions}
    members = [by_id[decision_id] for decision_id in pattern.member_decision_ids]
    ordered_members = sorted(members, key=lambda d: (d.decided_at, d.id.value))

    observed_count = len(ordered_members)
    total_eligible = _total_eligible_decisions(pattern, all_decisions)

    return ObservedDecisionProperty(
        property_type=pattern.strategy_name,
        factual_description=_factual_description(pattern, observed_count),
        scope=_SCOPE_BY_STRATEGY[pattern.strategy_name],
        observed_count=observed_count,
        total_eligible_decisions=total_eligible,
        proportion=observed_count / total_eligible,
        supporting_decision_ids=tuple(str(d.id) for d in ordered_members),
        first_observed_at=ordered_members[0].decided_at,
        last_observed_at=ordered_members[-1].decided_at,
        outcome_aware=_OUTCOME_AWARE_V1,
        sample_size_warning=_SAMPLE_SIZE_WARNING_V1,
    )


def build_observed_decision_properties(
    decision_repository: DecisionRepository,
) -> tuple[ObservedDecisionProperty, ...]:
    """The one function this package exposes. Deterministic given a
    deterministic Decision history: reruns `SameSubjectAndTypeStrategy`
    then `SameConfidenceStrategy` (the same order `pattern_recognition
    .composition.build_pattern_recognition_query` registers them in) and
    projects each `RecognizedPattern` independently -- no cross-Pattern
    merging, no `ConnectedPatternsStrategy`, no Strategy Signature of
    any kind is ever computed here (Sprint 12's own integration
    decision; Sprint 13 Phase 19's explicit verification requirement)."""
    decisions = decision_repository.list_all()
    timeline = _build_minimal_timeline(decisions)
    patterns = SameSubjectAndTypeStrategy().recognize(timeline) + SameConfidenceStrategy().recognize(timeline)
    return tuple(_project(pattern, decisions) for pattern in patterns)
