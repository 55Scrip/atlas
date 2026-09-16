"""Correcting a snapshot duplicated by a race.

The whole risk here is over-reach: hiding a row that was real history. So
most of these tests are about what the correction *refuses* -- a conclusion
that repeats legitimately, an evidence-only change under an unchanged
conclusion, anything separated by another observation. Being milliseconds
apart is what makes the race the likely story; it is never the proof.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, insert, select
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.investment_case_change.table import (
    create_investment_case_snapshot_table,
    investment_case_snapshot_table,
)
from atlas.alpha.snapshot_correction.service import (
    CorrectionRefused,
    DuplicateCorrectionRequest,
    DuplicatePair,
    apply_correction,
    ensure_schema,
    plan_correction,
)
from atlas.alpha.snapshot_correction.table import snapshot_correction_table

_T0 = datetime(2026, 9, 5, 14, 25, 10, 857242, tzinfo=timezone.utc)
CASE = "case-1"


@pytest.fixture
def engine() -> Engine:
    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool,
                           connect_args={"check_same_thread": False})
    create_investment_case_snapshot_table(engine)
    ensure_schema(engine)
    return engine


def _write(engine: Engine, *, at: datetime, content_hash: str = "hash-a",
           payload: dict | None = None, change: str = '{"changes": []}',
           case_id: str = CASE, current_yield: float | None = 0.03) -> str:
    body = {"valuation_status": "fairly_valued", "valuation_evidence": None}
    body.update(payload or {})
    row_id = f"{case_id}:{at.isoformat()}"
    with engine.begin() as connection:
        connection.execute(insert(investment_case_snapshot_table).values(
            id=row_id, case_id=case_id, captured_at=at.isoformat(), content_hash=content_hash,
            current_yield=current_yield, snapshot_json=json.dumps(body, sort_keys=True),
            change_intelligence_json=change, retracted_by=None))
    return row_id


def _request(canonical: str, duplicate: str, correction_id: str = "c-1") -> DuplicateCorrectionRequest:
    return DuplicateCorrectionRequest(
        correction_id=correction_id, reason="concurrency duplicate",
        pairs=(DuplicatePair(canonical_row_id=canonical, duplicate_row_id=duplicate),))


def _row(engine: Engine, row_id: str):
    with engine.connect() as connection:
        return connection.execute(
            select(investment_case_snapshot_table)
            .where(investment_case_snapshot_table.c.id == row_id)).mappings().first()


def _live_count(engine: Engine) -> int:
    with engine.connect() as connection:
        return len(connection.execute(
            select(investment_case_snapshot_table)
            .where(investment_case_snapshot_table.c.retracted_by.is_(None))).mappings().all())


def _ledger(engine: Engine):
    with engine.connect() as connection:
        return connection.execute(select(snapshot_correction_table)).mappings().all()


# --- What is corrected ------------------------------------------------


def test_a_proven_duplicate_is_retracted(engine) -> None:
    canonical = _write(engine, at=_T0)
    duplicate = _write(engine, at=_T0 + timedelta(milliseconds=6.7))
    apply_correction(engine, _request(canonical, duplicate))
    assert _row(engine, duplicate)["retracted_by"] == f"c-1/investment_case_snapshots/{duplicate}"
    assert _live_count(engine) == 1


def test_the_earlier_row_survives(engine) -> None:
    """The record should read as though the observation happened when it
    first happened, not milliseconds later."""
    canonical = _write(engine, at=_T0)
    duplicate = _write(engine, at=_T0 + timedelta(milliseconds=6.7))
    apply_correction(engine, _request(canonical, duplicate))
    assert _row(engine, canonical)["retracted_by"] is None


def test_nothing_is_deleted(engine) -> None:
    canonical = _write(engine, at=_T0)
    duplicate = _write(engine, at=_T0 + timedelta(milliseconds=6.7))
    apply_correction(engine, _request(canonical, duplicate))
    stored = _row(engine, duplicate)
    assert stored is not None
    assert stored["content_hash"] == "hash-a"
    assert json.loads(stored["snapshot_json"])["valuation_status"] == "fairly_valued"


def test_the_ledger_records_what_survived_and_why(engine) -> None:
    canonical = _write(engine, at=_T0)
    duplicate = _write(engine, at=_T0 + timedelta(milliseconds=6.7))
    apply_correction(engine, _request(canonical, duplicate))
    entries = _ledger(engine)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["kind"] == "concurrency_duplicate"
    assert entry["action"] == "retract"
    assert entry["canonical_row_id"] == canonical
    assert entry["target_row_id"] == duplicate
    assert "concurrency duplicate" in entry["reason"]
    verification = json.loads(entry["verification_json"])
    assert verification["same_snapshot_json"] is True
    assert verification["same_change_intelligence"] is True
    assert verification["same_frozen_evidence"] is True
    assert verification["captured_at_gap_milliseconds"] == pytest.approx(6.7, abs=0.01)


# --- What is refused --------------------------------------------------


def test_a_different_conclusion_is_refused(engine) -> None:
    canonical = _write(engine, at=_T0, content_hash="hash-a")
    other = _write(engine, at=_T0 + timedelta(milliseconds=5), content_hash="hash-b")
    with pytest.raises(CorrectionRefused, match="same_content_hash"):
        apply_correction(engine, _request(canonical, other))
    assert _live_count(engine) == 2


def test_a_different_stored_payload_is_refused(engine) -> None:
    canonical = _write(engine, at=_T0, payload={"valuation_status": "fairly_valued"})
    other = _write(engine, at=_T0 + timedelta(milliseconds=5), payload={"valuation_status": "expensive"})
    with pytest.raises(CorrectionRefused, match="same_snapshot_json"):
        apply_correction(engine, _request(canonical, other))


def test_a_different_transition_is_refused(engine) -> None:
    canonical = _write(engine, at=_T0, change='{"changes": []}')
    other = _write(engine, at=_T0 + timedelta(milliseconds=5), change='{"changes": ["growth"]}')
    with pytest.raises(CorrectionRefused, match="same_change_intelligence"):
        apply_correction(engine, _request(canonical, other))


def test_an_evidence_only_change_is_refused(engine) -> None:
    """The case this correction most needs to get wrong-proof: the conclusion
    stands still while the evidence beneath it moves. That is a real second
    observation, and it is what Snapshot Evidence Persistence exists to keep.
    """
    canonical = _write(engine, at=_T0, payload={"valuation_evidence": {"fingerprint": "fp-1"}})
    later = _write(engine, at=_T0 + timedelta(milliseconds=5),
                   payload={"valuation_evidence": {"fingerprint": "fp-2"}})
    with pytest.raises(CorrectionRefused) as refusal:
        apply_correction(engine, _request(canonical, later))
    assert "same_frozen_evidence" in str(refusal.value)
    assert _live_count(engine) == 2


def test_a_legacy_row_against_an_evidence_bearing_row_is_refused(engine) -> None:
    canonical = _write(engine, at=_T0, payload={"valuation_evidence": None})
    modern = _write(engine, at=_T0 + timedelta(milliseconds=5),
                    payload={"valuation_evidence": {"fingerprint": "fp-1"}})
    with pytest.raises(CorrectionRefused, match="same_frozen_evidence"):
        apply_correction(engine, _request(canonical, modern))


def test_a_legitimate_return_to_an_earlier_state_is_refused(engine) -> None:
    """A -> B -> A is real history. Only rows with nothing surviving between
    them can be one observation recorded twice."""
    first = _write(engine, at=_T0, content_hash="hash-a")
    _write(engine, at=_T0 + timedelta(days=1), content_hash="hash-b")
    returned = _write(engine, at=_T0 + timedelta(days=2), content_hash="hash-a")
    with pytest.raises(CorrectionRefused, match="legitimate return"):
        apply_correction(engine, _request(first, returned))
    assert _live_count(engine) == 3


def test_timestamp_proximity_alone_never_justifies_a_correction(engine) -> None:
    """Two rows one millisecond apart whose payloads differ are two
    observations, however suspicious the timing looks."""
    canonical = _write(engine, at=_T0, payload={"valuation_status": "fairly_valued"})
    other = _write(engine, at=_T0 + timedelta(milliseconds=1), payload={"valuation_status": "expensive"})
    with pytest.raises(CorrectionRefused):
        apply_correction(engine, _request(canonical, other))


def test_correcting_the_earlier_row_is_refused(engine) -> None:
    canonical = _write(engine, at=_T0)
    duplicate = _write(engine, at=_T0 + timedelta(milliseconds=6.7))
    with pytest.raises(CorrectionRefused, match="must be the earlier one"):
        apply_correction(engine, _request(canonical=duplicate, duplicate=canonical))


def test_rows_from_different_cases_are_refused(engine) -> None:
    canonical = _write(engine, at=_T0)
    other = _write(engine, at=_T0 + timedelta(milliseconds=5), case_id="case-2")
    with pytest.raises(CorrectionRefused, match="different Cases"):
        apply_correction(engine, _request(canonical, other))


def test_a_retracted_canonical_is_refused(engine) -> None:
    canonical = _write(engine, at=_T0)
    duplicate = _write(engine, at=_T0 + timedelta(milliseconds=6.7))
    third = _write(engine, at=_T0 + timedelta(milliseconds=12))
    apply_correction(engine, _request(canonical, duplicate))
    with pytest.raises(CorrectionRefused, match="is itself retracted"):
        apply_correction(engine, _request(duplicate, third))


def test_a_row_already_retracted_by_another_correction_is_refused(engine) -> None:
    canonical = _write(engine, at=_T0)
    duplicate = _write(engine, at=_T0 + timedelta(milliseconds=6.7))
    apply_correction(engine, _request(canonical, duplicate, correction_id="c-1"))
    with pytest.raises(CorrectionRefused, match="already retracted"):
        apply_correction(engine, _request(canonical, duplicate, correction_id="c-2"))


def test_a_missing_row_is_refused(engine) -> None:
    canonical = _write(engine, at=_T0)
    with pytest.raises(CorrectionRefused, match="does not exist"):
        apply_correction(engine, _request(canonical, "no-such-row"))


def test_a_row_cannot_be_its_own_duplicate(engine) -> None:
    canonical = _write(engine, at=_T0)
    with pytest.raises(CorrectionRefused, match="its own duplicate"):
        apply_correction(engine, _request(canonical, canonical))


def test_the_same_duplicate_twice_in_one_request_is_refused(engine) -> None:
    canonical = _write(engine, at=_T0)
    duplicate = _write(engine, at=_T0 + timedelta(milliseconds=6.7))
    request = DuplicateCorrectionRequest(
        correction_id="c-1", reason="r",
        pairs=(DuplicatePair(canonical, duplicate), DuplicatePair(canonical, duplicate)))
    with pytest.raises(CorrectionRefused, match="appears twice"):
        apply_correction(engine, request)


# --- Idempotency and planning -----------------------------------------


def test_applying_the_same_correction_twice_writes_nothing_the_second_time(engine) -> None:
    canonical = _write(engine, at=_T0)
    duplicate = _write(engine, at=_T0 + timedelta(milliseconds=6.7))
    first = apply_correction(engine, _request(canonical, duplicate))
    second = apply_correction(engine, _request(canonical, duplicate))
    assert len(first.pending) == 1
    assert len(second.pending) == 0
    assert len(_ledger(engine)) == 1
    assert _live_count(engine) == 1


def test_planning_writes_nothing(engine) -> None:
    canonical = _write(engine, at=_T0)
    duplicate = _write(engine, at=_T0 + timedelta(milliseconds=6.7))
    plan = plan_correction(engine, _request(canonical, duplicate))
    assert len(plan.pending) == 1
    assert _row(engine, duplicate)["retracted_by"] is None
    assert _ledger(engine) == []


def test_corrections_are_addressed_by_row_id_not_ticker(engine) -> None:
    """A correction that could be aimed at a ticker could hit rows nobody
    reviewed."""
    import ast
    import inspect

    from atlas.alpha.snapshot_correction import service

    tree = ast.parse(inspect.getsource(service))
    # Identifiers and literals only -- the prose may discuss tickers; the code
    # must never touch one.
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    names |= {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    docstring_nodes = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docstring_nodes.add(id(first.value))
    literals = {node.value for node in ast.walk(tree)
                if isinstance(node, ast.Constant) and isinstance(node.value, str)
                and id(node) not in docstring_nodes}
    for forbidden in ("ticker", "instrument_key", "case_instrument_bindings"):
        assert forbidden not in names, f"{forbidden} referenced in code"
        assert not any(forbidden in literal for literal in literals), f"{forbidden} used as a value"
    assert "canonical_row_id" in inspect.signature(DuplicatePair).parameters


def test_an_empty_request_is_refused(engine) -> None:
    with pytest.raises(CorrectionRefused, match="no pairs"):
        plan_correction(engine, DuplicateCorrectionRequest(correction_id="c", reason="r", pairs=()))
