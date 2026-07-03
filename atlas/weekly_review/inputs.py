"""Local input loading for the Atlas Weekly Investment Review workflow.

Loads and validates the portfolio, watchlist, investor profile, decision
journal, and optional evidence inputs from local files.  No network calls,
no provider dependency, no database writes.

Supports:
  - Portfolio: existing positions[] format and v1 extended accounts[] format
  - Watchlist: v1 rich item format (status, evidence_needed, open_questions, ...)
  - Investor profile: existing InvestorProfileEngine.load_profile
  - Decision journal: reads entry count from existing .atlas/decision_journal.json
  - Company facts directory: existence check only
  - Financials directory: existence check only
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Watchlist types
# ---------------------------------------------------------------------------


class WeeklyReviewWatchlistStatus(str, Enum):
    """Allowed watchlist item statuses for the Weekly Investment Review."""

    RESEARCH = "Research"
    WATCHLIST = "Watchlist"
    NEEDS_MORE_EVIDENCE = "Needs More Evidence"
    SUITABLE_FOR_FURTHER_REVIEW = "Suitable for Further Review"
    NOT_SUITABLE_UNDER_CURRENT_CONSTRAINTS = "Not Suitable Under Current Constraints"
    DECISION_DEFERRED = "Decision Deferred"


_STATUS_ALIASES: dict[str, WeeklyReviewWatchlistStatus] = {
    s.value.lower(): s for s in WeeklyReviewWatchlistStatus
} | {
    # legacy watchlist_intelligence statuses mapped to v1 statuses
    "observing": WeeklyReviewWatchlistStatus.WATCHLIST,
    "researching": WeeklyReviewWatchlistStatus.RESEARCH,
    "needs_more_evidence": WeeklyReviewWatchlistStatus.NEEDS_MORE_EVIDENCE,
    "thesis_forming": WeeklyReviewWatchlistStatus.RESEARCH,
    "ready_for_review": WeeklyReviewWatchlistStatus.SUITABLE_FOR_FURTHER_REVIEW,
    "paused": WeeklyReviewWatchlistStatus.WATCHLIST,
    "archived": WeeklyReviewWatchlistStatus.WATCHLIST,
}


@dataclass(frozen=True)
class WeeklyReviewWatchlistItem:
    """One item in a Weekly Review watchlist input."""

    ticker: str
    name: str
    status: WeeklyReviewWatchlistStatus
    reason: str
    evidence_needed: tuple[str, ...]
    open_questions: tuple[str, ...]
    manual_observations: tuple[str, ...]
    notes: str


@dataclass(frozen=True)
class WeeklyReviewWatchlistInput:
    """Parsed v1 watchlist input for the Weekly Investment Review."""

    name: str
    as_of: str
    items: tuple[WeeklyReviewWatchlistItem, ...]

    @classmethod
    def from_json_file(
        cls, path: Path
    ) -> tuple["WeeklyReviewWatchlistInput", list["WeeklyReviewInputWarning"]]:
        """Load and parse the v1 watchlist JSON file.

        Returns (watchlist, warnings).  Raises ValueError on structural
        errors (missing required fields, empty items list).
        """
        with path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            raise ValueError(f"Watchlist file must contain a JSON object: {path}")
        return cls.from_mapping(payload)

    @classmethod
    def from_mapping(
        cls, payload: dict[str, Any]
    ) -> tuple["WeeklyReviewWatchlistInput", list["WeeklyReviewInputWarning"]]:
        """Parse a watchlist mapping (dict).  Returns (watchlist, warnings)."""
        warnings: list[WeeklyReviewInputWarning] = []
        name = str(payload.get("name", "Watchlist")).strip() or "Watchlist"
        as_of = str(payload.get("as_of", "")).strip()

        raw_items = payload.get("items")
        if not isinstance(raw_items, list) or not raw_items:
            raise ValueError(
                "Watchlist JSON must contain a non-empty 'items' list.  "
                "Each item must have at least a 'ticker' field."
            )

        items: list[WeeklyReviewWatchlistItem] = []
        for idx, raw in enumerate(raw_items):
            item, item_warnings = _watchlist_item_from_mapping(raw, idx)
            items.append(item)
            warnings.extend(item_warnings)

        return (
            cls(name=name, as_of=as_of, items=tuple(items)),
            warnings,
        )


def _watchlist_item_from_mapping(
    payload: Any, idx: int
) -> tuple[WeeklyReviewWatchlistItem, list["WeeklyReviewInputWarning"]]:
    if not isinstance(payload, dict):
        raise ValueError(f"Watchlist item at index {idx} must be a JSON object.")
    warnings: list[WeeklyReviewInputWarning] = []

    ticker = str(payload.get("ticker", "")).strip().upper()
    if not ticker:
        raise ValueError(
            f"Watchlist item at index {idx} is missing required field 'ticker'."
        )

    name = str(payload.get("name", ticker)).strip() or ticker

    raw_status = str(payload.get("status", "")).strip()
    status = _STATUS_ALIASES.get(raw_status.lower())
    if status is None:
        if raw_status:
            warnings.append(
                WeeklyReviewInputWarning(
                    code="unknown_watchlist_status",
                    message=(
                        f"Watchlist item {ticker}: unknown status {raw_status!r}; "
                        "defaulting to 'Watchlist'."
                    ),
                )
            )
        else:
            warnings.append(
                WeeklyReviewInputWarning(
                    code="missing_watchlist_status",
                    message=(
                        f"Watchlist item {ticker}: no status provided; "
                        "defaulting to 'Watchlist'."
                    ),
                )
            )
        status = WeeklyReviewWatchlistStatus.WATCHLIST

    return (
        WeeklyReviewWatchlistItem(
            ticker=ticker,
            name=name,
            status=status,
            reason=str(payload.get("reason", "")).strip(),
            evidence_needed=tuple(
                str(e).strip()
                for e in payload.get("evidence_needed", [])
                if str(e).strip()
            ),
            open_questions=tuple(
                str(q).strip()
                for q in payload.get("open_questions", [])
                if str(q).strip()
            ),
            manual_observations=tuple(
                str(o).strip()
                for o in payload.get("manual_observations", [])
                if str(o).strip()
            ),
            notes=str(payload.get("notes", "")).strip(),
        ),
        warnings,
    )


# ---------------------------------------------------------------------------
# Portfolio types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WeeklyReviewHolding:
    """One holding in a Weekly Review portfolio input."""

    ticker: str
    name: str
    sector: str
    country: str
    weight: float
    market_value: float | None
    cost_basis: float | None
    currency: str
    quality_score: int
    risk_score: int
    role: str
    notes: str
    isin: str


@dataclass(frozen=True)
class WeeklyReviewAccount:
    """One account in a v1 extended portfolio."""

    name: str
    holdings: tuple[WeeklyReviewHolding, ...]


@dataclass(frozen=True)
class WeeklyReviewPortfolioInput:
    """Parsed portfolio for the Weekly Investment Review.

    Supports both the existing ``positions[]`` format and the v1 extended
    ``accounts[].holdings[]`` format.  In both cases, all holdings are
    accessible via ``all_holdings``.
    """

    as_of: str
    accounts: tuple[WeeklyReviewAccount, ...]

    @property
    def all_holdings(self) -> tuple[WeeklyReviewHolding, ...]:
        holdings: list[WeeklyReviewHolding] = []
        for account in self.accounts:
            holdings.extend(account.holdings)
        return tuple(holdings)

    @classmethod
    def from_json_file(
        cls, path: Path
    ) -> tuple["WeeklyReviewPortfolioInput", list["WeeklyReviewInputWarning"]]:
        """Load and parse a portfolio JSON file (positions[] or accounts[] format).

        Returns (portfolio, warnings).  Raises ValueError on required-field
        errors or if the file contains no holdings.
        """
        with path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            raise ValueError(f"Portfolio file must contain a JSON object: {path}")
        return cls.from_mapping(payload)

    @classmethod
    def from_mapping(
        cls, payload: dict[str, Any]
    ) -> tuple["WeeklyReviewPortfolioInput", list["WeeklyReviewInputWarning"]]:
        """Parse a portfolio mapping.  Supports positions[] and accounts[] formats."""
        warnings: list[WeeklyReviewInputWarning] = []
        as_of = str(payload.get("as_of", "")).strip()

        if "accounts" in payload:
            accounts, acct_warnings = _accounts_from_mapping(payload["accounts"])
            warnings.extend(acct_warnings)
        elif "positions" in payload:
            account, pos_warnings = _positions_to_account(payload["positions"])
            accounts = (account,)
            warnings.extend(pos_warnings)
        else:
            raise ValueError(
                "Portfolio JSON must contain either 'accounts' (v1 extended format) "
                "or 'positions' (existing format)."
            )

        if not any(acct.holdings for acct in accounts):
            raise ValueError("Portfolio must contain at least one holding.")

        return (
            cls(as_of=as_of, accounts=accounts),
            warnings,
        )


def _accounts_from_mapping(
    raw_accounts: Any,
) -> tuple[tuple[WeeklyReviewAccount, ...], list["WeeklyReviewInputWarning"]]:
    if not isinstance(raw_accounts, list) or not raw_accounts:
        raise ValueError("'accounts' must be a non-empty list.")
    warnings: list[WeeklyReviewInputWarning] = []
    accounts: list[WeeklyReviewAccount] = []
    for idx, raw in enumerate(raw_accounts):
        if not isinstance(raw, dict):
            raise ValueError(f"Account at index {idx} must be a JSON object.")
        acct_name = str(raw.get("name", f"Account {idx + 1}")).strip()
        raw_holdings = raw.get("holdings", [])
        if not isinstance(raw_holdings, list):
            raise ValueError(f"Account '{acct_name}': 'holdings' must be a list.")
        holdings: list[WeeklyReviewHolding] = []
        for h_idx, raw_h in enumerate(raw_holdings):
            holding, h_warnings = _holding_from_mapping(raw_h, h_idx, acct_name)
            holdings.append(holding)
            warnings.extend(h_warnings)
        accounts.append(WeeklyReviewAccount(name=acct_name, holdings=tuple(holdings)))
    # Derive relative weights from market_value when present
    all_holdings = [h for acct in accounts for h in acct.holdings]
    total_mv = sum(h.market_value for h in all_holdings if h.market_value is not None)
    if total_mv > 0:
        updated: list[WeeklyReviewHolding] = []
        for h in all_holdings:
            if h.market_value is not None:
                derived_weight = h.market_value / total_mv
                updated.append(_replace_weight(h, derived_weight))
            else:
                updated.append(h)
        # Rebuild accounts with derived weights
        pos = 0
        rebuilt: list[WeeklyReviewAccount] = []
        for acct in accounts:
            count = len(acct.holdings)
            rebuilt.append(
                WeeklyReviewAccount(
                    name=acct.name, holdings=tuple(updated[pos : pos + count])
                )
            )
            pos += count
        accounts = rebuilt
    return tuple(accounts), warnings


def _positions_to_account(
    raw_positions: Any,
) -> tuple[WeeklyReviewAccount, list["WeeklyReviewInputWarning"]]:
    if not isinstance(raw_positions, list) or not raw_positions:
        raise ValueError(
            "Portfolio 'positions' must be a non-empty list."
        )
    warnings: list[WeeklyReviewInputWarning] = []
    holdings: list[WeeklyReviewHolding] = []
    for idx, raw in enumerate(raw_positions):
        holding, h_warnings = _holding_from_positions_mapping(raw, idx)
        holdings.append(holding)
        warnings.extend(h_warnings)
    return WeeklyReviewAccount(name="Portfolio", holdings=tuple(holdings)), warnings


def _holding_from_mapping(
    payload: Any, idx: int, account_name: str
) -> tuple[WeeklyReviewHolding, list["WeeklyReviewInputWarning"]]:
    """Parse one holding from the v1 extended accounts[].holdings[] format."""
    if not isinstance(payload, dict):
        raise ValueError(
            f"Account '{account_name}': holding at index {idx} must be a JSON object."
        )
    warnings: list[WeeklyReviewInputWarning] = []

    ticker = str(payload.get("ticker", "")).strip().upper()
    if not ticker:
        raise ValueError(
            f"Account '{account_name}': holding at index {idx} is missing 'ticker'."
        )

    name = str(payload.get("name", ticker)).strip() or ticker

    sector = str(payload.get("sector", "")).strip()
    if not sector:
        sector = "Unclassified"
        warnings.append(
            WeeklyReviewInputWarning(
                code="missing_sector",
                message=(
                    f"Holding {ticker}: no sector provided; "
                    "classified as 'Unclassified'."
                ),
            )
        )

    market_value: float | None = None
    raw_mv = payload.get("market_value")
    if raw_mv is not None:
        try:
            market_value = float(raw_mv)
        except (TypeError, ValueError):
            raise ValueError(
                f"Holding {ticker}: 'market_value' must be a number, got {raw_mv!r}."
            )

    raw_weight = payload.get("weight")
    if raw_weight is not None:
        try:
            weight = _normalize_weight(float(raw_weight))
        except (TypeError, ValueError):
            raise ValueError(
                f"Holding {ticker}: 'weight' must be a number, got {raw_weight!r}."
            )
    elif market_value is not None:
        weight = 0.0  # will be derived after all holdings are loaded
    else:
        raise ValueError(
            f"Holding {ticker}: must provide either 'weight' or 'market_value'."
        )

    if market_value is None and weight == 0.0 and raw_weight is None:
        warnings.append(
            WeeklyReviewInputWarning(
                code="missing_market_value",
                message=(
                    f"Holding {ticker}: no market_value provided; "
                    "excluded from absolute-value calculations."
                ),
            )
        )

    cost_basis: float | None = None
    raw_cb = payload.get("cost_basis")
    if raw_cb is not None:
        try:
            cost_basis = float(raw_cb)
        except (TypeError, ValueError):
            pass

    return (
        WeeklyReviewHolding(
            ticker=ticker,
            name=name,
            sector=sector,
            country=str(payload.get("country", "")).strip(),
            weight=weight,
            market_value=market_value,
            cost_basis=cost_basis,
            currency=str(payload.get("currency", "USD")).strip() or "USD",
            quality_score=_clamp_score(payload.get("quality_score", 50)),
            risk_score=_clamp_score(payload.get("risk_score", 50)),
            role=str(payload.get("role", "")).strip(),
            notes=str(payload.get("notes", "")).strip(),
            isin=str(payload.get("isin", "")).strip(),
        ),
        warnings,
    )


def _holding_from_positions_mapping(
    payload: Any, idx: int
) -> tuple[WeeklyReviewHolding, list["WeeklyReviewInputWarning"]]:
    """Parse one position from the existing positions[] format."""
    if not isinstance(payload, dict):
        raise ValueError(f"Position at index {idx} must be a JSON object.")
    warnings: list[WeeklyReviewInputWarning] = []

    required = ("ticker", "weight")
    missing = [f for f in required if f not in payload]
    if missing:
        raise ValueError(
            f"Position at index {idx} is missing required fields: {', '.join(missing)}."
        )

    ticker = str(payload["ticker"]).strip().upper()

    sector = str(payload.get("sector", "")).strip()
    if not sector:
        sector = "Unclassified"
        warnings.append(
            WeeklyReviewInputWarning(
                code="missing_sector",
                message=(
                    f"Position {ticker}: no sector provided; "
                    "classified as 'Unclassified'."
                ),
            )
        )

    return (
        WeeklyReviewHolding(
            ticker=ticker,
            name=str(payload.get("company", ticker)).strip() or ticker,
            sector=sector,
            country=str(payload.get("country", "")).strip(),
            weight=_normalize_weight(float(payload["weight"])),
            market_value=None,
            cost_basis=None,
            currency="USD",
            quality_score=_clamp_score(payload.get("quality_score", 50)),
            risk_score=_clamp_score(payload.get("risk_score", 50)),
            role="",
            notes="",
            isin="",
        ),
        warnings,
    )


# ---------------------------------------------------------------------------
# Input paths and load result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WeeklyReviewInputWarning:
    """Non-blocking warning produced during input loading."""

    code: str
    message: str


@dataclass(frozen=True)
class WeeklyReviewInputPaths:
    """File paths for all weekly review inputs.

    ``portfolio_path`` and ``watchlist_path`` are required.
    All others are optional.
    """

    portfolio_path: Path
    watchlist_path: Path
    profile_path: Path | None = None
    journal_path: Path | None = None
    company_facts_dir: Path | None = None
    financials_dir: Path | None = None
    as_of: str = ""
    scope_notes: str = ""


@dataclass(frozen=True)
class WeeklyReviewLoadResult:
    """Result of loading and validating the full weekly review input bundle."""

    portfolio: WeeklyReviewPortfolioInput
    watchlist: WeeklyReviewWatchlistInput
    profile_available: bool
    journal_entry_count: int
    company_facts_available: bool
    financials_available: bool
    as_of: str
    scope_notes: str
    warnings: tuple[WeeklyReviewInputWarning, ...]
    journal_entries: tuple[dict[str, Any], ...] = ()  # raw dicts, lightweight read
    profile_principles: tuple[str, ...] = ()  # loaded from profile JSON if available
    profile_constraints: tuple[str, ...] = ()
    profile_risk_tolerance: str = ""
    profile_time_horizon: str = ""
    tickers_missing_facts: tuple[str, ...] = ()  # investable tickers with no facts file
    tickers_missing_financials: tuple[str, ...] = ()  # investable tickers with no financials file


# ---------------------------------------------------------------------------
# Top-level loader
# ---------------------------------------------------------------------------


def load_weekly_review_inputs(paths: WeeklyReviewInputPaths) -> WeeklyReviewLoadResult:
    """Load, validate, and return the weekly review input bundle.

    Required:
        paths.portfolio_path — must exist and be a valid portfolio JSON
        paths.watchlist_path — must exist and be a valid watchlist JSON

    Optional:
        paths.profile_path   — missing produces a warning; default profile used
        paths.journal_path   — missing/empty produces a warning
        paths.company_facts_dir — missing directory produces a warning
        paths.financials_dir    — missing directory produces a warning

    Raises:
        ValueError if a required file is missing or has an invalid format.
    """
    warnings: list[WeeklyReviewInputWarning] = []

    # --- Required: portfolio ---
    if not paths.portfolio_path.exists():
        raise ValueError(
            f"Required portfolio file not found: {paths.portfolio_path}"
        )
    portfolio, p_warns = WeeklyReviewPortfolioInput.from_json_file(paths.portfolio_path)
    warnings.extend(p_warns)

    # --- Required: watchlist ---
    if not paths.watchlist_path.exists():
        raise ValueError(
            f"Required watchlist file not found: {paths.watchlist_path}"
        )
    watchlist, w_warns = WeeklyReviewWatchlistInput.from_json_file(paths.watchlist_path)
    warnings.extend(w_warns)

    # --- Optional: investor profile ---
    profile_available = False
    profile_principles: tuple[str, ...] = ()
    profile_constraints: tuple[str, ...] = ()
    profile_risk_tolerance: str = ""
    profile_time_horizon: str = ""
    if paths.profile_path is not None:
        if paths.profile_path.exists():
            profile_available = True
            try:
                with paths.profile_path.open("r", encoding="utf-8") as fh:
                    profile_data = json.load(fh)
                if isinstance(profile_data, dict):
                    raw_p = profile_data.get("principles", [])
                    if isinstance(raw_p, list):
                        profile_principles = tuple(str(p) for p in raw_p if p)
                    elif raw_p:
                        warnings.append(
                            WeeklyReviewInputWarning(
                                code="invalid_profile_principles",
                                message=(
                                    "Investor profile 'principles' field is not a list; "
                                    "principles will not be loaded."
                                ),
                            )
                        )
                    raw_c = profile_data.get("constraints", [])
                    if isinstance(raw_c, list):
                        profile_constraints = tuple(str(c) for c in raw_c if c)
                    elif raw_c:
                        warnings.append(
                            WeeklyReviewInputWarning(
                                code="invalid_profile_constraints",
                                message=(
                                    "Investor profile 'constraints' field is not a list; "
                                    "constraints will not be loaded."
                                ),
                            )
                        )
                    rt = (
                        profile_data.get("risk_tolerance")
                        or profile_data.get("risk_preference")
                        or ""
                    )
                    profile_risk_tolerance = str(rt).strip()
                    profile_time_horizon = str(
                        profile_data.get("time_horizon", "")
                    ).strip()
            except (json.JSONDecodeError, OSError):
                warnings.append(
                    WeeklyReviewInputWarning(
                        code="invalid_profile",
                        message=(
                            f"Investor profile at {paths.profile_path} could not be "
                            "parsed; profile fields unavailable."
                        ),
                    )
                )
        else:
            warnings.append(
                WeeklyReviewInputWarning(
                    code="missing_optional_profile",
                    message=(
                        f"Investor profile not found at {paths.profile_path}; "
                        "default profile will be used. Suitability results may not "
                        "reflect your actual profile."
                    ),
                )
            )
    else:
        warnings.append(
            WeeklyReviewInputWarning(
                code="missing_optional_profile",
                message=(
                    "No investor profile path provided; default profile will be used. "
                    "Suitability results may not reflect your actual profile."
                ),
            )
        )

    # --- Optional: decision journal ---
    journal_entry_count = 0
    journal_entries: tuple[dict[str, Any], ...] = ()
    effective_journal_path = paths.journal_path
    if effective_journal_path is None:
        default_journal = Path(".atlas") / "decision_journal.json"
        if default_journal.exists():
            effective_journal_path = default_journal

    if effective_journal_path is not None and effective_journal_path.exists():
        try:
            with effective_journal_path.open("r", encoding="utf-8") as fh:
                raw = json.load(fh)
            if isinstance(raw, list):
                journal_entry_count = len(raw)
                journal_entries = tuple(e for e in raw if isinstance(e, dict))
        except (json.JSONDecodeError, OSError):
            warnings.append(
                WeeklyReviewInputWarning(
                    code="invalid_journal",
                    message=(
                        f"Decision journal at {effective_journal_path} could not be "
                        "read; open decisions not reviewed."
                    ),
                )
            )
    else:
        warnings.append(
            WeeklyReviewInputWarning(
                code="missing_optional_journal",
                message="No decision journal input provided; open decisions not reviewed.",
            )
        )

    # --- Optional: company facts directory ---
    company_facts_available = (
        paths.company_facts_dir is not None
        and paths.company_facts_dir.is_dir()
    )
    if not company_facts_available:
        warnings.append(
            WeeklyReviewInputWarning(
                code="missing_optional_company_facts",
                message=(
                    "No company facts directory provided or directory not found; "
                    "company facts will not be included. Evidence gaps noted."
                ),
            )
        )

    # --- Optional: financials directory ---
    financials_available = (
        paths.financials_dir is not None
        and paths.financials_dir.is_dir()
    )
    if not financials_available:
        warnings.append(
            WeeklyReviewInputWarning(
                code="missing_optional_financials",
                message=(
                    "No financials directory provided or directory not found; "
                    "financial history will not be included. Evidence gaps noted."
                ),
            )
        )

    as_of = paths.as_of.strip() if paths.as_of else ""

    # --- Per-ticker company facts and financials presence check ---
    investable_tickers = sorted(
        {h.ticker for h in portfolio.all_holdings if not h.sector or h.sector.lower() != "cash"}
        | {item.ticker for item in watchlist.items}
    )
    tickers_missing_facts: tuple[str, ...] = ()
    if paths.company_facts_dir is not None and paths.company_facts_dir.is_dir():
        tickers_missing_facts = tuple(
            t for t in investable_tickers
            if not (paths.company_facts_dir / f"{t}.json").exists()
        )
    tickers_missing_financials: tuple[str, ...] = ()
    if paths.financials_dir is not None and paths.financials_dir.is_dir():
        tickers_missing_financials = tuple(
            t for t in investable_tickers
            if not (paths.financials_dir / f"{t}.csv").exists()
        )

    return WeeklyReviewLoadResult(
        portfolio=portfolio,
        watchlist=watchlist,
        profile_available=profile_available,
        journal_entry_count=journal_entry_count,
        company_facts_available=company_facts_available,
        financials_available=financials_available,
        as_of=as_of,
        scope_notes=paths.scope_notes.strip() if paths.scope_notes else "",
        warnings=tuple(warnings),
        journal_entries=journal_entries,
        profile_principles=profile_principles,
        profile_constraints=profile_constraints,
        profile_risk_tolerance=profile_risk_tolerance,
        profile_time_horizon=profile_time_horizon,
        tickers_missing_facts=tickers_missing_facts,
        tickers_missing_financials=tickers_missing_financials,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize_weight(weight: float) -> float:
    normalized = weight / 100 if weight > 1 else weight
    return max(0.0, min(1.0, normalized))


def _clamp_score(value: Any) -> int:
    try:
        return max(0, min(100, round(float(value))))
    except (TypeError, ValueError):
        return 50


def _replace_weight(holding: WeeklyReviewHolding, weight: float) -> WeeklyReviewHolding:
    return WeeklyReviewHolding(
        ticker=holding.ticker,
        name=holding.name,
        sector=holding.sector,
        country=holding.country,
        weight=weight,
        market_value=holding.market_value,
        cost_basis=holding.cost_basis,
        currency=holding.currency,
        quality_score=holding.quality_score,
        risk_score=holding.risk_score,
        role=holding.role,
        notes=holding.notes,
        isin=holding.isin,
    )
