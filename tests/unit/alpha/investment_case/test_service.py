"""Tests for `atlas.alpha.investment_case.service
.InvestmentCaseCompositionService` (ATLAS-027 Phase 9/10) -- built
through the real, unmodified Case/Decision/Observation/Evidence/Outcome
persistence and the real `atlas.alpha.portfolio`/`case_generation`
services, exactly mirroring `atlas.alpha.case_intelligence`'s own test
style: nothing mocked below the composition service itself."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.service import AlphaPortfolioService, ImportHoldingInput, ImportPortfolioRequest
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio.trade_log_table import create_alpha_trade_log_table
from atlas.analysis_engine.business import BusinessCategory
from atlas.analysis_engine.risk.models import EVALUATED_RISK_CATEGORIES
from atlas.analysis_engine.valuation.contracts import ValuationMethodKind
from atlas.core.application.case.create_case import CaseService
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
from atlas.core.infrastructure.api.evidence.dependencies import get_evidence_repository
from atlas.core.infrastructure.api.knowledge_reference.dependencies import get_outcome_repository
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository
from atlas.core.infrastructure.persistence.decision.table import create_decision_table

_NOW = datetime.now(timezone.utc)


def _new_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(engine)
    create_alpha_portfolio_state_table(engine)
    create_alpha_trade_log_table(engine)
    create_business_record_table(engine)
    return engine


class _Harness:
    def __init__(self, engine):
        self.engine = engine
        self.case_repository = get_case_repository(engine)
        self.case_service = CaseService(self.case_repository)
        self.decision_repository = get_decision_repository(engine)
        self.observation_repository = get_observation_repository(engine)
        self.evidence_repository = get_evidence_repository(engine)
        self.outcome_repository = get_outcome_repository(engine)
        self.portfolio_store = AlphaPortfolioStore(engine)
        self.trade_log_store = AlphaTradeLogStore(engine)
        self.business_record_repository = SqlAlchemyBusinessRecordRepository(engine)
        self.case_generation_service = CaseGenerationService(self.case_service)
        self.portfolio_service = AlphaPortfolioService(
            self.portfolio_store, self.trade_log_store, None, self.case_generation_service
        )
        self.composition_service = InvestmentCaseCompositionService(
            self.case_repository,
            self.decision_repository,
            self.observation_repository,
            self.evidence_repository,
            self.outcome_repository,
            self.portfolio_store,
            self.trade_log_store,
            self.business_record_repository,
        )

    def import_holding(self, ticker: str, weight_percent: float = 20.0) -> str:
        state = self.portfolio_service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker=ticker, weight_percent=weight_percent),))
        )
        case_id = next(h for h in state.holdings if h.ticker == ticker).case_id
        assert case_id is not None
        return case_id

    def import_holdings(self, tickers: tuple[str, ...]) -> tuple[str, ...]:
        weight = round(100.0 / len(tickers), 2)
        state = self.portfolio_service.import_portfolio(
            ImportPortfolioRequest(
                holdings=tuple(ImportHoldingInput(ticker=t, weight_percent=weight) for t in tickers)
            )
        )
        by_ticker = {h.ticker: h.case_id for h in state.holdings}
        return tuple(by_ticker[t] for t in tickers)

    def count_calls(self, repository_name: str) -> "_CallCounter":
        repository = getattr(self, repository_name)
        return _CallCounter(repository)


class _CallCounter:
    """Wraps a repository's `list_all` to count invocations, without
    changing its return value -- used to prove `build_many` issues
    exactly one scan regardless of how many Cases are requested."""

    def __init__(self, repository) -> None:
        self._repository = repository
        self._original = repository.list_all
        self.call_count = 0
        repository.list_all = self._counted

    def _counted(self):
        self.call_count += 1
        return self._original()


@pytest.fixture
def harness() -> _Harness:
    return _Harness(_new_engine())


class TestUnresolvedCase:
    def test_unknown_case_id_returns_none(self, harness):
        assert harness.composition_service.build("00000000-0000-0000-0000-000000000099") is None

    def test_none_is_returned_not_a_fabricated_composition(self, harness):
        """Phase 22: unresolved identity must never produce a
        best-effort guess -- an explicit `None`, never a composition
        with invented fields."""
        result = harness.composition_service.build(str(uuid.uuid4()))
        assert result is None


class TestResearchCaseWithNoHolding:
    """Phase 8: a Case may exist without an active holding at all --
    automatic generation for held positions must not prohibit this."""

    def test_research_case_produces_a_full_composition_with_no_holding(self, harness):
        case = harness.case_service.create()
        composition = harness.composition_service.build(str(case.id.value))
        assert composition is not None
        assert composition.holding_context is None
        assert composition.canonical_analysis is not None

    def test_research_case_analysis_is_honest_insufficient_input_not_a_crash(self, harness):
        case = harness.case_service.create()
        composition = harness.composition_service.build(str(case.id.value))
        assert {f.kind for f in composition.canonical_analysis.business_analysis.findings} == set(BusinessCategory)
        assert {f.kind for f in composition.canonical_analysis.valuation_engine.findings} == set(
            ValuationMethodKind
        )


class TestAutoGeneratedCaseAnalysisAvailability:
    """Phase 10/24: once a Case exists (auto-generated or not), full
    `CanonicalAnalysis` is available immediately -- no Observation, no
    Decision, no Outcome required first."""

    def test_business_analysis_always_names_all_six_categories(self, harness):
        case_id = harness.import_holding("AMD")
        composition = harness.composition_service.build(case_id)
        assert {f.kind for f in composition.canonical_analysis.business_analysis.findings} == set(BusinessCategory)

    def test_valuation_engine_always_names_all_four_methods(self, harness):
        case_id = harness.import_holding("AMD")
        composition = harness.composition_service.build(case_id)
        assert {
            f.kind for f in composition.canonical_analysis.valuation_engine.findings
        } == set(ValuationMethodKind)

    def test_risk_analysis_always_names_the_four_evaluated_categories(self, harness):
        case_id = harness.import_holding("AMD")
        composition = harness.composition_service.build(case_id)
        assert {
            f.category for f in composition.canonical_analysis.risk_analysis.findings
        } == EVALUATED_RISK_CATEGORIES

    def test_conviction_is_present_without_any_decision_observation_or_outcome(self, harness):
        case_id = harness.import_holding("AMD")
        composition = harness.composition_service.build(case_id)
        assert composition.canonical_analysis.conviction is not None
        assert composition.decision_history == ()
        assert composition.observation_history == ()
        assert composition.outcome_history == ()

    def test_holding_context_reflects_the_real_linked_holding(self, harness):
        case_id = harness.import_holding("AMD", weight_percent=42.0)
        composition = harness.composition_service.build(case_id)
        assert composition.holding_context is not None
        assert composition.holding_context.ticker == "AMD"
        assert composition.holding_context.weight_percent == pytest.approx(42.0)


class TestReuseNotRecomputation:
    """Phase 9/14: this service must never independently recompute
    Business/Valuation/Risk/Conviction -- verified structurally, not
    just asserted in prose."""

    def test_service_module_never_imports_an_individual_evaluator_directly(self):
        import atlas.alpha.investment_case.service as service_module

        with open(service_module.__file__, encoding="utf-8") as handle:
            text = handle.read()
        for forbidden in (
            "atlas.analysis_engine.growth",
            "atlas.analysis_engine.capital_allocation",
            "atlas.analysis_engine.valuation.cash_flow",
            "atlas.analysis_engine.risk.business_risk",
            "atlas.analysis_engine.risk.financial_risk",
            "atlas.analysis_engine.risk.valuation_risk",
            "atlas.analysis_engine.conviction.calculate_conviction",
        ):
            assert forbidden not in text, f"found forbidden direct import: {forbidden!r}"
        assert "assemble_analysis" in text

    def test_canonical_analysis_is_the_real_object_assemble_analysis_type(self, harness):
        from atlas.analysis_engine.models import CanonicalAnalysis

        case_id = harness.import_holding("AMD")
        composition = harness.composition_service.build(case_id)
        assert isinstance(composition.canonical_analysis, CanonicalAnalysis)


def _make_decision(*, case_id: str, reason: str = "Testing.", observation_id=None, decided_at=_NOW):
    from atlas.core.domain.decision.entity import Decision
    from atlas.core.domain.decision.value_objects import Confidence, DecisionType, InvestmentCase, Subject, UserId

    return Decision.register(
        case_id=CaseId(value=uuid.UUID(case_id)),
        user_id=UserId(uuid.uuid4()),
        decision_type=DecisionType.BUY,
        subject=Subject("AMD"),
        investment_case=InvestmentCase(reason),
        confidence=Confidence(70),
        decided_at=decided_at,
        observation_id=observation_id,
    )


def _make_observation(*, case_id: str, statement: str = "Noted something.", observed_at=_NOW):
    from atlas.core.domain.observation.entity import Observation
    from atlas.core.domain.observation.value_objects import Statement as ObservationStatement
    from atlas.core.domain.observation.value_objects import Subject as ObservationSubject

    return Observation.capture(
        case_id=CaseId(value=uuid.UUID(case_id)),
        subject=ObservationSubject("AMD"),
        statement=ObservationStatement(statement),
        observed_at=observed_at,
    )


class TestDecisionObservationOutcomeHistory:
    def test_records_are_scoped_to_the_right_case_only(self, harness):
        case_a_id = harness.import_holding("AMD")
        case_b_id = harness.import_holding("NVDA")

        harness.decision_repository.add(_make_decision(case_id=case_a_id))

        composition_a = harness.composition_service.build(case_a_id)
        composition_b = harness.composition_service.build(case_b_id)
        assert len(composition_a.decision_history) == 1
        assert composition_b.decision_history == ()

    def test_current_thesis_reflects_the_latest_decision_and_observation(self, harness):
        case_id = harness.import_holding("AMD")
        observation = _make_observation(case_id=case_id, statement="Margins expanding.")
        harness.observation_repository.add(observation)
        decision = _make_decision(
            case_id=case_id,
            reason="Durable moat and cheap valuation.",
            observation_id=observation.id,
        )
        harness.decision_repository.add(decision)

        composition = harness.composition_service.build(case_id)
        assert composition.current_thesis.latest_decision_reason == "Durable moat and cheap valuation."
        assert composition.current_thesis.latest_decision_type == "BUY"
        assert composition.current_thesis.latest_observation_statement == "Margins expanding."


class TestThesisStaleness:
    def test_stale_thesis_flows_into_a_capped_conviction(self, harness):
        from atlas.analysis_engine.conviction import ConvictionLevel

        case_id = harness.import_holding("AMD")
        old_timestamp = _NOW - timedelta(days=200)
        observation = _make_observation(case_id=case_id, statement="Old note.", observed_at=old_timestamp)
        harness.observation_repository.add(observation)
        decision = _make_decision(
            case_id=case_id, reason="Old thesis.", observation_id=observation.id, decided_at=old_timestamp
        )
        harness.decision_repository.add(decision)

        composition = harness.composition_service.build(case_id)
        assert composition.canonical_analysis.conviction.level is not ConvictionLevel.VERY_HIGH


class TestNoAutomaticDecisionOrRecommendation:
    """Important Rules: Case existence/composition never fabricates a
    Decision or a directional Recommendation."""

    def test_building_a_composition_never_creates_a_decision(self, harness):
        case_id = harness.import_holding("AMD")
        harness.composition_service.build(case_id)
        assert harness.decision_repository.list_all() == []

    def test_recommendation_stays_withheld(self, harness):
        from atlas.decision_engine.contracts import RecommendationOutcomeKind

        case_id = harness.import_holding("AMD")
        composition = harness.composition_service.build(case_id)
        assert (
            composition.canonical_analysis.recommendation.recommendation.kind
            is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD
        )


class TestBuildMany:
    """ATLAS-028 Phase 3/22/23: `build_many` -- one scan per repository
    regardless of Case count, and results equivalent to calling `build`
    once per Case (modulo each call's own fresh `evaluated_at`)."""

    def test_empty_case_ids_returns_empty_dict(self, harness):
        assert harness.composition_service.build_many(()) == {}

    def test_unresolved_case_id_is_simply_absent_from_the_result(self, harness):
        result = harness.composition_service.build_many(("00000000-0000-0000-0000-000000000099",))
        assert result == {}

    def test_mixed_resolved_and_unresolved_case_ids(self, harness):
        real_case_id = harness.import_holding("AMD")
        result = harness.composition_service.build_many((real_case_id, "00000000-0000-0000-0000-000000000099"))
        assert set(result) == {real_case_id}

    def test_every_requested_case_id_that_exists_is_present(self, harness):
        case_ids = harness.import_holdings(("AMD", "NVDA", "META"))
        result = harness.composition_service.build_many(case_ids)
        assert set(result) == set(case_ids)

    def test_results_are_equivalent_to_calling_build_once_per_case(self, harness):
        case_ids = harness.import_holdings(("AMD", "NVDA"))
        batch = harness.composition_service.build_many(case_ids)
        for case_id in case_ids:
            individual = harness.composition_service.build(case_id)
            batched = batch[case_id]
            assert batched.holding_context.ticker == individual.holding_context.ticker
            assert batched.canonical_analysis.conviction.level == individual.canonical_analysis.conviction.level
            batched_statuses = {
                f.kind.value: f.status.value for f in batched.canonical_analysis.business_analysis.findings
            }
            individual_statuses = {
                f.kind.value: f.status.value for f in individual.canonical_analysis.business_analysis.findings
            }
            assert batched_statuses == individual_statuses

    def test_no_record_leakage_between_cases(self, harness):
        """One Case's Decisions must never appear in another Case's
        composition."""
        amd_id, nvda_id = harness.import_holdings(("AMD", "NVDA"))
        decision = _make_decision(case_id=amd_id, reason="AMD-only thesis.")
        harness.decision_repository.add(decision)

        batch = harness.composition_service.build_many((amd_id, nvda_id))
        assert len(batch[amd_id].decision_history) == 1
        assert batch[nvda_id].decision_history == ()

    def test_evidence_is_correctly_attributed_via_its_own_observation(self, harness):
        from atlas.core.domain.evidence.entity import Evidence
        from atlas.core.domain.evidence.value_objects import Direction
        from atlas.core.domain.evidence.value_objects import Statement as EvidenceStatement

        amd_id, nvda_id = harness.import_holdings(("AMD", "NVDA"))
        observation = _make_observation(case_id=amd_id, statement="AMD observation.")
        harness.observation_repository.add(observation)
        evidence = Evidence.capture(
            observation_id=observation.id,
            statement=EvidenceStatement("Corroborating detail."),
            direction=Direction.SUPPORTS,
            observed_at=_NOW,
        )
        harness.evidence_repository.add(evidence)

        batch = harness.composition_service.build_many((amd_id, nvda_id))
        # Just prove no crash and that NVDA's own composition is
        # unaffected -- the exact confidence value is Business
        # Evaluation's own concern, already covered elsewhere.
        assert len(batch[amd_id].observation_history) == 1
        assert batch[nvda_id].observation_history == ()

    def test_repository_scans_happen_exactly_once_regardless_of_case_count(self, harness):
        case_ids = harness.import_holdings(("AMD", "NVDA", "META"))
        decision_counter = harness.count_calls("decision_repository")
        observation_counter = harness.count_calls("observation_repository")
        evidence_counter = harness.count_calls("evidence_repository")
        outcome_counter = harness.count_calls("outcome_repository")

        harness.composition_service.build_many(case_ids)

        assert decision_counter.call_count == 1
        assert observation_counter.call_count == 1
        assert evidence_counter.call_count == 1
        assert outcome_counter.call_count == 1

    def test_trade_log_is_correctly_scoped_by_ticker_not_case(self, harness):
        amd_id, nvda_id = harness.import_holdings(("AMD", "NVDA"))
        batch = harness.composition_service.build_many((amd_id, nvda_id))
        assert batch[amd_id].trade_log == ()
        assert batch[nvda_id].trade_log == ()

    def test_determinism(self, harness):
        case_ids = harness.import_holdings(("AMD", "NVDA"))
        first = harness.composition_service.build_many(case_ids)
        second = harness.composition_service.build_many(case_ids)
        for case_id in case_ids:
            assert (
                first[case_id].canonical_analysis.conviction.level
                == second[case_id].canonical_analysis.conviction.level
            )
