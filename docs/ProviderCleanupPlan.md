# Atlas Provider Boundary Audit Plan

**Created:** 2026-07-02 (Sprint 145)  
**Updated:** 2026-07-02 (Sprint 146)  
**Status:** CLOSED — Sprint 146 removed stale exports `YahooCompany`, `YahooFinancials`, `YahooMarketData` from `atlas/providers/__init__.py`. Provider public surface reduced from 7 to 4 exports. Internal Yahoo types retained in `atlas/providers/yahoo.py`. No runtime behavior changed. Provider boundary audit track closed.

---

## Background

`atlas/providers/` is the external data boundary layer. It defines the provider protocol (`CompanyDataProvider`), the default opt-in mock provider, and the opt-in Yahoo Finance live provider. Providers are the only layer permitted to make network calls; all other modules must remain deterministic and local.

---

## `atlas/providers/` Inventory (Sprint 145 state)

**4 modules total.**

| File | Lines | Public API | Category |
|---|---|---|---|
| `__init__.py` | 19 | 7 re-exports | Re-export hub |
| `base.py` | 17 | `CompanyDataProvider` (Protocol) | **Provider contract — foundational** |
| `mock.py` | 155 | `MockCompanyAnalysisProvider`, `MOCK_COMPANY_NAMES`, `MOCK_COMPANY_PORTFOLIO_PROFILES` | Mock/test provider |
| `yahoo.py` | 348 | `YahooFinanceProvider`, `YahooFinanceProviderError`, `YahooCompany`, `YahooFinancials`, `YahooMarketData` | Live/network provider — opt-in only |

---

## Provider Contract Review

### `CompanyDataProvider` (Protocol, `base.py`)

Two abstract methods:

| Method | Return type | Blueprint-aligned? | External prod callers | Status |
|---|---|---|---|---|
| `get_company_analysis(ticker)` | `CompanyAnalysis` | Stable legacy type (foundational, Sprint 139 consolidated) | `atlas/analysis/engine.py`, `atlas/cli/main.py` (×3), `atlas/decision/comparison.py`, `atlas/comparison/engine.py`, `atlas/watchlist_review/engine.py` | **Active — 7 prod call sites** |
| `get_portfolio_profile(ticker)` | `PortfolioFitInput` | ✓ Blueprint-aligned (Sprint 133) | `atlas/intelligence/engine.py`, `atlas/dashboard/engine.py`, `atlas/decision/decision_engine.py`, `atlas/conversation/engine.py` | **Active — 4 prod call sites** |

Both return types are correct and stable. `get_portfolio_profile` returning `PortfolioFitInput` confirmed (Sprint 133). No legacy types remain in the contract.

---

## Concrete Provider Review

### `MockCompanyAnalysisProvider` (`mock.py`)

- Implements both `CompanyDataProvider` methods.
- `get_company_analysis`: supports NVDA, AMD, AAPL, MSFT, EVO. AMD, MSFT, AAPL have custom score overrides; NVDA and EVO use placeholder values.
- `get_portfolio_profile`: supports NVDA, AAPL, MSFT, EVO only. **AMD has no portfolio profile** — `LookupError` raised if called with "AMD". This is intentional (AMD is a comparison-only ticker in most tests).
- External production callers: `atlas/cli/main.py`, `atlas/home/engine.py`, `atlas/comparison/engine.py`, `atlas/watchlist_review/engine.py`, `atlas/conversation/engine.py`.
- No network access. No stale imports. Clean.

### `YahooFinanceProvider` (`yahoo.py`)

- Implements both `CompanyDataProvider` methods.
- Contract methods (`get_company_analysis`, `get_portfolio_profile`) return correct types.
- Yahoo-specific sub-methods: `get_company() -> YahooCompany`, `get_financials() -> YahooFinancials`, `get_market_data() -> YahooMarketData`.
  - These are **only called internally** within `yahoo.py` (by `get_company_analysis` and `get_portfolio_profile`).
  - External callers: only `tests/test_providers.py`. No production code outside `providers/` calls these.
- Network behavior: `urlopen` via `_fetch_json`. Correctly gated — opt-in only; no production code calls `YahooFinanceProvider` directly except `atlas/cli/main.py` when `--provider yahoo` flag is passed.
- No stale imports. No deleted-symbol references.

---

## Provider Method Caller Map

| Method | External production callers | Test callers |
|---|---|---|
| `get_company_analysis` | 7 (atlas/analysis/engine, atlas/cli/main×3, atlas/decision/comparison, atlas/comparison/engine, atlas/watchlist_review/engine) | many |
| `get_portfolio_profile` | 4 (atlas/intelligence/engine, atlas/dashboard/engine, atlas/decision/decision_engine, atlas/conversation/engine) | test_providers.py |
| `get_company` | 0 production (internal to yahoo.py only) | test_providers.py |
| `get_financials` | 0 production (internal to yahoo.py only) | test_providers.py |
| `get_market_data` | 0 production (internal to yahoo.py only) | test_providers.py |

`get_company`, `get_financials`, `get_market_data` are Yahoo-internal — callers outside the provider only access them in tests for verifying Yahoo data mapping. They are NOT part of the `CompanyDataProvider` contract.

---

## Export Review (`__init__.py` — 4 symbols, Sprint 146 state)

| Export | External callers | Status |
|---|---|---|
| `CompanyDataProvider` | 10+ production files | Active and intentional |
| `MockCompanyAnalysisProvider` | 5 production files, many tests | Active and intentional |
| `YahooFinanceProvider` | `atlas/cli/main.py`, `atlas/analysis/__init__.py`, tests | Active and intentional |
| `YahooFinanceProviderError` | `tests/test_providers.py`, `tests/test_provider_cli.py` | Active — test-only external callers; intentional for error handling |
| ~~`YahooCompany`~~ | Zero external callers — internal `yahoo.py` only | **Removed Sprint 146** — type retained in `yahoo.py` |
| ~~`YahooFinancials`~~ | Zero external callers — internal `yahoo.py` only | **Removed Sprint 146** — type retained in `yahoo.py` |
| ~~`YahooMarketData`~~ | Zero external callers — internal `yahoo.py` only | **Removed Sprint 146** — type retained in `yahoo.py` |

**Sprint 146 result:** Three stale implementation-detail re-exports removed. `YahooCompany`, `YahooFinancials`, `YahooMarketData` remain defined and used internally in `atlas/providers/yahoo.py`. They are not importable from `atlas.providers`. Provider public surface: 7 → 4 exports.

---

## Stale Import Audit

**Zero stale production imports in `atlas/providers/`.**

No references to `CompanyPortfolioProfile`, `PortfolioAnalysis`, `portfolio_fit_input_from_profile`, deleted analysis submodules, or `render_comparison_result` found anywhere in `atlas/providers/`.

---

## Boundary Direction Review

| Import direction | Files | Classification |
|---|---|---|
| providers → `atlas.analysis.company_analysis` | `mock.py`, `yahoo.py` | Expected — `CompanyAnalysis` is the contract return type |
| providers → `atlas.capabilities.portfolio_intelligence` | `mock.py`, `yahoo.py`, `base.py` | Expected — `PortfolioFitInput` is the Sprint 133 contract return type |
| providers → anything else | None | ✓ No upward dependencies |

No boundary violations. Providers do not import from `atlas/decision/`, `atlas/intelligence/`, `atlas/cli/`, `atlas/dashboard/`, or `atlas/conversation/`.

---

## Blueprint Alignment Review

| Provider method | Return type | Alignment |
|---|---|---|
| `get_company_analysis` | `CompanyAnalysis` | Stable legacy type (foundational). Sprint 139 consolidated. |
| `get_portfolio_profile` | `PortfolioFitInput` | ✓ Blueprint-aligned since Sprint 133 |

Both return types are stable. No migration warranted.

---

## Sprint 146 — Stale Export Removal (COMPLETED)

**Removed `YahooCompany`, `YahooFinancials`, `YahooMarketData` from `atlas/providers/__init__.py`.**

- Zero external callers confirmed (repo-wide grep before deletion).
- Types retained in `yahoo.py` — only the public re-export was removed.
- `YahooFinanceProviderError` retained — used by tests for error handling assertions.
- `YahooFinanceProvider` retained — used by CLI.
- `__init__.py` reduced from 7 to 4 exports.
- No runtime behavior changed.
- No provider behavior changed.
- No test behavior changed.

Provider boundary audit track: **CLOSED**.

---

## Final Stable Provider Package State (Sprint 146)

| Module | Lines | Public API | Status |
|---|---|---|---|
| `__init__.py` | 14 | 4 re-exports | Clean — no stale exports |
| `base.py` | 17 | `CompanyDataProvider` (Protocol) | Foundational — stable |
| `mock.py` | 155 | `MockCompanyAnalysisProvider` | Active — test/demo provider |
| `yahoo.py` | 348 | `YahooFinanceProvider`, `YahooFinanceProviderError`, `YahooCompany`*, `YahooFinancials`*, `YahooMarketData`* | Active — opt-in live provider |

*Internal types — not exported from `atlas.providers`.

---

## Remaining Provider Technical Debt

None identified. Provider boundary is clean:
- Contract methods are correct and stable.
- No stale exports remain in `__init__.py`.
- No upward dependencies (providers do not import from decision/intelligence/cli/dashboard/conversation).
- Yahoo provider remains opt-in.
- Mock provider remains provider-free.

---

## Recommended Sprint 147 Target

No remaining provider cleanup work. Sprint 147 should audit the next area of technical debt. Candidates:

- `atlas/analysis/portfolio.py` — 17+ production import sites; long-term migration track.
- Group C self-contained modules (`atlas/evidence/`, `atlas/reasoning/`, `atlas/risk/`) — Blueprint wrapper candidates.
- Provider-coupled Group B modules (`atlas/home/`, `atlas/comparison/`) — require provider architecture decision.

Suggest Sprint 147 audit `atlas/analysis/portfolio.py` callers for migration readiness, or pivot to a new consolidation area as determined by project priorities.
