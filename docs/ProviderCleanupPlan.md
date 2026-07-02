# Atlas Provider Boundary Audit Plan

**Created:** 2026-07-02 (Sprint 145)  
**Status:** ACTIVE — Sprint 145 inventory checkpoint. 4 modules audited. One stale `__init__.py` export group identified (`YahooCompany`, `YahooFinancials`, `YahooMarketData` — no external callers). Sprint 146 target: remove those 3 symbols from `__init__.py`.

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

## Export Review (`__init__.py` — 7 symbols)

| Export | External callers | Status |
|---|---|---|
| `CompanyDataProvider` | 10+ production files | Active and intentional |
| `MockCompanyAnalysisProvider` | 5 production files, many tests | Active and intentional |
| `YahooFinanceProvider` | `atlas/cli/main.py`, `atlas/analysis/__init__.py`, tests | Active and intentional |
| `YahooFinanceProviderError` | `tests/test_providers.py`, `tests/test_provider_cli.py` | Active — test-only external callers; intentional for error handling |
| `YahooCompany` | **Zero external callers** — only defined/used internally in `yahoo.py` | Stale export — implementation detail not needed in public API |
| `YahooFinancials` | **Zero external callers** — only defined/used internally in `yahoo.py` | Stale export — implementation detail not needed in public API |
| `YahooMarketData` | **Zero external callers** — only defined/used internally in `yahoo.py` | Stale export — implementation detail not needed in public API |

**Three stale exports identified:** `YahooCompany`, `YahooFinancials`, `YahooMarketData`. These are intermediate data types used internally by `YahooFinanceProvider` to fetch and parse Yahoo data before assembling `CompanyAnalysis` and `PortfolioFitInput`. No external production code or test imports them from `atlas.providers`. They are implementation details that leaked into the public API.

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

## Sprint 146 Target

**Remove `YahooCompany`, `YahooFinancials`, `YahooMarketData` from `atlas/providers/__init__.py`.**

- Zero external callers confirmed for all three types.
- Types remain in `yahoo.py` — deletion is from `__init__.py` only (public surface tightening).
- `YahooFinanceProviderError` stays — used by tests for error handling assertions.
- `YahooFinanceProvider` stays — used by CLI.
- Risk: LOW — no production or test code imports these from `atlas.providers`.
- Result: `__init__.py` reduced from 7 to 4 exports; provider public API reflects actual contract.

After Sprint 146, the provider boundary audit track can be closed.
