"""Cross-cutting contracts shared across `atlas.analysis_engine
.business_data` modules -- mirrors `atlas.analysis_engine.contracts`'s
own reason for existing: a shared vocabulary a stage module
(`validation.py`, `versioning.py`, `models.py`) can import without
importing the top-level `pipeline.py` orchestrator.
"""
from __future__ import annotations

from enum import Enum

__all__ = ["ValidationStatus"]


class ValidationStatus(str, Enum):
    """Phase 3's own named `BusinessRecord` field. `PENDING` never
    appears on a constructed `BusinessRecord` -- only `VALID` records
    are ever assembled into one (see `pipeline.py`); a document that
    fails validation stays a `ValidationRejection`
    (`validation.py`), never a `BusinessRecord` with this value set to
    `REJECTED`. Both non-`VALID` members are named for completeness and
    for any future caller that wants to describe validation state
    generically, not because this sprint constructs either."""

    PENDING = "pending"
    VALID = "valid"
    REJECTED = "rejected"
