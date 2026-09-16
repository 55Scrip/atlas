"""Plan and apply the retraction of a snapshot duplicated by a race.

Before snapshot persistence became atomic, two composers of the same Case
could both read the same head, both conclude the record had moved, and both
insert -- leaving two rows identical in every semantic field, milliseconds
apart. That cannot happen now, but rows written before the fix are still
there, and each one makes the history say Atlas observed something twice when
it observed it once.

This hides the later row and keeps the earlier one. It never deletes: the
duplicate keeps every column it had and gains a pointer to the ledger entry
explaining why it is no longer part of the effective timeline.

**What counts as proof.** Being milliseconds apart is what makes the race the
likely explanation, but it is never the evidence. Two rows are corrected only
when every semantic field is identical -- conclusion, stored payload,
transition, and the frozen evidence beneath them -- and when they are
*adjacent* in the surviving timeline. Adjacency matters: a Case that
legitimately returns to an earlier state has two rows with the same
conclusion, separated by a different observation, and that is real history,
not a duplicate. Comparing conclusions alone would also collapse the
evidence-only snapshots this system exists to keep, where the conclusion
stands still while the evidence under it moves.

Callers name explicit row ids. Nothing here resolves a ticker, and nothing
here searches for its own targets -- a correction that chose its own scope
could quietly widen.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from sqlalchemy import insert, select, update
from sqlalchemy.engine import Engine

from atlas.alpha.investment_case_change.table import (
    create_investment_case_snapshot_table,
    investment_case_snapshot_table,
)
from atlas.alpha.snapshot_correction.table import (
    CONCURRENCY_DUPLICATE,
    RETRACT,
    create_snapshot_correction_table,
    snapshot_correction_table,
)

__all__ = [
    "CorrectionRefused",
    "DuplicatePair",
    "DuplicateCorrectionRequest",
    "PlannedRetraction",
    "CorrectionPlan",
    "ensure_schema",
    "plan_correction",
    "apply_correction",
]

_SNAPSHOTS = "investment_case_snapshots"


class CorrectionRefused(RuntimeError):
    """A guard failed. Nothing is written, and the message says which."""


@dataclass(frozen=True)
class DuplicatePair:
    """One correction, addressed by row id. Never by ticker."""

    canonical_row_id: str
    duplicate_row_id: str


@dataclass(frozen=True)
class DuplicateCorrectionRequest:
    correction_id: str
    reason: str
    pairs: tuple[DuplicatePair, ...]
    kind: str = CONCURRENCY_DUPLICATE


@dataclass(frozen=True)
class PlannedRetraction:
    entry_id: str
    case_id: str
    canonical_row_id: str
    duplicate_row_id: str
    canonical_at: str
    duplicate_at: str
    gap_milliseconds: float
    content_hash: str
    verification: Mapping[str, Any]
    already_applied: bool


@dataclass(frozen=True)
class CorrectionPlan:
    correction_id: str
    retractions: tuple[PlannedRetraction, ...] = field(default_factory=tuple)

    @property
    def pending(self) -> tuple[PlannedRetraction, ...]:
        return tuple(r for r in self.retractions if not r.already_applied)


def ensure_schema(engine: Engine) -> None:
    create_investment_case_snapshot_table(engine)
    create_snapshot_correction_table(engine)


def _entry_id(correction_id: str, row_id: str) -> str:
    return f"{correction_id}/{_SNAPSHOTS}/{row_id}"


def _refuse(message: str) -> CorrectionRefused:
    return CorrectionRefused(message)


def _row(connection, row_id: str) -> Mapping[str, Any] | None:
    return (
        connection.execute(
            select(investment_case_snapshot_table)
            .where(investment_case_snapshot_table.c.id == row_id)
        )
        .mappings()
        .first()
    )


def _live_rows(connection, case_id: str) -> list[Mapping[str, Any]]:
    return list(
        connection.execute(
            select(investment_case_snapshot_table)
            .where(investment_case_snapshot_table.c.case_id == case_id,
                   investment_case_snapshot_table.c.retracted_by.is_(None))
            .order_by(investment_case_snapshot_table.c.captured_at)
        )
        .mappings()
        .all()
    )


def _evidence(row: Mapping[str, Any]) -> Any:
    return json.loads(row["snapshot_json"]).get("valuation_evidence")


def _plan_pair(connection, request: DuplicateCorrectionRequest, pair: DuplicatePair) -> PlannedRetraction:
    canonical = _row(connection, pair.canonical_row_id)
    duplicate = _row(connection, pair.duplicate_row_id)
    if canonical is None:
        raise _refuse(f"canonical row {pair.canonical_row_id!r} does not exist")
    if duplicate is None:
        raise _refuse(f"duplicate row {pair.duplicate_row_id!r} does not exist")
    if canonical["id"] == duplicate["id"]:
        raise _refuse(f"{pair.duplicate_row_id!r}: a row cannot be its own duplicate")

    entry_id = _entry_id(request.correction_id, duplicate["id"])
    already = duplicate["retracted_by"] == entry_id
    if duplicate["retracted_by"] is not None and not already:
        raise _refuse(
            f"{duplicate['id']!r} was already retracted by {duplicate['retracted_by']!r}")
    if canonical["retracted_by"] is not None:
        raise _refuse(
            f"canonical {canonical['id']!r} is itself retracted by {canonical['retracted_by']!r}")

    if canonical["case_id"] != duplicate["case_id"]:
        raise _refuse(f"{duplicate['id']!r}: rows belong to different Cases")
    if canonical["captured_at"] >= duplicate["captured_at"]:
        raise _refuse(
            f"{duplicate['id']!r}: the canonical row must be the earlier one "
            f"({canonical['captured_at']} is not before {duplicate['captured_at']})")

    checks = {
        "same_case": canonical["case_id"] == duplicate["case_id"],
        "same_content_hash": canonical["content_hash"] == duplicate["content_hash"],
        "same_snapshot_json": canonical["snapshot_json"] == duplicate["snapshot_json"],
        "same_change_intelligence": (canonical["change_intelligence_json"]
                                     == duplicate["change_intelligence_json"]),
        "same_current_yield": canonical["current_yield"] == duplicate["current_yield"],
        # Redundant given `same_snapshot_json`, and stated anyway: a row whose
        # frozen evidence differs is a different observation, never a duplicate.
        "same_frozen_evidence": _evidence(canonical) == _evidence(duplicate),
        "canonical_is_earlier": True,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise _refuse(f"{duplicate['id']!r}: not a proven duplicate -- failed {', '.join(failed)}")

    # Adjacency, unless this correction has already been applied (in which case
    # the duplicate is no longer in the live timeline to be adjacent to).
    if not already:
        live = _live_rows(connection, canonical["case_id"])
        positions = {row["id"]: index for index, row in enumerate(live)}
        if canonical["id"] not in positions or duplicate["id"] not in positions:
            raise _refuse(f"{duplicate['id']!r}: both rows must be live to be compared")
        if positions[duplicate["id"]] - positions[canonical["id"]] != 1:
            raise _refuse(
                f"{duplicate['id']!r}: another surviving observation sits between the two rows, "
                "so this is a legitimate return to an earlier state, not a duplicate")
        checks["adjacent_in_live_timeline"] = True
    else:
        checks["adjacent_in_live_timeline"] = "already applied"

    gap = ((datetime.fromisoformat(duplicate["captured_at"])
            - datetime.fromisoformat(canonical["captured_at"])).total_seconds() * 1000)
    return PlannedRetraction(
        entry_id=entry_id,
        case_id=canonical["case_id"],
        canonical_row_id=canonical["id"],
        duplicate_row_id=duplicate["id"],
        canonical_at=canonical["captured_at"],
        duplicate_at=duplicate["captured_at"],
        gap_milliseconds=round(gap, 3),
        content_hash=canonical["content_hash"],
        verification={**checks, "captured_at_gap_milliseconds": round(gap, 3)},
        already_applied=already,
    )


def _validate(request: DuplicateCorrectionRequest) -> None:
    """Shape checks that need no database, shared by planning and applying --
    so a request that could never be planned cannot be applied either."""
    if not request.pairs:
        raise _refuse("no pairs given")
    seen: set[str] = set()
    for pair in request.pairs:
        if pair.duplicate_row_id in seen:
            raise _refuse(f"{pair.duplicate_row_id!r} appears twice in one correction")
        seen.add(pair.duplicate_row_id)


def plan_correction(engine: Engine, request: DuplicateCorrectionRequest) -> CorrectionPlan:
    """Re-derive every correction from the database. Writes nothing."""
    _validate(request)
    with engine.connect() as connection:
        planned = tuple(_plan_pair(connection, request, pair) for pair in request.pairs)
    return CorrectionPlan(correction_id=request.correction_id, retractions=planned)


def apply_correction(engine: Engine, request: DuplicateCorrectionRequest) -> CorrectionPlan:
    """Apply what `plan_correction` proves, in one transaction.

    The plan is re-derived inside the transaction rather than trusted from a
    previous call, and each update is guarded on the exact state it planned
    against -- so a row that changed in between is not corrected on the
    strength of a stale reading.
    """
    _validate(request)
    ensure_schema(engine)
    applied_at = datetime.now(timezone.utc).isoformat()
    with engine.begin() as connection:
        planned = tuple(_plan_pair(connection, request, pair) for pair in request.pairs)
        for retraction in planned:
            if retraction.already_applied:
                continue
            result = connection.execute(
                update(investment_case_snapshot_table)
                .where(investment_case_snapshot_table.c.id == retraction.duplicate_row_id,
                       investment_case_snapshot_table.c.retracted_by.is_(None))
                .values(retracted_by=retraction.entry_id)
            )
            if result.rowcount != 1:
                raise _refuse(
                    f"{retraction.duplicate_row_id!r} changed while the correction was being applied")
            connection.execute(
                insert(snapshot_correction_table).values(
                    id=retraction.entry_id,
                    correction_id=request.correction_id,
                    kind=request.kind,
                    action=RETRACT,
                    target_table=_SNAPSHOTS,
                    target_row_id=retraction.duplicate_row_id,
                    canonical_row_id=retraction.canonical_row_id,
                    case_id=retraction.case_id,
                    reason=request.reason,
                    verification_json=json.dumps(retraction.verification, sort_keys=True),
                    before_json=json.dumps({"retracted_by": None}),
                    after_json=json.dumps({"retracted_by": retraction.entry_id}),
                    applied_at=applied_at,
                )
            )
    return CorrectionPlan(correction_id=request.correction_id, retractions=planned)
