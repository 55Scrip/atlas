"""Valuation Support for Capital Deployment (Alpha implementation sprint).

**Scope, per the binding reconciliation for this sprint.** No ADR for
"Valuation Support for Capital Deployment" existed anywhere in this
repository before this sprint -- `DE-008-Direction-Selection.md` names the
concept and fences it off (`DE-008` §21 invariant 11, §23 Rejected
Alternatives, §24 Open Questions) but never specifies it as a constructible
domain object. This module is that specification's first real
implementation, built under an explicit constraint: **`DE-008` stays
unmodified.** `ValuationStatus.UNDERVALUED` SHALL NOT become
`ValuationSupport.SUPPORTED`, and `ValuationStatus.EXPENSIVE` SHALL NOT
become `ValuationSupport.NOT_SUPPORTED`, by any mapping, threshold, or
proxy -- exactly as `DE-008` §21 invariant 11 already forbids for the
positive direction, applied here symmetrically to the negative one (see
"Why NOT_SUPPORTED is also unreachable today" below).

**The domain question, and why it differs from what `cash_flow.py` already
answers.** `ValuationSupport` answers exactly one question: "does today's
market valuation provide support for deploying new capital?" --
never "is this a good business," "will earnings grow," "is the outlook
attractive," or "should the investor buy" (those belong to Business
Analysis, Outlook, and Recommendation respectively, and this module reads
none of them). `ValuationMethodKind.FCF_YIELD_RELATIVE`
(`atlas.analysis_engine.valuation.cash_flow`) -- the only real, non-stub
valuation conclusion this codebase produces today -- answers a genuinely
different, narrower question: how does today's price compare with this
company's own recorded trading history. A company can be priced better
than its own history has ever offered and still be a poor place to commit
new capital (the business itself may have permanently weakened); a company
can be priced worse than its own history has ever offered and still be a
strong place to commit new capital (a structural re-rating driven by
genuinely improved economics). Distinguishing those two cases requires a
forward-looking judgment neither `FCF_YIELD_RELATIVE` nor the
`SCENARIO_BEAR`/`BASE`/`BULL` methods can honestly supply --
`FCF_YIELD_RELATIVE` by design makes no forward assumption at all, and
`scenarios.py`'s own module docstring already refuses to fabricate one.

**Why `NOT_SUPPORTED` is also unreachable today, not only `SUPPORTED`.**
It would be tempting to let `ValuationStatus.EXPENSIVE` -- the worst pole
of the identical historical-comparison scale `UNDERVALUED` sits at the
opposite end of -- establish `NOT_SUPPORTED`, on the theory that a
cautionary conclusion needs a lower evidentiary bar than a
capital-committing one (this codebase's own `DE-008` §21 invariant 5
already grants `EXPENSIVE` that lower bar for TRIM, an existing-position
action). This module deliberately does not take that path. `EXPENSIVE`
and `UNDERVALUED` are computed by the identical mechanism
(`cash_flow.py`'s own rule table, symmetric around the company's own
historical yield range) -- there is no fact internal to `FCF_YIELD_RELATIVE`
itself that makes one pole a legitimate absolute judgment about
capital-deployment support while the other pole is not. Both remain purely
comparative-to-own-history signals; neither carries the forward-looking
content the domain question requires, in either direction. Treating
`EXPENSIVE` as sufficient here would be exactly the same category error
`DE-008` §21 invariant 11 already forbids for `UNDERVALUED`, just applied
to the opposite pole -- not a principled asymmetry, a disguised one.

**`DE-015` implementation sprint: real logic, not a stub.** `status` is
now computed from two independently-sufficient proof paths -- the
Scenario path (`scenario_proof.py`, `DE-015` §9/§11/§12, itself built on
the valuation-native eligibility gate in `eligibility.py` and the shared,
opinion-free primitives in `business_facts.growth_primitives`) and the
Net-Cash path (`net_cash_proof.py`, `DE-015` §15) -- combined by the
proof-standard synthesis rule (`synthesis.py`, `DE-015` §16), never by
voting. `SUPPORTED`/`NOT_SUPPORTED` are genuinely reachable for a real
company for the first time; `INSUFFICIENT_INPUT` remains the honest,
expected, common outcome whenever neither path can establish anything,
or the paths disagree -- never minimized, never engineered away (`DE-015`
§8). See `eligibility.py`/`scenario_proof.py`/`net_cash_proof.py`/
`synthesis.py`'s own module docstrings for the full derivation.

**Independence, structurally enforced.** This module, and everything it
calls (`eligibility.py`, `scenario_proof.py`, `net_cash_proof.py`,
`proof.py`, `synthesis.py`, `business_facts.growth_primitives`), reads
only raw `BusinessFact`/`ValuationFact`s and the already-computed
`ValuationEngineResult` -- never `atlas.analysis_engine.recommendation`,
`.recommendation_conviction`, `.direction_selector`, `.outlook`,
`.business`, `BusinessCategoryStatus`, `BusinessFinding`, or
`atlas.decision_engine.contracts.PortfolioIntelligenceResult`. Nothing in
`atlas.analysis_engine.recommendation`/`.direction_selector` imports this
package either (verified by this package's own boundary tests) --
`select_direction`'s and `evaluate_recommendation_gate`'s signatures are
unchanged by this sprint, per `DE-015` §18's own instruction not to alter
Direction Selection to accommodate this implementation.

**Public contract, and why each field exists.**

- `status` (`ValuationSupportStatus`) -- the one fact a consumer needs:
  does today's valuation support new capital deployment. Exactly three
  members, no fourth. No confidence, score, probability, weighting,
  ranking, or Conviction field exists anywhere on this type -- `status`
  alone is the categorical conclusion, matching this codebase's own
  "status is the conclusion" discipline everywhere else.
- `reasoning` (`str`) -- explainability only, never consumed by gating
  logic anywhere. Describes the valuation conclusion in plain domain
  language; never names a valuation model, a formula, or a calculation
  (no "FCF yield," "DCF," "EV/EBIT," "PEG," "Residual Income," or any
  other implementation detail appears in any reasoning string this module
  ever constructs).
- `gap` (`ValuationSupportGapKind | None`) -- present exactly when
  `status is INSUFFICIENT_INPUT`, `None` otherwise; explains *why* a
  conclusion could not be reached, never a fourth status value.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.valuation.contracts import ValuationMethodKind
from atlas.analysis_engine.valuation.eligibility import IneligibilityReason, evaluate_scenario_eligibility
from atlas.analysis_engine.valuation.facts import ValuationFact
from atlas.analysis_engine.valuation.models import ValuationEngineResult
from atlas.analysis_engine.valuation.net_cash_proof import evaluate_net_cash_proof
from atlas.analysis_engine.valuation.scenario_proof import evaluate_scenario_proof
from atlas.analysis_engine.valuation.synthesis import SynthesisOutcome, synthesize_proofs

__all__ = [
    "ValuationSupportStatus",
    "ValuationSupportGapKind",
    "ValuationSupport",
    "evaluate_valuation_support",
]


class ValuationSupportStatus(str, Enum):
    """Exactly three members -- the adopted contract's own closed set.
    Never widened; a future capability that changes what is reachable
    still only ever produces one of these three."""

    SUPPORTED = "supported"
    NOT_SUPPORTED = "not_supported"
    INSUFFICIENT_INPUT = "insufficient_input"


class ValuationSupportGapKind(str, Enum):
    """Explanatory only -- see `ValuationSupport.gap`'s own docstring.

    **`DE-015` implementation sprint: additively widened, never renamed
    or removed.** `MISSING_CAPITAL_DEPLOYMENT_VALUATION_SUPPORT` is the
    original Alpha-stub-era member (kept verbatim -- no removals); the
    five members below are the smallest additive set that makes every
    real `INSUFFICIENT_INPUT` outcome the real evaluator can now produce
    non-silent, per `DE-015` §8/§9/§12/§16. Deliberately coarse where a
    single truthful category already covers several mechanical causes
    (`INSUFFICIENT_HISTORICAL_VALUATION_DATA` covers three distinct
    "not enough real data" reasons from the Scenario proof path alone) --
    no redundant member was added merely to distinguish causes a reader
    would not meaningfully act on differently."""

    MISSING_CAPITAL_DEPLOYMENT_VALUATION_SUPPORT = "missing_capital_deployment_valuation_support"

    NO_DURABLE_GROWTH_BASIS = "no_durable_growth_basis"
    """The Scenario path's own valuation-native eligibility gate (`DE-015`
    §9 condition 3) refused: full-history real evidence shows no
    legitimate growth basis on either Revenue or Free Cash Flow."""

    INSUFFICIENT_HISTORICAL_VALUATION_DATA = "insufficient_historical_valuation_data"
    """Not enough real historical data exists to build a range at all --
    covers fewer than two revenue-corroborated growth observations,
    no current Free Cash Flow yield, and no historical yield range,
    truthfully, without inventing a separate member for each."""

    SCENARIO_ENVELOPE_INCONCLUSIVE = "scenario_envelope_inconclusive"
    """A real, fully-computed forward-return envelope exists, but it
    straddles zero -- genuinely mixed evidence (`DE-015` §8), not a data
    shortfall."""

    CONFLICTING_VALUATION_PROOFS = "conflicting_valuation_proofs"
    """Two or more independently-sufficient valuation proofs (`DE-015`
    §16) disagree -- one establishes support, another establishes
    non-support. Never resolved by a tie-break."""

    NO_SUFFICIENT_VALUATION_PROOF = "no_sufficient_valuation_proof"
    """Residual, honest fallback: every registered proof path returned
    `does_not_establish`, for a combination of reasons not covered more
    specifically by the members above."""


#: `DE-015` implementation sprint. Deterministic, keyed lookup -- the same
#: "trivially diffable, never freeform" discipline `recommendation.py`'s
#: own `_DIRECTION_STATEMENTS` already established. Every string here
#: describes a valuation *conclusion* in plain domain language: never a
#: model name, a formula, a helper-function name, Outlook, or Business
#: Analysis. `SUPPORTED`'s own text explicitly restates `DE-015` §6's
#: narrower meaning (downside-aware, nominal, not economic sufficiency,
#: not risk-adjusted, not a BUY/ADD equivalent) so no render-facing
#: caller can present it as a stronger claim than Atlas can honestly make.
_SUPPORTED_REASONING = (
    "Atlas found a defensible, historically-grounded basis for concluding "
    "that today's valuation does not imply a loss, even under the less "
    "favorable end of the range Atlas considered. This describes the "
    "valuation itself only -- it does not weigh risk, does not compare "
    "against cash or any other alternative, and is not a recommendation to "
    "buy or add to a position."
)

_NOT_SUPPORTED_REASONING = (
    "Atlas found a defensible, historically-grounded valuation range for "
    "this company, and even the more favorable end of that range implies a "
    "loss at today's price. This describes the valuation itself only, "
    "independent of the business's own risk or any alternative use of "
    "capital."
)

_GAP_REASONING: dict["ValuationSupportGapKind", str] = {
    ValuationSupportGapKind.MISSING_CAPITAL_DEPLOYMENT_VALUATION_SUPPORT: (
        "Atlas's current valuation evidence describes how today's price compares "
        "with this company's own trading history. It does not yet make the "
        "separate, forward-looking judgment of whether committing new capital at "
        "today's price is supported -- so Atlas does not yet have a basis to "
        "conclude that today's valuation either supports or restricts deploying "
        "new capital into this position."
    ),
    ValuationSupportGapKind.NO_DURABLE_GROWTH_BASIS: (
        "This company's real historical record shows no period of genuine "
        "growth for Atlas to draw a forward valuation range from, so Atlas "
        "does not have a basis to conclude that today's valuation either "
        "supports or restricts deploying new capital into this position."
    ),
    ValuationSupportGapKind.INSUFFICIENT_HISTORICAL_VALUATION_DATA: (
        "There is not yet enough real historical data for Atlas to build a "
        "defensible valuation range for this company, so Atlas does not have "
        "a basis to conclude that today's valuation either supports or "
        "restricts deploying new capital into this position."
    ),
    ValuationSupportGapKind.SCENARIO_ENVELOPE_INCONCLUSIVE: (
        "Atlas built a defensible, historically-grounded valuation range for "
        "this company, but that range includes both a loss and a gain "
        "depending on which real historical scenario is used -- genuinely "
        "mixed evidence, not a basis for a one-sided conclusion."
    ),
    ValuationSupportGapKind.CONFLICTING_VALUATION_PROOFS: (
        "Atlas found two independent, real bases for evaluating this "
        "company's valuation, and they point in different directions -- one "
        "supports today's price, the other does not. Atlas does not resolve "
        "that disagreement by picking a side."
    ),
    ValuationSupportGapKind.NO_SUFFICIENT_VALUATION_PROOF: (
        "Atlas does not yet have a real basis, from any of the ways it "
        "currently knows how to evaluate valuation, to conclude that today's "
        "price either supports or restricts deploying new capital into this "
        "position."
    ),
}


@dataclass(frozen=True)
class ValuationSupport:
    """Minimal, immutable. Three public fields, no more -- see this
    module's own docstring for why each exists and why nothing else was
    added (no confidence/score/probability/weighting/ranking/conviction)."""

    status: ValuationSupportStatus
    reasoning: str
    gap: ValuationSupportGapKind | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, ValuationSupportStatus):
            raise AnalysisEngineContractError(
                "ValuationSupport.status must be a ValuationSupportStatus -- "
                "no other type, including a bare string, is accepted."
            )
        if not self.reasoning.strip():
            raise AnalysisEngineContractError(
                "ValuationSupport.reasoning must be non-empty -- explainability "
                "is a required part of the contract, never a bare status."
            )
        if (self.status is ValuationSupportStatus.INSUFFICIENT_INPUT) != (self.gap is not None):
            raise AnalysisEngineContractError(
                "ValuationSupport.gap must be present exactly when status is "
                "INSUFFICIENT_INPUT, and absent otherwise -- gap explains only "
                "why a conclusion could not be reached; it is never a fourth "
                "status value."
            )
        if self.gap is not None and not isinstance(self.gap, ValuationSupportGapKind):
            raise AnalysisEngineContractError(
                "ValuationSupport.gap must be a ValuationSupportGapKind when present."
            )


def _select_gap_for_no_sufficient_proof(
    business_facts: tuple[BusinessFact, ...],
    current_yield: float | None,
    historical_yields: tuple[float, ...],
    *,
    generated_at: datetime,
) -> ValuationSupportGapKind:
    """Re-derives the Scenario path's own eligibility check (cheap,
    deterministic, already real) purely to select the most specific real
    gap -- never by parsing `PathProof.evidence_summary` text, which
    exists for diagnostics, not control flow. Net-Cash's own
    `does_not_establish` ("priced above net cash") is the ordinary,
    unremarkable case for almost every real company and is never itself
    surfaced as the reason -- Scenario is the doctrinally richer path."""
    eligibility = evaluate_scenario_eligibility(business_facts, generated_at=generated_at)
    if not eligibility.eligible:
        if eligibility.ineligibility_reason is IneligibilityReason.NO_LEGITIMATE_GROWTH_BASIS:
            return ValuationSupportGapKind.NO_DURABLE_GROWTH_BASIS
        return ValuationSupportGapKind.INSUFFICIENT_HISTORICAL_VALUATION_DATA
    if current_yield is None or not historical_yields:
        return ValuationSupportGapKind.INSUFFICIENT_HISTORICAL_VALUATION_DATA
    # Eligible, with real current and historical yield data -> the
    # Scenario path computed a genuine envelope that straddled zero.
    return ValuationSupportGapKind.SCENARIO_ENVELOPE_INCONCLUSIVE


def evaluate_valuation_support(
    valuation_engine: ValuationEngineResult,
    business_facts: tuple[BusinessFact, ...],
    valuation_facts: tuple[ValuationFact, ...],
    *,
    generated_at: datetime,
) -> ValuationSupport:
    """Deterministic: identical inputs always produce an identical
    result. Orchestration only -- every real computation lives in
    `eligibility.py`/`scenario_proof.py`/`net_cash_proof.py`/
    `synthesis.py`; this function gathers real inputs, runs both proof
    paths, synthesizes them, and constructs the public contract. No new
    framework, no additional orchestration layer."""
    fcf_yield_finding = next(
        f for f in valuation_engine.findings if f.kind is ValuationMethodKind.FCF_YIELD_RELATIVE
    )

    scenario_proof = evaluate_scenario_proof(
        business_facts,
        current_yield=fcf_yield_finding.current_yield,
        historical_yields=fcf_yield_finding.historical_yields,
        generated_at=generated_at,
    )
    net_cash_proof = evaluate_net_cash_proof(business_facts, valuation_facts, generated_at=generated_at)

    result = synthesize_proofs((scenario_proof, net_cash_proof))

    if result.outcome is SynthesisOutcome.SUPPORT_ESTABLISHED:
        return ValuationSupport(status=ValuationSupportStatus.SUPPORTED, reasoning=_SUPPORTED_REASONING)
    if result.outcome is SynthesisOutcome.NON_SUPPORT_ESTABLISHED:
        return ValuationSupport(status=ValuationSupportStatus.NOT_SUPPORTED, reasoning=_NOT_SUPPORTED_REASONING)
    if result.outcome is SynthesisOutcome.CONFLICTING_PROOFS:
        gap = ValuationSupportGapKind.CONFLICTING_VALUATION_PROOFS
        return ValuationSupport(status=ValuationSupportStatus.INSUFFICIENT_INPUT, reasoning=_GAP_REASONING[gap], gap=gap)

    # SynthesisOutcome.NO_SUFFICIENT_PROOF
    gap = _select_gap_for_no_sufficient_proof(
        business_facts, fcf_yield_finding.current_yield, fcf_yield_finding.historical_yields, generated_at=generated_at
    )
    return ValuationSupport(status=ValuationSupportStatus.INSUFFICIENT_INPUT, reasoning=_GAP_REASONING[gap], gap=gap)
