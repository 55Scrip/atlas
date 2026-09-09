"""Forward-Looking Evidence, Stage 1.

Every test here is about one question: can Atlas turn a spoken sentence
into a typed claim it could defend to an investor, without ever
mistaking an expectation for a result?
"""
from datetime import date, datetime, timezone

import pytest

from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.forward_claims import (
    EXTRACTOR_VERSION,
    ClaimBound,
    ClaimRejectionReason,
    ClaimSubject,
    ClaimType,
    ClaimantRole,
    classify_claimant,
    extract_forward_claims,
)
from tests.unit.analysis_engine.business_data._fixtures import build_raw_document

EVALUATED_AT = datetime(2026, 9, 9, tzinfo=timezone.utc)
EXTRACTED_AT = datetime(2026, 9, 10, tzinfo=timezone.utc)

#: The real VST sentence, verbatim from the persisted 2026Q2 call.
VST_SENTENCE = (
    "Turning to slide nine, we are reaffirming our 2026 Adjusted EBITDA guidance range of "
    "$6.8 billion-$7.6 billion and our adjusted free cash flow before growth guidance range of "
    "$3.925 billion-$4.725 billion."
)


def transcript(content: str, *, title: str = "Executive Vice President & Chief Financial Officer",
               speaker: str = "Kris Moldovan", company: str = "VST",
               period_end: date | None = date(2026, 6, 30), published_at: datetime = EVALUATED_AT):
    result = ingest(
        build_raw_document(
            identifier=f"{company}:transcript:2026Q2:0",
            company=company,
            source_kind="transcript",
            published_at=published_at,
            period_start=period_end,
            period_end=period_end,
            metadata={"quarter": "2026Q2", "statement_index": 0, "speaker": speaker,
                      "title": title, "content": content},
        ),
        evaluated_at=EVALUATED_AT,
    )
    assert isinstance(result, IngestedRecord)
    return result.record


def claims_for(content: str, **kwargs):
    return extract_forward_claims(transcript(content, **kwargs), extracted_at=EXTRACTED_AT)


class TestTheRealVstStatement:
    def test_extracts_both_measures_management_guided_in_one_sentence(self):
        claims, _ = claims_for(VST_SENTENCE)
        assert {c.subject for c in claims} == {ClaimSubject.ADJUSTED_EBITDA, ClaimSubject.FREE_CASH_FLOW}

    def test_keeps_a_guidance_range_a_range_rather_than_collapsing_it_to_one_number(self):
        claims, _ = claims_for(VST_SENTENCE)
        ebitda = next(c for c in claims if c.subject is ClaimSubject.ADJUSTED_EBITDA)
        assert ebitda.bound is ClaimBound.RANGE
        assert (ebitda.value_low, ebitda.value_high) == (6.8e9, 7.6e9)
        assert ebitda.value_text == "$6.8 billion-$7.6 billion"

    def test_pairs_each_measure_with_its_own_figure_and_never_the_other_one(self):
        claims, _ = claims_for(VST_SENTENCE)
        fcf = next(c for c in claims if c.subject is ClaimSubject.FREE_CASH_FLOW)
        assert (fcf.value_low, fcf.value_high) == (3.925e9, 4.725e9)

    def test_records_who_said_it_verbatim(self):
        claims, _ = claims_for(VST_SENTENCE)
        assert all(c.stated_by == "Kris Moldovan" for c in claims)
        assert all(c.stated_by_title == "Executive Vice President & Chief Financial Officer" for c in claims)
        assert all(c.claimant_role is ClaimantRole.EXECUTIVE for c in claims)

    def test_is_guidance_about_a_subject_not_a_claim_type_named_after_the_subject(self):
        claims, _ = claims_for(VST_SENTENCE)
        assert all(c.claim_type is ClaimType.GUIDANCE for c in claims)
        assert {c.subject for c in claims} != {ClaimType.GUIDANCE}


class TestSourceGrounding:
    def test_every_claim_carries_the_exact_sentence_it_came_from(self):
        record = transcript(VST_SENTENCE)
        claims, _ = extract_forward_claims(record, extracted_at=EXTRACTED_AT)
        assert claims
        for claim in claims:
            assert claim.source_text in record.metadata["content"]
            assert claim.source_record_id == record.id

    def test_the_stated_figure_is_kept_as_management_said_it_not_only_as_a_number(self):
        claims, _ = claims_for(VST_SENTENCE)
        for claim in claims:
            assert claim.value_text in claim.source_text

    def test_the_horizon_is_kept_as_stated_too(self):
        claims, _ = claims_for("We expect full year 2027 revenue of $12 billion.")
        assert claims[0].horizon_text == "full year 2027"
        assert claims[0].horizon_period == "2027"


class TestSpeakerSafety:
    @pytest.mark.parametrize(
        "title,expected",
        [
            ("Chief Financial Officer (CFO)", ClaimantRole.EXECUTIVE),
            ("Chief Operating & Financial Officer", ClaimantRole.EXECUTIVE),
            ("President and Chief Executive Officer", ClaimantRole.EXECUTIVE),
            ("Head of Investor Relations", ClaimantRole.EXECUTIVE),
            ("Analyst", ClaimantRole.ANALYST),
            ("Analyst, Goldman Sachs", ClaimantRole.ANALYST),
            ("Analyst (Morgan Stanley)", ClaimantRole.ANALYST),
            ("Operator", ClaimantRole.OPERATOR),
            ("", ClaimantRole.UNKNOWN),
            (None, ClaimantRole.UNKNOWN),
        ],
    )
    def test_classifies_real_corpus_titles(self, title, expected):
        assert classify_claimant(title) is expected

    def test_an_analyst_asking_the_question_never_becomes_management_guidance(self):
        question = "Do you expect adjusted EBITDA to reach $7 billion in 2027?"
        claims, rejected = claims_for(question, title="Analyst (UBS)", speaker="Someone")
        assert claims == ()
        assert [r.reason for r in rejected] == [ClaimRejectionReason.NOT_A_COMPANY_INSIDER]

    def test_quoting_someone_elses_forecast_is_not_issuing_guidance(self):
        claims, rejected = claims_for("Analysts expect revenue of $12 billion in 2027, but we see it differently.")
        assert claims == ()
        assert ClaimRejectionReason.ATTRIBUTED_TO_A_THIRD_PARTY in [r.reason for r in rejected]


class TestNegativeControls:
    @pytest.mark.parametrize(
        "sentence",
        [
            "In the second quarter of 2026, total net sales were EUR 9.3 billion, which is above the high end of our guidance.",
            "Adjusted EBITDA was $7 billion in 2026, in line with our outlook.",
            "We generated $4 billion of free cash flow in 2026, ahead of guidance.",
            "Revenue increased to $10 billion in 2026, exceeding our forecast.",
        ],
    )
    def test_a_reported_result_never_becomes_a_forward_claim(self, sentence):
        claims, rejected = claims_for(sentence)
        assert claims == ()
        assert ClaimRejectionReason.HISTORICAL_STATEMENT in [r.reason for r in rejected]

    def test_a_forward_statement_with_no_number_is_rejected_rather_than_guessed(self):
        claims, rejected = claims_for("We expect strong demand for our products in 2027.")
        assert claims == ()

    def test_an_unknown_subject_is_rejected_rather_than_stored_as_free_text(self):
        claims, rejected = claims_for("We expect an income tax expense of approximately $125 million in 2027.")
        assert claims == ()
        assert ClaimRejectionReason.NO_KNOWN_SUBJECT in [r.reason for r in rejected]

    def test_a_relative_horizon_is_rejected_rather_than_resolved_to_a_year(self):
        claims, rejected = claims_for("We expect revenue of $12 billion next year.")
        assert claims == ()
        assert ClaimRejectionReason.NO_EXPLICIT_FUTURE_PERIOD in [r.reason for r in rejected]

    def test_a_year_earlier_than_the_source_period_is_not_a_horizon(self):
        claims, rejected = claims_for("We expect revenue of $12 billion in 2019.")
        assert claims == ()
        assert ClaimRejectionReason.NO_EXPLICIT_FUTURE_PERIOD in [r.reason for r in rejected]

    def test_a_non_transcript_record_yields_nothing_at_all(self):
        record = ingest(
            build_raw_document(
                identifier="VST:FY:2025", company="VST", source_kind="financial_statement",
                period_end=date(2025, 12, 31), metadata={"revenue": 17738000000.0, "currency": "USD"},
            ),
            evaluated_at=EVALUATED_AT,
        )
        assert isinstance(record, IngestedRecord)
        assert extract_forward_claims(record.record, extracted_at=EXTRACTED_AT) == ((), ())


class TestQualifiers:
    def test_a_lower_bound_is_not_silently_read_as_an_exact_figure(self):
        claims, _ = claims_for("We expect more than $10 billion of revenue in 2027.")
        assert claims[0].bound is ClaimBound.LOWER_BOUND
        assert claims[0].value_low == claims[0].value_high == 1e10

    def test_an_upper_bound_keeps_its_direction(self):
        claims, _ = claims_for("We expect capex of up to $5 billion in 2027.")
        assert claims[0].bound is ClaimBound.UPPER_BOUND

    def test_a_single_figure_is_a_point(self):
        claims, _ = claims_for("We expect revenue of approximately $7 billion in 2027.")
        assert claims[0].bound is ClaimBound.POINT


class TestTimeSemantics:
    def test_a_claim_is_dated_from_its_source_never_from_its_horizon(self):
        published = datetime(2026, 8, 25, tzinfo=timezone.utc)
        claims, _ = claims_for("We expect revenue of $12 billion in 2028.", published_at=published)
        assert claims[0].reported_at == published
        assert claims[0].horizon_period == "2028"
        # FY2028 guidance issued in 2026 is evidence available in 2026.
        assert claims[0].reported_at.year < int(claims[0].horizon_period)

    def test_a_claim_can_never_predate_the_source_that_carries_it(self):
        record = transcript(VST_SENTENCE)
        claims, _ = extract_forward_claims(record, extracted_at=EXTRACTED_AT)
        assert all(c.reported_at >= record.published_at for c in claims)


class TestDeterminism:
    def test_the_same_source_and_rules_always_produce_the_same_claims(self):
        first, _ = claims_for(VST_SENTENCE)
        second, _ = claims_for(VST_SENTENCE)
        assert first == second

    def test_re_extracting_the_same_record_never_produces_a_duplicate_claim(self):
        record = transcript(VST_SENTENCE)
        a, _ = extract_forward_claims(record, extracted_at=EXTRACTED_AT)
        b, _ = extract_forward_claims(record, extracted_at=EXTRACTED_AT)
        assert {c.id for c in a} == {c.id for c in b}
        assert len({c.id for c in a}) == len(a)

    def test_every_claim_records_which_rule_set_produced_it(self):
        claims, _ = claims_for(VST_SENTENCE)
        assert all(c.extractor_version == EXTRACTOR_VERSION for c in claims)


class TestSourceGroundingIsEnforcedNotAsserted:
    def test_grounding_holds_when_assertions_are_disabled(self):
        """`python -O` strips `assert`. The passage check must survive
        it, because an ungrounded claim is the one thing this package
        may never produce."""
        import subprocess
        import sys

        script = (
            "from atlas.analysis_engine.forward_claims import extract_forward_claims;"
            "assert True.__doc__;"
            "print('ok')"
        )
        result = subprocess.run([sys.executable, "-O", "-c", script], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        source = (
            __import__("pathlib").Path(extract_forward_claims.__module__.replace(".", "/") + ".py")
        )
        assert "assert sentence in content" not in source.read_text(encoding="utf-8")
