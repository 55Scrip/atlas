"""Business Quality Assessment models (Calibration Phase 5 -- Business
Quality Engine).

Every level below is a closed, categorical classification -- never a
numeric score, never a weighted average (the same discipline
`atlas.analysis_engine.conviction`/`capital_allocation` already
establish). `UNKNOWN` is always a legitimate, honest terminal state,
never a placeholder that later resolves to something else -- reached
whenever the real evidence available cannot support a conclusion, or
when Atlas structurally has no data source for a dimension at all.

Every assessment carries `unassessed_dimensions`: a fixed, disclosed
list of the qualitative evidence a human analyst would use that Atlas
has no data source for this sprint (market share, brand strength,
network effects, governance, addressable market size, and similar --
see `docs/Calibration-Phase-5-Business-Quality-Engine.md` Parts C-E for
exactly which dimensions apply to which engine and why). This list is
always present, regardless of the level reached -- an `EXCEPTIONAL`
read is still proxy-based, never presented as equivalent to genuine
qualitative competitive analysis.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = [
    "MoatLevel",
    "MoatEvidenceKind",
    "MoatAssessment",
    "ManagementQualityLevel",
    "ManagementDimensionKind",
    "ManagementDimensionAssessment",
    "ManagementAssessment",
    "ReinvestmentOpportunityLevel",
    "ReinvestmentEvidenceKind",
    "ReinvestmentAssessment",
    "BusinessQualityLevel",
    "BusinessQualityDriverKind",
    "BusinessQualityDriver",
    "BusinessQualityAssessment",
]


class MoatLevel(str, Enum):
    EXCEPTIONAL = "exceptional"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    UNKNOWN = "unknown"


class MoatEvidenceKind(str, Enum):
    """Named, closed vocabulary for what evidence contributed to a
    `MoatAssessment` -- every entry traces to one real, already-computed
    signal (see `moat.py`'s own module docstring), never free text."""

    STABLE_PROFITABILITY_THROUGH_VARYING_CONDITIONS = "stable_profitability_through_varying_conditions"
    VOLATILE_PROFITABILITY = "volatile_profitability"
    RISING_RETURNS_ON_CAPITAL = "rising_returns_on_capital"
    FALLING_RETURNS_ON_CAPITAL = "falling_returns_on_capital"
    DURABLE_GROWTH_ACROSS_MULTIPLE_METRICS = "durable_growth_across_multiple_metrics"
    CONSISTENT_VALUE_CREATION = "consistent_value_creation"
    STRONG_CAPITAL_ALLOCATION_TRACK_RECORD = "strong_capital_allocation_track_record"
    WEAK_CAPITAL_ALLOCATION_TRACK_RECORD = "weak_capital_allocation_track_record"


@dataclass(frozen=True)
class MoatAssessment:
    level: MoatLevel
    supporting_evidence: tuple[MoatEvidenceKind, ...]
    unassessed_dimensions: tuple[str, ...]


class ManagementQualityLevel(str, Enum):
    EXCEPTIONAL = "exceptional"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    UNKNOWN = "unknown"


class ManagementDimensionKind(str, Enum):
    """The brief's own seven dimensions, verbatim -- evaluating
    management behavior, never personality or communication style."""

    CAPITAL_ALLOCATION = "capital_allocation"
    EXECUTION = "execution"
    CONSISTENCY = "consistency"
    COMMUNICATION = "communication"
    LONG_TERM_THINKING = "long_term_thinking"
    SHAREHOLDER_ALIGNMENT = "shareholder_alignment"
    GOVERNANCE = "governance"


@dataclass(frozen=True)
class ManagementDimensionAssessment:
    kind: ManagementDimensionKind
    level: ManagementQualityLevel
    """Per-dimension level uses the identical five-member vocabulary as
    the overall assessment -- one closed vocabulary, not two."""


@dataclass(frozen=True)
class ManagementAssessment:
    level: ManagementQualityLevel
    dimensions: tuple[ManagementDimensionAssessment, ...]
    """Always names all seven `ManagementDimensionKind` members, every
    assessment -- `GOVERNANCE` always resolves to `UNKNOWN` this sprint
    (see module docstring)."""
    unassessed_dimensions: tuple[str, ...]


class ReinvestmentOpportunityLevel(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    LIMITED = "limited"
    UNKNOWN = "unknown"


class ReinvestmentEvidenceKind(str, Enum):
    DURABLE_GROWTH_ACROSS_MULTIPLE_METRICS = "durable_growth_across_multiple_metrics"
    RISING_RETURNS_ON_CAPITAL = "rising_returns_on_capital"
    FALLING_RETURNS_ON_CAPITAL = "falling_returns_on_capital"
    SUSTAINED_CASH_GENERATION = "sustained_cash_generation"
    INCONSISTENT_CASH_GENERATION = "inconsistent_cash_generation"
    RISING_REINVESTMENT_ACTIVITY = "rising_reinvestment_activity"


@dataclass(frozen=True)
class ReinvestmentAssessment:
    level: ReinvestmentOpportunityLevel
    supporting_evidence: tuple[ReinvestmentEvidenceKind, ...]
    unassessed_dimensions: tuple[str, ...]


class BusinessQualityLevel(str, Enum):
    EXCEPTIONAL = "exceptional"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    UNKNOWN = "unknown"


class BusinessQualityDriverKind(str, Enum):
    """Closed vocabulary for the integrated score's own strengths/
    weaknesses -- each member names exactly one real sub-assessment
    reading, never invented commentary (Phase 8's own "drivers must be
    backed by actual engine outputs")."""

    EXCEPTIONAL_COMPETITIVE_POSITION = "exceptional_competitive_position"
    STRONG_COMPETITIVE_POSITION = "strong_competitive_position"
    WEAK_COMPETITIVE_POSITION = "weak_competitive_position"
    EXCEPTIONAL_MANAGEMENT_QUALITY = "exceptional_management_quality"
    STRONG_MANAGEMENT_QUALITY = "strong_management_quality"
    WEAK_MANAGEMENT_QUALITY = "weak_management_quality"
    EXCELLENT_REINVESTMENT_RUNWAY = "excellent_reinvestment_runway"
    GOOD_REINVESTMENT_RUNWAY = "good_reinvestment_runway"
    LIMITED_REINVESTMENT_RUNWAY = "limited_reinvestment_runway"


@dataclass(frozen=True)
class BusinessQualityDriver:
    kind: BusinessQualityDriverKind
    source: str
    """Dot-path name of the exact sub-assessment field this driver was
    read from (`"moat.level"` / `"management.level"` /
    `"reinvestment.level"`) -- traceable, never a free-standing label."""


@dataclass(frozen=True)
class BusinessQualityAssessment:
    moat: MoatAssessment
    management: ManagementAssessment
    reinvestment: ReinvestmentAssessment
    overall_level: BusinessQualityLevel
    strengths: tuple[BusinessQualityDriver, ...]
    weaknesses: tuple[BusinessQualityDriver, ...]
    greatest_advantage: BusinessQualityDriver | None
    greatest_concern: BusinessQualityDriver | None
    unknowns: tuple[str, ...]
    """Deduplicated union of `moat`/`management`/`reinvestment`'s own
    `unassessed_dimensions` -- one place to see everything Atlas could
    not evaluate and why."""
