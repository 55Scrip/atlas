"""That a paragraph presents the table printed directly after it. Shadow only.

Presentation, not meaning: nothing here says what the table shows, whether it
supports the paragraph, or what either is about -- and nothing consumes it.
"""
from atlas.analysis_engine.table_introduction.contracts import (
    TABLE_INTRODUCTION_VERSION, LicensingBasis, SourceLocator, SourceParagraph, SourceTable,
    TableIntroductionEvidence,
)
from atlas.analysis_engine.table_introduction.reading import read_table_introductions

__all__ = ["TABLE_INTRODUCTION_VERSION", "LicensingBasis", "SourceLocator", "SourceParagraph",
           "SourceTable", "TableIntroductionEvidence", "read_table_introductions"]
