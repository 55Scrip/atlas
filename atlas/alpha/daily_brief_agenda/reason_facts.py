"""Semantic reason payloads (Implementation Sprint B1.1: Backend
Language Cleanup) -- the permanent boundary this sprint establishes:
**the backend produces meaning, the frontend produces language.**

`Signal.reason`/`AgendaItem.reason` (a plain `str`) predates this
module and is *not* removed here -- every source in `engine.py` still
constructs one, and it remains the wire format for any consumer that
has not adopted `ReasonFact` yet (internal logging, the raw fallback
text below). What this module adds is a second, additive, structured
channel: a closed `ReasonCode` naming *what kind* of fact fired, plus
the real, already-computed data (a closed enum's own `.value`, a
count, a real proper noun) needed to translate it -- never a rendered
sentence, never an English label, never a raw enum name concatenated
into English prose.

**Scope, decided deliberately narrow for this sprint.** Every source in
`daily_brief_agenda` was audited (see this sprint's own Final Report,
Phase 1). Two kinds of source were found:

1. Sources whose reason text is built *here*, in this package, from a
   closed, local vocabulary (`AttentionCategory`, `EvidenceGapKind`,
   `KeyFindingKind`, `LeadershipChangeEventType`/`ExecutiveRoleCategory`,
   `CredibilityFindingKind`, `BusinessQualityFindingKind`, Case
   Condition/Assumption status). These are exactly the sources
   `ReasonCode` below covers -- self-contained, low-risk to convert,
   and responsible for every concrete leak this sprint's own live
   verification found ("missing evidence (...)", "decision without
   outcome (...)", "(CEO) appointed").
2. Sources whose reason text comes from *another* engine's own
   free-form `.reason: str` (Change Intelligence, Portfolio Fit,
   Monitoring, and every "Decision Layer" `detect_*_change` engine --
   Decision Readiness, Investment Decision, Recommendation Conviction,
   Decision Path, Opportunity Cost, Decision Memory, Decision
   Explanation, Decision Reliability, Portfolio Decision). Converting
   these would mean redesigning each of those ~12 engines' own output
   contract -- a much larger, separate initiative this sprint's own
   "do not change business logic" instruction puts out of bounds. Left
   as fixed English text, unchanged, exactly as before this sprint;
   see the Final Report's own "Remaining implementation leaks."

**Never a rendered sentence.** A `ReasonFact` is data, not prose --
`value`/`secondary_value` are always a closed enum's own `.value`
string (frontend translates via its own key map, the same convention
`api/schemas.py` already documents for every other enum on the wire).
`label` is the one deliberate exception: a real, already-real proper
noun (a person's name, an investor-authored predicate/assumption
statement) that was never English-language "system speak" in the
first place and must never be translated -- passed through verbatim,
the same way a ticker already is.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = ["ReasonCode", "ReasonFact"]


class ReasonCode(str, Enum):
    """One member per distinct semantic fact shape this sprint converts
    -- never one per literal sentence. Each maps to exactly one
    canonical frontend translation (Phase 6: "the same reason must
    never appear differently depending on where it is rendered")."""

    WORKFLOW_GAP = "workflow_gap"
    """A structural gap `atlas.alpha.portfolio_status.AttentionCategory`
    already names (Decision without Outcome, Missing Case, ...).
    `value` = the category's own `.value`; `count` = how many real
    facts it summarizes (`ReviewQueueItem.reason_count`)."""

    MISSING_EVIDENCE = "missing_evidence"
    """A gap `atlas.decision_engine.contracts.EvidenceGapKind` already
    names. `value` = the gap kind's own `.value` -- the identical
    vocabulary Investment Case's own `investmentCase.intelligence
    .missingEvidence.*` keys already translate (Sprint B1's own
    "one truth, one place" finding, reused here rather than a second,
    parallel vocabulary)."""

    CONCENTRATION = "concentration"
    """A position-size finding `atlas.alpha.portfolio_intelligence
    .KeyFindingKind` already names (`HIGH_CONCENTRATION`/
    `ELEVATED_CONCENTRATION`). `value` = the finding kind's own
    `.value`."""

    LARGE_UNALLOCATED_CAPITAL = "large_unallocated_capital"
    """Portfolio-level, no entity ticker. `count` = the number of real
    considerations this capital could support
    (`KeyFinding.count`)."""

    EXECUTIVE_CHANGE = "executive_change"
    """A `LeadershipChangeEvent` already disclosed in a real transcript.
    `value` = `LeadershipChangeEventType.value` (the verb -- appointed/
    departed/...); `secondary_value` = `ExecutiveRoleCategory.value`
    (the role); `label` = the executive's own real name, never
    translated."""

    MANAGEMENT_CREDIBILITY = "management_credibility"
    """A deterioration `CredibilityFindingKind` already names
    (`INCONSISTENT_FOLLOW_THROUGH`/`GUIDANCE_REVISED_DOWNWARD` -- the
    only two members this source ever fires for; see
    `engine.py::management_credibility_signal`). `value` = the
    finding kind's own `.value`."""

    BUSINESS_QUALITY = "business_quality"
    """A deterioration `BusinessQualityFindingKind` already names
    (`WEAKENING_BUSINESS` -- the only member this source ever fires
    for; see `engine.py::business_quality_signal`). `value` = the
    finding kind's own `.value`."""

    CASE_CONDITION_STATUS = "case_condition_status"
    """A Case Condition that reached `status == "satisfied"`. `value` =
    the status string; `label` = the condition's own investor-authored
    `predicate_text` -- real free text, never translated, the same way
    a ticker or a person's name is not "system language" and stays
    exactly as written."""

    ASSUMPTION_STATUS = "assumption_status"
    """An Assumption that reached `status in ("invalidated",
    "challenged")`. `value` = the status string; `label` = the
    assumption's own investor-authored `statement` -- real free text,
    never translated, same reasoning as `CASE_CONDITION_STATUS`."""


@dataclass(frozen=True)
class ReasonFact:
    """One semantic fact -- never a rendered sentence. `entity` is the
    real ticker/subject the fact is about (never embedded in prose,
    unlike the legacy `reason: str` field this is threaded alongside).
    `value`/`secondary_value` are always a closed enum's own `.value`;
    `label` is real, already-real free text (a name, an investor's own
    words) that was never system language and is passed through
    verbatim, never translated. `count` is a real, already-computed
    number, never estimated here."""

    code: ReasonCode
    entity: str
    value: str | None = None
    secondary_value: str | None = None
    label: str | None = None
    count: int | None = None
