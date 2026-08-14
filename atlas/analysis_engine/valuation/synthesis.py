"""Proof synthesis (`DE-015` §16 Proof Standard).

Generic over any number of registered proof paths -- today exactly two
(`scenario_proof.py`, `net_cash_proof.py`), but this function's own logic
never hardcodes that count; a future third path is purely additive
(append one more `PathProof` to the input tuple, nothing here changes).

**Exact rule, verbatim from `DE-015` §16:**

    any ESTABLISHES_SUPPORT, none contradicting  -> support established
    any ESTABLISHES_NON_SUPPORT, none contradicting -> non-support established
    both appear among the paths                  -> conflicting proofs
    neither appears                                -> no sufficient proof

**No voting, no weights, no scores, no counts, no priority ranking.** A
single genuine proof outweighs any number of `DOES_NOT_ESTABLISH` results
from other paths; two genuine, conflicting proofs resolve to honest
uncertainty, never a tie-break by which path "wins."
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.analysis_engine.valuation.proof import PathProof, ProofVerdict

__all__ = ["SynthesisOutcome", "SynthesisResult", "synthesize_proofs"]


class SynthesisOutcome(str, Enum):
    """The four, and only four, shapes a proof synthesis can take --
    internal only, mapped to the public `ValuationSupportStatus` (plus,
    when applicable, a specific `ValuationSupportGapKind`) by the
    orchestrator in `support.py`."""

    SUPPORT_ESTABLISHED = "support_established"
    NON_SUPPORT_ESTABLISHED = "non_support_established"
    CONFLICTING_PROOFS = "conflicting_proofs"
    NO_SUFFICIENT_PROOF = "no_sufficient_proof"


@dataclass(frozen=True)
class SynthesisResult:
    outcome: SynthesisOutcome
    contributing_proofs: tuple[PathProof, ...]
    """Every proof considered, in the order supplied -- kept for
    `reasoning`/gap-selection purposes, never re-derived."""


def synthesize_proofs(proofs: tuple[PathProof, ...]) -> SynthesisResult:
    """Deterministic: identical `proofs` always produce an identical
    `SynthesisResult`. An empty `proofs` tuple is treated identically to
    a tuple of only `DOES_NOT_ESTABLISH` results -- `NO_SUFFICIENT_PROOF`."""
    has_support = any(p.verdict is ProofVerdict.ESTABLISHES_SUPPORT for p in proofs)
    has_non_support = any(p.verdict is ProofVerdict.ESTABLISHES_NON_SUPPORT for p in proofs)

    if has_support and has_non_support:
        outcome = SynthesisOutcome.CONFLICTING_PROOFS
    elif has_support:
        outcome = SynthesisOutcome.SUPPORT_ESTABLISHED
    elif has_non_support:
        outcome = SynthesisOutcome.NON_SUPPORT_ESTABLISHED
    else:
        outcome = SynthesisOutcome.NO_SUFFICIENT_PROOF

    return SynthesisResult(outcome=outcome, contributing_proofs=proofs)
