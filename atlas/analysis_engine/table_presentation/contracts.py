"""That a table's own shape shows it presents no data.

A filing sets a great deal in table markup that is not a table of anything: a
cover page, a signature block, a page header printed 97 times, a heading, two
cells of bulleted prose. Sprint 41 went looking for a way to tell those from a
real data matrix and found that the canonical answer is absent -- across 2,449
held tables there is not one `<th>`, `<thead>` or `<caption>`, and the attributes
that do exist (a width, a border, `border-collapse`) are on every single table,
so they separate nothing.

One thing survived falsification: a table with three or fewer non-empty cells is
not presenting data. On the sample where every label came from reading the table
rather than applying a predicate, that was right 15 times out of 15 with nothing
wrong, and it holds for all eleven issuers rather than one filer's template.

The evidence is deliberately ONE-SIDED. Four or more non-empty cells licenses
nothing at all: that population contains a signature block with nine cells and a
glossary with fifteen, and no measured feature separates them. So there is no
`DATA_PRESENTATION` here, and silence about a table means only silence.

It also does not mean the table may be ignored. A cover page and a page header
are part of the filing; this records what their shape shows about how they
present, and stops.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

TABLE_PRESENTATION_VERSION = "1.0.0"

#: Three or fewer. The adjudicated classes leave a gap rather than a boundary:
#: the tables read as presenting nothing carry 0, 1, 2, 3 and then 9 non-empty
#: cells, while the tables read as data start at 8. The threshold sits in the gap.
MAX_NON_EMPTY_CELLS_WITHOUT_DATA = 3


class TablePresentationKind(str, Enum):
    NOT_A_DATA_PRESENTATION = "not_a_data_presentation"
    """The table's shape shows it is not presenting a data matrix. There is no
    second member, because the converse was measured and refused."""


class LicensingFeature(str, Enum):
    NON_EMPTY_CELL_COUNT = "non_empty_cell_count"
    """How many of the table's cells carry any text at all. The only feature this
    layer reads, and it reads no further: which words a cell holds, whether they
    look like money, and whether they begin with a bullet are all measurable and
    all deliberately unused here."""


@dataclass(frozen=True)
class SourceLocator:
    """Which table, precisely. Shape is not an identifier: two filings of one
    issuer reuse the same event indices, and hundreds of tables share a shape."""

    issuer: str
    accession: str
    section: str
    source_event_index: int


@dataclass(frozen=True)
class SourceTable:
    """A parsed table, as this layer needs it: where it sits, and the text of its
    cells so their emptiness can be counted. Nothing reads a cell's words."""

    issuer: str
    accession: str
    section: str
    source_event_index: int
    cell_texts: tuple[str, ...]
    period: str | None = None


@dataclass(frozen=True)
class TablePresentationEvidence:
    table: SourceLocator
    kind: TablePresentationKind
    licensing_feature: LicensingFeature
    observed_value: int
    """The count itself, beside the threshold it was compared against, so a reader
    can check the decision rather than take it."""
    threshold: int
    source_period: str | None
    version: str
