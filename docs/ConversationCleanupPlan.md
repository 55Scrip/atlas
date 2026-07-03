# Atlas Conversation Package Cleanup Plan

**Created:** 2026-07-03 (Sprint 166)  
**Updated:** 2026-07-03 (Sprint 167)  
**Status:** CLOSED — Sprint 167 confirmed Sprint 166 findings unchanged. No cleanup action is warranted. Package is self-contained, actively used via `ConversationEngine`, and stable. No further `atlas/conversation/` cleanup work is planned until new dead code, stale exports, dependency-boundary issues, or a clear Blueprint-aligned successor emerges.

---

## Background

`atlas/conversation/` is a self-contained orchestration hub that routes natural investment questions to the appropriate Atlas engine and returns a deterministic `ConversationResponse`. It is active, well-bounded, and has one active CLI command (`atlas ask`). It has no deleted-module imports. Sprint 166 is the audit-first sprint following the intelligence track closure (Sprint 165).

---

## `atlas/conversation/` Package Inventory (Sprint 166 state)

**2 modules total.**

| File | Lines | Category |
|---|---|---|
| `__init__.py` | 17 | Re-export hub — 6 exports |
| `engine.py` | 548 | Core engine + dataclasses + renderer + private helpers |

---

## `engine.py` — Public API

| Symbol | Kind | Active production callers | Test callers | Status |
|---|---|---|---|---|
| `ConversationIntent` | `str` Enum (8 values) | `atlas/cli/main.py` (indirectly via response), `atlas/principles/engine.py` (TYPE_CHECKING) | `test_conversation_engine.py`, `test_principles_engine.py` | **Active** |
| `ConversationInput` | frozen dataclass | CLI (`ask_command`) | `test_conversation_engine.py`, `test_portfolio_intelligence_engine.py` | **Active** |
| `ConversationResponse` | frozen dataclass | CLI (returned by `.answer()`), `atlas/principles/engine.py` (TYPE_CHECKING annotation) | `test_conversation_engine.py`, `test_principles_engine.py` | **Active — consumed by principles as type annotation** |
| `IntentClassifier` | class | `ConversationEngine.__init__` | `test_conversation_engine.py`, `test_portfolio_intelligence_engine.py` | **Active — intent routing** |
| `ConversationEngine` | class | CLI (`ask_command`) | `test_conversation_engine.py`, `test_portfolio_intelligence_engine.py` | **Active — core orchestration engine** |
| `render_conversation_response` | function | CLI (`ask_command`) | `test_conversation_engine.py` | **Active** |

### `engine.py` — Private Helpers

All private helpers are internal and active.

| Symbol | Purpose | Callers |
|---|---|---|
| `_answer_company_analysis` | Routes `COMPANY_ANALYSIS` intent via `IntelligenceEngine` | `answer()` |
| `_answer_portfolio_review` | Routes `PORTFOLIO_REVIEW` intent via `PortfolioIntelligenceCapability` | `answer()` |
| `_answer_watchlist_review` | Routes `WATCHLIST_REVIEW` intent via `WatchlistIntelligenceEngine` | `answer()` |
| `_answer_theme_research` | Routes `THEME_RESEARCH` intent via `ThemeEngine` | `answer()` |
| `_answer_market_health` | Routes `MARKET_HEALTH` intent via `MarketHealthEngine` | `answer()` |
| `_answer_market_regime` | Routes `MARKET_REGIME` intent via `MarketRegimeEngine` | `answer()` |
| `_answer_risk_assessment` | Routes `RISK_ASSESSMENT` intent via `RiskAnalysis` (if supplied) or `AtlasInvestmentEngine` | `answer()` |
| `_answer_general_guidance` | Routes `GENERAL_INVESTMENT_GUIDANCE` intent via `IntelligenceEngine` | `answer()` |
| `_needs_context_response` | Returns graceful degradation when required context is missing | `_answer_portfolio_review`, `_answer_watchlist_review` |
| `_resolve_ticker` | Extracts ticker from explicit arg or question text (alias map) | `answer()` |
| `_resolve_theme` | Extracts theme keyword from question text | `_answer_theme_research` |
| `_default_market_snapshot` | Returns deterministic placeholder `MarketSnapshot` | `_answer_market_regime` |
| `_default_followups` | Returns standard follow-up question tuple | Multiple `_answer_*` methods |
| `_contains_any` | String keyword membership check | `IntentClassifier.classify` |
| `_normalize` | Lowercases and strips question text | `IntentClassifier.classify`, `_resolve_ticker`, `_resolve_theme` |
| `_render_list` | Formats `tuple[str, ...]` as bullet lines | `render_conversation_response` |

**Zero zero-caller private helpers found.**

---

## `ConversationEngine` Review

| Detail | Value |
|---|---|
| Source file | `atlas/conversation/engine.py:86` |
| Public methods | `.answer(ConversationInput) → ConversationResponse` |
| Constructor dependencies | 7 optional parameters (all default `None` → instantiate defaults) |
| Provider dependency | `ConversationInput.provider: CompanyDataProvider | None`; falls back to `MockCompanyAnalysisProvider()` inside `.answer()` if `None` |
| Network calls? | No direct network calls. Provider is caller-supplied or mock default. Network is CLI opt-in via `--provider yahoo`. |
| Intelligence dependency | `IntelligenceEngine` injected via constructor or instantiated as default. Called in `_answer_company_analysis` and `_answer_general_guidance`. |
| `RiskAnalysis` dependency | `ConversationInput.risk_analysis: RiskAnalysis | None` — optional caller-supplied context. Consumed directly in `_answer_risk_assessment`. |
| Production callers | CLI (`ask_command`) |
| Test callers | `tests/test_conversation_engine.py`, `tests/test_portfolio_intelligence_engine.py` |
| CLI callers | `atlas ask QUESTION [--provider] [--ticker] [--portfolio] [--watchlist] [--theme]` |
| Returns Blueprint-aligned data? | No — returns `ConversationResponse` (legacy type). Consumes Blueprint-aligned types: `PortfolioFitResult`, `WatchlistIntelligenceReport`. |
| Zero-caller public methods | None — `.answer()` is the only public method and is active. |
| Stale compatibility logic | None found. |

---

## Export Review (`__init__.py`)

6 exports. All active.

| Export | Active? | Direct external callers |
|---|---|---|
| `ConversationEngine` | ✓ | CLI, tests |
| `ConversationInput` | ✓ | CLI, tests |
| `ConversationIntent` | ✓ | Principles engine (TYPE_CHECKING), tests |
| `ConversationResponse` | ✓ | Principles engine (TYPE_CHECKING), tests |
| `IntentClassifier` | ✓ | Internally by `ConversationEngine`; also direct in tests |
| `render_conversation_response` | ✓ | CLI, tests |

**Finding:** All 6 exports are active. No stale exports. No removal candidates.

---

## Production Caller Map

**2 production callers: CLI + principles engine (TYPE_CHECKING only).**

| Caller | Import | Symbols used | Runtime or type-only? |
|---|---|---|---|
| `atlas/cli/main.py:ask_command` | `from atlas.conversation import ConversationEngine, ConversationInput, render_conversation_response` | 3 of 6 | **Runtime** |
| `atlas/principles/engine.py` | `from atlas.conversation import ConversationResponse` (under `TYPE_CHECKING`) | 1 of 6 | **TYPE_CHECKING only** — used as parameter annotation in `check_conversation_response()` |

No production engine outside CLI and principles (TYPE_CHECKING) imports from `atlas/conversation/`.

---

## CLI / Entrypoint Review

### `atlas ask`

| Detail | Value |
|---|---|
| Command | `atlas ask QUESTION [--provider mock\|yahoo] [--ticker TICKER] [--portfolio path] [--watchlist path] [--theme "..."]` |
| Implementation | `atlas/cli/main.py:269–297` |
| Imports used | `ConversationEngine`, `ConversationInput`, `render_conversation_response` |
| Provider selection | `_provider_from_name(provider_name)` — `"mock"` → `MockCompanyAnalysisProvider()`, `"yahoo"` → `YahooFinanceProvider()`. Default: `"mock"`. |
| Runtime behavior | Parses inputs, instantiates `ConversationEngine()`, builds `ConversationInput`, calls `.answer()`, prints via `render_conversation_response()` |
| CLI behavior | Active and unchanged |

---

## Intelligence Dependency Review

| Detail | Value |
|---|---|
| Import location | `atlas/conversation/engine.py:16` — `from atlas.intelligence import IntelligenceContext, IntelligenceEngine, IntelligenceInput` |
| Import type | **Runtime** — not TYPE_CHECKING-only. Required for constructor default and call sites. |
| How invoked | `self.intelligence_engine.analyze(IntelligenceInput(...))` — called in `_answer_company_analysis` and `_answer_general_guidance` |
| `IntelligenceInput` construction | Builds `IntelligenceContext` from `ConversationInput` fields (portfolio, watchlist, theme, market_snapshot, market_health_report, risk_analysis) then wraps with ticker + provider |
| `IntelligenceReport` fields accessed | `report.investment_report.atlas_score`, `report.confidence`, `report.executive_summary`, `report.company_positioning[:3]`, `report.atlas_conclusion`, `report.current_market_environment[1]` |
| Dependency intentional? | **Yes** — `COMPANY_ANALYSIS` and `GENERAL_INVESTMENT_GUIDANCE` intents delegate to `IntelligenceEngine` as the authoritative synthesis layer |
| Output shape coupling | **MEDIUM** — depends on 6 specific `IntelligenceReport` fields. If `IntelligenceReport` shape changes, conversation rendering changes. |
| Migration warranted? | No — the coupling is intentional and shallow. |

---

## Dependency Boundary Review

| Dependency | Import location | Classification | Direction acceptable? | Stable? |
|---|---|---|---|---|
| `atlas.adapters.portfolio` | `legacy_portfolio_to_domain_portfolio` (runtime), `Portfolio` (TYPE_CHECKING) | Adapter conversion | ✓ | ✓ |
| `atlas.analysis.engine` | `AtlasInvestmentEngine` (runtime) | Investment engine dependency | ✓ | ✓ |
| `atlas.capabilities.portfolio_intelligence` | `PortfolioIntelligenceCapability` (runtime) | Blueprint-aligned capability | ✓ correct direction | ✓ |
| `atlas.capabilities.watchlist_intelligence` | `WatchlistInput`, `WatchlistIntelligenceEngine`, models (runtime) | Blueprint-aligned capability | ✓ correct direction | ✓ |
| `atlas.intelligence` | `IntelligenceContext`, `IntelligenceEngine`, `IntelligenceInput` (runtime) | Orchestration dependency | ✓ conversation consumes intelligence | ✓ |
| `atlas.market` | 5 types (runtime) | Market data types | ✓ | ✓ |
| `atlas.providers` | `CompanyDataProvider`, `MockCompanyAnalysisProvider` (runtime) | Provider types + mock default | ✓ — mock default keeps network opt-in | ✓ |
| `atlas.risk` | `RiskAnalysis` (runtime) | Optional context field in dataclass | ✓ intentional — see below | ✓ |
| `atlas.themes` | `ThemeEngine`, `ThemeInput` (runtime) | Theme engine dependency | ✓ | ✓ |

**Provider coupling note:** Unlike `atlas/comparison/` and `atlas/home/`, conversation imports `MockCompanyAnalysisProvider` directly (as default fallback in `.answer()`). This is correct — it keeps network access opt-in while allowing zero-argument CLI usage.

**No circular dependencies.** Intelligence imports from conversation? No — `atlas/intelligence/engine.py` has no import from `atlas/conversation/`. Conversation → Intelligence is one-directional. ✓

**No deleted-module imports.** `atlas.reasoning`, `atlas.analysis.portfolio`, `atlas.analysis.comparison` — all absent. ✓

---

## `RiskAnalysis` Dependency Review

| Detail | Value |
|---|---|
| Import location | `atlas/conversation/engine.py:25` — `from atlas.risk import RiskAnalysis` |
| Import type | **Runtime** — required for dataclass field type annotation and runtime field access |
| Fields accessed | `risk.position_sizing.final_risk_recommendation`, `risk.position_sizing.liquidity_warning`, `risk.position_sizing.concentration_warning`, `risk.deployment_plan.market_regime_adjustment`, `risk.reasoning[:2]`, `risk.target_ticker` |
| Where consumed | `_answer_risk_assessment()` — directly builds response from `RiskAnalysis` fields if `risk_analysis` is not `None` |
| Dependency nature | Optional caller-supplied context in `ConversationInput.risk_analysis` |
| Intentional? | **Yes** — when a caller supplies a `RiskAnalysis`, conversation incorporates it into a direct risk response. Otherwise, falls back to investment engine risk score. |
| Should remain? | **Yes** — the coupling is shallow, optional, and provides meaningful output when supplied. |

---

## Stale Import Audit (repo-wide, conversation focus)

All checked. All hits in `atlas/conversation/` classified:

| Symbol | In `atlas/conversation/`? | Elsewhere (classified) |
|---|---|---|
| `atlas.reasoning` / deleted reasoning symbols | **None** ✓ | Test guardrails, docs, `atlas/domains/decision/` Blueprint class, deprecations metadata |
| `PortfolioIntelligenceEngine` | **None** ✓ | Test guardrails asserting absence |
| `portfolio_fit_input_from_profile` | **None** ✓ | Test guardrails asserting absence |
| `PortfolioAnalysis` / `PortfolioSignal` etc. | **None** ✓ | Test guardrails, docs, capability models doc comments |
| `render_comparison_result` | **None** ✓ | Test guardrails asserting absence |
| `YahooCompany` / `YahooFinancials` / `YahooMarketData` | **None** ✓ | Historical docs only |
| `check_intelligence_report` / `check_suitability_assessment` | **None** ✓ | Test guardrails asserting absence |

**No stale production imports in `atlas/conversation/`.**

---

## Blueprint Overlap Review

| Target | Overlap with `atlas/conversation/`? |
|---|---|
| `atlas/domains/` | No `atlas/domains/conversation/` exists. `atlas/domains/decision/` is a dependency of intelligence (consumed by conversation indirectly). |
| `atlas/capabilities/` | No conversation capability exists. Conversation **consumes** `PortfolioIntelligenceCapability` and `WatchlistIntelligenceEngine` from capabilities — correct direction. |
| `atlas/intelligence/` | Intelligence is a dependency of conversation — not a successor. |
| `atlas/dashboard/` | Dashboard is a parallel runtime layer, not a successor. No overlap in entrypoints. |
| `atlas/decision/` | Decision is consumed by intelligence (which conversation wraps). No direct overlap. |
| `atlas/suitability/` | Suitability consumes `IntelligenceReport` (via intelligence). Conversation also uses intelligence. Not redundant — different runtime purpose. |

**Conclusion:** No Blueprint-aligned successor exists for `atlas/conversation/`. The intent-routing and response-building logic is unique to this package. No migration warranted.

---

## Cleanup Candidate Classification

| Candidate | Evidence | Caller count | Risk | Sprint 167? |
|---|---|---|---|---|
| All 6 exports | All active — CLI, tests, principles (TYPE_CHECKING) | Active | N/A | Leave unchanged |
| All 16 private helpers | All called by `answer()` or renderer | Active | N/A | Leave unchanged |
| `IntelligenceEngine` dependency | Intentional orchestration — 2 intent branches | Active | N/A | Leave unchanged |
| `RiskAnalysis` dependency | Intentional optional context — 6 field reads | Active | N/A | Leave unchanged |
| `MockCompanyAnalysisProvider` import | Correct — default fallback to keep CLI zero-arg usage without network | Active | N/A | Leave unchanged |

**Overall assessment:** The conversation package is clean. No dead code, no stale exports, no closed-track residue, no Blueprint migration pressure, no zero-caller symbols. The engine is an active intent-routing hub. All 6 exports are intentional. Intelligence and risk dependencies are intentional and shallow.

---

## Final Stable Package State (Sprint 166)

| Module | Lines | Status |
|---|---|---|
| `__init__.py` | 17 | 6 exports — all intentional |
| `engine.py` | 548 | Active — `ConversationEngine` intent-routing hub with clean boundaries |

**Provider safety:** Network access is opt-in only (`--provider yahoo`). `MockCompanyAnalysisProvider` is used as the default in `.answer()`. `YahooFinanceProvider` never imported by `atlas/conversation/`. ✓

---

## Sprint 167 — Track Closure (COMPLETED)

**Conversation cleanup track is CLOSED as of Sprint 167.**

Sprint 167 verified:
- All 6 `atlas.conversation` exports remain importable ✓
- `ConversationEngine` active — `atlas ask` CLI entrypoint confirmed ✓
- `IntelligenceEngine` dependency confirmed intentional — runtime import, consumed by `_answer_company_analysis` and `_answer_general_guidance` ✓
- `RiskAnalysis` dependency confirmed intentional — optional caller-supplied context, 6 fields read, graceful degradation ✓
- `MockCompanyAnalysisProvider` default fallback — no network without opt-in ✓
- `YahooFinanceProvider` not imported by `atlas/conversation/` ✓
- Zero stale closed-track imports ✓
- No Blueprint-aligned successor introduced since Sprint 166 ✓
- No cleanup action is warranted ✓

**Closure rationale:** After inventory (Sprint 166) and final verification (Sprint 167), the conversation package contains only active, intentional code. `ConversationEngine.answer()` is the sole public method and has 1 production call site (CLI). All 6 exports are active. All 16 private helpers are active. Intelligence and risk dependencies are intentional, optional in impact, and shallow. Further cleanup would create churn without architectural benefit.

**Reopening condition:** If a Blueprint-aligned conversation capability emerges in `atlas/capabilities/`, if the CLI command is deprecated, or if new dead code or stale imports appear.

---

## Closed-Track Summary

| Track | Status |
|---|---|
| `atlas/analysis/` cleanup | CLOSED Sprint 141 |
| `atlas/decision/` cleanup | CLOSED Sprint 144 |
| Provider boundary audit | CLOSED Sprint 146 |
| Portfolio boundary | CLOSED Sprint 148 |
| Evidence package | CLOSED Sprint 150 |
| Reasoning package | CLOSED Sprint 153 |
| Risk package | CLOSED Sprint 155 |
| Principles package | CLOSED Sprint 158 |
| Comparison package | CLOSED Sprint 160 |
| Home package | CLOSED Sprint 162 |
| Intelligence package | CLOSED Sprint 165 |
| **Conversation package** | **CLOSED Sprint 167** |

---

## Recommended Sprint 168 Target

**Audit `atlas/dashboard/` package.**

`atlas/dashboard/` is another active runtime/application-facing surface. It should be audited after conversation is formally closed. Pattern: audit-first (Sprint 168 inventory), then targeted action or documentation closure sprint (Sprint 169).
