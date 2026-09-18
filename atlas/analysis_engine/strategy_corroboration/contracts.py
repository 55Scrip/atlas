"""Strategic Corroboration v1 -- the vocabulary.

Strategic Salience can say management keeps returning to something. It
cannot say whether that emphasis is matched by anything the company
actually did, because every signal it reads -- recurrence, prepared-remark
prominence, speaker breadth, priority language -- is authored by the
management doing the emphasising. A company that decides to stress a
theme can produce all four next quarter without changing its business.

This layer asks the other question: **what did the company do?**

**Management repeating itself is not corroboration.** A second sentence
saying the same thing does not independently support the first, and two
executives describing one guidance event are describing one event. Those
raise salience and change nothing here.

**Corroboration is not truth, causation, success, materiality or a
recommendation.** Reported capex tripling alongside a stated
infrastructure strategy establishes that the company spent the money. It
does not establish that the spending was wise, that the strategy caused
anything, or that any return will follow.

**Missing evidence is not negative evidence.** Atlas holds no headcount
line and no R&D line, so it can never observe those moving. Reporting
that as "not corroborated" would be honest; reporting it as "weakened"
would be a lie told by an absence.
"""
from __future__ import annotations

from enum import Enum

__all__ = [
    "EvidenceClass",
    "CorroborationRelation",
    "TemporalRelation",
    "CoverageState",
    "IndependenceChannel",
]


class EvidenceClass(str, Enum):
    """What kind of thing an observation is.

    Only classes Atlas can actually populate exist here. `MARKET_OUTCOME`
    is deliberately absent: a share price moving after an announcement is
    the market's opinion of a strategy, not evidence that the company
    executed one, and admitting it would let sentiment corroborate the
    thing that produced the sentiment."""

    STATED_INTENT = "stated_intent"
    """Management language. Present so it can be named and excluded --
    this class never corroborates anything, and a test holds that."""

    RESOURCE_DEPLOYMENT = "resource_deployment"
    """Money the company reported spending or returning: capital
    expenditure, buybacks, dividends, debt movements. Reported, audited,
    and not a sentence -- the strongest independent channel Atlas has."""

    FINANCIAL_OUTCOME = "financial_outcome"
    """Reported results: revenue, operating income, free cash flow, net
    income, earnings per share. What came out, not what was spent."""

    GUIDANCE_COMMITMENT = "guidance_commitment"
    """A guidance revision, owned by `forward_claims` and referenced
    here.

    Management-authored, and admitted anyway because a revision is a
    distinct *commitment event* rather than a restatement: a company that
    raises its own capital-expenditure guidance has changed a number it
    will be held to. It corroborates commitment. It never corroborates
    action, and a test holds that separation."""

    CUSTOMER_COMMITMENT = "customer_commitment"
    """An executed customer commitment, owned by `forward_claims`. The
    only class where a counterparty signs. Structurally supported and
    **empty for every company in this corpus** -- a search of all twelve
    with transcripts returns zero -- which is a finding about coverage,
    not a gap in the model."""


class CorroborationRelation(str, Enum):
    """What an observation corroborates -- never simply "supports".

    A capital-expenditure increase alongside a stated build-out supports
    that the company is *doing* the thing. It says nothing about whether
    the thing will work, and collapsing those into one word is how a
    layer like this starts sounding like a recommendation."""

    SUPPORTS_EXECUTION = "supports_execution"
    """Observed action moved in the direction the strategy implies."""
    WEAKENS_EXECUTION = "weakens_execution"
    """Observed action moved against it, where coverage is good enough
    for the movement to mean something."""
    SUPPORTS_OUTCOME = "supports_outcome"
    """A reported result moved in the stated intended direction. Not
    that the strategy produced it."""
    WEAKENS_OUTCOME = "weakens_outcome"
    SUPPORTS_COMMITMENT = "supports_commitment"
    """Management changed a number it will be held to."""
    CONTEXT_ONLY = "context_only"
    """Relevant, and neither supporting nor weakening -- including every
    observation whose period precedes the strategy statement."""


class TemporalRelation(str, Enum):
    """How an observation sits in time against the strategy statement.

    The corpus makes this the binding constraint rather than a
    formality: strategy statements run 2025Q3-2026Q2, and the newest
    financial fact for every benchmark is fiscal 2025. An initiative
    first stated in 2026Q2 therefore has *no* financial observation
    covering any time after it was stated, and the honest answer is that
    Atlas has not observed anything yet."""

    PRECEDES_STRATEGY = "precedes_strategy"
    """The observation's period ends before the statement was made. It
    cannot be evidence of executing something not yet announced."""
    CONTEMPORANEOUS = "contemporaneous"
    """The observation's period contains the statement."""
    SUBSEQUENT = "subsequent"
    """The observation measures time after the statement."""
    UNKNOWN = "unknown"


class IndependenceChannel(str, Enum):
    """Where an observation came from, so two observations can be tested
    for being the same thing twice.

    Two transcript passages from one call are not two independent
    economic observations merely because they are two records, and a CEO
    and a CFO describing one capital-expenditure decision are describing
    one decision."""

    MANAGEMENT_STATEMENT = "management_statement"
    """Anything said on a call. One channel, however many speakers."""
    REPORTED_FINANCIAL_STATEMENT = "reported_financial_statement"
    """A filed statement. Independent of the call that discussed it."""
    MANAGEMENT_GUIDANCE = "management_guidance"
    """A guidance revision: management-authored, but a commitment event
    distinct from describing one."""
    COUNTERPARTY_AGREEMENT = "counterparty_agreement"
    """Someone outside the company signed something."""


class CoverageState(str, Enum):
    """Why a strategy node has the corroboration it has -- which is as
    important as the corroboration itself.

    Four different silences are four different facts, and a layer that
    reports them identically is useless for deciding anything."""

    OBSERVED_SUPPORTING = "observed_supporting"
    OBSERVED_WEAKENING = "observed_weakening"
    MIXED = "mixed"
    """Support and weakening coexist. Reported as both, never voted into
    one answer -- a capital build-out can be real while the margin it
    was meant to produce moves the wrong way."""
    NO_INDEPENDENT_EVIDENCE = "no_independent_evidence"
    """Atlas looked in channels it has and found nothing linked. **Not
    contradiction.**"""
    EVIDENCE_SOURCE_UNAVAILABLE = "evidence_source_unavailable"
    """Atlas has no channel that could observe this at all -- headcount
    and research spending have no line in `BusinessFact`. Distinct from
    having looked and found nothing."""
    SEMANTIC_LINK_UNAVAILABLE = "semantic_link_unavailable"
    """The node kind has no defensible mapping to any observable
    measure. A dependency on regulatory approval is real and Atlas has
    no filed number that moves when it is granted."""
