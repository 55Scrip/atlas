"""Cross-venue issuer linking -- the evidence rules and the real cases.

The worked example is `GOOG` / `GOOGL`, because its evidence genuinely
exists: both carry SEC CIK `0001652044` (Alphabet Inc) in records Atlas
already stored. They are two different securities -- Class C and Class A,
different voting rights -- owned by one issuer, which makes them the
ideal proof that "same issuer" and "same security" are separable.

The counter-examples are equally real: Alpha Vantage returned `VOLVF`
(Volvo AB) and `VLVOF` (**Volvo Car AB**) tied at match score 0.8000, and
the portfolio holds `SU.PA` (Schneider Electric) while the database holds
`SU` (Suncor Energy).
"""
from __future__ import annotations

import pytest

from atlas.alpha.canonical_security.issuer_link import (
    EVIDENCE_KIND_STRENGTH,
    EvidenceStrength,
    IssuerLinkEvidence,
    IssuerLinkOutcome,
    cik_agreement_evidence,
    evaluate_issuer_link,
    legal_name_evidence,
    provider_search_evidence,
)

ALPHABET_CIK = "0001652044"
BERKSHIRE_CIK = "0001067983"
TSM_CIK = "0001046179"


def _ev(kind: str, agrees: bool | None = True) -> IssuerLinkEvidence:
    return IssuerLinkEvidence(kind=kind, agrees=agrees)


class TestProvenEvidenceLinks:
    def test_goog_and_googl_are_auto_confirmed_by_shared_cik(self):
        """The one provable cross-venue pair in the live corpus."""
        assessment = evaluate_issuer_link((cik_agreement_evidence(ALPHABET_CIK, ALPHABET_CIK),))
        assert assessment.outcome is IssuerLinkOutcome.AUTO_CONFIRMED
        assert assessment.may_link is True
        assert "authoritative" in assessment.reason

    def test_the_reason_names_the_authoritative_evidence(self):
        """Every automatic link must be explainable as "because of this
        evidence", never "they look similar"."""
        assessment = evaluate_issuer_link((cik_agreement_evidence(ALPHABET_CIK, ALPHABET_CIK),))
        assert "SEC_CIK" in assessment.reason

    def test_cik_zero_padding_is_not_a_contradiction(self):
        """SEC returns the same filer as `0000320193` and `320193`
        depending on endpoint. Comparing raw strings would manufacture a
        contradiction out of formatting."""
        assessment = evaluate_issuer_link((cik_agreement_evidence("320193", "0000320193"),))
        assert assessment.outcome is IssuerLinkOutcome.AUTO_CONFIRMED

    def test_user_confirmation_links_the_issuer(self):
        assessment = evaluate_issuer_link((_ev("USER_CONFIRMATION"),))
        assert assessment.outcome is IssuerLinkOutcome.AUTO_CONFIRMED

    def test_two_independent_strong_signals_suffice(self):
        assessment = evaluate_issuer_link(
            (_ev("OFFICIAL_PROVIDER_ISSUER_ID"), _ev("ISIN_ISSUER_PREFIX"))
        )
        assert assessment.outcome is IssuerLinkOutcome.AUTO_CONFIRMED

    def test_one_strong_signal_alone_only_raises_a_question(self):
        assessment = evaluate_issuer_link((_ev("OFFICIAL_PROVIDER_ISSUER_ID"),))
        assert assessment.outcome is IssuerLinkOutcome.AMBIGUOUS
        assert assessment.needs_human is True

    def test_the_same_strong_kind_twice_is_not_two_signals(self):
        """Independence is by kind: repeating one observation is not
        corroboration."""
        assessment = evaluate_issuer_link(
            (_ev("OFFICIAL_PROVIDER_ISSUER_ID"), _ev("OFFICIAL_PROVIDER_ISSUER_ID"))
        )
        assert assessment.outcome is IssuerLinkOutcome.AMBIGUOUS


class TestContradictionOutranksEverything:
    def test_different_ciks_block_the_link(self):
        assessment = evaluate_issuer_link((cik_agreement_evidence(ALPHABET_CIK, BERKSHIRE_CIK),))
        assert assessment.outcome is IssuerLinkOutcome.CONTRADICTORY
        assert assessment.may_link is False

    def test_a_contradiction_beats_any_amount_of_agreement(self):
        assessment = evaluate_issuer_link(
            (
                cik_agreement_evidence(ALPHABET_CIK, BERKSHIRE_CIK),
                _ev("USER_CONFIRMATION"),
                _ev("LEGAL_NAME_AND_JURISDICTION"),
                _ev("COMPANY_NAME_EXACT_MATCH"),
            )
        )
        assert assessment.outcome is IssuerLinkOutcome.CONTRADICTORY

    def test_a_name_mismatch_is_never_a_contradiction(self):
        """`AB Volvo` and `Volvo AB` disagree textually and are one
        company, so a name mismatch must not be promoted."""
        evidence = legal_name_evidence("Volvo AB", "AB Volvo", same_jurisdiction=True)
        assert evidence.strength is not EvidenceStrength.CONTRADICTORY
        assert evaluate_issuer_link((evidence,)).outcome is not IssuerLinkOutcome.CONTRADICTORY


class TestWeakEvidenceNeverLinks:
    def test_provider_match_score_is_always_weak(self):
        """`VOLVF` and `VLVOF` tied at 0.8000 and are different
        companies."""
        assert provider_search_evidence(0.8).strength is EvidenceStrength.WEAK
        assessment = evaluate_issuer_link((provider_search_evidence(0.8),))
        assert assessment.outcome is IssuerLinkOutcome.INSUFFICIENT_EVIDENCE

    def test_a_perfect_provider_score_still_cannot_link(self):
        assessment = evaluate_issuer_link((provider_search_evidence(1.0),))
        assert assessment.outcome is IssuerLinkOutcome.INSUFFICIENT_EVIDENCE

    def test_piling_up_weak_evidence_changes_nothing(self):
        assessment = evaluate_issuer_link(
            (
                _ev("COMPANY_NAME_EXACT_MATCH"),
                _ev("COMPANY_NAME_SIMILARITY"),
                _ev("TICKER_SIMILARITY"),
                _ev("SECTOR_MATCH"),
                _ev("PROVIDER_MATCH_SCORE"),
            )
        )
        assert assessment.outcome is IssuerLinkOutcome.INSUFFICIENT_EVIDENCE

    def test_an_unclassified_kind_defaults_to_weak(self):
        """A new signal must be powerless until deliberately
        classified."""
        assessment = evaluate_issuer_link((_ev("SOME_NEW_HEURISTIC"),))
        assert assessment.outcome is IssuerLinkOutcome.INSUFFICIENT_EVIDENCE

    def test_no_evidence_at_all_is_no_match(self):
        assert evaluate_issuer_link(()).outcome is IssuerLinkOutcome.NO_MATCH


class TestTheRealCases:
    def test_volvo_ab_and_volvo_car_ab_cannot_link(self):
        """Alpha Vantage's actual response: same score, different
        companies, and no identifier for either."""
        assessment = evaluate_issuer_link(
            (
                provider_search_evidence(0.8),
                legal_name_evidence("Volvo AB", "Volvo Car AB", same_jurisdiction=True),
            )
        )
        assert assessment.outcome is not IssuerLinkOutcome.AUTO_CONFIRMED

    def test_volv_b_and_volvf_remain_insufficient_not_linked(self):
        """SEC has never heard of the Stockholm line, so no shared CIK
        exists. `INSUFFICIENT_EVIDENCE` is the correct answer, not a gap
        to be closed with cleverness."""
        assessment = evaluate_issuer_link(
            (cik_agreement_evidence(None, None), provider_search_evidence(0.8))
        )
        assert assessment.outcome is IssuerLinkOutcome.INSUFFICIENT_EVIDENCE
        assert assessment.may_link is False

    def test_tsmc_native_and_tsm_adr_remain_unlinked(self):
        """`TSM` has CIK 0001046179; the Taiwan native line has none."""
        assessment = evaluate_issuer_link((cik_agreement_evidence(None, TSM_CIK),))
        assert assessment.outcome is IssuerLinkOutcome.INSUFFICIENT_EVIDENCE

    def test_novo_copenhagen_and_nvo_remain_unlinked(self):
        assessment = evaluate_issuer_link(
            (
                cik_agreement_evidence(None, None),
                legal_name_evidence("Novo Nordisk A/S", "Novo Nordisk A/S", same_jurisdiction=False),
            )
        )
        assert assessment.outcome is not IssuerLinkOutcome.AUTO_CONFIRMED

    def test_schneider_and_suncor_can_never_link(self):
        """Hard invariant. Any future normalization that breaks this is
        invalid by definition."""
        assessment = evaluate_issuer_link(
            (_ev("TICKER_SIMILARITY"), legal_name_evidence("Schneider Electric SE", "Suncor Energy Inc", same_jurisdiction=False))
        )
        assert assessment.outcome is not IssuerLinkOutcome.AUTO_CONFIRMED
        assert assessment.may_link is False

    def test_same_legal_name_different_issuer_does_not_auto_link(self):
        assessment = evaluate_issuer_link(
            (legal_name_evidence("Acme Corp", "Acme Corp", same_jurisdiction=True),)
        )
        assert assessment.outcome is IssuerLinkOutcome.AMBIGUOUS
        assert assessment.may_link is False


class TestBerkshireNotationVersusShareClass:
    def test_brk_b_and_brk_dash_b_share_one_cik(self):
        """Provider notation only -- SEC writes `BRK-B` where the
        portfolio holds `BRK.B`, and both are the same filer."""
        assessment = evaluate_issuer_link((cik_agreement_evidence(BERKSHIRE_CIK, BERKSHIRE_CIK),))
        assert assessment.outcome is IssuerLinkOutcome.AUTO_CONFIRMED

    def test_a_shared_cik_does_not_make_share_classes_interchangeable(self):
        """BRK.A and BRK.B share a CIK and are different securities. The
        assessment is about the *issuer*; it carries no notion of
        substitutability, which is what keeps a shared filer from
        collapsing two share classes."""
        assessment = evaluate_issuer_link((cik_agreement_evidence(BERKSHIRE_CIK, BERKSHIRE_CIK),))
        assert assessment.outcome is IssuerLinkOutcome.AUTO_CONFIRMED
        for forbidden in ("same_security", "interchangeable", "substitutable", "share_class"):
            assert not hasattr(assessment, forbidden)


class TestDiscoveryIsNotProof:
    def test_search_evidence_is_weak_by_construction(self):
        assert EVIDENCE_KIND_STRENGTH["PROVIDER_MATCH_SCORE"] is EvidenceStrength.WEAK

    def test_search_candidates_cannot_reach_auto_confirmed_alone(self):
        assessment = evaluate_issuer_link(
            (provider_search_evidence(0.9), provider_search_evidence(0.95))
        )
        assert assessment.outcome is IssuerLinkOutcome.INSUFFICIENT_EVIDENCE

    def test_search_plus_a_real_identifier_does_confirm(self):
        """Discovery proposes, evidence disposes."""
        assessment = evaluate_issuer_link(
            (provider_search_evidence(0.8), cik_agreement_evidence(ALPHABET_CIK, ALPHABET_CIK))
        )
        assert assessment.outcome is IssuerLinkOutcome.AUTO_CONFIRMED


class TestDeterminismAndBoundaries:
    def test_evaluation_is_deterministic(self):
        evidence = (cik_agreement_evidence(ALPHABET_CIK, ALPHABET_CIK), provider_search_evidence(0.8))
        first, second = evaluate_issuer_link(evidence), evaluate_issuer_link(evidence)
        assert first.outcome is second.outcome and first.reason == second.reason

    def test_evidence_travels_with_the_outcome(self):
        evidence = (cik_agreement_evidence(ALPHABET_CIK, ALPHABET_CIK),)
        assert evaluate_issuer_link(evidence).evidence == evidence

    @pytest.mark.parametrize("outcome", list(IssuerLinkOutcome))
    def test_only_auto_confirmed_permits_a_link(self, outcome):
        from atlas.alpha.canonical_security.issuer_link import IssuerLinkAssessment

        assessment = IssuerLinkAssessment(outcome=outcome, reason="x")
        assert assessment.may_link is (outcome is IssuerLinkOutcome.AUTO_CONFIRMED)

    def test_module_imports_no_provider_adapter(self):
        from pathlib import Path

        source = Path("atlas/alpha/canonical_security/issuer_link.py").read_text()
        for forbidden in ("business_data_providers", "alpha_vantage", "sec_edgar import"):
            assert forbidden not in source.split('"""', 2)[2]
