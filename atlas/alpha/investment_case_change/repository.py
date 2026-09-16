"""SQLAlchemy-backed store for `AnalyticalSnapshot`s (Investment Case
Monitoring & Change Intelligence v1) and, since History v1, each
snapshot row's own persisted `ChangeIntelligence` transition.

`get_latest` is the one read a caller needs for building the *current*
Investment Case: "what did Atlas believe this Case's structured state
was, most recently" -- ordered by `captured_at` descending, `LIMIT 1`.
`get_history` (History v1) is the second read: every row for a Case,
oldest first, each paired with the `ChangeIntelligence` that produced
it -- reconstructed from persisted columns, never recomputed (see this
module's own `_to_change_intelligence`).

`add` is the only write and is **idempotent by content**: it re-checks
the current head's own `content_hash` before inserting, so a caller may
call it unconditionally after every `build()`/`build_many()` assembly
(the exact "existing refresh pathway" the Change Intelligence sprint's
own instruction names) without ever risking a duplicate row for
analytically-unchanged state -- see this package's own `__init__.py`
for the full rationale.

**Snapshot Evidence Persistence.** A row also freezes the valuation
evidence its conclusion was made from (`valuation_evidence_snapshot`),
written from the same composition in the same insert, so a stored
decision and the evidence beside it can never come from two moments.
Three consequences follow, and each is deliberate:

* *Frozen as of creation.* A later filing, a price refresh or a new
  methodology never edits a written row -- they produce a new one, and
  the old row keeps saying what Atlas actually had. Reading history
  never consults the live database.
* *Legacy rows have none.* A row written before this contract reads back
  as `None`, which is the honest "never recorded" -- distinct from a
  recorded evidence set whose prior list is genuinely empty. Nothing is
  backfilled.
* *Idempotency now spans evidence too.* `add` still absorbs a repeat of
  analytically-unchanged state, but no longer when the evidence beneath
  it has moved: a restated prior year, a newly available fiscal epoch or
  a changed Valuation Support writes a row even though the conclusion
  stands still, because absorbing it would leave the record asserting
  the evidence never changed. A price tick still writes nothing -- the
  evidence fingerprint excludes the current yield for exactly the reason
  `content_hash` already does.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from sqlalchemy import and_, asc, desc, insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.investment_case.valuation_evidence_snapshot import (
    ValuationEvidenceSnapshot,
    deserialize_valuation_evidence,
    serialize_valuation_evidence,
)
from atlas.analysis_engine.investment_case_change import (
    AnalyticalSnapshot,
    ChangeCategory,
    ChangeDirection,
    ChangeFinding,
    ChangeIntelligence,
    ThesisImpact,
    compare_snapshots,
)
from atlas.alpha.investment_case_change.table import investment_case_snapshot_table

__all__ = ["SqlAlchemyInvestmentCaseSnapshotRepository", "StoredSnapshotRow", "serialize_change_intelligence"]


def _live(case_id: str):
    """A Case's history: every row but those retracted as transient
    migration state (`atlas.alpha.migration_correction`)."""
    table = investment_case_snapshot_table
    return and_(table.c.case_id == case_id, table.c.retracted_by.is_(None))


@dataclass(frozen=True)
class StoredSnapshotRow:
    """One persisted row exactly as stored, retracted or not -- the audit
    view a correction plans against, never a history read."""

    id: str
    snapshot: AnalyticalSnapshot
    change_intelligence_json: str | None
    retracted_by: str | None


class SqlAlchemyInvestmentCaseSnapshotRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def stored_rows(self, case_id: str) -> tuple[StoredSnapshotRow, ...]:
        """Every stored row for `case_id`, retracted ones included, oldest
        first. Read-only."""
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(investment_case_snapshot_table)
                    .where(investment_case_snapshot_table.c.case_id == case_id)
                    .order_by(asc(investment_case_snapshot_table.c.captured_at))
                )
                .mappings()
                .all()
            )
        return tuple(
            StoredSnapshotRow(
                id=row["id"],
                snapshot=_to_snapshot(row),
                change_intelligence_json=row["change_intelligence_json"],
                retracted_by=row["retracted_by"],
            )
            for row in rows
        )

    def get_latest(self, case_id: str) -> AnalyticalSnapshot | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(investment_case_snapshot_table)
                    .where(_live(case_id))
                    .order_by(desc(investment_case_snapshot_table.c.captured_at))
                    .limit(1)
                )
                .mappings()
                .first()
            )
        return _to_snapshot(row) if row is not None else None

    def get_history(self, case_id: str) -> tuple[tuple[AnalyticalSnapshot, ChangeIntelligence], ...]:
        """Every persisted snapshot for `case_id`, oldest first, each
        paired with the `ChangeIntelligence` that describes how it
        differs from the row immediately before it. Read-only: never
        writes, never calls `compare_snapshots` against real state (the
        one exception -- the first row -- uses `compare_snapshots(None,
        snapshot)`, which is the pure, constant baseline constructor,
        not a real comparison; see that function's own docstring)."""
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(investment_case_snapshot_table)
                    .where(_live(case_id))
                    .order_by(asc(investment_case_snapshot_table.c.captured_at))
                )
                .mappings()
                .all()
            )
        return tuple((snapshot, transition) for snapshot, transition, _ in _replay(rows))

    def get_history_with_evidence(
        self, case_id: str
    ) -> tuple[tuple[AnalyticalSnapshot, ChangeIntelligence, ValuationEvidenceSnapshot | None], ...]:
        """`get_history`, with each row's own frozen valuation evidence beside
        it -- read from the very same row, in the same single query, so the
        evidence can neither cost an extra round trip per snapshot nor come
        from a different row than the snapshot it is shown with.

        `None` for a row written before the evidence contract existed. That
        is the honest "never recorded"; it is never today's evidence standing
        in for a snapshot that has none.
        """
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(investment_case_snapshot_table)
                    .where(_live(case_id))
                    .order_by(asc(investment_case_snapshot_table.c.captured_at))
                )
                .mappings()
                .all()
            )
        return _replay(rows)

    def get_latest_valuation_evidence(self, case_id: str) -> ValuationEvidenceSnapshot | None:
        """The frozen valuation evidence of the current head, or `None` when
        the head predates this contract (or no head exists). Reads the stored
        row only -- never the live composition."""
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(investment_case_snapshot_table)
                    .where(_live(case_id))
                    .order_by(desc(investment_case_snapshot_table.c.captured_at))
                    .limit(1)
                )
                .mappings()
                .first()
            )
        if row is None:
            return None
        return deserialize_valuation_evidence(json.loads(row["snapshot_json"]).get("valuation_evidence"))

    def get_valuation_evidence_history(self, case_id: str) -> tuple[tuple[str, ValuationEvidenceSnapshot | None], ...]:
        """Every live row's frozen valuation evidence, oldest first, paired
        with the row's own `captured_at`. `None` for a row written before the
        contract existed -- never today's evidence standing in for it.

        Read-only and purely frozen: the stored JSON is the whole source, so
        the answer to "what did Atlas have then" cannot drift as the live
        database moves on.
        """
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(investment_case_snapshot_table)
                    .where(_live(case_id))
                    .order_by(asc(investment_case_snapshot_table.c.captured_at))
                )
                .mappings()
                .all()
            )
        return tuple(
            (row["captured_at"], deserialize_valuation_evidence(json.loads(row["snapshot_json"]).get("valuation_evidence")))
            for row in rows
        )

    def add(self, case_id: str, snapshot: AnalyticalSnapshot, change_intelligence: ChangeIntelligence,
            *, valuation_evidence: ValuationEvidenceSnapshot | None = None) -> bool:
        """Returns `True` when a new row was actually written, `False`
        when the current head already carries an identical
        `content_hash` (analytically unchanged -- "recomputed, not
        changed"; nothing is written). Never raises on the no-op path;
        a caller does not need to check first.

        `change_intelligence` must be the exact result of comparing this
        `snapshot` against the current head (the caller already computes
        this for its own, current-Case purposes -- see
        `InvestmentCaseCompositionService._assemble`'s own comment) --
        never recomputed here, and never persisted when `is_baseline` is
        `True` (a baseline has nothing to persist; `get_history` derives
        it structurally, from "this is the oldest row for this Case")."""
        current_head = self.get_latest(case_id)
        if current_head is not None and current_head.content_hash == snapshot.content_hash:
            # (Snapshot Evidence Persistence) Analytically unchanged is no
            # longer the whole question. The conclusion can stand still while
            # the evidence under it moves -- a restated prior year, a newly
            # available fiscal epoch, a denominator that became exact, a
            # Valuation Support that resolved. Absorbing those would leave the
            # record saying the evidence never changed, which is false. The
            # fingerprint deliberately ignores the current yield, exactly as
            # `content_hash` does, so a price tick still writes nothing.
            head_evidence = self.get_latest_valuation_evidence(case_id)
            unchanged = (head_evidence.fingerprint if head_evidence is not None else None)
            incoming = (valuation_evidence.fingerprint if valuation_evidence is not None else None)
            if unchanged == incoming:
                return False
        with self._engine.begin() as connection:
            connection.execute(
                insert(investment_case_snapshot_table).values(
                    **_to_row(case_id, snapshot, change_intelligence, valuation_evidence)
                )
            )
        return True


def _replay(rows) -> tuple[tuple[AnalyticalSnapshot, ChangeIntelligence, ValuationEvidenceSnapshot | None], ...]:
    """One Case's stored rows, oldest first, each turned into the snapshot it
    holds, the transition it recorded, and the evidence it froze. Purely a
    projection of the rows handed in: no query, no recomputation against live
    state (the first row's baseline is the constant baseline constructor, not
    a comparison), and no row is added, dropped or reordered."""
    results = []
    previous_captured_at = None
    for row in rows:
        snapshot = _to_snapshot(row)
        if previous_captured_at is None:
            transition = compare_snapshots(None, snapshot)
        else:
            transition = _to_change_intelligence(
                row, previous_captured_at=previous_captured_at, current_captured_at=snapshot.captured_at
            )
        evidence = deserialize_valuation_evidence(json.loads(row["snapshot_json"]).get("valuation_evidence"))
        results.append((snapshot, transition, evidence))
        previous_captured_at = snapshot.captured_at
    return tuple(results)


def _to_row(case_id: str, snapshot: AnalyticalSnapshot, change_intelligence: ChangeIntelligence,
            valuation_evidence: "ValuationEvidenceSnapshot | None" = None) -> dict[str, Any]:
    captured_at = snapshot.captured_at.isoformat()
    return {
        "id": f"{case_id}:{captured_at}",
        "case_id": case_id,
        "captured_at": captured_at,
        "content_hash": snapshot.content_hash,
        "current_yield": None if snapshot.current_yield is None else repr(snapshot.current_yield),
        "snapshot_json": json.dumps(
            {
                "business_category_states": list(snapshot.business_category_states),
                "risk_category_states": list(snapshot.risk_category_states),
                "valuation_status": snapshot.valuation_status,
                "valuation_finding_id": snapshot.valuation_finding_id,
                "strength_kinds": list(snapshot.strength_kinds),
                "risk_highlight_kinds": list(snapshot.risk_highlight_kinds),
                "open_question_origins": list(snapshot.open_question_origins),
                "atlas_thesis_narrative": snapshot.atlas_thesis_narrative,
                "atlas_thesis_posture": snapshot.atlas_thesis_posture,
                "financial_risk_methodology": snapshot.financial_risk_methodology,
                "valuation_methodology": snapshot.valuation_methodology,
                # Absent, not null, on a row written before this contract --
                # `_to_snapshot`'s `.get` keeps that distinction honest.
                **({} if valuation_evidence is None
                   else {"valuation_evidence": serialize_valuation_evidence(valuation_evidence)}),
            },
            sort_keys=True,
        ),
        "change_intelligence_json": serialize_change_intelligence(change_intelligence),
    }


def serialize_change_intelligence(change_intelligence: ChangeIntelligence) -> str | None:
    """The exact `change_intelligence_json` `add` persists for a transition:
    `None` for a baseline, which has nothing to persist."""
    if change_intelligence.is_baseline:
        return None
    return json.dumps(_change_intelligence_payload(change_intelligence), sort_keys=True)


def _change_intelligence_payload(change_intelligence: ChangeIntelligence) -> dict[str, Any]:
    return {
        "thesis_impact": change_intelligence.thesis_impact.value,
        "summary_narrative": change_intelligence.summary_narrative,
        "changes": [_change_finding_to_dict(c) for c in change_intelligence.changes],
    }


def _change_finding_to_dict(change: ChangeFinding) -> dict[str, Any]:
    return {
        "id": change.id,
        "category": change.category.value,
        "direction": change.direction.value,
        "previous_state": change.previous_state,
        "current_state": change.current_state,
        "details": dict(change.details),
        "evidence_references": list(change.evidence_references),
        "source_finding_id": change.source_finding_id,
    }


def _change_finding_from_dict(payload: Mapping[str, Any]) -> ChangeFinding:
    return ChangeFinding(
        id=payload["id"],
        category=ChangeCategory(payload["category"]),
        direction=ChangeDirection(payload["direction"]),
        previous_state=payload["previous_state"],
        current_state=payload["current_state"],
        details=dict(payload["details"]),
        evidence_references=tuple(payload["evidence_references"]),
        source_finding_id=payload["source_finding_id"],
    )


def _to_change_intelligence(
    row: Mapping[str, Any], *, previous_captured_at, current_captured_at
) -> ChangeIntelligence:
    """Reconstructs a non-baseline row's own transition from its
    persisted `change_intelligence_json` -- never recomputed via
    `compare_snapshots` against real prior/current state (History v1's
    own "persisted, not recomputed" decision; see this module's own
    top-level docstring). `None`/missing `change_intelligence_json`
    means this row predates the column (backward compatibility): its
    transition was genuinely never recorded, reported honestly rather
    than fabricated by comparing snapshots after the fact."""
    raw = row["change_intelligence_json"]
    if not raw:
        return ChangeIntelligence(
            is_baseline=False,
            changes=(),
            thesis_impact=ThesisImpact.UNCHANGED,
            summary_narrative="Historical change detail is not available for this entry.",
            previous_captured_at=previous_captured_at,
            current_captured_at=current_captured_at,
        )
    payload = json.loads(raw)
    return ChangeIntelligence(
        is_baseline=False,
        changes=tuple(_change_finding_from_dict(c) for c in payload["changes"]),
        thesis_impact=ThesisImpact(payload["thesis_impact"]),
        summary_narrative=payload["summary_narrative"],
        previous_captured_at=previous_captured_at,
        current_captured_at=current_captured_at,
    )


def _to_snapshot(row: Mapping[str, Any]) -> AnalyticalSnapshot:
    from datetime import datetime

    payload = json.loads(row["snapshot_json"])
    current_yield_raw = row["current_yield"]
    return AnalyticalSnapshot(
        business_category_states=tuple(tuple(entry) for entry in payload["business_category_states"]),
        risk_category_states=tuple(tuple(entry) for entry in payload["risk_category_states"]),
        valuation_status=payload["valuation_status"],
        valuation_finding_id=payload["valuation_finding_id"],
        current_yield=None if current_yield_raw is None else float(current_yield_raw),
        strength_kinds=tuple(payload["strength_kinds"]),
        risk_highlight_kinds=tuple(payload["risk_highlight_kinds"]),
        open_question_origins=tuple(payload["open_question_origins"]),
        # Backward compatibility: rows persisted before History v1 added
        # these two fields have no such keys in their own `snapshot_json`
        # -- `None` is the honest "this historical thesis text was never
        # recorded", never a fabricated placeholder.
        atlas_thesis_narrative=payload.get("atlas_thesis_narrative"),
        atlas_thesis_posture=payload.get("atlas_thesis_posture"),
        content_hash=row["content_hash"],
        captured_at=datetime.fromisoformat(row["captured_at"]),
        # Absent on rows written before the method was recorded: `None`,
        # which never equals a current method, so Financial Risk is
        # re-baselined rather than compared across methods.
        financial_risk_methodology=payload.get("financial_risk_methodology"),
        valuation_methodology=payload.get("valuation_methodology"),
    )
