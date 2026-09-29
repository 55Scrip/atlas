"""Reading "this table presents no data" off a parsed table's shape.

One question is asked of each table: how many of its cells carry any text? A
filing's page headers, cover pages, signature blocks and prose panels answer with
one, two or three. Its data matrices answer with eight or more.

What counts as text is the parser's answer, not a fresh one. `TableCell.text`
arrives already whitespace-collapsed and stripped, so a space, a non-breaking
space and an em space all reach this layer as the empty string. A lone "$", "%",
dash or "0" is text: the filing printed it, and counting it is the cautious
direction for one-sided evidence. Salesforce's acquisition-contribution table is
exactly why -- "Total revenues | $ | 399" and "Pretax income | 24" is five cells,
not three, and the rule leaves it alone.
"""
from __future__ import annotations

from collections.abc import Iterable

from atlas.analysis_engine.table_presentation.contracts import (
    MAX_NON_EMPTY_CELLS_WITHOUT_DATA,
    TABLE_PRESENTATION_VERSION,
    LicensingFeature,
    SourceLocator,
    SourceTable,
    TablePresentationEvidence,
    TablePresentationKind,
)

__all__ = ["non_empty_cell_count", "read_table_presentation"]


def non_empty_cell_count(cell_texts: Iterable[str]) -> int:
    """How many cells carry any character once surrounding space is removed."""
    return sum(1 for text in cell_texts if text.strip())


def read_table_presentation(
    tables: Iterable[SourceTable],
) -> tuple[TablePresentationEvidence, ...]:
    """Evidence for every table whose shape shows it presents no data.

    Silent about every other table, and that silence carries no meaning: a table
    with four or more non-empty cells may be a data matrix or a signature block,
    and this layer has nothing to say about which.
    """
    records: list[TablePresentationEvidence] = []
    for table in sorted(tables, key=lambda t: (t.issuer, t.accession, t.section,
                                               t.source_event_index)):
        observed = non_empty_cell_count(table.cell_texts)
        if observed > MAX_NON_EMPTY_CELLS_WITHOUT_DATA:
            continue
        records.append(
            TablePresentationEvidence(
                table=SourceLocator(issuer=table.issuer, accession=table.accession,
                                    section=table.section,
                                    source_event_index=table.source_event_index),
                kind=TablePresentationKind.NOT_A_DATA_PRESENTATION,
                licensing_feature=LicensingFeature.NON_EMPTY_CELL_COUNT,
                observed_value=observed,
                threshold=MAX_NON_EMPTY_CELLS_WITHOUT_DATA,
                source_period=table.period,
                version=TABLE_PRESENTATION_VERSION,
            )
        )
    return tuple(records)
