"""Strategic Action Attribution v1 -- the vocabulary.

Strategic Corroboration established that Alphabet's reported capital
expenditure rose from $52.5bn to $91.5bn while management described a
data-centre build-out. What it could not establish is that any of the
increase went to that build-out: the figure is consolidated, and a
company could announce X, raise total spending, and spend the increase
entirely on Y without any of the earlier signals changing.

This layer asks what evidence, if any, closes that gap. **The audit that
preceded it found that for most observations, none does** -- and saying
so precisely is the capability, not a shortfall of it.

**Temporal coincidence is not attribution.** An action in the period a
strategy was announced is corroboration and nothing more.

**Semantic similarity is not attribution.** A strategy about capital and
an action measured in capital expenditure share a word, not a link.

**Two weak links do not compose into a strong one.** "AI is mentioned
often" plus "capital expenditure rose" plus "analysts ask about data
centres" is narrative, not evidence, and nothing here may add them up.

**Management may attribute without corroborating.** "We invested $X in
Project Y" is precise and is still management's own account; precision
is not independence. The attribution role and the action-evidence role
are recorded separately for exactly this reason.
"""
from __future__ import annotations

from enum import Enum

__all__ = [
    "AttributionResolution",
    "AttributionBasis",
    "AttributionStatus",
    "EvidenceRole",
    "ActionTense",
]


class AttributionResolution(str, Enum):
    """How finely an observation can be placed.

    Only levels the corpus actually evidences exist. `SEGMENT` and
    `BUSINESS_LINE` are deliberately absent: a search of every record in
    the corpus for a dimensional key -- segment, axis, member, geography,
    reportable unit -- returns **nothing**. The European ESEF records
    carry `esef_concepts`, which maps a measure to the IFRS concept it
    came from, not to a dimension, and none of the four benchmark
    companies has even that.

    Publishing a `SEGMENT` member Atlas can never populate would read as
    a capability."""

    COMPANY = "company"
    """The whole issuer. Where every consolidated figure sits, and where
    almost everything stays."""
    GEOGRAPHY = "geography"
    """A named place, not a category. Sprint 7 learned that
    `GEOGRAPHIC_MARKET` groups Arizona and China together; a resolution
    claim needs the place itself, so this member is used only where a
    specific place is named in the linking passage."""
    PROJECT = "project"
    """A named asset or build -- a plant, a facility, a site."""
    CAPACITY_ASSET = "capacity_asset"
    """A quantified physical capability: megawatts at a named plant,
    cards issued, units deployed."""
    COUNTERPARTY = "counterparty"
    """A named customer or partner to an agreement."""


class ActionTense(str, Enum):
    """Whether an action has happened.

    The corpus makes this the dominant distinction. Of sixteen
    quantified-purpose statements across the four benchmark companies,
    most describe money that *will* be spent. An amount attached to an
    intention is attribution of a plan, and turning it into attribution
    of an action is the single most tempting error available here."""

    OBSERVED_PAST = "observed_past"
    STATED_INTENT = "stated_intent"
    UNKNOWN = "unknown"


class EvidenceRole(str, Enum):
    """What a piece of evidence is doing in an attribution.

    Three roles, kept apart because one source often cannot fill two.
    A filed statement shows an action and says nothing about purpose; a
    transcript sentence supplies purpose and is not independent
    verification. An attribution built from both is more precise than
    either -- and still carries a management-authored link."""

    STRATEGY_SIDE = "strategy_side"
    ACTION_SIDE = "action_side"
    LINKING = "linking"


class AttributionBasis(str, Enum):
    """On what grounds an action is attributed.

    These are epistemic kinds, not strengths, and nothing orders or
    scores them."""

    EXPLICIT_MANAGEMENT_QUANTIFICATION = "explicit_management_quantification"
    """Management named an amount and a purpose in one passage: "we plan
    to invest more than $200 million in Arizona to establish a facility
    for manufacturing specialized components". Attribution of the
    allocation; never independent evidence that it happened."""

    MANAGEMENT_NAMED_LINK = "management_named_link"
    """Management tied an action or asset to a named project, place or
    counterparty without an amount -- "a 20-year contract with Amazon at
    our Comanche Peak nuclear plant". Useful attribution with no number,
    which is a real and common shape."""

    DERIVED_STRUCTURAL = "derived_structural"
    """Atlas placed the action using a reported breakdown rather than a
    sentence. **Unreachable in this corpus**: no dimensional data
    exists. The member is kept because the distinction between a
    structural placement and a management sentence is the one that would
    matter most if such data ever arrives, and a layer that had no word
    for it would quietly file the first segment figure it ever saw under
    a management quote."""

    CANDIDATE_ONLY = "candidate_only"
    """A shared canonical factor, or an action in the same period.
    Enough to look at, never enough to assert -- see
    `AttributionStatus`."""


class AttributionStatus(str, Enum):
    """What may be said about the attribution as a whole."""

    ATTRIBUTED = "attributed"
    """A linking fact exists, with provenance, tying this action or
    allocation to this strategy node at the stated resolution."""
    AMBIGUOUS = "ambiguous"
    """A link exists and does not resolve to one target -- an action
    placed in a scope that contains several strategy nodes. The scope is
    reported; the choice is not made."""
    CONFLICTING = "conflicting"
    """Two linking facts imply incompatible scopes. Both are kept."""
    CANDIDATE_ONLY = "candidate_only"
    """Factor equality or period overlap and nothing else. Never
    published as a fact."""
    NO_ATTRIBUTION_EVIDENCE = "no_attribution_evidence"
    """Atlas searched the channels it has and found no linking fact.
    **The normal answer**, and the honest one for Alphabet's $39bn."""
