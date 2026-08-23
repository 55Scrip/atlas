"""SQLAlchemy-backed store for `EvidenceSnapshot`s and each row's own
persisted `EvidenceHistory` transition. Mirrors `atlas.alpha
.investment_case_change.repository.SqlAlchemyInvestmentCaseSnapshotRepository`
exactly -- same `get_latest`/`get_history`/`add` shape, same
idempotent-by-content-hash write discipline.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from sqlalchemy import asc, desc, insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.evidence_timeline.models import (
    EvidenceHistory,
    EvidenceSnapshot,
    EvidenceTransition,
    EvidenceTransitionCategory,
    SourceEvidenceEvent,
)
from atlas.alpha.evidence_timeline.table import evidence_snapshot_table
from atlas.analysis_engine.investment_case_change import ChangeDirection

__all__ = ["SqlAlchemyEvidenceSnapshotRepository"]


class SqlAlchemyEvidenceSnapshotRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_latest(self, case_id: str) -> EvidenceSnapshot | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(evidence_snapshot_table)
                    .where(evidence_snapshot_table.c.case_id == case_id)
                    .order_by(desc(evidence_snapshot_table.c.captured_at))
                    .limit(1)
                )
                .mappings()
                .first()
            )
        return _to_snapshot(row) if row is not None else None

    def get_history(self, case_id: str) -> tuple[tuple[EvidenceSnapshot, EvidenceHistory], ...]:
        """Every persisted snapshot for `case_id`, oldest first, each
        paired with the `EvidenceHistory` describing how it differs from
        the row immediately before it -- mirrors `SqlAlchemyInvestmentCase
        SnapshotRepository.get_history`'s own docstring exactly."""
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(evidence_snapshot_table)
                    .where(evidence_snapshot_table.c.case_id == case_id)
                    .order_by(asc(evidence_snapshot_table.c.captured_at))
                )
                .mappings()
                .all()
            )
        results: list[tuple[EvidenceSnapshot, EvidenceHistory]] = []
        previous_captured_at = None
        for row in rows:
            snapshot = _to_snapshot(row)
            if previous_captured_at is None:
                history = EvidenceHistory(
                    is_baseline=True, transitions=(), new_source_evidence=(), previous_captured_at=None, current_captured_at=snapshot.captured_at
                )
            else:
                history = _to_evidence_history(row, previous_captured_at=previous_captured_at, current_captured_at=snapshot.captured_at)
            results.append((snapshot, history))
            previous_captured_at = snapshot.captured_at
        return tuple(results)

    def add(self, case_id: str, snapshot: EvidenceSnapshot, history: EvidenceHistory) -> bool:
        """Returns `True` when a new row was actually written, `False`
        when the current head already carries an identical
        `content_hash`. Never raises on the no-op path. `history` must
        be the exact result of comparing this `snapshot` against the
        current head -- never recomputed here, and never persisted when
        `is_baseline` is `True`."""
        current_head = self.get_latest(case_id)
        if current_head is not None and current_head.content_hash == snapshot.content_hash:
            return False
        with self._engine.begin() as connection:
            connection.execute(insert(evidence_snapshot_table).values(**_to_row(case_id, snapshot, history)))
        return True


def _to_row(case_id: str, snapshot: EvidenceSnapshot, history: EvidenceHistory) -> dict[str, Any]:
    captured_at = snapshot.captured_at.isoformat()
    return {
        "id": f"{case_id}:{captured_at}",
        "case_id": case_id,
        "captured_at": captured_at,
        "content_hash": snapshot.content_hash,
        "snapshot_json": json.dumps(
            {
                "overall_coverage": snapshot.overall_coverage,
                "overall_confidence": snapshot.overall_confidence,
                "stance_level": snapshot.stance_level,
                "evidence_quality": snapshot.evidence_quality,
                "conflict_status": snapshot.conflict_status,
                "freshness": snapshot.freshness,
                "missing_dimensions": list(snapshot.missing_dimensions),
                "known_periods": list(snapshot.known_periods),
            },
            sort_keys=True,
        ),
        "evidence_history_json": None if history.is_baseline else json.dumps(_history_payload(history), sort_keys=True),
    }


def _history_payload(history: EvidenceHistory) -> dict[str, Any]:
    return {
        "transitions": [_transition_to_dict(t) for t in history.transitions],
        "new_source_evidence": [{"fact_kind": e.fact_kind, "period": e.period} for e in history.new_source_evidence],
    }


def _transition_to_dict(transition: EvidenceTransition) -> dict[str, Any]:
    return {
        "id": transition.id,
        "category": transition.category.value,
        "direction": transition.direction.value,
        "previous_state": transition.previous_state,
        "current_state": transition.current_state,
        "details": dict(transition.details),
    }


def _transition_from_dict(payload: Mapping[str, Any]) -> EvidenceTransition:
    return EvidenceTransition(
        id=payload["id"],
        category=EvidenceTransitionCategory(payload["category"]),
        direction=ChangeDirection(payload["direction"]),
        previous_state=payload["previous_state"],
        current_state=payload["current_state"],
        details=dict(payload["details"]),
    )


def _to_evidence_history(row: Mapping[str, Any], *, previous_captured_at, current_captured_at) -> EvidenceHistory:
    """Reconstructs a non-baseline row's own transition from its
    persisted `evidence_history_json` -- never recomputed via
    `compare_evidence_snapshots` against real prior/current state."""
    raw = row["evidence_history_json"]
    if not raw:
        return EvidenceHistory(
            is_baseline=False, transitions=(), new_source_evidence=(), previous_captured_at=previous_captured_at, current_captured_at=current_captured_at
        )
    payload = json.loads(raw)
    return EvidenceHistory(
        is_baseline=False,
        transitions=tuple(_transition_from_dict(t) for t in payload["transitions"]),
        # Backward compatibility: rows persisted before Source Evidence
        # History was added have no such key -- an empty tuple is the
        # honest "not recorded," never a fabricated retroactive guess.
        new_source_evidence=tuple(SourceEvidenceEvent(fact_kind=e["fact_kind"], period=e["period"]) for e in payload.get("new_source_evidence", [])),
        previous_captured_at=previous_captured_at,
        current_captured_at=current_captured_at,
    )


def _to_snapshot(row: Mapping[str, Any]) -> EvidenceSnapshot:
    from datetime import datetime

    payload = json.loads(row["snapshot_json"])
    return EvidenceSnapshot(
        overall_coverage=payload["overall_coverage"],
        overall_confidence=payload["overall_confidence"],
        stance_level=payload["stance_level"],
        evidence_quality=payload["evidence_quality"],
        conflict_status=payload["conflict_status"],
        freshness=payload["freshness"],
        missing_dimensions=tuple(payload["missing_dimensions"]),
        # Backward compatibility: rows persisted before Source Evidence
        # History was added have no such key -- honest "not recorded."
        known_periods=tuple(payload.get("known_periods", [])),
        content_hash=row["content_hash"],
        captured_at=datetime.fromisoformat(row["captured_at"]),
    )
