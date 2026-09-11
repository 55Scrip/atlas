"""Guidance revision semantics (Forward-Looking Evidence, Stage 2, repaired
in Stage 2.1 against real Q1->Q2 history).

Stage 1 answered "what did management say?". This answers "what
changed?" -- and nothing more. A revision here is a **numeric**
statement: the same company's expectation for the same measure over the
same horizon went up, went down, or stayed put.

**A revision is never an opinion about the investment.** `RAISED` on
capital expenditure and `RAISED` on revenue are the same value of the
same enum, and this module has no field that could say one is welcome
and the other is not. Deciding which it is belongs to a later stage;
encoding a polarity here would quietly make that decision for it.

**One event, several kinds of evidence.** A revision is an event -- a
claim announced a new value, replacing whatever came before -- so there
is exactly one `GuidanceRevision` per claim that has any prior at all.
What Atlas knows about the *prior* is its evidence, and there are two
independent sources of it:

- an earlier claim Atlas itself observed on a previous call
  (`OBSERVED_PRIOR_CLAIM`), and
- the company restating its own previous figure in the very sentence
  that announces the new one -- "up from our previous estimate of $180
  billion to $190 billion" (`PRIOR_VALUE_STATED_IN_SAME_SOURCE`).

Both are kept, side by side, on the one event. Stage 2 read a stated
prior only for the earliest claim in each group, so when Alphabet's
Q1 call arrived, the Q2 CFO's own restatement stopped producing
anything -- Atlas held more evidence and reported less. Evidence belongs
to the passage that carries it, not to the claim's position in history,
and a new call can now only ever add to what an old one proved. When
the two sources state the same prior they corroborate each other; when
they state different ones, both stay visible and the event says so,
rather than Atlas choosing between management's memory and its own.

**Comparison is conservative by construction.** Company, claim type,
subject, horizon year, horizon kind, unit and bound shape must all
match, or the pair is incomparable with a named reason.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.analysis_engine.forward_claims.contracts import ClaimBound, HorizonKind
from atlas.analysis_engine.forward_claims.models import ForwardClaim

__all__ = [
    "REVISION_ENGINE_VERSION",
    "RevisionType",
    "NonRevisionReason",
    "RevisionBasis",
    "ClaimComparison",
    "RevisionEvidence",
    "GuidanceRevision",
    "compare_claims",
    "group_claims",
    "detect_revisions",
]

#: Bumped when the rules below change in a way that could alter a
#: classification. v2: partial range moves, horizon kind, and one event
#: per claim carrying every evidence basis.
REVISION_ENGINE_VERSION = "guidance-revision-v2"


class RevisionType(str, Enum):
    """The numeric direction of a change, and deliberately nothing else.

    `WITHDRAWN` is absent: the corpus contains no company withdrawing
    guidance, only Operator sentences explaining how to withdraw a
    *question* -- exactly the false positive a keyword rule produces.
    """

    RAISED = "raised"
    """No stated figure moved down and at least one moved up."""
    LOWERED = "lowered"
    """No stated figure moved up and at least one moved down."""
    REAFFIRMED = "reaffirmed"
    """Every stated figure is unchanged."""


class NonRevisionReason(str, Enum):
    """Why two claims produced no revision. "There is no revision" and
    "Atlas cannot safely compare these" are different answers."""

    NO_PRIOR_CLAIM = "no_prior_claim"
    DIFFERENT_COMPANY = "different_company"
    DIFFERENT_CLAIM_TYPE = "different_claim_type"
    DIFFERENT_SUBJECT = "different_subject"
    DIFFERENT_HORIZON = "different_horizon"
    DIFFERENT_HORIZON_KIND = "different_horizon_kind"
    """Same year number, different year: fiscal against calendar, or an
    explicit kind against an unqualified one."""
    INCOMPATIBLE_UNIT = "incompatible_unit"
    INCOMPATIBLE_BOUND = "incompatible_bound"
    """A point and a range are not the same shape of statement."""
    AMBIGUOUS_ORDER = "ambiguous_order"
    MIXED_RANGE_CHANGE = "mixed_range_change"
    """One end of a range moved up while the other moved down -- a
    widening or a contraction. Not a direction, and reading one out of it
    would mean comparing midpoints the company never stated. A range
    with one end unchanged is *not* mixed: "raising the low end" is a
    raise."""


class RevisionBasis(str, Enum):
    OBSERVED_PRIOR_CLAIM = "observed_prior_claim"
    """The prior is an earlier claim Atlas extracted from a different
    source it actually saw."""
    PRIOR_VALUE_STATED_IN_SAME_SOURCE = "prior_value_stated_in_same_source"
    """Management restated its own previous figure while announcing the
    new one. Atlas never observed that earlier guidance being issued
    through this basis, and it must never be presented as if it had."""


@dataclass(frozen=True)
class ClaimComparison:
    """The outcome of comparing exactly two claims. Exactly one of
    `revision_type`/`reason` is set."""

    revision_type: RevisionType | None
    reason: NonRevisionReason | None

    @property
    def is_revision(self) -> bool:
        return self.revision_type is not None


@dataclass(frozen=True)
class RevisionEvidence:
    """One source's account of what the prior value was, and the
    direction that implies. Grounded in a retrievable passage."""

    basis: RevisionBasis
    revision_type: RevisionType
    prior_value_low: float
    prior_value_high: float
    prior_value_text: str
    prior_source_record_id: str
    prior_source_text: str
    prior_reported_at: datetime
    prior_claim_id: str | None
    """The earlier claim, for an observed prior. Always `None` for a
    stated prior: that value came from the new claim's own sentence."""
    corroborates_claim_id: str | None = None
    """Stated prior only: the immediately preceding observed claim, when
    management's restated figure is exactly the figure Atlas observed.
    Only the immediate predecessor is ever considered -- "previous
    estimate" refers to the latest one, and searching deeper history for
    a number that happens to match would be guessing which call they
    meant."""


@dataclass(frozen=True)
class GuidanceRevision:
    """One revision event: a claim replaced whatever preceded it.

    Claims are never mutated to record that they were superseded -- a
    revision is a separate, additive relation, so the claim remains what
    was said on its date.
    """

    id: str
    company: str
    subject: str
    horizon_period: str
    horizon_kind: HorizonKind
    revision_type: RevisionType | None
    """The direction every evidence basis agrees on. `None` only when
    the bases disagree on direction -- in which case each basis carries
    its own, and Atlas does not pick one."""

    new_claim_id: str
    new_value_low: float
    new_value_high: float
    new_value_text: str
    new_source_record_id: str
    new_source_text: str
    new_reported_at: datetime
    stated_by: str
    stated_by_title: str

    evidence: tuple[RevisionEvidence, ...]
    revision_engine_version: str

    @property
    def corroborated(self) -> bool:
        """At least two independent bases state exactly the same prior."""
        priors = {(e.prior_value_low, e.prior_value_high) for e in self.evidence}
        return len(self.evidence) >= 2 and len(priors) == 1

    @property
    def evidence_disagrees(self) -> bool:
        """Two bases state different priors. Both remain; neither wins."""
        priors = {(e.prior_value_low, e.prior_value_high) for e in self.evidence}
        return len(priors) > 1


def _comparability(old: ForwardClaim, new: ForwardClaim) -> NonRevisionReason | None:
    if old.company != new.company:
        return NonRevisionReason.DIFFERENT_COMPANY
    if old.claim_type is not new.claim_type:
        return NonRevisionReason.DIFFERENT_CLAIM_TYPE
    if old.subject is not new.subject:
        return NonRevisionReason.DIFFERENT_SUBJECT
    if old.horizon_period != new.horizon_period:
        return NonRevisionReason.DIFFERENT_HORIZON
    if old.horizon_kind is not new.horizon_kind:
        return NonRevisionReason.DIFFERENT_HORIZON_KIND
    if old.unit != new.unit:
        return NonRevisionReason.INCOMPATIBLE_UNIT
    if old.bound is not new.bound:
        return NonRevisionReason.INCOMPATIBLE_BOUND
    return None


def _direction(old_low: float, old_high: float, new_low: float, new_high: float) -> RevisionType | None:
    """The one truth table, for every bound shape and every evidence
    basis. `None` means mixed: one end up while the other went down.

    A point (and a one-sided bound) carries a single figure in both
    fields, so this reduces to comparing that figure. What a direction
    *means* -- that "up to 90" from "up to 100" is a lower ceiling, or
    that raised capex may be bad news -- is not asked here.

    Exact equality is correct, not a tolerance: both operands come from
    decimal text through the same multiplication, so equal source
    figures give bit-identical floats.
    """
    moved_up = new_low > old_low or new_high > old_high
    moved_down = new_low < old_low or new_high < old_high
    if moved_up and moved_down:
        return None
    if moved_up:
        return RevisionType.RAISED
    if moved_down:
        return RevisionType.LOWERED
    return RevisionType.REAFFIRMED


def compare_claims(old: ForwardClaim, new: ForwardClaim) -> ClaimComparison:
    """Pure and deterministic. `old` must have been reported strictly
    before `new`; equal timestamps are ambiguous rather than resolved by
    any tiebreak, because a record id is not a clock."""
    reason = _comparability(old, new)
    if reason is not None:
        return ClaimComparison(None, reason)
    if not old.reported_at < new.reported_at:
        return ClaimComparison(None, NonRevisionReason.AMBIGUOUS_ORDER)
    direction = _direction(old.value_low, old.value_high, new.value_low, new.value_high)
    if direction is None:
        return ClaimComparison(None, NonRevisionReason.MIXED_RANGE_CHANGE)
    return ClaimComparison(direction, None)


GroupKey = tuple[str, str, str, str, str]


def group_claims(claims: tuple[ForwardClaim, ...]) -> dict[GroupKey, list[ForwardClaim]]:
    """Claims that are candidates for comparison, keyed by everything
    that must match, each group in chronological order. A fiscal-year and
    a calendar-year claim for the same number never share a group. One
    pass plus one sort per group -- never an all-pairs scan."""
    groups: dict[GroupKey, list[ForwardClaim]] = {}
    for claim in claims:
        key = (claim.company, claim.claim_type.value, claim.subject.value, claim.horizon_kind.value, claim.horizon_period)
        groups.setdefault(key, []).append(claim)
    for group in groups.values():
        # `id` breaks ties only for stable ordering; it never decides
        # which claim revised the other -- equal times are ambiguous.
        group.sort(key=lambda c: (c.reported_at, c.id))
    return groups


#: "up from our previous estimate of $180 billion to $190 billion".
#: Anchored on an explicit prior-guidance phrase, so "up from 42% a year
#: ago" -- a historical comparison, not a revision -- never matches.
_PRIOR_CLAUSE = re.compile(
    r"\b(?:up|down)?\s*from\s+(?:our|the)\s+(?:previous|prior|last)\s+"
    r"(?:estimate|guidance|outlook|range|expectations?|forecast)\s+(?:of\s+)?(?P<values>[^.;]*)",
    re.I,
)
_MONEY = re.compile(
    r"(?P<cur>\$|€|£)?\s?(?P<num>\d[\d,]*(?:\.\d+)?)\s*(?P<scale>billion|million|bn|mm)\b", re.I
)
_SCALE_FACTOR = {"billion": 1_000_000_000, "bn": 1_000_000_000, "million": 1_000_000, "mm": 1_000_000}


def _stated_prior(claim: ForwardClaim) -> tuple[float, float, str] | None:
    """The company's own previous figure, restated in the sentence that
    announced the new one -- read from the passage the claim already
    carries, so Stage 1 extraction is untouched."""
    clause = _PRIOR_CLAUSE.search(claim.source_text)
    if clause is None:
        return None
    matches = list(_MONEY.finditer(clause.group("values")))
    if not matches:
        return None
    values = [float(m.group("num").replace(",", "")) * _SCALE_FACTOR[m.group("scale").lower()] for m in matches]
    text = clause.group("values")[matches[0].start() : matches[-1].end()].strip()
    if claim.bound is ClaimBound.RANGE:
        if len(values) < 2 or values[1] < values[0]:
            return None
        return values[0], values[1], text
    return values[0], values[0], text


def _observed_evidence(older: ForwardClaim, newer: ForwardClaim) -> RevisionEvidence | NonRevisionReason:
    comparison = compare_claims(older, newer)
    if comparison.revision_type is None:
        return comparison.reason or NonRevisionReason.NO_PRIOR_CLAIM
    return RevisionEvidence(
        basis=RevisionBasis.OBSERVED_PRIOR_CLAIM,
        revision_type=comparison.revision_type,
        prior_value_low=older.value_low,
        prior_value_high=older.value_high,
        prior_value_text=older.value_text,
        prior_source_record_id=older.source_record_id,
        prior_source_text=older.source_text,
        prior_reported_at=older.reported_at,
        prior_claim_id=older.id,
    )


def _stated_evidence(claim: ForwardClaim, predecessor: ForwardClaim | None) -> RevisionEvidence | NonRevisionReason | None:
    stated = _stated_prior(claim)
    if stated is None:
        return None
    low, high, text = stated
    direction = _direction(low, high, claim.value_low, claim.value_high)
    if direction is None:
        return NonRevisionReason.MIXED_RANGE_CHANGE
    corroborates = (
        predecessor.id
        if predecessor is not None
        and _comparability(predecessor, claim) is None
        and (predecessor.value_low, predecessor.value_high) == (low, high)
        else None
    )
    return RevisionEvidence(
        basis=RevisionBasis.PRIOR_VALUE_STATED_IN_SAME_SOURCE,
        revision_type=direction,
        prior_value_low=low,
        prior_value_high=high,
        prior_value_text=text,
        prior_source_record_id=claim.source_record_id,
        prior_source_text=claim.source_text,
        prior_reported_at=claim.reported_at,
        prior_claim_id=None,
        corroborates_claim_id=corroborates,
    )


def detect_revisions(
    claims: tuple[ForwardClaim, ...],
) -> tuple[tuple[GuidanceRevision, ...], dict[GroupKey, NonRevisionReason]]:
    """Every revision event the claims support, plus why each group
    that produced none did not. Deterministic and order-independent.

    Every claim is considered on its own terms: its immediate
    predecessor (if Atlas observed one) and its own stated prior (if the
    sentence carries one) are each evidence for the change it announced.
    Neither depends on the other being absent, so adding history can
    only add evidence to an event, never remove it.
    """
    revisions: list[GuidanceRevision] = []
    unrevised: dict[GroupKey, NonRevisionReason] = {}

    for key, group in sorted(group_claims(claims).items()):
        produced = False
        for position, claim in enumerate(group):
            predecessor = group[position - 1] if position > 0 else None
            evidence: list[RevisionEvidence] = []

            if predecessor is not None:
                observed = _observed_evidence(predecessor, claim)
                if isinstance(observed, RevisionEvidence):
                    evidence.append(observed)
                else:
                    unrevised.setdefault(key, observed)

            stated = _stated_evidence(claim, predecessor)
            if isinstance(stated, RevisionEvidence):
                evidence.append(stated)
            elif isinstance(stated, NonRevisionReason):
                unrevised.setdefault(key, stated)

            if not evidence:
                continue
            directions = {e.revision_type for e in evidence}
            produced = True
            revisions.append(
                GuidanceRevision(
                    id=f"{claim.id}:revision",
                    company=claim.company,
                    subject=claim.subject.value,
                    horizon_period=claim.horizon_period,
                    horizon_kind=claim.horizon_kind,
                    revision_type=directions.pop() if len(directions) == 1 else None,
                    new_claim_id=claim.id,
                    new_value_low=claim.value_low,
                    new_value_high=claim.value_high,
                    new_value_text=claim.value_text,
                    new_source_record_id=claim.source_record_id,
                    new_source_text=claim.source_text,
                    new_reported_at=claim.reported_at,
                    stated_by=claim.stated_by,
                    stated_by_title=claim.stated_by_title,
                    evidence=tuple(sorted(evidence, key=lambda e: list(RevisionBasis).index(e.basis))),
                    revision_engine_version=REVISION_ENGINE_VERSION,
                )
            )
        if not produced:
            unrevised.setdefault(key, NonRevisionReason.NO_PRIOR_CLAIM)

    return tuple(revisions), unrevised
