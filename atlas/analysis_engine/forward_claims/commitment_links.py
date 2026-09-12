"""Source-local links between commitment statements (Forward-Looking
Evidence, Stage 5.2).

Most real commitments are not stated in one sentence. VST announces
"long-term power purchase agreements with Meta" and only the next
sentence says "The agreements, which are also for 20 years, cover 2,176
megawatts..."; Micron's "our first five-year SCA" is an agreement only
because two sentences earlier it said "strategic customer agreements, or
SCAs". This module finds those connections -- and only those that the
source itself spells out.

**No link without an explicit source reason.** Every link names the
words that make it (`reference_text`) and the words they point at
(`antecedent_text`). Three reasons exist, because three are all the real
corpus shows:

- an explicit back-reference -- a determiner and an agreement noun,
  "this 20-year agreement", "Under this agreement", "The agreements";
- a component reference -- "the operating capacity", repeating exactly a
  component the back-referencing sentence just quantified;
- an acronym definition -- "<words ending in agreement(s)>, or ABC" or
  "(ABC)", whose initials spell the acronym.

"Seems to be about the same thing" is never a reason: "Uprate capacity"
after "upgrade capacity", or energization dates for "the site", are not
linked, however obvious they are to a reader.

**Local only.** A link stays inside one source record -- one speaker's
turn -- and reaches at most `LINK_WINDOW` sentences, backward. It never
crosses from an analyst's question to an executive's answer, or from
prepared remarks to Q&A, and there is no transcript-wide memory.

**Refusal beats guessing.** No link when the window holds a second
executed commitment, when a different agreement (an acquisition, a debt
agreement) is mentioned in between, when the commitment sentence names
several customers ("with Amazon Web Services ... with Meta"), when a
plural reference meets a singular agreement or the reverse, when the
referring sentence carries status language of its own (an opportunity,
a discussion, a new signing), or when an acronym is defined two ways.

**Links, not claims.** The linker never builds a
`CustomerCommitmentClaim` and never reads a term out of a sentence. It
says which sentences belong together and why; turning a link into a
`CommitmentSupport` -- and a claim -- is a separate, reviewable step.
Inert like the rest of the package: nothing in Atlas's analysis or
decision path imports it.
"""
from __future__ import annotations

import re
from collections.abc import Sequence

from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.forward_claims.commitments import (
    LINK_WINDOW,
    CommitmentStatus,
    CommitmentStatusReading,
    SourceEvidenceLink,
    SourceLinkKind,
    _noun_alternation,
    commitment_noun_pattern,
    read_commitment_status,
)
from atlas.analysis_engine.forward_claims.contracts import ClaimantRole
from atlas.analysis_engine.forward_claims.extraction import _SENTENCE, classify_claimant

__all__ = ["LINKER_VERSION", "find_commitment_links", "link_commitment_sentences"]

LINKER_VERSION = "commitment-links-v1"

_NO_STATUS = CommitmentStatusReading(CommitmentStatus.UNKNOWN, None)
_ACRONYM_USE = re.compile(r"(?:,\s*or\s+|\(\s*)([A-Z]{2,6})s?\b")
_MODIFIER = r"(?:(?:\d+|[a-z]+)-year\s+|long-term\s+|multi-?year\s+|power\s+purchase\s+|supply\s+|customer\s+)*"
_CUSTOMER = re.compile(r"\bwith\s+([A-Z][\w.&'-]*(?:\s+[A-Z][\w.&'-]*)*)")
_QUANTIFIED = re.compile(r"\d[\d,.]*\s+(?:megawatts|gigawatts|MW|GW)\s+of\s+([a-z][a-z-]*(?:\s+[a-z][a-z-]*)?)")
_STOP = {"from", "at", "in", "for", "to", "of", "and", "with", "on", "by", "under", "across", "the"}


def _acronym_definitions(sentences: Sequence[str]) -> list[tuple[int, str, str]]:
    """(sentence, acronym, definition text) for every "... agreements, or
    ABCs" / "... agreement (ABC)" whose preceding words' initials spell
    the acronym and end in an agreement noun. An acronym defined two
    different ways in one source is dropped entirely."""
    found: list[tuple[int, str, str, str]] = []
    for i, sentence in enumerate(sentences):
        for match in _ACRONYM_USE.finditer(sentence):
            acronym = match.group(1)
            words = re.findall(r"[A-Za-z][\w-]*", sentence[: match.start()])[-len(acronym):]
            if len(words) != len(acronym) or "".join(w[0] for w in words).upper() != acronym:
                continue
            if not commitment_noun_pattern().fullmatch(words[-1]):
                continue
            start = sentence.rfind(words[0], 0, match.start())
            meaning = " ".join(w.casefold() for w in words).removesuffix("s")
            found.append((i, acronym, sentence[start: match.end()], meaning))
    meanings: dict[str, set[str]] = {}
    for _, acronym, _, meaning in found:
        meanings.setdefault(acronym, set()).add(meaning)
    return [(i, a, text) for i, a, text, _ in found if len(meanings[a]) == 1]


def _reference(acronyms: frozenset[str]) -> re.Pattern[str]:
    nouns = _noun_alternation(acronyms)
    return re.compile(r"\b(?:under\s+)?(?:this|that|the|these|those)\s+" + _MODIFIER + r"(?:" + nouns + r")\b", re.I)


def _anchor_phrase(sentence: str, reading: CommitmentStatusReading, acronyms: frozenset[str]) -> str | None:
    """The span from the execution words to the agreement noun they
    govern -- "we announced long-term power purchase agreements"."""
    start = sentence.find(reading.marker_text or "")
    noun = commitment_noun_pattern(acronyms).search(sentence, max(start, 0))
    if start < 0 or noun is None:
        return None
    return sentence[start: noun.end()]


def link_commitment_sentences(source_record_id: str, sentences: Sequence[str]) -> tuple[SourceEvidenceLink, ...]:
    """Pure and deterministic over one speaker's sentences, in order.
    Linear: each sentence looks back at most `LINK_WINDOW` sentences."""
    definitions = _acronym_definitions(sentences)

    def acronyms_at(i: int) -> frozenset[str]:
        return frozenset(a for d, a, _ in definitions if 0 < i - d <= LINK_WINDOW)

    def link(kind: SourceLinkKind, anchor: int, referring: int, antecedent: int, reference: str, target: str):
        return SourceEvidenceLink(
            source_record_id=source_record_id, link_kind=kind, anchor_index=anchor, referring_index=referring,
            antecedent_index=antecedent, reference_text=reference, antecedent_text=target,
            referring_sentence=sentences[referring], antecedent_sentence=sentences[antecedent],
            linker_version=LINKER_VERSION,
        )

    readings = [read_commitment_status(s, acronyms_at(i)) for i, s in enumerate(sentences)]
    anchors = {i for i, r in enumerate(readings) if r.status is CommitmentStatus.EXECUTED}
    links: list[SourceEvidenceLink] = []

    for i in sorted(anchors):
        if read_commitment_status(sentences[i]).status is CommitmentStatus.EXECUTED:
            continue  # readable on its own; no acronym needed
        for d, acronym, text in definitions:
            if 0 < i - d <= LINK_WINDOW and re.search(rf"\b{acronym}s?\b", sentences[i]):
                links.append(link(SourceLinkKind.ACRONYM_DEFINITION, i, i, d, acronym, text))

    supporters: dict[int, list[int]] = {}
    for k, sentence in enumerate(sentences):
        if k in anchors or readings[k] != _NO_STATUS:
            continue
        reference = _reference(acronyms_at(k)).search(sentence)
        if reference is None:
            continue
        candidates = [j for j in range(max(0, k - LINK_WINDOW), k) if j in anchors]
        if len(candidates) != 1:
            continue  # nothing to point at, or two things
        j = candidates[0]
        phrase = _anchor_phrase(sentences[j], readings[j], acronyms_at(j))
        if phrase is None or len(set(_CUSTOMER.findall(sentences[j]))) > 1:
            continue  # several customers in one sentence: "the agreement" is whose?
        anchor_plural = bool(commitment_noun_pattern(acronyms_at(j), plural_only=True).search(phrase))
        if anchor_plural and not _CUSTOMER.search(sentences[j]):
            continue  # plural and unnamed: a contracted position, not one commitment
        reference_plural = bool(commitment_noun_pattern(acronyms_at(k), plural_only=True).search(reference.group(0)))
        if reference_plural != anchor_plural:
            continue
        mentions = commitment_noun_pattern(acronyms_at(k))
        if any(m not in supporters.get(j, []) and mentions.search(sentences[m]) for m in range(j + 1, k)):
            continue  # another agreement came in between
        links.append(link(SourceLinkKind.EXPLICIT_BACK_REFERENCE, j, k, j, reference.group(0), phrase))
        supporters.setdefault(j, []).append(k)

    for j, ks in supporters.items():
        for k in ks:
            m = k + 1
            if m >= len(sentences) or m in anchors or m - j > LINK_WINDOW or readings[m] != _NO_STATUS:
                continue
            components: list[tuple[str, str]] = []
            for quantified in _QUANTIFIED.finditer(sentences[k]):
                words = quantified.group(1).split()
                while words and words[-1] in _STOP:
                    words.pop()
                if words and words[0] not in _STOP:
                    phrase = " ".join(words)
                    components.append((phrase, sentences[k][quantified.start(): quantified.start(1) + len(phrase)]))
            names = [c for c, _ in components]
            hits = [
                (c, full, re.search(rf"\bthe\s+{re.escape(c)}\b", sentences[m], re.I))
                for c, full in components
                if names.count(c) == 1
            ]
            hits = [h for h in hits if h[2] is not None]
            if len(hits) == 1:
                _, full, found = hits[0]
                links.append(link(SourceLinkKind.COMPONENT_REFERENCE, j, m, k, found.group(0), full))

    return tuple(sorted(links, key=lambda l: (l.anchor_index, l.referring_index, l.antecedent_index)))


def find_commitment_links(record: BusinessRecord) -> tuple[SourceEvidenceLink, ...]:
    """Links within one transcript record, for an executive speaker only:
    an analyst's words never ground a company's commitment."""
    if record.document_type is not SourceKind.TRANSCRIPT:
        return ()
    content = record.metadata.get("content")
    if not isinstance(content, str) or not content.strip():
        return ()
    title, speaker = record.metadata.get("title"), record.metadata.get("speaker")
    role = classify_claimant(title if isinstance(title, str) else None, speaker if isinstance(speaker, str) else None)
    if role is not ClaimantRole.EXECUTIVE:
        return ()
    if not commitment_noun_pattern().search(content):
        # No agreement noun anywhere in the turn: no anchor, reference or
        # acronym definition is possible (a defined acronym's expansion
        # itself ends in one), so there is nothing to link.
        return ()
    sentences = [s.strip() for s in _SENTENCE.split(content) if s.strip()]
    return link_commitment_sentences(record.id, sentences)
