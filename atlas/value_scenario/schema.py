"""Schema dataclasses for Atlas Value Scenario Reviews.

Represents scenario-based value and return ranges, assumptions, evidence items,
change triggers, revisions, portfolio contributions, and safety boundaries.

This module is intentionally schema-only. It does not implement valuation
calculations, forecasts, scoring, probability weighting, market data, live
prices, news, external APIs, AI/LLM calls, CLI commands, UI, persistence,
or broker integrations.

The core principle:
    Atlas should help users understand possible value ranges, not pretend to
    know the future.

The core guardrail:
    Atlas does not issue single-point price targets or action calls.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar


# ---------------------------------------------------------------------------
# Canonical enums
# ---------------------------------------------------------------------------


class ScenarioReviewType(str, Enum):
    """Canonical review type values."""

    HOLDING = "holding"
    PORTFOLIO = "portfolio"
    MIXED = "mixed"


class ScenarioSubjectType(str, Enum):
    """Canonical subject type values."""

    HOLDING = "holding"
    PORTFOLIO = "portfolio"
    WATCHLIST_ITEM = "watchlist_item"


class ScenarioTimeHorizon(str, Enum):
    """Canonical time horizon values.

    Short term: 1–3 months.
    Medium term: 6–12 months.
    Long term: 3–5 years.
    """

    SHORT_TERM = "short_term"
    MEDIUM_TERM = "medium_term"
    LONG_TERM = "long_term"


class ScenarioCaseType(str, Enum):
    """Canonical scenario case type values."""

    BEAR = "bear"
    BASE = "base"
    BULL = "bull"
    DOWNSIDE = "downside"
    UPSIDE = "upside"
    UNCERTAINTY_BAND = "uncertainty_band"


class ScenarioEvidenceQuality(str, Enum):
    """Canonical evidence quality values."""

    STRONG = "strong"
    ADEQUATE = "adequate"
    INCOMPLETE = "incomplete"
    WEAK = "weak"
    OUTDATED = "outdated"
    CONFLICTING = "conflicting"


class ScenarioConfidence(str, Enum):
    """Canonical confidence values.

    Describes confidence in the scenario structure and supporting evidence,
    not certainty about future returns.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class ScenarioAssumptionType(str, Enum):
    """Canonical assumption type values."""

    REVENUE_GROWTH = "revenue_growth"
    EARNINGS_GROWTH = "earnings_growth"
    MARGIN = "margin"
    VALUATION_MULTIPLE = "valuation_multiple"
    BALANCE_SHEET = "balance_sheet"
    CAPITAL_ALLOCATION = "capital_allocation"
    COMPETITIVE_POSITION = "competitive_position"
    BUSINESS_QUALITY = "business_quality"
    MARKET_SENTIMENT = "market_sentiment"
    MOMENTUM = "momentum"
    MACRO_RATE_SENSITIVITY = "macro_rate_sensitivity"
    CURRENCY = "currency"


class ScenarioDirection(str, Enum):
    """Canonical direction values for assumptions."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    MIXED = "mixed"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


class ScenarioEvidenceType(str, Enum):
    """Canonical evidence type values."""

    COMPANY_REPORT = "company_report"
    EARNINGS_CALL = "earnings_call"
    GUIDANCE = "guidance"
    FINANCIAL_HISTORY = "financial_history"
    RESEARCH_NOTE = "research_note"
    USER_NOTE = "user_note"
    MARKET_CONTEXT = "market_context"
    UNKNOWN = "unknown"


class ScenarioFreshness(str, Enum):
    """Canonical freshness values for evidence items."""

    CURRENT = "current"
    RECENT = "recent"
    STALE = "stale"
    UNKNOWN = "unknown"


class ScenarioChangeTriggerType(str, Enum):
    """Canonical change trigger type values."""

    EARNINGS_REPORT = "earnings_report"
    GUIDANCE_CHANGE = "guidance_change"
    REVENUE_GROWTH_ACCELERATION = "revenue_growth_acceleration"
    REVENUE_GROWTH_DECELERATION = "revenue_growth_deceleration"
    MARGIN_SURPRISE = "margin_surprise"
    VALUATION_MULTIPLE_EXPANSION = "valuation_multiple_expansion"
    VALUATION_MULTIPLE_COMPRESSION = "valuation_multiple_compression"
    BALANCE_SHEET_DETERIORATION = "balance_sheet_deterioration"
    BALANCE_SHEET_IMPROVEMENT = "balance_sheet_improvement"
    PRODUCT_OR_STRATEGY_UPDATE = "product_or_strategy_update"
    REGULATORY_CHANGE = "regulatory_change"
    MACRO_RATE_REGIME_CHANGE = "macro_rate_regime_change"
    CURRENCY_MOVEMENT = "currency_movement"
    THESIS_EVIDENCE_IMPROVED = "thesis_evidence_improved"
    THESIS_EVIDENCE_WEAKENED = "thesis_evidence_weakened"


class ScenarioExpectedEffect(str, Enum):
    """Canonical expected effect values for change triggers."""

    RANGE_MAY_EXPAND = "range_may_expand"
    RANGE_MAY_COMPRESS = "range_may_compress"
    RANGE_MAY_SHIFT_UP = "range_may_shift_up"
    RANGE_MAY_SHIFT_DOWN = "range_may_shift_down"
    CONFIDENCE_MAY_INCREASE = "confidence_may_increase"
    CONFIDENCE_MAY_DECREASE = "confidence_may_decrease"
    UNKNOWN = "unknown"


class ScenarioRangeImpactLevel(str, Enum):
    """Canonical range impact level values for portfolio contributions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    DOMINANT = "dominant"


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

EnumT = TypeVar("EnumT", bound=Enum)


def _require_non_empty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")


def _coerce_enum(value: EnumT | str | None, enum_type: type[EnumT], field_name: str) -> EnumT:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except (ValueError, KeyError) as exc:
        raise ValueError(
            f"{field_name} must be a valid {enum_type.__name__}: {value!r}"
        ) from exc


def _coerce_optional_enum(
    value: EnumT | str | None, enum_type: type[EnumT], field_name: str
) -> EnumT | None:
    if value is None:
        return None
    return _coerce_enum(value, enum_type, field_name)


def _list_of_strings(values: list[str], field_name: str) -> list[str]:
    if not isinstance(values, list):
        raise ValueError(f"{field_name} must be a list.")
    if not all(isinstance(item, str) for item in values):
        raise ValueError(f"{field_name} must contain only strings.")
    return list(values)


def _objects(
    values: list[Any], cls: type, field_name: str
) -> list[Any]:
    if not isinstance(values, list):
        raise ValueError(f"{field_name} must be a list.")
    result = []
    for item in values:
        if isinstance(item, cls):
            result.append(item)
        elif isinstance(item, dict):
            result.append(cls.from_dict(item))
        else:
            raise ValueError(f"{field_name} must contain {cls.__name__} objects or dicts.")
    return result


def _json_object(text: str, cls_name: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{cls_name}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{cls_name}: expected a JSON object, got {type(data).__name__}.")
    return data


# ---------------------------------------------------------------------------
# ScenarioSubject
# ---------------------------------------------------------------------------


@dataclass
class ScenarioSubject:
    """Identifies what is being reviewed in a Value Scenario Review."""

    subject_id: str
    subject_type: ScenarioSubjectType | str
    display_name: str
    ticker: str | None = None
    portfolio_id: str | None = None
    source_reference: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.subject_id, "ScenarioSubject.subject_id")
        self.subject_type = _coerce_enum(
            self.subject_type, ScenarioSubjectType, "ScenarioSubject.subject_type"
        ).value
        _require_non_empty(self.display_name, "ScenarioSubject.display_name")

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "subject_type": self.subject_type,
            "display_name": self.display_name,
            "ticker": self.ticker,
            "portfolio_id": self.portfolio_id,
            "source_reference": self.source_reference,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScenarioSubject":
        return cls(
            subject_id=data.get("subject_id", ""),
            subject_type=data.get("subject_type", ""),
            display_name=data.get("display_name", ""),
            ticker=data.get("ticker"),
            portfolio_id=data.get("portfolio_id"),
            source_reference=data.get("source_reference"),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "ScenarioSubject":
        return cls.from_dict(_json_object(text, "ScenarioSubject"))


# ---------------------------------------------------------------------------
# ScenarioRange
# ---------------------------------------------------------------------------


@dataclass
class ScenarioRange:
    """A single scenario range within a defined case and time horizon.

    lower_percent must be strictly less than upper_percent for forward-looking
    scenario outputs. Atlas does not issue single-point targets.
    """

    range_id: str
    horizon: ScenarioTimeHorizon | str
    case_type: ScenarioCaseType | str
    lower_percent: float
    upper_percent: float
    currency_basis: str | None = None
    assumption_ids: list[str] = field(default_factory=list)
    evidence_item_ids: list[str] = field(default_factory=list)
    confidence: ScenarioConfidence | str = ScenarioConfidence.UNKNOWN
    evidence_quality: ScenarioEvidenceQuality | str = ScenarioEvidenceQuality.INCOMPLETE
    uncertainty_note: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.range_id, "ScenarioRange.range_id")
        self.horizon = _coerce_enum(
            self.horizon, ScenarioTimeHorizon, "ScenarioRange.horizon"
        ).value
        self.case_type = _coerce_enum(
            self.case_type, ScenarioCaseType, "ScenarioRange.case_type"
        ).value
        if not isinstance(self.lower_percent, (int, float)):
            raise ValueError("ScenarioRange.lower_percent must be a number.")
        if not isinstance(self.upper_percent, (int, float)):
            raise ValueError("ScenarioRange.upper_percent must be a number.")
        if self.lower_percent >= self.upper_percent:
            raise ValueError(
                f"ScenarioRange.lower_percent ({self.lower_percent}) must be strictly less than "
                f"upper_percent ({self.upper_percent}). "
                "Atlas does not issue single-point targets or ranges with lower >= upper."
            )
        self.confidence = _coerce_enum(
            self.confidence, ScenarioConfidence, "ScenarioRange.confidence"
        ).value
        self.evidence_quality = _coerce_enum(
            self.evidence_quality, ScenarioEvidenceQuality, "ScenarioRange.evidence_quality"
        ).value
        self.assumption_ids = _list_of_strings(self.assumption_ids, "ScenarioRange.assumption_ids")
        self.evidence_item_ids = _list_of_strings(
            self.evidence_item_ids, "ScenarioRange.evidence_item_ids"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "range_id": self.range_id,
            "horizon": self.horizon,
            "case_type": self.case_type,
            "lower_percent": self.lower_percent,
            "upper_percent": self.upper_percent,
            "currency_basis": self.currency_basis,
            "assumption_ids": self.assumption_ids,
            "evidence_item_ids": self.evidence_item_ids,
            "confidence": self.confidence,
            "evidence_quality": self.evidence_quality,
            "uncertainty_note": self.uncertainty_note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScenarioRange":
        return cls(
            range_id=data.get("range_id", ""),
            horizon=data.get("horizon", ""),
            case_type=data.get("case_type", ""),
            lower_percent=data.get("lower_percent", 0.0),
            upper_percent=data.get("upper_percent", 0.0),
            currency_basis=data.get("currency_basis"),
            assumption_ids=data.get("assumption_ids", []),
            evidence_item_ids=data.get("evidence_item_ids", []),
            confidence=data.get("confidence", ScenarioConfidence.UNKNOWN.value),
            evidence_quality=data.get("evidence_quality", ScenarioEvidenceQuality.INCOMPLETE.value),
            uncertainty_note=data.get("uncertainty_note"),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "ScenarioRange":
        return cls.from_dict(_json_object(text, "ScenarioRange"))


# ---------------------------------------------------------------------------
# ScenarioAssumption
# ---------------------------------------------------------------------------


@dataclass
class ScenarioAssumption:
    """An assumption that grounds one or more scenario ranges."""

    assumption_id: str
    assumption_type: ScenarioAssumptionType | str
    description: str
    direction: ScenarioDirection | str = ScenarioDirection.UNKNOWN
    related_horizon: ScenarioTimeHorizon | str | None = None
    related_range_ids: list[str] = field(default_factory=list)
    evidence_item_ids: list[str] = field(default_factory=list)
    confidence: ScenarioConfidence | str = ScenarioConfidence.UNKNOWN

    def __post_init__(self) -> None:
        _require_non_empty(self.assumption_id, "ScenarioAssumption.assumption_id")
        self.assumption_type = _coerce_enum(
            self.assumption_type, ScenarioAssumptionType, "ScenarioAssumption.assumption_type"
        ).value
        _require_non_empty(self.description, "ScenarioAssumption.description")
        self.direction = _coerce_enum(
            self.direction, ScenarioDirection, "ScenarioAssumption.direction"
        ).value
        self.related_horizon = _coerce_optional_enum(
            self.related_horizon, ScenarioTimeHorizon, "ScenarioAssumption.related_horizon"
        )
        if self.related_horizon is not None:
            self.related_horizon = self.related_horizon.value
        self.related_range_ids = _list_of_strings(
            self.related_range_ids, "ScenarioAssumption.related_range_ids"
        )
        self.evidence_item_ids = _list_of_strings(
            self.evidence_item_ids, "ScenarioAssumption.evidence_item_ids"
        )
        self.confidence = _coerce_enum(
            self.confidence, ScenarioConfidence, "ScenarioAssumption.confidence"
        ).value

    def to_dict(self) -> dict[str, Any]:
        return {
            "assumption_id": self.assumption_id,
            "assumption_type": self.assumption_type,
            "description": self.description,
            "direction": self.direction,
            "related_horizon": self.related_horizon,
            "related_range_ids": self.related_range_ids,
            "evidence_item_ids": self.evidence_item_ids,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScenarioAssumption":
        return cls(
            assumption_id=data.get("assumption_id", ""),
            assumption_type=data.get("assumption_type", ""),
            description=data.get("description", ""),
            direction=data.get("direction", ScenarioDirection.UNKNOWN.value),
            related_horizon=data.get("related_horizon"),
            related_range_ids=data.get("related_range_ids", []),
            evidence_item_ids=data.get("evidence_item_ids", []),
            confidence=data.get("confidence", ScenarioConfidence.UNKNOWN.value),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "ScenarioAssumption":
        return cls.from_dict(_json_object(text, "ScenarioAssumption"))


# ---------------------------------------------------------------------------
# ScenarioEvidenceItem
# ---------------------------------------------------------------------------


@dataclass
class ScenarioEvidenceItem:
    """A piece of evidence supporting one or more scenario assumptions."""

    evidence_item_id: str
    evidence_type: ScenarioEvidenceType | str
    description: str
    source_reference: str | None = None
    evidence_quality: ScenarioEvidenceQuality | str = ScenarioEvidenceQuality.INCOMPLETE
    freshness: ScenarioFreshness | str = ScenarioFreshness.UNKNOWN
    related_assumption_ids: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require_non_empty(self.evidence_item_id, "ScenarioEvidenceItem.evidence_item_id")
        self.evidence_type = _coerce_enum(
            self.evidence_type, ScenarioEvidenceType, "ScenarioEvidenceItem.evidence_type"
        ).value
        _require_non_empty(self.description, "ScenarioEvidenceItem.description")
        self.evidence_quality = _coerce_enum(
            self.evidence_quality,
            ScenarioEvidenceQuality,
            "ScenarioEvidenceItem.evidence_quality",
        ).value
        self.freshness = _coerce_enum(
            self.freshness, ScenarioFreshness, "ScenarioEvidenceItem.freshness"
        ).value
        self.related_assumption_ids = _list_of_strings(
            self.related_assumption_ids, "ScenarioEvidenceItem.related_assumption_ids"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_item_id": self.evidence_item_id,
            "evidence_type": self.evidence_type,
            "description": self.description,
            "source_reference": self.source_reference,
            "evidence_quality": self.evidence_quality,
            "freshness": self.freshness,
            "related_assumption_ids": self.related_assumption_ids,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScenarioEvidenceItem":
        return cls(
            evidence_item_id=data.get("evidence_item_id", ""),
            evidence_type=data.get("evidence_type", ""),
            description=data.get("description", ""),
            source_reference=data.get("source_reference"),
            evidence_quality=data.get(
                "evidence_quality", ScenarioEvidenceQuality.INCOMPLETE.value
            ),
            freshness=data.get("freshness", ScenarioFreshness.UNKNOWN.value),
            related_assumption_ids=data.get("related_assumption_ids", []),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "ScenarioEvidenceItem":
        return cls.from_dict(_json_object(text, "ScenarioEvidenceItem"))


# ---------------------------------------------------------------------------
# ScenarioChangeTrigger
# ---------------------------------------------------------------------------


@dataclass
class ScenarioChangeTrigger:
    """An event that would cause a scenario range to be revised."""

    trigger_id: str
    trigger_type: ScenarioChangeTriggerType | str
    description: str
    expected_effect: ScenarioExpectedEffect | str = ScenarioExpectedEffect.UNKNOWN
    related_assumption_ids: list[str] = field(default_factory=list)
    related_range_ids: list[str] = field(default_factory=list)
    monitoring_note: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.trigger_id, "ScenarioChangeTrigger.trigger_id")
        self.trigger_type = _coerce_enum(
            self.trigger_type, ScenarioChangeTriggerType, "ScenarioChangeTrigger.trigger_type"
        ).value
        _require_non_empty(self.description, "ScenarioChangeTrigger.description")
        self.expected_effect = _coerce_enum(
            self.expected_effect, ScenarioExpectedEffect, "ScenarioChangeTrigger.expected_effect"
        ).value
        self.related_assumption_ids = _list_of_strings(
            self.related_assumption_ids, "ScenarioChangeTrigger.related_assumption_ids"
        )
        self.related_range_ids = _list_of_strings(
            self.related_range_ids, "ScenarioChangeTrigger.related_range_ids"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "trigger_id": self.trigger_id,
            "trigger_type": self.trigger_type,
            "description": self.description,
            "expected_effect": self.expected_effect,
            "related_assumption_ids": self.related_assumption_ids,
            "related_range_ids": self.related_range_ids,
            "monitoring_note": self.monitoring_note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScenarioChangeTrigger":
        return cls(
            trigger_id=data.get("trigger_id", ""),
            trigger_type=data.get("trigger_type", ""),
            description=data.get("description", ""),
            expected_effect=data.get("expected_effect", ScenarioExpectedEffect.UNKNOWN.value),
            related_assumption_ids=data.get("related_assumption_ids", []),
            related_range_ids=data.get("related_range_ids", []),
            monitoring_note=data.get("monitoring_note"),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "ScenarioChangeTrigger":
        return cls.from_dict(_json_object(text, "ScenarioChangeTrigger"))


# ---------------------------------------------------------------------------
# ScenarioRevision
# ---------------------------------------------------------------------------


@dataclass
class ScenarioRevision:
    """A record of what changed in a scenario and why."""

    revision_id: str
    revised_at: str
    reason: str
    previous_range_ids: list[str] = field(default_factory=list)
    updated_range_ids: list[str] = field(default_factory=list)
    trigger_ids: list[str] = field(default_factory=list)
    changed_assumption_ids: list[str] = field(default_factory=list)
    evidence_item_ids: list[str] = field(default_factory=list)
    revision_note: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.revision_id, "ScenarioRevision.revision_id")
        _require_non_empty(self.revised_at, "ScenarioRevision.revised_at")
        _require_non_empty(self.reason, "ScenarioRevision.reason")
        self.previous_range_ids = _list_of_strings(
            self.previous_range_ids, "ScenarioRevision.previous_range_ids"
        )
        self.updated_range_ids = _list_of_strings(
            self.updated_range_ids, "ScenarioRevision.updated_range_ids"
        )
        self.trigger_ids = _list_of_strings(self.trigger_ids, "ScenarioRevision.trigger_ids")
        self.changed_assumption_ids = _list_of_strings(
            self.changed_assumption_ids, "ScenarioRevision.changed_assumption_ids"
        )
        self.evidence_item_ids = _list_of_strings(
            self.evidence_item_ids, "ScenarioRevision.evidence_item_ids"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "revision_id": self.revision_id,
            "revised_at": self.revised_at,
            "reason": self.reason,
            "previous_range_ids": self.previous_range_ids,
            "updated_range_ids": self.updated_range_ids,
            "trigger_ids": self.trigger_ids,
            "changed_assumption_ids": self.changed_assumption_ids,
            "evidence_item_ids": self.evidence_item_ids,
            "revision_note": self.revision_note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScenarioRevision":
        return cls(
            revision_id=data.get("revision_id", ""),
            revised_at=data.get("revised_at", ""),
            reason=data.get("reason", ""),
            previous_range_ids=data.get("previous_range_ids", []),
            updated_range_ids=data.get("updated_range_ids", []),
            trigger_ids=data.get("trigger_ids", []),
            changed_assumption_ids=data.get("changed_assumption_ids", []),
            evidence_item_ids=data.get("evidence_item_ids", []),
            revision_note=data.get("revision_note"),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "ScenarioRevision":
        return cls.from_dict(_json_object(text, "ScenarioRevision"))


# ---------------------------------------------------------------------------
# PortfolioContribution
# ---------------------------------------------------------------------------


@dataclass
class PortfolioContribution:
    """A single holding's contribution to a portfolio scenario."""

    contribution_id: str
    holding_id: str
    display_name: str
    ticker: str | None = None
    portfolio_weight: float | None = None
    contribution_to_range: str | None = None
    range_impact_level: ScenarioRangeImpactLevel | str = ScenarioRangeImpactLevel.MEDIUM
    key_reason: str | None = None
    evidence_quality: ScenarioEvidenceQuality | str = ScenarioEvidenceQuality.INCOMPLETE

    def __post_init__(self) -> None:
        _require_non_empty(self.contribution_id, "PortfolioContribution.contribution_id")
        _require_non_empty(self.holding_id, "PortfolioContribution.holding_id")
        _require_non_empty(self.display_name, "PortfolioContribution.display_name")
        if self.portfolio_weight is not None and not isinstance(
            self.portfolio_weight, (int, float)
        ):
            raise ValueError("PortfolioContribution.portfolio_weight must be a number or null.")
        self.range_impact_level = _coerce_enum(
            self.range_impact_level,
            ScenarioRangeImpactLevel,
            "PortfolioContribution.range_impact_level",
        ).value
        self.evidence_quality = _coerce_enum(
            self.evidence_quality,
            ScenarioEvidenceQuality,
            "PortfolioContribution.evidence_quality",
        ).value

    def to_dict(self) -> dict[str, Any]:
        return {
            "contribution_id": self.contribution_id,
            "holding_id": self.holding_id,
            "display_name": self.display_name,
            "ticker": self.ticker,
            "portfolio_weight": self.portfolio_weight,
            "contribution_to_range": self.contribution_to_range,
            "range_impact_level": self.range_impact_level,
            "key_reason": self.key_reason,
            "evidence_quality": self.evidence_quality,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PortfolioContribution":
        return cls(
            contribution_id=data.get("contribution_id", ""),
            holding_id=data.get("holding_id", ""),
            display_name=data.get("display_name", ""),
            ticker=data.get("ticker"),
            portfolio_weight=data.get("portfolio_weight"),
            contribution_to_range=data.get("contribution_to_range"),
            range_impact_level=data.get(
                "range_impact_level", ScenarioRangeImpactLevel.MEDIUM.value
            ),
            key_reason=data.get("key_reason"),
            evidence_quality=data.get(
                "evidence_quality", ScenarioEvidenceQuality.INCOMPLETE.value
            ),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "PortfolioContribution":
        return cls.from_dict(_json_object(text, "PortfolioContribution"))


# ---------------------------------------------------------------------------
# HoldingScenario
# ---------------------------------------------------------------------------


@dataclass
class HoldingScenario:
    """Scenario review for a single holding."""

    holding_scenario_id: str
    subject: ScenarioSubject | dict[str, Any]
    ranges: list[ScenarioRange | dict[str, Any]] = field(default_factory=list)
    key_drivers: list[str] = field(default_factory=list)
    key_risks: list[str] = field(default_factory=list)
    assumption_ids: list[str] = field(default_factory=list)
    evidence_quality: ScenarioEvidenceQuality | str = ScenarioEvidenceQuality.INCOMPLETE
    confidence: ScenarioConfidence | str = ScenarioConfidence.UNKNOWN
    change_trigger_ids: list[str] = field(default_factory=list)
    revision_ids: list[str] = field(default_factory=list)
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.holding_scenario_id, "HoldingScenario.holding_scenario_id")
        if isinstance(self.subject, dict):
            self.subject = ScenarioSubject.from_dict(self.subject)
        self.ranges = _objects(self.ranges, ScenarioRange, "HoldingScenario.ranges")
        self.key_drivers = _list_of_strings(self.key_drivers, "HoldingScenario.key_drivers")
        self.key_risks = _list_of_strings(self.key_risks, "HoldingScenario.key_risks")
        self.assumption_ids = _list_of_strings(
            self.assumption_ids, "HoldingScenario.assumption_ids"
        )
        self.evidence_quality = _coerce_enum(
            self.evidence_quality, ScenarioEvidenceQuality, "HoldingScenario.evidence_quality"
        ).value
        self.confidence = _coerce_enum(
            self.confidence, ScenarioConfidence, "HoldingScenario.confidence"
        ).value
        self.change_trigger_ids = _list_of_strings(
            self.change_trigger_ids, "HoldingScenario.change_trigger_ids"
        )
        self.revision_ids = _list_of_strings(self.revision_ids, "HoldingScenario.revision_ids")

    def to_dict(self) -> dict[str, Any]:
        return {
            "holding_scenario_id": self.holding_scenario_id,
            "subject": self.subject.to_dict() if isinstance(self.subject, ScenarioSubject) else self.subject,
            "ranges": [r.to_dict() if isinstance(r, ScenarioRange) else r for r in self.ranges],
            "key_drivers": self.key_drivers,
            "key_risks": self.key_risks,
            "assumption_ids": self.assumption_ids,
            "evidence_quality": self.evidence_quality,
            "confidence": self.confidence,
            "change_trigger_ids": self.change_trigger_ids,
            "revision_ids": self.revision_ids,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HoldingScenario":
        return cls(
            holding_scenario_id=data.get("holding_scenario_id", ""),
            subject=data.get("subject", {}),
            ranges=data.get("ranges", []),
            key_drivers=data.get("key_drivers", []),
            key_risks=data.get("key_risks", []),
            assumption_ids=data.get("assumption_ids", []),
            evidence_quality=data.get(
                "evidence_quality", ScenarioEvidenceQuality.INCOMPLETE.value
            ),
            confidence=data.get("confidence", ScenarioConfidence.UNKNOWN.value),
            change_trigger_ids=data.get("change_trigger_ids", []),
            revision_ids=data.get("revision_ids", []),
            notes=data.get("notes"),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "HoldingScenario":
        return cls.from_dict(_json_object(text, "HoldingScenario"))


# ---------------------------------------------------------------------------
# PortfolioScenario
# ---------------------------------------------------------------------------


@dataclass
class PortfolioScenario:
    """Scenario review at portfolio level."""

    portfolio_scenario_id: str
    portfolio_id: str
    ranges: list[ScenarioRange | dict[str, Any]] = field(default_factory=list)
    weighted_contributions: list[PortfolioContribution | dict[str, Any]] = field(
        default_factory=list
    )
    main_upside_drivers: list[str] = field(default_factory=list)
    main_downside_drivers: list[str] = field(default_factory=list)
    concentration_sensitivity: str | None = None
    valuation_sensitivity: str | None = None
    evidence_gaps: list[str] = field(default_factory=list)
    holdings_requiring_review: list[str] = field(default_factory=list)
    confidence: ScenarioConfidence | str = ScenarioConfidence.UNKNOWN
    evidence_quality: ScenarioEvidenceQuality | str = ScenarioEvidenceQuality.INCOMPLETE

    def __post_init__(self) -> None:
        _require_non_empty(self.portfolio_scenario_id, "PortfolioScenario.portfolio_scenario_id")
        _require_non_empty(self.portfolio_id, "PortfolioScenario.portfolio_id")
        self.ranges = _objects(self.ranges, ScenarioRange, "PortfolioScenario.ranges")
        self.weighted_contributions = _objects(
            self.weighted_contributions,
            PortfolioContribution,
            "PortfolioScenario.weighted_contributions",
        )
        self.main_upside_drivers = _list_of_strings(
            self.main_upside_drivers, "PortfolioScenario.main_upside_drivers"
        )
        self.main_downside_drivers = _list_of_strings(
            self.main_downside_drivers, "PortfolioScenario.main_downside_drivers"
        )
        self.evidence_gaps = _list_of_strings(
            self.evidence_gaps, "PortfolioScenario.evidence_gaps"
        )
        self.holdings_requiring_review = _list_of_strings(
            self.holdings_requiring_review, "PortfolioScenario.holdings_requiring_review"
        )
        self.confidence = _coerce_enum(
            self.confidence, ScenarioConfidence, "PortfolioScenario.confidence"
        ).value
        self.evidence_quality = _coerce_enum(
            self.evidence_quality, ScenarioEvidenceQuality, "PortfolioScenario.evidence_quality"
        ).value

    def to_dict(self) -> dict[str, Any]:
        return {
            "portfolio_scenario_id": self.portfolio_scenario_id,
            "portfolio_id": self.portfolio_id,
            "ranges": [r.to_dict() if isinstance(r, ScenarioRange) else r for r in self.ranges],
            "weighted_contributions": [
                c.to_dict() if isinstance(c, PortfolioContribution) else c
                for c in self.weighted_contributions
            ],
            "main_upside_drivers": self.main_upside_drivers,
            "main_downside_drivers": self.main_downside_drivers,
            "concentration_sensitivity": self.concentration_sensitivity,
            "valuation_sensitivity": self.valuation_sensitivity,
            "evidence_gaps": self.evidence_gaps,
            "holdings_requiring_review": self.holdings_requiring_review,
            "confidence": self.confidence,
            "evidence_quality": self.evidence_quality,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PortfolioScenario":
        return cls(
            portfolio_scenario_id=data.get("portfolio_scenario_id", ""),
            portfolio_id=data.get("portfolio_id", ""),
            ranges=data.get("ranges", []),
            weighted_contributions=data.get("weighted_contributions", []),
            main_upside_drivers=data.get("main_upside_drivers", []),
            main_downside_drivers=data.get("main_downside_drivers", []),
            concentration_sensitivity=data.get("concentration_sensitivity"),
            valuation_sensitivity=data.get("valuation_sensitivity"),
            evidence_gaps=data.get("evidence_gaps", []),
            holdings_requiring_review=data.get("holdings_requiring_review", []),
            confidence=data.get("confidence", ScenarioConfidence.UNKNOWN.value),
            evidence_quality=data.get(
                "evidence_quality", ScenarioEvidenceQuality.INCOMPLETE.value
            ),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "PortfolioScenario":
        return cls.from_dict(_json_object(text, "PortfolioScenario"))


# ---------------------------------------------------------------------------
# ScenarioSafetyBoundary
# ---------------------------------------------------------------------------


@dataclass
class ScenarioSafetyBoundary:
    """Enforces Atlas's non-negotiable scenario guardrails.

    All fields must remain True. Setting any field to False raises ValueError.
    """

    no_single_point_targets: bool = True
    no_action_calls: bool = True
    no_execution_instructions: bool = True
    no_prediction_certainty: bool = True
    assumptions_required: bool = True
    evidence_quality_required: bool = True
    uncertainty_required: bool = True
    change_triggers_required: bool = True

    def __post_init__(self) -> None:
        _SAFETY_FIELDS = [
            "no_single_point_targets",
            "no_action_calls",
            "no_execution_instructions",
            "no_prediction_certainty",
            "assumptions_required",
            "evidence_quality_required",
            "uncertainty_required",
            "change_triggers_required",
        ]
        for fname in _SAFETY_FIELDS:
            val = getattr(self, fname)
            if not isinstance(val, bool):
                raise ValueError(f"ScenarioSafetyBoundary.{fname} must be a boolean.")
            if not val:
                raise ValueError(
                    f"ScenarioSafetyBoundary.{fname} must be True. "
                    "Atlas safety boundary fields may not be disabled."
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "no_single_point_targets": self.no_single_point_targets,
            "no_action_calls": self.no_action_calls,
            "no_execution_instructions": self.no_execution_instructions,
            "no_prediction_certainty": self.no_prediction_certainty,
            "assumptions_required": self.assumptions_required,
            "evidence_quality_required": self.evidence_quality_required,
            "uncertainty_required": self.uncertainty_required,
            "change_triggers_required": self.change_triggers_required,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScenarioSafetyBoundary":
        return cls(
            no_single_point_targets=data.get("no_single_point_targets", True),
            no_action_calls=data.get("no_action_calls", True),
            no_execution_instructions=data.get("no_execution_instructions", True),
            no_prediction_certainty=data.get("no_prediction_certainty", True),
            assumptions_required=data.get("assumptions_required", True),
            evidence_quality_required=data.get("evidence_quality_required", True),
            uncertainty_required=data.get("uncertainty_required", True),
            change_triggers_required=data.get("change_triggers_required", True),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "ScenarioSafetyBoundary":
        return cls.from_dict(_json_object(text, "ScenarioSafetyBoundary"))


# ---------------------------------------------------------------------------
# ValueScenarioReview
# ---------------------------------------------------------------------------


@dataclass
class ValueScenarioReview:
    """Top-level Value Scenario Review object.

    Represents a complete scenario review session including holding-level and/or
    portfolio-level scenarios, assumptions, evidence items, change triggers,
    revisions, and the safety boundary.
    """

    scenario_review_id: str
    review_type: ScenarioReviewType | str
    created_at: str
    subject: ScenarioSubject | dict[str, Any]
    time_horizons: list[ScenarioTimeHorizon | str] = field(default_factory=list)
    holding_scenarios: list[HoldingScenario | dict[str, Any]] = field(default_factory=list)
    portfolio_scenario: PortfolioScenario | dict[str, Any] | None = None
    assumptions: list[ScenarioAssumption | dict[str, Any]] = field(default_factory=list)
    evidence_items: list[ScenarioEvidenceItem | dict[str, Any]] = field(default_factory=list)
    change_triggers: list[ScenarioChangeTrigger | dict[str, Any]] = field(default_factory=list)
    revisions: list[ScenarioRevision | dict[str, Any]] = field(default_factory=list)
    safety_boundary: ScenarioSafetyBoundary | dict[str, Any] = field(
        default_factory=ScenarioSafetyBoundary
    )

    def __post_init__(self) -> None:
        _require_non_empty(self.scenario_review_id, "ValueScenarioReview.scenario_review_id")
        self.review_type = _coerce_enum(
            self.review_type, ScenarioReviewType, "ValueScenarioReview.review_type"
        ).value
        _require_non_empty(self.created_at, "ValueScenarioReview.created_at")
        if isinstance(self.subject, dict):
            self.subject = ScenarioSubject.from_dict(self.subject)

        # Coerce time horizons
        coerced_horizons = []
        for i, h in enumerate(self.time_horizons):
            coerced_horizons.append(
                _coerce_enum(h, ScenarioTimeHorizon, f"ValueScenarioReview.time_horizons[{i}]").value
            )
        self.time_horizons = coerced_horizons

        self.holding_scenarios = _objects(
            self.holding_scenarios, HoldingScenario, "ValueScenarioReview.holding_scenarios"
        )

        if isinstance(self.portfolio_scenario, dict):
            self.portfolio_scenario = PortfolioScenario.from_dict(self.portfolio_scenario)

        self.assumptions = _objects(
            self.assumptions, ScenarioAssumption, "ValueScenarioReview.assumptions"
        )
        self.evidence_items = _objects(
            self.evidence_items, ScenarioEvidenceItem, "ValueScenarioReview.evidence_items"
        )
        self.change_triggers = _objects(
            self.change_triggers, ScenarioChangeTrigger, "ValueScenarioReview.change_triggers"
        )
        self.revisions = _objects(
            self.revisions, ScenarioRevision, "ValueScenarioReview.revisions"
        )

        if isinstance(self.safety_boundary, dict):
            self.safety_boundary = ScenarioSafetyBoundary.from_dict(self.safety_boundary)

        # Structural review type consistency
        if self.review_type == ScenarioReviewType.HOLDING.value and not self.holding_scenarios:
            raise ValueError(
                "ValueScenarioReview: review_type 'holding' requires at least one holding_scenario."
            )
        if self.review_type == ScenarioReviewType.PORTFOLIO.value and self.portfolio_scenario is None:
            raise ValueError(
                "ValueScenarioReview: review_type 'portfolio' requires a portfolio_scenario."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_review_id": self.scenario_review_id,
            "review_type": self.review_type,
            "created_at": self.created_at,
            "subject": self.subject.to_dict() if isinstance(self.subject, ScenarioSubject) else self.subject,
            "time_horizons": list(self.time_horizons),
            "holding_scenarios": [
                h.to_dict() if isinstance(h, HoldingScenario) else h
                for h in self.holding_scenarios
            ],
            "portfolio_scenario": (
                self.portfolio_scenario.to_dict()
                if isinstance(self.portfolio_scenario, PortfolioScenario)
                else self.portfolio_scenario
            ),
            "assumptions": [
                a.to_dict() if isinstance(a, ScenarioAssumption) else a
                for a in self.assumptions
            ],
            "evidence_items": [
                e.to_dict() if isinstance(e, ScenarioEvidenceItem) else e
                for e in self.evidence_items
            ],
            "change_triggers": [
                t.to_dict() if isinstance(t, ScenarioChangeTrigger) else t
                for t in self.change_triggers
            ],
            "revisions": [
                r.to_dict() if isinstance(r, ScenarioRevision) else r
                for r in self.revisions
            ],
            "safety_boundary": (
                self.safety_boundary.to_dict()
                if isinstance(self.safety_boundary, ScenarioSafetyBoundary)
                else self.safety_boundary
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ValueScenarioReview":
        return cls(
            scenario_review_id=data.get("scenario_review_id", ""),
            review_type=data.get("review_type", ""),
            created_at=data.get("created_at", ""),
            subject=data.get("subject", {}),
            time_horizons=data.get("time_horizons", []),
            holding_scenarios=data.get("holding_scenarios", []),
            portfolio_scenario=data.get("portfolio_scenario"),
            assumptions=data.get("assumptions", []),
            evidence_items=data.get("evidence_items", []),
            change_triggers=data.get("change_triggers", []),
            revisions=data.get("revisions", []),
            safety_boundary=data.get("safety_boundary", {}),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "ValueScenarioReview":
        data = _json_object(text, "ValueScenarioReview")
        return cls.from_dict(data)
