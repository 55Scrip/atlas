"""Daily Brief v1 -- a distribution layer over Investment Case Change
Intelligence, never a second analysis engine.

Daily Brief answers exactly one question: "what changed today that
deserves the investor's attention?" Every fact this module produces is
a direct read of an already-computed `ChangeIntelligence` (Investment
Case Monitoring & Change Intelligence v1) -- this module never re-derives
a `BusinessCategoryStatus`/`RiskStatus`/`ValuationStatus`, never touches
a `BusinessRecord`, and never invents a priority/importance/urgency/
confidence number. Its only two computations, both purely presentational
and purely a function of already-real structured data, are:

1. **Eligibility** (`build_daily_brief_entry` returning `None`): a Case
   appears only when it is not a baseline and has at least one real
   `ChangeFinding` -- exactly the "thesis strengthened/weakened, new/
   resolved risk, new/resolved strength, new/resolved open question,
   analytical coverage changed" trigger list this sprint's own product
   brief names, because that list *is* `ChangeCategory`'s own closed
   membership. "Otherwise, do not include it" (silence over noise) is
   enforced here, once, for every caller.
2. **Headline** (`_headline`): a short, one-line label chosen from a
   fixed table keyed by `ChangeCategory`/`ChangeDirection` -- the same
   "closed vocabulary, no invented judgment" discipline
   `investment_case_change.describe_change` already applies to its own,
   longer sentence. `change_summary`/`why_it_matters` on each entry
   reuse `describe_change`/`thesis_impact_sentence` verbatim -- this
   module writes no new sentence-generation logic of its own beyond the
   one-line headline table.

**Ordering is alphabetical by ticker, never by an invented importance
score.** The product brief explicitly forbids priority/importance/
urgency/confidence numbers; alphabetical-by-ticker is the one ordering
this sprint can apply without inventing a ranking model.

**Pure, no persistence, no orchestration.** This module never reads a
Portfolio, a Watchlist, or a repository -- it only turns a list of
`(case_id, ticker, ChangeIntelligence)` a caller already assembled into
a `DailyBrief`. Gathering that list (Portfolio holdings + Watchlist
entries, each Case's own `ChangeIntelligence` via
`InvestmentCaseCompositionService.build`) is an Alpha-layer concern
(`atlas.alpha.daily_brief`), the same "Core computes, Alpha orchestrates"
split this whole sprint arc has used for every capability so far.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.analysis_engine.investment_case_change import (
    ChangeCategory,
    ChangeDirection,
    ChangeFinding,
    ChangeIntelligence,
    ThesisImpact,
    describe_change,
    dimension_label,
    thesis_impact_sentence,
)

__all__ = ["DailyBriefEntry", "DailyBrief", "build_daily_brief_entry", "build_daily_brief"]


@dataclass(frozen=True)
class DailyBriefEntry:
    """One company's worth of "what changed" -- every field is either a
    direct value from an already-computed `ChangeIntelligence` or a
    fixed-vocabulary label chosen from it. Never free-form AI text."""

    case_id: str
    ticker: str | None
    headline: str
    change_summary: str
    why_it_matters: str
    thesis_impact: ThesisImpact
    changes: tuple[ChangeFinding, ...]


@dataclass(frozen=True)
class DailyBrief:
    generated_at: datetime
    summary: str
    entries: tuple[DailyBriefEntry, ...]


_SINGLE_CHANGE_HEADLINE_VERB = {
    ChangeDirection.POSITIVE: "strengthened",
    ChangeDirection.NEGATIVE: "weakened",
}

_RISK_HEADLINE_VERB = {
    ChangeDirection.NEGATIVE: "increased",
    ChangeDirection.POSITIVE: "decreased",
}

_THESIS_IMPACT_HEADLINE = {
    ThesisImpact.STRENGTHENED: "Thesis strengthened.",
    ThesisImpact.WEAKENED: "Thesis weakened.",
    ThesisImpact.MIXED: "Mixed signals.",
    #: Reachable: several `ChangeDirection.NEUTRAL` changes (today,
    #: exclusively `ANALYTICAL_COVERAGE_CHANGED`) can coexist with zero
    #: positive/negative ones, which `_thesis_impact` correctly reports
    #: as `UNCHANGED` even though real changes exist.
    ThesisImpact.UNCHANGED: "Analytical coverage changed.",
}

_BUSINESS_QUALITY_CATEGORIES = (
    ChangeCategory.GROWTH_CHANGED,
    ChangeCategory.CAPITAL_ALLOCATION_CHANGED,
    ChangeCategory.BUSINESS_QUALITY_CHANGED,
)
_RISK_CATEGORIES = (
    ChangeCategory.BUSINESS_RISK_CHANGED,
    ChangeCategory.FINANCIAL_RISK_CHANGED,
    ChangeCategory.VALUATION_RISK_CHANGED,
)


def _single_change_headline(change: ChangeFinding) -> str:
    if change.category is ChangeCategory.ANALYTICAL_COVERAGE_CHANGED:
        if change.current_state in ("insufficient_input", "not_evaluated"):
            return "Analytical coverage reduced."
        return "New analytical coverage."
    if change.category in _BUSINESS_QUALITY_CATEGORIES:
        label = dimension_label(change.details.get("dimension", ""))
        return f"{label} {_SINGLE_CHANGE_HEADLINE_VERB[change.direction]}."
    if change.category in _RISK_CATEGORIES:
        label = dimension_label(change.details.get("dimension", ""))
        return f"{label} {_RISK_HEADLINE_VERB[change.direction]}."
    if change.category is ChangeCategory.VALUATION_CHANGED:
        return "Valuation became more attractive." if change.direction is ChangeDirection.POSITIVE else "Valuation became less attractive."
    if change.category is ChangeCategory.STRENGTH_ADDED:
        return "New strength identified."
    if change.category is ChangeCategory.STRENGTH_REMOVED:
        return "Strength no longer supported."
    if change.category is ChangeCategory.RISK_ADDED:
        return "New risk identified."
    if change.category is ChangeCategory.RISK_REMOVED:
        return "Risk resolved."
    if change.category is ChangeCategory.OPEN_QUESTION_ADDED:
        return "New open question."
    if change.category is ChangeCategory.OPEN_QUESTION_RESOLVED:
        return "Open question resolved."
    return "Analytical state changed."  # pragma: no cover -- exhaustive above; defensive only.


def _headline(changes: tuple[ChangeFinding, ...], thesis_impact: ThesisImpact) -> str:
    if len(changes) == 1:
        return _single_change_headline(changes[0])
    return _THESIS_IMPACT_HEADLINE[thesis_impact]


def build_daily_brief_entry(
    case_id: str, ticker: str | None, change_intelligence: ChangeIntelligence
) -> DailyBriefEntry | None:
    """`None` when this Case has nothing worth reporting today: a
    baseline (first-ever analysis -- never a change), or a real
    comparison that produced zero `ChangeFinding`s ("recomputed, not
    changed"; see `investment_case_change.compare_snapshots`'s own
    docstring). This is the one, single eligibility check the whole
    sprint's "otherwise, do not include it" rule reduces to."""
    if change_intelligence.is_baseline or not change_intelligence.changes:
        return None
    changes = change_intelligence.changes
    return DailyBriefEntry(
        case_id=case_id,
        ticker=ticker,
        headline=_headline(changes, change_intelligence.thesis_impact),
        change_summary="\n".join(describe_change(change) for change in changes),
        why_it_matters=thesis_impact_sentence(change_intelligence.thesis_impact),
        thesis_impact=change_intelligence.thesis_impact,
        changes=changes,
    )


def _overall_summary(entries: tuple[DailyBriefEntry, ...]) -> str:
    if not entries:
        return "No material analytical changes since your previous review."
    if len(entries) == 1:
        return "1 company has a meaningful analytical change to review."
    return f"{len(entries)} companies have meaningful analytical changes to review."


def build_daily_brief(
    entries: tuple[DailyBriefEntry, ...], *, generated_at: datetime
) -> DailyBrief:
    """`entries` should already be exactly the non-`None` results of
    `build_daily_brief_entry` -- this function performs no eligibility
    filtering of its own, only deterministic ordering and the overall
    summary sentence. Sorted alphabetically by ticker (case-insensitive,
    `None` tickers last) -- never by an invented importance score, per
    this sprint's own explicit "no ranking model" instruction."""
    ordered = tuple(sorted(entries, key=lambda entry: (entry.ticker is None, (entry.ticker or "").upper())))
    return DailyBrief(
        generated_at=generated_at,
        summary=_overall_summary(ordered),
        entries=ordered,
    )
