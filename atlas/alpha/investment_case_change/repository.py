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
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from sqlalchemy import asc, desc, insert, select
from sqlalchemy.engine import Engine

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

__all__ = ["SqlAlchemyInvestmentCaseSnapshotRepository"]


class SqlAlchemyInvestmentCaseSnapshotRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_latest(self, case_id: str) -> AnalyticalSnapshot | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(investment_case_snapshot_table)
                    .where(investment_case_snapshot_table.c.case_id == case_id)
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
                    .where(investment_case_snapshot_table.c.case_id == case_id)
                    .order_by(asc(investment_case_snapshot_table.c.captured_at))
                )
                .mappings()
                .all()
            )
        results: list[tuple[AnalyticalSnapshot, ChangeIntelligence]] = []
        previous_captured_at = None
        for row in rows:
            snapshot = _to_snapshot(row)
            if previous_captured_at is None:
                change_intelligence = compare_snapshots(None, snapshot)
            else:
                change_intelligence = _to_change_intelligence(
                    row, previous_captured_at=previous_captured_at, current_captured_at=snapshot.captured_at
                )
            results.append((snapshot, change_intelligence))
            previous_captured_at = snapshot.captured_at
        return tuple(results)

    def add(self, case_id: str, snapshot: AnalyticalSnapshot, change_intelligence: ChangeIntelligence) -> bool:
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
            return False
        with self._engine.begin() as connection:
            connection.execute(
                insert(investment_case_snapshot_table).values(**_to_row(case_id, snapshot, change_intelligence))
            )
        return True


def _to_row(case_id: str, snapshot: AnalyticalSnapshot, change_intelligence: ChangeIntelligence) -> dict[str, Any]:
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
            },
            sort_keys=True,
        ),
        "change_intelligence_json": (
            None if change_intelligence.is_baseline else json.dumps(_change_intelligence_payload(change_intelligence), sort_keys=True)
        ),
    }


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
    )
