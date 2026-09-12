"""Deterministic commitment term reader (Forward-Looking Evidence,
Stage 5.3).

Stage 5.1 decides whether a sentence states an executed customer
commitment; Stage 5.2 decides which nearby sentences explicitly belong to
it. This module reads the commitment's terms out of exactly that
evidence and builds `CustomerCommitmentClaim`s -- the first automatic
claims.

**It reads only verified evidence.** Its input is a `CommitmentEvidence`
bundle: one executed anchor sentence plus the `SourceEvidenceLink`s
anchored to it. It never sees the rest of the transcript, so it cannot
wander to a neighbouring sentence the linker did not justify.

**No field without its own source span.** Every value is read from a
span inside the anchor proposition or a linked sentence, and the claim
types re-check that on construction:

- customer: "<agreement> with <Name>", from the anchor only -- a linked
  sentence never names the customer, and "our customer" stays unnamed;
- agreement: the agreement noun and its own modifiers ("20-year
  agreement", "long-term power purchase agreements");
- kind: only when the agreement's own words say it -- "power purchase" or
  "PPA", or "supply" -- or when it is listed under such agreements ("...
  power purchase agreements, including a 20-year agreement with ...").
  Otherwise `None`: a unit, an asset or an industry never decides it;
- quantities: "<number> megawatts/gigawatts [of <measure>]", with "up
  to" / "at least" / ranges as bounds and "approximately" kept in the
  text; no currency, no conversion, no sums;
- term: "N-year" on the agreement itself, or "for N years" right after
  it; never derived from dates;
- window: an explicit year with an explicit start ("commence in December
  of 2026") or end ("by 2034") -- a bare "in 2027" with no start verb
  states no delivery period at all. Delivery timing is kept apart from
  the contract term.

**Scope.** When one sentence states several commitments ("a 20-year
agreement with Amazon Web Services for 1,200 megawatts ... and 20-year
agreements with Meta covering 2,176 megawatts ..."), each customer owns
only what follows its own agreement phrase, up to the next one. A
quantity stated before any agreement phrase -- "approximately 3.8
gigawatts ... through multiple power purchase agreements" -- belongs to
no customer and is dropped. So are quantities of demand, growth,
markets, pipelines, potential or backlog.

**Withheld, with a reason.** An anchor that yields no claim says why:
no agreement phrase, a plural agreement with no named customer (a
position across customers), or no committed term at all ("we signed an
agreement" is not enough).

Inert: nothing in Atlas's analysis or decision path imports it, and the
claims feed no interpretation or synthesis.
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.forward_claims.commitment_links import find_commitment_links
from atlas.analysis_engine.forward_claims.commitments import (
    CommitmentKind,
    CommitmentStatus,
    CommitmentSupport,
    CommitmentTerm,
    CommitmentWindow,
    CommittedQuantity,
    CustomerCommitmentClaim,
    SourceEvidenceLink,
    SourceLinkKind,
    commitment_noun_pattern,
    read_commitment_status,
)
from atlas.analysis_engine.forward_claims.contracts import ClaimBound, ClaimantRole, HorizonKind
from atlas.analysis_engine.forward_claims.extraction import _SENTENCE, classify_claimant
from atlas.analysis_engine.forward_claims.source_time import period_ordinal, transcript_period

__all__ = [
    "TERM_READER_VERSION",
    "CommitmentEvidence",
    "WithholdReason",
    "WithheldCommitment",
    "commitment_evidence",
    "extract_customer_commitments",
    "read_commitment_evidence",
]

TERM_READER_VERSION = "commitment-terms-v1"


@dataclass(frozen=True)
class CommitmentEvidence:
    """Everything the reader is allowed to read about one commitment
    statement: the anchor sentence, the links anchored to it, and who
    said it where. Deliberately not the source record, whose full
    content would let a reader roam."""

    company: str
    source_record_id: str
    source_kind: SourceKind
    source_period: str | None
    claimant_role: ClaimantRole
    stated_by: str
    stated_by_title: str
    sentence_index: int
    sentence: str
    links: tuple[SourceEvidenceLink, ...]

    def __post_init__(self) -> None:
        for link in self.links:
            if link.source_record_id != self.source_record_id or link.anchor_index != self.sentence_index:
                raise ValueError("evidence holds only links anchored to its own sentence")


class WithholdReason(str, Enum):
    """Why an executed anchor produced no claim."""

    NOT_EXECUTED = "not_executed"
    """The anchor does not read as executed (a caller passed one anyway)."""
    NO_AGREEMENT_PHRASE = "no_agreement_phrase"
    """No agreement noun the execution words govern."""
    AGGREGATE_ACROSS_CUSTOMERS = "aggregate_across_customers"
    """Plural agreements and no named customer: a contracted position."""
    NO_COMMITTED_TERM = "no_committed_term"
    """An agreement exists, but no quantity, numeric term or window is
    stated for it -- here or in a linked sentence."""
    REJECTED_BY_CLAIM_CONTRACT = "rejected_by_claim_contract"
    """The reader's result failed the claim type's own checks. Should
    never happen; kept so a reader bug is visible rather than silent."""


@dataclass(frozen=True)
class WithheldCommitment:
    source_record_id: str
    sentence_index: int
    sentence: str
    reason: WithholdReason
    detail: str


_STOP = {
    "a", "an", "the", "our", "its", "their", "this", "that", "these", "those", "and", "or", "but", "with", "for",
    "of", "in", "to", "through", "including", "under", "by", "at", "on", "from", "is", "are", "was", "were", "be",
    "have", "has", "had", "we", "first", "second", "third", "fourth", "which", "such", "as", "into", "over",
    "across", "per", "while", "all", "both",
    # verbs that can sit right before an agreement noun ("both involve contracts")
    "involve", "involves", "include", "includes", "cover", "covers", "sign", "signs", "enter", "enters", "execute",
    "executes", "announce", "announces", "complete", "completes", "reach", "reaches", "secure", "secures", "win",
}
_CUSTOMER_AFTER = re.compile(r"\s+with\s+([A-Z][\w&'-]*(?:\s+[A-Z][\w&'-]*)*)")
_ENUMERATION = re.compile(r"\s*,?\s*(?:including|such as)\b")
_CLAUSE_END = re.compile(r";|,\s*(?:while|but|whereas)\b|,?\s+and\s+(?:we|our)\b|\.\s")
_POWER = re.compile(r"\bpower\s+purchase\b|\bPPAs?\b", re.I)
_SUPPLY = re.compile(r"\bsupply\b", re.I)
_NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "twelve": 12, "fifteen": 15, "twenty": 20, "twenty-five": 25, "thirty": 30,
}
_N = r"(\d+|" + "|".join(sorted(_NUMBER_WORDS, key=len, reverse=True)) + r")"
_TERM_ON_AGREEMENT = re.compile(r"\b" + _N + r"-year\b", re.I)
_TERM_AFTER = re.compile(
    r"^(?:\s+with\s+[A-Z][\w&'-]*(?:\s+[A-Z][\w&'-]*)*)?\s*,?\s*(?:(?:which|that)\s+(?:is|are|runs?|lasts?)\s+(?:also\s+)?)?"
    r"for\s+(" + _N[1:-1] + r")\s+years\b",
    re.I,
)
_QUANTITY = re.compile(
    r"(?:(?P<approx>approximately|about|around|roughly|nearly)\s+)?"
    r"(?:(?P<low>\d[\d,]*(?:\.\d+)?)\s*(?P<join>-|–|to|and)\s*)?"
    r"(?P<num>\d[\d,]*(?:\.\d+)?)[\s-]+(?P<unit>megawatts?|gigawatts?|MW|GW)\b(?![\s-]*hours?)",
)
_UNITS = {"megawatt": "MW", "megawatts": "MW", "mw": "MW", "gigawatt": "GW", "gigawatts": "GW", "gw": "GW"}
_NOT_COMMITTED = {
    "demand", "growth", "market", "markets", "pipeline", "opportunity", "opportunities", "potential", "backlog",
    "auction", "auctions", "queue",
}
_MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
_TIME = re.compile(
    r"\b(?P<prep>from|starting in|beginning in|through|until|by|in)\s+"
    r"(?:the\s+)?(?:(?:first|second)\s+half\s+of\s+|(?:first|second|third|fourth)\s+quarter\s+of\s+|(?:" + _MONTHS + r")\s+(?:of\s+)?)?"
    r"(?:(?P<basis>calendar|fiscal)\s+(?:year\s+)?)?(?P<year>20\d\d)\b",
    re.I,
)
_START_VERB = re.compile(r"^(?:commenc\w*|begin\w*|beginning|start\w*|coming|come|go|going)$", re.I)
_START_LANGUAGE = re.compile(r"\b(?:commenc\w*|begin\w*|start\w*|coming online|come online|go live)\b", re.I)


@dataclass(frozen=True)
class _Phrase:
    text: str
    start: int
    end: int
    customer: str | None
    after_customer: int


def _number(text: str) -> float:
    return float(text.replace(",", ""))


def _agreement_phrases(sentence: str, acronyms: frozenset[str]) -> list[_Phrase]:
    """Each agreement noun with its own modifiers -- lowercase words or
    "N-year", read backward until a determiner, preposition, ordinal,
    participle or punctuation -- and the customer named right after it."""
    phrases = []
    for noun in commitment_noun_pattern(acronyms).finditer(sentence):
        start, taken = noun.start(), 0
        for token in reversed(list(re.finditer(r"[\w'-]+", sentence[: noun.start()]))):
            word = token.group(0)
            if sentence[token.end(): start].strip() or taken == 4:
                break
            if word.lower() in _STOP or word.lower().endswith("ed") or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", word):
                break
            start, taken = token.start(), taken + 1
        customer = _CUSTOMER_AFTER.match(sentence, noun.end())
        phrases.append(_Phrase(
            text=sentence[start: noun.end()], start=start, end=noun.end(),
            customer=customer.group(1) if customer else None,
            after_customer=customer.end() if customer else noun.end(),
        ))
    return phrases


def _kind(phrase: _Phrase, phrases: list[_Phrase], sentence: str) -> CommitmentKind | None:
    def own(text: str) -> CommitmentKind | None:
        if _POWER.search(text):
            return CommitmentKind.POWER_PURCHASE
        if _SUPPLY.search(text):
            return CommitmentKind.PRODUCT_SUPPLY
        return None

    kind = own(phrase.text)
    if kind is not None:
        return kind
    for head in phrases:  # "... power purchase agreements, including a 20-year agreement with ..."
        if head.end <= phrase.start and head.customer is None and _ENUMERATION.match(sentence, head.end):
            return own(head.text)
    return None


def _term(text_after: str, phrase_text: str) -> CommitmentTerm | None:
    on_agreement = _TERM_ON_AGREEMENT.search(phrase_text)
    if on_agreement:
        n = on_agreement.group(1).lower()
        return CommitmentTerm(float(_NUMBER_WORDS.get(n, n)), on_agreement.group(0))
    after = _TERM_AFTER.match(text_after)
    if after:
        n = after.group(1).lower()
        text = after.group(0)
        return CommitmentTerm(float(_NUMBER_WORDS.get(n, n)), text[text.lower().rfind(n):])
    return None


def _quantities(text: str) -> tuple[CommittedQuantity, ...]:
    found = []
    for q in _QUANTITY.finditer(text):
        following = re.findall(r"[\w'-]+", text[q.end(): q.end() + 60])[:4]
        if {w.lower() for w in following} & _NOT_COMMITTED:
            continue
        measure_words = []
        if following and following[0].lower() == "of":
            for word in following[1:3]:
                if word.lower() in _STOP:
                    break
                measure_words.append(word)
        measure = None
        if measure_words:
            measure_start = text.index("of", q.end())
            measure = text[measure_start: text.index(measure_words[-1], measure_start) + len(measure_words[-1])]
        before = text[max(0, q.start() - 16): q.start()].lower()
        unit = _UNITS[q.group("unit").lower()]
        number = _number(q.group("num"))
        low_text, join = q.group("low"), q.group("join")
        if low_text and (join in ("-", "–", "to") or re.search(r"\bbetween\s*$", before)):
            bound, low, high = ClaimBound.RANGE, _number(low_text), number
        elif low_text:
            continue  # "433 and 500 megawatts" without "between": not one quantity
        elif re.search(r"\bup to\s*$", before):
            bound, low, high = ClaimBound.UPPER_BOUND, number, number
        elif re.search(r"\b(at least|more than|over|in excess of)\s*$", before):
            bound, low, high = ClaimBound.LOWER_BOUND, number, number
        else:
            bound, low, high = ClaimBound.POINT, number, number
        found.append(CommittedQuantity(bound, low, high, unit, q.group(0), measure))
    return tuple(found)


def _windows(text: str) -> list[tuple[CommitmentWindow, int, int]]:
    """(window, span start, span end) for each explicit start or end year.
    "in <year>" is a start only when start language comes before it."""
    found = []
    for t in _TIME.finditer(text):
        prep = t.group("prep").lower()
        if prep in ("through", "until", "by"):
            start_year, end_year = None, int(t.group("year"))
        elif prep in ("from", "starting in", "beginning in") or _START_LANGUAGE.search(text[: t.start()]):
            start_year, end_year = int(t.group("year")), None
        else:
            continue
        span_start = t.start()
        preceding = list(re.finditer(r"[\w'-]+", text[: t.start()]))[-3:]
        for token in preceding:
            if _START_VERB.match(token.group(0)):
                span_start = token.start()
                break
        basis = (t.group("basis") or "").lower()
        kind = {"calendar": HorizonKind.CALENDAR_YEAR, "fiscal": HorizonKind.FISCAL_YEAR}.get(basis, HorizonKind.UNSPECIFIED_YEAR)
        found.append((CommitmentWindow(start_year, end_year, kind, text[span_start: t.end()]), span_start, t.end()))
    return found


def _clause(text: str, start: int, stop: int) -> str:
    end = _CLAUSE_END.search(text, start, stop)
    return text[start: end.start() if end else stop]


def _supports(evidence: CommitmentEvidence) -> list[CommitmentSupport]:
    supports: list[CommitmentSupport] = []
    for link in evidence.links:
        if link.link_kind is SourceLinkKind.ACRONYM_DEFINITION:
            supports.append(CommitmentSupport(link))
            continue
        sentence = link.referring_sentence
        at = sentence.index(link.reference_text)
        after = sentence[at + len(link.reference_text):]
        quantities = _quantities(_clause(sentence, at, len(sentence)))
        term = _term(after, link.reference_text) if link.link_kind is SourceLinkKind.EXPLICIT_BACK_REFERENCE else None
        if quantities or term:
            supports.append(CommitmentSupport(link, quantities=quantities, term=term))
        previous_end = at
        for window, span_start, span_end in _windows(sentence[at:]):
            component = None
            if link.link_kind is SourceLinkKind.COMPONENT_REFERENCE:
                words = sentence[previous_end: at + span_start].strip(" ,").split()
                while words and words[0].lower() in {"and", "or", "while", "with"}:
                    words.pop(0)
                while words and words[-1].lower() in {"to", "and", "is", "are", "expected"}:
                    words.pop()
                component = " ".join(words) or None
            supports.append(CommitmentSupport(link, window=window, component_text=component))
            previous_end = at + span_end
    return supports


def read_commitment_evidence(
    evidence: CommitmentEvidence,
) -> tuple[tuple[CustomerCommitmentClaim, ...], tuple[WithheldCommitment, ...]]:
    """Claims for every commitment the anchor states, in sentence order,
    or the reason there are none. Pure and deterministic."""
    sentence = evidence.sentence

    def withhold(reason: WithholdReason, detail: str) -> WithheldCommitment:
        return WithheldCommitment(evidence.source_record_id, evidence.sentence_index, sentence, reason, detail)

    acronyms = frozenset(l.reference_text for l in evidence.links if l.link_kind is SourceLinkKind.ACRONYM_DEFINITION)
    reading = read_commitment_status(sentence, acronyms)
    if reading.status is not CommitmentStatus.EXECUTED:
        return (), (withhold(WithholdReason.NOT_EXECUTED, reading.status.value),)
    phrases = _agreement_phrases(sentence, acronyms)
    named, seen = [], set()
    for phrase in phrases:
        if phrase.customer and phrase.customer not in seen:
            named.append(phrase)
            seen.add(phrase.customer)
    if not named:
        marker_at = sentence.find(reading.marker_text or "")
        governed = next((p for p in phrases if p.end > marker_at), None)
        if governed is None:
            return (), (withhold(WithholdReason.NO_AGREEMENT_PHRASE, "no agreement noun after the execution words"),)
        if commitment_noun_pattern(acronyms, plural_only=True).search(governed.text):
            return (), (withhold(WithholdReason.AGGREGATE_ACROSS_CUSTOMERS, governed.text),)
        named = [governed]

    supports = _supports(evidence) if len(named) == 1 else []
    claims, withheld = [], []
    for i, phrase in enumerate(named):
        stop = named[i + 1].start if i + 1 < len(named) else len(sentence)
        scope = _clause(sentence, phrase.start, stop)
        quantities = _quantities(scope)
        term = _term(sentence[phrase.end:stop], phrase.text)
        windows = _windows(scope)
        window = windows[0][0] if len(windows) == 1 else None
        has_linked_terms = any(s.quantities or s.term or s.window for s in supports)
        if not (quantities or term or window or has_linked_terms):
            withheld.append(withhold(WithholdReason.NO_COMMITTED_TERM, phrase.customer or phrase.text))
            continue
        try:
            claims.append(CustomerCommitmentClaim(
                company=evidence.company,
                commitment_kind=_kind(phrase, phrases, sentence),
                counterparty_text=phrase.customer,
                agreement_text=phrase.text,
                execution_text=reading.marker_text or "",
                commitment_text=sentence,
                quantities=quantities,
                term=term,
                window=window,
                claimant_role=evidence.claimant_role,
                stated_by=evidence.stated_by,
                stated_by_title=evidence.stated_by_title,
                source_record_id=evidence.source_record_id,
                source_kind=evidence.source_kind,
                source_text=sentence,
                source_period=evidence.source_period,
                statement_at=None,
                extractor_version=TERM_READER_VERSION,
                sentence_index=evidence.sentence_index,
                supports=tuple(supports),
            ))
        except ValueError as error:
            withheld.append(withhold(WithholdReason.REJECTED_BY_CLAIM_CONTRACT, str(error)))
    return tuple(claims), tuple(withheld)


def commitment_evidence(record: BusinessRecord) -> tuple[CommitmentEvidence, ...]:
    """One bundle per executed anchor in an executive transcript record,
    holding that anchor's links and nothing else of the record."""
    if record.document_type is not SourceKind.TRANSCRIPT:
        return ()
    content = record.metadata.get("content")
    if not isinstance(content, str) or not content.strip():
        return ()
    title, speaker = record.metadata.get("title"), record.metadata.get("speaker")
    title = title if isinstance(title, str) else ""
    speaker = speaker if isinstance(speaker, str) else ""
    role = classify_claimant(title or None, speaker or None)
    if role is not ClaimantRole.EXECUTIVE:
        return ()
    sentences = [s.strip() for s in _SENTENCE.split(content) if s.strip()]
    links = find_commitment_links(record)
    acronym_anchors = {l.anchor_index for l in links if l.link_kind is SourceLinkKind.ACRONYM_DEFINITION}
    anchors = sorted(
        {i for i, s in enumerate(sentences) if read_commitment_status(s).status is CommitmentStatus.EXECUTED}
        | acronym_anchors
    )
    return tuple(
        CommitmentEvidence(
            company=record.company, source_record_id=record.id, source_kind=record.document_type,
            source_period=transcript_period(record), claimant_role=role, stated_by=speaker, stated_by_title=title,
            sentence_index=i, sentence=sentences[i], links=tuple(l for l in links if l.anchor_index == i),
        )
        for i in anchors
    )


def _source_order(record: BusinessRecord) -> tuple:
    ordinal = period_ordinal(transcript_period(record)) or (0, 0)
    index = record.metadata.get("statement_index")
    return (record.company, ordinal, index if isinstance(index, int) else -1, record.id)


def extract_customer_commitments(
    records: Iterable[BusinessRecord],
) -> tuple[tuple[CustomerCommitmentClaim, ...], tuple[WithheldCommitment, ...]]:
    """Every customer commitment claim the records state, in canonical
    source order (company, fiscal period, statement, sentence) whatever
    order the records arrive in. Restatements of one agreement in
    different statements or calls stay separate claims."""
    claims: list[CustomerCommitmentClaim] = []
    withheld: list[WithheldCommitment] = []
    for record in sorted(records, key=_source_order):
        for evidence in commitment_evidence(record):
            found, refused = read_commitment_evidence(evidence)
            claims.extend(found)
            withheld.extend(refused)
    return tuple(claims), tuple(withheld)
