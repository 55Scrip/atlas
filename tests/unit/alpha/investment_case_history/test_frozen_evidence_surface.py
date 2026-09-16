"""History shows what Atlas had then -- and can be made to prove it.

The read path is only trustworthy if it cannot be talked into substituting
today's evidence. These tests attach evidence by snapshot identity, keep two
snapshots of one Case distinct under an identical conclusion, and destroy the
current evidence entirely before re-reading a historical entry.

The layering matters as much as the content: Core computes and orders the
history, Alpha carries the frozen evidence, and the join happens in the API
schema. A test at the bottom holds that boundary.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, insert
from sqlalchemy.pool import StaticPool

from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.investment_case_change.table import (
    create_investment_case_snapshot_table,
    investment_case_snapshot_table,
)
from atlas.alpha.investment_case_history.api.schemas import (
    AnalyticalHistoryView,
    HistoricalValuationEvidenceView,
)
from atlas.alpha.investment_case_history.service import AnalyticalHistoryWithEvidence, snapshot_identity
from atlas.analysis_engine.investment_case_history import HistoricalAnalysisEntry, build_analytical_history

from tests.unit.alpha.investment_case_change.test_valuation_evidence_snapshot import (
    CURRENT,
    PRIORS,
    baseline,
    frozen,
    snapshot,
)
from tests.unit.alpha.investment_case.test_valuation_evidence_metadata import epoch
from tests.unit.alpha.investment_case_history.test_service import harness  # noqa: F401

_T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
CASE = "case-1"


@pytest.fixture()
def repository():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    create_investment_case_snapshot_table(engine)
    return SqlAlchemyInvestmentCaseSnapshotRepository(engine), engine


def view_of(repository_, case_id: str = CASE, ticker: str = "TCK") -> AnalyticalHistoryView:
    """The exact join the service and router perform, over one Case."""
    entries, evidence_by_snapshot = [], {}
    for snap, transition, evidence in repository_.get_history_with_evidence(case_id):
        entries.append(HistoricalAnalysisEntry(
            case_id=case_id, ticker=ticker, snapshot=snap, change_intelligence=transition))
        evidence_by_snapshot[snapshot_identity(case_id, snap.captured_at)] = evidence
    return AnalyticalHistoryView.from_domain(AnalyticalHistoryWithEvidence(
        history=build_analytical_history(tuple(entries), generated_at=_T0),
        evidence_by_snapshot_id=evidence_by_snapshot,
    ))


def legacy_row(connection, *, captured_at: datetime, content_hash: str = "old"):
    connection.execute(insert(investment_case_snapshot_table).values(
        id=f"{CASE}:{captured_at.isoformat()}", case_id=CASE, captured_at=captured_at.isoformat(),
        content_hash=content_hash, current_yield=None,
        snapshot_json=json.dumps({
            "business_category_states": [], "risk_category_states": [],
            "valuation_status": "fairly_valued", "valuation_finding_id": "f",
            "strength_kinds": [], "risk_highlight_kinds": [], "open_question_origins": [],
        }),
        change_intelligence_json=None))


class TestLegacy:
    def test_a_pre_persistence_snapshot_reports_no_evidence_rather_than_an_empty_one(self, repository):
        repo, engine = repository
        with engine.begin() as connection:
            legacy_row(connection, captured_at=_T0)
        entry = view_of(repo).entries[0]
        assert entry.valuation_evidence is None

    def test_legacy_and_evidence_bearing_rows_live_together(self, repository):
        """The real future state: one Case with old rows and new ones."""
        repo, engine = repository
        with engine.begin() as connection:
            legacy_row(connection, captured_at=_T0)
            legacy_row(connection, captured_at=_T0 + timedelta(days=1), content_hash="old2")
        repo.add(CASE, snapshot(content_hash="new", captured_at=_T0 + timedelta(days=2)),
                 baseline(), valuation_evidence=frozen(PRIORS, CURRENT))
        entries = view_of(repo).entries
        assert len(entries) == 3
        assert [e.valuation_evidence is None for e in entries] == [False, True, True], "newest first"


class TestWithheld:
    def test_a_withheld_valuation_is_recorded_evidence_not_an_absence(self, repository):
        from atlas.analysis_engine.valuation.contracts import ValuationDecisionEligibility
        from atlas.analysis_engine.valuation.models import FcfYieldEvidence, ShareCountMethod
        from atlas.alpha.investment_case.valuation_evidence_snapshot import freeze_valuation_evidence
        from tests.unit.alpha.investment_case_change.test_valuation_evidence_snapshot import METHOD, SUPPORT
        from tests.unit.alpha.investment_case.test_valuation_evidence_metadata import finding

        repo, _ = repository
        bare = FcfYieldEvidence(
            eligibility=ValuationDecisionEligibility.NOT_APPLICABLE, minimum_prior_epochs=3,
            share_count_method=ShareCountMethod.CURRENT_SHARE_COUNT_PROXY)
        repo.add(CASE, snapshot(content_hash="h1"), baseline(),
                 valuation_evidence=freeze_valuation_evidence(
                     finding(bare), SUPPORT, None, valuation_methodology=METHOD))
        evidence = view_of(repo).entries[0].valuation_evidence
        assert evidence is not None, "a withheld valuation is not a legacy absence"
        assert evidence.prior_epoch_count == 0
        assert evidence.eligibility == "not_applicable"
        assert evidence.valuation_support_status == "insufficient_input"


class TestSnapshotIdentity:
    def test_two_snapshots_of_one_case_keep_their_own_evidence(self, repository):
        """S1/S2: identical conclusion, different prior sets. Attaching by
        ticker would give both the newest evidence; attaching by snapshot
        identity gives each its own."""
        repo, _ = repository
        first = frozen(PRIORS, CURRENT)
        repo.add(CASE, snapshot(content_hash="h1", captured_at=_T0), baseline(), valuation_evidence=first)
        deeper = [epoch(2021, fcf=100, market_cap=2_500), *PRIORS]
        second = frozen(deeper, CURRENT)
        repo.add(CASE, snapshot(content_hash="h1", captured_at=_T0 + timedelta(days=1)),
                 baseline(), valuation_evidence=second)
        entries = view_of(repo).entries
        assert [e.valuation_evidence.prior_epoch_count for e in entries] == [4, 3], "newest first"
        assert entries[0].snapshot_id != entries[1].snapshot_id

    def test_the_join_key_is_the_snapshot_id_the_api_publishes(self, repository):
        repo, _ = repository
        repo.add(CASE, snapshot(content_hash="h1"), baseline(), valuation_evidence=frozen(PRIORS, CURRENT))
        entry = view_of(repo).entries[0]
        assert entry.snapshot_id == snapshot_identity(CASE, _T0)


class TestFrozenRead:
    def test_a_later_snapshot_never_rewrites_an_earlier_entry(self, repository):
        repo, _ = repository
        repo.add(CASE, snapshot(content_hash="h1", captured_at=_T0), baseline(),
                 valuation_evidence=frozen(PRIORS, CURRENT))
        before = view_of(repo).entries[0].model_dump_json()
        restated = [epoch(2022, fcf=999, market_cap=2_000), *PRIORS[1:]]
        repo.add(CASE, snapshot(content_hash="h1", captured_at=_T0 + timedelta(days=1)),
                 baseline(), valuation_evidence=frozen(restated, CURRENT))
        oldest = view_of(repo).entries[-1]
        assert oldest.model_dump_json() == before, "the earlier entry changed when a later one arrived"

    def test_the_history_read_writes_nothing(self, repository):
        repo, engine = repository
        repo.add(CASE, snapshot(content_hash="h1"), baseline(), valuation_evidence=frozen(PRIORS, CURRENT))
        with engine.connect() as connection:
            before = connection.execute(investment_case_snapshot_table.select()).mappings().all()
        view_of(repo)
        view_of(repo)
        with engine.connect() as connection:
            after = connection.execute(investment_case_snapshot_table.select()).mappings().all()
        assert [dict(r) for r in before] == [dict(r) for r in after]

    def test_a_retracted_snapshot_stays_hidden(self, repository):
        repo, engine = repository
        repo.add(CASE, snapshot(content_hash="h1", captured_at=_T0), baseline(),
                 valuation_evidence=frozen(PRIORS, CURRENT))
        repo.add(CASE, snapshot(content_hash="h2", captured_at=_T0 + timedelta(days=1)), baseline(),
                 valuation_evidence=frozen(PRIORS, CURRENT))
        with engine.begin() as connection:
            connection.execute(investment_case_snapshot_table.update()
                               .where(investment_case_snapshot_table.c.captured_at == _T0.isoformat())
                               .values(retracted_by="correction-1"))
        entries = view_of(repo).entries
        assert len(entries) == 1, "a retracted row reappeared through the evidence reader"


class TestPreservedContent:
    def test_methodology_identity_survives_the_read(self, repository):
        repo, _ = repository
        repo.add(CASE, snapshot(content_hash="h1"), baseline(), valuation_evidence=frozen(PRIORS, CURRENT))
        evidence = view_of(repo).entries[0].valuation_evidence
        assert "fiscal_epoch_v3" in (evidence.valuation_methodology or "")
        assert evidence.schema_version == "valuation_evidence_snapshot_v1"

    def test_the_range_edges_and_prior_order_survive_the_read(self, repository):
        repo, _ = repository
        repo.add(CASE, snapshot(content_hash="h1"), baseline(), valuation_evidence=frozen(PRIORS, CURRENT))
        evidence = view_of(repo).entries[0].valuation_evidence
        assert [e.fiscal_year for e in evidence.prior_epochs] == [2022, 2023, 2024]
        assert evidence.range_edge.low_edge_fiscal_year == 2022
        assert evidence.range_edge.high_edge_fiscal_year == 2024
        assert evidence.range_edge.second_lowest_fiscal_year == 2023

    def test_valuation_support_and_the_yield_of_the_day_survive_the_read(self, repository):
        repo, _ = repository
        repo.add(CASE, snapshot(content_hash="h1"), baseline(), valuation_evidence=frozen(PRIORS, CURRENT))
        evidence = view_of(repo).entries[0].valuation_evidence
        assert evidence.valuation_support_status == "insufficient_input"
        assert evidence.valuation_support_gap == "scenario_envelope_inconclusive"
        assert evidence.fcf_yield_at_analysis == pytest.approx(100 / 1_500)

    def test_ordering_and_row_count_are_untouched_by_the_join(self, repository):
        repo, _ = repository
        for index in range(4):
            repo.add(CASE, snapshot(content_hash=f"h{index}", captured_at=_T0 + timedelta(days=index)),
                     baseline(), valuation_evidence=frozen(PRIORS, CURRENT))
        entries = view_of(repo).entries
        assert len(entries) == 4
        assert [e.captured_at for e in entries] == sorted((e.captured_at for e in entries), reverse=True)
        assert len({e.snapshot_id for e in entries}) == 4


class TestLayering:
    def test_core_never_imports_the_alpha_evidence_type(self):
        """The join belongs outside Core. Core computes and orders history; it
        must not learn how Atlas persists evidence."""
        import ast
        from pathlib import Path

        root = Path(__file__).resolve().parents[4]
        offenders = []
        for directory in ("atlas/analysis_engine", "atlas/decision_engine"):
            for path in (root / directory).rglob("*.py"):
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module and (
                        "valuation_evidence_snapshot" in node.module
                        or "investment_case_change.repository" in node.module
                        or "investment_case_history.service" in node.module
                    ):
                        offenders.append(f"{path.relative_to(root)} -> {node.module}")
        assert offenders == []

    def test_the_core_history_contract_is_unchanged(self):
        """`HistoricalAnalysisEntry` still has exactly its four Core fields."""
        from dataclasses import fields

        assert {f.name for f in fields(HistoricalAnalysisEntry)} == {
            "case_id", "ticker", "snapshot", "change_intelligence"}

    def test_the_evidence_view_tolerates_an_absent_record(self):
        assert HistoricalValuationEvidenceView.from_domain(None) is None


# -- through the REAL service, not a hand-built join -------------------------


class TestThroughTheService:
    """The join the router actually performs, over real stores. The tests above
    build the map themselves; these do not, so a service that keyed evidence by
    ticker, or a join that reordered Core's history, would be caught here."""

    def test_two_snapshots_of_one_case_keep_their_own_evidence(self, harness):
        from atlas.alpha.investment_case_history.api.schemas import AnalyticalHistoryView

        case_id = harness.import_holding("TCK")
        first = frozen(PRIORS, CURRENT)
        harness.snapshot_repository.add(
            case_id, snapshot(content_hash="h1", captured_at=_T0), baseline(), valuation_evidence=first)
        deeper = [epoch(2021, fcf=100, market_cap=2_500), *PRIORS]
        harness.snapshot_repository.add(
            case_id, snapshot(content_hash="h1", captured_at=_T0 + timedelta(days=1)), baseline(),
            valuation_evidence=frozen(deeper, CURRENT))
        view = AnalyticalHistoryView.from_domain(harness.history_service.build_analytical_history())
        counts = [entry.valuation_evidence.prior_epoch_count for entry in view.entries]
        assert counts == [4, 3], "the service attached one Case's newest evidence to both of its snapshots"

    def test_the_join_preserves_core_ordering_across_several_cases(self, harness):
        from atlas.alpha.investment_case_history.api.schemas import AnalyticalHistoryView

        first_case = harness.import_holding("AAA")
        second_case = harness.add_to_watchlist("ZZZ")
        # Interleaved in time, deliberately out of case_id order.
        harness.snapshot_repository.add(
            second_case, snapshot(content_hash="z1", captured_at=_T0), baseline(),
            valuation_evidence=frozen(PRIORS, CURRENT))
        harness.snapshot_repository.add(
            first_case, snapshot(content_hash="a1", captured_at=_T0 + timedelta(days=1)), baseline(),
            valuation_evidence=frozen(PRIORS, CURRENT))
        harness.snapshot_repository.add(
            second_case, snapshot(content_hash="z2", captured_at=_T0 + timedelta(days=2)), baseline(),
            valuation_evidence=frozen(PRIORS, CURRENT))
        history = harness.history_service.build_analytical_history()
        expected = [entry.snapshot.captured_at for entry in history.entries]
        view = AnalyticalHistoryView.from_domain(history)
        assert [entry.captured_at for entry in view.entries] == expected, "the join reordered Core's history"
        assert len(view.entries) == 3, "the join added or dropped a row"
        assert all(entry.valuation_evidence is not None for entry in view.entries)

    def test_the_service_reads_evidence_without_a_query_per_snapshot(self, harness):
        """One query per Case, not one per snapshot: the evidence comes off the
        same rows the history already read."""
        case_id = harness.import_holding("TCK")
        for index in range(6):
            harness.snapshot_repository.add(
                case_id, snapshot(content_hash=f"h{index}", captured_at=_T0 + timedelta(days=index)),
                baseline(), valuation_evidence=frozen(PRIORS, CURRENT))
        statements = []
        from sqlalchemy import event

        @event.listens_for(harness.engine, "before_cursor_execute")
        def record(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
            if "investment_case_snapshots" in statement:
                statements.append(statement)

        harness.history_service.build_analytical_history()
        event.remove(harness.engine, "before_cursor_execute", record)
        assert len(statements) <= 2, f"N+1 evidence reads: {len(statements)} queries for 6 snapshots"
