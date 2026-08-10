"""SQLAlchemy-backed store for `AnalyticalSnapshot`s (Investment Case
Monitoring & Change Intelligence v1).

`get_latest` is the one read a caller needs: "what did Atlas believe
this Case's structured state was, most recently" -- ordered by
`captured_at` descending, `LIMIT 1`. `add` is the only write, and is
**idempotent by content**: it re-checks the current head's own
`content_hash` before inserting, so a caller may call it unconditionally
after every `build()`/`build_many()` assembly (the exact "existing
refresh pathway" the sprint's own instruction names) without ever
risking a duplicate row for analytically-unchanged state -- see this
package's own `__init__.py` for the full rationale.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from sqlalchemy import desc, insert, select
from sqlalchemy.engine import Engine

from atlas.analysis_engine.investment_case_change import AnalyticalSnapshot
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

    def add(self, case_id: str, snapshot: AnalyticalSnapshot) -> bool:
        """Returns `True` when a new row was actually written, `False`
        when the current head already carries an identical
        `content_hash` (analytically unchanged -- "recomputed, not
        changed"; nothing is written). Never raises on the no-op path;
        a caller does not need to check first."""
        current_head = self.get_latest(case_id)
        if current_head is not None and current_head.content_hash == snapshot.content_hash:
            return False
        with self._engine.begin() as connection:
            connection.execute(insert(investment_case_snapshot_table).values(**_to_row(case_id, snapshot)))
        return True


def _to_row(case_id: str, snapshot: AnalyticalSnapshot) -> dict[str, Any]:
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
            },
            sort_keys=True,
        ),
    }


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
        content_hash=row["content_hash"],
        captured_at=datetime.fromisoformat(row["captured_at"]),
    )
