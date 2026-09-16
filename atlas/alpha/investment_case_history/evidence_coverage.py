"""How much historical evidence Atlas actually has -- measured, not assumed.

Atlas can now freeze the evidence behind a conclusion and read it back. What
it could not say is *how much of that record exists yet*, and the answer
"we need more history" is too vague to plan against. This module answers the
precise version: how many evidence-bearing snapshots, for which Cases, over
what span, under which methodology, and how many genuinely distinct evidence
states -- so that "is this question answerable yet?" stops being a guess.

**It counts; it does not judge.** There is no readiness score here, and no
threshold saying how many snapshots are enough. Deciding that ten
observations settle a question is a statistical claim this module is in no
position to make, and inventing a number would dress a guess as a standard.

**Three primitives are kept apart on purpose**, because collapsing them is
the easiest way to overstate a record:

* `evidence_snapshot_count` -- how many snapshots were written.
* `distinct_evidence_state_count` -- how many genuinely different evidence
  sets those snapshots represent. Ten snapshots of one unchanged state are
  one observation of that state, not ten.
* `distinct_evidence_day_count` -- how many calendar days they fall on. Ten
  snapshots from one afternoon do not span ten days.

None of the three is a count of *independent* observations, and nothing here
claims otherwise.

**Legacy rows are not evidence.** A snapshot written before the persistence
contract has no frozen evidence; it counts toward the total historical
record and toward nothing else. It is never reconstructed.

**Methodologies are not pooled.** Snapshots built under different valuation
methods describe different things, so they are grouped separately and a
method-dependent question must say which group it is asking about.

Read-only and decision-free: no valuation, recommendation, risk, fit,
stance, Decision Layer or Daily Brief result reads this, and the import
firewall in the tests enforces it.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Sequence

__all__ = [
    "Availability",
    "ReadinessQuestion",
    "MethodologyGroup",
    "CaseEvidenceCoverage",
    "HistoricalEvidenceCoverage",
    "SnapshotRecord",
    "build_coverage",
]


class Availability(str, Enum):
    """What can be asked of the record -- deliberately not "ready".

    `AVAILABLE` means the record structurally contains what the question
    needs, never that it contains enough of it to be convincing.
    """

    #: The record structurally supports the question. Says nothing about
    #: whether the sample is large enough to be persuasive.
    AVAILABLE = "available"
    #: Everything needed is being recorded; the thing asked about simply has
    #: not happened yet. More time may resolve it.
    NOT_YET_OBSERVED = "not_yet_observed"
    #: A kind of data the record does not contain at all. More time will not
    #: resolve it; something new has to be built or captured.
    MISSING_REQUIRED_DATA = "missing_required_data"


@dataclass(frozen=True)
class ReadinessQuestion:
    """One question, with what it structurally needs and whether the record
    has it. `detail` says what is missing in the record's own terms."""

    key: str
    question: str
    requirement: str
    availability: Availability
    detail: str


@dataclass(frozen=True)
class MethodologyGroup:
    """Snapshots sharing one valuation methodology identity. Kept apart from
    every other group: a comparison across two methods is comparing two
    rulers, not two measurements."""

    valuation_methodology: str | None
    evidence_schema_version: str | None
    snapshot_count: int
    case_count: int
    earliest_at: datetime | None
    latest_at: datetime | None
    span_days: int


@dataclass(frozen=True)
class CaseEvidenceCoverage:
    case_id: str
    ticker: str | None

    total_snapshot_count: int
    legacy_snapshot_count: int
    evidence_snapshot_count: int

    first_snapshot_at: datetime | None
    latest_snapshot_at: datetime | None
    first_evidence_at: datetime | None
    latest_evidence_at: datetime | None
    #: `0` when exactly one evidence-bearing snapshot exists -- a real span of
    #: no elapsed time, never a stand-in for "missing".
    evidence_span_days: int

    distinct_snapshot_day_count: int
    distinct_evidence_day_count: int
    distinct_evidence_state_count: int

    valuation_status_counts: Mapping[str, int]
    valuation_status_transition_count: int
    valuation_support_state_counts: Mapping[str, int]
    recommendation_state_counts: Mapping[str, int]

    range_edge_observation_count: int
    single_low_edge_dependency_count: int
    single_high_edge_dependency_count: int
    range_edge_dependency_transition_count: int

    methodologies: tuple[str | None, ...]
    evidence_schema_versions: tuple[str | None, ...]


@dataclass(frozen=True)
class HistoricalEvidenceCoverage:
    generated_at: datetime

    visible_case_count: int
    cases_with_any_history: int
    cases_with_frozen_evidence: int
    cases_without_frozen_evidence: int

    total_live_snapshot_count: int
    legacy_snapshot_count: int
    evidence_snapshot_count: int
    distinct_evidence_state_count: int
    distinct_evidence_day_count: int

    earliest_evidence_at: datetime | None
    latest_evidence_at: datetime | None
    evidence_span_days: int

    methodology_groups: tuple[MethodologyGroup, ...]
    readiness: tuple[ReadinessQuestion, ...]
    cases: tuple[CaseEvidenceCoverage, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SnapshotRecord:
    """One surviving snapshot, as coverage needs to see it: its own frozen
    state, never anything read from the live Case."""

    case_id: str
    ticker: str | None
    captured_at: datetime
    valuation_status: str | None
    recommendation_state: str | None
    valuation_methodology: str | None
    evidence: Mapping[str, Any] | None

    @property
    def is_evidence_bearing(self) -> bool:
        """The persistence contract decides this and nothing else: a frozen
        evidence payload is present, or it is not. Never inferred from a
        date, a methodology token or a status."""
        return self.evidence is not None


def _fingerprint(evidence: Mapping[str, Any]) -> str:
    """Which evidence state this is. Uses the fingerprint the persistence
    contract already stored where present; otherwise derives one from the
    frozen payload, canonically, so a record written by an older writer is
    still comparable with itself."""
    stored = evidence.get("fingerprint")
    if isinstance(stored, str) and stored:
        return stored
    material = {key: evidence.get(key) for key in
                ("prior_epochs", "valuation_methodology", "numerator_method", "share_count_method",
                 "eligibility", "minimum_prior_epochs", "valuation_support_status")}
    return hashlib.sha256(json.dumps(material, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _transitions(values: Sequence[Any]) -> int:
    """Changes between consecutive observations, in the record's own order --
    not the number of observations. Five readings with one change is one
    transition."""
    return sum(1 for previous, current in zip(values, values[1:]) if previous != current)


def _span_days(earliest: datetime | None, latest: datetime | None) -> int:
    if earliest is None or latest is None:
        return 0
    return (latest - earliest).days


def _case_coverage(case_id: str, ticker: str | None, records: Sequence[SnapshotRecord]) -> CaseEvidenceCoverage:
    ordered = sorted(records, key=lambda record: record.captured_at)
    evidence = [record for record in ordered if record.is_evidence_bearing]
    edges = [(record, (record.evidence or {}).get("metadata") or {}) for record in evidence]
    range_edges = [
        (record, (metadata.get("range_edge") or {}))
        for record, metadata in edges
        if isinstance(metadata, dict) and metadata.get("range_edge")
    ]
    dependency_series = [bool(edge.get("single_low_edge_dependency")) or bool(edge.get("single_high_edge_dependency"))
                         for _, edge in range_edges]
    return CaseEvidenceCoverage(
        case_id=case_id,
        ticker=ticker,
        total_snapshot_count=len(ordered),
        legacy_snapshot_count=len(ordered) - len(evidence),
        evidence_snapshot_count=len(evidence),
        first_snapshot_at=ordered[0].captured_at if ordered else None,
        latest_snapshot_at=ordered[-1].captured_at if ordered else None,
        first_evidence_at=evidence[0].captured_at if evidence else None,
        latest_evidence_at=evidence[-1].captured_at if evidence else None,
        evidence_span_days=_span_days(
            evidence[0].captured_at if evidence else None, evidence[-1].captured_at if evidence else None),
        distinct_snapshot_day_count=len({record.captured_at.date() for record in ordered}),
        distinct_evidence_day_count=len({record.captured_at.date() for record in evidence}),
        distinct_evidence_state_count=len({_fingerprint(record.evidence or {}) for record in evidence}),
        valuation_status_counts=dict(Counter(
            record.valuation_status for record in ordered if record.valuation_status is not None)),
        valuation_status_transition_count=_transitions([record.valuation_status for record in ordered]),
        valuation_support_state_counts=dict(Counter(
            (record.evidence or {}).get("valuation_support_status") for record in evidence
            if (record.evidence or {}).get("valuation_support_status") is not None)),
        recommendation_state_counts=dict(Counter(
            record.recommendation_state for record in ordered if record.recommendation_state is not None)),
        range_edge_observation_count=len(range_edges),
        single_low_edge_dependency_count=sum(
            1 for _, edge in range_edges if edge.get("single_low_edge_dependency")),
        single_high_edge_dependency_count=sum(
            1 for _, edge in range_edges if edge.get("single_high_edge_dependency")),
        range_edge_dependency_transition_count=_transitions(dependency_series),
        methodologies=tuple(sorted({record.valuation_methodology for record in ordered}, key=lambda v: (v is None, v))),
        evidence_schema_versions=tuple(sorted(
            {(record.evidence or {}).get("schema_version") for record in evidence}, key=lambda v: (v is None, v))),
    )


def _readiness(coverage: Sequence[CaseEvidenceCoverage], *, evidence_snapshots: int,
               distinct_states: int) -> tuple[ReadinessQuestion, ...]:
    """What the record can and cannot be asked, question by question.

    Each requirement is the *logical* minimum for the question to be
    answerable at all -- the structure the answer needs to exist. None of
    them is a sample size, and `AVAILABLE` never means the answer would be
    statistically convincing.
    """
    cases_with_two_states = [c for c in coverage if c.distinct_evidence_state_count >= 2]
    cases_with_transition = [c for c in coverage if c.valuation_status_transition_count > 0]
    cases_with_two_edge_states = [c for c in coverage if c.range_edge_observation_count >= 2]
    reduce_capable = [c for c in cases_with_two_states if c.range_edge_observation_count >= 2]

    return (
        ReadinessQuestion(
            key="snapshot_inspection",
            question="What evidence did Atlas have at a given past moment?",
            requirement="At least one evidence-bearing snapshot.",
            availability=Availability.AVAILABLE if evidence_snapshots >= 1 else Availability.NOT_YET_OBSERVED,
            detail=f"{evidence_snapshots} evidence-bearing snapshot(s) recorded.",
        ),
        ReadinessQuestion(
            key="evidence_change",
            question="Has a Case's frozen evidence changed between two recorded states?",
            requirement="At least two distinct evidence states for one Case.",
            availability=(Availability.AVAILABLE if cases_with_two_states
                          else Availability.NOT_YET_OBSERVED),
            detail=(f"{len(cases_with_two_states)} Case(s) have two or more distinct evidence states "
                    f"({distinct_states} distinct state(s) recorded in total)."),
        ),
        ReadinessQuestion(
            key="valuation_transition",
            question="Has a Case's valuation classification changed over the recorded history?",
            requirement="An observed change of valuation status between consecutive snapshots.",
            availability=(Availability.AVAILABLE if cases_with_transition
                          else Availability.NOT_YET_OBSERVED),
            detail=f"{len(cases_with_transition)} Case(s) show at least one valuation-status transition.",
        ),
        ReadinessQuestion(
            key="range_edge_longitudinal",
            question="Has range-edge dependence changed across recorded snapshots?",
            requirement="At least two evidence-bearing snapshots carrying range-edge evidence for one Case.",
            availability=(Availability.AVAILABLE if cases_with_two_edge_states
                          else Availability.NOT_YET_OBSERVED),
            detail=f"{len(cases_with_two_edge_states)} Case(s) have two or more range-edge observations.",
        ),
        ReadinessQuestion(
            key="reduce_gate_longitudinal",
            question="Did a REDUCE classification hold across changes in its own evidence?",
            requirement=(
                "For one Case: two or more distinct frozen evidence states, each carrying the frozen "
                "valuation status, Valuation Support and range-edge evidence the shadow experiment reads, "
                "under a single valuation methodology."
            ),
            availability=(Availability.AVAILABLE if reduce_capable else Availability.NOT_YET_OBSERVED),
            detail=(f"{len(reduce_capable)} Case(s) have two or more distinct evidence states with range-edge "
                    f"evidence. Structural availability only: it says the comparison can be assembled, "
                    f"never that the number of observations makes it conclusive."),
        ),
        ReadinessQuestion(
            key="outcome_backtest",
            question="Did one policy produce better realised returns than another?",
            requirement="Realised outcome data per decision -- entry, exit and subsequent return.",
            availability=Availability.MISSING_REQUIRED_DATA,
            detail=("Atlas records no realised outcomes. This is not a question of accumulating more "
                    "snapshots: the data class does not exist."),
        ),
    )


def build_coverage(
    records: Sequence[SnapshotRecord], *, visible_case_count: int, generated_at: datetime
) -> HistoricalEvidenceCoverage:
    """Count the surviving record. Pure: the same snapshots always produce the
    same coverage, and nothing here reads the live database."""
    by_case: dict[str, list[SnapshotRecord]] = {}
    tickers: dict[str, str | None] = {}
    for record in records:
        by_case.setdefault(record.case_id, []).append(record)
        tickers.setdefault(record.case_id, record.ticker)

    cases = tuple(sorted(
        (_case_coverage(case_id, tickers.get(case_id), case_records) for case_id, case_records in by_case.items()),
        key=lambda coverage: (coverage.ticker is None, coverage.ticker or "", coverage.case_id),
    ))
    evidence = [record for record in records if record.is_evidence_bearing]

    groups: dict[tuple[str | None, str | None], list[SnapshotRecord]] = {}
    for record in records:
        key = (record.valuation_methodology,
               (record.evidence or {}).get("schema_version") if record.evidence else None)
        groups.setdefault(key, []).append(record)
    methodology_groups = tuple(
        MethodologyGroup(
            valuation_methodology=methodology,
            evidence_schema_version=schema_version,
            snapshot_count=len(grouped),
            case_count=len({record.case_id for record in grouped}),
            earliest_at=min(record.captured_at for record in grouped),
            latest_at=max(record.captured_at for record in grouped),
            span_days=_span_days(min(record.captured_at for record in grouped),
                                 max(record.captured_at for record in grouped)),
        )
        for (methodology, schema_version), grouped in sorted(
            groups.items(), key=lambda item: (item[0][0] is None, item[0][0] or "", item[0][1] or ""))
    )

    distinct_states = len({_fingerprint(record.evidence or {}) for record in evidence})
    earliest = min((record.captured_at for record in evidence), default=None)
    latest = max((record.captured_at for record in evidence), default=None)
    return HistoricalEvidenceCoverage(
        generated_at=generated_at,
        visible_case_count=visible_case_count,
        cases_with_any_history=len(cases),
        cases_with_frozen_evidence=sum(1 for c in cases if c.evidence_snapshot_count > 0),
        cases_without_frozen_evidence=sum(1 for c in cases if c.evidence_snapshot_count == 0),
        total_live_snapshot_count=len(records),
        legacy_snapshot_count=len(records) - len(evidence),
        evidence_snapshot_count=len(evidence),
        distinct_evidence_state_count=distinct_states,
        distinct_evidence_day_count=len({record.captured_at.date() for record in evidence}),
        earliest_evidence_at=earliest,
        latest_evidence_at=latest,
        evidence_span_days=_span_days(earliest, latest),
        methodology_groups=methodology_groups,
        readiness=_readiness(cases, evidence_snapshots=len(evidence), distinct_states=distinct_states),
        cases=cases,
    )
