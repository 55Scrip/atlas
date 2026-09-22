"""What management says is supposed to happen, and what would show it.

Sprint 23 gave Atlas observed actions from filings. The action shadow then
showed the strategy side could not say what it was claiming: a node keeps a
short canonical factor -- `data center`, `in Arizona`, `invest` -- while the
passage said "ensure that everything necessary for the data center at Comanche
Peak is completed on schedule" or "invest more than $200 million in Arizona to
establish a state-of-the-art facility". The predicate, the horizon, the
dependency and the magnitude were all in the sentence and none of them survived.

**A claim is not a forecast, and most claims carry no number.** Of the ten
action-named nodes, four state a measurable magnitude and five are observable
only as events -- a groundbreaking, a contract, a completion. One is a standing
priority with no object at all. So `measure_kinds` is empty far more often than
not, and that is the correct answer rather than a gap to fill.

**A measure comes from the predicate, never from a number nearby.** A passage
about power markets needing "a spread around that $555 a megawatt day" contains
a currency amount and the word megawatt and states no Vistra claim at all. The
verb decides what kind of evidence would bear on the claim; a magnitude is only
attached when the amount is the predicate's own object.

**Nothing here reads Action Evidence.** The claim has to be derivable from what
management said, or the representation leaks the answer backwards into the
question. The comparison is a later, separate step.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

__all__ = [
    "STRATEGY_CLAIM_VERSION", "ClaimStatus", "ClaimType", "Direction", "Observability",
    "MeasureKind", "EventKind", "Horizon", "Dependency", "Magnitude", "ClaimProvenance",
    "StrategyClaim",
]

STRATEGY_CLAIM_VERSION = "strategy-claim-1"


class ClaimStatus(str, Enum):
    """What kind of speech act the passage is. A priority is not a forecast."""

    ASSERTED_STRATEGY = "asserted_strategy"
    FORWARD_INTENT = "forward_intent"
    OBSERVATIONAL_STATEMENT = "observational_statement"
    MANAGEMENT_THESIS = "management_thesis"


class ClaimType(str, Enum):
    CAPITAL_ALLOCATION = "capital_allocation"
    CAPITAL_RETURN = "capital_return"
    BUILD = "build"
    CONTRACTING = "contracting"
    DELIVERY = "delivery"
    ADOPTION = "adoption"
    PRIORITY = "priority"


class Direction(str, Enum):
    DEPLOY = "deploy"
    RETURN = "return"
    BUILD = "build"
    EXPAND = "expand"
    COMPLETE = "complete"
    INCREASE = "increase"


class Observability(str, Enum):
    """How a reader could tell whether the claim is progressing. Observable
    does not mean numeric: a groundbreaking is observable and has no unit."""

    QUANTITATIVELY_OBSERVABLE = "quantitatively_observable"
    QUALITATIVELY_OBSERVABLE = "qualitatively_observable"
    PARTIALLY_OBSERVABLE = "partially_observable"
    NOT_DIRECTLY_OBSERVABLE = "not_directly_observable"


class MeasureKind(str, Enum):
    """Only kinds the corpus earned."""

    CAPITAL_DEPLOYMENT = "capital_deployment"
    CAPITAL_RETURNED = "capital_returned"
    CAPACITY = "capacity"


class EventKind(str, Enum):
    """What would count as the claim happening."""

    CAPITAL_DEPLOYED = "capital_deployed"
    CONSTRUCTION_STARTED = "construction_started"
    CONTRACT_ENTERED = "contract_entered"
    COMPLETION = "completion"
    SHARE_REPURCHASE = "share_repurchase"
    FACILITY_ESTABLISHED = "facility_established"


@dataclass(frozen=True)
class Horizon:
    raw_text: str
    """Exactly as said -- "on schedule", "over an 8-year period", "after 2028".
    Never resolved into a date the source did not give."""


@dataclass(frozen=True)
class Dependency:
    raw_text: str
    marker: str
    """The words that made it a dependency: "because", "underpins",
    "as permitted by the terms of", "before any offsets from"."""


@dataclass(frozen=True)
class Magnitude:
    value_text: str
    unit: str
    qualifier: str = ""
    """"approximately", "more than" -- kept, because they are the claim."""


@dataclass(frozen=True)
class ClaimProvenance:
    issuer: str
    node_id: str
    node_kind: str
    source_record_id: str
    source_period: str
    speaker_title: str


@dataclass(frozen=True)
class StrategyClaim:
    provenance: ClaimProvenance
    source_passage: str
    """The sentence, verbatim. Every field below must be visible in it."""
    claim_type: ClaimType
    status: ClaimStatus
    predicate: str
    """Management's own verb: "break ground", "allocating capital", "repurchased"."""
    direction: Direction
    object_text: str
    entities: tuple[str, ...]
    """Source-preserved mention surfaces. Never resolved -- identity is a
    different layer and Sprint 21 closed it as a bottleneck."""
    observability: Observability
    measure_kinds: tuple[MeasureKind, ...]
    event_kinds: tuple[EventKind, ...]
    magnitude: Magnitude | None
    horizon: Horizon | None
    dependencies: tuple[Dependency, ...]
    version: str = STRATEGY_CLAIM_VERSION
