"""What a verified guidance revision means economically (Forward-Looking
Evidence, Stage 4.1).

Stage 2.1 established *that* management's figure for a measure moved and
which way. This module answers the next question and deliberately no
further one: what that movement says about the business, taken at face
value. It does not ask why management moved the figure, whether it will
be met, whether the market expected it, or whether it matters to the
investment -- nothing the evidence states answers those, and a rule that
pretended to would be manufacturing a thesis.

**Revision direction is not investment direction.** RAISED on revenue
and RAISED on capital expenditure are the same fact about two different
quantities. Revenue, earnings and cash generation are quantities a
business is stronger for having more of, so a raised outlook for them
strengthens that part of the outlook. Investment spending is not: more
of it can mean more opportunity, and it also consumes cash and adds
execution risk. So a capex revision records that expected spending went
up or down, and its effect on the outlook is `AMBIGUOUS` -- in both
directions. A reaffirmation records only that the stated figures did not
change; it is not evidence of confidence, credibility or achievement.

**No polarity, no score, no company aggregate.** There is no
positive/negative field, no confidence number and no roll-up across
events: a company whose revenue guidance rose while its free-cash-flow
guidance fell has two interpretations, not a net sentiment.

**Chronology only.** The one temporal fact used is each claim's fiscal
`source_period`. No statement age, fetch, ingestion or period-end date
is read -- Stage 3.1/3.2 established none of them is when management
spoke -- so nothing here says "recently".

**Inert.** Like the rest of this package, nothing in Atlas's analysis or
decision path imports it.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.analysis_engine.forward_claims.contracts import ClaimSubject, HorizonKind
from atlas.analysis_engine.forward_claims.models import ForwardClaim
from atlas.analysis_engine.forward_claims.revisions import GuidanceRevision, RevisionBasis, RevisionType

__all__ = [
    "INTERPRETATION_VERSION",
    "ForwardEvidenceKind",
    "EconomicDimension",
    "ExpectedMovement",
    "OutlookEffect",
    "GuidanceEconomicInterpretation",
    "interpret_revision",
    "interpret_revisions",
]

#: Bumped whenever a mapping below changes meaning.
INTERPRETATION_VERSION = "guidance-interpretation-v1"


class ForwardEvidenceKind(str, Enum):
    """Which kind of forward evidence produced an economic signal (Stage
    4.2). Only guidance revisions exist today; contracts, capacity,
    commitments and the like are added here when Atlas can actually
    extract them -- an unreachable member would read as a capability."""

    GUIDANCE_REVISION = "guidance_revision"


class EconomicDimension(str, Enum):
    """The economic quantity a guided measure is about. Several measures
    can share one dimension (net sales and revenue are both REVENUE)."""

    REVENUE = "revenue"
    EARNINGS = "earnings"
    CASH_GENERATION = "cash_generation"
    INVESTMENT_SPENDING = "investment_spending"


class ExpectedMovement(str, Enum):
    """What management's expected quantity did -- read straight from the
    revision, with no judgement of whether that is good."""

    INCREASED = "increased"
    DECREASED = "decreased"
    UNCHANGED = "unchanged"


class OutlookEffect(str, Enum):
    """What that movement does to the business outlook along this
    dimension, and nothing beyond it -- not a recommendation, and not a
    view of the stock."""

    STRENGTHENING = "strengthening"
    WEAKENING = "weakening"
    UNCHANGED = "unchanged"
    """The stated figures did not move. No more than that: a reaffirmed
    figure is not a stronger one, and not a sign of confidence."""
    AMBIGUOUS = "ambiguous"
    """The dimension has no single better direction. More investment
    spending can reflect opportunity and also consumes cash; less can
    free cash and also signal less opportunity. Which one applies is
    not in the evidence."""


_DIMENSION: dict[ClaimSubject, EconomicDimension] = {
    ClaimSubject.REVENUE: EconomicDimension.REVENUE,
    ClaimSubject.ADJUSTED_EBITDA: EconomicDimension.EARNINGS,
    ClaimSubject.FREE_CASH_FLOW: EconomicDimension.CASH_GENERATION,
    ClaimSubject.CAPITAL_EXPENDITURE: EconomicDimension.INVESTMENT_SPENDING,
}

_MOVEMENT: dict[RevisionType, ExpectedMovement] = {
    RevisionType.RAISED: ExpectedMovement.INCREASED,
    RevisionType.LOWERED: ExpectedMovement.DECREASED,
    RevisionType.REAFFIRMED: ExpectedMovement.UNCHANGED,
}

#: Dimensions a business is stronger for having more of. Investment
#: spending is deliberately absent.
_MORE_IS_STRONGER = frozenset({EconomicDimension.REVENUE, EconomicDimension.EARNINGS, EconomicDimension.CASH_GENERATION})

#: How an explanation names each canonical subject. A canonical subject
#: can be broader than the source's own measure: FREE_CASH_FLOW covers
#: VST's "adjusted free cash flow before growth", and ADJUSTED_EBITDA
#: covers a plain "EBITDA" and every issuer's own adjustments. Those two
#: are named as "a ... measure" so the explanation never presents them
#: as the plain, standard figure; the verbatim passage travels with the
#: interpretation for the exact wording.
_MEASURE_LABEL: dict[ClaimSubject, str] = {
    ClaimSubject.REVENUE: "revenue",
    ClaimSubject.ADJUSTED_EBITDA: "an EBITDA measure",
    ClaimSubject.FREE_CASH_FLOW: "a free-cash-flow measure",
    ClaimSubject.CAPITAL_EXPENDITURE: "capital expenditure",
}

_VERB: dict[RevisionType, str] = {
    RevisionType.RAISED: "raised",
    RevisionType.LOWERED: "lowered",
    RevisionType.REAFFIRMED: "reaffirmed",
}


@dataclass(frozen=True)
class GuidanceEconomicInterpretation:
    """The direct economic meaning of one verified `GuidanceRevision`,
    linked back to it field by field."""

    revision_id: str
    company: str
    subject: ClaimSubject
    horizon_period: str
    horizon_kind: HorizonKind
    revision_type: RevisionType

    dimension: EconomicDimension
    movement: ExpectedMovement
    outlook_effect: OutlookEffect

    unit: str
    """The currency and scale management stated, e.g. `"USD_BILLION"`.
    Every value and change below is an absolute amount in that currency
    -- $175 billion is `175e9` -- never a multiple of the scale."""
    new_value_low: float
    new_value_high: float
    new_value_text: str
    prior_value_low: float | None
    prior_value_high: float | None
    prior_value_text: str | None
    """`None` when the revision's evidence bases state different prior
    figures: the direction is agreed, the starting point is not."""

    low_end_change: float | None
    high_end_change: float | None
    """Descriptive magnitude, per end, in the claims' own base units --
    new minus prior. Never a midpoint (a range's midpoint is a figure
    management did not state), never a materiality judgement. `None`
    when the prior figures are not agreed."""
    low_end_relative_change: float | None
    high_end_relative_change: float | None
    """Each end's change as a fraction of its prior value; `None` when
    the prior is unknown or zero."""

    prior_source_periods: tuple[str | None, ...]
    """The fiscal period of the call each evidence basis took its prior
    from -- chronology, never a date."""
    new_source_period: str | None
    evidence_bases: tuple[RevisionBasis, ...]
    new_source_text: str
    """Verbatim passage of the new guidance, carrying the measure's own
    wording (e.g. "adjusted free cash flow before growth")."""

    explanation: str
    """One deterministic, factual sentence built from the fields above --
    what changed, never why."""
    interpretation_version: str

    # -- `synthesis.ForwardEconomicSignal` (Stage 4.2) -------------------------
    # Read-only views so a guidance interpretation can be synthesized
    # alongside future forward-evidence kinds; no field changes.

    @property
    def signal_id(self) -> str:
        return self.revision_id

    @property
    def source_period(self) -> str | None:
        return self.new_source_period

    @property
    def evidence_kind(self) -> "ForwardEvidenceKind":
        return ForwardEvidenceKind.GUIDANCE_REVISION


def _horizon_phrase(horizon_kind: HorizonKind, horizon_period: str) -> str:
    if horizon_kind is HorizonKind.FISCAL_YEAR:
        return f"fiscal {horizon_period}"
    if horizon_kind is HorizonKind.CALENDAR_YEAR:
        return f"calendar {horizon_period}"
    return horizon_period


def _end_clause(low_change: float | None, high_change: float | None, is_range: bool) -> str:
    """Which ends of a range moved -- stated only for ranges, and only
    when something moved."""
    if not is_range or low_change is None or high_change is None or (low_change == 0 and high_change == 0):
        return ""

    def word(change: float) -> str:
        return "rose" if change > 0 else "fell" if change < 0 else "was unchanged"

    if word(low_change) == word(high_change):
        return f"; both ends {word(low_change)}"
    return f"; the low end {word(low_change)} and the high end {word(high_change)}"


def _explanation(
    revision: GuidanceRevision, subject: ClaimSubject, prior_text: str | None,
    low_change: float | None, high_change: float | None,
) -> str:
    """What changed, in the figures' own words: "X management raised its
    2026 guidance for capital expenditure: $175 billion to $185 billion
    -> $180 billion to $190 billion; both ends rose." Never why."""
    horizon = _horizon_phrase(revision.horizon_kind, revision.horizon_period)
    head = f"{revision.company} management {_VERB[revision.revision_type]} its {horizon} guidance for {_MEASURE_LABEL[subject]}"
    if prior_text is None:
        return f"{head}: now {revision.new_value_text}; its sources state different prior figures."
    is_range = revision.new_value_low != revision.new_value_high
    return f"{head}: {prior_text} \u2192 {revision.new_value_text}{_end_clause(low_change, high_change, is_range)}."


def _relative(change: float | None, prior: float | None) -> float | None:
    if change is None or prior is None or prior == 0:
        return None
    return change / abs(prior)


def interpret_revision(revision: GuidanceRevision, new_claim: ForwardClaim) -> GuidanceEconomicInterpretation | None:
    """Pure and deterministic. `new_claim` is the claim the revision
    announced (`revision.new_claim_id`); it supplies the unit the
    revision itself does not carry. `None` when the revision's evidence
    bases disagree on direction: there is no single movement to
    interpret, and choosing one would be picking between management's
    memory and Atlas's own record."""
    if new_claim.id != revision.new_claim_id:
        raise ValueError(f"{new_claim.id} is not the claim revision {revision.id} announced")
    if revision.revision_type is None:
        return None
    subject = ClaimSubject(revision.subject)
    dimension = _DIMENSION[subject]
    movement = _MOVEMENT[revision.revision_type]
    if movement is ExpectedMovement.UNCHANGED:
        effect = OutlookEffect.UNCHANGED
    elif dimension in _MORE_IS_STRONGER:
        effect = OutlookEffect.STRENGTHENING if movement is ExpectedMovement.INCREASED else OutlookEffect.WEAKENING
    else:
        effect = OutlookEffect.AMBIGUOUS

    priors = {(e.prior_value_low, e.prior_value_high) for e in revision.evidence}
    if len(priors) == 1:
        (prior_low, prior_high), = priors
        prior_text = revision.evidence[0].prior_value_text
        low_change = revision.new_value_low - prior_low
        high_change = revision.new_value_high - prior_high
    else:
        prior_low = prior_high = prior_text = low_change = high_change = None

    return GuidanceEconomicInterpretation(
        revision_id=revision.id,
        company=revision.company,
        subject=subject,
        horizon_period=revision.horizon_period,
        horizon_kind=revision.horizon_kind,
        revision_type=revision.revision_type,
        dimension=dimension,
        movement=movement,
        outlook_effect=effect,
        unit=new_claim.unit,
        new_value_low=revision.new_value_low,
        new_value_high=revision.new_value_high,
        new_value_text=revision.new_value_text,
        prior_value_low=prior_low,
        prior_value_high=prior_high,
        prior_value_text=prior_text,
        low_end_change=low_change,
        high_end_change=high_change,
        low_end_relative_change=_relative(low_change, prior_low),
        high_end_relative_change=_relative(high_change, prior_high),
        prior_source_periods=tuple(e.prior_source_period for e in revision.evidence),
        new_source_period=revision.new_source_period,
        evidence_bases=tuple(e.basis for e in revision.evidence),
        new_source_text=revision.new_source_text,
        explanation=_explanation(revision, subject, prior_text, low_change, high_change),
        interpretation_version=INTERPRETATION_VERSION,
    )


def interpret_revisions(
    revisions: tuple[GuidanceRevision, ...], claims: tuple[ForwardClaim, ...]
) -> tuple[GuidanceEconomicInterpretation, ...]:
    """One interpretation per interpretable revision, in the revisions'
    own order. Never aggregated: each event keeps its own dimension and
    effect. A claim with no revision has nothing to interpret -- only
    revisions are read; `claims` only resolves each revision's own new
    claim."""
    by_id = {claim.id: claim for claim in claims}
    out = (interpret_revision(r, by_id[r.new_claim_id]) for r in revisions)
    return tuple(i for i in out if i is not None)
