"""Reading paragraph-introduces-table out of a parsed filing.

Two conditions, both required, both measured. The paragraph must be the object
immediately before the table, and it must carry introducing syntax. Sprint 39
removed each in turn: without the adjacency the rule is 91% precise, without the
syntax 75%, and with both it was right 803 times out of 803.

"Immediately before" is exact here. The audit that measured this skipped
paragraphs that looked like page furniture, which recovered four records across
the corpus and required a regex guessing which paragraphs are page numbers.
Four records is not worth a guess, so this refuses them: the paragraph must be
the table's immediate predecessor among the section's paragraphs and tables.
Reference events are transparent, not skipped -- `FilingContent` keeps them in
their own tuple, so they are not in this ordering at all.
"""
from __future__ import annotations

import re
from collections.abc import Iterable

from atlas.analysis_engine.table_introduction.contracts import (
    TABLE_INTRODUCTION_VERSION,
    LicensingBasis,
    SourceLocator,
    SourceParagraph,
    SourceTable,
    TableIntroductionEvidence,
)

__all__ = ["read_table_introductions"]

#: A colon closing the paragraph. Trailing whitespace only -- a colon anywhere
#: earlier introduces something inside the sentence, not the table after it.
_TRAILING_COLON = re.compile(r":\s*$")

#: A list item. Its own lead-in is the paragraph above it, so a bullet never
#: introduces the table below it.
_BULLET = re.compile(r"^\s*[•▪●∙]")

#: A definite forward reference to the table being printed. The optional word is
#: there because the corpus contains "the following maturity table" once, which
#: is as much a forward reference as the other 273; admitting one intervening
#: word adds exactly that case and matches nothing else in 19,560 paragraphs.
#: "above", "preceding" and the bare noun "table" are deliberately absent.
_DEICTIC = re.compile(
    r"\bthe\s+following\s+(?:[A-Za-z()\-]+\s+)?tables?\b"
    r"|\bthe\s+tables?\s+below\b",
    re.IGNORECASE,
)

#: A sentence boundary: terminal punctuation, then space, then something that
#: starts a sentence. Splitting only before a capital or an opening bracket keeps
#: "ASU No. 2023-08" and "U.S., we" whole, which a bare ". " split would not.
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+(?=[A-Z(“])")


def _sentences(text: str) -> list[str]:
    return [s for s in (part.strip() for part in _SENTENCE_BREAK.split(text)) if s]


def _licensing(paragraph: SourceParagraph) -> tuple[tuple[LicensingBasis, ...], str] | None:
    """The bases the paragraph satisfies and the sentence that carries them.

    Returns `None` when the paragraph introduces nothing, which is the common
    case: most paragraphs that happen to sit above a table are headings, page
    numbers, units labels or ordinary prose.
    """
    text = paragraph.text
    if _BULLET.match(text):
        return None
    sentences = _sentences(text)
    if not sentences:
        return None

    bases: list[LicensingBasis] = []
    if _TRAILING_COLON.search(text):
        bases.append(LicensingBasis.COLON_ADJACENCY)
    deictic = [s for s in sentences if _DEICTIC.search(s)]
    if deictic:
        bases.append(LicensingBasis.EXPLICIT_DEICTIC_TABLE_REFERENCE)
    if not bases:
        return None

    #: The colon is terminal, so when it licenses the record the closing sentence
    #: is the surface. Otherwise it is the sentence that names the table.
    surface = sentences[-1] if LicensingBasis.COLON_ADJACENCY in bases else deictic[-1]
    return tuple(bases), surface


def read_table_introductions(
    paragraphs: Iterable[SourceParagraph], tables: Iterable[SourceTable],
) -> tuple[TableIntroductionEvidence, ...]:
    """Every table whose immediately preceding source object introduces it.

    One record per table at most, so the same paragraph and table can never be
    related twice. Documents are handled independently and in the order their
    objects occupy in their own source, never in the order they were passed.
    """
    by_document: dict[tuple[str, str, str], dict[int, SourceParagraph | SourceTable]] = {}
    for item in (*paragraphs, *tables):
        key = (item.issuer, item.accession, item.section)
        #: Two objects cannot share a position: `source_event_index` indexes one
        #: event, and one event becomes one object.
        by_document.setdefault(key, {})[item.source_event_index] = item

    records: list[TableIntroductionEvidence] = []
    for (issuer, accession, section), objects in sorted(by_document.items()):
        positions = sorted(objects)
        for index, position in enumerate(positions):
            table = objects[position]
            if not isinstance(table, SourceTable) or index == 0:
                continue
            paragraph = objects[positions[index - 1]]
            if not isinstance(paragraph, SourceParagraph):
                continue
            licensed = _licensing(paragraph)
            if licensed is None:
                continue
            bases, surface = licensed
            records.append(
                TableIntroductionEvidence(
                    introducer=SourceLocator(issuer=issuer, accession=accession, section=section,
                                             source_event_index=paragraph.source_event_index),
                    table=SourceLocator(issuer=issuer, accession=accession, section=section,
                                        source_event_index=table.source_event_index),
                    licensing_surface=surface,
                    licensing_bases=bases,
                    source_period=paragraph.period,
                    version=TABLE_INTRODUCTION_VERSION,
                )
            )
    return tuple(records)
