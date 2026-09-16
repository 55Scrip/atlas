"""Coverage counts the record honestly, or it is worse than nothing.

The failure mode this guards against is flattery: a thin record described in
a way that sounds substantial. Ten snapshots of one unchanged state are not
ten observations; three snapshots from one afternoon do not span three days;
a snapshot written before Atlas froze evidence is not evidence. Each of those
is a separate primitive here, and each has a test that fails if they are
collapsed.

The readiness answers are structural, never statistical: `available` means
the comparison can be assembled from what is stored, and no test here asserts
that any number of observations is enough.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from tests.unit.alpha.investment_case_history.test_service import harness  # noqa: F401
from atlas.alpha.investment_case_history.evidence_coverage import (
    Availability,
    SnapshotRecord,
    build_coverage,
)

_T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
METHOD = "fiscal_epoch_v3+issuer_common_equity_market_cap_v1"


def evidence(*, priors: int = 3, support: str = "insufficient_input", fingerprint: str | None = None,
             low_edge: bool = False, high_edge: bool = False, with_range_edge: bool = True,
             methodology: str = METHOD, schema: str = "valuation_evidence_snapshot_v1") -> dict:
    payload = {
        "schema_version": schema,
        "valuation_methodology": methodology,
        "valuation_support_status": support,
        "prior_epochs": [{"fiscal_period": f"20{20 + i}-12-31"} for i in range(priors)],
        "fingerprint": fingerprint if fingerprint is not None else f"fp-{priors}-{support}-{low_edge}-{high_edge}",
    }
    if with_range_edge:
        payload["metadata"] = {"range_edge": {
            "single_low_edge_dependency": low_edge, "single_high_edge_dependency": high_edge}}
    return payload


def record(*, case_id: str = "c1", ticker: str | None = "TCK", day: int = 0, hour: int = 0,
           status: str = "fairly_valued", methodology: str | None = METHOD,
           frozen: dict | None = None, posture: str | None = "strengths_only") -> SnapshotRecord:
    return SnapshotRecord(
        case_id=case_id, ticker=ticker,
        captured_at=_T0 + timedelta(days=day, hours=hour),
        valuation_status=status, recommendation_state=posture,
        valuation_methodology=methodology, evidence=frozen,
    )


def coverage(records, *, visible: int | None = None):
    return build_coverage(tuple(records), visible_case_count=visible if visible is not None else 1,
                          generated_at=_T0)


def question(result, key):
    return next(q for q in result.readiness if q.key == key)


# -- what counts as evidence -------------------------------------------------


class TestEvidenceBearing:
    def test_no_history_at_all_is_empty_not_an_error(self):
        result = coverage([], visible=3)
        assert result.total_live_snapshot_count == 0
        assert result.cases_with_frozen_evidence == 0
        assert result.evidence_span_days == 0
        assert question(result, "snapshot_inspection").availability is Availability.NOT_YET_OBSERVED

    def test_a_legacy_snapshot_counts_toward_the_record_and_nothing_else(self):
        """This is the whole point of the distinction: legacy rows are real
        history and are not evidence."""
        result = coverage([record(day=0), record(day=1)])
        assert result.total_live_snapshot_count == 2
        assert result.legacy_snapshot_count == 2
        assert result.evidence_snapshot_count == 0
        assert result.distinct_evidence_state_count == 0
        assert result.cases_with_frozen_evidence == 0
        assert result.cases[0].legacy_snapshot_count == 2

    def test_a_frozen_payload_is_what_makes_a_snapshot_evidence_bearing(self):
        result = coverage([record(day=0), record(day=1, frozen=evidence())])
        assert result.evidence_snapshot_count == 1
        assert result.legacy_snapshot_count == 1
        assert result.cases_with_frozen_evidence == 1

    def test_a_withheld_valuation_with_no_priors_is_still_evidence_bearing(self):
        """A recorded decision not to value is a recorded state; only an
        absent payload is an absence."""
        result = coverage([record(frozen=evidence(priors=0, with_range_edge=False))])
        assert result.evidence_snapshot_count == 1
        assert result.cases[0].range_edge_observation_count == 0


# -- the three primitives that must never merge ------------------------------


class TestPrimitivesStaySeparate:
    def test_ten_identical_snapshots_are_one_evidence_state(self):
        frozen = evidence(fingerprint="same")
        result = coverage([record(day=0, hour=index, frozen=frozen) for index in range(10)])
        case = result.cases[0]
        assert case.evidence_snapshot_count == 10
        assert case.distinct_evidence_state_count == 1
        assert case.distinct_evidence_day_count == 1
        assert result.distinct_evidence_state_count == 1

    def test_one_state_across_three_days_keeps_all_three_numbers_apart(self):
        frozen = evidence(fingerprint="same")
        result = coverage([record(day=index, frozen=frozen) for index in range(3)])
        case = result.cases[0]
        assert (case.evidence_snapshot_count, case.distinct_evidence_state_count,
                case.distinct_evidence_day_count) == (3, 1, 3)

    def test_three_states_on_one_day_keep_all_three_numbers_apart(self):
        result = coverage([record(day=0, hour=index, frozen=evidence(fingerprint=f"s{index}"))
                           for index in range(3)])
        case = result.cases[0]
        assert (case.evidence_snapshot_count, case.distinct_evidence_state_count,
                case.distinct_evidence_day_count) == (3, 3, 1)

    def test_a_single_evidence_snapshot_spans_zero_days_which_is_not_missing(self):
        result = coverage([record(frozen=evidence())])
        assert result.cases[0].evidence_span_days == 0
        assert result.cases[0].first_evidence_at is not None

    def test_a_real_span_is_measured_in_days(self):
        result = coverage([record(day=0, frozen=evidence(fingerprint="a")),
                           record(day=30, frozen=evidence(fingerprint="b"))])
        assert result.evidence_span_days == 30
        assert result.cases[0].evidence_span_days == 30


# -- methodology and schema --------------------------------------------------


class TestMethodology:
    def test_two_methodologies_are_never_pooled(self):
        records = [record(day=0, methodology="fiscal_epoch_v3", frozen=evidence(fingerprint="a")),
                   record(day=1, methodology="fiscal_epoch_v3", frozen=evidence(fingerprint="b")),
                   record(day=2, methodology="fiscal_epoch_v4", frozen=evidence(fingerprint="c")),
                   record(day=3, methodology="fiscal_epoch_v4", frozen=evidence(fingerprint="d"))]
        result = coverage(records)
        assert result.evidence_snapshot_count == 4
        counts = {group.valuation_methodology: group.snapshot_count for group in result.methodology_groups}
        assert counts == {"fiscal_epoch_v3": 2, "fiscal_epoch_v4": 2}

    def test_the_evidence_schema_version_is_not_the_valuation_methodology(self):
        records = [record(day=0, frozen=evidence(schema="valuation_evidence_snapshot_v1", fingerprint="a")),
                   record(day=1, frozen=evidence(schema="valuation_evidence_snapshot_v2", fingerprint="b"))]
        result = coverage(records)
        assert {g.evidence_schema_version for g in result.methodology_groups} == {
            "valuation_evidence_snapshot_v1", "valuation_evidence_snapshot_v2"}
        assert {g.valuation_methodology for g in result.methodology_groups} == {METHOD}

    def test_a_methodology_group_carries_its_own_span(self):
        result = coverage([record(day=0, methodology="a", frozen=evidence(fingerprint="1")),
                           record(day=10, methodology="a", frozen=evidence(fingerprint="2"))])
        group = next(g for g in result.methodology_groups if g.valuation_methodology == "a")
        assert group.span_days == 10 and group.case_count == 1


# -- what the record can be asked about --------------------------------------


class TestRangeEdgeAndSupport:
    def test_range_edge_observations_and_dependencies_are_counted(self):
        records = [record(day=0, frozen=evidence(fingerprint="a", low_edge=True)),
                   record(day=1, frozen=evidence(fingerprint="b", low_edge=False)),
                   record(day=2, frozen=evidence(fingerprint="c", high_edge=True))]
        case = coverage(records).cases[0]
        assert case.range_edge_observation_count == 3
        assert case.single_low_edge_dependency_count == 1
        assert case.single_high_edge_dependency_count == 1

    def test_a_change_in_edge_dependence_is_a_transition_not_three_observations(self):
        records = [record(day=0, frozen=evidence(fingerprint="a", low_edge=False)),
                   record(day=1, frozen=evidence(fingerprint="b", low_edge=True)),
                   record(day=2, frozen=evidence(fingerprint="c", low_edge=False))]
        case = coverage(records).cases[0]
        assert case.range_edge_observation_count == 3
        assert case.range_edge_dependency_transition_count == 2

    def test_evidence_without_range_edge_is_not_counted_as_an_observation(self):
        case = coverage([record(frozen=evidence(with_range_edge=False))]).cases[0]
        assert case.evidence_snapshot_count == 1
        assert case.range_edge_observation_count == 0

    def test_valuation_support_states_are_counted_with_their_real_enum_values(self):
        records = [record(day=0, frozen=evidence(fingerprint="a", support="insufficient_input")),
                   record(day=1, frozen=evidence(fingerprint="b", support="not_supported")),
                   record(day=2, frozen=evidence(fingerprint="c", support="supported"))]
        case = coverage(records).cases[0]
        assert case.valuation_support_state_counts == {
            "insufficient_input": 1, "not_supported": 1, "supported": 1}


class TestStatusAndTransitions:
    def test_valuation_statuses_are_counted_across_the_whole_record(self):
        records = [record(day=0, status="fairly_valued"), record(day=1, status="fairly_valued"),
                   record(day=2, status="expensive")]
        case = coverage(records).cases[0]
        assert case.valuation_status_counts == {"fairly_valued": 2, "expensive": 1}

    def test_five_observations_with_two_changes_are_two_transitions(self):
        statuses = ["fairly_valued", "fairly_valued", "expensive", "expensive", "fairly_valued"]
        records = [record(day=index, status=status) for index, status in enumerate(statuses)]
        case = coverage(records).cases[0]
        assert case.total_snapshot_count == 5
        assert case.valuation_status_transition_count == 2

    def test_an_unchanging_status_is_zero_transitions_not_missing_data(self):
        case = coverage([record(day=index, status="expensive") for index in range(4)]).cases[0]
        assert case.valuation_status_transition_count == 0

    def test_transitions_follow_the_recorded_order_not_the_input_order(self):
        records = [record(day=2, status="expensive"), record(day=0, status="fairly_valued"),
                   record(day=1, status="fairly_valued")]
        assert coverage(records).cases[0].valuation_status_transition_count == 1

    def test_recommendation_states_are_counted_where_recorded(self):
        records = [record(day=0, posture="strengths_only"), record(day=1, posture="risks_only")]
        assert coverage(records).cases[0].recommendation_state_counts == {
            "strengths_only": 1, "risks_only": 1}


# -- readiness, question by question -----------------------------------------


class TestReadiness:
    def test_there_is_no_single_readiness_score(self):
        result = coverage([record(frozen=evidence())])
        assert not hasattr(result, "readiness_score")
        assert len({q.key for q in result.readiness}) == len(result.readiness) >= 6

    def test_one_evidence_snapshot_answers_the_inspection_question_only(self):
        result = coverage([record(frozen=evidence())])
        assert question(result, "snapshot_inspection").availability is Availability.AVAILABLE
        assert question(result, "evidence_change").availability is Availability.NOT_YET_OBSERVED

    def test_two_distinct_states_make_the_evidence_change_question_answerable(self):
        result = coverage([record(day=0, frozen=evidence(fingerprint="a")),
                           record(day=1, frozen=evidence(fingerprint="b"))])
        assert question(result, "evidence_change").availability is Availability.AVAILABLE

    def test_ten_identical_states_do_not_make_it_answerable(self):
        """The flattery test: volume is not change."""
        frozen = evidence(fingerprint="same")
        result = coverage([record(day=index, frozen=frozen) for index in range(10)])
        assert result.evidence_snapshot_count == 10
        assert question(result, "evidence_change").availability is Availability.NOT_YET_OBSERVED

    def test_a_valuation_transition_is_answerable_from_legacy_history_alone(self):
        """Valuation status is frozen on every snapshot, so this question does
        not wait on the evidence contract."""
        result = coverage([record(day=0, status="fairly_valued"), record(day=1, status="expensive")])
        assert result.evidence_snapshot_count == 0
        assert question(result, "valuation_transition").availability is Availability.AVAILABLE

    def test_an_unchanged_classification_is_not_yet_observed_rather_than_missing(self):
        result = coverage([record(day=index, status="expensive") for index in range(3)])
        assert question(result, "valuation_transition").availability is Availability.NOT_YET_OBSERVED

    def test_the_reduce_question_needs_two_evidence_states_carrying_range_edges(self):
        thin = coverage([record(day=0, frozen=evidence(fingerprint="a"))])
        assert question(thin, "reduce_gate_longitudinal").availability is Availability.NOT_YET_OBSERVED
        rich = coverage([record(day=0, frozen=evidence(fingerprint="a", low_edge=True)),
                         record(day=1, frozen=evidence(fingerprint="b", low_edge=False))])
        assert question(rich, "reduce_gate_longitudinal").availability is Availability.AVAILABLE

    def test_structural_availability_never_claims_statistical_sufficiency(self):
        rich = coverage([record(day=0, frozen=evidence(fingerprint="a", low_edge=True)),
                         record(day=1, frozen=evidence(fingerprint="b", low_edge=False))])
        detail = question(rich, "reduce_gate_longitudinal").detail
        assert "Structural availability only" in detail
        for forbidden in ("robust", "validated", "significant", "confiden", "sufficient sample"):
            assert forbidden not in detail.lower()

    def test_the_outcome_question_is_missing_data_not_merely_unobserved(self):
        """No amount of waiting produces realised returns: the data class does
        not exist, and the answer must say so rather than imply patience."""
        rich = coverage([record(day=index, frozen=evidence(fingerprint=f"s{index}", low_edge=True))
                         for index in range(50)])
        outcome = question(rich, "outcome_backtest")
        assert outcome.availability is Availability.MISSING_REQUIRED_DATA
        assert "not a question of accumulating more" in outcome.detail

    def test_no_readiness_answer_mentions_a_snapshot_count_threshold(self):
        result = coverage([record(day=index, frozen=evidence(fingerprint=f"s{index}")) for index in range(5)])
        import re

        for q in result.readiness:
            assert not re.search(r"\b(at least|minimum of)\s+(5|10|20|30|50|100)\b", q.requirement, re.I)


# -- determinism and shape ---------------------------------------------------


class TestShape:
    def test_coverage_is_pure(self):
        records = [record(day=index, frozen=evidence(fingerprint=f"s{index}")) for index in range(4)]
        assert coverage(records) == coverage(records)

    def test_cases_are_reported_per_case_and_aggregated_consistently(self):
        records = [record(case_id="c1", ticker="AAA", day=0, frozen=evidence(fingerprint="a")),
                   record(case_id="c2", ticker="BBB", day=1),
                   record(case_id="c2", ticker="BBB", day=2, frozen=evidence(fingerprint="b"))]
        result = coverage(records, visible=2)
        assert result.cases_with_any_history == 2
        assert result.cases_with_frozen_evidence == 2
        assert result.total_live_snapshot_count == 3
        assert sum(c.total_snapshot_count for c in result.cases) == 3
        assert sum(c.evidence_snapshot_count for c in result.cases) == result.evidence_snapshot_count

    def test_a_case_with_only_legacy_history_is_counted_as_having_none(self):
        result = coverage([record(case_id="c1", ticker="AAA", day=0),
                           record(case_id="c2", ticker="BBB", day=0, frozen=evidence())], visible=2)
        assert result.cases_with_frozen_evidence == 1
        assert result.cases_without_frozen_evidence == 1

    def test_a_fingerprint_is_derived_when_an_older_payload_lacks_one(self):
        first = {k: v for k, v in evidence(priors=3).items() if k != "fingerprint"}
        second = {k: v for k, v in evidence(priors=5).items() if k != "fingerprint"}
        result = coverage([record(day=0, frozen=first), record(day=1, frozen=second)])
        assert result.distinct_evidence_state_count == 2


# -- through the REAL service, over real stores ------------------------------


class TestThroughTheService:
    """The pure tests above never touch the database. These do, so a query
    that forgot retraction, or a scope that leaked, is caught here."""

    def test_a_retracted_snapshot_is_not_part_of_the_record(self, harness):
        from atlas.alpha.investment_case_change.table import investment_case_snapshot_table
        from tests.unit.alpha.investment_case_history.test_pagination import write

        case_id = harness.import_holding("AAA")
        for index in range(3):
            write(harness, case_id, index=index)
        full = harness.history_service.build_evidence_coverage()
        assert full.total_live_snapshot_count == 3

        with harness.engine.begin() as connection:
            connection.execute(investment_case_snapshot_table.update()
                               .where(investment_case_snapshot_table.c.content_hash == f"h{case_id}:1")
                               .values(retracted_by="correction-1"))
        after = harness.history_service.build_evidence_coverage()
        assert after.total_live_snapshot_count == 2, "a retracted snapshot was counted"
        assert after.cases[0].total_snapshot_count == 2

    def test_a_case_outside_scope_is_not_part_of_the_record(self, harness):
        from tests.unit.alpha.investment_case_history.test_pagination import write

        visible = harness.import_holding("AAA")
        for index in range(2):
            write(harness, visible, index=index)
            write(harness, "case-not-in-portfolio-or-watchlist", index=index)
        result = harness.history_service.build_evidence_coverage()
        assert result.total_live_snapshot_count == 2, "an out-of-scope snapshot was counted"
        assert {case.case_id for case in result.cases} == {visible}
        assert result.visible_case_count == 1

    def test_a_case_leaving_scope_leaves_the_record(self, harness):
        from tests.unit.alpha.investment_case_history.test_pagination import write

        held = harness.import_holding("AAA")
        watched = harness.add_to_watchlist("BBB")
        write(harness, held, index=0)
        write(harness, watched, index=1)
        assert harness.history_service.build_evidence_coverage().total_live_snapshot_count == 2
        harness.watchlist_store.remove("BBB", removed_at=_T0 + timedelta(days=30))
        after = harness.history_service.build_evidence_coverage()
        assert after.total_live_snapshot_count == 1
        assert after.visible_case_count == 1

    def test_coverage_costs_one_snapshot_query(self, harness):
        from sqlalchemy import event

        from tests.unit.alpha.investment_case_history.test_pagination import write

        cases = [harness.import_holding("AAA")] + [harness.add_to_watchlist(f"W{i}") for i in range(4)]
        for case_id in cases:
            for index in range(5):
                write(harness, case_id, index=index)
        statements = []

        @event.listens_for(harness.engine, "before_cursor_execute")
        def record_statement(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
            if "investment_case_snapshots" in statement:
                statements.append(statement)

        harness.history_service.build_evidence_coverage()
        event.remove(harness.engine, "before_cursor_execute", record_statement)
        assert len(statements) == 1, f"coverage took {len(statements)} snapshot queries"


# -- the firewall ------------------------------------------------------------


#: Every surface that turns evidence into something the investor acts on.
#: A report about how much history exists must never become an input to the
#: next decision -- that is how observability quietly becomes policy.
DECISION_ROOTS = (
    "atlas/analysis_engine", "atlas/decision_engine", "atlas/alpha/portfolio_fit",
    "atlas/alpha/investment_decision", "atlas/alpha/decision_support.py",
    "atlas/alpha/decision_memory", "atlas/alpha/portfolio_intelligence",
    "atlas/alpha/investment_case",
)
COVERAGE_MODULE = "atlas.alpha.investment_case_history.evidence_coverage"


class TestImportFirewall:
    @staticmethod
    def _python_files(root: str):
        from pathlib import Path
        target = Path(__file__).resolve().parents[4] / root
        return [target] if target.is_file() else sorted(target.rglob("*.py"))

    def test_no_decision_bearing_module_imports_the_coverage_model(self):
        import ast
        from pathlib import Path

        repository_root = Path(__file__).resolve().parents[4]
        offenders = []
        for root in DECISION_ROOTS:
            for path in self._python_files(root):
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                for node in ast.walk(tree):
                    module = None
                    if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                        module = node.module
                    elif isinstance(node, ast.Import):
                        module = next((a.name for a in node.names if a.name.startswith(COVERAGE_MODULE)), None)
                    if module is not None and module.startswith(COVERAGE_MODULE):
                        offenders.append(str(path.relative_to(repository_root)))
        assert offenders == []

    def test_no_decision_bearing_module_names_the_coverage_types(self):
        from pathlib import Path

        repository_root = Path(__file__).resolve().parents[4]
        offenders = [
            str(path.relative_to(repository_root))
            for root in DECISION_ROOTS
            for path in self._python_files(root)
            if "HistoricalEvidenceCoverage" in path.read_text(encoding="utf-8")
            or "CaseEvidenceCoverage" in path.read_text(encoding="utf-8")
        ]
        assert offenders == []

    def test_the_coverage_model_reads_nothing_live(self):
        """It counts snapshots handed to it. No repository, no engine, no
        session -- so it cannot accidentally consult the current Case."""
        import ast
        from pathlib import Path

        source = (Path(__file__).resolve().parents[4]
                  / "atlas/alpha/investment_case_history/evidence_coverage.py").read_text(encoding="utf-8")
        imported = {node.module for node in ast.walk(ast.parse(source))
                    if isinstance(node, ast.ImportFrom) and node.module}
        assert not any(name.startswith("atlas.") for name in imported), imported
        for forbidden in ("sqlalchemy", "Engine", "repository", "get_history"):
            assert forbidden not in source
