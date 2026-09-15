"""A methodology migration that composed a Case before evidence the new
method needs was recorded leaves transient history behind. The correction
must turn that history into exactly the one the migration writes when it
runs in the right order -- built here through the same production write
paths -- without deleting anything, and must refuse every request it cannot
prove is such an artifact."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, insert, select, update

from atlas.alpha.daily_brief_change_log.eligibility import EligibleChange
from atlas.alpha.daily_brief_change_log.store import DailyBriefChangeLogStore
from atlas.alpha.daily_brief_change_log.table import daily_brief_change_log_table
from atlas.alpha.decision_memory.engine import DecisionSnapshotInputs, build_snapshot, detect_decision_change
from atlas.alpha.decision_memory.repository import SqlAlchemyDecisionMemoryRepository, _snapshot_payload
from atlas.alpha.decision_memory.table import decision_memory_snapshot_table
from atlas.alpha.decision_path.models import FinalReachableState
from atlas.alpha.decision_readiness.models import DecisionReadinessStatus
from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.investment_case_change.table import investment_case_snapshot_table
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.migration_correction.service import (
    RECOMPUTE_TRANSITION,
    RETRACT,
    CorrectionRefused,
    CorrectionRequest,
    apply_correction,
    correction_schema_present,
    ensure_correction_schema,
    plan_correction,
)
from atlas.alpha.migration_correction.table import migration_artifact_correction_table
from atlas.alpha.opportunity_cost.models import AlternativeKind
from atlas.alpha.recommendation_conviction.models import ConvictionStrength, RecommendationStability
from atlas.analysis_engine.investment_case_change import AnalyticalSnapshot, compare_snapshots
from atlas.analysis_engine.methodology import METHODOLOGY_KEY
from atlas.analysis_engine.risk.financial_risk import FINANCIAL_RISK_METHODOLOGY
from atlas.analysis_engine.valuation.cash_flow import FISCAL_EPOCH_V2, VALUATION_METHODOLOGY

CASE = "case-under-migration"
OTHER_CASE = "case-bystander"
USER = "00000000-0000-0000-0000-000000000001"
OLD_IDENTITY = "financial_risk=debt_burden_v2;outlook=sensitivity_v2;rolling_growth=fiscal_year_windows_v2;valuation=fiscal_epoch_v2"

T_PRE = datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc)
WINDOW_START = datetime(2026, 1, 20, 0, 0, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 1, 20, 0, 10, tzinfo=timezone.utc)
T_A = WINDOW_START + timedelta(minutes=1)  # transient snapshot
T_B = WINDOW_START + timedelta(minutes=2)  # transient decision
T_E = WINDOW_START + timedelta(minutes=5)  # real snapshot
T_C = WINDOW_START + timedelta(minutes=6)  # real decision


def _analytical(*, valuation: str, valuation_risk: str, method: str, content_hash: str, at: datetime) -> AnalyticalSnapshot:
    return AnalyticalSnapshot(
        business_category_states=(("growth", "moderate", "business_finding:growth"),),
        risk_category_states=(("valuation_risk", valuation_risk, "risk_finding:valuation_risk"),),
        valuation_status=valuation,
        valuation_finding_id="valuation_finding:fcf_yield_relative",
        current_yield=None if valuation == "insufficient_input" else 0.02,
        strength_kinds=(),
        risk_highlight_kinds=() if valuation == "insufficient_input" else ("valuation",),
        open_question_origins=("valuation_inconclusive",) if valuation == "insufficient_input" else (),
        atlas_thesis_narrative="narrative",
        atlas_thesis_posture="risks_only",
        content_hash=content_hash,
        captured_at=at,
        financial_risk_methodology=FINANCIAL_RISK_METHODOLOGY,
        valuation_methodology=method,
    )


SNAP_PRE = _analytical(valuation="expensive", valuation_risk="high", method=FISCAL_EPOCH_V2, content_hash="h-pre", at=T_PRE)
SNAP_A = _analytical(valuation="insufficient_input", valuation_risk="insufficient_input", method=VALUATION_METHODOLOGY,
                     content_hash="h-transient", at=T_A)
SNAP_E = _analytical(valuation="expensive", valuation_risk="high", method=VALUATION_METHODOLOGY, content_hash="h-real", at=T_E)


def _decision(action: DecisionAction, strength: ConvictionStrength, alternatives: int, at: datetime):
    return build_snapshot(
        CASE,
        DecisionSnapshotInputs(
            action=action,
            readiness_status=DecisionReadinessStatus.WAITING,
            blocker_codes=("monitoring_pending",),
            conviction_strength=strength,
            conviction_stability=RecommendationStability.OPERATIONALLY_BLOCKED,
            decision_path_step_count=4,
            decision_path_final_state=FinalReachableState.FULLY_REACHABLE,
            primary_alternative_kind=AlternativeKind.WAIT,
            alternative_count=alternatives,
        ),
        recorded_at=at,
    )


MEM_PRE = _decision(DecisionAction.REDUCE, ConvictionStrength.WEAK, 2, T_PRE + timedelta(minutes=1))
MEM_B = _decision(DecisionAction.NO_DECISION, ConvictionStrength.UNAVAILABLE, 4, T_B)
MEM_C = _decision(DecisionAction.REDUCE, ConvictionStrength.WEAK, 3, T_C)


def _engine(path):
    engine = create_engine(f"sqlite:///{path}", future=True)
    ensure_correction_schema(engine)
    return engine


def _write_pre_migration(engine) -> None:
    snapshots = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
    snapshots.add(CASE, SNAP_PRE, compare_snapshots(None, SNAP_PRE))
    with engine.begin() as connection:
        connection.execute(
            insert(decision_memory_snapshot_table).values(
                id=f"{CASE}:{MEM_PRE.recorded_at.isoformat()}",
                case_id=CASE,
                ticker="XYZ",
                recorded_at=MEM_PRE.recorded_at.isoformat(),
                content_hash=MEM_PRE.content_hash,
                snapshot_json=json.dumps({**_snapshot_payload(MEM_PRE), METHODOLOGY_KEY: OLD_IDENTITY}, sort_keys=True),
                change_json=None,
            )
        )
    DailyBriefChangeLogStore(engine).record_if_new(USER, (_logged("weak", "unavailable", reason="recommendation_conviction_transition"),), now=T_PRE)


def _logged(value: str, previous: str, *, reason: str = "investment_decision_transition", case_id: str = CASE) -> EligibleChange:
    return EligibleChange(ticker="XYZ", case_id=case_id, reason_code=reason, value=value, secondary_value=previous,
                          label=None, headline=f"XYZ: {previous} -> {value}", priority_rank=0)


def _compose(engine, snapshot, decision) -> None:
    """One production composition: the snapshot and decision paths exactly
    as `InvestmentCaseCompositionService` / `DecisionMemoryService` write."""
    snapshots = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
    snapshots.add(CASE, snapshot, compare_snapshots(snapshots.get_latest(CASE), snapshot))
    memory = SqlAlchemyDecisionMemoryRepository(engine)
    memory.add(CASE, decision, detect_decision_change(memory.get_latest_comparable(CASE), decision, detected_at=decision.recorded_at),
               ticker="XYZ")


def _migrated_in_the_wrong_order(path):
    engine = _engine(path)
    _write_pre_migration(engine)
    _compose(engine, SNAP_A, MEM_B)
    _compose(engine, SNAP_E, MEM_C)
    DailyBriefChangeLogStore(engine).record_if_new(USER, (_logged("reduce", "no_decision"),), now=T_C)
    return engine


def _migrated_in_the_right_order(path):
    engine = _engine(path)
    _write_pre_migration(engine)
    _compose(engine, SNAP_E, MEM_C)
    return engine


def _id(at: datetime) -> str:
    return f"{CASE}:{at.isoformat()}"


def _log_id(engine, value: str, previous: str) -> str:
    with engine.connect() as connection:
        return connection.execute(
            select(daily_brief_change_log_table.c.id).where(
                daily_brief_change_log_table.c.value == value, daily_brief_change_log_table.c.secondary_value == previous
            )
        ).scalar_one()


def _request(engine, **overrides) -> CorrectionRequest:
    fields = dict(
        case_id=CASE,
        reason="migration composed the Case before its required evidence existed",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        retract_snapshot_ids=(_id(T_A),),
        recompute_snapshot_ids=(_id(T_E),),
        retract_memory_ids=(_id(T_B),),
        recompute_memory_ids=(_id(T_C),),
        retract_change_log_ids=(_log_id(engine, "reduce", "no_decision"),),
    )
    fields.update(overrides)
    return CorrectionRequest(**fields)


def _dump(engine) -> dict:
    with engine.connect() as connection:
        return {
            t.name: sorted(tuple(r) for r in connection.execute(select(t)))
            for t in (investment_case_snapshot_table, decision_memory_snapshot_table, daily_brief_change_log_table,
                      migration_artifact_correction_table)
        }


def _history(engine) -> dict:
    snapshots = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
    memory = SqlAlchemyDecisionMemoryRepository(engine)
    return {
        "snapshots": [(s.content_hash, c.is_baseline, c.changes, c.thesis_impact, c.summary_narrative)
                      for s, c in snapshots.get_history(CASE)],
        "latest_snapshot": snapshots.get_latest(CASE).content_hash,
        "memory": [(e.snapshot.content_hash, e.change.is_baseline, e.change.previous_action) for e in memory.get_history(CASE)],
        "memory_latest": memory.get_latest(CASE).content_hash,
        "memory_previous": memory.get_previous(CASE).content_hash,
        "memory_comparable": memory.get_latest_comparable(CASE).content_hash,
        "change_log": [(e.reason_code, e.value, e.secondary_value) for e in DailyBriefChangeLogStore(engine).list_recent(USER, now=T_C)],
    }


@pytest.fixture
def wrong(tmp_path):
    return _migrated_in_the_wrong_order(tmp_path / "wrong.db")


@pytest.fixture
def clean(tmp_path):
    return _migrated_in_the_right_order(tmp_path / "clean.db")


class TestTheArtifact:
    def test_the_wrong_order_narrates_the_migration_as_news(self, wrong, clean):
        assert _history(wrong) != _history(clean)
        assert ("investment_decision_transition", "reduce", "no_decision") in _history(wrong)["change_log"]


class TestCorrection:
    def test_a_dry_run_writes_nothing(self, wrong):
        before = _dump(wrong)
        plan = plan_correction(wrong, _request(wrong))
        assert len(plan.pending) == 5
        assert _dump(wrong) == before

    def test_the_corrected_history_is_the_right_order_history(self, wrong, clean):
        apply_correction(wrong, plan_correction(wrong, _request(wrong)))
        assert _history(wrong) == _history(clean)

    def test_the_recomputed_snapshot_transition_is_the_methodology_rebaseline_not_null(self, wrong):
        plan = plan_correction(wrong, _request(wrong))
        (snapshot_write,) = [w for w in plan.writes if w.action == RECOMPUTE_TRANSITION and w.target_row_id == _id(T_E)]
        assert json.loads(snapshot_write.after["change_intelligence_json"]) == {
            "changes": [], "summary_narrative": "No material change since the previous analysis.", "thesis_impact": "unchanged",
        }
        (memory_write,) = [w for w in plan.writes if w.action == RECOMPUTE_TRANSITION and w.target_row_id == _id(T_C)]
        assert memory_write.after == {"change_json": None}

    def test_current_state_is_untouched(self, wrong):
        memory = SqlAlchemyDecisionMemoryRepository(wrong)
        snapshots = SqlAlchemyInvestmentCaseSnapshotRepository(wrong)
        before = (snapshots.get_latest(CASE), memory.get_latest(CASE))
        apply_correction(wrong, plan_correction(wrong, _request(wrong)))
        assert (snapshots.get_latest(CASE), memory.get_latest(CASE)) == before

    def test_nothing_is_deleted_and_every_write_is_audited(self, wrong):
        before = _dump(wrong)
        apply_correction(wrong, plan_correction(wrong, _request(wrong)))
        after = _dump(wrong)
        for table in (investment_case_snapshot_table.name, decision_memory_snapshot_table.name, daily_brief_change_log_table.name):
            assert len(after[table]) == len(before[table])
        with wrong.connect() as connection:
            ledger = connection.execute(select(migration_artifact_correction_table)).mappings().all()
            retracted = connection.execute(
                select(decision_memory_snapshot_table.c.retracted_by).where(decision_memory_snapshot_table.c.id == _id(T_B))
            ).scalar_one()
        assert sorted(e["action"] for e in ledger) == [RECOMPUTE_TRANSITION] * 2 + [RETRACT] * 3
        assert retracted in {e["id"] for e in ledger}
        (memory_entry,) = [e for e in ledger if e["target_row_id"] == _id(T_C)]
        assert json.loads(json.loads(memory_entry["before_json"])["change_json"])["previousAction"] == "no_decision"
        assert memory_entry["predecessor_row_id"] == _id(MEM_PRE.recorded_at)
        assert all(e["reason"] and e["window_start"] == WINDOW_START.isoformat() for e in ledger)

    def test_a_second_run_writes_nothing(self, wrong):
        assert apply_correction(wrong, plan_correction(wrong, _request(wrong))) == 5
        after_first = _dump(wrong)
        assert apply_correction(wrong, plan_correction(wrong, _request(wrong))) == 0
        assert _dump(wrong) == after_first

    def test_a_retracted_change_log_entry_holds_no_natural_key(self, wrong):
        apply_correction(wrong, plan_correction(wrong, _request(wrong)))
        recorded = DailyBriefChangeLogStore(wrong).record_if_new(USER, (_logged("reduce", "no_decision"),), now=T_C + timedelta(days=1))
        assert len(recorded) == 1

    def test_the_dry_run_schema_check(self, tmp_path):
        engine = create_engine(f"sqlite:///{tmp_path / 'bare.db'}", future=True)
        assert not correction_schema_present(engine)
        ensure_correction_schema(engine)
        assert correction_schema_present(engine)


class TestRefusals:
    """Each guard, broken once: the correction refuses and writes nothing."""

    def _refused(self, engine, request, match: str) -> None:
        before = _dump(engine)
        with pytest.raises(CorrectionRefused, match=match):
            apply_correction(engine, plan_correction(engine, request))
        assert _dump(engine) == before

    def test_no_reason(self, wrong):
        self._refused(wrong, _request(wrong, reason="  "), "reason")

    def test_no_case(self, wrong):
        self._refused(wrong, _request(wrong, case_id=""), "Case id")

    def test_a_row_of_another_case(self, wrong):
        self._refused(wrong, _request(wrong, case_id=OTHER_CASE), "not a stored row")

    def test_a_naive_window(self, wrong):
        self._refused(wrong, _request(wrong, window_start=WINDOW_START.replace(tzinfo=None)), "timezone")

    def test_a_window_longer_than_one_migration(self, wrong):
        self._refused(wrong, _request(wrong, window_start=WINDOW_END - timedelta(days=2)), "at most")

    def test_a_target_outside_the_window(self, wrong):
        self._refused(wrong, _request(wrong, window_end=T_B + timedelta(seconds=1)), "outside the migration window")

    def test_the_current_head_is_never_retracted(self, wrong):
        self._refused(wrong, _request(wrong, retract_snapshot_ids=(_id(T_A), _id(T_E)), recompute_snapshot_ids=()),
                      "current state")

    def test_a_retraction_without_recomputing_its_successor(self, wrong):
        self._refused(wrong, _request(wrong, recompute_snapshot_ids=()), "must be recomputed")

    def test_a_predecessor_inside_the_window(self, wrong):
        self._refused(wrong, _request(wrong, window_start=T_PRE, window_end=T_PRE + timedelta(hours=23)),
                      "outside the migration window")

    def test_no_methodology_boundary(self, wrong):
        with wrong.begin() as connection:
            row = connection.execute(select(investment_case_snapshot_table.c.snapshot_json)
                                     .where(investment_case_snapshot_table.c.id == _id(T_PRE))).scalar_one()
            payload = json.loads(row)
            payload["valuation_methodology"] = VALUATION_METHODOLOGY
            connection.execute(update(investment_case_snapshot_table).where(investment_case_snapshot_table.c.id == _id(T_PRE))
                               .values(snapshot_json=json.dumps(payload, sort_keys=True)))
        self._refused(wrong, _request(wrong), "no methodology migration")

    def test_rows_written_under_another_methodology_than_this_code(self, wrong, monkeypatch):
        import atlas.alpha.migration_correction.service as service

        monkeypatch.setattr(service, "ANALYSIS_METHODOLOGY", OLD_IDENTITY + "+next")
        self._refused(wrong, _request(wrong), "not the methodology this code runs")

    def test_a_transition_already_clean_is_not_an_artifact(self, wrong):
        clean_value = json.dumps({"changes": [], "summary_narrative": "No material change since the previous analysis.",
                                  "thesis_impact": "unchanged"}, sort_keys=True)
        with wrong.begin() as connection:
            connection.execute(update(investment_case_snapshot_table).where(investment_case_snapshot_table.c.id == _id(T_E))
                               .values(change_intelligence_json=clean_value))
        self._refused(wrong, _request(wrong), "already holds its clean transition")

    def test_only_a_correction_that_retracts_something(self, wrong):
        self._refused(wrong, _request(wrong, retract_snapshot_ids=(), retract_memory_ids=(), retract_change_log_ids=()),
                      "retracts at least one row")

    def test_a_genuine_change_log_entry_outside_the_window(self, wrong):
        self._refused(wrong, _request(wrong, retract_change_log_ids=(_log_id(wrong, "weak", "unavailable"),)),
                      "outside the migration window")

    def test_a_change_log_entry_that_narrates_something_else(self, wrong):
        DailyBriefChangeLogStore(wrong).record_if_new(USER, (_logged("exit", "no_decision"),), now=T_C)
        self._refused(wrong, _request(wrong, retract_change_log_ids=(_log_id(wrong, "exit", "no_decision"),)),
                      "narrates no retracted")

    def test_a_change_log_entry_of_another_case(self, wrong):
        DailyBriefChangeLogStore(wrong).record_if_new(USER, (_logged("reduce", "hold", case_id=OTHER_CASE),), now=T_C)
        self._refused(wrong, _request(wrong, retract_change_log_ids=(_log_id(wrong, "reduce", "hold"),)), "belongs to Case")

    def test_a_change_log_reason_memory_does_not_record(self, wrong):
        DailyBriefChangeLogStore(wrong).record_if_new(USER, (_logged("mixed", None, reason="change_intelligence_thesis_impact"),),
                                                      now=T_C)
        with wrong.connect() as connection:
            entry = connection.execute(select(daily_brief_change_log_table.c.id).where(
                daily_brief_change_log_table.c.reason_code == "change_intelligence_thesis_impact")).scalar_one()
        self._refused(wrong, _request(wrong, retract_change_log_ids=(entry,)), "not a transition Decision Memory records")

    def test_market_data_recorded_inside_the_window(self, wrong):
        with wrong.begin() as connection:
            connection.exec_driver_sql("create table business_records (id text, version_created_at text)")
            connection.exec_driver_sql("insert into business_records values ('r', ?)", ((T_A + timedelta(seconds=30)).isoformat(),))
        self._refused(wrong, _request(wrong), "business_records: 1 rows recorded inside the window")

    def test_share_evidence_retrieved_inside_the_window(self, wrong):
        with wrong.begin() as connection:
            connection.exec_driver_sql("create table class_rights_observations (recorded_at text, retrieved_at text)")
            connection.exec_driver_sql("insert into class_rights_observations values (?, ?)",
                                       (T_A.isoformat(), (WINDOW_START + timedelta(seconds=5)).isoformat()))
        self._refused(wrong, _request(wrong), "retrieved inside it")

    def test_any_evidence_table_with_retrieval_provenance_is_found_by_its_shape(self, wrong):
        with wrong.begin() as connection:
            connection.exec_driver_sql("create table some_future_evidence (recorded_at text, retrieved_at text)")
            connection.exec_driver_sql("insert into some_future_evidence values (?, ?)", (T_E.isoformat(), T_E.isoformat()))
        self._refused(wrong, _request(wrong), "some_future_evidence: 1 rows inside the window were retrieved inside it")

    def test_share_evidence_retrieved_before_the_window_is_migration_evidence(self, wrong):
        with wrong.begin() as connection:
            connection.exec_driver_sql("create table class_rights_observations (recorded_at text, retrieved_at text)")
            connection.exec_driver_sql("insert into class_rights_observations values (?, ?)",
                                       (T_A.isoformat(), (WINDOW_START - timedelta(hours=4)).isoformat()))
        plan = plan_correction(wrong, _request(wrong))
        assert plan.verification["evidence"]["class_rights_observations"]["recorded_in_window"] == 1

    def test_case_evidence_recorded_inside_the_window(self, wrong):
        with wrong.begin() as connection:
            connection.exec_driver_sql("create table evidence_snapshots (case_id text, captured_at text)")
            connection.exec_driver_sql("insert into evidence_snapshots values (?, ?)", (CASE, T_E.isoformat()))
        self._refused(wrong, _request(wrong), "evidence_snapshots")

    def test_the_database_moved_since_the_plan(self, wrong):
        plan = plan_correction(wrong, _request(wrong))
        with wrong.begin() as connection:
            connection.execute(update(decision_memory_snapshot_table).where(decision_memory_snapshot_table.c.id == _id(T_C))
                               .values(change_json='{"tampered": true}'))
        before = _dump(wrong)
        with pytest.raises(CorrectionRefused, match="changed since this plan"):
            apply_correction(wrong, plan)
        assert _dump(wrong) == before

    def test_a_row_retracted_by_another_correction(self, wrong):
        apply_correction(wrong, plan_correction(wrong, _request(wrong)))
        self._refused(wrong, _request(wrong, reason="a different reason"), "already retracted")


class TestReadsSkipRetractedRows:
    def test_every_history_read(self, wrong, clean):
        apply_correction(wrong, plan_correction(wrong, _request(wrong)))
        corrected = _history(wrong)
        assert corrected["memory_previous"] == MEM_PRE.content_hash
        assert _id(T_A) not in [s.content_hash for s, _ in SqlAlchemyInvestmentCaseSnapshotRepository(wrong).get_history(CASE)]
        assert "h-transient" not in [row[0] for row in corrected["snapshots"]]
        assert ("investment_decision_transition", "reduce", "no_decision") not in corrected["change_log"]
        assert corrected == _history(clean)

    def test_stored_rows_still_show_them(self, wrong):
        apply_correction(wrong, plan_correction(wrong, _request(wrong)))
        stored = SqlAlchemyDecisionMemoryRepository(wrong).stored_rows(CASE)
        assert [r.id for r in stored if r.retracted_by is not None] == [_id(T_B)]
