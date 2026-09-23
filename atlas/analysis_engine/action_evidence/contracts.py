"""What a primary filing reports a company actually did.

Sprint 22 measured where Atlas's evidence for the things management
names actually lives. Every one of the eight observed actions it found
-- Vistra entering a 20-year PPA with AWS for 1,200 MW from Comanche
Peak, Micron's CHIPS Act funding agreements, the Lotus acquisition --
was in 10-K *narrative*, and none of it was represented anywhere. XBRL
tags positions (an asset retirement obligation, a trust's fair value),
not events, so the dimensional layer could never have carried them.

**An observed action is a narrow thing, on purpose.** The source must
report that something happened: an agreement was entered into, an
interest was acquired, a refresh was completed. Four things that look
like actions are not:

* intent -- "we plan to", "we anticipate commencing";
* description -- "AI Mode allows users to ...";
* position -- "As of December 31, 2024, we have entered into leases";
* another actor's act reported by the filer -- "the U.S. government
  announced export regulations".

**Nothing here decides who the actor is beyond what the sentence
says.** "we" in a registrant's own annual report is the registrant, by
the genre's own convention, and so is "the Company". A named actor is
kept as the words the filing used, and whether it is the filer is left
unestablished rather than guessed. Identity is a different layer, and
Sprint 21 showed it is not what attribution is waiting on.

**No consumer.** This is a decision-shadow read model: it is derived
from held filing text and nothing in the decision path imports it.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum

__all__ = [
    "ACTION_EVIDENCE_VERSION",
    "ActorKind",
    "ActionType",
    "ActionStatus",
    "QuantityKind",
    "DateKind",
    "SourceParagraph",
    "SourceLocator",
    "Quantity",
    "DateEvidence",
    "ActionEvidence",
]

ACTION_EVIDENCE_VERSION = "action-evidence-1"


class ActorKind(str, Enum):
    """How the actor was established. Never *who* it is beyond the text."""

    FILER_PRONOUN = "filer_pronoun"
    """ "we" -- the registrant speaking in its own annual report."""
    FILER_DEFINED = "filer_defined"
    """ "the Company" -- the term every 10-K defines as the registrant."""
    IMPLICIT = "implicit"
    """A subjectless sentence that opens with the predicate, as a
    highlights bullet does. The subject is not written, so it is not
    asserted."""
    NAMED = "named"
    """A named actor, kept verbatim. Not established as the filer."""


class ActionType(str, Enum):
    """Coarse family. The source's own predicate is kept beside it."""

    CONTRACT_ENTERED = "contract_entered"
    ENTRY = "entry"
    """ "entered into" something that is not an agreement -- a market."""
    ACQUISITION = "acquisition"
    COMPLETION = "completion"
    EXECUTION = "execution"
    ONGOING_ACTIVITY = "ongoing_activity"
    SHARE_REPURCHASE = "share_repurchase"
    """Shares actually bought back. Never a board authorization, which is a
    ceiling someone is permitted to spend, not money spent."""


class ActionStatus(str, Enum):
    """What the source reports about where the action stands.

    Kept apart because they are different claims: an agreement entered
    into has not necessarily delivered anything, and a service now being
    provided has not "completed"."""

    ENTERED = "entered"
    COMPLETED = "completed"
    ONGOING = "ongoing"


class QuantityKind(str, Enum):
    """What a number measures, from its own unit. A contract's 20 years
    is a duration and its 1,200 MW a capacity; neither is an amount of
    money, and a number with no unit is not given one."""

    CAPACITY = "capacity"
    DURATION = "duration"
    MONETARY = "monetary"
    PERCENT = "percent"
    UNSPECIFIED = "unspecified"


class DateKind(str, Enum):
    EVENT = "event"
    """The date governs the action itself."""
    ANNOUNCEMENT = "announcement"
    """The date governs the filer *announcing* the action. "In September
    2025, we announced that we had entered into" dates the announcement;
    the agreement was entered into on or before it."""
    PERIOD = "period"
    """Only a year is given. Not an event date."""


@dataclass(frozen=True)
class SourceParagraph:
    """One paragraph of held filing narrative, as the filing parser gave it."""

    issuer: str
    accession: str
    section: str
    ordinal: int
    text: str


@dataclass(frozen=True)
class SourceLocator:
    """Enough to re-read the exact words: which filing, which section,
    which paragraph, which sentence, where in it."""

    issuer: str
    accession: str
    section: str
    paragraph_ordinal: int
    sentence_ordinal: int
    predicate_offset: int

    @property
    def key(self) -> str:
        raw = "|".join(str(p) for p in (self.issuer, self.accession, self.section,
                                        self.paragraph_ordinal, self.sentence_ordinal,
                                        self.predicate_offset))
        return hashlib.sha256(raw.encode()).hexdigest()


@dataclass(frozen=True)
class Quantity:
    value_text: str
    """As written: "1,200", "6.1 billion", "433"."""
    unit: str | None
    """As written: "MW", "year", "$", "%". None when the source gives none --
    "433 of uprate energy" is not given MW because a neighbour is."""
    kind: QuantityKind
    qualifier: str = ""
    """The words that change what the number means: "up to", "a total of",
    "of operating energy and capacity"."""


@dataclass(frozen=True)
class DateEvidence:
    raw_text: str
    kind: DateKind
    year: int
    month: int | None = None
    day: int | None = None
    """None whenever the source did not give a day. Never filled in."""


@dataclass(frozen=True)
class ActionEvidence:
    locator: SourceLocator
    sentence: str
    """The whole sentence, verbatim. The fields below are readings of it;
    this is the evidence."""
    actor_text: str | None
    actor_kind: ActorKind
    actor_is_filer: bool | None
    """True only for "we" and "the Company". None means not established."""
    predicate: str
    """The source's own words: "had entered into", "also entered into",
    "acquired", "is now providing"."""
    action_type: ActionType
    status: ActionStatus
    object_text: str
    counterparty_text: str | None
    quantities: tuple[Quantity, ...]
    date: DateEvidence | None
    reported_via: str | None = None
    """"announced" when the source reports the action through an
    announcement; the reporting is not the action."""
    version: str = ACTION_EVIDENCE_VERSION

    @property
    def key(self) -> str:
        return self.locator.key
