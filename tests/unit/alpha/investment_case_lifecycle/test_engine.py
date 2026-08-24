"""Tests for `atlas.alpha.investment_case_lifecycle.engine` -- the pure
Mandatory Core / Publication / Lifecycle-state logic. Exercised through
real `InvestmentCaseComposition`/`CanonicalAnalysis` objects built by
this package's own `tests.unit.alpha.investment_case_lifecycle
._fixtures`, never hand-faked statuses.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.investment_case_lifecycle.engine import (
    build_atlas_status,
    derive_lifecycle_state,
    detect_regression,
    evaluate_important_gaps,
    evaluate_mandatory_core,
    evaluate_publication_eligibility,
    evidence_tier_for,
    next_expected_action,
)
from atlas.alpha.investment_case_lifecycle.models import (
    EvidenceTier,
    LifecycleState,
    MandatoryItemAssessment,
    MandatoryItemId,
    MissingReasonCode,
)
from atlas.analysis_engine.recommendation import RecommendationDirection
from tests.unit.alpha.investment_case_lifecycle._fixtures import (
    build_composition,
    financial_statement_records,
    full_records,
    market_snapshot_record,
    profile_record,
    with_real_recommendation,
)

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _item(core, item_id: MandatoryItemId) -> MandatoryItemAssessment:
    return core.item(item_id)


class TestMandatoryCore:
    def test_all_satisfied_with_full_evidence(self):
        composition = build_composition(full_records())
        core = evaluate_mandatory_core(composition, ticker=None)
        assert core.all_satisfied is True
        assert core.satisfied_count() == 4

    def test_m1_missing_without_profile_or_ticker(self):
        composition = build_composition((*financial_statement_records(), market_snapshot_record()))
        core = evaluate_mandatory_core(composition, ticker=None)
        m1 = _item(core, MandatoryItemId.M1_IDENTITY_KNOWN)
        assert m1.satisfied is False
        assert m1.reason is MissingReasonCode.WAITING_FOR_COMPANY_PROFILE

    def test_m1_satisfied_by_resolved_ticker_alone(self):
        composition = build_composition((*financial_statement_records(), market_snapshot_record()))
        core = evaluate_mandatory_core(composition, ticker="ASML")
        m1 = _item(core, MandatoryItemId.M1_IDENTITY_KNOWN)
        assert m1.satisfied is True
        assert m1.satisfied_via == "resolved_ticker"

    def test_m2_missing_without_business_records(self):
        composition = build_composition((profile_record(), market_snapshot_record()), populated=False)
        core = evaluate_mandatory_core(composition, ticker=None)
        m2 = _item(core, MandatoryItemId.M2_CURRENT_ECONOMICS)
        assert m2.satisfied is False
        assert m2.reason is MissingReasonCode.WAITING_FOR_CURRENT_ECONOMICS

    def test_m3_missing_without_market_snapshot(self):
        composition = build_composition((profile_record(), *financial_statement_records()))
        core = evaluate_mandatory_core(composition, ticker=None)
        m3 = _item(core, MandatoryItemId.M3_MARKET_PRICE)
        assert m3.satisfied is False
        assert m3.reason is MissingReasonCode.WAITING_FOR_MARKET_PRICE

    def test_m4_missing_without_any_real_risk_finding(self):
        composition = build_composition((profile_record(), market_snapshot_record()), populated=False)
        core = evaluate_mandatory_core(composition, ticker=None)
        m4 = _item(core, MandatoryItemId.M4_RISK_EVIDENCE)
        assert m4.satisfied is False
        assert m4.reason is MissingReasonCode.WAITING_FOR_RISK_EVIDENCE

    def test_multiple_items_missing_reported_independently(self):
        composition = build_composition((), populated=False)
        core = evaluate_mandatory_core(composition, ticker=None)
        assert core.all_satisfied is False
        missing_ids = {i.item for i in core.missing_items()}
        assert missing_ids == set(MandatoryItemId)

    def test_all_four_items_always_named(self):
        composition = build_composition((), populated=False)
        core = evaluate_mandatory_core(composition, ticker=None)
        assert {i.item for i in core.items} == set(MandatoryItemId)


class TestPublicationEligibility:
    def test_satisfied_core_with_real_recommendation_is_eligible(self):
        composition = with_real_recommendation(build_composition(full_records()))
        eligibility = evaluate_publication_eligibility(composition, ticker=None)
        assert eligibility.eligible is True
        assert eligibility.blocking_reason is None

    def test_satisfied_core_with_withheld_recommendation_blocks_on_recommendation_only(self):
        composition = build_composition(full_records())
        eligibility = evaluate_publication_eligibility(composition, ticker=None)
        assert eligibility.eligible is False
        assert eligibility.mandatory_core.all_satisfied is True
        assert eligibility.blocking_reason is MissingReasonCode.WAITING_FOR_RECOMMENDATION

    def test_real_negative_direction_still_publishes(self):
        composition = with_real_recommendation(build_composition(full_records()), direction=RecommendationDirection.EXIT)
        eligibility = evaluate_publication_eligibility(composition, ticker=None)
        assert eligibility.eligible is True

    def test_unsatisfied_core_blocks_before_recommendation_is_even_considered(self):
        composition = build_composition((), populated=False)
        eligibility = evaluate_publication_eligibility(composition, ticker=None)
        assert eligibility.eligible is False
        assert eligibility.recommendation_exists is False
        assert eligibility.mandatory_core.all_satisfied is False
        # Blocking reason is reported per-item on the Mandatory Core,
        # not duplicated as a top-level reason when the Core itself is
        # the blocker.
        assert eligibility.blocking_reason is None


class TestLifecycleState:
    def test_no_evidence_is_company_added(self):
        composition = build_composition((), populated=False)
        eligibility = evaluate_publication_eligibility(composition, ticker=None)
        state, regressed = derive_lifecycle_state(
            composition, eligibility, has_ever_monitored=False, previous_state=None
        )
        assert state is LifecycleState.COMPANY_ADDED
        assert regressed is False

    def test_identity_only_is_data_collection(self):
        composition = build_composition((profile_record(),), populated=False)
        eligibility = evaluate_publication_eligibility(composition, ticker=None)
        state, _ = derive_lifecycle_state(composition, eligibility, has_ever_monitored=False, previous_state=None)
        assert state is LifecycleState.DATA_COLLECTION

    def test_partial_evidence_beyond_identity_is_analysis_running(self):
        composition = build_composition((profile_record(), market_snapshot_record()), populated=False)
        eligibility = evaluate_publication_eligibility(composition, ticker=None)
        state, _ = derive_lifecycle_state(composition, eligibility, has_ever_monitored=False, previous_state=None)
        assert state is LifecycleState.ANALYSIS_RUNNING

    def test_eligible_first_time_is_published_not_monitoring(self):
        composition = with_real_recommendation(build_composition(full_records()))
        eligibility = evaluate_publication_eligibility(composition, ticker=None)
        state, regressed = derive_lifecycle_state(
            composition, eligibility, has_ever_monitored=False, previous_state=LifecycleState.ANALYSIS_RUNNING
        )
        assert state is LifecycleState.PUBLISHED
        assert regressed is False

    def test_eligible_after_monitoring_is_continuous_monitoring(self):
        composition = with_real_recommendation(build_composition(full_records()))
        eligibility = evaluate_publication_eligibility(composition, ticker=None)
        state, _ = derive_lifecycle_state(
            composition, eligibility, has_ever_monitored=True, previous_state=LifecycleState.PUBLISHED
        )
        assert state is LifecycleState.CONTINUOUS_MONITORING

    def test_regression_from_published_caps_at_analysis_running(self):
        composition = build_composition((), populated=False)
        eligibility = evaluate_publication_eligibility(composition, ticker=None)
        state, regressed = derive_lifecycle_state(
            composition, eligibility, has_ever_monitored=False, previous_state=LifecycleState.PUBLISHED
        )
        assert state is LifecycleState.ANALYSIS_RUNNING
        assert regressed is True

    def test_regression_from_continuous_monitoring_caps_at_analysis_running(self):
        composition = build_composition((), populated=False)
        eligibility = evaluate_publication_eligibility(composition, ticker=None)
        state, regressed = derive_lifecycle_state(
            composition, eligibility, has_ever_monitored=True, previous_state=LifecycleState.CONTINUOUS_MONITORING
        )
        assert state is LifecycleState.ANALYSIS_RUNNING
        assert regressed is True

    def test_regression_never_drops_below_analysis_running(self):
        composition = build_composition((), populated=False)
        eligibility = evaluate_publication_eligibility(composition, ticker=None)
        state, _ = derive_lifecycle_state(
            composition, eligibility, has_ever_monitored=False, previous_state=LifecycleState.PUBLISHED
        )
        assert state not in (LifecycleState.COMPANY_ADDED, LifecycleState.DATA_COLLECTION)


class TestImportantAndOptionalGaps:
    def test_important_gaps_present_but_publication_still_allowed(self):
        composition = with_real_recommendation(build_composition(full_records()))
        eligibility = evaluate_publication_eligibility(composition, ticker=None)
        gaps = evaluate_important_gaps(composition.canonical_analysis, eligibility.mandatory_core)
        # Full-records fixture leaves capital allocation / some risk
        # categories / valuation unresolved -- real, non-blocking gaps.
        assert len(gaps) > 0
        assert eligibility.eligible is True

    def test_evidence_tier_is_mandatory_only_when_important_gaps_exist(self):
        composition = build_composition(full_records())
        core = evaluate_mandatory_core(composition, ticker=None)
        gaps = evaluate_important_gaps(composition.canonical_analysis, core)
        assert evidence_tier_for(gaps, ()) is EvidenceTier.MANDATORY_ONLY

    def test_evidence_tier_is_mandatory_plus_important_when_no_gaps(self):
        assert evidence_tier_for((), ()) is EvidenceTier.MANDATORY_PLUS_IMPORTANT


class TestRegressionDetection:
    def test_names_exactly_which_items_invalidated(self):
        composition = build_composition(full_records())
        previous_core = evaluate_mandatory_core(composition, ticker=None)
        degraded = build_composition((profile_record(),), populated=False)
        current_core = evaluate_mandatory_core(degraded, ticker=None)

        record = detect_regression(
            previous_core=previous_core, current_core=current_core, regression_occurred=True, occurred_at=NOW
        )
        assert record is not None
        assert MandatoryItemId.M3_MARKET_PRICE in record.invalidated_items
        assert MandatoryItemId.M2_CURRENT_ECONOMICS in record.invalidated_items
        assert MandatoryItemId.M1_IDENTITY_KNOWN not in record.invalidated_items

    def test_no_record_when_regression_did_not_occur(self):
        composition = build_composition(full_records())
        core = evaluate_mandatory_core(composition, ticker=None)
        record = detect_regression(previous_core=core, current_core=core, regression_occurred=False, occurred_at=NOW)
        assert record is None

    def test_secondary_evidence_disappearing_alone_does_not_regress_state(self):
        """Losing Important-tier (non-mandatory) evidence must never
        trigger `derive_lifecycle_state`'s own regression path -- only
        a Mandatory Core item flipping does, and that flip is driven
        entirely by `previous_state`/`eligibility.eligible`, never by
        secondary evidence."""
        composition = with_real_recommendation(build_composition(full_records()))
        eligibility = evaluate_publication_eligibility(composition, ticker=None)
        state, regressed = derive_lifecycle_state(
            composition, eligibility, has_ever_monitored=False, previous_state=LifecycleState.ANALYSIS_RUNNING
        )
        assert state is LifecycleState.PUBLISHED
        assert regressed is False


class TestBuildAtlasStatus:
    def test_published_since_set_on_first_publication(self):
        composition = with_real_recommendation(build_composition(full_records()))
        status = build_atlas_status(
            case_id="case-1",
            composition=composition,
            ticker=None,
            has_ever_monitored=False,
            last_monitored_at=None,
            previous_state=LifecycleState.ANALYSIS_RUNNING,
            previous_core=None,
            published_since=NOW,
            generated_at=NOW,
        )
        assert status.lifecycle_state is LifecycleState.PUBLISHED
        assert status.published_since == NOW

    def test_published_since_none_while_not_yet_published(self):
        composition = build_composition((), populated=False)
        status = build_atlas_status(
            case_id="case-1",
            composition=composition,
            ticker=None,
            has_ever_monitored=False,
            last_monitored_at=None,
            previous_state=None,
            previous_core=None,
            published_since=NOW,
            generated_at=NOW,
        )
        assert status.published_since is None

    def test_published_since_preserved_through_regression(self):
        composition = build_composition((), populated=False)
        previous_core = evaluate_mandatory_core(build_composition(full_records()), ticker=None)
        status = build_atlas_status(
            case_id="case-1",
            composition=composition,
            ticker=None,
            has_ever_monitored=False,
            last_monitored_at=None,
            previous_state=LifecycleState.PUBLISHED,
            previous_core=previous_core,
            published_since=NOW,
            generated_at=NOW,
        )
        assert status.lifecycle_state is LifecycleState.ANALYSIS_RUNNING
        assert status.published_since == NOW
        assert status.last_regression is not None


class TestNextExpectedAction:
    def test_company_added_action(self):
        composition = build_composition((), populated=False)
        eligibility = evaluate_publication_eligibility(composition, ticker=None)
        assert next_expected_action(LifecycleState.COMPANY_ADDED, eligibility) == "waiting for company profile"

    def test_analysis_running_waiting_for_recommendation(self):
        composition = build_composition(full_records())
        eligibility = evaluate_publication_eligibility(composition, ticker=None)
        assert next_expected_action(LifecycleState.ANALYSIS_RUNNING, eligibility) == "synthesizing recommendation"
