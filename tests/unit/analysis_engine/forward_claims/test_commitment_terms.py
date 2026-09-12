"""Forward-Looking Evidence, Stage 5.3 -- the deterministic commitment
term reader: executed anchor + verified links -> CustomerCommitmentClaim.

Real sentences are verbatim from persisted transcripts (see the Stage 5.1
and 5.2 tests for their provenance). The success criterion is that every
automatic claim is right and every field traces to its own source span --
not that a count is reached.
"""
from __future__ import annotations

import dataclasses
import random
from datetime import date, datetime, timezone

import pytest

from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.forward_claims.commitment_links import link_commitment_sentences
from atlas.analysis_engine.forward_claims.commitment_terms import (
    TERM_READER_VERSION,
    CommitmentEvidence,
    WithheldCommitment,
    WithholdReason,
    extract_customer_commitments,
    read_commitment_evidence,
)
from atlas.analysis_engine.forward_claims.commitments import CommitmentKind, SourceLinkKind
from atlas.analysis_engine.forward_claims.contracts import ClaimBound, ClaimantRole, HorizonKind
from tests.unit.analysis_engine.business_data._fixtures import build_raw_document
from tests.unit.analysis_engine.forward_claims.test_commitment_links import (
    AMD_ANTHROPIC,
    AMD_OPENAI,
    GOOGL_TPU,
    MU_SCA,
    VST_AWS_2025Q3,
    VST_NUCLEAR_2025Q4,
    VST_OPPORTUNITY,
)
from tests.unit.analysis_engine.forward_claims.test_commitments import (
    CRM_ACQUISITION,
    SU_MOU,
    VST_ACQUISITION,
    VST_CONTRACTED,
    VST_DEBT,
    VST_EXISTENCE_ONLY,
)

PP, SUPPLY = CommitmentKind.POWER_PURCHASE, CommitmentKind.PRODUCT_SUPPLY


def evidence(sentences, anchor, *, company="VST", period="2025Q4", record="rec") -> CommitmentEvidence:
    links = tuple(l for l in link_commitment_sentences(record, sentences) if l.anchor_index == anchor)
    return CommitmentEvidence(
        company=company, source_record_id=record, source_kind=SourceKind.TRANSCRIPT, source_period=period,
        claimant_role=ClaimantRole.EXECUTIVE, stated_by="James Burke", stated_by_title="Chief Executive Officer",
        sentence_index=anchor, sentence=sentences[anchor], links=links,
    )


def read(sentences, anchor, **kwargs):
    return read_commitment_evidence(evidence(sentences, anchor, **kwargs))


def one(sentences, anchor, **kwargs):
    claims, withheld = read(sentences, anchor, **kwargs)
    assert len(claims) == 1, withheld
    return claims[0]


def quantities(claim, linked=True):
    found = list(claim.quantities) + ([q for s in claim.supports for q in s.quantities] if linked else [])
    return [(q.bound, q.value_low, q.unit, q.measure_text) for q in found]


def record(sentences, *, company="VST", quarter="2025Q4", index=1, title="President and Chief Executive Officer"):
    at = datetime(2026, 9, 9, tzinfo=timezone.utc)
    result = ingest(
        build_raw_document(
            identifier=f"{company}:transcript:{quarter}:{index}", company=company, source_kind="transcript",
            published_at=at, period_start=date(2025, 12, 31), period_end=date(2025, 12, 31),
            metadata={"quarter": quarter, "statement_index": index, "speaker": "James Burke", "title": title,
                      "content": " ".join(sentences)},
        ),
        evaluated_at=at,
    )
    assert isinstance(result, IngestedRecord)
    return result.record


def extract(*records):
    return extract_customer_commitments(records)


class TestReadingTerms:
    def test_1_5_executed_anchor_with_local_quantity_and_term(self):
        aws = next(c for c in read((VST_CONTRACTED,), 0)[0] if c.counterparty_text == "Amazon Web Services")
        assert quantities(aws) == [(ClaimBound.POINT, 1200, "MW", None)]
        assert (aws.term.years, aws.term.text) == (20, "20-year")
        assert aws.extractor_version == TERM_READER_VERSION

    def test_2_executed_anchor_with_a_linked_quantity(self):
        amazon = one(VST_NUCLEAR_2025Q4, 3)
        assert amazon.quantities == () and quantities(amazon) == [(ClaimBound.POINT, 1200, "MW", "of capacity")]
        assert amazon.supports[0].link.reference_text == "Under this agreement"

    def test_3_8_executed_anchor_with_a_linked_term_and_an_upper_bound(self):
        aws = one(VST_AWS_2025Q3, 1, period="2025Q3")
        (support,) = aws.supports
        assert (support.term.years, support.term.text) == (20, "20-year")
        assert quantities(aws) == [(ClaimBound.UPPER_BOUND, 1200, "MW", "of new load")]

    def test_4_several_quantities_stay_separate_and_are_never_summed(self):
        meta = next(c for c in read((VST_CONTRACTED,), 0)[0] if c.counterparty_text == "Meta")
        assert quantities(meta) == [(ClaimBound.POINT, 2176, "MW", "of operating capacity"),
                                    (ClaimBound.POINT, 433, "MW", "of upgrades")]
        assert not {2609, 3.8, 3800} & {q.value_low for q in meta.quantities}

    def test_6_quantity_and_delivery_window_from_one_proposition(self):
        openai = one(AMD_OPENAI, 0, company="AMD", period="2025Q3")
        assert quantities(openai) == [(ClaimBound.POINT, 6, "GW", "of Instinct GPUs")]
        assert (openai.window.start_year, openai.window.end_year, openai.window.text) == (
            2026, None, "start coming online in the second half of 2026")

    def test_7_an_unnamed_customer_stays_unnamed(self):
        assert one(VST_AWS_2025Q3, 1, period="2025Q3").counterparty_text is None
        assert one(MU_SCA, 2, company="MU", period="2026Q2").counterparty_text is None

    @pytest.mark.parametrize("sentence, bound, low, high", [
        ("We have signed a 10-year supply agreement with Acme for between 500 and 700 megawatts.", ClaimBound.RANGE, 500, 700),
        ("We have signed a 10-year supply agreement with Acme for 500 to 700 megawatts.", ClaimBound.RANGE, 500, 700),
        ("We have signed a 10-year supply agreement with Acme for at least 300 megawatts.", ClaimBound.LOWER_BOUND, 300, 300),
        ("We have signed a 10-year supply agreement with Acme for up to 2 gigawatts.", ClaimBound.UPPER_BOUND, 2, 2),
        ("We have signed a 10-year supply agreement with Acme that will cover 450 megawatts.", ClaimBound.POINT, 450, 450),
    ])
    def test_bounds_are_read_only_from_their_own_words(self, sentence, bound, low, high):
        (q,) = one((sentence,), 0).quantities
        assert (q.bound, q.value_low, q.value_high) == (bound, low, high)

    def test_approximately_stays_in_the_text_not_in_a_bound(self):
        (q,) = one(("We have signed a 10-year supply agreement with Acme for approximately 450 megawatts.",), 0).quantities
        assert (q.bound, q.value_text) == (ClaimBound.POINT, "approximately 450 megawatts")

    def test_a_year_is_a_window_only_with_start_or_end_language(self):
        signed_in = one(("We have signed a 10-year power purchase agreement with Acme in 2025.",), 0)
        assert signed_in.window is None
        by = one(("We have signed a power purchase agreement with Acme for deliveries through 2030.",), 0)
        assert (by.window.start_year, by.window.end_year) == (None, 2030)

    def test_term_and_delivery_window_are_never_derived_from_each_other(self):
        meta = one(VST_NUCLEAR_2025Q4, 9)
        terms = [s.term for s in meta.supports if s.term]
        windows = [s.window for s in meta.supports if s.window]
        assert [t.years for t in terms] == [20]
        assert [(w.start_year, w.end_year) for w in windows] == [(2026, None), (2027, None)]


class TestKind:
    def test_kind_comes_only_from_the_agreements_own_words(self):
        assert one(VST_AWS_2025Q3, 1).commitment_kind is PP
        assert one(("We have signed a 10-year supply agreement with Acme for 500 megawatts.",), 0).commitment_kind is SUPPLY

    def test_a_listed_agreement_inherits_the_kind_it_is_listed_under(self):
        assert {c.counterparty_text: c.commitment_kind for c in read((VST_CONTRACTED,), 0)[0]} == {
            "Amazon Web Services": PP, "Meta": PP}

    def test_units_and_assets_never_decide_the_kind(self):
        assert one(AMD_OPENAI, 0, company="AMD").commitment_kind is None, "6 GW does not mean power purchase"
        amazon = one(VST_NUCLEAR_2025Q4, 3)
        assert amazon.commitment_kind is None and amazon.comparison_key is None, "'contract ... at our nuclear plant'"

    def test_19_a_support_cannot_change_the_kind(self):
        s = ("We have signed a 15-year agreement with Acme.", "The agreement is a power purchase arrangement for 500 megawatts.")
        c = one(s, 0)
        assert c.commitment_kind is None and quantities(c) == [(ClaimBound.POINT, 500, "MW", None)]


class TestScopeAndNegatives:
    def test_9_29_the_3_2_gw_opportunity_never_becomes_a_claim(self):
        claims, withheld = extract(record(VST_NUCLEAR_2025Q4 + VST_OPPORTUNITY))
        assert not any("3.2" in q.value_text for c in claims for q in c.quantities)
        (refused,) = read(VST_OPPORTUNITY, 1)[1]
        assert refused.reason is WithholdReason.NOT_EXECUTED

    def test_14_30_the_3_8_gw_total_is_withheld_and_never_anyones_quantity(self):
        claims, withheld = extract(record(VST_NUCLEAR_2025Q4))
        assert any(w.reason is WithholdReason.AGGREGATE_ACROSS_CUSTOMERS and "3.8" in w.sentence for w in withheld)
        multi = read((VST_CONTRACTED,), 0)[0]
        assert [c.counterparty_text for c in multi] == ["Amazon Web Services", "Meta"]
        assert not any("3.8" in q.value_text for c in multi + claims for q in c.quantities)

    @pytest.mark.parametrize("sentences", [
        AMD_ANTHROPIC,
        (SU_MOU,),
        ("We signed a non-binding MoU with Acme for 500 megawatts.",),
        (VST_ACQUISITION,),
        (CRM_ACQUISITION,),
        (VST_DEBT,),
    ], ids=["partnership", "real-mou", "mou-with-mw", "acquisition-mw", "acquisition-usd", "debt"])
    def test_10_13_32_rejected_status_never_reaches_term_reading(self, sentences):
        claims, _ = extract(record(sentences))
        assert claims == ()

    def test_15_market_demand_is_not_a_committed_quantity(self):
        c = one(("We have signed a 20-year power purchase agreement with Acme for 500 megawatts, and we expect "
                 "2 gigawatts of demand growth.",), 0)
        assert quantities(c) == [(ClaimBound.POINT, 500, "MW", None)]
        c = one(("We have signed a 20-year power purchase agreement with Acme covering 500 megawatts while "
                 "ERCOT adds 3 gigawatts of load growth.",), 0)
        assert [q.value_low for q in c.quantities] == [500]

    def test_16_31_amd_revenue_potential_never_attaches(self):
        claims, _ = extract(record(AMD_OPENAI, company="AMD", quarter="2025Q3"))
        (openai,) = claims
        assert quantities(openai) == [(ClaimBound.POINT, 6, "GW", "of Instinct GPUs")]
        assert openai.supports == ()
        assert not any("$" in q.value_text or "billion" in q.value_text for q in openai.quantities)

    def test_17_currency_is_never_a_quantity(self):
        c = one(("We have signed a 10-year supply agreement with Acme worth $2 billion.",), 0)
        assert c.quantities == () and c.term.years == 10

    def test_18_a_support_cannot_name_the_customer(self):
        s = ("We have signed a 15-year power purchase agreement.",
             "Under this agreement, Acme Corp will take 500 megawatts of capacity.")
        c = one(s, 0)
        assert c.counterparty_text is None and quantities(c) == [(ClaimBound.POINT, 500, "MW", "of capacity")]

    def test_20_a_support_cannot_carry_status_language_into_the_claim(self):
        s = ("We have signed a 15-year power purchase agreement with Acme.", "Under this agreement, we may add 2 gigawatts.")
        c = one(s, 0)
        assert c.supports == () and c.quantities == ()

    def test_21_an_ambiguous_reference_supports_nobody(self):
        s = ("We signed a 10-year agreement with Acme.", "We also signed a 5-year agreement with Beta.",
             "The agreement covers 500 megawatts.")
        claims, _ = extract(record(s))
        assert [(c.counterparty_text, c.term.years, c.supports) for c in claims] == [("Acme", 10, ()), ("Beta", 5, ())]

    def test_an_agreement_with_no_committed_term_is_withheld_with_a_reason(self):
        claims, withheld = read((VST_EXISTENCE_ONLY,), 0)
        assert claims == () and [w.reason for w in withheld] == [WithholdReason.NO_COMMITTED_TERM]


class TestRealControls:
    def test_26_vst_aws_2025q3(self):
        c = one(VST_AWS_2025Q3, 1, period="2025Q3")
        assert (c.commitment_kind, c.counterparty_text, c.agreement_text, c.source_period) == (
            PP, None, "power purchase agreement", "2025Q3")
        assert c.execution_text == "the recently announced power purchase agreement"

    def test_27_vst_aws_2025q4(self):
        aws = next(c for c in read((VST_CONTRACTED,), 0)[0] if c.counterparty_text == "Amazon Web Services")
        assert (aws.commitment_kind, aws.agreement_text, aws.term.years, aws.window) == (PP, "20-year agreement", 20, None)

    def test_28_vst_meta_terms_quantities_and_delivery(self):
        meta = one(VST_NUCLEAR_2025Q4, 9)
        assert (meta.commitment_kind, meta.counterparty_text, meta.agreement_text) == (
            PP, "Meta", "long-term power purchase agreements")
        assert quantities(meta) == [(ClaimBound.POINT, 2176, "MW", "of operating capacity"),
                                    (ClaimBound.POINT, 433, "MW", "of upgrade capacity")]
        deliveries = [(s.component_text, s.window.start_year, s.window.text) for s in meta.supports if s.window]
        assert deliveries == [("the operating capacity at Perry", 2026, "commence in December of 2026"),
                              ("Davis-Besse", 2027, "in December 2027")]
        assert not any(s.window and s.window.start_year == 2031 for s in meta.supports), "uprate dates stay unlinked"

    def test_33_mu_sca(self):
        c = one(MU_SCA, 2, company="MU", period="2026Q2")
        assert (c.commitment_kind, c.counterparty_text, c.agreement_text, c.term.years, c.quantities) == (
            None, None, "five-year SCA", 5, ())
        assert [s.link.link_kind for s in c.supports] == [SourceLinkKind.ACRONYM_DEFINITION]

    def test_34_googl_is_withheld(self):
        assert extract(record(GOOGL_TPU, company="GOOGL", quarter="2026Q2")) == ((), ())


class TestProvenanceAndDeterminism:
    def test_22_every_field_walks_back_to_a_source_sentence(self):
        meta = one(VST_NUCLEAR_2025Q4, 9)
        assert meta.commitment_text == meta.source_text == VST_NUCLEAR_2025Q4[9]
        for text in (meta.counterparty_text, meta.agreement_text, meta.execution_text):
            assert text in meta.source_text
        for s in meta.supports:
            sentence = s.link.referring_sentence
            assert sentence in VST_NUCLEAR_2025Q4
            for text in [q.value_text for q in s.quantities] + [s.term and s.term.text, s.window and s.window.text,
                                                                s.component_text]:
                assert text is None or text in sentence

    def test_23_24_ids_and_order_do_not_depend_on_input_order(self):
        records = [record(VST_NUCLEAR_2025Q4, index=1), record(AMD_OPENAI, company="AMD", quarter="2025Q3", index=2),
                   record(MU_SCA, company="MU", quarter="2026Q2", index=2), record((VST_CONTRACTED,), index=3)]
        first = extract(*records)
        shuffled = records[:]
        random.Random(3).shuffle(shuffled)
        assert extract(*shuffled) == first == extract(*records)
        assert [c.company for c in first[0]] == ["AMD", "MU", "VST", "VST", "VST", "VST"]

    def test_25_restatements_stay_separate_observations(self):
        claims, _ = extract(record(VST_AWS_2025Q3, quarter="2025Q3", index=2), record(VST_NUCLEAR_2025Q4, index=1),
                            record((VST_CONTRACTED,), index=3))
        amazon = [c for c in claims if c.counterparty_text in (None, "Amazon", "Amazon Web Services") and c.company == "VST"
                  and any(q.value_low == 1200 for q in c.quantities + tuple(q for s in c.supports for q in s.quantities))]
        assert len({c.id for c in amazon}) == 3
        assert [c.source_period for c in amazon] == ["2025Q3", "2025Q4", "2025Q4"]

    def test_evidence_cannot_carry_another_sentences_links(self):
        e = evidence(VST_NUCLEAR_2025Q4, 9)
        with pytest.raises(ValueError, match="anchored to its own sentence"):
            dataclasses.replace(e, sentence_index=3)

    def test_an_analyst_turn_yields_nothing(self):
        assert extract(record(VST_NUCLEAR_2025Q4, title="Analyst")) == ((), ())

    def test_no_economic_or_recommendation_field_in_the_reader_types(self):
        tokens = {t for cls in (CommitmentEvidence, WithheldCommitment) for f in dataclasses.fields(cls) for t in f.name.split("_")}
        for forbidden in ("revenue", "earnings", "price", "value", "score", "confidence", "visibility", "recommendation",
                          "outlook", "movement", "polarity", "materiality"):
            assert forbidden not in tokens, forbidden

    def test_the_golden_set_reproduces_from_real_sequences(self):
        claims, _ = extract(
            record(VST_AWS_2025Q3, quarter="2025Q3", index=2), record(VST_NUCLEAR_2025Q4, index=1),
            record((VST_CONTRACTED,), index=3), record(AMD_OPENAI, company="AMD", quarter="2025Q3", index=2),
            record(MU_SCA, company="MU", quarter="2026Q2", index=2),
        )
        assert sorted((c.company, c.source_period, c.counterparty_text or "-", c.commitment_kind and c.commitment_kind.value)
                      for c in claims) == sorted([
            ("VST", "2025Q3", "-", "power_purchase"), ("VST", "2025Q4", "Amazon", None),
            ("VST", "2025Q4", "Meta", "power_purchase"), ("VST", "2025Q4", "Amazon Web Services", "power_purchase"),
            ("VST", "2025Q4", "Meta", "power_purchase"), ("AMD", "2025Q3", "OpenAI", None), ("MU", "2026Q2", "-", None),
        ])
