"""Traceability primitive (ATLAS-020, Phase 7 realized as a real type).

`Provenance` is the one mechanism every `Finding` (`findings.py`) and
every new field on `CanonicalAnalysis` (`models.py`) uses to answer
"where did this come from, what does it depend on, what would change
it, and who reads it" — never a separate "sources" appendix bolted onto
the side of the analysis, which is exactly the design this package's
own `__init__.py` explains was rejected for `CanonicalAnalysis` itself.

Deliberately minimal: three closed enums and one dataclass, no free
text anywhere except `reference` (an id string, never a sentence) and
`consumers` (each a closed identifier, not prose).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

__all__ = ["SourceKind", "UpdateTrigger", "Consumer", "Provenance"]


class SourceKind(str, Enum):
    """What kind of thing produced a value -- a closed, small set.
    `EXTERNAL_DATA_SOURCE` is reserved, named now so a future sprint
    that adds financial-statement/news/report ingestion does not need
    to widen this enum's meaning -- no code in this sprint ever
    constructs a `Provenance` with this value, matching the same
    "reserve the name, never construct it" discipline
    `atlas.decision_engine.contracts.RecommendationOutcomeKind.DIRECTIONAL`
    already established."""

    CORE_DOMAIN_RECORD = "core_domain_record"
    """A specific Decision, Observation, Evidence, or Outcome record."""

    DECISION_ENGINE_STAGE = "decision_engine_stage"
    """A finding copied verbatim from a named `atlas.decision_engine` stage."""

    ANALYSIS_ENGINE_STAGE = "analysis_engine_stage"
    """Computed by a stage inside this package itself (e.g. Conviction)."""

    EXTERNAL_DATA_SOURCE = "external_data_source"
    """Reserved. Never constructed this sprint -- no external data
    source is ingested anywhere in this codebase yet."""


class UpdateTrigger(str, Enum):
    """The specific domain event that invalidates a value and requires
    it to be recomputed -- never "periodically" or "on page load,"
    always a named, real event this codebase already models."""

    NEW_DECISION_RECORDED = "new_decision_recorded"
    NEW_OBSERVATION_RECORDED = "new_observation_recorded"
    NEW_EVIDENCE_RECORDED = "new_evidence_recorded"
    NEW_OUTCOME_RECORDED = "new_outcome_recorded"
    NEW_TRADE_RECORDED = "new_trade_recorded"
    HOLDING_STATE_CHANGED = "holding_state_changed"
    UPSTREAM_STAGE_CHANGED = "upstream_stage_changed"
    """Recompute because a `Finding`/section this one `dependencies` on
    changed -- the general "derived value" case, distinct from the
    named domain-event triggers above."""


class Consumer(str, Enum):
    """Which surface reads a given field -- generated from the
    ownership map documented in this sprint's design artifact, not
    hand-maintained per field. A closed set so "consumers" can never
    silently drift into free text."""

    PORTFOLIO_PAGE = "portfolio_page"
    INVESTMENT_CASE_PAGE = "investment_case_page"
    DISCOVERY = "discovery"
    WEEKLY_REVIEW = "weekly_review"
    HISTORY = "history"


@dataclass(frozen=True)
class Provenance:
    """Attached to a `Finding` or a `CanonicalAnalysis` field -- never a
    standalone record. `source_kind`/`source_references` say where a
    value came from; `dependencies` says what other `Finding`s it was
    derived from (by their own `Finding.id`); `update_trigger` says what
    would invalidate it; `consumers` says who reads it; `computed_at` is
    always the caller-supplied evaluation timestamp, never a wall-clock
    read inside this package (the same determinism rule
    `atlas.decision_engine` already enforces)."""

    source_kind: SourceKind
    source_references: tuple[str, ...]
    dependencies: tuple[str, ...]
    update_trigger: UpdateTrigger
    consumers: tuple[Consumer, ...]
    computed_at: datetime
