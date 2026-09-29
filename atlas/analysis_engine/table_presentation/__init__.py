"""That a table's own shape shows it presents no data. Shadow only.

One-sided: silence about a table means silence, never that it presents data. And
nothing consumes any of it.
"""
from atlas.analysis_engine.table_presentation.contracts import (
    MAX_NON_EMPTY_CELLS_WITHOUT_DATA, TABLE_PRESENTATION_VERSION, LicensingFeature, SourceLocator,
    SourceTable, TablePresentationEvidence, TablePresentationKind,
)
from atlas.analysis_engine.table_presentation.reading import (
    non_empty_cell_count, read_table_presentation,
)

__all__ = ["MAX_NON_EMPTY_CELLS_WITHOUT_DATA", "TABLE_PRESENTATION_VERSION", "LicensingFeature",
           "SourceLocator", "SourceTable", "TablePresentationEvidence", "TablePresentationKind",
           "non_empty_cell_count", "read_table_presentation"]
