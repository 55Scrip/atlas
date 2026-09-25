"""That a paragraph presents the table printed directly after it.

A filing says "The following is a summary of our principal facilities as of
August 28, 2025:" and then prints the table. Until Sprint 38 Atlas could not
even ask which came first: paragraphs and tables were filed in separate tuples,
each numbered from zero, so the sentence and the table it introduced were both
"index 0". `source_event_index` fixed the order. This records the one relation
that order makes visible.

It records presentation and stops there. That a paragraph introduces a table
does NOT say the paragraph governs the table's cells, that the table supports or
proves anything the paragraph claims, that either concerns a project, or that
two tables are the same anything. Those are readings. This layer has no
vocabulary for them and nothing consumes it.

The rule is narrow because the corpus made it narrow. A colon alone licenses
nothing: of 1,105 colon-terminated paragraphs in the held filings, 276 introduce
a bullet run and 75 introduce prose. Adjacency alone licenses nothing either: of
the 558 tables whose preceding paragraph does not end in a colon, 163 are
preceded by a bare page number, 156 by a heading, 52 by a units label such as
"(in millions)" and 132 by ordinary prose. Both together, measured over 1,387
adjudicated cases, were true 803 times and false none.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

TABLE_INTRODUCTION_VERSION = "1.0.0"


class LicensingBasis(str, Enum):
    """Why one record was emitted. Both are recorded when both hold, because a
    paragraph that names the following table *and* ends in a colon carries two
    pieces of source evidence and dropping either would be a smaller truth."""

    COLON_ADJACENCY = "colon_adjacency"
    """The paragraph's last sentence ends in a colon and the table is the next
    source object. Neither half suffices: see this module's own docstring for
    what each admits on its own."""

    EXPLICIT_DEICTIC_TABLE_REFERENCE = "explicit_deictic_table_reference"
    """The paragraph names the table that follows, definitely and forwards --
    "the following table", "the table below". The held corpus uses exactly these
    two forms, 273 and 28 times, plus one "the following maturity table". A
    backward reference ("the table above", "the preceding table", 22 of them)
    is not this, and neither is the bare word "table"."""


@dataclass(frozen=True)
class SourceLocator:
    """Where an object sits, precisely enough to survive repetition. Text is not
    an identifier: 870 paragraph texts occur more than once inside a single
    filing, and two filings of one issuer reuse the same event indices."""

    issuer: str
    accession: str
    section: str
    source_event_index: int


@dataclass(frozen=True)
class SourceParagraph:
    """A parsed paragraph, carrying the position the parser gave it. Deliberately
    `source_event_index` and not `order_index`: the per-tuple ordinal cannot
    order a paragraph against a table, which is the whole difficulty here."""

    issuer: str
    accession: str
    section: str
    source_event_index: int
    text: str
    period: str | None = None


@dataclass(frozen=True)
class SourceTable:
    """A parsed table. Its shape is carried because it identifies the object to a
    reader; nothing here reads the shape, and nothing reads the cells."""

    issuer: str
    accession: str
    section: str
    source_event_index: int
    row_count: int
    column_count: int
    period: str | None = None


@dataclass(frozen=True)
class TableIntroductionEvidence:
    introducer: SourceLocator
    table: SourceLocator
    licensing_surface: str
    """The verbatim sentence that does the introducing -- not the whole
    paragraph. Micron's Properties paragraph opens "Our corporate headquarters
    are located in Boise, Idaho." and ends "The following is a summary of our
    principal facilities as of August 28, 2025:". The second sentence licenses
    the record; the first says nothing about the table."""
    licensing_bases: tuple[LicensingBasis, ...]
    source_period: str | None
    version: str
