"""Recommendation Reasoning Forward-Context Integration.

Verified forward evidence -- guidance revisions and executed customer
commitments -- reaches the recommendation's reasoning as *context*: it
must be visible, source-grounded and honest about what it does not
establish, and it must never change the direction, the drivers, the
change triggers, the unknowns or the conviction. Real sentences come
from the persisted transcripts (see the forward_claims tests for their
provenance)."""
from __future__ import annotations

import dataclasses
import random
from datetime import datetime, timezone

import pytest

from atlas.analysis_engine.forward_context import build_forward_reasoning_context
from atlas.analysis_engine.forward_claims import detect_revisions, extract_forward_claims
from atlas.analysis_engine.reasoning import (
    ContractedVolumeContext,
    ForwardGuidanceContext,
    ForwardGuidanceSubject,
    ForwardReasoningContext,
    GuidanceRevisionKind,
    UnestablishedEconomics,
    deserialize_reasoning,
    serialize_reasoning,
)
from atlas.analysis_engine.recommendation import RecommendationDirection, RecommendationReasoning
from tests.unit.analysis_engine.forward_claims.test_commitment_links import (
    AMD_OPENAI,
    MU_SCA,
    VST_AWS_2025Q3,
    VST_NUCLEAR_2025Q4,
    VST_OPPORTUNITY,
)
from tests.unit.analysis_engine.forward_claims.test_commitment_terms import record
from tests.unit.analysis_engine.forward_claims.test_commitments import VST_CONTRACTED
from tests.unit.analysis_engine.forward_claims.test_interpretation import CRM, GOOGL, VST, statement

AT = datetime(2026, 9, 11, tzinfo=timezone.utc)
ALL_FOUR = tuple(UnestablishedEconomics)


def guidance_records(company, sentences, title="Chief Financial Officer"):
    return [statement(text, company=company, quarter=q, title=title) for q, text in sentences.items()]


def vst_records():
    return [
        *guidance_records("VST", VST),
        record(VST_AWS_2025Q3, quarter="2025Q3", index=2),
        record(VST_NUCLEAR_2025Q4 + VST_OPPORTUNITY, index=1),
        record((VST_CONTRACTED,), index=3),
    ]


def vst_context() -> ForwardReasoningContext:
    context = build_forward_reasoning_context(vst_records(), extracted_at=AT)
    assert context is not None
    return context


class TestTheVstContext:
    def test_4_guidance_is_the_two_reaffirmed_measures_qualified_as_management_defined(self):
        guidance = vst_context().guidance
        assert [(g.subject, g.revision, g.horizon_period, g.value_text, g.measure_defined_by_management) for g in guidance] == [
            (ForwardGuidanceSubject.ADJUSTED_EBITDA, GuidanceRevisionKind.REAFFIRMED, "2026", "$6.8 billion-$7.6 billion", True),
            (ForwardGuidanceSubject.FREE_CASH_FLOW, GuidanceRevisionKind.REAFFIRMED, "2026", "$3.925 billion-$4.725 billion", True),
        ]

    def test_5_17_18_contracted_volume_is_five_observations_each_stated_never_summed(self):
        volume = vst_context().contracted_volume
        assert len(volume) == 5
        assert [c.source_period for c in volume][0] == "2025Q3"
        texts = [t for c in volume for t in c.quantity_texts]
        assert "up to 1,200 megawatts of new load" in texts
        assert {"2,176 megawatts of operating capacity", "433 megawatts of upgrade capacity"} <= set(texts)
        assert not any(total in " ".join(texts) for total in ("3.8", "3,8", "2,609", "3,809"))
        assert all(isinstance(t, str) for t in texts), "quantities travel as text: there is nothing to add up"
        meta = next(c for c in volume if c.delivery_start_years)
        assert (meta.counterparty_text, meta.term_years, meta.delivery_start_years) == ("Meta", 20.0, (2026, 2027))

    def test_6_every_observation_carries_the_economics_it_does_not_establish(self):
        context = vst_context()
        assert all(c.not_established == ALL_FOUR for c in context.contracted_volume)
        assert context.unestablished_economics == ALL_FOUR

    def test_17_names_are_verbatim_and_observations_are_not_customers(self):
        context = vst_context()
        assert context.counterparty_texts == ("Amazon", "Amazon Web Services", "Meta")
        assert context.unnamed_observation_count == 1
        assert "identityResolved" in serialize_reasoning(RecommendationReasoning(forward_context=context))["forwardContext"]

    def test_19_20_no_field_can_carry_revenue_earnings_or_price(self):
        names = {f.name for cls in (ForwardReasoningContext, ForwardGuidanceContext, ContractedVolumeContext)
                 for f in dataclasses.fields(cls)}
        for forbidden in ("revenue", "earnings", "price", "margin", "polarity", "score", "confidence",
                          "materiality", "supportive", "positive", "movement", "effect"):
            assert not any(forbidden == token for name in names for token in name.split("_")), forbidden

    def test_the_3_2_gw_opportunity_never_appears(self):
        payload = str(serialize_reasoning(RecommendationReasoning(forward_context=vst_context())))
        assert "3.2" not in payload and "opportunit" not in payload


class TestOtherCompanies:
    def test_12_googl_capex_raised_twice_is_one_item_with_its_history_count(self):
        context = build_forward_reasoning_context(guidance_records("GOOGL", GOOGL), extracted_at=AT)
        (item,) = context.guidance
        assert (item.subject, item.revision, item.value_text, item.prior_value_text, item.revision_count) == (
            ForwardGuidanceSubject.CAPITAL_EXPENDITURE, GuidanceRevisionKind.RAISED,
            "$195 billion to $205 billion", "$180 billion to $190 billion", 2)
        assert item.measure_defined_by_management is False and context.contracted_volume == ()

    def test_13_crm_revenue_raised_in_its_fiscal_year(self):
        context = build_forward_reasoning_context(
            guidance_records("CRM", CRM, title="Chief Operating & Financial Officer"), extracted_at=AT)
        (item,) = context.guidance
        assert (item.subject, item.revision, item.horizon_kind) == (
            ForwardGuidanceSubject.REVENUE, GuidanceRevisionKind.RAISED, "fiscal_year")

    def test_14_amd_contracted_gpu_volume_without_any_revenue_figure(self):
        context = build_forward_reasoning_context([record(AMD_OPENAI, company="AMD", quarter="2025Q3")], extracted_at=AT)
        (item,) = context.contracted_volume
        assert (item.counterparty_text, item.quantity_texts, item.term_years, item.delivery_start_years) == (
            "OpenAI", ("6 gigawatts of Instinct GPUs",), None, (2026,))
        assert "$" not in str(serialize_reasoning(RecommendationReasoning(forward_context=context)))

    def test_15_mu_five_year_sca_establishes_no_volume_so_no_context(self):
        assert build_forward_reasoning_context([record(MU_SCA, company="MU", quarter="2026Q2", index=2)], extracted_at=AT) is None

    def test_16_no_forward_evidence_is_none_never_a_reassurance(self):
        assert build_forward_reasoning_context((), extracted_at=AT) is None
        dull = statement("Thank you, operator, and good morning everyone.", company="ACME", quarter="2026Q2")
        assert build_forward_reasoning_context([dull], extracted_at=AT) is None
        with pytest.raises(ValueError, match="empty forward context"):
            ForwardReasoningContext()


class TestDeterminismAndProvenance:
    def test_22_27_same_records_in_any_order_give_the_same_context(self):
        records = vst_records()
        first = build_forward_reasoning_context(records, extracted_at=AT)
        random.Random(9).shuffle(records)
        assert build_forward_reasoning_context(records, extracted_at=AT) == first

    def test_22_guidance_first_then_volume_in_fiscal_order(self):
        context = vst_context()
        periods = [c.source_period for c in context.contracted_volume]
        assert periods == sorted(periods)

    def test_23_every_guidance_item_leads_back_to_a_revision_and_its_transcript(self):
        records = guidance_records("VST", VST)
        claims = tuple(c for r in records for c in extract_forward_claims(r, extracted_at=AT)[0])
        revisions = {r.id: r for r in detect_revisions(claims)[0]}
        by_claim = {c.id: c for c in claims}
        for item in build_forward_reasoning_context(records, extracted_at=AT).guidance:
            revision = revisions[item.signal_id]
            assert by_claim[revision.new_claim_id].source_text in VST[item.source_period]

    def test_23_every_volume_item_leads_back_to_its_commitment_claim(self):
        for item in vst_context().contracted_volume:
            assert item.signal_id.endswith(":contracted_volume") and ":commitment:" in item.signal_id

    def test_24_26_serialization_round_trips_and_older_rows_read_as_absent(self):
        context = vst_context()
        payload = serialize_reasoning(RecommendationReasoning(forward_context=context))
        assert deserialize_reasoning(payload).forward_context == context
        assert serialize_reasoning(RecommendationReasoning())["forwardContext"] is None
        legacy = {k: v for k, v in payload.items() if k != "forwardContext"}
        assert deserialize_reasoning(legacy).forward_context is None


class TestTheGateCarriesContextWithoutReadingIt:
    """Behavioural twin of the structural firewall: the same gate inputs
    with and without forward context give identical decisions."""

    def _gates(self, forward_context):
        """The same inputs twice -- built once, because the fixture mints
        fresh observation ids on every build."""
        from tests.unit.analysis_engine.test_recommendation import (
            TestDirectionSelectorNowWired,
            _assessment,
            _insufficient_valuation_engine,
            _insufficient_valuation_support,
        )
        from atlas.analysis_engine.conviction import ConvictionLevel
        from atlas.analysis_engine.recommendation import evaluate_recommendation_gate
        from tests.unit.analysis_engine._fixtures import GENERATED_AT

        engine_input, output, business_analysis = TestDirectionSelectorNowWired()._held_weak_business_result()
        fields = dict(
            business_evaluation=output.business_evaluation, valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence, reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.HIGH), business_analysis=business_analysis,
            valuation_engine=_insufficient_valuation_engine(), valuation_support=_insufficient_valuation_support(),
            has_high_financial_or_valuation_risk=True, has_open_questions=False, generated_at=GENERATED_AT,
        )
        return (evaluate_recommendation_gate(engine_input, **fields),
                evaluate_recommendation_gate(engine_input, **fields, forward_context=forward_context))

    def test_1_2_3_7_9_10_11_direction_drivers_conviction_and_triggers_are_identical(self):
        without, with_context = self._gates(vst_context())
        a, b = without.recommendation, with_context.recommendation
        assert a.direction is b.direction is RecommendationDirection.TRIM
        assert (a.conviction_level, a.conviction_reason) == (b.conviction_level, b.conviction_reason)
        assert without.conviction == with_context.conviction
        assert dataclasses.replace(b.reasoning, forward_context=None) == a.reasoning
        assert b.reasoning.forward_context == vst_context()

    def test_8_the_context_is_in_no_polarity_bucket(self):
        reasoning = self._gates(vst_context())[1].recommendation.reasoning
        kinds = {r.kind.value for r in reasoning.primary_drivers + reasoning.counter_drivers}
        assert not any("guidance" in k or "commitment" in k or "volume" in k for k in kinds)

    def test_a_withheld_outcome_carries_the_context_too(self):
        from tests.unit.analysis_engine.test_recommendation import _assessment, _call_gate
        from atlas.analysis_engine.conviction import ConvictionLevel
        from tests.unit.analysis_engine._fixtures import run_minimal

        engine_input, output = run_minimal()
        result = _call_gate(engine_input, output, conviction=_assessment(ConvictionLevel.HIGH),
                            forward_context=vst_context())
        assert result.recommendation.reasoning.forward_context == vst_context()


class TestProviderSafety:
    def test_28_the_builder_and_forward_evidence_touch_no_provider_network_or_persistence(self):
        """Forward context is built from records the composition already
        loaded -- opening an Investment Case cannot call a provider because
        of it. Structural: nothing on the path can even import one."""
        import ast
        from pathlib import Path

        root = Path(__file__).resolve().parents[3] / "atlas" / "analysis_engine"
        files = [root / "forward_context.py", *(root / "forward_claims").glob("*.py")]
        forbidden = ("atlas.alpha", "atlas.core.infrastructure", "requests", "httpx", "urllib", "aiohttp",
                     "sqlalchemy", "sqlite3", "socket")
        for path in files:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            modules = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
            modules |= {n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
            leaked = [m for m in modules if any(m == f or m.startswith(f + ".") for f in forbidden)]
            assert leaked == [], f"{path.name}: {leaked}"
