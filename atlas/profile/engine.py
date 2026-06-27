import json
from dataclasses import asdict, dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any


class InvestmentGoal(str, Enum):
    WEALTH_ACCUMULATION = "Wealth accumulation"
    RETIREMENT = "Retirement"
    INCOME = "Income"
    FINANCIAL_INDEPENDENCE = "Financial Independence"
    CAPITAL_PRESERVATION = "Capital Preservation"
    LEARNING = "Learning"
    EXPERIMENTAL_PORTFOLIO = "Experimental Portfolio"


class PortfolioPurpose(str, Enum):
    CORE_PORTFOLIO = "Core Portfolio"
    GROWTH_PORTFOLIO = "Growth Portfolio"
    INCOME_PORTFOLIO = "Income Portfolio"
    EXPLORATION_PORTFOLIO = "Exploration Portfolio"
    HIGH_CONVICTION_PORTFOLIO = "High Conviction Portfolio"


class RiskPreference(str, Enum):
    CONSERVATIVE = "Conservative"
    BALANCED = "Balanced"
    GROWTH = "Growth"
    AGGRESSIVE = "Aggressive"


class RiskTolerance(str, Enum):
    CONSERVATIVE = "Conservative"
    BALANCED = "Balanced"
    GROWTH = "Growth"
    AGGRESSIVE = "Aggressive"


class RiskCapacity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class TimeHorizon(str, Enum):
    SHORT = "<3 years"
    MEDIUM = "3-10 years"
    LONG = "10+ years"


@dataclass(frozen=True)
class InvestorProfile:
    name: str
    investment_goals: tuple[InvestmentGoal, ...]
    portfolio_purpose: PortfolioPurpose
    risk_preference: RiskPreference
    risk_tolerance: RiskTolerance
    risk_capacity: RiskCapacity
    time_horizon: TimeHorizon
    notes: str = ""


@dataclass(frozen=True)
class InvestorContext:
    investment_goals: tuple[str, ...]
    portfolio_purpose: str
    risk_profile: str
    risk_capacity: str
    risk_tolerance: str
    time_horizon: str
    capital_safety_context: str
    reasoning_context: tuple[str, ...]


class InvestorProfileEngine:
    def create_default_profile(self, name: str = "Atlas Investor") -> InvestorProfile:
        return InvestorProfile(
            name=name,
            investment_goals=(InvestmentGoal.WEALTH_ACCUMULATION,),
            portfolio_purpose=PortfolioPurpose.CORE_PORTFOLIO,
            risk_preference=RiskPreference.BALANCED,
            risk_tolerance=RiskTolerance.BALANCED,
            risk_capacity=RiskCapacity.MEDIUM,
            time_horizon=TimeHorizon.LONG,
            notes="Default deterministic investor context. Update before relying on fit.",
        )

    def create_profile(
        self,
        name: str,
        investment_goals: tuple[InvestmentGoal, ...],
        portfolio_purpose: PortfolioPurpose,
        risk_preference: RiskPreference,
        risk_tolerance: RiskTolerance,
        risk_capacity: RiskCapacity,
        time_horizon: TimeHorizon,
        notes: str = "",
    ) -> InvestorProfile:
        if not investment_goals:
            raise ValueError("Investor profile requires at least one investment goal.")
        return InvestorProfile(
            name=name.strip() or "Atlas Investor",
            investment_goals=investment_goals,
            portfolio_purpose=portfolio_purpose,
            risk_preference=risk_preference,
            risk_tolerance=risk_tolerance,
            risk_capacity=risk_capacity,
            time_horizon=time_horizon,
            notes=notes,
        )

    def update_profile(
        self,
        profile: InvestorProfile,
        name: str | None = None,
        investment_goals: tuple[InvestmentGoal, ...] | None = None,
        portfolio_purpose: PortfolioPurpose | None = None,
        risk_preference: RiskPreference | None = None,
        risk_tolerance: RiskTolerance | None = None,
        risk_capacity: RiskCapacity | None = None,
        time_horizon: TimeHorizon | None = None,
        notes: str | None = None,
    ) -> InvestorProfile:
        if investment_goals == ():
            raise ValueError("Investor profile requires at least one investment goal.")
        return replace(
            profile,
            name=(name.strip() or profile.name) if name is not None else profile.name,
            investment_goals=investment_goals or profile.investment_goals,
            portfolio_purpose=portfolio_purpose or profile.portfolio_purpose,
            risk_preference=risk_preference or profile.risk_preference,
            risk_tolerance=risk_tolerance or profile.risk_tolerance,
            risk_capacity=risk_capacity or profile.risk_capacity,
            time_horizon=time_horizon or profile.time_horizon,
            notes=notes if notes is not None else profile.notes,
        )

    def investor_context(self, profile: InvestorProfile) -> InvestorContext:
        return InvestorContext(
            investment_goals=tuple(goal.value for goal in profile.investment_goals),
            portfolio_purpose=profile.portfolio_purpose.value,
            risk_profile=profile.risk_preference.value,
            risk_capacity=profile.risk_capacity.value,
            risk_tolerance=profile.risk_tolerance.value,
            time_horizon=profile.time_horizon.value,
            capital_safety_context=_capital_safety_context(profile),
            reasoning_context=_reasoning_context(profile),
        )

    def save_profile(self, profile: InvestorProfile, path: Path) -> InvestorProfile:
        payload = _profile_to_mapping(profile)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return profile

    def load_profile(self, path: Path) -> InvestorProfile:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        if not isinstance(payload, dict):
            raise ValueError("Investor profile JSON must contain an object.")
        return profile_from_mapping(payload)


def profile_from_mapping(payload: dict[str, Any]) -> InvestorProfile:
    try:
        raw_goals = payload["investment_goals"]
        if not isinstance(raw_goals, list) or not raw_goals:
            raise ValueError("investment_goals must be a non-empty list.")
        return InvestorProfile(
            name=str(payload.get("name", "Atlas Investor")),
            investment_goals=tuple(
                _parse_enum(InvestmentGoal, str(goal)) for goal in raw_goals
            ),
            portfolio_purpose=_parse_enum(
                PortfolioPurpose,
                str(payload["portfolio_purpose"]),
            ),
            risk_preference=_parse_enum(
                RiskPreference,
                str(payload["risk_preference"]),
            ),
            risk_tolerance=_parse_enum(
                RiskTolerance,
                str(payload["risk_tolerance"]),
            ),
            risk_capacity=_parse_enum(
                RiskCapacity,
                str(payload["risk_capacity"]),
            ),
            time_horizon=_parse_enum(TimeHorizon, str(payload["time_horizon"])),
            notes=str(payload.get("notes", "")),
        )
    except KeyError as exc:
        message = f"Investor profile is missing required field: {exc.args[0]}"
        raise ValueError(message) from exc


def render_investor_profile(profile: InvestorProfile) -> str:
    context = InvestorProfileEngine().investor_context(profile)
    lines = [
        "Investor Profile",
        "",
        f"Name: {profile.name}",
        f"Investment Goals: {', '.join(context.investment_goals)}",
        f"Portfolio Purpose: {context.portfolio_purpose}",
        f"Risk Profile: {context.risk_profile}",
        f"Risk Tolerance: {context.risk_tolerance}",
        f"Risk Capacity: {context.risk_capacity}",
        f"Time Horizon: {context.time_horizon}",
        f"Capital Safety Context: {context.capital_safety_context}",
        "",
        "Investor Context",
        *_render_list(context.reasoning_context),
        "",
        "Notes",
        profile.notes or "None",
        "",
        "Research Framing",
        "This establishes investor context only. It is not financial advice.",
    ]
    return "\n".join(lines)


def _profile_to_mapping(profile: InvestorProfile) -> dict[str, Any]:
    payload = asdict(profile)
    payload["investment_goals"] = [goal.value for goal in profile.investment_goals]
    payload["portfolio_purpose"] = profile.portfolio_purpose.value
    payload["risk_preference"] = profile.risk_preference.value
    payload["risk_tolerance"] = profile.risk_tolerance.value
    payload["risk_capacity"] = profile.risk_capacity.value
    payload["time_horizon"] = profile.time_horizon.value
    return payload


def _parse_enum(enum_type, raw_value: str):
    normalized = raw_value.strip().lower().replace("_", " ").replace("-", " ")
    for item in enum_type:
        if normalized in {
            item.name.lower().replace("_", " "),
            item.value.lower().replace("-", " "),
        }:
            return item
    valid = ", ".join(item.value for item in enum_type)
    raise ValueError(f"Unknown {enum_type.__name__}: {raw_value}. Valid values: {valid}")


def _capital_safety_context(profile: InvestorProfile) -> str:
    if profile.time_horizon == TimeHorizon.SHORT:
        return "Short horizon: preserve liquidity and avoid long-duration risk assumptions."
    if profile.risk_capacity == RiskCapacity.LOW:
        return "Low risk capacity: prioritize resilience and capital safety context."
    return "Investment capital should remain separate from short-term liquidity needs."


def _reasoning_context(profile: InvestorProfile) -> tuple[str, ...]:
    return (
        f"Goals: {', '.join(goal.value for goal in profile.investment_goals)}.",
        f"Portfolio purpose: {profile.portfolio_purpose.value}.",
        f"Risk preference: {profile.risk_preference.value}.",
        f"Risk capacity: {profile.risk_capacity.value}.",
        f"Time horizon: {profile.time_horizon.value}.",
    )


def _render_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]
