"""Plan and apply one migration-artifact correction.

See this package's `__init__.py` for what is corrected and why. Every
guard below is re-derived from the database; any failure raises
`CorrectionRefused` and nothing is written. `apply_correction` re-plans
inside itself and writes the ledger entries and the corrected rows in one
transaction, each update guarded on the exact state it planned against.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping

from sqlalchemy import MetaData, Table, insert, select, update
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.engine import Engine

from atlas.alpha.daily_brief_change_log.store import DailyBriefChangeLogStore
from atlas.alpha.daily_brief_change_log.table import create_daily_brief_change_log_table, daily_brief_change_log_table
from atlas.alpha.decision_memory.engine import detect_decision_change
from atlas.alpha.decision_memory.repository import (
    SqlAlchemyDecisionMemoryRepository,
    StoredDecisionRow,
    serialize_decision_change,
)
from atlas.alpha.decision_memory.table import create_decision_memory_snapshot_table, decision_memory_snapshot_table
from atlas.alpha.investment_case_change.repository import (
    SqlAlchemyInvestmentCaseSnapshotRepository,
    StoredSnapshotRow,
    serialize_change_intelligence,
)
from atlas.alpha.investment_case_change.table import create_investment_case_snapshot_table, investment_case_snapshot_table
from atlas.alpha.migration_correction.table import (
    create_migration_artifact_correction_table,
    migration_artifact_correction_table,
)
from atlas.analysis_engine.investment_case_change import compare_snapshots
from atlas.analysis_engine.methodology import ANALYSIS_METHODOLOGY, METHODOLOGY_KEY, comparable_payload
from atlas.analysis_engine.risk.financial_risk import FINANCIAL_RISK_METHODOLOGY
from atlas.analysis_engine.valuation.cash_flow import VALUATION_METHODOLOGY

__all__ = [
    "RETRACT",
    "RECOMPUTE_TRANSITION",
    "CorrectionRefused",
    "CorrectionRequest",
    "PlannedWrite",
    "CorrectionPlan",
    "ensure_correction_schema",
    "correction_schema_present",
    "plan_correction",
    "apply_correction",
]

RETRACT = "retract"
RECOMPUTE_TRANSITION = "recompute_transition"

#: A migration window longer than this is not one migration run.
MAX_WINDOW = timedelta(hours=24)

_SNAPSHOTS = investment_case_snapshot_table.name
_MEMORY = decision_memory_snapshot_table.name
_CHANGE_LOG = daily_brief_change_log_table.name
_TABLES: dict[str, Table] = {
    _SNAPSHOTS: investment_case_snapshot_table,
    _MEMORY: decision_memory_snapshot_table,
    _CHANGE_LOG: daily_brief_change_log_table,
}
_TRANSITION_COLUMN = {_SNAPSHOTS: "change_intelligence_json", _MEMORY: "change_json"}

#: Change-log reason codes whose transition Decision Memory also records,
#: and the snapshot field it records it under. Only these can be matched
#: to a retracted Decision Memory row, so only these can be retracted.
_CHANGE_LOG_TRANSITION_FIELDS = {
    "investment_decision_transition": "action",
    "recommendation_conviction_transition": "convictionStrength",
}

#: Evidence keyed by Case: nothing may be recorded for the Case inside the
#: window. (table, case column, timestamp column)
_CASE_EVIDENCE = (
    ("evidence_snapshots", "case_id", "captured_at"),
    ("ingestion_results", "case_id", "ran_at"),
    ("monitoring_results", "case_id", "generated_at"),
)
#: Evidence not keyed by Case and without a retrieval time, checked across
#: every issuer: nothing may be recorded inside the window. (table,
#: recorded column)
_UNRETRIEVED_EVIDENCE = (
    ("business_records", "version_created_at"),
    ("security_share_filings", "processed_at"),
    ("security_share_observations", "recorded_at"),
)
#: Every other table that records when its evidence was retrieved is found
#: by that shape, never by name: anything it recorded inside the window
#: must have been retrieved before it -- a migration deriving from what
#: Atlas already held, never a new fact.
_RECORDED, _RETRIEVED = "recorded_at", "retrieved_at"


class CorrectionRefused(RuntimeError):
    """A guard failed. Nothing was written."""


@dataclass(frozen=True)
class CorrectionRequest:
    """Explicit row ids of one explicit Case -- never a ticker."""

    case_id: str
    reason: str
    window_start: datetime
    window_end: datetime
    retract_snapshot_ids: tuple[str, ...] = ()
    recompute_snapshot_ids: tuple[str, ...] = ()
    retract_memory_ids: tuple[str, ...] = ()
    recompute_memory_ids: tuple[str, ...] = ()
    retract_change_log_ids: tuple[str, ...] = ()

    @property
    def correction_id(self) -> str:
        canonical = json.dumps(
            {
                "case_id": self.case_id,
                "reason": self.reason,
                "window": [self.window_start.isoformat(), self.window_end.isoformat()],
                "retract_snapshot_ids": sorted(self.retract_snapshot_ids),
                "recompute_snapshot_ids": sorted(self.recompute_snapshot_ids),
                "retract_memory_ids": sorted(self.retract_memory_ids),
                "recompute_memory_ids": sorted(self.recompute_memory_ids),
                "retract_change_log_ids": sorted(self.retract_change_log_ids),
            },
            sort_keys=True,
        )
        return "mac-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class PlannedWrite:
    entry_id: str
    action: str
    target_table: str
    target_row_id: str
    predecessor_row_id: str | None
    before: Mapping[str, Any]
    after: Mapping[str, Any]
    already_applied: bool


@dataclass(frozen=True)
class CorrectionPlan:
    request: CorrectionRequest
    correction_id: str
    methodology: str
    writes: tuple[PlannedWrite, ...]
    verification: Mapping[str, Any]

    @property
    def pending(self) -> tuple[PlannedWrite, ...]:
        return tuple(w for w in self.writes if not w.already_applied)


def correction_schema_present(engine: Engine) -> bool:
    """Whether the ledger and every `retracted_by` column already exist --
    a dry run plans only against a schema it does not have to change."""
    inspector = sa_inspect(engine)
    names = set(inspector.get_table_names())
    if migration_artifact_correction_table.name not in names:
        return False
    return all(
        name in names and "retracted_by" in {c["name"] for c in inspector.get_columns(name)} for name in _TABLES
    )


def ensure_correction_schema(engine: Engine) -> None:
    create_investment_case_snapshot_table(engine)
    create_decision_memory_snapshot_table(engine)
    create_daily_brief_change_log_table(engine)
    create_migration_artifact_correction_table(engine)


def _parse(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


def _refuse(message: str) -> CorrectionRefused:
    return CorrectionRefused(message)


# -- one history table, seen generically --------------------------------------------------------------


@dataclass(frozen=True)
class _Row:
    id: str
    at: datetime
    retracted_by: str | None
    content_hash: str
    transition: str | None
    methodology: Any
    stored: Any


@dataclass(frozen=True)
class _History:
    table: str
    rows: tuple[_Row, ...]
    current_methodology: Any
    #: The transition production would persist for `current` written on top
    #: of head `previous`, or `None` when production would write no row.
    clean_transition: Callable[[_Row, _Row], tuple[bool, str | None]]


def _snapshot_history(rows: tuple[StoredSnapshotRow, ...]) -> _History:
    def clean(previous: _Row, current: _Row) -> tuple[bool, str | None]:
        # `SqlAlchemyInvestmentCaseSnapshotRepository.add`: an identical
        # head absorbs the snapshot; otherwise `compare_snapshots` against it.
        if previous.content_hash == current.content_hash:
            return False, None
        return True, serialize_change_intelligence(compare_snapshots(previous.stored.snapshot, current.stored.snapshot))

    return _History(
        table=_SNAPSHOTS,
        rows=tuple(
            _Row(
                id=r.id,
                at=r.snapshot.captured_at,
                retracted_by=r.retracted_by,
                content_hash=r.snapshot.content_hash,
                transition=r.change_intelligence_json,
                methodology=(r.snapshot.financial_risk_methodology, r.snapshot.valuation_methodology),
                stored=r,
            )
            for r in rows
        ),
        current_methodology=(FINANCIAL_RISK_METHODOLOGY, VALUATION_METHODOLOGY),
        clean_transition=clean,
    )


def _memory_history(rows: tuple[StoredDecisionRow, ...]) -> _History:
    def clean(previous: _Row, current: _Row) -> tuple[bool, str | None]:
        # `DecisionMemoryService._record_current_snapshot` + `add`: only a
        # head under today's methodology is a baseline to diff against or
        # to absorb an identical snapshot.
        comparable = comparable_payload(previous.stored.snapshot_json) is not None
        if comparable and previous.content_hash == current.content_hash:
            return False, None
        change = detect_decision_change(
            previous.stored.snapshot if comparable else None,
            current.stored.snapshot,
            detected_at=current.stored.snapshot.recorded_at,
        )
        return True, serialize_decision_change(change)

    return _History(
        table=_MEMORY,
        rows=tuple(
            _Row(
                id=r.id,
                at=r.snapshot.recorded_at,
                retracted_by=r.retracted_by,
                content_hash=r.snapshot.content_hash,
                transition=r.change_json,
                methodology=json.loads(r.snapshot_json).get(METHODOLOGY_KEY),
                stored=r,
            )
            for r in rows
        ),
        current_methodology=ANALYSIS_METHODOLOGY,
        clean_transition=clean,
    )


def _entry_id(correction_id: str, table: str, row_id: str) -> str:
    return f"{correction_id}/{table}/{row_id}"


def _stored_row(engine: Engine, table: str, row_id: str) -> dict[str, Any]:
    t = _TABLES[table]
    with engine.connect() as connection:
        row = connection.execute(select(t).where(t.c.id == row_id)).mappings().first()
    return dict(row)


def _ledger(engine: Engine, correction_id: str) -> dict[str, Mapping[str, Any]]:
    t = migration_artifact_correction_table
    with engine.connect() as connection:
        rows = connection.execute(select(t).where(t.c.correction_id == correction_id)).mappings().all()
    return {row["id"]: row for row in rows}


def _plan_history(
    engine: Engine,
    history: _History,
    request: CorrectionRequest,
    retract_ids: tuple[str, ...],
    recompute_ids: tuple[str, ...],
    ledger: Mapping[str, Mapping[str, Any]],
) -> tuple[list[PlannedWrite], list[tuple[_Row, _Row, _Row]], dict[str, Any]]:
    """The writes for one history table, the (retracted, successor,
    surviving predecessor) triples they restore, and what was verified."""
    table, correction_id = history.table, request.correction_id
    by_id = {r.id: r for r in history.rows}
    for row_id in retract_ids + recompute_ids:
        if row_id not in by_id:
            raise _refuse(f"{table}: {row_id!r} is not a stored row of Case {request.case_id!r}")
    own_prefix = f"{correction_id}/"
    foreign = {r.id for r in history.rows if r.retracted_by is not None and not r.retracted_by.startswith(own_prefix)}
    for row_id in retract_ids + recompute_ids:
        if row_id in foreign:
            raise _refuse(f"{table}: {row_id!r} was already retracted by {by_id[row_id].retracted_by!r}")
    for row_id in retract_ids + recompute_ids:
        at = by_id[row_id].at
        if not request.window_start <= at <= request.window_end:
            raise _refuse(f"{table}: {row_id!r} at {at.isoformat()} is outside the migration window")

    order = [r for r in history.rows if r.id not in foreign]
    retract, recompute = set(retract_ids), set(recompute_ids)
    if order and order[-1].id in retract:
        raise _refuse(f"{table}: {order[-1].id!r} is the Case's current state; a correction never retracts it")

    triples: list[tuple[_Row, _Row, _Row]] = []
    successor_of: dict[str, _Row] = {}
    for index, row in enumerate(order):
        if row.id not in retract:
            continue
        successor = next((o for o in order[index + 1:] if o.id not in retract), None)
        if successor is None or successor.id not in recompute:
            raise _refuse(
                f"{table}: retracting {row.id!r} leaves its successor's transition diffed against it; "
                "that successor must be recomputed in the same correction"
            )
        successor_of[row.id] = successor

    survivors = [r for r in order if r.id not in retract]
    writes: list[PlannedWrite] = []
    recomputed: dict[str, Any] = {}
    for row_id in recompute_ids:
        current = by_id[row_id]
        position = survivors.index(current)
        if position == 0:
            raise _refuse(f"{table}: {row_id!r} has no surviving predecessor; no methodology boundary to restore")
        predecessor = survivors[position - 1]
        between = [o for o in order if predecessor.at < o.at < current.at]
        if not between:
            raise _refuse(f"{table}: nothing is retracted before {row_id!r}; its transition is already genuine")
        if predecessor.at >= request.window_start:
            raise _refuse(f"{table}: surviving predecessor {predecessor.id!r} is inside the window, not pre-migration state")
        for row in between + [current]:
            if row.methodology != history.current_methodology:
                raise _refuse(
                    f"{table}: {row.id!r} was written under {row.methodology!r}, not the methodology this code runs "
                    f"({history.current_methodology!r})"
                )
        if predecessor.methodology == history.current_methodology:
            raise _refuse(
                f"{table}: surviving predecessor {predecessor.id!r} shares the current methodology; "
                "this is no methodology migration"
            )
        would_write, clean = history.clean_transition(predecessor, current)
        if not would_write:
            raise _refuse(f"{table}: production would have written no row {row_id!r} on top of {predecessor.id!r}")
        column = _TRANSITION_COLUMN[table]
        entry_id = _entry_id(correction_id, table, row_id)
        if entry_id in ledger:
            if current.transition != clean:
                raise _refuse(f"{table}: {row_id!r} was corrected by {entry_id!r} but no longer holds that correction")
            before = json.loads(ledger[entry_id]["before_json"])
            already = True
        else:
            if current.transition == clean:
                raise _refuse(f"{table}: {row_id!r} already holds its clean transition; not a migration artifact")
            before = _stored_row(engine, table, row_id)
            already = False
        writes.append(
            PlannedWrite(
                entry_id=entry_id,
                action=RECOMPUTE_TRANSITION,
                target_table=table,
                target_row_id=row_id,
                predecessor_row_id=predecessor.id,
                before=before,
                after={column: clean},
                already_applied=already,
            )
        )
        recomputed[row_id] = {"predecessor": predecessor.id, "retracted_between": [o.id for o in between], column: clean}
        for row in between:
            triples.append((row, current, predecessor))

    for row_id in retract_ids:
        row = by_id[row_id]
        entry_id = _entry_id(correction_id, table, row_id)
        if row.retracted_by == entry_id:
            if entry_id not in ledger:
                raise _refuse(f"{table}: {row_id!r} names {entry_id!r}, which the ledger does not hold")
            before, already = json.loads(ledger[entry_id]["before_json"]), True
        else:
            before, already = _stored_row(engine, table, row_id), False
        writes.append(
            PlannedWrite(
                entry_id=entry_id,
                action=RETRACT,
                target_table=table,
                target_row_id=row_id,
                predecessor_row_id=None,
                before=before,
                after={"retracted_by": entry_id},
                already_applied=already,
            )
        )
    return writes, triples, {"retracted": list(retract_ids), "recomputed": recomputed}


def _plan_change_log(
    engine: Engine,
    request: CorrectionRequest,
    memory_triples: list[tuple[_Row, _Row, _Row]],
    ledger: Mapping[str, Mapping[str, Any]],
) -> tuple[list[PlannedWrite], dict[str, Any]]:
    store = DailyBriefChangeLogStore(engine)
    writes: list[PlannedWrite] = []
    verified: dict[str, Any] = {}
    for entry_row_id in request.retract_change_log_ids:
        row = store.stored_row(entry_row_id)
        if row is None:
            raise _refuse(f"{_CHANGE_LOG}: {entry_row_id!r} is not a stored row")
        if row["case_id"] != request.case_id:
            raise _refuse(f"{_CHANGE_LOG}: {entry_row_id!r} belongs to Case {row['case_id']!r}")
        detected_at = _parse(row["detected_at"])
        if not request.window_start <= detected_at <= request.window_end:
            raise _refuse(f"{_CHANGE_LOG}: {entry_row_id!r} at {row['detected_at']} is outside the migration window")
        field = _CHANGE_LOG_TRANSITION_FIELDS.get(row["reason_code"])
        if field is None:
            raise _refuse(f"{_CHANGE_LOG}: {row['reason_code']!r} is not a transition Decision Memory records")

        def value(r: _Row) -> Any:
            return json.loads(r.stored.snapshot_json).get(field)

        narrated = [
            (retracted, successor, predecessor)
            for retracted, successor, predecessor in memory_triples
            if value(retracted) == row["secondary_value"] and value(successor) == row["value"]
        ]
        if not narrated:
            raise _refuse(
                f"{_CHANGE_LOG}: {entry_row_id!r} ({row['secondary_value']} -> {row['value']}) narrates no retracted "
                "Decision Memory transition of this correction"
            )
        for _, _, predecessor in narrated:
            comparable = comparable_payload(predecessor.stored.snapshot_json) is not None
            if comparable and value(predecessor) == row["secondary_value"]:
                raise _refuse(f"{_CHANGE_LOG}: the clean history reproduces {entry_row_id!r}; it is genuine")
        entry_id = _entry_id(request.correction_id, _CHANGE_LOG, entry_row_id)
        if row["retracted_by"] == entry_id:
            if entry_id not in ledger:
                raise _refuse(f"{_CHANGE_LOG}: {entry_row_id!r} names {entry_id!r}, which the ledger does not hold")
            before, already = json.loads(ledger[entry_id]["before_json"]), True
        elif row["retracted_by"] is not None:
            raise _refuse(f"{_CHANGE_LOG}: {entry_row_id!r} was already retracted by {row['retracted_by']!r}")
        else:
            before, already = dict(row), False
        writes.append(
            PlannedWrite(
                entry_id=entry_id,
                action=RETRACT,
                target_table=_CHANGE_LOG,
                target_row_id=entry_row_id,
                predecessor_row_id=None,
                before=before,
                after={"retracted_by": entry_id},
                already_applied=already,
            )
        )
        verified[entry_row_id] = {
            "reason_code": row["reason_code"],
            "narrates": [[r.id, s.id] for r, s, _ in narrated],
        }
    return writes, verified


def _check_evidence(engine: Engine, request: CorrectionRequest) -> dict[str, Any]:
    """Market data lives in `business_records`; a snapshot's own
    `current_yield` is a valuation output the migration evidence may
    legitimately move, so it is no evidence check."""
    report: dict[str, Any] = {}
    inspector = sa_inspect(engine)
    existing = set(inspector.get_table_names())
    metadata = MetaData()
    # Timestamps are ISO-8601 text: a date prefix before the window bounds the scan.
    floor = (request.window_start - timedelta(days=1)).date().isoformat()

    def in_window(values) -> list:
        return [v for v in values if v[0] is not None and request.window_start <= _parse(v[0]) <= request.window_end]

    for name, case_column, at_column in _CASE_EVIDENCE:
        if name not in existing:
            report[name] = "absent"
            continue
        t = Table(name, metadata, autoload_with=engine)
        with engine.connect() as connection:
            values = connection.execute(
                select(t.c[at_column]).where(t.c[case_column] == request.case_id, t.c[at_column] >= floor)
            ).all()
        recorded = in_window(values)
        if recorded:
            raise _refuse(f"{name}: {len(recorded)} rows recorded for the Case inside the window: new evidence")
        report[name] = 0
    retrieved = sorted(
        (name, _RECORDED, _RETRIEVED)
        for name in existing
        if {_RECORDED, _RETRIEVED} <= {c["name"] for c in inspector.get_columns(name)}
    )
    for name, at_column, retrieved_column in [(n, c, None) for n, c in _UNRETRIEVED_EVIDENCE] + retrieved:
        if name not in existing:
            report[name] = "absent"
            continue
        t = Table(name, metadata, autoload_with=engine)
        columns = [t.c[at_column]] + ([t.c[retrieved_column]] if retrieved_column else [])
        with engine.connect() as connection:
            values = connection.execute(select(*columns).where(t.c[at_column] >= floor)).all()
        recorded = in_window(values)
        if recorded and retrieved_column is None:
            raise _refuse(f"{name}: {len(recorded)} rows recorded inside the window: new evidence")
        late = [v for v in recorded if v[1] is None or _parse(v[1]) >= request.window_start]
        if late:
            raise _refuse(f"{name}: {len(late)} rows inside the window were retrieved inside it: new evidence")
        report[name] = (
            {"recorded_in_window": len(recorded), "latest_retrieved_at": max(v[1] for v in recorded)} if recorded else 0
        )
    return report


def _check_request(request: CorrectionRequest) -> None:
    if not request.case_id.strip():
        raise _refuse("an explicit Case id is required")
    if not request.reason.strip():
        raise _refuse("an explicit correction reason is required")
    for bound in (request.window_start, request.window_end):
        if bound.tzinfo is None:
            raise _refuse("the migration window must be timezone-aware")
    if not request.window_start < request.window_end:
        raise _refuse("the migration window must start before it ends")
    if request.window_end - request.window_start > MAX_WINDOW:
        raise _refuse(f"a migration window is at most {MAX_WINDOW}; this is not one migration run")
    ids = (
        request.retract_snapshot_ids
        + request.recompute_snapshot_ids
        + request.retract_memory_ids
        + request.recompute_memory_ids
        + request.retract_change_log_ids
    )
    if not (request.retract_snapshot_ids or request.retract_memory_ids or request.retract_change_log_ids):
        raise _refuse("a correction retracts at least one row")
    if len(ids) != len(set(ids)):
        raise _refuse("a row id is named more than once")


def plan_correction(engine: Engine, request: CorrectionRequest) -> CorrectionPlan:
    """Verifies every guard and returns the writes the correction needs --
    writing nothing. Requires the correction schema (`ensure_correction_schema`)."""
    _check_request(request)
    if not correction_schema_present(engine):
        raise _refuse("the correction schema is absent; plan against a database that has it")
    ledger = _ledger(engine, request.correction_id)
    snapshots = _snapshot_history(SqlAlchemyInvestmentCaseSnapshotRepository(engine).stored_rows(request.case_id))
    memory = _memory_history(SqlAlchemyDecisionMemoryRepository(engine).stored_rows(request.case_id))

    snapshot_writes, _, snapshot_verified = _plan_history(
        engine, snapshots, request, request.retract_snapshot_ids, request.recompute_snapshot_ids, ledger
    )
    memory_writes, memory_triples, memory_verified = _plan_history(
        engine, memory, request, request.retract_memory_ids, request.recompute_memory_ids, ledger
    )
    change_log_writes, change_log_verified = _plan_change_log(engine, request, memory_triples, ledger)
    evidence = _check_evidence(engine, request)

    writes = tuple(snapshot_writes + memory_writes + change_log_writes)
    unknown = set(ledger) - {w.entry_id for w in writes}
    if unknown:
        raise _refuse(f"the ledger holds entries of this correction no longer planned: {sorted(unknown)}")
    return CorrectionPlan(
        request=request,
        correction_id=request.correction_id,
        methodology=ANALYSIS_METHODOLOGY,
        writes=writes,
        verification={
            "case_id": request.case_id,
            "window": [request.window_start.isoformat(), request.window_end.isoformat()],
            "methodology": {
                "analysis": ANALYSIS_METHODOLOGY,
                "financial_risk": FINANCIAL_RISK_METHODOLOGY,
                "valuation": VALUATION_METHODOLOGY,
            },
            _SNAPSHOTS: snapshot_verified,
            _MEMORY: memory_verified,
            _CHANGE_LOG: change_log_verified,
            "evidence": evidence,
        },
    )


def apply_correction(engine: Engine, plan: CorrectionPlan, *, now: datetime | None = None) -> int:
    """Re-plans, refuses if the database moved since `plan`, then writes
    every pending entry and row in one transaction. Returns the number of
    rows corrected -- 0 when the correction was already applied."""
    fresh = plan_correction(engine, plan.request)
    if fresh.writes != plan.writes:
        raise _refuse("the database changed since this plan was made; plan again")
    pending = fresh.pending
    if not pending:
        return 0
    applied_at = (now or datetime.now(timezone.utc)).isoformat()
    verification = json.dumps(fresh.verification, sort_keys=True, default=str)
    with engine.begin() as connection:
        for write in pending:
            connection.execute(
                insert(migration_artifact_correction_table).values(
                    id=write.entry_id,
                    correction_id=fresh.correction_id,
                    action=write.action,
                    target_table=write.target_table,
                    target_row_id=write.target_row_id,
                    case_id=plan.request.case_id,
                    reason=plan.request.reason,
                    window_start=plan.request.window_start.isoformat(),
                    window_end=plan.request.window_end.isoformat(),
                    methodology=fresh.methodology,
                    predecessor_row_id=write.predecessor_row_id,
                    before_json=json.dumps(write.before, sort_keys=True, default=str),
                    after_json=json.dumps(write.after, sort_keys=True, default=str),
                    verification_json=verification,
                    applied_at=applied_at,
                )
            )
            t = _TABLES[write.target_table]
            guard = [t.c.id == write.target_row_id, t.c.retracted_by.is_(None)]
            if write.action == RETRACT:
                values = {"retracted_by": write.entry_id}
            else:
                column = _TRANSITION_COLUMN[write.target_table]
                held = write.before[column]
                guard.append(t.c[column].is_(None) if held is None else t.c[column] == held)
                values = {column: write.after[column]}
            if connection.execute(update(t).where(*guard).values(**values)).rowcount != 1:
                raise _refuse(f"{write.target_table}: {write.target_row_id!r} moved while correcting; nothing written")
    return len(pending)
