"""Snapshot persistence must be idempotent under concurrency.

Deciding whether the record moved means reading the head and then inserting.
While those were two separate SQLite transactions, two composers of the same
Case both read the same head, both concluded it had moved, and both wrote --
identical rows differing only by microseconds. No conclusion was falsified,
but the same observation was counted twice, which is precisely what a
longitudinal record must never do.

These tests cover both halves: that the race is closed, and that closing it
did not quietly collapse the persistence doctrine it sits on -- evidence-only
changes, methodology boundaries and the legacy transition must all still
write, and an excluded price tick must still not.
"""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.investment_case.valuation_evidence_snapshot import (
    SCHEMA_VERSION,
    FrozenEpoch,
    ValuationEvidenceSnapshot,
)
from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.investment_case_change.table import (
    create_investment_case_snapshot_table,
    investment_case_snapshot_table,
)
from atlas.analysis_engine.investment_case_change import AnalyticalSnapshot, compare_snapshots

_T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
_T1 = datetime(2026, 2, 1, tzinfo=timezone.utc)
_T2 = datetime(2026, 3, 1, tzinfo=timezone.utc)

# `id` is `case_id:captured_at`, so two rows can only coexist with distinct
# capture times -- which is exactly what the real race produced: composers
# each stamp their own `datetime.now()`, microseconds apart.
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _snapshot(*, content_hash: str, captured_at: datetime = _T0,
              current_yield: float | None = 0.03) -> AnalyticalSnapshot:
    return AnalyticalSnapshot(
        business_category_states=(("growth", "moderate", "business_finding:growth"),),
        risk_category_states=(),
        valuation_status="fairly_valued",
        valuation_finding_id="valuation_finding:fcf_yield_relative",
        current_yield=current_yield,
        strength_kinds=(),
        risk_highlight_kinds=(),
        open_question_origins=(),
        atlas_thesis_narrative="The case is supported by growth.",
        atlas_thesis_posture="strengths_only",
        content_hash=content_hash,
        captured_at=captured_at,
    )


def _baseline(snapshot: AnalyticalSnapshot):
    return compare_snapshots(None, snapshot)


def _epoch(fiscal_period: str, fcf_yield: float) -> FrozenEpoch:
    return FrozenEpoch(
        fiscal_period=fiscal_period, free_cash_flow=100.0, raw_free_cash_flow=100.0,
        senior_claim_low=0.0, senior_claim_high=0.0, market_cap_low=1000.0, market_cap_high=1000.0,
        share_price=10.0, shares_outstanding=100.0, currency="USD", fcf_yield=fcf_yield,
        denominator_quality="issuer_equivalent", observed_on="2026-01-01", available_from="2026-01-01",
    )


def _evidence(*, fingerprint: str, methodology: str = "fiscal_epoch_v3",
              priors: tuple[FrozenEpoch, ...] = ()) -> ValuationEvidenceSnapshot:
    return ValuationEvidenceSnapshot(
        schema_version=SCHEMA_VERSION, valuation_methodology=methodology,
        numerator_method="common_attributable_fcf_v1", nci_treatment="unmeasured",
        share_count_method="issuer_common_equity_market_cap", eligibility="eligible",
        minimum_prior_epochs=3, withheld_reasons=(), valuation_position="within_prior_range",
        valuation_status="fairly_valued", current_yield=0.03, current_epoch=None,
        prior_epochs=priors, valuation_support_status="supported", valuation_support_gap=None,
        metadata=None, fingerprint=fingerprint,
    )


@pytest.fixture
def engine() -> Engine:
    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool,
                           connect_args={"check_same_thread": False})
    create_investment_case_snapshot_table(engine)
    return engine


@pytest.fixture
def file_engine(tmp_path) -> Engine:
    """Concurrency needs a real file and a real pool.

    The in-memory `StaticPool` fixture above shares a single DBAPI
    connection, so two threads would interleave inside one transaction and
    test the fixture rather than the code.
    """
    engine = create_engine(f"sqlite:///{tmp_path / 'atlas.db'}", future=True)
    create_investment_case_snapshot_table(engine)
    return engine


def _rows(engine: Engine, case_id: str = "case-1"):
    with engine.connect() as connection:
        return connection.execute(
            investment_case_snapshot_table.select()
            .where(investment_case_snapshot_table.c.case_id == case_id)
        ).mappings().all()


# --- The persistence doctrine still holds -----------------------------


def test_the_first_snapshot_is_written(engine) -> None:
    repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
    snapshot = _snapshot(content_hash="hash-a")
    assert repository.add("case-1", snapshot, _baseline(snapshot)) is True
    assert len(_rows(engine)) == 1


def test_an_identical_recomposition_writes_nothing(engine) -> None:
    repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
    snapshot = _snapshot(content_hash="hash-a")
    repository.add("case-1", snapshot, _baseline(snapshot))
    assert repository.add("case-1", snapshot, _baseline(snapshot)) is False
    assert len(_rows(engine)) == 1


def test_a_changed_conclusion_writes(engine) -> None:
    repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
    first = _snapshot(content_hash="hash-a")
    repository.add("case-1", first, _baseline(first))
    second = _snapshot(content_hash="hash-b", captured_at=_T1)
    assert repository.add("case-1", second, compare_snapshots(first, second)) is True
    assert len(_rows(engine)) == 2


def test_evidence_moving_under_an_unchanged_conclusion_still_writes(engine) -> None:
    """The heart of Snapshot Evidence Persistence: the conclusion can stand
    still while the evidence under it moves, and absorbing that would leave
    the record saying the evidence never changed."""
    repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
    snapshot = _snapshot(content_hash="hash-a")
    repository.add("case-1", snapshot, _baseline(snapshot),
                   valuation_evidence=_evidence(fingerprint="fp-1"))
    later = _snapshot(content_hash="hash-a", captured_at=_T1)
    assert repository.add("case-1", later, _baseline(later),
                          valuation_evidence=_evidence(fingerprint="fp-2")) is True
    assert len(_rows(engine)) == 2


def test_identical_evidence_under_an_unchanged_conclusion_writes_nothing(engine) -> None:
    repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
    snapshot = _snapshot(content_hash="hash-a")
    evidence = _evidence(fingerprint="fp-1")
    repository.add("case-1", snapshot, _baseline(snapshot), valuation_evidence=evidence)
    assert repository.add("case-1", snapshot, _baseline(snapshot), valuation_evidence=evidence) is False
    assert len(_rows(engine)) == 1


def test_a_methodology_boundary_is_not_collapsed(engine) -> None:
    """Different methodology means a different fingerprint, so the record
    keeps the boundary rather than pretending one method produced both."""
    repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
    snapshot = _snapshot(content_hash="hash-a")
    repository.add("case-1", snapshot, _baseline(snapshot),
                   valuation_evidence=_evidence(fingerprint="fp-v2", methodology="fiscal_epoch_v2"))
    later = _snapshot(content_hash="hash-a", captured_at=_T1)
    assert repository.add("case-1", later, _baseline(later),
                          valuation_evidence=_evidence(fingerprint="fp-v3",
                                                       methodology="fiscal_epoch_v3")) is True


def test_a_price_tick_alone_still_writes_nothing(engine) -> None:
    """`content_hash` and the fingerprint both exclude the current yield: a
    price move is not new evidence, and atomicity must not change that."""
    repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
    evidence = _evidence(fingerprint="fp-1")
    repository.add("case-1", _snapshot(content_hash="hash-a", current_yield=0.03),
                   _baseline(_snapshot(content_hash="hash-a")), valuation_evidence=evidence)
    moved = _snapshot(content_hash="hash-a", current_yield=0.09)
    assert repository.add("case-1", moved, _baseline(moved), valuation_evidence=evidence) is False
    assert len(_rows(engine)) == 1


def test_the_first_modern_snapshot_after_a_legacy_head_writes(engine) -> None:
    """The live transition: a legacy head carries no evidence, so the first
    evidence-bearing composition must be recorded, not absorbed."""
    repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
    snapshot = _snapshot(content_hash="hash-a")
    repository.add("case-1", snapshot, _baseline(snapshot))  # legacy: no evidence
    modern = _snapshot(content_hash="hash-a", captured_at=_T1)
    assert repository.add("case-1", modern, _baseline(modern),
                          valuation_evidence=_evidence(fingerprint="fp-1")) is True
    assert len(_rows(engine)) == 2


def test_a_retracted_head_does_not_block_a_return_to_that_state(engine) -> None:
    """Why this is a transaction and not a uniqueness constraint: a retracted
    row is invisible to the head read, and a legitimate later return to the
    same state must still be recordable. A UNIQUE key could not express that.
    """
    repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
    snapshot = _snapshot(content_hash="hash-a")
    repository.add("case-1", snapshot, _baseline(snapshot),
                   valuation_evidence=_evidence(fingerprint="fp-1"))
    with engine.begin() as connection:
        connection.execute(text("update investment_case_snapshots set retracted_by='correction-1'"))
    returned = _snapshot(content_hash="hash-a", captured_at=_T1)
    assert repository.add("case-1", returned, _baseline(returned),
                          valuation_evidence=_evidence(fingerprint="fp-1")) is True
    assert len(_rows(engine)) == 2


# --- Concurrency ------------------------------------------------------


def test_concurrent_threads_writing_the_same_state_produce_one_row(file_engine) -> None:
    """Each writer stamps its own capture time, exactly as real composers do
    -- so the primary key cannot mask the race, and only the atomic head
    read can stop a second row."""
    repository = SqlAlchemyInvestmentCaseSnapshotRepository(file_engine)
    evidence = _evidence(fingerprint="fp-1")

    def write(n: int):
        snapshot = _snapshot(content_hash="hash-a",
                             captured_at=_T0.replace(microsecond=n + 1))
        return repository.add("case-1", snapshot, _baseline(snapshot), valuation_evidence=evidence)

    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(write, range(10)))

    assert sum(1 for r in results if r) == 1, "more than one writer believed it moved the record"
    assert len(_rows(file_engine)) == 1


def test_different_cases_are_not_serialised_into_one_row(file_engine) -> None:
    """The lock guards persistence, not the application: two different Cases
    must both persist."""
    repository = SqlAlchemyInvestmentCaseSnapshotRepository(file_engine)
    snapshot = _snapshot(content_hash="hash-a")

    def write(case_id):
        return repository.add(case_id, snapshot, _baseline(snapshot))

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(write, [f"case-{n}" for n in range(6)]))
    assert all(results)
    for n in range(6):
        assert len(_rows(file_engine, f"case-{n}")) == 1


def test_a_failed_insert_rolls_back_and_leaves_the_record_usable(engine) -> None:
    """A writer that dies inside the critical section must not leave the
    transaction open, or every later composer would block on it."""
    repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
    snapshot = _snapshot(content_hash="hash-a")

    class _Exploding:
        content_hash = "hash-a"

        def __getattr__(self, name):
            raise RuntimeError("serialisation exploded")

    with pytest.raises(Exception):
        repository.add("case-1", _Exploding(), _baseline(snapshot))
    assert _rows(engine) == []
    assert repository.add("case-1", snapshot, _baseline(snapshot)) is True
    assert len(_rows(engine)) == 1


def _worker_script(database: str, content_hash: str) -> str:
    return textwrap.dedent(f"""
        import sys, time
        sys.path.insert(0, {REPO!r})
        from datetime import datetime, timezone
        from sqlalchemy import create_engine
        from atlas.alpha.investment_case_change.repository import (
            SqlAlchemyInvestmentCaseSnapshotRepository)
        from atlas.alpha.investment_case_change.table import create_investment_case_snapshot_table
        from atlas.analysis_engine.investment_case_change import AnalyticalSnapshot, compare_snapshots
        engine = create_engine("sqlite:///{database}", future=True)
        create_investment_case_snapshot_table(engine)
        snapshot = AnalyticalSnapshot(
            business_category_states=(("growth","moderate","business_finding:growth"),),
            risk_category_states=(), valuation_status="fairly_valued",
            valuation_finding_id="valuation_finding:fcf_yield_relative", current_yield=0.03,
            strength_kinds=(), risk_highlight_kinds=(), open_question_origins=(),
            atlas_thesis_narrative="n", atlas_thesis_posture="strengths_only",
            content_hash={content_hash!r},
            captured_at=datetime(2026,1,1,microsecond=int(sys.argv[2]),tzinfo=timezone.utc))
        start = float(sys.argv[1])
        while time.time() < start:
            time.sleep(0.0005)
        wrote = SqlAlchemyInvestmentCaseSnapshotRepository(engine).add(
            "case-1", snapshot, compare_snapshots(None, snapshot))
        print("WROTE" if wrote else "DEDUPED", flush=True)
    """)


def test_separate_processes_writing_the_same_state_produce_one_row(tmp_path) -> None:
    """The authoritative test. `threading.Lock` cannot help here: a batch run
    from a command and the API serving a page are different processes, which
    is exactly how this was reachable in production."""
    import time

    database = tmp_path / "atlas.db"
    engine = create_engine(f"sqlite:///{database}", future=True)
    create_investment_case_snapshot_table(engine)

    start = time.time() + 2.0
    children = [
        subprocess.Popen([sys.executable, "-c", _worker_script(str(database), "hash-a"),
                          str(start), str(n + 1)], stdout=subprocess.PIPE, text=True)
        for n in range(5)
    ]
    outs = [c.stdout.read().strip() for c in children]
    for child in children:
        child.wait(120)

    assert outs.count("WROTE") == 1, f"expected exactly one writer, got {outs}"
    assert len(_rows(engine)) == 1
