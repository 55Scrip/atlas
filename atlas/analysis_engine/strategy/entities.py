"""The named things management referred to, kept with what was said about them.

Sprint 13 tried to join a strategy node to a dimensional fact and found
the node→entity edge missing almost everywhere: VST's filings name 299
entities and its strategy graph reached exactly one of them. The reason
is visible in one line of `extraction.py` -- `subject_text=mention.surface`
-- where a sentence becomes the canonical factor it resolved to.
"the data center at Comanche Peak is completed on schedule" becomes
`data center`, and the plant is gone from everything except the
evidence text nobody indexes.

**Nothing was lost from the corpus.** `StrategyEvidence.source_text`
keeps the whole sentence. What was missing is a representation, so this
module adds one beside the node rather than changing how nodes are
built: extraction, node identity, factors and every existing node kind
are untouched.

**This is not named-entity recognition.** It reads only the passages
already attached to an existing strategy node, and it keeps a mention
only when the passage says something about it. A transcript is full of
analysts, quarters, currencies and product slogans; none of that
belongs here unless the strategy evidence itself put it there.

**Kind is evidence, and the corpus mostly does not supply it.** "our
partner, NVIDIA" says NVIDIA is a partner. "invest more than $200
million in Arizona" does not say Arizona is a geography -- a reader
knows that from the world, not from the sentence, and a rule that
guessed it would also make "in Clip" a geography. So `PARTNER` is the
only kind these four companies earn, and everything else is UNKNOWN.
That is a smaller answer than it looks: the useful part is the
relationship, which the preposition does state.

**Identity is never asserted.** A mention is a mention. "Comanche Peak"
does not become `vistra:ComanchePeakNuclearPowerPlantMember`, "West
Texas" does not become `TexasSegmentMember`, and two spellings of one
plant stay two mentions unless something other than their similarity
says otherwise.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

__all__ = [
    "STRATEGY_ENTITY_VERSION",
    "EntityKind",
    "EntityRelationship",
    "StrategyEntityMention",
    "entity_mentions",
]

STRATEGY_ENTITY_VERSION = "strategy-entities-1"


class EntityKind(str, Enum):
    """What the passage says the entity is.

    One member and UNKNOWN. Every other kind considered -- geography,
    facility, project, product, programme -- failed the same test: the
    corpus names the thing without saying what it is, and assigning a
    kind would mean supplying world knowledge the sentence does not
    contain. `UNKNOWN` is not a gap here; it is the finding."""

    PARTNER = "partner"
    """The passage itself says so: "GPUs from our partner, NVIDIA",
    "expanding this partnership in Mexico with Clip". The marker is the
    word, not the name."""

    UNKNOWN = "unknown"
    """Named, and the passage does not classify it. The normal answer,
    and the correct one for Comanche Peak, Arizona and West Texas."""


class EntityRelationship(str, Enum):
    """What the passage asserts between the node and the entity.

    Read from the preposition or verb that governs the mention, which is
    in the text, unlike the entity's kind. Anything not matched stays
    UNKNOWN rather than defaulting to a plausible edge -- a default here
    would give every entity the same relationship and make the whole
    representation worthless."""

    LOCATED_AT = "located_at"
    """Sited at the named place: "the data center at Comanche Peak"."""
    INVESTS_IN = "invests_in"
    """Money directed at it: "invest more than $200 million in Arizona"."""
    PARTNERS_WITH = "partners_with"
    """Named as a counterparty: "with Clip", "our partner, NVIDIA"."""
    INCLUDES = "includes"
    """Named as one of a list the node's subject enumerates: "through
    distribution partners, one to many, including FIS, WPP, and
    Comcast advertising"."""
    UNKNOWN_RELATIONSHIP = "unknown_relationship"


@dataclass(frozen=True)
class StrategyEntityMention:
    """One named thing, one strategy node, one passage.

    Deliberately an observation rather than an entity: repeated mentions
    across quarters are repeated rows, because merging them would be a
    continuity claim and nothing here is entitled to make one."""

    node_id: str
    mention_text: str
    """Exactly as management wrote it, including case and spacing."""
    entity_kind: EntityKind
    relationship: EntityRelationship
    source_record_id: str
    source_passage: str
    source_period: str
    speaker_title: str | None = None
    is_management_authored: bool = True
    """Always true: the only input is management evidence already
    attached to a node. Recorded rather than assumed, because a later
    consumer must not read entity extraction as independent
    corroboration."""

    @property
    def continuity_key(self) -> str:
        """What would have to match for two mentions to be the same thing.

        The exact surface text, case-folded and whitespace-collapsed,
        and nothing else -- no stemming, no substring, no similarity. So
        "West Texas" and "Texas" never collide, "Google Cloud" and
        "Cloud" never collide, and "Comanche Peak" and "Comanche Peak
        Nuclear Power Plant" stay separate until something other than
        their spelling joins them."""
        return " ".join(self.mention_text.split()).casefold()


#: A candidate is a run of capitalised words, allowing lowercase joiners
#: inside it ("Bank of America"). Deliberately not a parser: the job is
#: to find where a name *might* be, and every rule after this one is
#: about throwing candidates away.
_CANDIDATE = re.compile(
    r"\b[A-Z][\w&.'-]*(?:\s+(?:of|and|the|de|for)\s+[A-Z][\w&.'-]*|\s+[A-Z][\w&.'-]*)*")

#: Quantities, dates and money. A number with a unit is not a name,
#: however strategically important -- "4,500 megawatts" belongs to the
#: structures that already own quantities, not here.
_QUANTITY = re.compile(
    r"^(?:\$|€|£)?\d|"
    r"^(?:Q[1-4]|FY)\d*$|"
    r"^(?:January|February|March|April|May|June|July|August|September|October|November|December)$|"
    r"^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)$",
    re.I)

#: Words that begin a sentence or a clause and are capitalised only for
#: that reason. A candidate starting with one of these is trimmed rather
#: than dropped, so "Our partner, NVIDIA" still yields NVIDIA.
_SENTENCE_WORDS = frozenset({
    "a", "an", "and", "as", "at", "but", "by", "for", "from", "given", "however",
    "i", "if", "in", "it", "its", "last", "looking", "of", "on", "or", "our", "perhaps",
    "plus", "second", "so", "that", "the", "their", "then", "there", "these", "they",
    "third", "this", "to", "we", "what", "when", "while", "with", "additionally",
    "overall", "using", "during", "both", "first", "now", "also", "he", "she",
})

#: Capitalised phrases that are boilerplate, roles or organs of the call
#: rather than things a strategy concerns.
_NOT_AN_ENTITY = frozenset({
    "ceo", "cfo", "coo", "cto", "chief executive officer", "chief financial officer",
    "president", "chairman", "operator", "analyst", "gaap", "non-gaap", "sec",
    "securities and exchange commission", "safe harbor", "safe harbour",
    "q&a", "ir", "investor relations", "form 10-k", "form 10-q",
    # "AI" is capitalised everywhere in these transcripts and names no
    # thing; treating it as an entity is the specific error Sprint 13's
    # GOOGL control exists to prevent.
    "ai", "artificial intelligence",
    # Financial vocabulary. Capitalised by convention, owned by the
    # structures that already model money.
    "capex", "opex", "ebitda", "ebit", "roi", "roic", "fcf", "eps", "p&l",
})

#: A word that begins a sentence is capitalised for that reason alone.
#: A one-word candidate in that position is kept only when its own
#: shape says it is a name -- all capitals (NVIDIA, DRAM) or an internal
#: capital (CapEx, YouTube) -- because "Depending", "Having" and
#: "Looking" are otherwise indistinguishable from "Arizona".
_SENTENCE_START = re.compile(r"(?:^|[.!?]\s+|\A)$")

#: "As Sundar mentioned", "Philipp will talk more about" -- a person
#: being quoted or introduced, not a thing the strategy concerns.
_SPEAKER_REFERENCE = re.compile(
    r"\b(?:will|would|can|could)\s+(?:talk|comment|speak|walk|cover|share|discuss|take)\b"
    r"|^\s*(?:mentioned|said|noted|added|covered)\b", re.I)
_SPEAKER_INTRO = re.compile(r"\b(?:as|and|,)\s+$", re.I)

#: The preposition or verb immediately before a mention, and what it
#: asserts. Order matters: the longest, most specific marker wins.
_RELATIONSHIP_MARKERS: tuple[tuple[re.Pattern[str], EntityRelationship], ...] = (
    (re.compile(r"\bpartners?(?:hip)?[^.]{0,40}?\bwith\s+$", re.I), EntityRelationship.PARTNERS_WITH),
    (re.compile(r"\bpartner,\s+$", re.I), EntityRelationship.PARTNERS_WITH),
    (re.compile(r"\bincluding\s+(?:[A-Z][\w&.'-]*,?\s+(?:and\s+)?)*$"), EntityRelationship.INCLUDES),
    (re.compile(r"\b(?:invest|investing|invested|allocat\w+|spend\w*|commit\w*)[^.]{0,60}?\bin\s+$", re.I),
     EntityRelationship.INVESTS_IN),
    (re.compile(r"\b(?:at|located\s+at)\s+$", re.I), EntityRelationship.LOCATED_AT),
)

#: A possessive or a contraction carries the name plus a grammatical
#: tail. "YouTube's" is YouTube; "I've" and "AI's" are not entities at
#: all, and only survive the capitalisation test because of the tail.
_TAIL = re.compile(r"[\u2019']\s*(?:s|ve|re|ll|d|m)\b", re.I)
#: "AI-powered" is an adjective built from an excluded word.
_HYPHEN_ADJECTIVE = re.compile(r"^(.*?)-[a-z]")


def _strip_grammar(text: str) -> str:
    text = _TAIL.sub("", text)
    adjective = _HYPHEN_ADJECTIVE.match(text)
    if adjective and adjective.group(1):
        text = adjective.group(1)
    return text.strip()


def _trim(candidate: str) -> str:
    """Drop leading words that are capitalised only by position."""
    words = candidate.split()
    while words and words[0].casefold() in _SENTENCE_WORDS:
        words.pop(0)
    while words and words[-1].casefold() in _SENTENCE_WORDS:
        words.pop()
    return " ".join(words)


def _is_entity_candidate(text: str) -> bool:
    if not text or _QUANTITY.match(text):
        return False
    if text.casefold() in _NOT_AN_ENTITY:
        return False
    if len(text) < 2:
        return False
    # A single all-caps token of one or two letters is an abbreviation
    # in running prose far more often than a name.
    return not (len(text) <= 2 and text.isupper() and " " not in text)


#: Everything before the mention is the locative itself, so the
#: preposition opens the sentence: "At Google Marketing Live, we
#: showcased ...". That places the telling, not the thing.
_OPENS_THE_SENTENCE = re.compile(r"(?:^|[.!?]\s+)(?:at|located\s+at)\s*$", re.I)


def _relationship_for(passage: str, start: int) -> EntityRelationship:
    before = passage[:start]
    for pattern, relationship in _RELATIONSHIP_MARKERS:
        if not pattern.search(before):
            continue
        # "At Google Marketing Live, we showcased ..." is a venue, not a
        # site an initiative sits on. A locative that opens the sentence
        # is placing the telling, not the thing.
        if relationship is EntityRelationship.LOCATED_AT and _OPENS_THE_SENTENCE.search(before):
            return EntityRelationship.UNKNOWN_RELATIONSHIP
        return relationship
    return EntityRelationship.UNKNOWN_RELATIONSHIP


def _looks_like_a_name(text: str) -> bool:
    """Shape evidence that a single word is a name rather than a
    sentence's first word: all capitals, or a capital inside it."""
    return text.isupper() or any(c.isupper() for c in text[1:])


def _is_speaker_reference(passage: str, start: int, end: int) -> bool:
    after = passage[end:end + 40]
    before = passage[max(0, start - 6):start]
    return bool(_SPEAKER_REFERENCE.search(after)) and bool(_SPEAKER_INTRO.search(before) or True)


def _kind_for(relationship: EntityRelationship) -> EntityKind:
    """Kind only where the same clause that names the entity says it.

    An earlier version looked in a 60-character window either side, and
    on the real corpus that made "GPUs", "TPUs" and "Mexico" partners,
    because "our partner, NVIDIA" and "this partnership in Mexico with
    Clip" put the word near several names it does not describe. The
    window was measuring proximity, which is what this whole sprint
    exists to refuse.

    So kind is read from the construction that governs the mention, and
    that leaves exactly one: a name introduced as a counterparty is a
    partner. This makes `PARTNER` a restatement of `PARTNERS_WITH`
    rather than independent evidence, which is the honest position --
    across four companies these passages name things without saying
    what they are, and any richer taxonomy would be supplying world
    knowledge the sentences do not contain."""
    if relationship is EntityRelationship.PARTNERS_WITH:
        return EntityKind.PARTNER
    return EntityKind.UNKNOWN


def entity_mentions(
    *, node_id: str, passages: "list[tuple[str, str, str, str | None]]"
) -> tuple[StrategyEntityMention, ...]:
    """Named things in this node's own evidence.

    `passages` is `(text, record_id, period, speaker_title)` taken from
    the node's `evidence` -- never the company's whole transcript. A
    name in a sibling node's sentence belongs to that node.

    One row per (mention, passage): the same name in two quarters is two
    observations, because collapsing them would assert continuity.
    """
    out: list[StrategyEntityMention] = []
    seen: set[tuple[str, str, str]] = set()
    for text, record_id, period, speaker_title in passages:
        for match in _CANDIDATE.finditer(text):
            raw = match.group(0).rstrip(",;:")
            if not re.search(r"\b[A-Z]\.(?:[A-Z]\.)+$", raw):
                raw = raw.rstrip(".")
            trimmed = _strip_grammar(_trim(raw))
            if not _is_entity_candidate(trimmed):
                continue
            start = match.start() + raw.find(trimmed) if trimmed in raw else match.start()
            sentence_initial = not text[:start].strip(" \t") or bool(
                re.search(r"[.!?]\s+$", text[:start]))
            if sentence_initial and " " not in trimmed and not _looks_like_a_name(trimmed):
                continue
            if " " not in trimmed and _is_speaker_reference(text, start, start + len(trimmed)):
                continue
            key = (record_id, trimmed, text)
            if key in seen:
                continue          # the same name twice in one passage is one mention
            seen.add(key)
            relationship = _relationship_for(text, start)
            out.append(StrategyEntityMention(
                node_id=node_id,
                mention_text=trimmed,
                entity_kind=_kind_for(relationship),
                relationship=relationship,
                source_record_id=record_id,
                source_passage=text,
                source_period=period,
                speaker_title=speaker_title,
            ))
    return tuple(out)
