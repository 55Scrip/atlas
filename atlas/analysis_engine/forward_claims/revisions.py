"""Guidance revision semantics (Forward-Looking Evidence, Stage 2).

Stage 1 answered "what did management say?". This answers "what
changed?" -- and nothing more. A revision here is a **numeric**
statement about two claims: the same company's expectation for the same
measure over the same horizon went up, went down, or stayed put.

**A revision is never an opinion about the investment.** `RAISED` on
capital expenditure and `RAISED` on revenue are the same value of the
same enum, and this module has no field that could say one is welcome
and the other is not. Raising capex may be a company investing into
demand or a company losing control of its costs; deciding which is a
later stage's work, and encoding a polarity here would quietly make
that decision for it. `test_revisions.py` pins this.

**Comparison is conservative by construction.** Every dimension that
could make two claims mean different things -- company, claim type,
subject, horizon, unit, how the value is bounded -- must match exactly,
or the pair is reported incomparable with the reason. Two ranges that
merely overlap are not a direction; `180-190` becoming `185-195` is
recorded as a mixed change rather than guessed into `RAISED` on the
strength of a midpoint the company never stated.

**Two kinds of prior value, never conflated.** Normally the older
operand is a claim Atlas observed on an earlier call. But a company can
also restate its own previous number inside the sentence announcing the
new one -- "up from our previous estimate of $180 billion to $190
billion". That is real, source-grounded evidence of a revision, and it
is *not* an earlier observation: Atlas never saw that guidance issued.
`RevisionBasis` keeps the two apart, so a future consumer can tell a
reconstructed history from a reported one.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.analysis_engine.forward_claims.contracts import ClaimBound
from atlas.analysis_engine.forward_claims.models import ForwardClaim

__all__ = [
    "REVISION_ENGINE_VERSION",
    "RevisionType",
    "NonRevisionReason",
    "RevisionBasis",
    "ClaimComparison",
    "GuidanceRevision",
    "compare_claims",
    "group_claims",
    "detect_revisions",
]

#: Bumped when the comparison rules below change in a way that could
#: alter a classification. Stamped onto every revision, so a revision
#: produced by older rules stays distinguishable from a newer one.
REVISION_ENGINE_VERSION = "guidance-revision-v1"


class RevisionType(str, Enum):
    """The numeric direction of a change, and deliberately nothing else.

    `WITHDRAWN` is absent. The corpus contains no company withdrawing
    guidance -- what it does contain is five Operator sentences
    explaining how to withdraw a *question* from the queue, which is
    exactly the false positive a keyword rule would produce. Absence of
    a later claim is not withdrawal either; it is absence. When a real
    withdrawal appears in a real call, it needs its own non-numeric
    claim shape, which Stage 2 does not have.
    """

    RAISED = "raised"
    LOWERED = "lowered"
    REAFFIRMED = "reaffirmed"


class NonRevisionReason(str, Enum):
    """Why two claims produced no revision. "There is no revision" and
    "Atlas cannot safely compare these" are different answers, and a
    consumer that cannot tell them apart will eventually report the
    second as the first."""

    NO_PRIOR_CLAIM = "no_prior_claim"
    DIFFERENT_COMPANY = "different_company"
    DIFFERENT_CLAIM_TYPE = "different_claim_type"
    DIFFERENT_SUBJECT = "different_subject"
    DIFFERENT_HORIZON = "different_horizon"
    INCOMPATIBLE_UNIT = "incompatible_unit"
    INCOMPATIBLE_BOUND = "incompatible_bound"
    """A point and a range are not the same shape of statement.
    "approximately $7 billion" and "$6.8-$7.6 billion" may well be the
    same intent, but reading a direction out of them requires deciding
    which end of the range the point should be measured against."""
    AMBIGUOUS_ORDER = "ambiguous_order"
    MIXED_RANGE_CHANGE = "mixed_range_change"
    """One end moved up and the other down, or the ranges overlap
    without both ends moving the same way."""


class RevisionBasis(str, Enum):
    OBSERVED_PRIOR_CLAIM = "observed_prior_claim"
    """Both operands are claims Atlas extracted from two different
    sources it actually saw."""
    PRIOR_VALUE_STATED_IN_SAME_SOURCE = "prior_value_stated_in_same_source"
    """Management restated its own previous figure while announcing the
    new one. Atlas never observed the earlier guidance being issued, and
    this value must never be presented as if it had."""


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
class GuidanceRevision:
    """One numeric change, grounded in both of its operands.

    Claims are never mutated to record that they were superseded: a
    revision is a separate, additive relation. A claim is what was said
    on a date, and that does not stop being true because something was
    said later -- rewriting it would destroy the history that makes
    backtesting and management-reliability work possible at all.
    """

    id: str
    company: str
    subject: str
    horizon_period: str
    revision_type: RevisionType
    basis: RevisionBasis

    prior_value_low: float
    prior_value_high: float
    prior_value_text: str
    prior_source_record_id: str
    prior_source_text: str
    prior_reported_at: datetime
    prior_claim_id: str | None
    """`None` when the prior value was merely referenced by management
    rather than observed by Atlas -- there is no earlier claim to point
    at, and inventing an id would imply one existed."""

    new_claim_id: str
    new_value_low: float
    new_value_high: float
    new_value_text: str
    new_source_record_id: str
    new_source_text: str
    new_reported_at: datetime
    stated_by: str
    stated_by_title: str

    revision_engine_version: str


def _comparability(old: ForwardClaim, new: ForwardClaim) -> NonRevisionReason | None:
    if old.company != new.company:
        return NonRevisionReason.DIFFERENT_COMPANY
    if old.claim_type is not new.claim_type:
        return NonRevisionReason.DIFFERENT_CLAIM_TYPE
    if old.subject is not new.subject:
        return NonRevisionReason.DIFFERENT_SUBJECT
    if old.horizon_period != new.horizon_period:
        return NonRevisionReason.DIFFERENT_HORIZON
    if old.unit != new.unit:
        return NonRevisionReason.INCOMPATIBLE_UNIT
    if old.bound is not new.bound:
        return NonRevisionReason.INCOMPATIBLE_BOUND
    return None


def compare_claims(old: ForwardClaim, new: ForwardClaim) -> ClaimComparison:
    """Pure and deterministic. `old` must have been reported strictly
    before `new`; equal timestamps are ambiguous rather than resolved by
    any tiebreak, because a record id is not a clock."""
    reason = _comparability(old, new)
    if reason is not None:
        return ClaimComparison(None, reason)
    if not old.reported_at < new.reported_at:
        return ClaimComparison(None, NonRevisionReason.AMBIGUOUS_ORDER)

    # Exact equality is correct here, not a tolerance: both operands are
    # produced by the same parser from decimal text through the same
    # multiplication, so equal source figures give bit-identical floats.
    if old.bound is ClaimBound.RANGE:
        low_up, high_up = new.value_low > old.value_low, new.value_high > old.value_high
        low_down, high_down = new.value_low < old.value_low, new.value_high < old.value_high
        if low_up and high_up:
            return ClaimComparison(RevisionType.RAISED, None)
        if low_down and high_down:
            return ClaimComparison(RevisionType.LOWERED, None)
        if new.value_low == old.value_low and new.value_high == old.value_high:
            return ClaimComparison(RevisionType.REAFFIRMED, None)
        return ClaimComparison(None, NonRevisionReason.MIXED_RANGE_CHANGE)

    # POINT, LOWER_BOUND and UPPER_BOUND each carry one stated figure,
    # so the direction is that figure's. What the direction *means* --
    # "up to 90" from "up to 100" is a lower ceiling -- is economic
    # reading, and belongs to a later stage.
    if new.value_low > old.value_low:
        return ClaimComparison(RevisionType.RAISED, None)
    if new.value_low < old.value_low:
        return ClaimComparison(RevisionType.LOWERED, None)
    return ClaimComparison(RevisionType.REAFFIRMED, None)


def group_claims(claims: tuple[ForwardClaim, ...]) -> dict[tuple[str, str, str, str], list[ForwardClaim]]:
    """Claims that are candidates for comparison, keyed by what must
    match, each group in chronological order. Grouping is a single pass
    plus one sort per group -- never an all-pairs scan."""
    groups: dict[tuple[str, str, str, str], list[ForwardClaim]] = {}
    for claim in claims:
        key = (claim.company, claim.claim_type.value, claim.subject.value, claim.horizon_period)
        groups.setdefault(key, []).append(claim)
    for group in groups.values():
        # `id` breaks ties only for stable ordering of equally-timed
        # claims; it never decides which of them revised the other --
        # `compare_claims` reports that pair ambiguous.
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


def _referenced_prior_value(claim: ForwardClaim) -> tuple[float, float, str] | None:
    """The company's own previous figure, restated in the sentence that
    announced the new one. Read from the claim's own `source_text`, so
    it is grounded in exactly the passage the claim already carries --
    Stage 1's extraction is untouched."""
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


def detect_revisions(
    claims: tuple[ForwardClaim, ...],
) -> tuple[tuple[GuidanceRevision, ...], dict[tuple[str, str, str, str], NonRevisionReason]]:
    """Every revision the claims support, plus why each group that
    produced none did not. Deterministic and order-independent: the
    result depends on the claims, never on the sequence they arrive in.
    """
    revisions: list[GuidanceRevision] = []
    unrevised: dict[tuple[str, str, str, str], NonRevisionReason] = {}

    for key, group in sorted(group_claims(claims).items()):
        # Consecutive pairs only. A group of four claims is three
        # revisions, and the history keeps all four -- collapsing to
        # "first vs latest" would erase a raise that was later undone.
        produced = False
        for older, newer in zip(group, group[1:]):
            comparison = compare_claims(older, newer)
            if comparison.revision_type is None:
                unrevised.setdefault(key, comparison.reason or NonRevisionReason.NO_PRIOR_CLAIM)
                continue
            produced = True
            revisions.append(
                GuidanceRevision(
                    id=f"{newer.id}:revises:{older.id}",
                    company=newer.company,
                    subject=newer.subject.value,
                    horizon_period=newer.horizon_period,
                    revision_type=comparison.revision_type,
                    basis=RevisionBasis.OBSERVED_PRIOR_CLAIM,
                    prior_value_low=older.value_low,
                    prior_value_high=older.value_high,
                    prior_value_text=older.value_text,
                    prior_source_record_id=older.source_record_id,
                    prior_source_text=older.source_text,
                    prior_reported_at=older.reported_at,
                    prior_claim_id=older.id,
                    new_claim_id=newer.id,
                    new_value_low=newer.value_low,
                    new_value_high=newer.value_high,
                    new_value_text=newer.value_text,
                    new_source_record_id=newer.source_record_id,
                    new_source_text=newer.source_text,
                    new_reported_at=newer.reported_at,
                    stated_by=newer.stated_by,
                    stated_by_title=newer.stated_by_title,
                    revision_engine_version=REVISION_ENGINE_VERSION,
                )
            )

        # The earliest claim in a group has nothing before it in Atlas --
        # but management may have restated its own previous figure while
        # issuing it.
        earliest = group[0]
        referenced = _referenced_prior_value(earliest)
        if referenced is not None:
            low, high, text = referenced
            if earliest.bound is ClaimBound.RANGE:
                if earliest.value_low > low and earliest.value_high > high:
                    revision_type = RevisionType.RAISED
                elif earliest.value_low < low and earliest.value_high < high:
                    revision_type = RevisionType.LOWERED
                elif earliest.value_low == low and earliest.value_high == high:
                    revision_type = RevisionType.REAFFIRMED
                else:
                    unrevised.setdefault(key, NonRevisionReason.MIXED_RANGE_CHANGE)
                    continue
            else:
                if earliest.value_low > low:
                    revision_type = RevisionType.RAISED
                elif earliest.value_low < low:
                    revision_type = RevisionType.LOWERED
                else:
                    revision_type = RevisionType.REAFFIRMED
            produced = True
            revisions.append(
                GuidanceRevision(
                    id=f"{earliest.id}:revises:stated-prior",
                    company=earliest.company,
                    subject=earliest.subject.value,
                    horizon_period=earliest.horizon_period,
                    revision_type=revision_type,
                    basis=RevisionBasis.PRIOR_VALUE_STATED_IN_SAME_SOURCE,
                    prior_value_low=low,
                    prior_value_high=high,
                    prior_value_text=text,
                    prior_source_record_id=earliest.source_record_id,
                    prior_source_text=earliest.source_text,
                    prior_reported_at=earliest.reported_at,
                    prior_claim_id=None,
                    new_claim_id=earliest.id,
                    new_value_low=earliest.value_low,
                    new_value_high=earliest.value_high,
                    new_value_text=earliest.value_text,
                    new_source_record_id=earliest.source_record_id,
                    new_source_text=earliest.source_text,
                    new_reported_at=earliest.reported_at,
                    stated_by=earliest.stated_by,
                    stated_by_title=earliest.stated_by_title,
                    revision_engine_version=REVISION_ENGINE_VERSION,
                )
            )
        if not produced:
            unrevised.setdefault(key, NonRevisionReason.NO_PRIOR_CLAIM)

    return tuple(revisions), unrevised
