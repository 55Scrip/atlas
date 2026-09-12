"""Executed customer commitments as state evidence (Forward-Looking
Evidence, Stage 5.1).

Guidance is evidence about *change*: a figure, then a revised figure.
A signed 20-year power purchase agreement is evidence about *state*: it
means something the first time Atlas sees it, with nothing to compare it
against. This module is only a representation of that state -- a claim
type and the boundary a statement must cross to become one. It extracts
nothing from transcripts, interprets nothing economically and feeds no
synthesis.

**What a claim is.** A company insider stating that a customer has
already committed, in a concluded agreement, to take the company's
output -- electricity and capacity from its plants, or its products --
with at least one committed term (a quantity, a numeric duration, or a
delivery window) stated in the same proposition. Named
`CustomerCommitmentClaim` because the direction is part of the meaning:
the transcripts' own word for it is "customer commitments", and in
financial reporting a company's *commercial commitments* are its own
obligations, the opposite economic sign. The narrow name keeps out, by
definition:

- **What does not exist yet.** An opportunity, a pipeline, "capacity
  that can be contracted", discussions, agreements the company expects
  to conclude. VST's "additional 3.2 gigawatts" is the pinned case:
  real megawatts, a real counterparty type, and no commitment.
- **What is not definitive.** An MoU, a letter of intent, a term sheet,
  a framework agreement, anything non-binding -- even when "signed".
- **What is not a customer's commitment.** Acquisition and merger
  agreements, debt and credit agreements, government agreements: legal
  contracts, often with a megawatt or a dollar figure, and the wrong
  concept entirely.
- **A partnership or relationship** that states no concluded agreement.
- **A contracted position across customers.** "We have now contracted
  approximately 3.8 gigawatts" or "agreements for our entire calendar
  2026 HBM supply" total several commitments; they are not one, and a
  claim for the total would double-count the claims for its parts. An
  agreement with no named counterparty is accepted only in the
  singular for that reason.

**Status is a gate, not a field.** `read_commitment_status` reads one
proposition deterministically and names what it says -- executed,
opportunity, in discussion, expected, non-definitive, not a customer
commitment, partnership only, or unknown. A claim can be constructed
only from a proposition that reads as `EXECUTED`; every other reading
is a reason there is no claim, never a weaker claim. Blocking language
wins over execution language, so "signed a non-binding MoU" is
non-definitive and "can be contracted" is an opportunity.

**Everything is grounded in one proposition.** `commitment_text` is a
verbatim span of the source sentence, and the counterparty, the
agreement, every quantity, the duration and the window must each appear
inside it. Nothing is borrowed from a neighbouring sentence: "The
agreements, which are also for 20 years, cover 2,176 megawatts" names
no counterparty and states no execution, so it is not a claim, however
obvious its antecedent is to a reader.

**A neighbour may add terms only through an explicit link** (Stage 5.2).
A `CommitmentSupport` carries terms a nearby sentence of the same
speaker's turn states, tied to the claim by a `SourceEvidenceLink` whose
own words justify it ("The agreements, which are also for 20 years...",
"the operating capacity", "strategic customer agreements, or SCAs").
Supports sit beside the claim's own terms rather than inside them, never
name the customer, and never change which commitment the claim is.
`commitment_links` finds the links; it builds no claims.

**No economics.** There is no price, revenue, earnings, cash-flow or
value field, and a quantity cannot be in a currency: nothing the real
corpus says about these agreements prices them, and a megawatt is not a
dollar. There is no movement or polarity either -- first observation is
not "raised". Quantities are never converted, summed or compared across
commitment kinds: 6 gigawatts of GPUs deployed and 2,176 megawatts of
nuclear capacity sold are different quantities in the same unit.

**Separate from historical analysis, and inert.** Nothing in Atlas's
analysis or decision path imports it, and it does not satisfy
`ForwardEconomicSignal`, so it cannot enter the synthesis by accident.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.forward_claims.contracts import ClaimBound, ClaimantRole, HorizonKind

__all__ = [
    "LINK_WINDOW",
    "SUPPORTED_QUANTITY_UNITS",
    "CommitmentKind",
    "CommitmentStatus",
    "CommitmentStatusReading",
    "CommitmentSupport",
    "CommittedQuantity",
    "CommitmentTerm",
    "CommitmentWindow",
    "CustomerCommitmentClaim",
    "SourceEvidenceLink",
    "SourceLinkKind",
    "commitment_noun_pattern",
    "read_commitment_status",
]


class CommitmentKind(str, Enum):
    """What the customer committed to take. Two kinds, because the real
    corpus shows exactly two and they do not share a meaning: a
    gigawatt in one is not a gigawatt in the other."""

    POWER_PURCHASE = "power_purchase"
    """Electricity and/or capacity from the company's generation (VST's
    nuclear PPAs with Amazon Web Services and Meta). A quantity counts
    generating capacity."""
    PRODUCT_SUPPLY = "product_supply"
    """The company's products, supplied or deployed (AMD's Instinct GPUs
    for OpenAI). A quantity counts whatever the source counts -- for
    AMD, gigawatts of GPUs deployed -- and never generating capacity."""


class CommitmentStatus(str, Enum):
    """What one proposition says about whether a commitment exists.
    Only `EXECUTED` can become a claim."""

    EXECUTED = "executed"
    """The company states it has signed, executed, contracted, completed,
    concluded, finalized, entered into or announced an agreement or
    contract."""
    OPPORTUNITY = "opportunity"
    """Opportunity, pipeline, potential, "can be contracted", a modal --
    the commitment does not exist yet."""
    IN_DISCUSSION = "in_discussion"
    """Discussions, conversations, negotiations."""
    EXPECTED = "expected"
    """The commitment is placed in the future or made conditional: "expect
    to conclude agreements", "will sign", "when they're ready to sign"."""
    NON_DEFINITIVE = "non_definitive"
    """MoU, letter of intent, term sheet, framework agreement, non-binding.
    Not necessarily unenforceable -- just not presented as the definitive
    commitment."""
    NOT_A_CUSTOMER_COMMITMENT = "not_a_customer_commitment"
    """An acquisition, merger, divestiture, debt, credit or financing
    agreement."""
    PARTNERSHIP_ONLY = "partnership_only"
    """A partnership, collaboration or relationship with no concluded
    agreement stated."""
    UNKNOWN = "unknown"
    """No status the rules can read: no execution language, a negation, or
    an agreement known only by reference ("this agreement")."""


@dataclass(frozen=True)
class CommitmentStatusReading:
    status: CommitmentStatus
    marker_text: str | None
    """The verbatim words that decided the status, when there are any."""


_COMMITMENT_VERB = r"(sign|enter|conclude|complete|execute|finaliz|secure|contract|announce|reach)\w*"

# Order is precedence: the first family that matches decides, and every
# blocking family is tried before execution language.
_BLOCKING: tuple[tuple[CommitmentStatus, re.Pattern[str]], ...] = (
    (CommitmentStatus.NON_DEFINITIVE, re.compile(
        r"\b(non-?binding|unbinding|MoUs?|memorand(um|a) of understanding|letters? of intent|LOIs?"
        r"|term sheets?|framework agreements?|heads of agreement)\b", re.I)),
    (CommitmentStatus.NOT_A_CUSTOMER_COMMITMENT, re.compile(
        r"\b(acqui(re|res|red|ring|sitions?)|mergers?|divest\w*|debt|credit agreements?|credit facilit\w+"
        r"|loans?|notes|indentures?|bonds?|financing)\b", re.I)),
    (CommitmentStatus.OPPORTUNITY, re.compile(
        r"\b(opportunit(y|ies)|pipeline|potential(ly)?|prospect(s|ive)?|possibl[ey]|(can|could) be contracted"
        r"|to contract|would|could|may|might)\b", re.I)),
    (CommitmentStatus.IN_DISCUSSION, re.compile(
        r"\b(discussions?|discussing|conversations?|negotiat\w+|talks|talking)\b", re.I)),
    (CommitmentStatus.EXPECTED, re.compile(
        r"\b(expect(s|ed|ing)?|anticipat(e|es|ed|ing)|plan(s|ned|ning)?|aim(s|ed|ing)?|intend(s|ed|ing)?"
        r"|hop(e|es|ed|ing)|seek(s|ing)?|look(s|ing)? forward)\s+(\w+\s+){0,2}?to\s+"
        + _COMMITMENT_VERB
        + r"|\bwill\s+(\w+\s+)?" + _COMMITMENT_VERB
        + r"|\b(if|once|when|unless)\b[^.;]{0,40}?\b" + _COMMITMENT_VERB, re.I)),
    (CommitmentStatus.UNKNOWN, re.compile(r"\b(not|never|yet to)\b", re.I)),
)
_EXECUTION = re.compile(
    r"\b(we|we've|has|have|had)\s+((now|already|successfully|recently|also)\s+)*"
    r"(signed|executed|contracted|completed|concluded|finalized|entered into|announced)\b",
    re.I,
)
_PARTNERSHIP = re.compile(r"\b(partnerships?|partner(s|ed|ing)?|collaborat\w+|relationships?|alliances?)\b", re.I)


def _noun_alternation(acronyms: frozenset[str], plural_only: bool = False) -> str:
    words = ["agreements", "contracts", "PPAs"] if plural_only else ["agreements?", "contracts?", "PPAs?"]
    words += [re.escape(a) + ("s" if plural_only else "s?") for a in sorted(acronyms)]
    return "|".join(words)


def commitment_noun_pattern(acronyms: frozenset[str] = frozenset(), plural_only: bool = False) -> re.Pattern[str]:
    """Agreement nouns, plus any acronym the same source has just defined
    as one (`commitment_links`). Never a fixed list of issuers' terms."""
    return re.compile(r"\b(" + _noun_alternation(acronyms, plural_only) + r")\b", re.I)


def _executed_agreement(nouns: str) -> re.Pattern[str]:
    """ "the recently announced power purchase agreement" -- execution
    stated by a participle on the agreement itself, not by a verb.
    "Contracted" is excluded: "contracted renewables" names assets."""
    return re.compile(
        r"\b(?:the|our|this|its|a|an)\s+(?:(?:recently|newly|previously|already)\s+)?"
        r"(?:announced|signed|executed|finalized|concluded)\s+(?:[\w-]+\s+){0,3}?(?:" + nouns + r")\b",
        re.I,
    )


def read_commitment_status(proposition: str, acronyms: frozenset[str] = frozenset()) -> CommitmentStatusReading:
    """Pure and deterministic. Reads one proposition -- a sentence, or
    the span of one that states the commitment -- and never looks at its
    neighbours. Execution needs an agreement noun and either an execution
    verb with the company as actor or an execution participle on the
    agreement itself; any blocking word anywhere in the proposition
    overrides it. `acronyms` are agreement acronyms defined nearby in the
    same source -- the only way a neighbouring sentence influences a
    reading."""
    for status, pattern in _BLOCKING:
        match = pattern.search(proposition)
        if match:
            return CommitmentStatusReading(status, match.group(0))
    nouns = commitment_noun_pattern(acronyms)
    execution = _EXECUTION.search(proposition)
    if execution and nouns.search(proposition):
        return CommitmentStatusReading(CommitmentStatus.EXECUTED, execution.group(0))
    participle = _executed_agreement(_noun_alternation(acronyms)).search(proposition)
    if participle:
        return CommitmentStatusReading(CommitmentStatus.EXECUTED, participle.group(0))
    partnership = _PARTNERSHIP.search(proposition)
    if partnership:
        return CommitmentStatusReading(CommitmentStatus.PARTNERSHIP_ONLY, partnership.group(0))
    return CommitmentStatusReading(CommitmentStatus.UNKNOWN, None)


SUPPORTED_QUANTITY_UNITS = frozenset({"MW", "GW"})
"""The units real executed commitments are stated in. Deliberately no
currency: no committed amount of money appears in any real commitment
proposition, and a currency here is where invented revenue would enter."""


@dataclass(frozen=True)
class CommittedQuantity:
    """One committed amount, exactly as stated. A commitment can have
    several -- Meta's agreements cover "2,176 megawatts of operating
    capacity and an additional 433 megawatts of upgrades" -- and they
    stay separate: Atlas does not add them into a total the source did
    not state, or split them into contracts the source did not itemize."""

    bound: ClaimBound
    value_low: float
    value_high: float
    unit: str
    """"MW" or "GW", as stated. Never converted between the two."""
    value_text: str
    """The amount verbatim: "1,200 megawatts"."""
    measure_text: str | None
    """What is being counted, verbatim, when the source says: "of
    operating capacity", "of Instinct GPUs". `None` when it does not --
    AWS's "1,200 megawatts" names no measure -- and then only
    `commitment_kind` says what the unit counts."""


@dataclass(frozen=True)
class CommitmentTerm:
    """A numeric duration the source states ("20-year", "five-year").
    Kept apart from quantities: a year is not a megawatt. "Multiyear"
    and "long-term" state no number and are not terms."""

    years: float
    text: str


@dataclass(frozen=True)
class CommitmentWindow:
    """When the committed quantity is delivered or supplied, in explicit
    years -- "second half of 2026" is start 2026; "2031-2034" is both
    ends; "through 2027" is an end only. Either end may be unknown, and
    unknown is not filled in from the duration or from anywhere else.
    The text keeps any finer grain the years drop."""

    start_year: int | None
    end_year: int | None
    horizon_kind: HorizonKind
    text: str


def _fold(text: str) -> str:
    return " ".join(text.casefold().split())


def _check_terms(
    quantities: tuple[CommittedQuantity, ...], term: CommitmentTerm | None, delivery: CommitmentWindow | None
) -> None:
    for q in quantities:
        if q.unit not in SUPPORTED_QUANTITY_UNITS:
            raise ValueError(f"unsupported quantity unit {q.unit!r}")
        if not 0 < q.value_low <= q.value_high:
            raise ValueError("a committed quantity is positive and value_low <= value_high")
        if q.bound is not ClaimBound.RANGE and q.value_low != q.value_high:
            raise ValueError("only a RANGE has two different values")
    if term is not None and term.years <= 0:
        raise ValueError("a term is a positive number of years")
    if delivery is not None:
        start, end = delivery.start_year, delivery.end_year
        if start is None and end is None:
            raise ValueError("a window states at least one year")
        if start is not None and end is not None and start > end:
            raise ValueError("a window cannot end before it starts")


def _term_texts(
    quantities: tuple[CommittedQuantity, ...], term: CommitmentTerm | None, delivery: CommitmentWindow | None
) -> list[str]:
    texts = [t for q in quantities for t in (q.value_text, q.measure_text) if t is not None]
    texts += [term.text] if term is not None else []
    texts += [delivery.text] if delivery is not None else []
    return texts


LINK_WINDOW = 2
"""How far apart, in sentences of one speaker's turn, a link may reach.
Every explicit link in the real corpus is one or two sentences long; the
ones that are not explicit ("Uprate capacity" three sentences after
"upgrade capacity", energization dates about "the site") are no closer
for a wider window, only more dangerous."""


class SourceLinkKind(str, Enum):
    """How two sentences of one source are connected -- never what the
    connection means economically."""

    EXPLICIT_BACK_REFERENCE = "explicit_back_reference"
    """A determiner and an agreement noun pointing back at the one
    executed commitment just stated: "this 20-year agreement", "Under this
    agreement", "The agreements"."""
    COMPONENT_REFERENCE = "component_reference"
    """A definite repetition of a component that a back-referencing
    sentence has just quantified: "the operating capacity" after "2,176
    megawatts of operating capacity"."""
    ACRONYM_DEFINITION = "acronym_definition"
    """The source defining an acronym as an agreement ("strategic customer
    agreements, or SCAs"), so that "our first five-year SCA" reads as
    one."""


@dataclass(frozen=True)
class SourceEvidenceLink:
    """Why one sentence belongs to a commitment another sentence states --
    the answer Atlas must be able to give for every link. Both sentences
    are from one source record (one speaker's turn), the link points only
    backward, and `reference_text` is the explicit wording that makes it."""

    source_record_id: str
    link_kind: SourceLinkKind
    anchor_index: int
    """The sentence stating the executed commitment the link serves."""
    referring_index: int
    antecedent_index: int
    """Always earlier than `referring_index`."""
    reference_text: str
    """The words in the referring sentence that point back: "this 20-year
    agreement", "the operating capacity", "SCA"."""
    antecedent_text: str
    """What they point at, verbatim from the antecedent sentence."""
    referring_sentence: str
    antecedent_sentence: str
    linker_version: str

    def __post_init__(self) -> None:
        if not self.antecedent_index < self.referring_index:
            raise ValueError("a link points backward only")
        if not self.reference_text or self.reference_text not in self.referring_sentence:
            raise ValueError("reference_text must be stated in the referring sentence")
        if not self.antecedent_text or self.antecedent_text not in self.antecedent_sentence:
            raise ValueError("antecedent_text must be stated in the antecedent sentence")
        indices = (self.anchor_index, self.referring_index, self.antecedent_index)
        if max(indices) - min(indices) > LINK_WINDOW:
            raise ValueError(f"a link reaches at most {LINK_WINDOW} sentences")
        if self.link_kind is SourceLinkKind.EXPLICIT_BACK_REFERENCE and self.antecedent_index != self.anchor_index:
            raise ValueError("a back-reference points at the commitment's own sentence")
        if self.link_kind is SourceLinkKind.ACRONYM_DEFINITION and self.referring_index != self.anchor_index:
            raise ValueError("an acronym definition serves the sentence that uses the acronym")
        if self.link_kind is SourceLinkKind.COMPONENT_REFERENCE and self.antecedent_index <= self.anchor_index:
            raise ValueError("a component reference points at the sentence that quantified the component")

    @property
    def id(self) -> str:
        return (
            f"{self.source_record_id}:link:{self.link_kind.value}:"
            f"{self.anchor_index}:{self.antecedent_index}->{self.referring_index}"
        )


@dataclass(frozen=True)
class CommitmentSupport:
    """Terms of a commitment stated in a linked sentence rather than in
    the commitment's own proposition -- kept apart from the claim's own
    terms, so what the anchor says and what a neighbour adds stay
    distinguishable. An acronym definition carries no terms: it only lets
    the anchor be read."""

    link: SourceEvidenceLink
    quantities: tuple[CommittedQuantity, ...] = ()
    term: CommitmentTerm | None = None
    window: CommitmentWindow | None = None
    component_text: str | None = None
    """What a quantity or window is about, when the sentence says:
    "the operating capacity at Perry", "Davis-Besse"."""

    def __post_init__(self) -> None:
        delivery = self.window
        has_terms = bool(self.quantities or self.term or delivery)
        if self.link.link_kind is SourceLinkKind.ACRONYM_DEFINITION:
            if has_terms or self.component_text is not None:
                raise ValueError("an acronym definition supports a reading, not a term")
            return
        if not has_terms:
            raise ValueError("a supporting sentence must state a quantity, a numeric duration or a window")
        reading = read_commitment_status(self.link.referring_sentence)
        if reading != CommitmentStatusReading(CommitmentStatus.UNKNOWN, None):
            raise ValueError(
                f"a supporting sentence states no status of its own; this one reads as {reading.status.value} "
                f"({reading.marker_text!r})"
            )
        texts = _term_texts(self.quantities, self.term, delivery)
        texts += [self.component_text] if self.component_text is not None else []
        for text in texts:
            if not text or text not in self.link.referring_sentence:
                raise ValueError(f"{text!r} is not stated in the supporting sentence")
        _check_terms(self.quantities, self.term, delivery)


@dataclass(frozen=True)
class CustomerCommitmentClaim:
    """One executed customer commitment, as one proposition states it,
    plus any terms explicitly linked neighbours add (`supports`).
    Construction enforces the boundary: an invalid claim cannot exist."""

    company: str
    commitment_kind: CommitmentKind

    counterparty_text: str | None
    """The customer as the source names it ("Amazon Web Services",
    "Meta"), verbatim and never normalized to an identity. `None` when
    unnamed -- allowed for a single stated agreement only. Never taken
    from a linked sentence: "our customer" stays unnamed."""
    agreement_text: str
    """The agreement as named: "20-year agreement", "comprehensive
    multiyear agreement". A group ("20-year agreements with Meta") stays
    one claim."""
    execution_text: str
    """The words that prove the commitment is concluded ("We have now
    contracted") -- what `read_commitment_status` reads as `EXECUTED`."""
    commitment_text: str
    """The proposition every other field is grounded in: a verbatim span
    of `source_text`."""

    quantities: tuple[CommittedQuantity, ...]
    term: CommitmentTerm | None
    window: CommitmentWindow | None

    claimant_role: ClaimantRole
    stated_by: str
    stated_by_title: str

    source_record_id: str
    source_kind: SourceKind
    source_text: str
    source_period: str | None
    """The fiscal quarter the call reported on -- when it was *said*, not
    when the agreement was signed or starts."""
    statement_at: datetime | None
    extractor_version: str
    """Which rule set, or which audit, produced this claim."""

    sentence_index: int | None = None
    """Where `source_text` sits in its source record -- required once a
    claim has supports, because every link is anchored to it."""
    supports: tuple[CommitmentSupport, ...] = ()

    def __post_init__(self) -> None:
        if self.claimant_role is not ClaimantRole.EXECUTIVE:
            raise ValueError("only a company insider can state the company's commitment")
        if not self.commitment_text or self.commitment_text not in self.source_text:
            raise ValueError("commitment_text must be a verbatim span of source_text")
        self._check_supports()
        acronyms = frozenset(
            s.link.reference_text for s in self.supports if s.link.link_kind is SourceLinkKind.ACRONYM_DEFINITION
        )
        reading = read_commitment_status(self.commitment_text, acronyms)
        if reading.status is not CommitmentStatus.EXECUTED:
            raise ValueError(f"the proposition reads as {reading.status.value} ({reading.marker_text!r}), not executed")
        if reading.marker_text != self.execution_text:
            raise ValueError("execution_text must be the words the status reading found")
        if not commitment_noun_pattern(acronyms).search(self.agreement_text):
            raise ValueError("agreement_text must name an agreement, contract or PPA")
        delivery = self.window
        grounded = [self.agreement_text]
        grounded += [self.counterparty_text] if self.counterparty_text is not None else []
        grounded += _term_texts(self.quantities, self.term, delivery)
        for text in grounded:
            if not text or text not in self.commitment_text:
                raise ValueError(f"{text!r} is not stated in the commitment's own proposition")
        if self.counterparty_text is None and commitment_noun_pattern(acronyms, plural_only=True).search(self.agreement_text):
            raise ValueError("plural agreements with no named customer are a contracted position, not one commitment")
        linked_terms = any(s.quantities or s.term or s.window for s in self.supports)
        if not (self.quantities or self.term or delivery or linked_terms):
            raise ValueError("a commitment must state at least a quantity, a numeric duration or a window")
        _check_terms(self.quantities, self.term, delivery)

    def _check_supports(self) -> None:
        """Every support must chain back to this claim's own sentence, in
        this claim's own source record."""
        if not self.supports:
            return
        if self.sentence_index is None:
            raise ValueError("a claim with supports must say which sentence it is")
        back_references = {
            s.link.referring_index: s.link.referring_sentence
            for s in self.supports
            if s.link.link_kind is SourceLinkKind.EXPLICIT_BACK_REFERENCE
        }
        for support in self.supports:
            link = support.link
            if link.source_record_id != self.source_record_id or link.anchor_index != self.sentence_index:
                raise ValueError("a support must be linked to this claim's own sentence in its own source")
            if link.link_kind is SourceLinkKind.EXPLICIT_BACK_REFERENCE and link.antecedent_sentence != self.source_text:
                raise ValueError("a back-reference must point at this claim's sentence")
            if link.link_kind is SourceLinkKind.ACRONYM_DEFINITION and link.referring_sentence != self.source_text:
                raise ValueError("an acronym definition must serve this claim's sentence")
            if link.link_kind is SourceLinkKind.COMPONENT_REFERENCE and (
                back_references.get(link.antecedent_index) != link.antecedent_sentence
            ):
                raise ValueError("a component reference must point at one of this claim's back-references")

    @property
    def id(self) -> str:
        """Provenance identity: deterministic, one per stated commitment
        per statement. Two commitments in one sentence (AWS and Meta)
        get two ids; the same statement never yields two."""
        basis = "|".join((self.commitment_kind.value, self.counterparty_text or "", self.agreement_text, self.commitment_text))
        return f"{self.source_record_id}:commitment:{hashlib.sha256(basis.encode()).hexdigest()[:16]}"

    @property
    def comparison_key(self) -> tuple[str, CommitmentKind, str] | None:
        """What a later stage may compare across statements to see a
        commitment change -- company, kind and customer, and nothing that
        can move (quantity, term, window, period). Customer names match
        only as stated ("Amazon" and "Amazon Web Services" do not), so a
        missed match is possible and a false one is not. `None` without
        a named customer: two unnamed commitments cannot be told apart."""
        if self.counterparty_text is None:
            return None
        return (self.company, self.commitment_kind, _fold(self.counterparty_text))
