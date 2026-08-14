"""Tests for `atlas.analysis_engine.valuation.synthesis` (`DE-015` §16
Proof Standard) -- generic over any number of proof paths, no voting."""
from __future__ import annotations

from atlas.analysis_engine.valuation.proof import PathProof, ProofVerdict
from atlas.analysis_engine.valuation.synthesis import SynthesisOutcome, synthesize_proofs


def _proof(name: str, verdict: ProofVerdict) -> PathProof:
    return PathProof(path_name=name, verdict=verdict, evidence_summary="test")


class TestOnePath:
    def test_single_support_proof(self):
        result = synthesize_proofs((_proof("a", ProofVerdict.ESTABLISHES_SUPPORT),))
        assert result.outcome is SynthesisOutcome.SUPPORT_ESTABLISHED

    def test_single_non_support_proof(self):
        result = synthesize_proofs((_proof("a", ProofVerdict.ESTABLISHES_NON_SUPPORT),))
        assert result.outcome is SynthesisOutcome.NON_SUPPORT_ESTABLISHED

    def test_single_does_not_establish(self):
        result = synthesize_proofs((_proof("a", ProofVerdict.DOES_NOT_ESTABLISH),))
        assert result.outcome is SynthesisOutcome.NO_SUFFICIENT_PROOF


class TestTwoPaths:
    def test_both_does_not_establish(self):
        result = synthesize_proofs(
            (_proof("scenario", ProofVerdict.DOES_NOT_ESTABLISH), _proof("net_cash", ProofVerdict.DOES_NOT_ESTABLISH))
        )
        assert result.outcome is SynthesisOutcome.NO_SUFFICIENT_PROOF

    def test_one_support_one_does_not_establish(self):
        result = synthesize_proofs(
            (_proof("scenario", ProofVerdict.DOES_NOT_ESTABLISH), _proof("net_cash", ProofVerdict.ESTABLISHES_SUPPORT))
        )
        assert result.outcome is SynthesisOutcome.SUPPORT_ESTABLISHED

    def test_conflicting_support_and_non_support(self):
        result = synthesize_proofs(
            (_proof("scenario", ProofVerdict.ESTABLISHES_NON_SUPPORT), _proof("net_cash", ProofVerdict.ESTABLISHES_SUPPORT))
        )
        assert result.outcome is SynthesisOutcome.CONFLICTING_PROOFS


class TestThreeSyntheticPaths:
    def test_third_path_participates_with_no_special_casing(self):
        result = synthesize_proofs(
            (
                _proof("a", ProofVerdict.DOES_NOT_ESTABLISH),
                _proof("b", ProofVerdict.DOES_NOT_ESTABLISH),
                _proof("c", ProofVerdict.ESTABLISHES_SUPPORT),
            )
        )
        assert result.outcome is SynthesisOutcome.SUPPORT_ESTABLISHED

    def test_three_paths_conflict(self):
        result = synthesize_proofs(
            (
                _proof("a", ProofVerdict.ESTABLISHES_SUPPORT),
                _proof("b", ProofVerdict.ESTABLISHES_NON_SUPPORT),
                _proof("c", ProofVerdict.DOES_NOT_ESTABLISH),
            )
        )
        assert result.outcome is SynthesisOutcome.CONFLICTING_PROOFS

    def test_three_paths_all_agree_non_support(self):
        result = synthesize_proofs(
            (
                _proof("a", ProofVerdict.ESTABLISHES_NON_SUPPORT),
                _proof("b", ProofVerdict.ESTABLISHES_NON_SUPPORT),
                _proof("c", ProofVerdict.DOES_NOT_ESTABLISH),
            )
        )
        assert result.outcome is SynthesisOutcome.NON_SUPPORT_ESTABLISHED


class TestNoProof:
    def test_empty_proof_tuple(self):
        result = synthesize_proofs(())
        assert result.outcome is SynthesisOutcome.NO_SUFFICIENT_PROOF


class TestOneSufficientProofPlusManyDoesNotEstablish:
    def test_one_support_outweighs_many_non_proofs(self):
        proofs = tuple(_proof(f"p{i}", ProofVerdict.DOES_NOT_ESTABLISH) for i in range(10)) + (
            _proof("winner", ProofVerdict.ESTABLISHES_SUPPORT),
        )
        result = synthesize_proofs(proofs)
        assert result.outcome is SynthesisOutcome.SUPPORT_ESTABLISHED


class TestNoVotingNoWeighting:
    def test_more_non_establish_results_never_outvote_a_real_proof(self):
        """Explicit adversarial check: 9 DOES_NOT_ESTABLISH results
        against 1 ESTABLISHES_NON_SUPPORT -- a count-based or
        weighted-vote rule would (wrongly) favor the majority; this rule
        must not."""
        proofs = tuple(_proof(f"p{i}", ProofVerdict.DOES_NOT_ESTABLISH) for i in range(9)) + (
            _proof("real", ProofVerdict.ESTABLISHES_NON_SUPPORT),
        )
        result = synthesize_proofs(proofs)
        assert result.outcome is SynthesisOutcome.NON_SUPPORT_ESTABLISHED


class TestContributingProofsPreserved:
    def test_all_proofs_kept_in_order(self):
        proofs = (_proof("a", ProofVerdict.DOES_NOT_ESTABLISH), _proof("b", ProofVerdict.ESTABLISHES_SUPPORT))
        result = synthesize_proofs(proofs)
        assert result.contributing_proofs == proofs


class TestDeterminism:
    def test_identical_inputs_produce_identical_result(self):
        proofs = (_proof("a", ProofVerdict.ESTABLISHES_SUPPORT),)
        assert synthesize_proofs(proofs) == synthesize_proofs(proofs)
