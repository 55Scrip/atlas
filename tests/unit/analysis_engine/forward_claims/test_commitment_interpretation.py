"""Forward-Looking Evidence, Stage 5.4 -- contracted volume as state
evidence, and the company forward picture that holds state and revision
evidence side by side.

Real claims come from verbatim transcript sentences through the real
Stage 5.1-5.3 pipeline; real guidance from the Stage 4.1 sentences. The
questions: is a commitment interpreted without any prior figure, without
movement, without money, and does it sit next to annual guidance without
ever becoming part of it?
"""
from __future__ import annotations

import dataclasses
import random
from dataclasses import dataclass

import pytest

from atlas.analysis_engine.forward_claims import (
    ALL_ECONOMIC_ASPECTS,
    CompanyForwardPicture,
    ContractedVolumeInterpretation,
    EconomicAspect,
    EconomicDimension,
    EvidenceSpan,
    ForwardEconomicSignal,
    ForwardEvidenceKind,
    ForwardStateSignal,
    HorizonKind,
    StateDimension,
    StateDimensionSummary,
    StateObservation,
    VolumeWithholdReason,
    WithheldVolume,
    describe_company_forward_picture,
    describe_synthesis,
    interpret_customer_commitment,
    interpret_customer_commitments,
    synthesize_company_forward_picture,
    synthesize_forward_signals,
)
from tests.unit.analysis_engine.forward_claims.test_commitment_links import (
    AMD_OPENAI,
    MU_SCA,
    VST_AWS_2025Q3,
    VST_NUCLEAR_2025Q4,
    VST_OPPORTUNITY,
)
from tests.unit.analysis_engine.forward_claims.test_commitment_terms import extract, one, record
from tests.unit.analysis_engine.forward_claims.test_commitments import VST_CONTRACTED
from tests.unit.analysis_engine.forward_claims.test_interpretation import CRM, GOOGL, VST
from tests.unit.analysis_engine.forward_claims.test_synthesis import real

VOLUME = StateDimension.CONTRACTED_VOLUME


def vst_claims():
    claims, _ = extract(
        record(VST_AWS_2025Q3, quarter="2025Q3", index=2),
        record(VST_NUCLEAR_2025Q4 + VST_OPPORTUNITY, index=1),
        record((VST_CONTRACTED,), index=3),
    )
    return claims


def vst_volumes():
    volumes, withheld = interpret_customer_commitments(vst_claims())
    assert withheld == ()
    return volumes


def vst_picture() -> CompanyForwardPicture:
    _, _, _, guidance = real("VST", VST)
    (picture,) = synthesize_company_forward_picture(guidance + vst_volumes())
    return picture


def meta_from_announcement() -> ContractedVolumeInterpretation:
    return next(v for v in vst_volumes() if v.claim.counterparty_text == "Meta" and v.claim.supports)


def text_of(volumes) -> str:
    return " ".join(v.explanation for v in volumes) + " " + " ".join(
        q.value_text + (q.measure_text or "") for v in volumes for q in v.quantities)


@dataclass(frozen=True)
class StandInState:
    """Any state evidence at all -- the picture must not care what made it."""

    signal_id: str
    source_period: str | None
    span: EvidenceSpan = EvidenceSpan(10, (), (), HorizonKind.UNSPECIFIED_YEAR)
    company: str = "ACME"
    state_dimension: StateDimension = VOLUME
    evidence_kind: ForwardEvidenceKind = ForwardEvidenceKind.CUSTOMER_COMMITMENT
    not_established: frozenset = ALL_ECONOMIC_ASPECTS
    explanation: str = "ACME: stand-in state."


class TestStateInterpretation:
    def test_1_a_first_observation_is_interpreted_without_any_prior(self):
        (claim,) = extract(record(AMD_OPENAI, company="AMD", quarter="2025Q3"))[0]
        v = interpret_customer_commitment(claim)
        assert isinstance(v, ContractedVolumeInterpretation) and v.claim is claim
        assert v.state_dimension is VOLUME and v.evidence_kind is ForwardEvidenceKind.CUSTOMER_COMMITMENT

    def test_2_3_state_evidence_has_no_movement_and_no_effect(self):
        v = meta_from_announcement()
        for fake in ("movement", "outlook_effect", "revision_type", "horizon_period", "dimension"):
            assert not hasattr(v, fake), fake
        assert isinstance(v, ForwardStateSignal) and not isinstance(v, ForwardEconomicSignal)

    def test_5_6_7_contracted_volume_is_not_revenue_earnings_or_cash(self):
        v = meta_from_announcement()
        assert v.state_dimension.value not in {d.value for d in EconomicDimension}
        assert not {"revenue", "earnings", "cash", "price", "value"} & {f.name for f in dataclasses.fields(v)}

    def test_8_unknown_economics_travels_with_the_fact(self):
        v = meta_from_announcement()
        assert v.not_established == ALL_ECONOMIC_ASPECTS == frozenset(EconomicAspect)
        assert v.explanation.endswith("Price, revenue, earnings and cash-flow contribution are not established.")
        with pytest.raises(ValueError, match="establishes no price"):
            dataclasses.replace(v, not_established=ALL_ECONOMIC_ASPECTS - {EconomicAspect.PRICE})

    def test_quantities_cannot_be_anything_but_the_claims_own(self):
        v = meta_from_announcement()
        with pytest.raises(ValueError, match="exactly the claim's"):
            dataclasses.replace(v, quantities=v.quantities[:1])


class TestRealControls:
    def test_9_amd_revenue_potential_never_appears(self):
        (v,) = interpret_customer_commitments(extract(record(AMD_OPENAI, company="AMD", quarter="2025Q3"))[0])[0]
        assert [(q.value_low, q.unit, q.measure_text) for q in v.quantities] == [(6, "GW", "of Instinct GPUs")]
        assert (v.span.term_years, v.span.start_years) == (None, (2026,))
        for forbidden in ("$", "billion", "100"):
            assert forbidden not in text_of([v]), forbidden

    def test_10_11_neither_the_3_2_opportunity_nor_the_3_8_total_appears(self):
        text = text_of(vst_volumes())
        assert "3.2" not in text and "3.8" not in text

    def test_12_13_14_meta_quantities_term_and_delivery(self):
        v = meta_from_announcement()
        assert [(q.value_low, q.measure_text) for q in v.quantities] == [(2176, "of operating capacity"),
                                                                        (433, "of upgrade capacity")]
        assert (v.span.term_years, v.span.start_years, v.span.end_years) == (20, (2026, 2027), ())
        assert 2031 not in v.span.start_years + v.span.end_years

    def test_15_aws_observations_stay_separate(self):
        observations = vst_picture().state(VOLUME).observations
        aws = [o for o in observations if any(q.value_low == 1200 for q in o.signal.quantities)]
        assert aws[0].source_period == "2025Q3", "fiscal order; within a period, by id"
        assert sorted((o.source_period, o.signal.claim.counterparty_text or "-") for o in aws) == [
            ("2025Q3", "-"), ("2025Q4", "Amazon"), ("2025Q4", "Amazon Web Services")]
        assert len({o.signal_id for o in aws}) == 3

    def test_16_mu_five_year_sca_establishes_no_volume(self):
        (claim,) = extract(record(MU_SCA, company="MU", quarter="2026Q2", index=2))[0]
        assert interpret_customer_commitment(claim) == WithheldVolume(claim.id, VolumeWithholdReason.NO_ESTABLISHED_VOLUME)

    @pytest.mark.parametrize("sentences, reason", [
        (("We have signed a 10-year agreement with Acme for 500 megawatts.",), VolumeWithholdReason.MEASURE_NOT_STATED),
        (("We have signed an agreement with Acme for 500 megawatts of capacity.",), VolumeWithholdReason.NO_TERM_OR_DELIVERY),
        (("We have signed a 10-year power purchase agreement with Acme.",
          "This agreement, which is for 15 years, covers 500 megawatts."), VolumeWithholdReason.TERMS_DISAGREE),
    ])
    def test_ambiguous_volume_is_withheld_with_a_reason(self, sentences, reason):
        claim = one(sentences, 0)
        result = interpret_customer_commitment(claim)
        assert isinstance(result, WithheldVolume) and result.reason is reason


class TestCompanyPicture:
    def test_17_18_revision_only_input_gives_exactly_the_stage_4_2_synthesis(self):
        for company, sentences, title in (("VST", VST, "Chief Financial Officer"), ("GOOGL", GOOGL, "Chief Financial Officer"),
                                          ("CRM", CRM, "Chief Operating & Financial Officer")):
            synthesis, _, _, guidance = real(company, sentences, title=title)
            (picture,) = synthesize_company_forward_picture(guidance)
            assert picture.annual == (synthesis,) == synthesize_forward_signals(guidance)
            assert not picture.state(VOLUME).supported
            assert picture.evidence_kinds == (ForwardEvidenceKind.GUIDANCE_REVISION,)

    def test_19_state_only_input_works(self):
        (picture,) = synthesize_company_forward_picture(interpret_customer_commitments(
            extract(record(AMD_OPENAI, company="AMD", quarter="2025Q3"))[0])[0])
        assert picture.annual == () and len(picture.state(VOLUME).observations) == 1

    def test_20_22_mixed_input_keeps_both_shapes_and_separate_horizons(self):
        picture = vst_picture()
        (annual,) = picture.annual
        assert (annual.horizon_kind, annual.horizon_period) == (HorizonKind.UNSPECIFIED_YEAR, "2026")
        assert annual.evidence_kinds == (ForwardEvidenceKind.GUIDANCE_REVISION,), "a 2026 delivery start is not 2026 guidance"
        assert {e.signal_id for d in annual.dimensions for e in d.history}.isdisjoint(
            o.signal_id for o in picture.state(VOLUME).observations)
        assert picture.evidence_kinds == (ForwardEvidenceKind.CUSTOMER_COMMITMENT, ForwardEvidenceKind.GUIDANCE_REVISION)
        assert [line for line in describe_company_forward_picture(picture)][:5] == [
            "unspecified year 2026:", *(f"  {l}" for l in describe_synthesis(annual))]

    def test_21_nothing_is_netted_into_a_score(self):
        tokens = {t for cls in (CompanyForwardPicture, StateDimensionSummary, StateObservation, EvidenceSpan)
                  for f in dataclasses.fields(cls) for t in f.name.split("_")}
        for forbidden in ("score", "net", "overall", "sentiment", "polarity", "verdict", "total", "aggregate",
                          "confidence", "materiality", "probability", "current", "latest", "conflict"):
            assert forbidden not in tokens, forbidden

    def test_23_observations_are_in_fiscal_order(self):
        periods = [o.source_period for o in vst_picture().state(VOLUME).observations]
        assert periods == sorted(periods) and periods[0] == "2025Q3"

    def test_24_shuffled_input_gives_the_same_picture(self):
        _, _, _, guidance = real("VST", VST)
        signals = list(guidance + vst_volumes())
        first = synthesize_company_forward_picture(signals)
        random.Random(5).shuffle(signals)
        assert synthesize_company_forward_picture(signals) == first

    def test_25_every_observation_walks_back_to_a_transcript_sentence(self):
        sources = set(VST_AWS_2025Q3 + VST_NUCLEAR_2025Q4 + (VST_CONTRACTED,))
        for o in vst_picture().state(VOLUME).observations:
            claim = o.signal.claim
            assert claim.source_text in sources and o.signal_id.startswith(claim.id)
            for support in claim.supports:
                assert support.link.referring_sentence in sources and support.link.antecedent_sentence in sources

    def test_26_27_the_description_states_evidence_not_conclusions(self):
        text = " ".join(describe_company_forward_picture(vst_picture())).lower()
        for forbidden in ("recommend", "buy", "sell", "trim", "conviction", "bullish", "bearish", "positive", "negative",
                          "secured", "visibility", "valuation", "accretive", "attractive", "profitable", "strong",
                          "demand", "guaranteed", "overall"):
            assert forbidden not in text, forbidden
        assert "not established by any observation -- price, revenue contribution" in text

    def test_29_any_state_signal_fits_without_change(self):
        (picture,) = synthesize_company_forward_picture([StandInState("s1", "2026Q1")])
        assert picture.company == "ACME" and picture.state(VOLUME).observations[0].signal_id == "s1"

    def test_30_different_quantities_are_two_observations_not_a_conflict(self):
        a = StandInState("a", "2026Q1", explanation="1,200 MW")
        b = StandInState("b", "2026Q1", explanation="800 MW")
        (picture,) = synthesize_company_forward_picture([a, b])
        assert [o.signal for o in picture.state(VOLUME).observations] == [a, b]

    def test_a_partially_priced_state_leaves_only_the_common_gaps(self):
        a = StandInState("a", "2026Q1", not_established=frozenset({EconomicAspect.EARNINGS_CONTRIBUTION}))
        b = StandInState("b", "2026Q2")
        (picture,) = synthesize_company_forward_picture([a, b])
        assert picture.state(VOLUME).established_by_none == frozenset({EconomicAspect.EARNINGS_CONTRIBUTION})


class TestTheSeamRefusesImpossibleSignals:
    def test_a_signal_that_is_both_revision_and_state_is_refused(self):
        @dataclass(frozen=True)
        class Both(StandInState):
            horizon_period: str = "2026"
            horizon_kind: HorizonKind = HorizonKind.UNSPECIFIED_YEAR
            dimension: EconomicDimension = EconomicDimension.REVENUE
            movement: str = "unchanged"
            outlook_effect: str = "unchanged"

        with pytest.raises(ValueError, match="both"):
            synthesize_company_forward_picture([Both("x", "2026Q1")])

    def test_a_signal_that_is_neither_is_refused(self):
        with pytest.raises(ValueError, match="neither"):
            synthesize_company_forward_picture([object()])

    def test_the_annual_synthesis_refuses_state_evidence(self):
        with pytest.raises(ValueError, match="not a revision signal"):
            synthesize_forward_signals([StandInState("s", "2026Q1")])

    def test_a_span_is_never_empty_and_never_an_annual_horizon(self):
        with pytest.raises(ValueError, match="term or at least one year"):
            EvidenceSpan(None, (), (), HorizonKind.UNSPECIFIED_YEAR)
        assert "horizon_period" not in {f.name for f in dataclasses.fields(EvidenceSpan)}
