"""Executive Identity + Tenure History + Leadership Change Events +
Succession Knowledge + Leadership Composition Queries + Management
Knowledge Linking + Leadership Change Findings (Capability Expansion
Sprint 10: Executive Change Intelligence, Phases 2 through 8).

**Phase 1 audit finding, the load-bearing fact this entire module is
built around**: this codebase has exactly one real, already-ingested
source of executive identity -- `earnings_call.ManagementStatement`'s
own `speaker`/`title` fields (Alpha Vantage's transcript API reports
both per statement). `company_profile.py`'s `CompanyProfile` carries no
officer data; `regulatory_filings.py`'s own module docstring is explicit
that Atlas reads a SEC filing's *metadata* (form type, accession number)
and never its *content* -- so an 8-K's own Item 5.02 (the real-world
disclosure of an executive appointment/departure) is invisible to Atlas
today; no `BusinessFactKind` or provider anywhere carries a director or
officer name. This module therefore builds exclusively from Sprint 2's
own already-classified `speaker`/`title` metadata -- it adds no new
`CommentaryCategory`, no new `SourceKind`, no new provider call, and
(per Phase 9's own instruction) registers no new `KnowledgeDomain`: the
underlying `TRANSCRIPT` records are already covered by the existing
`EARNINGS_CALL_ANALYSIS` domain, and this module is a pure, further
aggregation of that same already-covered evidence, exactly the
precedent Financial Quality/Business Quality/Management Credibility
Intelligence already established.

**This is a real, disclosed, load-bearing limitation, not an oversight:
`start_date`/`end_date` on `ExecutiveIdentity` are always `None` in this
build.** No transcript ever states "today is my first day as CEO" or an
explicit employment start/end date -- only that a named person spoke,
under a given title, in a given quarter's call. `first_observed_date`/
`last_observed_date` carry the real evidence Atlas actually has: the
earliest and latest transcript on which that person was recorded
speaking under that role. These are evidence-observation windows, never
a claim about actual HR-recorded employment dates -- the distinction
Phase 3's own "unknown dates should remain unknown; do not approximate"
instruction exists to protect.

**`LeadershipChangeEventType` is a complete, closed vocabulary per
Phase 4's own list -- but only `APPOINTMENT`/`INTERIM_APPOINTMENT`/
`PERMANENT_APPOINTMENT`/`ROLE_CHANGE`/`DEPARTURE` are ever reachable
from real data in this build.** `RESIGNATION`/`RETIREMENT`/
`TERMINATION`/`PROMOTION`/`BOARD_APPOINTMENT`/`BOARD_DEPARTURE` remain
real, valid members -- Atlas simply has no source that ever states a
departure's specific reason, or any director-level (non-speaking) board
data, so these members are never populated -- a framework, not a
complete dataset, the identical discipline `SegmentGrowthInformation`
(Sprint 6) and `return_on_invested_capital_unavailable_reason` (Sprint
5) already establish. `DEPARTURE` itself is deliberately neutral: it
means "last observed in this role, a different individual subsequently
observed in the same role" -- never a claim of resignation, retirement,
or termination, which the source never states.

**Succession Knowledge (Phase 5) is deliberately narrow**: the *only*
succession relationship this module ever represents is an interim-to-
permanent transition within the identical `ExecutiveRoleCategory`,
evidenced by the literal word "interim" being present in the earlier
title and absent from the later one -- real, disclosed textual
evidence, never an inference drawn "solely because one tenure ends near
another's beginning" (this sprint's own explicit non-goal). A CEO-to-
CEO succession (Phase 5's own other example) is never represented in
this build: no source explicitly states that link, and inferring it
from mere chronological adjacency is exactly what this sprint forbids.

**Role-change detection (also feeding `LeadershipChangeEventType.
ROLE_CHANGE`) requires the identical speaker name observed under two
different `ExecutiveRoleCategory` values** -- a strong, literal signal
(the same person, a different title), not an inference across two
different individuals.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from atlas.alpha.investment_case.earnings_call import EarningsCallKnowledge

__all__ = [
    "ExecutiveRoleCategory",
    "ExecutiveIdentity",
    "LeadershipChangeEventType",
    "LeadershipChangeEvent",
    "SuccessionRelationship",
    "LeadershipChangeFindingKind",
    "LeadershipChangeFinding",
    "ExecutiveChangeKnowledge",
    "extract_executive_change_intelligence",
    "executive_at",
    "executives_present_during",
    "changes_between",
    "find_executive_for_statement",
]


class ExecutiveRoleCategory(str, Enum):
    CEO = "ceo"
    CFO = "cfo"
    COO = "coo"
    CHAIR = "chair"
    EXECUTIVE_CHAIR = "executive_chair"
    PRESIDENT = "president"
    CTO = "cto"
    CIO = "cio"
    GENERAL_COUNSEL = "general_counsel"
    BOARD_DIRECTOR = "board_director"
    OTHER_EXECUTIVE = "other_executive"


_ROLE_KEYWORDS: tuple[tuple[str, ExecutiveRoleCategory], ...] = (
    ("chief executive officer", ExecutiveRoleCategory.CEO),
    ("ceo", ExecutiveRoleCategory.CEO),
    ("chief financial officer", ExecutiveRoleCategory.CFO),
    ("cfo", ExecutiveRoleCategory.CFO),
    ("chief operating officer", ExecutiveRoleCategory.COO),
    ("coo", ExecutiveRoleCategory.COO),
    ("chief technology officer", ExecutiveRoleCategory.CTO),
    ("cto", ExecutiveRoleCategory.CTO),
    ("chief information officer", ExecutiveRoleCategory.CIO),
    ("cio", ExecutiveRoleCategory.CIO),
    ("general counsel", ExecutiveRoleCategory.GENERAL_COUNSEL),
    ("executive chairman", ExecutiveRoleCategory.EXECUTIVE_CHAIR),
    ("executive chair", ExecutiveRoleCategory.EXECUTIVE_CHAIR),
    ("chairman", ExecutiveRoleCategory.CHAIR),
    ("chair", ExecutiveRoleCategory.CHAIR),
    ("president", ExecutiveRoleCategory.PRESIDENT),
    ("board director", ExecutiveRoleCategory.BOARD_DIRECTOR),
    ("director", ExecutiveRoleCategory.BOARD_DIRECTOR),
)
"""Priority-ordered, literal substring matches only -- a title that
matches none of these falls through to the non-executive exclusion
check below, never a guess (Phase 2's own "do not infer titles that
are not explicitly supported by source material")."""

_INTERIM_KEYWORD = "interim"

#: Trust Hardening Sprint: Alpha Vantage's own transcript metadata
#: reports these literally and consistently -- confirmed against real,
#: already-ingested AMAT transcripts: every sell-side participant's
#: title is exactly `"Analyst (<firm>)"` (e.g. `"Analyst (Bernstein
#: Research)"`), and the call moderator's title is exactly
#: `"Operator"`. Neither is a guess or a heuristic threshold -- both are
#: literal, structural substrings Alpha Vantage itself always includes,
#: the same "real, disclosed textual evidence, never an inference"
#: discipline this module's own docstring already requires elsewhere
#: (see Succession Knowledge/Role-change detection above). A speaker
#: whose title contains either marker is never a company executive,
#: regardless of what other words the title contains.
_NON_EXECUTIVE_KEYWORDS = ("analyst", "operator", "moderator")

#: Investor Relations staff (confirmed real example: "Corporate Vice
#: President, Investor Relations") are real company employees, but an
#: IR title alone does not identify a leadership role -- only tracked
#: as an executive when the title *also* carries one of the real
#: `_ROLE_KEYWORDS` matches above (checked first, so this never
#: excludes a genuine "Chief Investor Relations Officer"-style title).
_INVESTOR_RELATIONS_KEYWORD = "investor relations"


def _role_category(title: str | None) -> ExecutiveRoleCategory | None:
    """Returns `None` -- never `OTHER_EXECUTIVE` -- for a speaker who is
    not a company executive at all: an analyst, the call operator, or
    an untitled/unknown speaker (Phase 5's own "unknown roles must not
    default into executive identities"). `OTHER_EXECUTIVE` remains the
    real, honest catch-all for a genuinely-titled executive whose exact
    role just isn't one of the specific keywords tracked above -- it is
    never a default for "we don't know who this is.\""""
    if title is None:
        return None
    lowered = title.lower()
    if any(keyword in lowered for keyword in _NON_EXECUTIVE_KEYWORDS):
        return None
    if _INVESTOR_RELATIONS_KEYWORD in lowered:
        # Checked before the keyword loop below, not after: an
        # "Investor Relations" title very commonly carries "Vice
        # President" (the real, confirmed example this sprint found --
        # "Corporate Vice President, Investor Relations" -- would
        # otherwise falsely match the bare "president" keyword). A
        # title that is genuinely both IR *and* a real top executive
        # role would need a stronger, unambiguous marker than "vice
        # president" to overturn this -- none of `_ROLE_KEYWORDS`'
        # entries besides "president"/"chairman"/"chair" are broad
        # enough to accidentally fire here, and those three are exactly
        # the ones this exclusion exists to guard against.
        return None
    for keyword, category in _ROLE_KEYWORDS:
        if keyword in lowered:
            return category
    return ExecutiveRoleCategory.OTHER_EXECUTIVE


def _is_interim(title: str | None) -> bool:
    return title is not None and _INTERIM_KEYWORD in title.lower()


# -- Phase 2 + 3: Executive Identity Model + Tenure History -----------------


@dataclass(frozen=True)
class ExecutiveIdentity:
    """Every field Phase 2 asks for. `start_date`/`end_date` are always
    `None` in this build -- see this module's own docstring for why;
    `first_observed_date`/`last_observed_date` carry the real evidence
    window this module actually has."""

    name: str
    role_category: ExecutiveRoleCategory
    raw_title: str | None
    """The most recently observed verbatim title for this (name, role
    category) pair -- never normalized beyond the case-insensitive
    keyword match used to derive `role_category`/`is_interim`."""
    company: str | None
    start_date: date | None
    end_date: date | None
    is_interim: bool
    """Derived from the most recently observed `raw_title` only -- an
    earlier occurrence's own interim status, if it later changed, is
    not separately preserved on this one record (Phase 6's timeline
    queries and `LeadershipChangeEvent.provenance` strings carry that
    finer-grained history instead)."""
    first_observed_date: date
    last_observed_date: date
    source_transcripts: tuple[str, ...]
    """Every distinct transcript (by its own `quarter` label) this
    identity was observed speaking in, chronological."""
    statement_count: int


def _extract_identities(ticker: str | None, earnings_call: EarningsCallKnowledge) -> tuple[ExecutiveIdentity, ...]:
    accumulators: dict[tuple[str, ExecutiveRoleCategory], dict] = {}
    for transcript in earnings_call.transcripts:
        observed_date = transcript.fiscal_date_ending or transcript.published_at
        seen_this_transcript: set[tuple[str, ExecutiveRoleCategory]] = set()
        for statement in transcript.statements:
            role_category = _role_category(statement.title)
            if role_category is None:
                continue
            key = (statement.speaker, role_category)
            entry = accumulators.setdefault(key, {"dates": [], "transcripts": [], "raw_title": None, "statement_count": 0})
            entry["statement_count"] += 1
            entry["raw_title"] = statement.title
            if key not in seen_this_transcript:
                entry["dates"].append(observed_date)
                entry["transcripts"].append(transcript.quarter)
                seen_this_transcript.add(key)

    identities = [
        ExecutiveIdentity(
            name=name, role_category=role_category, raw_title=entry["raw_title"], company=ticker,
            start_date=None, end_date=None, is_interim=_is_interim(entry["raw_title"]),
            first_observed_date=min(entry["dates"]), last_observed_date=max(entry["dates"]),
            source_transcripts=tuple(entry["transcripts"]), statement_count=entry["statement_count"],
        )
        for (name, role_category), entry in accumulators.items()
    ]
    identities.sort(key=lambda identity: identity.first_observed_date)
    return tuple(identities)


# -- Phase 5: Succession Knowledge ------------------------------------------


@dataclass(frozen=True)
class SuccessionRelationship:
    role_category: ExecutiveRoleCategory
    outgoing_executive_name: str
    outgoing_last_observed_date: date
    incoming_executive_name: str
    incoming_first_observed_date: date
    evidence: str
    """A disclosed, human-readable statement of exactly what textual
    signal supports this relationship -- Phase 5's own "may represent a
    succession relationship only when the underlying evidence genuinely
    links the roles," made inspectable rather than only asserted."""


def _successions(identities: tuple[ExecutiveIdentity, ...]) -> tuple[SuccessionRelationship, ...]:
    by_role: dict[ExecutiveRoleCategory, list[ExecutiveIdentity]] = {}
    for identity in identities:
        by_role.setdefault(identity.role_category, []).append(identity)
    for group in by_role.values():
        group.sort(key=lambda identity: identity.first_observed_date)

    successions: list[SuccessionRelationship] = []
    for role_category, group in by_role.items():
        for earlier, later in zip(group, group[1:]):
            if earlier.is_interim and not later.is_interim and earlier.name != later.name:
                successions.append(
                    SuccessionRelationship(
                        role_category=role_category, outgoing_executive_name=earlier.name,
                        outgoing_last_observed_date=earlier.last_observed_date, incoming_executive_name=later.name,
                        incoming_first_observed_date=later.first_observed_date,
                        evidence=(
                            "The earlier executive's most recently observed title in this role contained "
                            "'interim'; the later executive's title in the same role did not."
                        ),
                    )
                )
    return tuple(successions)


# -- Phase 4: Leadership Change Events ---------------------------------------


class LeadershipChangeEventType(str, Enum):
    APPOINTMENT = "appointment"
    DEPARTURE = "departure"
    RESIGNATION = "resignation"
    RETIREMENT = "retirement"
    TERMINATION = "termination"
    PROMOTION = "promotion"
    INTERIM_APPOINTMENT = "interim_appointment"
    PERMANENT_APPOINTMENT = "permanent_appointment"
    BOARD_APPOINTMENT = "board_appointment"
    BOARD_DEPARTURE = "board_departure"
    ROLE_CHANGE = "role_change"


@dataclass(frozen=True)
class LeadershipChangeEvent:
    event_type: LeadershipChangeEventType
    executive_name: str
    role_category: ExecutiveRoleCategory
    """For `ROLE_CHANGE`, the *new* role category; for every other
    event type, the role the event concerns."""
    prior_role_category: ExecutiveRoleCategory | None
    """Only ever set for `ROLE_CHANGE`."""
    effective_date: date | None
    """Always `None` in this build -- no source states an explicit
    effective date, only when a person was observed speaking."""
    announcement_date: date | None
    """Always `None` in this build -- an earnings call transcript is
    not itself an announcement of the change."""
    observed_date: date
    """The real, evidence-based date this event was derived from."""
    source_transcript: str
    provenance: str
    """A disclosed, human-readable explanation of exactly how this
    event was derived (Phase 11's own provenance requirement, made
    inspectable rather than only asserted in a docstring)."""


def _leadership_change_events(
    identities: tuple[ExecutiveIdentity, ...], successions: tuple[SuccessionRelationship, ...]
) -> tuple[LeadershipChangeEvent, ...]:
    events: list[LeadershipChangeEvent] = []

    by_role: dict[ExecutiveRoleCategory, list[ExecutiveIdentity]] = {}
    for identity in identities:
        by_role.setdefault(identity.role_category, []).append(identity)
    for group in by_role.values():
        group.sort(key=lambda identity: identity.first_observed_date)

    by_name: dict[str, list[ExecutiveIdentity]] = {}
    for identity in identities:
        by_name.setdefault(identity.name, []).append(identity)
    for group in by_name.values():
        group.sort(key=lambda identity: identity.first_observed_date)

    role_change_targets: set[tuple[str, ExecutiveRoleCategory]] = set()
    role_change_sources: set[tuple[str, ExecutiveRoleCategory]] = set()
    for name, group in by_name.items():
        if len(group) < 2:
            continue
        for earlier, later in zip(group, group[1:]):
            if earlier.role_category is later.role_category:
                continue
            events.append(
                LeadershipChangeEvent(
                    event_type=LeadershipChangeEventType.ROLE_CHANGE, executive_name=name,
                    role_category=later.role_category, prior_role_category=earlier.role_category,
                    effective_date=None, announcement_date=None, observed_date=later.first_observed_date,
                    source_transcript=later.source_transcripts[0],
                    provenance=(
                        f"Same individual previously observed as {earlier.role_category.value} through "
                        f"{earlier.last_observed_date.isoformat()}, subsequently observed as "
                        f"{later.role_category.value} beginning {later.first_observed_date.isoformat()}."
                    ),
                )
            )
            role_change_targets.add((later.name, later.role_category))
            role_change_sources.add((earlier.name, earlier.role_category))

    succession_incoming = {(s.incoming_executive_name, s.role_category) for s in successions}

    for role_category, group in by_role.items():
        for index, identity in enumerate(group):
            key = (identity.name, identity.role_category)
            is_first = index == 0
            is_last = index == len(group) - 1

            if key in role_change_targets:
                pass
            elif key in succession_incoming:
                events.append(
                    LeadershipChangeEvent(
                        event_type=LeadershipChangeEventType.PERMANENT_APPOINTMENT, executive_name=identity.name,
                        role_category=role_category, prior_role_category=None, effective_date=None,
                        announcement_date=None, observed_date=identity.first_observed_date,
                        source_transcript=identity.source_transcripts[0],
                        provenance=(
                            "First observed without an 'interim' title in this role, immediately following an "
                            "interim predecessor in the same role."
                        ),
                    )
                )
            else:
                event_type = (
                    LeadershipChangeEventType.INTERIM_APPOINTMENT if identity.is_interim
                    else LeadershipChangeEventType.APPOINTMENT
                )
                provenance = (
                    "First observed speaking in this role in the available transcript history."
                    if is_first else
                    "First observed speaking in this role; a different individual was previously observed in the "
                    "same role. Atlas does not know the reason or exact date of the transition."
                )
                events.append(
                    LeadershipChangeEvent(
                        event_type=event_type, executive_name=identity.name, role_category=role_category,
                        prior_role_category=None, effective_date=None, announcement_date=None,
                        observed_date=identity.first_observed_date, source_transcript=identity.source_transcripts[0],
                        provenance=provenance,
                    )
                )

            if not is_last and key not in role_change_sources:
                successor = group[index + 1]
                events.append(
                    LeadershipChangeEvent(
                        event_type=LeadershipChangeEventType.DEPARTURE, executive_name=identity.name,
                        role_category=role_category, prior_role_category=None, effective_date=None,
                        announcement_date=None, observed_date=identity.last_observed_date,
                        source_transcript=identity.source_transcripts[-1],
                        provenance=(
                            f"Last observed speaking in this role on {identity.last_observed_date.isoformat()}; a "
                            f"different individual ({successor.name}) was subsequently observed in the same role. "
                            "Atlas does not know the reason or exact date of any departure."
                        ),
                    )
                )

    events.sort(key=lambda event: event.observed_date)
    return tuple(events)


# -- Phase 6: Leadership Composition History (query helpers) ----------------


def executive_at(
    identities: tuple[ExecutiveIdentity, ...], role_category: ExecutiveRoleCategory, as_of: date
) -> ExecutiveIdentity | None:
    """Phase 6's own "who was CEO during this period" -- a pure lookup
    over already-built `first_observed_date`/`last_observed_date`
    windows, no new computation."""
    candidates = [
        identity for identity in identities
        if identity.role_category is role_category and identity.first_observed_date <= as_of <= identity.last_observed_date
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda identity: identity.first_observed_date)


def executives_present_during(
    identities: tuple[ExecutiveIdentity, ...], start: date, end: date
) -> tuple[ExecutiveIdentity, ...]:
    return tuple(
        identity for identity in identities
        if identity.first_observed_date <= end and identity.last_observed_date >= start
    )


def changes_between(
    events: tuple[LeadershipChangeEvent, ...], start: date, end: date
) -> tuple[LeadershipChangeEvent, ...]:
    return tuple(event for event in events if start <= event.observed_date <= end)


# -- Phase 7: Management Knowledge Linking -----------------------------------


def find_executive_for_statement(
    identities: tuple[ExecutiveIdentity, ...], speaker: str, statement_date: date
) -> ExecutiveIdentity | None:
    """Resolves a raw `speaker` name + statement date (the exact shape
    every `ManagementCommitment`/`GuidanceItem` already carries) to the
    matching `ExecutiveIdentity` -- Phase 7's own "the CFO at that time
    said" linkage, provided as a pure function callers opt into. Neither
    Sprint 8's `management_credibility_intelligence.py` nor Sprint 9's
    `management_guidance_intelligence.py` is modified to call this --
    both remain untouched, per this sprint's own non-goals."""
    candidates = [
        identity for identity in identities
        if identity.name == speaker and identity.first_observed_date <= statement_date <= identity.last_observed_date
    ]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    return max(candidates, key=lambda identity: identity.statement_count)


# -- Phase 8: Leadership Change Intelligence (findings) ----------------------


class LeadershipChangeFindingKind(str, Enum):
    CEO_TRANSITION_OCCURRED = "ceo_transition_occurred"
    CFO_TRANSITION_OCCURRED = "cfo_transition_occurred"
    INTERIM_LEADERSHIP_PRESENT = "interim_leadership_present"
    REPEATED_EXECUTIVE_TURNOVER = "repeated_executive_turnover"
    LONG_EXECUTIVE_TENURE = "long_executive_tenure"
    MAJOR_BOARD_TRANSITION = "major_board_transition"
    """Never populated in this build -- Atlas has no non-speaking board
    director data source; see this module's own docstring."""
    INSUFFICIENT_LEADERSHIP_HISTORY = "insufficient_leadership_history"


@dataclass(frozen=True)
class LeadershipChangeFinding:
    kind: LeadershipChangeFindingKind
    supporting_executives: tuple[str, ...]
    supporting_events: tuple[LeadershipChangeEvent, ...]


_MIN_TRANSCRIPTS_FOR_LONG_TENURE = 4
"""Disclosed, simple threshold: observed speaking across at least four
distinct transcripts (a full year of quarterly earnings calls, the
cadence this codebase already assumes) counts as a long observed
tenure -- never a fabricated precise year count."""
_MIN_DEPARTURES_FOR_REPEATED_TURNOVER = 2


def _findings(
    identities: tuple[ExecutiveIdentity, ...], events: tuple[LeadershipChangeEvent, ...]
) -> tuple[LeadershipChangeFinding, ...]:
    findings: list[LeadershipChangeFinding] = []

    ceo_departures = tuple(
        e for e in events if e.role_category is ExecutiveRoleCategory.CEO and e.event_type is LeadershipChangeEventType.DEPARTURE
    )
    if ceo_departures:
        findings.append(
            LeadershipChangeFinding(
                kind=LeadershipChangeFindingKind.CEO_TRANSITION_OCCURRED,
                supporting_executives=tuple(e.executive_name for e in ceo_departures), supporting_events=ceo_departures,
            )
        )

    cfo_departures = tuple(
        e for e in events if e.role_category is ExecutiveRoleCategory.CFO and e.event_type is LeadershipChangeEventType.DEPARTURE
    )
    if cfo_departures:
        findings.append(
            LeadershipChangeFinding(
                kind=LeadershipChangeFindingKind.CFO_TRANSITION_OCCURRED,
                supporting_executives=tuple(e.executive_name for e in cfo_departures), supporting_events=cfo_departures,
            )
        )

    interim_appointments = tuple(e for e in events if e.event_type is LeadershipChangeEventType.INTERIM_APPOINTMENT)
    if interim_appointments:
        findings.append(
            LeadershipChangeFinding(
                kind=LeadershipChangeFindingKind.INTERIM_LEADERSHIP_PRESENT,
                supporting_executives=tuple(e.executive_name for e in interim_appointments),
                supporting_events=interim_appointments,
            )
        )

    all_departures = tuple(e for e in events if e.event_type is LeadershipChangeEventType.DEPARTURE)
    if len(all_departures) >= _MIN_DEPARTURES_FOR_REPEATED_TURNOVER:
        findings.append(
            LeadershipChangeFinding(
                kind=LeadershipChangeFindingKind.REPEATED_EXECUTIVE_TURNOVER,
                supporting_executives=tuple(e.executive_name for e in all_departures), supporting_events=all_departures,
            )
        )

    long_tenure = tuple(identity for identity in identities if len(identity.source_transcripts) >= _MIN_TRANSCRIPTS_FOR_LONG_TENURE)
    if long_tenure:
        findings.append(
            LeadershipChangeFinding(
                kind=LeadershipChangeFindingKind.LONG_EXECUTIVE_TENURE,
                supporting_executives=tuple(identity.name for identity in long_tenure), supporting_events=(),
            )
        )

    if not findings:
        findings.append(
            LeadershipChangeFinding(
                kind=LeadershipChangeFindingKind.INSUFFICIENT_LEADERSHIP_HISTORY, supporting_executives=(),
                supporting_events=(),
            )
        )

    return tuple(findings)


# -- Composition --------------------------------------------------------------


@dataclass(frozen=True)
class ExecutiveChangeKnowledge:
    executives: tuple[ExecutiveIdentity, ...]
    leadership_changes: tuple[LeadershipChangeEvent, ...]
    successions: tuple[SuccessionRelationship, ...]
    findings: tuple[LeadershipChangeFinding, ...]


def extract_executive_change_intelligence(
    ticker: str | None, earnings_call: EarningsCallKnowledge
) -> ExecutiveChangeKnowledge:
    """Pure, no I/O. `earnings_call.transcripts == ()` yields an empty
    executive history -- never a fabricated leadership record."""
    identities = _extract_identities(ticker, earnings_call)
    successions = _successions(identities)
    events = _leadership_change_events(identities, successions)
    findings = _findings(identities, events)
    return ExecutiveChangeKnowledge(
        executives=identities, leadership_changes=events, successions=successions, findings=findings,
    )
