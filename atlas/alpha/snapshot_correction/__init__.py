"""Audited correction of snapshot rows that are not migration artifacts.

The first and so far only kind is `concurrency_duplicate`: a row written
twice because two composers of the same Case raced before snapshot
persistence became atomic. See `service.py` for what has to be proven before
anything is corrected, and `table.py` for why this does not reuse the
migration-artifact ledger.
"""
from atlas.alpha.snapshot_correction.service import (
    CorrectionPlan,
    CorrectionRefused,
    DuplicateCorrectionRequest,
    DuplicatePair,
    PlannedRetraction,
    apply_correction,
    ensure_schema,
    plan_correction,
)
from atlas.alpha.snapshot_correction.table import CONCURRENCY_DUPLICATE, RETRACT

__all__ = [
    "CONCURRENCY_DUPLICATE",
    "RETRACT",
    "CorrectionPlan",
    "CorrectionRefused",
    "DuplicateCorrectionRequest",
    "DuplicatePair",
    "PlannedRetraction",
    "apply_correction",
    "ensure_schema",
    "plan_correction",
]
