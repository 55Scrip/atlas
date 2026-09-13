"""Decision Layer methodology re-baseline (`atlas.analysis_engine.methodology`).

Financial Risk v2 and the fiscal-epoch valuation history reached the Daily
Brief as "GOOG: Recommendation changed from hold to reduce" -- the Decision
Layer diffed each Case's fresh result against a row computed under the old
method. These tests pin that a persisted result carries the methodology that
produced it, that a result from another methodology is never a baseline for
"what changed", and that the current state still moves to the new result.
"""
from __future__ import annotations

import inspect
import json
from datetime import datetime, timezone

import pytest

from atlas.alpha.decision_explanation import repository as explanation_repository
from atlas.alpha.decision_explanation import service as explanation_service
from atlas.alpha.decision_memory import service as memory_service
from atlas.alpha.decision_memory.engine import DecisionSnapshotInputs, build_snapshot, detect_decision_change
from atlas.alpha.decision_path import repository as path_repository
from atlas.alpha.decision_path import service as path_service
from atlas.alpha.decision_path.models import FinalReachableState
from atlas.alpha.decision_readiness import repository as readiness_repository
from atlas.alpha.decision_readiness import service as readiness_service
from atlas.alpha.decision_readiness.models import DecisionReadinessStatus
from atlas.alpha.decision_reliability import repository as reliability_repository
from atlas.alpha.decision_reliability import service as reliability_service
from atlas.alpha.investment_decision import repository as decision_repository
from atlas.alpha.investment_decision import service as decision_service
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.investment_decision.table import investment_decision_result_table
from atlas.alpha.opportunity_cost import repository as opportunity_repository
from atlas.alpha.opportunity_cost import service as opportunity_service
from atlas.alpha.portfolio_decision import repository as portfolio_repository
from atlas.alpha.portfolio_decision import service as portfolio_service
from atlas.alpha.recommendation_conviction import repository as conviction_repository
from atlas.alpha.recommendation_conviction import service as conviction_service
from atlas.alpha.recommendation_conviction.models import ConvictionStrength, RecommendationStability
from atlas.analysis_engine import methodology
from atlas.analysis_engine.business_facts.growth_primitives import ROLLING_GROWTH_METHODOLOGY
from atlas.analysis_engine.risk.financial_risk import FINANCIAL_RISK_METHODOLOGY
from atlas.analysis_engine.valuation.cash_flow import FCF_YIELD_METHODOLOGY
from tests.unit.alpha.decision_memory.test_service import _Harness, _new_engine

#: Every Decision Layer store the Daily Brief diffs: (repository module,
#: service module) -- decision memory is covered separately below.
_RESULT_LAYERS = (
    (readiness_repository, readiness_service),
    (decision_repository, decision_service),
    (conviction_repository, conviction_service),
    (path_repository, path_service),
    (opportunity_repository, opportunity_service),
    (explanation_repository, explanation_service),
    (reliability_repository, reliability_service),
    (portfolio_repository, portfolio_service),
)


@pytest.fixture
def harness():
    return _Harness(_new_engine())


@pytest.fixture
def method_change(monkeypatch):
    """Simulates Atlas's next change of method after rows were written."""
    return lambda: monkeypatch.setattr(methodology, "ANALYSIS_METHODOLOGY", methodology.ANALYSIS_METHODOLOGY + ";next=v1")


class TestIdentity:
    def test_names_every_deliberate_method(self):
        for method in (FINANCIAL_RISK_METHODOLOGY, FCF_YIELD_METHODOLOGY, ROLLING_GROWTH_METHODOLOGY):
            assert method in methodology.ANALYSIS_METHODOLOGY

    def test_a_stamped_payload_is_comparable(self):
        stamped = methodology.stamp_methodology({"action": "hold"})
        assert methodology.comparable_payload(json.dumps(stamped)) == stamped

    def test_an_unstamped_legacy_payload_is_not(self):
        assert methodology.comparable_payload(json.dumps({"action": "hold"})) is None

    def test_a_payload_from_another_method_is_not(self, method_change):
        stamped = json.dumps(methodology.stamp_methodology({"action": "hold"}))
        method_change()
        assert methodology.comparable_payload(stamped) is None


class TestEveryDecisionLayerStore:
    @pytest.mark.parametrize("repository_module, service_module", _RESULT_LAYERS)
    def test_results_are_stamped_and_changes_read_only_comparable_ones(self, repository_module, service_module):
        repository = next(
            c for _, c in inspect.getmembers(repository_module, inspect.isclass) if c.__module__ == repository_module.__name__
        )
        assert "stamp_methodology(" in inspect.getsource(repository.upsert)
        assert "comparable_payload(" in inspect.getsource(repository.get_comparable)
        source = inspect.getsource(service_module)
        assert "_result_repository.get_comparable(case_id)" in source
        assert "_result_repository.get(case_id)" not in source

    def test_decision_memory_diffs_only_a_comparable_head(self):
        source = inspect.getsource(memory_service.DecisionMemoryService._record_current_snapshot)
        assert "get_latest_comparable(case_id)" in source


class TestResultStore:
    def test_a_result_from_another_method_is_no_baseline_but_still_readable(self, harness, method_change):
        case_id = harness.import_holding("NVDA")
        harness.investment_decision_service.synthesize_for_case(case_id)
        repository = harness.investment_decision_result_repository
        assert repository.get_comparable(case_id) is not None
        method_change()
        assert repository.get_comparable(case_id) is None
        assert repository.get(case_id) is not None  # the stored row itself is untouched

    def test_a_legacy_row_is_no_baseline(self, harness):
        case_id = harness.import_holding("NVDA")
        current = harness.investment_decision_service.synthesize_for_case(case_id)
        with harness.engine.begin() as connection:
            row = connection.execute(investment_decision_result_table.select()).mappings().one()
            legacy = {k: v for k, v in json.loads(row["result_json"]).items() if k != methodology.METHODOLOGY_KEY}
            connection.execute(
                investment_decision_result_table.update().values(result_json=json.dumps(legacy))
            )
        assert harness.investment_decision_result_repository.get(case_id).action is current.action
        assert harness.investment_decision_result_repository.get_comparable(case_id) is None


def _force_previous_action(harness, case_id: str, action: DecisionAction) -> None:
    """Rewrites the stored decision as if it had been computed with another
    action, keeping whatever methodology stamp it carries -- and starts a
    new request (the service memoizes its computation per request)."""
    with harness.engine.begin() as connection:
        row = connection.execute(investment_decision_result_table.select()).mappings().one()
        payload = json.loads(row["result_json"])
        payload["action"] = action.value
        connection.execute(investment_decision_result_table.update().values(result_json=json.dumps(payload)))
    harness.investment_decision_service._synthesize_for_case_cache.clear()


class TestChangeForCase:
    def test_a_real_change_under_one_method_is_still_reported(self, harness):
        case_id = harness.import_holding("NVDA")
        current = harness.investment_decision_service.synthesize_for_case(case_id)
        other = DecisionAction.BUY if current.action is not DecisionAction.BUY else DecisionAction.HOLD
        _force_previous_action(harness, case_id, other)
        change = harness.investment_decision_service.change_for_case(case_id)
        assert change is not None and change.previous_action is other and change.current_action is current.action

    def test_a_change_across_methods_is_not_reported_but_the_state_moves(self, harness, method_change):
        case_id = harness.import_holding("NVDA")
        current = harness.investment_decision_service.synthesize_for_case(case_id)
        other = DecisionAction.BUY if current.action is not DecisionAction.BUY else DecisionAction.HOLD
        _force_previous_action(harness, case_id, other)
        method_change()
        assert harness.investment_decision_service.change_for_case(case_id) is None
        stored = harness.investment_decision_result_repository.get_comparable(case_id)
        assert stored is not None and stored.action is current.action
        # ...and the next real change is diffed against the new baseline.
        _force_previous_action(harness, case_id, other)
        assert harness.investment_decision_service.change_for_case(case_id) is not None


class TestDecisionMemory:
    def _forced_change(self, harness, case_id):
        head = harness.decision_memory_repository.get_latest(case_id)
        forced = build_snapshot(
            case_id,
            DecisionSnapshotInputs(
                action=DecisionAction.BUY,
                readiness_status=DecisionReadinessStatus.READY,
                blocker_codes=(),
                conviction_strength=ConvictionStrength.STRONG,
                conviction_stability=RecommendationStability.STABLE,
                decision_path_step_count=0,
                decision_path_final_state=FinalReachableState.ALREADY_REACHED,
                primary_alternative_kind=None,
                alternative_count=0,
            ),
            recorded_at=datetime.now(timezone.utc),
        )
        change = detect_decision_change(head, forced, detected_at=forced.recorded_at)
        harness.decision_memory_repository.add(case_id, forced, change, ticker="NVDA")

    def test_a_method_change_records_a_new_baseline_not_a_change(self, harness, method_change):
        case_id = harness.import_holding("NVDA")
        harness.decision_memory_service.assess_for_case(case_id)
        method_change()
        assert harness.decision_memory_service.change_for_case(case_id) is None
        history = harness.decision_memory_repository.get_history(case_id)
        assert [entry.change.is_baseline for entry in history] == [True, True]
        assert history[0].snapshot.content_hash == history[1].snapshot.content_hash
        assert harness.decision_memory_service.assess_for_case(case_id).latest_change is None

    def test_after_the_new_baseline_a_real_change_is_reported(self, harness, method_change):
        case_id = harness.import_holding("NVDA")
        harness.decision_memory_service.assess_for_case(case_id)
        method_change()
        harness.decision_memory_service.change_for_case(case_id)
        self._forced_change(harness, case_id)
        change = harness.decision_memory_service.change_for_case(case_id)
        assert change is not None and change.recommendation_changed

    def test_an_unchanged_decision_under_one_method_appends_nothing(self, harness):
        case_id = harness.import_holding("NVDA")
        harness.decision_memory_service.assess_for_case(case_id)
        harness.decision_memory_service.assess_for_case(case_id)
        assert len(harness.decision_memory_repository.get_history(case_id)) == 1
