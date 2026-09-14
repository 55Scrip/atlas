"""The fiscal_epoch_v2 -> fiscal_epoch_v3 migration is a methodology event,
never company news: results and snapshots written under v2 are no baseline
for v3's "what changed", history keeps its own identity, and a second run
under v3 appends nothing."""
from __future__ import annotations

import dataclasses
import json

import pytest

from atlas.analysis_engine import methodology
from atlas.analysis_engine.investment_case_change import compare_snapshots
from atlas.analysis_engine.valuation.cash_flow import FISCAL_EPOCH_V2, VALUATION_METHODOLOGY
from atlas.analysis_engine.valuation.issuer_basis import (
    COMMON_FCF_NUMERATOR_METHODOLOGY,
    ISSUER_MARKET_CAP_METHODOLOGY,
)
from tests.unit.alpha.decision_memory.test_service import _Harness, _new_engine
from tests.unit.analysis_engine.test_investment_case_change import _snapshot

#: The identity every Decision Layer row was stamped with before the migration.
V2_IDENTITY = ("financial_risk=debt_burden_v2;outlook=sensitivity_v2;rolling_growth=fiscal_year_windows_v2;"
               "valuation=fiscal_epoch_v2")


class TestIdentity:
    def test_the_valuation_identity_composes_epochs_denominator_and_numerator(self):
        assert VALUATION_METHODOLOGY.split("+") == ["fiscal_epoch_v3", ISSUER_MARKET_CAP_METHODOLOGY,
                                                    COMMON_FCF_NUMERATOR_METHODOLOGY]
        assert methodology.ANALYSIS_METHODOLOGY == V2_IDENTITY.replace("valuation=fiscal_epoch_v2",
                                                                       f"valuation={VALUATION_METHODOLOGY}")

    def test_a_v2_stamped_result_is_no_baseline(self):
        v2_row = json.dumps({"action": "hold", methodology.METHODOLOGY_KEY: V2_IDENTITY})
        assert methodology.comparable_payload(v2_row) is None

    def test_a_numerator_change_alone_would_change_the_identity(self, monkeypatch):
        monkeypatch.setitem(methodology._COMPONENTS, "valuation",
                            VALUATION_METHODOLOGY.replace(COMMON_FCF_NUMERATOR_METHODOLOGY, "common_attributable_fcf_v2"))
        assert ";".join(f"{k}={v}" for k, v in sorted(methodology._COMPONENTS.items())) != methodology.ANALYSIS_METHODOLOGY


class TestSnapshots:
    def test_a_v2_snapshot_is_never_compared_with_v3_on_valuation(self):
        before = dataclasses.replace(_snapshot(valuation_status="fairly_valued"), valuation_methodology=FISCAL_EPOCH_V2)
        after = dataclasses.replace(_snapshot(valuation_status="undervalued"), valuation_methodology=VALUATION_METHODOLOGY)
        assert compare_snapshots(before, after).changes == ()

    def test_two_v3_snapshots_do_compare_on_valuation(self):
        before = dataclasses.replace(_snapshot(valuation_status="fairly_valued"), valuation_methodology=VALUATION_METHODOLOGY)
        after = dataclasses.replace(_snapshot(valuation_status="undervalued"), valuation_methodology=VALUATION_METHODOLOGY)
        assert compare_snapshots(before, after).changes


class TestDecisionMemory:
    @pytest.fixture
    def harness(self):
        return _Harness(_new_engine())

    def test_the_migration_records_a_clean_baseline_and_keeps_the_v2_history(self, harness, monkeypatch):
        case_id = harness.import_holding("NVDA")
        monkeypatch.setattr(methodology, "ANALYSIS_METHODOLOGY", V2_IDENTITY)
        harness.decision_memory_service.assess_for_case(case_id)  # written under v2
        monkeypatch.undo()
        assert harness.decision_memory_service.change_for_case(case_id) is None  # no fake company change
        history = harness.decision_memory_repository.get_history(case_id)
        assert [entry.change.is_baseline for entry in history] == [True, True]  # v2 kept, v3 baseline added
        harness.decision_memory_service.assess_for_case(case_id)  # a second v3 run
        assert len(harness.decision_memory_repository.get_history(case_id)) == 2  # nothing duplicated
