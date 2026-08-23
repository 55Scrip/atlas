"""Result shapes for the Stance Engine (Atlas Intelligence Sprint 2 --
Recommendation Quality & Actionability). See this package's `engine.py`
module docstring for the full derivation rules.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.alpha.coverage import ConfidenceLevel

__all__ = [
    "StanceLevel",
    "StanceReasonCode",
    "StanceReason",
    "Stance",
    "StanceComparisonReasonCode",
    "StanceComparisonReason",
    "StanceComparison",
]


class StanceLevel(str, Enum):
    """Deliverable 2's own seven-member outcome vocabulary. Explicitly
    **not** a trade-sizing instruction -- see this package's own
    `__init__.py` for why. `INCREASE`/`REDUCE` describe the *direction*
    of Atlas's current view (strengthening/weakening), never "buy more"/
    "sell some"; the presentation layer renders them as "View
    strengthened"/"View weakened," never anything share-count-adjacent."""

    INCREASE = "increase"
    """Atlas's view has genuinely strengthened since the last review,
    with enough coverage/confidence to say so plainly."""
    MAINTAIN = "maintain"
    """The current view remains intact -- nothing material changed, and
    Atlas has enough basis to say that plainly."""
    REDUCE = "reduce"
    """Atlas's view has genuinely weakened since the last review, with
    enough coverage/confidence to say so plainly."""
    REVIEW = "review"
    """Something material requires investor review before Atlas can
    state a clear directional stance -- mixed signals, a weak Portfolio
    Fit alongside an otherwise-favorable signal, or high risk alongside
    an otherwise-favorable signal."""
    WAIT = "wait"
    """The case may be genuinely interesting, but Atlas's own coverage
    or confidence is too thin to support any directional claim yet --
    patient, not alarmed."""
    AVOID_DECISION = "avoid_decision"
    """A real red flag exists -- contradicting evidence, or conviction
    itself could not be established -- strong enough that Atlas should
    not support any decision right now, not merely "wait for more
    data.\""""
    NO_RECOMMENDATION = "no_recommendation"
    """Atlas has no company data to reason from at all -- the floor
    state, distinct from every level above (which all presuppose at
    least some real analysis exists)."""


class StanceReasonCode(str, Enum):
    """Every fact that contributed to a `Stance` -- closed vocabulary,
    matching `atlas.analysis_engine.conviction.ConvictionReasonCode`/
    `atlas.alpha.coverage.models.ConfidenceReasonCode`'s own established
    pattern: the presentation layer writes the sentence, this engine
    only names real, already-computed facts."""

    NO_COMPANY_DATA = "no_company_data"
    CONTRADICTING_EVIDENCE_PRESENT = "contradicting_evidence_present"
    CONVICTION_INSUFFICIENT = "conviction_insufficient"
    CONFIDENCE_VERY_LIMITED = "confidence_very_limited"
    CONFIDENCE_LIMITED = "confidence_limited"
    CONFIDENCE_MODERATE = "confidence_moderate"
    THESIS_STRENGTHENED = "thesis_strengthened"
    THESIS_WEAKENED = "thesis_weakened"
    THESIS_MIXED = "thesis_mixed"
    THESIS_UNCHANGED = "thesis_unchanged"
    DECISION_SUPPORT_FAVORABLE = "decision_support_favorable"
    DECISION_SUPPORT_UNFAVORABLE = "decision_support_unfavorable"
    DECISION_SUPPORT_NEUTRAL = "decision_support_neutral"
    PORTFOLIO_FIT_WEAK = "portfolio_fit_weak"
    PORTFOLIO_FIT_FAVORABLE = "portfolio_fit_favorable"
    HIGH_RISK_PRESENT = "high_risk_present"
    NO_HIGH_RISK = "no_high_risk"


@dataclass(frozen=True)
class StanceReason:
    code: StanceReasonCode


@dataclass(frozen=True)
class Stance:
    level: StanceLevel
    reasoning: tuple[StanceReason, ...]
    """Every reason that drove the final `level` -- the gating chain
    itself, in order. Never a subset; always the complete decision
    trail, the same "name every applicable code" discipline
    `ConvictionAssessment.reasons` already established."""
    supporting_signals: tuple[StanceReason, ...]
    """Real signals pointing favorably -- a subset of facts this engine
    observed, never a second computation. Empty when nothing favorable
    was found."""
    limiting_signals: tuple[StanceReason, ...]
    """Real signals holding the stance back -- the counterpart to
    `supporting_signals`. Empty when nothing limiting was found."""
    confidence: ConfidenceLevel
    """Reused verbatim from `atlas.alpha.coverage.CoverageAssessment
    .overall_confidence` -- this engine never derives a second
    confidence signal."""
    missing_information: tuple[str, ...]
    """Reused verbatim from `atlas.alpha.coverage.CoverageAssessment
    .missing_dimensions` -- real dimension keys, not free text."""


class StanceComparisonReasonCode(str, Enum):
    """Closed vocabulary for `StanceComparison.reasoning` -- deliberately
    not free text (an Atlas Intelligence Sprint 1 lesson: a hand-written
    English sentence here would leak untranslated into a Swedish UI the
    same way this Sprint's own `ConfidenceReasonCode` was introduced to
    fix). The presentation layer owns the sentence for each code."""

    PREFERRED_HAS_A_MORE_FAVORABLE_STANCE = "preferred_has_a_more_favorable_stance"
    BOTH_STANCES_TIED = "both_stances_tied"
    ONE_OR_BOTH_TOO_UNCERTAIN_TO_COMPARE = "one_or_both_too_uncertain_to_compare"


@dataclass(frozen=True)
class StanceComparisonReason:
    code: StanceComparisonReasonCode
    ticker: str | None = None
    """The ticker this reason is about, when the code names one side
    specifically (`PREFERRED_HAS_A_MORE_FAVORABLE_STANCE`); `None` for
    codes about the comparison as a whole."""


@dataclass(frozen=True)
class StanceComparison:
    """Deliverable 9 (Compare Integration) -- a pure comparison of two
    already-computed `Stance`s. Computes nothing about either company;
    mirrors `atlas.alpha.portfolio_fit.models.FitComparison`'s own
    shape and "never a forced tiebreak" discipline, with one deliberate
    difference: `reasoning` here is closed reason codes, not free
    sentences -- see `StanceComparisonReasonCode`'s own docstring."""

    ticker_a: str
    stance_a: Stance
    ticker_b: str
    stance_b: Stance
    preferred_ticker: str | None
    """`None` whenever Atlas cannot honestly prefer one over the other
    -- both landed on the same level, or either one lacks a confident
    enough basis to compare at all (`WAIT`/`AVOID_DECISION`/
    `NO_RECOMMENDATION`). Never a forced tiebreak dressed up as a
    preference."""
    reasoning: tuple[StanceComparisonReason, ...]
