"""The Knowledge Provider contract (Automatic Knowledge Ingestion
Framework). See `contract.py`/`outcome.py` for the full design
rationale."""
from __future__ import annotations

from .contract import KnowledgeProvider
from .outcome import (
    AcquisitionValidationStatus,
    ExtractionStatus,
    KnowledgeAcquisitionOutcome,
    summarize_acquisition,
)

__all__ = [
    "KnowledgeProvider",
    "AcquisitionValidationStatus",
    "ExtractionStatus",
    "KnowledgeAcquisitionOutcome",
    "summarize_acquisition",
]
