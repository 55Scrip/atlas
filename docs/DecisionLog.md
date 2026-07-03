# Atlas Decision Log

This log records architectural decisions that shape future development.

## 2026-07-03: Sprint 179 — Company Analysis Package Audit

Decision: Audit the legacy company analysis runtime surface (`atlas/analysis/`) and confirm the boundary with `atlas/capabilities/company_analysis/`.

**Rationale:** Sprint 179 was specified as auditing `atlas/company_analysis/`, which does not exist as a standalone package. The company analysis runtime surface is `atlas/analysis/` — the legacy scoring and investment-report layer partially cleaned up in Sprint 141. This audit establishes whether the remaining 5 modules are clean and whether the Sprint 141 closure is verified stable.

**Key findings:**
- `atlas/company_analysis/` does not exist; the legacy surface is `atlas/analysis/` (5 modules, ~655 lines)
- Sprint 141 closure verified: 12 deleted modules remain unimportable
- All 12 `__all__` exports are active with production callers
- `atlas/capabilities/company_analysis/` is fully decoupled from `atlas/analysis/` — capability does not import the legacy layer; boundary is clean
- One stale alias found: `CompanyAnalysisProvider` in `atlas/analysis/company_analysis.py:154` — module-level import of `CompanyDataProvider` aliased to `CompanyAnalysisProvider`, with zero external callers and not in `__all__`
- `ThresholdRecommendationPolicy` generates legacy recommendation language ("Strong Buy"/"Buy"/etc.) — pre-existing, confined to the legacy layer, not emitted by the Blueprint capability
- Provider boundary correct — no direct network access in `atlas/analysis/`; Yahoo remains opt-in only

**Changes made:** Audit-only. Created `docs/CompanyAnalysisCleanupPlan.md`, added 11 guardrail tests in `tests/test_company_analysis_package_sprint179.py`.

**Next sprint recommendation:** Close `atlas/analysis/` cleanup track — remove stale `CompanyAnalysisProvider` alias from `atlas/analysis/company_analysis.py:154`.

---

## 2026-07-03: Sprint 178 — Adapters Package Audit

Decision: Audit `atlas/adapters/` and confirm no cleanup is warranted.

**Rationale:** After auditing capabilities (Sprint 176) and domains (Sprint 177), `atlas/adapters/` was the next audit target — the translation layer bridging external/legacy JSON to Blueprint-aligned types. Full inventory confirmed 5 adapter modules, 756 lines, 7 public symbols.

**Key findings:**
- All 5 adapters are pure JSON-to-type translators: deterministic, no network, no provider imports, no business logic
- All 7 public symbols have active production callers; no zero-caller symbols
- `atlas.analysis.scores.clamp_score` import in `portfolio.py` is correct and active (not stale) — confirmed retained Sprint 140
- Portfolio boundary CLOSED Sprint 148 verified stable: 3 active symbols importable, 6 deleted symbols absent
- No adapter imports `atlas.providers`, `atlas.cli`, or any network library
- No circular dependencies; dependency direction: adapter → domain/capability/shared/active-utilities
- No `__all__` in `__init__.py` is correct — adapters consumed by direct module path
- No cleanup warranted

**Changes made:** Audit-only. Created `docs/AdaptersCleanupPlan.md`, added 14 guardrail tests in `tests/test_adapters_package_sprint178.py`.

**Next sprint recommendation:** Audit `atlas/company_analysis/` package.

---

## 2026-07-03: Sprint 177 — Domains Package Audit

Decision: Audit `atlas/domains/` and confirm no cleanup is warranted.

**Rationale:** After auditing the capabilities layer (Sprint 176), the next audit target was the domain layer — the foundational Blueprint contracts that capabilities depend on. Full inventory confirmed 9 subpackages, ~1,730 lines, 68 total active exports. No stale imports, no provider coupling, no upward dependencies, no circular dependencies. Boundary direction is correct throughout: `atlas.shared → atlas.domains → atlas.capabilities`.

**Key findings:**
- 4 substantive domain subpackages (`decision`, `knowledge`, `portfolio`, `research`) are foundational and widely consumed
- 5 thin/placeholder subpackages (`ai`, `authentication`, `daily_brief`, `decision_journal`, `watchlist`) are correct future-boundary markers
- `atlas.domains.decision.ReasoningEngine` is the active Blueprint-layer class — distinct from deleted `atlas.reasoning.ReasoningEngine`; existing Sprint 163 guardrails confirm this
- `atlas/domains/ai/` re-exports Protocol interfaces from `atlas.ai` — correct future-AI boundary, test-adjacent only, no production callers
- No cleanup warranted

**Changes made:** Audit-only. Created `docs/DomainsCleanupPlan.md`, added 18 guardrail tests in `tests/test_domains_package_sprint177.py`.

**Next sprint recommendation:** Audit `atlas/adapters/` package.

---

## 2026-07-03: Sprint 176 — Capabilities Package Audit

Decision: Audit `atlas/capabilities/` and confirm no cleanup is warranted.

**Rationale:** After 15 closed cleanup tracks and three RC checkpoints, `atlas/capabilities/` was the next highest-leverage audit target. Full inventory confirmed 5 subpackages (4 active + 1 closed Sprint 171), 52 total active exports, no stale imports, no provider coupling, no circular dependencies, no overlap with domain layer beyond correct dependency direction.

**Findings:**
- All capability exports are active and have production callers
- Dependency direction is consistently: `domains/shared → capabilities`; no reverse coupling
- `discovery` is the aggregating capability — correctly imports `CompanyAnalysisReport` and `WatchlistIntelligenceReport`
- `WatchlistInput.from_json_file()` in models is a minor file-I/O note; not a risk
- `atlas/domains/daily_brief/` is a correctly empty placeholder namespace; `atlas/capabilities/daily_brief/` owns the implementation
- `portfolio_intelligence/` subtrack remains closed (Sprint 171); verified stable
- No cleanup warranted

**Changes made:** Audit-only. Created `docs/CapabilitiesCleanupPlan.md`, added 12 guardrail tests in `tests/test_capabilities_package_sprint176.py`.

**Next sprint recommendation:** Audit `atlas/domains/` package.

---

## 2026-07-03: Sprint 175 — RC Checkpoint After 15 Closed Cleanup Tracks

Decision: Treat Atlas as RC2-stable after 15 closed cleanup tracks and three RC checkpoints (Sprint 163, Sprint 172, Sprint 175).

**Rationale:** All 15 cleanup tracks verified closed. All 13 deleted modules confirmed absent. All 10 active packages importable. CLI help surface reflects Sprint 174 change (empty groups absent). Provider boundary unchanged. 1541 tests passed, 3 skipped. RC2 green. Daily brief demo passes.

**Closed-track summary (15 tracks):**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- `atlas/evidence/` cleanup — CLOSED Sprint 150
- `atlas/reasoning/` cleanup — CLOSED Sprint 153
- `atlas/risk/` cleanup — CLOSED Sprint 155
- `atlas/principles/` cleanup — CLOSED Sprint 158
- `atlas/comparison/` cleanup — CLOSED Sprint 160
- `atlas/home/` cleanup — CLOSED Sprint 162
- `atlas/intelligence/` cleanup — CLOSED Sprint 165
- `atlas/conversation/` cleanup — CLOSED Sprint 167
- `atlas/dashboard/` cleanup — CLOSED Sprint 169
- `atlas/capabilities/portfolio_intelligence/` cleanup — CLOSED Sprint 171
- `atlas/cli/` cleanup — CLOSED Sprint 174

**Next sprint recommendation:** Audit `atlas/capabilities/` package (excluding `portfolio_intelligence/`, already closed Sprint 171).

---

## 2026-07-03: Sprint 174 — Remove Empty CLI Groups and Close CLI Cleanup Track

Decision: Remove empty shell CLI app groups and close the CLI cleanup track.

**Rationale:** After the CLI registry audit (Sprint 173), the only actionable cleanup was removing empty `evidence`, `reason`, and `risk` CLI groups from `atlas/cli/main.py`. These groups were residual scaffolding from retired commands (`atlas evidence assess`, `atlas reason analyze`, `atlas risk size`). They exposed no callable commands and only cluttered `atlas --help`. Removing them improves CLI clarity without changing any active or retired command behavior.

**Changes made:** Removed 3 app declarations and 3 `app.add_typer()` registrations (~6 lines total) from `atlas/cli/main.py`. Zero behavioral change — no callable command was removed.

**Verified:**
- `atlas --help` no longer shows `evidence`, `reason`, or `risk` groups ✓
- All active groups remain (intelligence, dashboard, principles, risk-drift, watchlist, daily, portfolio, etc.) ✓
- All 7 retired commands remain not callable ✓
- `_RETIRED_REGISTRY` unchanged — 7 entries, all accurate ✓
- 1536 tests passed, 3 skipped ✓
- RC2 green ✓

**Closed-track summary (15 tracks):**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — CLOSED Sprint 155
- Principles package — CLOSED Sprint 158
- Comparison package — CLOSED Sprint 160
- Home package — CLOSED Sprint 162
- Intelligence package — CLOSED Sprint 165
- Conversation package — CLOSED Sprint 167
- Dashboard package — CLOSED Sprint 169
- Portfolio intelligence capability — CLOSED Sprint 171
- **CLI deprecated command registry — CLOSED Sprint 174**

**Sprint 175 recommended target:** Release candidate checkpoint after 15 closed tracks — pattern matches Sprint 163 (after 10 tracks) and Sprint 172 (after 14 tracks).

---

## 2026-07-03: Sprint 173 — CLI Deprecated Command Registry Audit Checkpoint

Decision: `atlas/cli/` deprecated command registry is clean. One cleanup action is warranted: remove 3 empty shell app groups.

**Rationale:** After audit-first inventory (Sprint 173), the CLI registry is accurate and complete. `_REGISTRY` is correctly empty (all deprecated commands retired Sprint 91). All 7 `_RETIRED_REGISTRY` entries are accurate after 14 cleanup closures — all retirement metadata verified against repository reality. No retired command is accidentally callable. Provider boundary is correct: `_provider_from_name()` in CLI only; default mock; Yahoo opt-in only.

**One cleanup candidate found:** Three sub-app groups are declared and registered in `main.py` but contain zero commands: `evidence_app` (`atlas evidence`), `reason_app` (`atlas reason`), `risk_app` (`atlas risk`). These are residual scaffolding from the retired commands `atlas evidence assess`, `atlas reason analyze`, and `atlas risk size`. They expose empty CLI groups confusing to users. Removing them is a 6-line-per-group change with zero behavioral impact.

**Stale metadata confirmed accurate:** All `removal_criteria` strings verified:
- `atlas evidence assess`: `atlas.evidence` still imported by comparison, decision_journal, watchlist_review ✓
- `atlas risk size`: `RiskAnalysis` still imported by conversation and intelligence ✓
- `atlas portfolio review`: `PortfolioReviewEngine` still instantiated by `atlas/home/engine.py` ✓

**Sprint 174 recommended target:** Remove empty shell CLI app groups (`evidence_app`, `reason_app`, `risk_app`) and close the CLI cleanup track. This closes a 15th cleanup track.

---

## 2026-07-03: Sprint 172 — Release Candidate Checkpoint After 14 Cleanup Closures

Decision: Atlas is release-candidate stable after 14 cleanup track closures.

**Rationale:** After closing analysis, decision, providers, portfolio boundary, evidence, reasoning, risk, principles, comparison, home, intelligence, conversation, dashboard, and portfolio intelligence capability cleanup tracks (Sprints 141–171), Atlas remains stable. Deleted modules remain absent, active modules remain importable, retired CLI paths remain retired, provider boundaries remain unchanged, and release verification remains green.

**Verification results:**
- All 13 deleted modules absent ✓
- All 9 active packages importable ✓
- All 7 retired CLI commands remain retired; `_REGISTRY` empty ✓
- All active CLI commands remain active ✓
- Provider boundaries unchanged across all 6 audited packages ✓
- 1524 tests passed, 3 skipped ✓
- `scripts/verify_release_candidate.sh` — RC2 green ✓
- `scripts/run_daily_brief_demo.sh` — provider-free, passes ✓
- No stale active runtime references found ✓

**Notable stale symbol classifications (all expected):**
- `atlas/domains/decision/engine.py` `ReasoningEngine` — distinct Blueprint-layer class, not the deleted `atlas.reasoning.ReasoningEngine`
- `atlas/providers/yahoo.py` `YahooCompany`, `YahooFinancials`, `YahooMarketData` — active internal types in opt-in Yahoo provider, not stale references
- `atlas/capabilities/portfolio_intelligence/models.py` legacy type doc-comments — migration notes only, not imports

**Sprint 173 recommended target:** Audit `atlas/cli/` deprecated command registry — after 14 cleanup closures and two RC checkpoints, the CLI command surface is the next smallest high-leverage audit target.

---

## 2026-07-03: Sprint 171 — Close Portfolio Intelligence Capability Cleanup Track

Decision: Close the `atlas/capabilities/portfolio_intelligence/` cleanup track. No further cleanup work is warranted.

**Rationale:** After inventory (Sprint 170) and final verification (Sprint 171), the portfolio intelligence capability contains only active, intentional code. `PortfolioIntelligenceCapability.analyze()` is the sole public method, consumed by 5 production packages (decision, intelligence, conversation, dashboard, providers). All 4 exports are active. Dependency surface is minimal — the capability depends only on `atlas.shared.entities` and its own sibling models module. No provider imports. No network calls. No deleted-module imports. No circular dependencies. Further cleanup would create churn without architectural benefit.

**Final verification (Sprint 171):** All 4 exports importable. All 5 production consumer packages confirmed active. Provider boundary confirmed: no concrete provider class imported anywhere in the capability. Zero stale closed-track imports. No Blueprint-aligned successor introduced. No cleanup action warranted.

**Docstring cleanup performed:** Removed stale "Future expansion" note (`themes`, `knowledge_context` fields never added) and completed-migration field-mapping table from `PortfolioFitInput` docstring in `models.py`. Documentation-only change; zero runtime impact.

**Closed-track summary (14 tracks):**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — CLOSED Sprint 155
- Principles package — CLOSED Sprint 158
- Comparison package — CLOSED Sprint 160
- Home package — CLOSED Sprint 162
- Intelligence package — CLOSED Sprint 165
- Conversation package — CLOSED Sprint 167
- Dashboard package — CLOSED Sprint 169
- **Portfolio intelligence capability — CLOSED Sprint 171**

**Sprint 172 recommended target:** Release candidate checkpoint — after closing 14 cleanup tracks, Atlas should run a full RC checkpoint before starting another broad package audit. Pattern matches Sprint 163 (RC after 10 tracks).

---

## 2026-07-03: Sprint 170 — Portfolio Intelligence Capability Audit Checkpoint

Decision: `atlas/capabilities/portfolio_intelligence/` is clean and architecturally exemplary. No cleanup work is warranted.

**Finding — package identity:** `atlas/portfolio_intelligence/` does NOT exist as a top-level package. The legacy `PortfolioIntelligenceEngine` was deleted Sprint 128; `atlas.analysis.portfolio` was deleted Sprint 135. The active Blueprint-aligned surface is `atlas/capabilities/portfolio_intelligence/` (3 modules, 4 exports, 471 lines total).

**Rationale:** After audit-first inventory (Sprint 170), the capability package contains only active, intentional code. `PortfolioIntelligenceCapability.analyze()` is the sole public method, consumed by 5 production packages (decision, intelligence, conversation, dashboard, providers). All 4 exports are active. All 17 private helpers are active. Dependency surface is minimal — the capability depends only on `atlas.shared.entities` (Holding, Portfolio) and its own sibling models module. No provider imports. No network calls. No deleted-module imports. No circular dependencies.

**Notable:** This is the most architecturally sound capability audited so far. The dependency direction is exemplary: providers supply `PortfolioFitInput` → CLI passes to engines → engines pass to capability. The capability knows nothing about providers.

**Stale comment candidate:** `models.py:42–44` contains a "Future expansion" note for `themes` and `knowledge_context` fields that were never added to `PortfolioFitInput`. Docstring-only — no runtime impact. Cleanup candidate for Sprint 171.

**Sprint 171 recommended target:** Close `atlas/capabilities/portfolio_intelligence/` cleanup track — optional docstring cleanup (stale future-expansion note) + documentation track closure.

---

## 2026-07-03: Sprint 169 — Close Dashboard Cleanup Track

Decision: Close the `atlas/dashboard/` cleanup track. No cleanup work is warranted.

**Rationale:** After inventory (Sprint 168) and final verification (Sprint 169), the dashboard package contains only active, intentional code. `DashboardEngine.build()` is the sole public method, active at 1 production call site (CLI `atlas dashboard show`). All 6 exports are active. All 17 private helpers are active. Dashboard has the cleanest provider boundary of any audited package — it imports no concrete provider class at all. `CompanyDataProvider` is used only as a type annotation in `DashboardInput.provider`. Provider selection lives entirely at the CLI layer. No stale imports. No Blueprint-aligned successor. Further cleanup would create churn without architectural benefit.

**Final verification (Sprint 169):** All 6 exports importable. `atlas dashboard show` CLI entrypoint confirmed active. Provider boundary confirmed cleanest of any audited package. Zero stale closed-track imports. No new Blueprint successor. No cleanup action warranted.

**Closed-track summary (13 tracks):**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — CLOSED Sprint 155
- Principles package — CLOSED Sprint 158
- Comparison package — CLOSED Sprint 160
- Home package — CLOSED Sprint 162
- Intelligence package — CLOSED Sprint 165
- Conversation package — CLOSED Sprint 167
- **Dashboard package — CLOSED Sprint 169**

**Sprint 170 recommended target:** Audit `atlas/portfolio_intelligence/` package — a major active domain-adjacent runtime surface, natural next step after dashboard is closed.

---

## 2026-07-03: Sprint 168 — Dashboard Package Audit Checkpoint

Decision: `atlas/dashboard/` package is clean. No cleanup work is warranted.

**Rationale:** After audit-first inventory (Sprint 168), the dashboard package contains only active, intentional code. All 6 exports are active. `DashboardEngine.build()` is the sole public method, active at 1 production call site (CLI `atlas dashboard show`). All 17 private helpers are active. No zero-caller symbols. No stale exports. No closed-track import residue. No Blueprint-aligned successor exists. Dashboard has the cleanest provider boundary of any audited package — it imports only `CompanyDataProvider` as a type annotation and never imports any concrete provider class. Provider selection lives entirely at the CLI layer. Dashboard does not import `atlas.intelligence` or `atlas.conversation` — it orchestrates independently at the application layer.

**Notable:** Dashboard calls `_dashboard_text_without_principles()` twice — once before `PrinciplesEngine.check()` (for principles pre-check on draft text) and once via `render_dashboard()` at CLI time. This is an intentional design pattern.

**Sprint 169 recommended target:** Close the dashboard cleanup track — documentation-only sprint confirming audit findings. Pattern matches Sprint 150, 155, 158, 160, 162, 165, and 167.

---

## 2026-07-03: Sprint 167 — Close Conversation Cleanup Track

Decision: Close the `atlas/conversation/` cleanup track. No cleanup work is warranted.

**Rationale:** After inventory (Sprint 166) and final verification (Sprint 167), the conversation package contains only active, intentional code. `ConversationEngine.answer()` is the sole public method, active at 1 production call site (CLI `atlas ask`). All 6 exports are active. All 16 private helpers are active. `IntelligenceEngine` dependency is intentional — consumed by `_answer_company_analysis` and `_answer_general_guidance` intent branches. `RiskAnalysis` dependency is intentional, optional, and shallow. No stale imports. No Blueprint successor. Further cleanup would create churn without architectural benefit.

**Final verification (Sprint 167):** All 6 exports importable. `atlas ask` CLI entrypoint confirmed active. Intelligence and risk dependencies confirmed intentional. Zero stale closed-track imports. No new Blueprint successor. Provider boundary unchanged. No cleanup action warranted.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — CLOSED Sprint 155
- Principles package — CLOSED Sprint 158
- Comparison package — CLOSED Sprint 160
- Home package — CLOSED Sprint 162
- Intelligence package — CLOSED Sprint 165
- **Conversation package — CLOSED Sprint 167**

**Sprint 168 recommended target:** Audit `atlas/dashboard/` package — another active runtime/application-facing surface, natural next step after conversation is closed.

---

## 2026-07-03: Sprint 166 — Conversation Package Audit Checkpoint

Decision: `atlas/conversation/` package is clean. No cleanup work is warranted.

**Rationale:** After audit-first inventory (Sprint 166), the conversation package contains only active, intentional code. All 6 exports are active and consumed by CLI (`atlas ask`) and `atlas/principles/engine.py` (TYPE_CHECKING only). `ConversationEngine.answer()` is the sole public method, active at 1 production call site (CLI). All 16 private helpers are active. No zero-caller symbols. No stale exports. No closed-track import residue. No Blueprint-aligned successor exists. Provider boundary is clean and opt-in — `MockCompanyAnalysisProvider` is the default fallback; `YahooFinanceProvider` never imported. Intelligence dependency (`IntelligenceEngine`) is intentional and consumed by 2 of 8 intent branches. `RiskAnalysis` dependency is intentional, optional, and shallow.

**Sprint 167 recommended target:** Close the conversation cleanup track — documentation-only sprint confirming audit findings. Pattern matches Sprint 150, 155, 158, 160, 162, and 165.

---

## 2026-07-03: Sprint 165 — Close Intelligence Cleanup Track

Decision: Close the `atlas/intelligence/` cleanup track. No cleanup work is warranted.

**Rationale:** After inventory (Sprint 164) and final verification (Sprint 165), the intelligence package contains only active, intentional code. `IntelligenceEngine.analyze()` is the sole public method, active at 3 production call paths (CLI×2, conversation). All 5 exports are active. All 13 private helpers are active. `RiskAnalysis` dependency is intentional, optional, and shallow. No stale imports. No Blueprint successor. Further cleanup would create churn without architectural benefit.

**Final verification (Sprint 165):** All 5 exports importable. `atlas intelligence analyze` and `atlas daily summary` CLI paths confirmed active. Conversation and suitability integrations confirmed intentional. Zero stale closed-track imports. No new Blueprint successor. No provider boundary violation. No cleanup action warranted.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — CLOSED Sprint 155
- Principles package — CLOSED Sprint 158
- Comparison package — CLOSED Sprint 160
- Home package — CLOSED Sprint 162
- **Intelligence package — CLOSED Sprint 165**

**Sprint 166 recommended target:** Audit `atlas/conversation/` package — an active runtime orchestration surface that depends on intelligence (now closed) and is a natural next step in the cleanup sequence.

---

## 2026-07-03: Sprint 164 — Intelligence Package Audit Checkpoint

Decision: `atlas/intelligence/` package is clean. No cleanup work is warranted.

**Rationale:** After audit-first inventory (Sprint 164), the intelligence package contains only active, intentional code. All 5 exports are active and consumed by CLI (2 commands), `atlas/conversation/engine.py`, and `atlas/suitability/engine.py`. `IntelligenceEngine.analyze()` is the sole public method and has 3 production call sites. All 13 private helpers are internal and active. No zero-caller symbols exist. No stale exports. No closed-track import residue. No Blueprint-aligned successor exists. Provider boundary is clean and opt-in. The `RiskAnalysis` dependency is intentional, optional at call time, and shallow (4 fields read).

**One correction made:** `atlas/cli/deprecations.py` `removal_criteria` for `atlas risk size` previously mentioned `atlas/reasoning engines` as a `RiskAnalysis` caller (stale since Sprint 153). Corrected to `atlas/conversation and atlas/intelligence engines`. Metadata-only, no runtime impact.

**Sprint 165 recommended target:** Close the intelligence cleanup track — documentation-only sprint confirming audit findings. Pattern matches Sprint 150, 155, 158, 160, and 162.

---

## 2026-07-03: Sprint 163 — Release Candidate Checkpoint After Cleanup Closures

Decision: Sprint 163 confirms Atlas release-candidate stability after 10 cleanup tracks were closed.

**Rationale:** After closing analysis, decision, providers, portfolio boundary, evidence, reasoning, risk, principles, comparison, and home cleanup tracks, Atlas remains stable. Deleted modules remain absent, active modules remain importable, retired CLI paths remain retired, provider boundaries remain unchanged, and release verification remains green.

**Verification summary:**
- Deleted modules: `atlas/reasoning/`, `atlas/analysis/portfolio.py`, `atlas/analysis/growth.py`, `atlas/analysis/macro.py`, `atlas/analysis/moat.py`, `atlas/analysis/quality.py`, `atlas/analysis/sentiment.py`, `atlas/analysis/technicals.py`, `atlas/analysis/valuation.py` — all confirmed absent ✓
- Retired symbols (`ReasoningEngine` from `atlas.reasoning`, `PortfolioIntelligenceEngine`, `check_reasoning_report`, `check_intelligence_report`, `check_suitability_assessment`, `PortfolioAnalysis`, `PortfolioSignal`, `render_comparison_result`, etc.) — all hits are expected guardrail tests, docs/comments, or distinct Blueprint-layer classes (e.g. `atlas/domains/decision/` defines its own `ReasoningEngine`, unrelated to deleted `atlas.reasoning`) ✓
- Active packages (`atlas.evidence`, `atlas.risk`, `atlas.principles`, `atlas.comparison`, `atlas.home`) — all importable, all exports intact ✓
- Retired CLI commands (`atlas reason analyze`, `atlas risk size`, `atlas evidence assess`, `atlas portfolio analyze`, `atlas portfolio review`, `atlas watchlist analyze`, `atlas daily brief`) — all in `_RETIRED_REGISTRY`, none registered in `_REGISTRY`, none callable ✓
- Active CLI commands (`atlas home`, `atlas compare`, `atlas daily summary`, `atlas intelligence analyze`, etc.) — all registered and active ✓
- Provider boundaries — `atlas/comparison/` and `atlas/home/` both use `MockCompanyAnalysisProvider` as default; `YahooFinanceProvider` remains CLI opt-in only via `--provider yahoo`; no new provider imports introduced ✓
- Demo: provider-free, deterministic ✓
- RC2: green ✓
- Tests: 1460 passed, 3 skipped ✓

**Stale reference noted (non-blocking):** `atlas/cli/deprecations.py` `removal_criteria` for `atlas risk size` still mentions `atlas/reasoning engines` as a `RiskAnalysis` caller. `atlas/reasoning/` was deleted Sprint 153. The actual current callers are `atlas/intelligence/engine.py` and `atlas/conversation/engine.py`. This is a retired command record (never executed), not a stale active import. No runtime impact. Can be corrected in Sprint 164 during `atlas/intelligence/` audit if desired.

**Sprint 164 recommended target:** Audit `atlas/intelligence/` package. `atlas/intelligence/` is a larger runtime surface and should be audited now that the cleanup closure sequence has been release-verified.

---

## 2026-07-03: Sprint 162 — Close Home Cleanup Track

Decision: Close the `atlas/home/` cleanup track. No cleanup work is warranted.

**Rationale:** After inventory (Sprint 161) and final verification (Sprint 162), the home package contains only active, intentional code. `AtlasHomeEngine` is used by the active `atlas home` CLI command. Provider coupling is clean: `MockCompanyAnalysisProvider` is the default (deterministic, local); `YahooFinanceProvider` is CLI opt-in only and never imported by `atlas/home/` directly. No Blueprint successor exists. Further cleanup would create churn without architectural benefit.

**Final verification (Sprint 162):** All 7 exports importable. CLI caller confirmed active. Zero stale closed-track imports. No new Blueprint successor. No provider boundary violation.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — CLOSED Sprint 155
- Principles package — CLOSED Sprint 158
- Comparison package — CLOSED Sprint 160
- **Home package — CLOSED Sprint 162**

**Sprint 163 recommended target:** Audit `atlas/cli/` deprecated command registry — verify each removal criterion is still accurate, check for stale references to now-deleted modules, confirm no deprecated commands have been reintroduced.

---

## 2026-07-03: Sprint 161 — Home Package Audit Checkpoint

Decision: Audit `atlas/home/` as a Group B provider-coupled module. Audit-only sprint. No runtime changes.

**Findings:**
- 2 modules: `__init__.py` (19 lines), `engine.py` (611 lines). 7 exports.
- `AtlasHomeEngine` is active: 1 production caller (CLI `atlas home`), 15 tests. Single `.build()` public method. No zero-caller methods.
- Provider coupling is intentional and clean: `CompanyDataProvider` as type annotation; `MockCompanyAnalysisProvider` as default (deterministic, local). `YahooFinanceProvider` only reachable via `--provider yahoo` CLI flag — never imported by `atlas/home/` itself. Pattern identical to `atlas/comparison/`.
- All 7 exports are active or intentional sub-types. `AtlasHomePriority`, `AtlasHomeMonitoring`, `AtlasHomeSummary` have zero direct external production callers but are correct sub-types of `AtlasHomeOutput`.
- Zero stale closed-track imports. Zero dead code. Zero Blueprint pressure.
- `atlas/home/` **consumes** `WatchlistInput` from `atlas/capabilities/watchlist_intelligence/` — correct direction.
- No `atlas/domains/home/` or `atlas/capabilities/home/` exists. No Blueprint successor.
- `atlas/capabilities/daily_brief/` is conceptually adjacent but not a successor — different scope (daily briefing vs. personalized investor dashboard).

**Sprint 162 recommended target:** Close the home cleanup track — documentation-only sprint confirming no cleanup is warranted. See `docs/HomeCleanupPlan.md`.

---

## 2026-07-03: Sprint 160 — Close Comparison Cleanup Track

Decision: Close the `atlas/comparison/` cleanup track. No cleanup work is warranted.

**Rationale:** After inventory (Sprint 159) and final verification (Sprint 160), the comparison package contains only active, intentional code. `InvestmentComparisonEngine` is used by the active `atlas compare` CLI command. Provider coupling is clean: `MockCompanyAnalysisProvider` is the default (deterministic, local); `YahooFinanceProvider` is CLI opt-in only and never imported by `atlas/comparison/` directly. No Blueprint successor exists. Further cleanup would create churn without architectural benefit.

**Final verification (Sprint 160):** All 9 exports importable. CLI caller confirmed active. Zero stale closed-track imports. No new Blueprint successor. No provider boundary violation.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — CLOSED Sprint 155
- Principles package — CLOSED Sprint 158
- **Comparison package — CLOSED Sprint 160**

**Sprint 161 recommended target:** Audit `atlas/home/` — Group B provider-coupled module. Inventory modules, map callers, verify provider boundary, check Blueprint overlap, classify cleanup candidates.

---

## 2026-07-03: Sprint 159 — Comparison Package Audit Checkpoint

Decision: Audit `atlas/comparison/` as a provider-coupled module. Audit-only sprint. No runtime changes.

**Findings:**
- 2 modules: `__init__.py` (23 lines), `engine.py` (1009 lines). 9 exports.
- `InvestmentComparisonEngine` is active: 1 production caller (CLI `atlas compare`), 1 test file. Clean `.compare()` public API; no zero-caller methods.
- Provider coupling is intentional and clean: `CompanyDataProvider` as type annotation; `MockCompanyAnalysisProvider` as default (deterministic, local). `YahooFinanceProvider` only reachable via `--provider yahoo` CLI flag — never imported by `atlas/comparison/` itself.
- All 9 exports are active or intentional sub-types (`InvestmentComparisonObservation`, `InvestmentComparisonSection` have zero direct external callers but are correct sub-types of the active report).
- Zero stale closed-track imports. Zero dead code. Zero Blueprint pressure.
- `atlas/decision/comparison.py` (130 lines) is a completely separate module — score-ranked ticker comparison for the decision flow. No overlap with `InvestmentComparisonEngine`.
- No `atlas/domains/comparison/` or `atlas/capabilities/comparison/` exists. No Blueprint successor.

**Sprint 160 recommended target:** Close the comparison cleanup track — documentation-only sprint confirming no cleanup is warranted. See `docs/ComparisonCleanupPlan.md`.

---

## 2026-07-03: Sprint 158 — Close Principles Cleanup Track

Decision: Close the `atlas/principles/` cleanup track. No further cleanup work is warranted.

**Rationale:** After audit (Sprint 156) and removal of two zero-caller convenience functions (Sprint 157), Sprint 158 confirmed the principles package contains only active, intentional code. `check_reasoning_report` was removed Sprint 152. `check_intelligence_report` and `check_suitability_assessment` were removed Sprint 157 after `atlas/reasoning/` was deleted. The remaining 9 exports are all active or well-tested. Further cleanup would create churn without architectural benefit.

**Final verification (Sprint 158):** All 9 exports importable. 5 known callers confirmed. CLI active. Zero removed-check references in active code. Zero provider imports. Zero stale closed-track imports. No Blueprint successor introduced.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — CLOSED Sprint 155
- **Principles package — CLOSED Sprint 158**

**Sprint 159 recommended target:** Audit `atlas/comparison/` — provider-coupled module with known Blueprint overlap (`InvestmentComparisonEngine`). Audit-first: inventory modules, map callers, verify provider boundary, check Blueprint overlap, classify cleanup candidates.

---

## 2026-07-03: Sprint 157 — Remove Dormant Principles Report Checks

Decision: Remove `check_intelligence_report` and `check_suitability_assessment` from `atlas/principles/engine.py` and `atlas/principles/__init__.py`.

**Rationale:** Sprint 156 audit identified both functions as zero-caller (no production or test callers). Each carried a lazy runtime import and TYPE_CHECKING parameter annotation — identical pattern to `check_reasoning_report` removed in Sprint 152. Removal reduces principles public API from 11 to 9 exports with no production behavior changes.

**Changes:** Deleted 2 functions, 2 lazy imports (`render_intelligence_report`, `render_suitability_assessment`), 2 TYPE_CHECKING import names (`IntelligenceReport`, `SuitabilityAssessment`). Updated `__init__.py` imports and `__all__`. Updated guardrail tests. Updated docs.

**Active API preserved:** `PrinciplesEngine`, `PrinciplesCheck`, `render_principles_check`, `check_conversation_response`, `check_text_against_principles`, and all 4 type-system symbols remain unchanged. All 5 production callers unaffected.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — CLOSED Sprint 155
- **Principles package — CLOSED Sprint 157**

**Sprint 158 recommended target:** Close principles cleanup track formally (documentation-only sprint confirming stable post-Sprint-157 state). No code changes expected.

---

## 2026-07-02: Sprint 156 — Principles Package Audit Checkpoint

Decision: Audit `atlas/principles/` as a Group C self-contained module. Audit-only sprint. No runtime changes.

**Findings:**
- 2 modules: `__init__.py` (27 lines), `engine.py` (324 lines).
- 11 exports. Core engine active: `PrinciplesEngine` and `PrinciplesCheck` used by 5 production engines (comparison, dashboard, decision_journal, portfolio_review, watchlist_review) + CLI.
- `render_principles_check` used by active `atlas principles check` CLI command.
- Sprint 152 removal of `check_reasoning_report` verified clean — no `atlas.reasoning` references remain.
- **Two zero-caller convenience functions identified:** `check_intelligence_report` and `check_suitability_assessment` — zero production callers, zero test callers. Each contains a lazy import and a TYPE_CHECKING annotation parameter type; identical pattern to `check_reasoning_report` removed in Sprint 152.
- Boundary clean: zero provider imports, zero upward dependencies at module load time.
- No Blueprint-aligned successor; no overlap with `atlas/domains/` or `atlas/capabilities/`.
- No stale closed-track imports.

**Sprint 157 recommended target:** Remove `check_intelligence_report` and `check_suitability_assessment` — two zero-caller convenience functions — following the Sprint 152 pattern. Reduces principles API from 11 to 9 exports. See `docs/PrinciplesCleanupPlan.md`.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — CLOSED Sprint 155
- **Principles package — ACTIVE (Sprint 157 cleanup planned)**

---

## 2026-07-02: Sprint 155 — Close Risk Cleanup Track

Decision: Close the `atlas/risk/` cleanup track. No cleanup work is warranted.

**Rationale:** After inventory (Sprint 154), caller verification, stale import audit, and Blueprint overlap review, the risk package contains only active, intentional code. `RiskAnalysis` is still used by 2 production engines (`conversation`, `intelligence`). `RiskEngine` has zero production callers but shares a file with the active type — deletion requires file surgery with no Blueprint migration target. Further cleanup would create churn without architectural benefit.

**Final verification (Sprint 155):** All 8 exports importable. 2 known callers confirmed. Zero provider imports. Zero stale closed-track imports. No Blueprint successor introduced.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — CLOSED Sprint 153
- Risk package — **CLOSED Sprint 155**

**Sprint 156 recommended target:** Audit Group C self-contained module `atlas/principles/` — `check_reasoning_report()` was removed Sprint 152, reducing the principles API; remaining exports and callers should be inventoried and confirmed stable.

---

## 2026-07-02: Sprint 154 — Risk Package Audit Checkpoint

Decision: Audit `atlas/risk/` as a Group C self-contained module. Audit-only sprint. No runtime changes.

**Findings:**
- 2 modules: `__init__.py` (21 lines), `engine.py` (448 lines).
- 8 exports in `__all__`: all reachable, but only `RiskAnalysis` has active production callers.
- **`RiskAnalysis` is actively used by 2 production engines:**
  - `atlas/conversation/engine.py` — optional context field in `ConversationInput`
  - `atlas/intelligence/engine.py` — optional context in `IntelligenceInput`/`IntelligenceReport`; accesses `.position_sizing.*` and `.deployment_plan.*` fields
- `RiskEngine` has zero production instantiation points — `atlas risk size` was retired Sprint 88.
- `RiskEngine` and `RiskAnalysis` share the same file. Deleting `RiskEngine` requires separating `RiskAnalysis` to a new file (surgery). No Blueprint migration target exists. Surgery risk outweighs value.
- `render_risk_analysis` is test-only (zero production callers).
- Self-contained boundary: imports only `atlas.analysis.scores.clamp_score` (utility, still active) and `atlas.market.MarketRegime` (expected Group B dependency). No provider, CLI, conversation, or intelligence imports.
- Zero stale closed-track imports (no reasoning, no deleted analysis modules).
- No Blueprint-aligned successor: no `atlas/domains/risk/` or `atlas/capabilities/risk/` exists.
- No dead code, no stale migration residue, no consolidation candidates.
- Full findings in `docs/RiskCleanupPlan.md`.

**Sprint 155 recommendation:** Close risk cleanup track (documentation-only). No cleanup work warranted. `RiskAnalysis` must remain; `RiskEngine` cannot be removed without risky surgery; no Blueprint successor.

---

## 2026-07-02: Sprint 153 — Delete atlas/reasoning/ Package

Decision: Delete `atlas/reasoning/` package entirely (engine.py + __init__.py, 594 lines).

**Rationale:** Sprint 152 removed `check_reasoning_report()` from `atlas/principles/engine.py`, leaving zero production-code dependencies on `atlas.reasoning`. Sprint 153 completes the two-sprint sequence by deleting the dormant package. `atlas reason analyze` was retired Sprint 87; no runtime behavior changes.

**Changes made:**
- `atlas/reasoning/` directory deleted (engine.py, __init__.py, __pycache__/).
- `atlas/cli/deprecations.py` — updated `atlas reason analyze` removal_criteria to confirm deletion done.
- `tests/test_reasoning_engine.py` — rewritten as Sprint 153 deletion guards; engine behavior tests removed; CLI retirement and migration guardrails retained.
- `tests/test_reason_analyze_deprecation.py` — `test_reasoning_engine_module_remains_on_disk` replaced with `test_reasoning_package_deleted` (asserts ModuleNotFoundError).
- `tests/test_reasoning_package_sprint151.py` — removed all `atlas.reasoning` import tests; added Sprint 153 deletion guard; Sprint 152 and closed-track guardrails retained.
- `tests/test_risk_size_deprecation.py` — removed `atlas/reasoning/engine.py` from `RISK_ANALYSIS_CALLERS` tuple.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — CLOSED Sprint 150
- Reasoning package — **CLOSED Sprint 153**

---

## 2026-07-02: Sprint 152 — Remove Dormant Principles Reasoning Report Check

Decision: Remove `check_reasoning_report()` from `atlas/principles/engine.py`. This was a zero-caller function whose sole purpose was to call `render_reasoning_report()` from `atlas.reasoning` via a lazy import. Removing it eliminates the only remaining production-code dependency on `atlas.reasoning`.

**Changes made:**
- `atlas/principles/engine.py` — deleted `check_reasoning_report()` (4 lines), removed TYPE_CHECKING import of `ReasoningReport`, removed lazy import of `render_reasoning_report`.
- `atlas/principles/__init__.py` — removed `check_reasoning_report` import and `__all__` entry (11 active exports remain).
- `atlas/cli/deprecations.py` — updated `atlas reason analyze` removal_criteria to reflect Sprint 152 blocker resolved.
- `tests/test_reason_analyze_deprecation.py` — replaced `test_principles_engine_lazy_import_is_still_present` with `test_principles_engine_no_longer_references_atlas_reasoning` and `test_principles_engine_does_not_export_check_reasoning_report`.
- `tests/test_reasoning_package_sprint151.py` — replaced Sprint 151 lazy-import presence assertions with Sprint 152 removal assertions.

**Result:** `atlas/principles/engine.py` has zero references to `atlas.reasoning`. No production code references `atlas.reasoning` at runtime. `atlas/reasoning/` package remains on disk — deletion deferred to Sprint 153.

**Sprint 153 recommendation:** Delete `atlas/reasoning/` package entirely (engine.py + __init__.py, 594 lines of dormant code).

---

## 2026-07-02: Sprint 151 — Reasoning Package Audit Checkpoint

Decision: Audit `atlas/reasoning/` as a Group C self-contained module. Audit-only sprint. No runtime changes.

**Findings:**
- 2 modules: `__init__.py` (19 lines), `engine.py` (575 lines).
- 7 exports in `__all__`: all reachable from `__init__.py`, but zero have active runtime production callers.
- CLI command `atlas reason analyze` was retired Sprint 87. Zero production code instantiates `ReasoningEngine`.
- Sole production-code reference: `atlas/principles/engine.py` holds (a) a TYPE_CHECKING-only import of `ReasoningReport` (line 9) and (b) a lazy runtime import of `render_reasoning_report` inside `check_reasoning_report()` (line 147).
- `check_reasoning_report()` has zero external callers — confirmed Sprint 87, confirmed Sprint 151.
- `check_reasoning_report()` is exported in `atlas/principles/__init__.py` but unreachable in any production path.
- The lazy import was introduced to avoid a transitive circular import chain (`atlas.reasoning` imports `atlas.analysis.engine`, `atlas.capabilities.portfolio_intelligence`, `atlas.risk`, `atlas.economics`, `atlas.market`, `atlas.monitoring`, `atlas.themes`).
- Self-contained boundary: zero imports from `atlas/providers/`, `atlas/cli/`, `atlas/dashboard/`, `atlas/conversation/`, `atlas/intelligence/`, `atlas/domains/`, or deleted analysis modules.
- Blueprint overlap: `atlas/domains/decision/engine.py` has its own `ReasoningEngine` and `Evidence` (completely different purpose — Blueprint decision reasoning). No migration warranted. No conflict.
- Zero stale closed-track imports.
- No dead private helpers; all are internal to the dormant engine.
- Full findings in `docs/ReasoningCleanupPlan.md`.

**Sprint 152 recommendation:** Remove `check_reasoning_report()` from `atlas/principles/engine.py` (zero callers, only production dependency on `atlas.reasoning`). This unblocks Sprint 153: full deletion of `atlas/reasoning/` package (594 lines of dormant code).

---

## 2026-07-02: Sprint 150 — Close Evidence Cleanup Track

Decision: Close the `atlas/evidence/` cleanup track. No cleanup work is warranted.

**Rationale:** After inventory (Sprint 149), caller verification, stale import audit, Blueprint overlap review, and Sprint 150 final verification, the evidence package contains only active, intentional code. It is self-contained, imports only `atlas.language`, is actively used by 3 production engines (`comparison`, `decision_journal`, `watchlist_review`), and has no dead code, no stale migration residue, and no Blueprint-aligned successor. Further cleanup would create churn without architectural benefit.

**Final verification (Sprint 150):** All 9 exports importable. 3 known callers confirmed. Zero upward dependencies. Zero stale imports. No successor introduced.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — CLOSED Sprint 148
- Evidence package — **CLOSED Sprint 150**

**Sprint 151 recommended target:** Audit Group C self-contained module `atlas/reasoning/` — known lazy import tech debt (`atlas/principles/` lazy import of `render_reasoning_report`, documented Sprint 87). Smallest safe Group C audit-first target.

---

## 2026-07-02: Sprint 149 — Evidence Package Audit Checkpoint

Decision: Audit `atlas/evidence/` as a Group C self-contained module. Audit-only sprint. No runtime changes.

**Findings:**
- 2 modules: `__init__.py` (23 lines), `engine.py` (540 lines).
- 9 exports in `__all__`: all intentional. No stale exports.
- 3 production engine callers confirmed (exactly as expected): `atlas/comparison/engine.py`, `atlas/decision_journal/engine.py`, `atlas/watchlist_review/engine.py`. No additional callers found.
- All 3 callers inject `EvidenceQualityEngine` and consume `EvidenceAssessment` fields for scoring and routing.
- Self-contained boundary: imports only from `atlas.language` (Group D infrastructure). No provider, CLI, dashboard, conversation, intelligence, or decision imports.
- Zero stale closed-track imports.
- `render_evidence_assessment` is exported but has zero production callers — test-only usage in `test_evidence_engine.py`. Not a critical cleanup target.
- `atlas/domains/decision/` has its own `Evidence`/`EvidenceStrength`/`EvidenceCategory` types — naming overlap only. Different purpose (structured evidence items with category taxonomy) vs. `atlas/evidence/` (source quality assessment engine). No migration warranted.
- No Blueprint-aligned successor exists.
- No dead helpers, no stale migration residue, no duplicated logic.

**Sprint 150 recommendation:** Close the evidence cleanup track — no cleanup work is warranted. Package is stable and active.

---

## 2026-07-02: Sprint 148 — Close Portfolio Boundary Cleanup Track

Decision: Remove the stale `PortfolioFitInput` import from `atlas/adapters/portfolio.py` and close the portfolio boundary cleanup track.

**Rationale:** After deleting `atlas.analysis.portfolio` (Sprint 135), removing the identity adapter `portfolio_fit_input_from_profile` (Sprint 137), auditing all remaining callers (Sprint 147), and now removing the final stale `PortfolioFitInput` import, the adapter boundary is intentional and stable. `Portfolio` and `PortfolioPosition` are the correct permanent home for legacy CLI JSON-loading boundary types. No Blueprint-aligned JSON-loading type exists as a replacement, and the adapter has no upward dependencies. No further cleanup is warranted.

**Change:** One import line removed from `atlas/adapters/portfolio.py`. Zero behavior change.

**Closed-track summary:**
- `atlas/analysis/` cleanup — CLOSED Sprint 141
- `atlas/decision/` cleanup — CLOSED Sprint 144
- Provider boundary audit — CLOSED Sprint 146
- Portfolio boundary — **CLOSED Sprint 148**

**Sprint 149 recommended target:** Audit Group C self-contained module `atlas/evidence/` — self-contained, no provider dependency, 3 active engine callers, no Blueprint successor yet. Smallest safe audit-first step.

---

## 2026-07-02: Sprint 147 — Portfolio Boundary Caller Audit

Decision: Audit all remaining callers of `Portfolio`, `PortfolioPosition`, and `legacy_portfolio_to_domain_portfolio` from `atlas/adapters/portfolio.py`. No runtime changes.

**Findings:**
- Zero stale `atlas.analysis.portfolio` imports in production code — deletion from Sprint 135 is complete and stable.
- 9 CLI `Portfolio.from_json_file` call sites across 9 commands: `ask`, `home`, `dashboard show`, `daily summary`, `portfolio summary`, `intelligence analyze`, `suitability analyze`, `risk-drift analyze`, `monitor`. All correct and permanent — these are the JSON-loading boundary.
- 8 engine files use `Portfolio` as a TYPE_CHECKING-only type annotation: `conversation`, `decision_context`, `dashboard`, `home`, `intelligence`, `monitoring`, `risk_drift`, `suitability`. All correct.
- 6 runtime callers of `legacy_portfolio_to_domain_portfolio`: CLI (×2), `conversation`, `dashboard`, `decision_engine`, `intelligence`, `portfolio_review`. All correct.
- `atlas/portfolio_review/engine.py` is the only engine that imports `Portfolio as LegacyPortfolio` at module runtime (not behind TYPE_CHECKING) — intentional: it constructs the review input from a legacy Portfolio.
- Adapter boundary is clean: no upward dependencies, no provider imports, no CLI imports.
- **One stale import in adapter:** `from atlas.capabilities.portfolio_intelligence import PortfolioFitInput` at line 33 — imported but unused. Left over from Sprint 133.
- No Blueprint-aligned JSON-loading type exists. `atlas.adapters.portfolio.Portfolio` is the correct permanent home.

**Sprint 148 target:** Remove stale `PortfolioFitInput` import from adapter, add boundary guardrail, close portfolio boundary track.

---

## 2026-07-02: Sprint 146 — Remove Stale Yahoo Provider Re-exports

Decision: Remove `YahooCompany`, `YahooFinancials`, `YahooMarketData` from `atlas/providers/__init__.py`.

**Rationale:** Zero external callers confirmed by repo-wide grep (Sprint 145 audit). These types are implementation details of `YahooFinanceProvider` — internal data transfer objects used within `yahoo.py` to fetch and parse raw Yahoo Finance API responses before assembling `CompanyAnalysis` and `PortfolioFitInput`. Exposing them in `__init__.py` incorrectly suggested they were part of the provider contract. Removing them from the public surface tightens the API to reflect actual usage without changing any runtime behavior.

**Changes:**
- `atlas/providers/__init__.py`: 3 imports and 3 `__all__` entries removed. File reduced from 19 to 14 lines. `__all__` reduced from 7 to 4 exports.
- `atlas/providers/yahoo.py`: unchanged. Types retained for internal use.
- `tests/test_provider_package_sprint145.py`: `test_sprint145_atlas_providers_all_exports` updated to expect only 4 active exports. 3 Sprint 146 guardrail tests added.
- 4 docs updated.

**Provider boundary audit track:** CLOSED. All identified cleanup complete.

**Recommended Sprint 147 target:** No remaining provider cleanup. Pivot to next technical debt area — `atlas/analysis/portfolio.py` caller migration audit or Group C self-contained module Blueprint wrappers.

---

## 2026-07-02: Sprint 145 — Provider Boundary Audit

Decision: Begin `atlas/providers/` boundary audit. Audit-only sprint. No runtime changes.

**Findings:**
- 4 modules, 539 lines total.
- `CompanyDataProvider` protocol: 2 methods. `get_company_analysis` has 7 production call sites; `get_portfolio_profile` has 4. Both return correct types (`CompanyAnalysis`, `PortfolioFitInput`). `get_portfolio_profile` returning `PortfolioFitInput` confirmed (Sprint 133).
- `MockCompanyAnalysisProvider`: clean, 5 supported tickers for analysis, 4 for portfolio profile (AMD intentionally excluded from portfolio profiles).
- `YahooFinanceProvider`: correct contract implementation. Yahoo-specific sub-methods (`get_company`, `get_financials`, `get_market_data`) are internal-only; no production code outside `providers/` calls them.
- Zero stale production imports. No boundary violations (providers do not import from decision/intelligence/CLI/dashboard).
- Blueprint alignment: both contract methods return stable, correct types.
- **Three stale `__init__.py` exports identified:** `YahooCompany`, `YahooFinancials`, `YahooMarketData` — zero external callers. These are implementation details of `YahooFinanceProvider` that leaked into the public API.

**Sprint 146 recommended target:** Remove `YahooCompany`, `YahooFinancials`, `YahooMarketData` from `atlas/providers/__init__.py`. Types stay in `yahoo.py`; only their public-API surface is tightened. Zero external callers confirmed. Low risk.

---

## 2026-07-02: Sprint 144 — Close Decision Cleanup Track

Decision: Formally close the `atlas/decision/` cleanup track after Sprints 142–144. No further cleanup sprints planned until a new dead-code finding or clear successor architecture emerges.

**Rationale:** After package inventory (Sprint 142), dead renderer deletion (Sprint 143), export verification, and release guardrails, the decision package contains only active, intentional modules. All 5 `__init__.py` exports are healthy. All 7 modules have clear responsibilities. No stale imports. No dead code. Further cleanup would create churn without architectural benefit.

**Final stable package:** `__init__.py`, `decision_engine.py`, `decision_context.py`, `decision_result.py`, `decision_renderer.py`, `comparison.py`, `memory.py`.

**Why `decision_engine.py` remains:** Foundational composition engine. Single external production caller (`atlas/intelligence/engine.py`). Composes portfolio fit, comparison, watchlist intelligence, and memory. No Blueprint-aligned successor yet.

**Why `comparison.py` remains:** Canonical comparison location since Sprint 103. Active symbols: `ComparisonCandidate`, `ComparisonRanking`, `ComparisonResult`, `compare_tickers`. Dead renderer path deleted Sprint 143. Clean.

**Why `memory.py` remains:** Canonical memory/history location since Sprint 104. CLI `atlas memory save/show/compare` commands depend on it. All 7 public symbols active.

**Reopening condition:** Reopen when a new zero-caller dead function is found, when `decision_engine.py` has a clear Blueprint-aligned successor, or when the package accumulates new stale migration residue.

**Sprint 145 recommended target:** Provider boundary audit — inspect `atlas/providers/` for stale symbols, dead provider implementations, or boundary violations following the same audit-first pattern.

---

## 2026-07-02: Sprint 143 — Delete Dead Decision Comparison Renderer

Decision: Delete `render_comparison_result`, `_render_ranking`, and `_ranking_score` from `atlas/decision/comparison.py`. Zero external callers confirmed by repo-wide grep.

**Zero-caller audit findings:**
- `render_comparison_result`: only hit was its own definition and internal calls to `_render_ranking`. Zero external production callers. Zero CLI surface.
- `_render_ranking`: only called by `render_comparison_result` (now deleted).
- `_ranking_score`: only called by `_render_ranking` (now deleted).

**Changes:** 3 functions deleted (~45 lines). `comparison.py` reduced from 186 to ~141 lines. Active API (`ComparisonCandidate`, `ComparisonRanking`, `ComparisonResult`, `compare_tickers`) unchanged. Sprint 142 guardrail updated: `test_sprint142_render_comparison_result_is_importable` → `test_sprint143_render_comparison_result_deleted`. Docs updated.

**Behavior changes:** None. Comparison ranking, decision engine, CLI, memory, and all other behavior unchanged.

**Sprint 144 recommended target:** Decision package release checkpoint — verify the decision package is stable, confirm no further cleanup warranted, and close the decision cleanup track.

---

## 2026-07-02: Sprint 142 — Decision Package Cleanup Checkpoint

Decision: Begin `atlas/decision/` cleanup track with an audit-only sprint. No runtime changes.

**Findings:**
- 7 modules, 1010 lines total.
- All 5 `__init__.py` exports are active and intentional.
- `decision_engine.py` (474 lines): foundational — composes portfolio fit, comparison, watchlist intelligence, memory. No stale imports.
- `decision_context.py` (23 lines): clean frozen DTO. `Portfolio` TYPE_CHECKING-guarded.
- `decision_result.py` (42 lines): clean frozen DTO. `PortfolioFitResult` TYPE_CHECKING-guarded.
- `decision_renderer.py` (32 lines): active utility.
- `comparison.py` (186 lines): canonical comparison location (migrated from `atlas.analysis.comparison` Sprint 103). **`render_comparison_result` is dead — zero external callers.** `_render_ranking` and `_ranking_score` are also dead (only called by `render_comparison_result`).
- `memory.py` (238 lines): canonical memory/history location (migrated from `atlas.analysis.memory` Sprint 104). All 7 public symbols active.
- Stale import audit: zero stale production imports. All stale symbol hits are guardrail tests or docstring migration notes.
- Blueprint overlap: `atlas/domains/decision/` has same-named types (`DecisionContext`, `DecisionResult`) but different purpose and shape. No migration warranted.

**Sprint 143 recommended target:** Delete `render_comparison_result`, `_render_ranking`, `_ranking_score` from `atlas/decision/comparison.py` — zero external callers, ~45 dead lines, no CLI surface, no behavior change.

---

## 2026-07-02: Sprint 141 — Close Analysis Cleanup Track

Decision: Formally close the `atlas/analysis/` cleanup track after Sprints 100–141. No further cleanup sprints are planned until `engine.py` has a clear successor architecture.

**Rationale:** After portfolio deletion (Sprints 128–135), placeholder consolidation (Sprint 139), export verification (Sprint 140), and deleted-module guardrails, the remaining analysis package contains only active, intentional modules. All 12 `__init__.py` exports are healthy. All deleted modules are verified gone. Further cleanup would create churn without architectural benefit.

**Final stable package:** `__init__.py`, `company_analysis.py`, `engine.py`, `explanation.py`, `report.py`, `scores.py`. No stale exports. No dead modules.

**Why `engine.py` remains:** 10 external production callers. It is the primary scoring engine for the entire analysis layer. No safe migration path until a Blueprint-aligned successor is designed with a clear caller migration plan.

**Why `scores.py` remains:** 10 external production callers across 6 packages. A 2-line utility; moving it creates churn for zero benefit. It is a permanent shared utility.

**Reopening condition:** Reopen this track when `engine.py` has a clear Blueprint-aligned successor and fewer than 10 active callers remain on the legacy path, or when a new batch of zero-caller modules is identified.

**Sprint 142 recommended target:** Decision package cleanup checkpoint — audit `atlas/decision/` for dead code, stale symbols, or consolidation candidates following the same audit-first pattern used for `atlas/analysis/`.

---

## 2026-07-02: Sprint 140 — Analysis Package Release Candidate Checkpoint

Decision: Audit-only sprint. No runtime behavior changed. `atlas/analysis/` confirmed at 6 modules. Sprint 138 module inventory corrected: `comparison.py` was deleted Sprint 103; `investment.py` never existed; the true remaining modules are `company_analysis.py`, `engine.py`, `explanation.py`, `report.py`, `scores.py`, `__init__.py`.

**Findings:**
- `atlas/analysis/__init__.py`: 12 exports, all active and intentional. No stale exports.
- `company_analysis.py`: clean post-Sprint 139. All 7 placeholder types and factories present. No imports from deleted submodules.
- `engine.py`: 230 lines. 10 external production callers. Foundational — do not migrate.
- `explanation.py`: 199 lines. `InvestmentExplanation`, `explain_investment_report`, `render_investment_explanation`. 1 external production caller (`atlas/decision/memory.py`). Active utility.
- `report.py`: 39 lines. `build_investment_report`, `render_investment_report`. 2 external production callers (`atlas/cli/main.py`, `atlas/comparison/engine.py`). Active utility.
- `scores.py`: 2 lines. `clamp_score`. 10 external production callers across 6 packages. Shared utility — do not move.
- All historically deleted modules confirmed not importable (watchlist, comparison, memory, scoring, portfolio, 7 placeholder submodules).
- All deleted legacy portfolio symbols confirmed absent (PortfolioIntelligenceEngine, PortfolioAnalysis, PortfolioSignal, PortfolioRecommendation, CompanyPortfolioProfile).

**Changes:** 1 new guardrail test file (`tests/test_analysis_package_sprint140.py`, 7 tests). 4 docs updated. No production code changed.

**Sprint 141 recommended target:** Close the analysis cleanup track. The `atlas/analysis/` package is clean and stable. No further consolidation is warranted. Sprint 141 should document the track closure in DecisionLog and update the status line to reflect that the analysis cleanup is complete.

---

## 2026-07-02: Sprint 139 — Consolidate 7 placeholder analysis submodules into company_analysis.py

Decision: Inline `GrowthAnalysis`, `MacroAnalysis`, `MoatAnalysis`, `QualityAnalysis`, `SentimentAnalysis`, `TechnicalAnalysis`, `ValuationAnalysis` (and their `placeholder_*` factories) from 7 separate 18-line files into `atlas/analysis/company_analysis.py`. Delete the 7 source files.

**Zero-caller audit findings:**
- All 7 modules (`growth.py`, `macro.py`, `moat.py`, `quality.py`, `sentiment.py`, `technicals.py`, `valuation.py`) had zero external callers outside `company_analysis.py` itself. All 7 types were already re-exported through `company_analysis.py`; no production file imported from the submodules directly.

**Changes:** 7 placeholder type/factory pairs inlined into `company_analysis.py`; 7 source files deleted; `tests/test_company_analysis.py` imports consolidated + 4 Sprint 139 guardrail tests added; 4 docs updated. `atlas/analysis/` reduced from 13 modules to 6.

**Why this was safe:** Identical structure across all 7 modules (same 4-field frozen dataclass, one factory). Zero external import surface. Consolidation removes indirection without changing any behavior or value.

**Sprint 140 recommended target:** Analysis package release candidate checkpoint — audit remaining 6 modules (`company_analysis.py`, `comparison.py`, `engine.py`, `investment.py`, `scores.py`, `__init__.py`), confirm no stale exports, and assess whether any additional consolidation is warranted before closing out the `atlas/analysis/` cleanup track.

---

## 2026-07-02: Sprint 132 — Delete PortfolioAnalysis, PortfolioSignal, PortfolioRecommendation

Decision: Delete `PortfolioAnalysis`, `PortfolioSignal`, and `PortfolioRecommendation` from `atlas/analysis/portfolio.py`. Confirmed zero active production callers after Sprint 131 migrated the last dependency (`reasoning/engine.py`).

**Zero-caller audit findings:**
- `PortfolioAnalysis`: all hits outside `portfolio.py` were test fixture imports, docstring comments (in `atlas/capabilities/portfolio_intelligence/models.py`), stale string literals (`atlas/cli/deprecations.py`), and re-exports (`atlas/analysis/__init__.py`). Zero production import sites.
- `PortfolioSignal`: all hits were field type annotations within `PortfolioAnalysis` (also deleted) and stale test assertions. Zero production import sites.
- `PortfolioRecommendation`: all hits were `PortfolioAnalysis.recommendation` field type (deleted), docstring comment in models.py, stale string in deprecations.py, and stale re-export in `__init__.py`. Zero production import sites.

**Changes:** `PortfolioSignal`, `PortfolioRecommendation`, `PortfolioAnalysis` classes deleted; unused `from enum import Enum` removed; `PortfolioAnalysis`/`PortfolioRecommendation` removed from `atlas/analysis/__init__.py`; 8 new Sprint 132 guardrail tests added; stale "importable" assertions flipped across 7 test files. `portfolio.py` reduced from 109 to 69 lines.

**Why `Portfolio`, `PortfolioPosition`, `CompanyPortfolioProfile` remain:** `Portfolio` and `PortfolioPosition` are the CLI JSON-loading boundary (5 commands in `cli/main.py`); `CompanyPortfolioProfile` is the provider contract type (`providers/base.py`, `providers/mock.py`, `providers/yahoo.py`) — HIGH risk to migrate atomically.

**Sprint 133 recommended target:** Migrate `CompanyPortfolioProfile` from providers to `PortfolioFitInput`. Requires updating 3 provider files simultaneously.

## 2026-07-02: Sprint 131 — Migrate ReasoningInput.portfolio_analysis to PortfolioFitResult

Decision: Retype `ReasoningInput.portfolio_analysis` in `atlas/reasoning/engine.py` from `PortfolioAnalysis | None` to `PortfolioFitResult | None`. Remove TYPE_CHECKING guard entirely. Update all field accesses.

**Rationale:** `PortfolioAnalysis` had zero production runtime callers after Sprint 118 moved it behind `TYPE_CHECKING`. The field `ReasoningInput.portfolio_analysis` was typed as `PortfolioAnalysis | None` but is never populated in production — intelligence and decision engines pass `PortfolioFitResult` to their own result types. Retyping to `PortfolioFitResult` removes the last production-facing `PortfolioAnalysis` dependency.

**Field mapping applied:**
- `.final_reasoning` → `.summary` (PortfolioFitResult field)
- `.portfolio_score` → `.fit_score` (PortfolioFitResult field)
- `.sector_concentration.reasoning` → `.sector_concentration.note` (PortfolioFitDimension field)

**Changes:** TYPE_CHECKING import block removed; `PortfolioFitResult` added as runtime import; `ReasoningInput.portfolio_analysis` retyped; 6 guardrail tests added; `PORTFOLIO_ENGINE_CALLERS` is now empty (all 5 callers migrated across Sprints 124–131).

**Result:** `PortfolioAnalysis`, `PortfolioSignal`, and `PortfolioRecommendation` are now test-only with zero production callers. Deletion candidates for Sprint 132.

**Sprint 132 recommended target:** Delete `PortfolioAnalysis`, `PortfolioSignal`, `PortfolioRecommendation` from `atlas/analysis/portfolio.py` and `atlas/analysis/__init__.py`. Also update stale `atlas/cli/deprecations.py` string that references `atlas/reasoning/engine.py (PortfolioAnalysis)`.

## 2026-07-02: Sprint 130 — Delete Dead Portfolio Private Helpers

Decision: Delete 16 dead private helper functions and `get_mock_company_portfolio_profile` from `atlas/analysis/portfolio.py`. Confirmed zero active callers repo-wide before deletion.

**Zero-caller audit findings:**
- All 16 helper name hits in `atlas/capabilities/portfolio_intelligence/engine.py` are independently-defined functions in that module — not imports from or calls to the legacy helpers.
- `_weighted_average` hit in `suitability/engine.py` is that file's own local function.
- `get_mock_company_portfolio_profile` had stale imports only (both tests that called it deleted Sprint 128).

**Changes:** 16 private helpers deleted; `get_mock_company_portfolio_profile` deleted; unused `CompanyDataProvider` import removed; stale test imports removed; `__init__.py` export removed. `portfolio.py` reduced from ~350 to 109 lines.

**Sprint 131 recommended target:** Migrate `PortfolioAnalysis` out of `reasoning/engine.py` — retype `ReasoningInput.portfolio_analysis` as `PortfolioFitResult | None`, update duck-typed field accesses. After Sprint 131, `PortfolioAnalysis`, `PortfolioSignal`, `PortfolioRecommendation` become deletion candidates.

## 2026-07-02: Sprint 129 — Remaining Portfolio Legacy Symbol Audit

Decision: Audit all remaining public symbols in `atlas/analysis/portfolio.py`. No deletions this sprint. Sprint 130 target selected.

**Findings:**
- 7 public symbols remain: `Portfolio`, `PortfolioPosition`, `PortfolioSignal`, `PortfolioRecommendation`, `PortfolioAnalysis`, `CompanyPortfolioProfile`, `get_mock_company_portfolio_profile`
- 16 private helpers are dead code (zero callers since `PortfolioIntelligenceEngine` deleted)
- `get_mock_company_portfolio_profile` has zero active callers (stale import only)
- `PortfolioAnalysis` annotation-only in `reasoning/engine.py`; `ReasoningInput.portfolio_analysis` field never populated in production — test-fixture-only usage
- `PortfolioRecommendation` zero production callers; only used as `PortfolioAnalysis.recommendation` field type
- `PortfolioSignal` zero external callers; only used as `PortfolioAnalysis` field types
- `CompanyPortfolioProfile` deeply coupled to 3 provider files — HIGH risk to migrate
- `Portfolio` (legacy) CLI boundary: `Portfolio.from_json_file` in `cli/main.py` (5 commands)

**Sprint 130 target:** Delete 16 dead private helpers + `get_mock_company_portfolio_profile`. Zero behavior change. Reduces `portfolio.py` from ~350 to ~90 lines.

## 2026-07-02: Sprint 128 — Delete PortfolioIntelligenceEngine

Decision: Delete `PortfolioIntelligenceEngine` class from `atlas/analysis/portfolio.py` and remove its re-export from `atlas/analysis/__init__.py`. Zero active production callers confirmed as of Sprint 127.

**Audit finding:** `grep -rn "PortfolioIntelligenceEngine"` across the repo found zero active production callers after Sprints 124–127 migrated all 4 engine call sites (decision, intelligence, conversation, dashboard) to `PortfolioIntelligenceCapability`. Remaining hits were test files and documentation strings only.

**Deletion scope:** Only the `PortfolioIntelligenceEngine` class (lines 85–145 in the pre-deletion file). All shared types — `Portfolio`, `PortfolioPosition`, `PortfolioAnalysis`, `PortfolioSignal`, `PortfolioRecommendation`, `CompanyPortfolioProfile`, `get_mock_company_portfolio_profile` — remain intact. Private helper functions (`_diversification_impact`, `_sector_concentration`, etc.) become dead code but are left in place for this sprint.

**Test cleanup:** Deleted `test_portfolio_engine_analyzes_target_in_portfolio_context` and `test_portfolio_engine_penalizes_existing_holding_overlap` (test_portfolio.py), deleted `test_portfolio_engine_can_analyze_ticker_from_provider` (test_providers.py). Rewrote `test_sprint118_reasoning_portfolio_analysis_field_still_accepted` to construct `PortfolioAnalysis` directly. Updated 8 stale "engine importable" assertions across sprint-guardrail tests to either remove the check or flip to assert NOT importable.

**Guardrails added:** 3 new tests in `test_portfolio_analyze_deprecation.py` (Sprint 128 block) confirm: `PortfolioIntelligenceEngine` raises `ImportError` from `atlas.analysis.portfolio`, is absent from `atlas.analysis` namespace, and shared types remain importable.

**Remaining `atlas.analysis.portfolio` runtime coupling:** `cli/main.py` (Portfolio loading), `adapters/portfolio.py` (LegacyPortfolio adapter), `providers/` (CompanyPortfolioProfile), `portfolio_review/engine.py` (structural analysis), `reasoning/engine.py` (PortfolioAnalysis duck-typing). These are out of scope for Sprint 128.

## 2026-07-02: Sprint 127 — Dashboard Engine: Remove Stale portfolio_engine Attribute; PortfolioIntelligenceEngine Zero-Caller Milestone

Decision: Remove the dead `self.portfolio_engine` / `portfolio_engine` constructor parameter
from `atlas/dashboard/engine.py`. Option A + B (dead-code removal + Portfolio to TYPE_CHECKING).

**Audit finding:** `self.portfolio_engine = portfolio_engine or PortfolioIntelligenceEngine()`
was assigned at construction but never read anywhere in the file. `_portfolio_section`
target-fit block was fully migrated to `self.portfolio_fit_capability` in Sprint 115.
After that migration, the legacy attribute had zero active call sites.

**`PortfolioIntelligenceEngine` zero-caller milestone reached:** After Sprint 127, no production
engine in the Atlas codebase imports or instantiates `PortfolioIntelligenceEngine`. It remains
in `atlas/analysis/portfolio.py` and is re-exported by `atlas/analysis/__init__.py`, but has
no active callers. Sprint 128 is the designated deletion sprint.

**Remaining `atlas.analysis.portfolio` active imports:** `cli/main.py` (Portfolio loading),
`adapters/portfolio.py` (LegacyPortfolio adapter), `providers/` (CompanyPortfolioProfile),
`portfolio_review/engine.py` (structural analysis). These are out of scope for Sprint 127.

## 2026-07-02: Sprint 126 — Conversation Engine: Remove Stale portfolio_engine Attribute

Decision: Remove the dead `self.portfolio_engine` / `portfolio_engine` constructor parameter
from `atlas/conversation/engine.py`. This is Option A (pure dead-code removal).

**Audit finding:** `self.portfolio_engine = portfolio_engine or PortfolioIntelligenceEngine()`
was assigned at construction but never read anywhere in the file. `_answer_portfolio_review`
was fully migrated to `self.portfolio_fit_capability` in Sprint 114. After Sprint 125 updated
the `IntelligenceEngine(...)` call to use `portfolio_fit_capability=`, no code in the engine
accessed `self.portfolio_engine`. It was a zombie attribute.

**Changes:** `PortfolioIntelligenceEngine` import removed; `portfolio_engine` constructor
parameter removed; `self.portfolio_engine` assignment removed; `Portfolio` moved to
TYPE_CHECKING (annotation-only on `ConversationInput.portfolio`); `from __future__ import
annotations` added.

**No behavior change** — the removed attribute had no active call sites.

**Remaining `PortfolioIntelligenceEngine` runtime caller:** `atlas/dashboard/engine.py` only.

## 2026-07-02: Sprint 125 — Intelligence Engine: PortfolioIntelligenceEngine → PortfolioIntelligenceCapability

Decision: Migrate `atlas/intelligence/engine.py` from legacy `PortfolioIntelligenceEngine`
to Blueprint-aligned `PortfolioIntelligenceCapability`. Option D (tiny runtime migration)
chosen — same pattern as Sprint 124, all field mappings are 1:1.

**Adapter chain:** same pattern as decision engine — `provider.get_portfolio_profile(ticker)`
→ `portfolio_fit_input_from_profile(profile)` → `legacy_portfolio_to_domain_portfolio(portfolio)`
→ `capability.analyze(domain_portfolio, fit_input)`.

**Field mappings:** `portfolio_score` → `fit_score`; `.reasoning` → `.note` on all 7 dimensions;
`overlap_with_existing_holdings` → `overlap`; `diversification_impact` → `diversification`;
`expected_portfolio_quality_impact` → `quality_impact`; `expected_portfolio_risk_impact` → `risk_impact`.

**`IntelligenceReport.portfolio_analysis`:** field name kept for caller compatibility; type
annotation updated to `PortfolioFitResult`.

**`conversation/engine.py` side-effect fix:** the `IntelligenceEngine(portfolio_engine=...)` kwarg
was stale after `IntelligenceEngine` dropped that parameter. Updated to pass
`portfolio_fit_capability=self.portfolio_fit_capability` instead. `conversation/engine.py`
retains its own `self.portfolio_engine` (legacy) for its own `_answer_portfolio_review` path.

**No behavior change** for the no-portfolio path. Portfolio impact text wording changes slightly
(`.note` framing vs `.reasoning` framing) — this is the intended Blueprint-layer framing,
consistent with all prior migrations.

## 2026-07-02: Sprint 124 — Decision Engine: PortfolioIntelligenceEngine → PortfolioIntelligenceCapability

Decision: Migrate `atlas/decision/decision_engine.py` from legacy `PortfolioIntelligenceEngine`
to Blueprint-aligned `PortfolioIntelligenceCapability`. Use `fit_score < 55` as the unified
poor-fit boundary, replacing both legacy guards.

**Recommendation guard replacement:** The legacy code used two sequential guards:
1. `if portfolio_analysis.recommendation.value in {"Avoid", "Reduce"}` (fires when `portfolio_score < 50`)
2. `if portfolio_analysis.portfolio_score < 55: return WATCH`

`PortfolioFitResult` intentionally omits the recommendation enum. Both guards are consolidated
into a single `if portfolio_fit_result.fit_score < 55` check, returning WATCH (atlas_score ≥ 75)
or AVOID (atlas_score < 75).

**Documented behavior change:** Scores in [50, 54] previously returned WATCH only (old guard 1
did not fire for NEUTRAL recommendation; old guard 2 fired unconditionally returning WATCH).
New code returns WATCH or AVOID based on `atlas_score`. This is a slightly stronger response
for well-scored tickers with poor portfolio fit. Scores ≥ 55 are unaffected.

**Field mappings:** `portfolio_score` → `fit_score`, `final_reasoning` → `summary`,
`overlap_with_existing_holdings` → `overlap`. Dimension `.score` and `.note` unchanged.

**Constructor:** `portfolio_engine: PortfolioIntelligenceEngine` → `portfolio_fit_capability:
PortfolioIntelligenceCapability`. `atlas/intelligence/engine.py` updated to drop stale
`portfolio_engine=` kwarg from its `AtlasDecisionEngine(...)` call (retains its own
`self.portfolio_engine` for `_optional_portfolio_analysis`).

**`decision_result.py`:** `portfolio_analysis` field annotation updated from `PortfolioAnalysis`
to `PortfolioFitResult`; field name kept for external caller compatibility.

## 2026-07-02: Sprint 123 — Decision Layer Portfolio Audit: Partial TYPE_CHECKING Cleanup

Decision: `decision_context.py` and `decision_result.py` annotation-only imports moved behind
TYPE_CHECKING. `decision_engine.py` runtime coupling retained unchanged.

`decision_context.py`: `Portfolio` is used only as a type annotation on `DecisionContext.portfolio`.
No runtime field access anywhere in the file. Moved behind TYPE_CHECKING.

`decision_result.py`: `PortfolioAnalysis` is used only as a type annotation on
`DecisionResult.portfolio_analysis`. No runtime field access. Moved behind TYPE_CHECKING.

`decision_engine.py`: `PortfolioIntelligenceEngine` is instantiated at line 24 and called via
`analyze_ticker()` at line 116. `PortfolioAnalysis` is accessed for `.portfolio_score`,
`.final_reasoning`, `.recommendation.value`, `.sector_concentration.score`,
`.country_concentration.score`, `.market_cap_concentration.score`,
`.overlap_with_existing_holdings.score`. Not safe to touch without full behavioral parity.

Blocker for Sprint 124: `portfolio_analysis.recommendation.value` is used to gate action
selection (`if portfolio_analysis.recommendation.value in {"Avoid", "Reduce"}`). `PortfolioFitResult`
intentionally omits the recommendation enum (no advisory semantics in Blueprint layer). Sprint 124
must decide: drop the guard, introduce a compatibility score threshold, or retain the enum.

## 2026-07-02: Sprint 122 — Home Portfolio Dependency: TYPE_CHECKING Only (Option D)

Decision: `atlas/home/engine.py` imports `Portfolio` only for the `AtlasHomeInput.portfolio`
field annotation. No runtime field access occurs inside the engine — the value is only
None-checked and passed through to `PortfolioReviewInput`. Migration is TYPE_CHECKING guard
(Option D): `from __future__ import annotations` + `if TYPE_CHECKING: from atlas.analysis.portfolio import Portfolio`.

Rationale: Purest possible annotation-only case. No duck-typed field access, no logic change,
no caller impact. Zero risk. Same pattern as Sprints 118, 119 (partial), 121.

## 2026-07-02: Sprint 121 — Monitoring Portfolio Dependency: TYPE_CHECKING Only (Option D)

Decision: `atlas/monitoring/engine.py` imports `Portfolio` for method type annotations only.
No `PortfolioAnalysis` or `PortfolioIntelligenceEngine` imports present. Migration strategy
is TYPE_CHECKING guard (Option D): `from __future__ import annotations` + `if TYPE_CHECKING:
from atlas.analysis.portfolio import Portfolio`. All runtime attribute access (`.positions`,
`.ticker`, `.weight`, `.sector`, `.country`, `.quality_score`, `.risk_score`) is duck-typed
and requires no import. All callers (cli, dashboard, portfolio_review) continue passing
legacy Portfolio objects unchanged.

Rationale: Option A (shared Portfolio migration) would require migrating all three callers
simultaneously — `cli/main.py`, `dashboard/engine.py`, and `portfolio_review/engine.py` — which
is out of scope for Sprint 121. Option D achieves the boundary goal (no runtime import from
legacy module) with zero behavior change and zero caller breakage.

## 2026-06-29: Keep Sprint 36 as a Foundation Sprint

Decision: establish boundaries, canonical entities, docs, CI, hooks, and AI
interfaces without rewriting existing engines.

Rationale: Atlas already has working deterministic engines. A large migration
would add risk without improving the investor experience.

## 2026-06-29: Use Python Backend as the Source of Truth

Decision: keep existing backend code under `atlas/` and document `backend/` as
the backend boundary.

Rationale: this preserves all existing APIs and test coverage while making the
repository easier to navigate.

## 2026-06-29: Add Strict TypeScript Configuration Before Frontend Code

Decision: add `frontend/tsconfig.json` and `frontend/package.json` with strict
type checking, but no frontend runtime.

Rationale: future UI work should start from strong defaults without forcing an
application framework too early.

## 2026-06-29: Define AI as Interfaces First

Decision: create `atlas.ai` protocols for reasoning, knowledge, summary,
discovery, and decision support services.

Rationale: Atlas should remain deterministic and explainable until concrete AI
services can be evaluated against the Constitution.

## 2026-06-29: Build Portfolio as the First Real Domain

Decision: implement deterministic portfolio calculations, validation, and
structured observations inside `atlas.domains.portfolio`.

Rationale: portfolio understanding is foundational to Atlas. A portfolio is not
just a list of positions; it is a collection of investment decisions. The domain
therefore starts with value, allocation, concentration, and data quality before
any user-facing action language.

## 2026-06-29: Separate Decision Reasoning From Recommendations

Decision: add `atlas.domains.decision` as a non-advisory reasoning foundation
instead of modifying the older action-oriented `atlas.decision` package.

Rationale: Sprint 38 is about evidence, observations, unknowns, confidence, and
explainability. Keeping the new domain separate preserves existing behavior and
gives future AI services a deterministic reasoning contract.

## 2026-06-30: Model Knowledge as Attributed Facts

Decision: implement `atlas.domains.knowledge` as immutable nodes, edges,
facts, sources, references, and deterministic queries.

Rationale: Atlas knowledge should be structured evidence, not generated
opinion. The domain should remain independent of AI providers, vector databases,
and graph storage so future Portfolio, Research, Decision Engine, and AI layers
can share the same factual foundation.

## 2026-06-30: Model Research as Structured Understanding

Decision: implement `atlas.domains.research` as research projects, notes,
questions, assumptions, evidence references, thesis fragments, summaries, and
validation.

Rationale: research should connect curiosity, evidence, assumptions, and open
questions before Atlas reaches conclusions. Keeping Research independent of AI,
UI, persistence, providers, and recommendations preserves the Blueprint
principle that understanding comes before judgment.

## 2026-06-30: Build Company Analysis as a Capability

Decision: implement `atlas.capabilities.company_analysis` as a consumer of
Company, Knowledge, Research, and Decision structures rather than as a new
domain owner.

Rationale: Company Analysis should organize existing structured evidence into
explainable business understanding. Keeping it in `atlas.capabilities` prevents
it from owning Knowledge, Research, or Decision responsibilities and preserves
the Blueprint principle that Atlas helps investors understand businesses before
forming conviction.

## 2026-06-30: Build Watchlist Intelligence as Structured Observation

Decision: implement `atlas.capabilities.watchlist_intelligence` as a consumer of
Research, Knowledge, and Company Analysis structures rather than as a domain
owner.

Rationale: a watchlist should help investors track unanswered questions without
creating noise or trading behavior. Keeping Watchlist Intelligence in
`atlas.capabilities` preserves clean domain ownership and reinforces the
Blueprint principle that Atlas supports understanding before action.

## 2026-06-30: Build Discovery as Structured Curiosity

Decision: implement `atlas.capabilities.discovery` as a deterministic consumer
of Knowledge, Research, Company Analysis, and Watchlist Intelligence structures.

Rationale: Discovery should help investors decide what deserves further study,
not what action to take. Keeping it in `atlas.capabilities` preserves domain
ownership boundaries and aligns with the Blueprint principle that discovery is
the disciplined pursuit of understanding before conviction.

## 2026-06-30: Introduce `atlas.adapters` as the Legacy-to-Domain Bridge

Decision: add `atlas.adapters.portfolio.legacy_portfolio_to_domain_portfolio`
and a new, additive `atlas portfolio summary` CLI command that calls
`atlas.domains.portfolio` directly, instead of rewriting the existing
`atlas portfolio analyze`/`atlas portfolio review` commands.

Rationale: the legacy CLI portfolio file format
(`atlas.analysis.portfolio.Portfolio`, positions with a relative `weight`
and no absolute market value) answers a different question (ticker-fit
analysis, CIO review with provider/profile/market dependencies) than the
Portfolio Domain (portfolio understanding: allocation, concentration,
validation). Forcing the existing commands onto the domain would have been
a disguised behavior change, not a safe migration. Adding `atlas.adapters`
as the one layer permitted to import both legacy and domain code lets the
CLI begin exercising `atlas.domains.portfolio` today, on a read-only path,
without touching the two existing commands or their output. Architecture
boundary tests were updated so domains may never import adapters back,
keeping the dependency direction one-way (legacy/CLI -> adapters -> domains).

## 2026-06-30: Augment, Don't Replace, `atlas portfolio analyze`

Decision: extend `atlas portfolio analyze` to additionally print a Portfolio
Domain summary (allocation, concentration, cash weight, top holdings) using
the Sprint 45 adapter, while leaving `PortfolioIntelligenceEngine`'s
proprietary ticker-fit scoring (diversification impact, sector/country/
market-cap concentration impact, overlap, expected quality/risk impact, and
the `Strong Add`/`Add`/`Neutral`/`Reduce`/`Avoid` recommendation) completely
unchanged.

## 2026-07-01: Add Capability JSON Export Commands (Sprint 51)

Decision: add `atlas watchlist intelligence [--output FILE]` and
`atlas discovery export [--output FILE]` as the first capability export
commands, backed by new `exporter.py` modules in each capability package that
serialize the capability's native report type to a JSON dict matching the
Sprint 50 Daily Brief input format.

Rationale: Sprint 50 added Daily Brief `--watchlist` and `--discovery` CLI
flags that accept local JSON files, but users had to author those files manually.
Sprint 51 closes this gap by adding export commands that produce JSON in exactly
the format the loaders expect, enabling a fully deterministic local workflow
with no manual JSON authoring required. The exporters are pure functions with no
side effects; the CLI commands produce human-readable output by default and write
JSON only when `--output` is supplied, preserving the useful plain-text output
path. Both commands run on empty inputs (no watchlist items, no discovery inputs)
which produces valid structural JSON that Daily Brief can consume — wiring real
structured inputs to the export commands is deferred to Sprint 52.

## 2026-07-01: Extend Daily Brief CLI with Local JSON Input Flags (Sprint 50)

Decision: add `--research`, `--watchlist`, `--discovery`, and `--company-analysis`
flags to `atlas daily summary`, backed by a new `json_loader.py` module that
parses local JSON files into lightweight structured types the Daily Brief engine
can consume, and route those parsed objects through the Sprint 49 `build_daily_brief_input`
builder before calling `DailyBriefCapability.generate()`.

Rationale: the Sprint 49 capability integration proved all five input types work
correctly at the library level. Sprint 50 closes the gap between capability-level
integration and runtime usability without requiring a full JSON serialisation
round-trip for existing Atlas capability outputs. Each flag reads a local file
only, validates the JSON shape enough to fail cleanly on bad input, and makes no
network calls. The `json_loader.py` module uses minimal dataclasses (not the full
typed Atlas models) because the engine already uses duck-typed `getattr` access —
this keeps the loader self-contained, easy to test, and easy to extend. The
`--portfolio` flag was already present from Sprint 48; the four new flags follow
the same additive pattern.

## 2026-07-01: Connect Daily Brief to Typed Atlas Structures (Sprint 49)

Decision: create `atlas.capabilities.daily_brief.input_builder.build_daily_brief_input`
as the canonical adapter from typed Atlas structures to `DailyBriefInput`, and fix
five attribute-name mismatches in the engine that prevented correct output when real
typed objects were supplied.

Rationale: Sprint 48's engine used duck typing (`getattr` with fallback) to consume
inputs, but several attribute names were wrong for the real Atlas types — `ticker`
instead of `title` for `ResearchNote`, `suggested_next_steps` instead of
`suggested_next_research_steps` for `WatchlistIntelligenceReport`, `reason` instead
of `reasons[0].detail` for `DiscoveryCandidate`, `ticker` instead of `company.ticker`
and `evidence_gaps` instead of `evidence_links` for `CompanyAnalysisReport`. The
mismatches were silent (the fallback values suppressed them) but would have produced
wrong output in production. The input builder adds a typed, keyword-only interface
that documents what Atlas structures are accepted, extracts `ResearchProject` open
questions automatically, and is easy to test. No new data sources were introduced;
all inputs come from existing Atlas domains and capabilities.

## 2026-07-01: Add Daily Brief as a Blueprint-Aligned Capability

Decision: create `atlas.capabilities.daily_brief` as a new capability
alongside `company_analysis`, `watchlist_intelligence`, and `discovery`,
and wire it to a new `atlas daily summary` CLI command, while leaving the
legacy `atlas.daily_brief` engine and `atlas daily brief` command
completely unchanged.

Rationale: a legacy Daily Brief engine (`atlas.daily_brief`) already
exists and is fully tested (8 tests, 6 sections, CIO-style multi-engine
output). Rather than rewriting it, Sprint 48 adds a parallel
Blueprint-aligned capability that accepts domain-native inputs
(`PortfolioSummary` from the Sprint 45 adapter, `ResearchNote`,
`KnowledgeCollection`, `CompanyAnalysisReport`, `WatchlistIntelligenceReport`,
`DiscoveryReport`) and produces a deterministic, calm, provider-free
`DailyBriefReport`. This preserves the existing CLI command's behavior
exactly, gives the Blueprint architecture its first Daily Brief path, and
sets up future sprints to extend `atlas daily summary` with additional
input flags as more domain-native JSON inputs become CLI-accessible.

## 2026-06-30: Augment, Don't Replace, `atlas portfolio review`

Decision: apply the same additive pattern from Sprint 46 to
`atlas portfolio review`: append a Portfolio Domain summary section to the
existing CIO-style review output rather than rewriting or replacing any
part of `PortfolioReviewEngine`.

Rationale: the legacy review engine combines investor profile, suitability,
risk drift, themes, market context, economics, monitoring, and principles
checks — none of which have a Portfolio Domain equivalent today. Replacing
any part of this logic would require new domain models (investor profile,
market regime, economics signals) that are out of scope. The
`PortfolioReviewEngine` depends on `atlas.analysis.portfolio.Portfolio`
(the legacy type), not `atlas.shared.Portfolio`, so it cannot be swapped
for domain-native calls without a larger migration. The additive pattern is
safe, reversible, and brings all three `portfolio` CLI commands
(`summary`, `analyze`, `review`) to a state where they exercise
`atlas.domains.portfolio` for the calculations it genuinely owns:
allocation, concentration, cash weight, and top holdings. The Sprint 45
adapter needed no changes for Sprints 46 or 47.

## 2026-06-30: Augment, Don't Replace, `atlas portfolio analyze`

Decision: extend `atlas portfolio analyze` to additionally print a Portfolio
Domain summary (allocation, concentration, cash weight, top holdings) using
the Sprint 45 adapter, while leaving `PortfolioIntelligenceEngine`'s
proprietary ticker-fit scoring completely unchanged.

Rationale: `atlas portfolio analyze` answers "how well would this new
ticker fit the existing portfolio" — a hypothetical-addition scoring
question with no Portfolio Domain equivalent. The Portfolio Domain
deliberately only answers "what does this portfolio currently look like."
Rewriting the fit-scoring math to route through the domain would require
either inventing domain concepts that don't belong there (target-weight
scoring, pro-forma exposure) or producing different numbers under a
different methodology, which would be a hidden behavior change disguised as
a migration. Appending the existing domain summary section is additive,
preserves every existing output byte exactly, and still proves the CLI
analyze path can pull from `atlas.domains.portfolio` for the parts that
genuinely overlap (allocation, concentration). The Sprint 45 adapter needed
no changes.

## 2026-07-01: Wire Real JSON Inputs to Capability Export Commands (Sprint 52)

Decision: add three adapter modules (`atlas/adapters/watchlist.py`,
`atlas/adapters/knowledge.py`, `atlas/adapters/research_input.py`) and extend
`atlas watchlist intelligence` with `--input` and `atlas discovery export` with
`--knowledge`, `--research`, `--watchlist` so both commands produce meaningful
structured output from local JSON files.

Rationale: Sprint 51's export commands ran on empty inputs, producing valid but
empty reports — no candidates, no open questions, no suggestions. This made the
end-to-end pipeline (`watchlist intelligence → discovery export → daily summary`)
structurally correct but semantically inert. Sprint 52 closes the gap by parsing
real watchlist items, knowledge facts, and research projects from local files and
routing them through the same deterministic engines. The adapter modules are placed
in `atlas/adapters/` (the only layer permitted to bridge legacy shapes and domain
types), remain side-effect-free, and raise ValueError with clear messages on
invalid input. `open_questions` in watchlist items are converted to
`ResearchProject` entries with `OPEN` `ResearchQuestion` objects so the
`WatchlistIntelligenceEngine` surfaces them as unresolved questions in its report —
consistent with how other Atlas inputs represent open questions. No existing CLI
command behavior was changed; all new flags are additive and optional.

## 2026-07-01: Add Research Export Command to Complete Daily Brief Pipeline (Sprint 53)

Decision: add `atlas/capabilities/daily_brief/research_exporter.py` with
`research_projects_to_dict()` and an `atlas research export [--input FILE]
[--output FILE]` CLI command that converts the adapter-format research projects
JSON (`{"projects": [...]}`) to the Daily Brief–compatible research JSON
(`{"notes": [...], "open_questions": [...]}`).

Rationale: Research notes and open questions were the only Daily Brief input
type that still required users to author JSON manually. Every other input type
(portfolio, watchlist, discovery, knowledge) already had a CLI export command
producing a file consumable by `atlas daily summary`. This sprint closes that
gap with a pure conversion step: `research_projects_from_dict` parses the input,
`research_projects_to_dict` serialises it to the daily brief format.
The exporter is placed in `atlas/capabilities/daily_brief/` (alongside the
other daily brief modules) because its output format is defined entirely by what
`parse_research_json` / the Daily Brief engine expect — it is a daily brief
concern, not a general research concern. No new domain models or capability
engines were introduced; this is a serialisation adapter only.

## 2026-07-01: Add Company Analysis Export Command to Complete Daily Brief Pipeline (Sprint 54)

Decision: add `atlas/capabilities/company_analysis/exporter.py` with
`company_report_to_dict` / `company_reports_to_list`, `atlas/adapters/company_analysis.py`
with `company_reports_from_dict`, and an `atlas company-analysis export [--input FILE]
[--output FILE]` CLI command under a new `company-analysis` subapp.

Rationale: Company analysis was the last Daily Brief input type that required users
to author JSON manually. The adapter accepts the same output format that the exporter
produces (self-consistent round-trip), so users can author company analysis JSON in
the export format, pass it to `atlas company-analysis export`, and consume the output
with `atlas daily summary --company-analysis`. When no input is provided the command
exports `[]` — an empty list that `parse_company_analysis_json` accepts and that
`build_daily_brief_input` treats as an empty tuple of company reports. `confidence`
accepts either a plain string (`"low"`) or a structured object with `level`,
`explanation`, `drivers`, and `limitations` fields, covering both quick authoring
and detailed structured input. The adapter reuses the existing `CompanyAnalysisReport`
model without invoking `CompanyAnalysisEngine` — the report is built directly from
user-supplied JSON fields without running deterministic risk / confidence scoring on
knowledge facts, since users may not have knowledge facts available at export time.

## 2026-07-01: Wire CompanyAnalysisEngine to Export Command (Sprint 55)

Decision: extend `atlas company-analysis export` with `--ticker`, `--knowledge`,
and `--research` flags that wire `CompanyAnalysisEngine.analyze()` to the
existing Sprint 54 export path, using the Sprint 52 adapters
(`knowledge_facts_from_dict`, `research_projects_from_dict`) for local input
parsing.

Rationale: Sprint 54's export command required users to author the full
company analysis JSON structure by hand. Sprint 55 closes this gap by letting
the engine derive observations, risks, evidence links, confidence, and
what-could-change content from local knowledge facts and research projects.
The `--ticker` flag is the minimum required input for the engine-backed path
because `CompanyAnalysisInput` requires a `Company` object with a ticker. When
`--research` is supplied, the first project matching the ticker topic is selected
as `research_project`; if none matches, the first project is used — this avoids
a hard failure for single-project research files where the topic may not exactly
match the ticker. The Sprint 54 `--input` path is preserved unchanged as a
separate branch in the same command, giving users two authoring options:
engine-backed (from structured local files) and manual (from a pre-authored
report JSON). No new adapter or exporter files were needed — only main.py was
modified, adding 40 lines to the existing command function.

## 2026-07-01: Add --company-name and --business-description to Company Analysis Export (Sprint 56)

Decision: add two optional string flags — `--company-name` and
`--business-description` — to `atlas company-analysis export`. Both populate
`CompanyAnalysisInput` fields used by `CompanyAnalysisEngine` without requiring
any network calls or new adapters.

Rationale: Sprint 55 always defaulted `Company.name` to the ticker string (e.g.
"AMD" instead of "AMD Corporation") and always left `business_description` empty,
causing a "Missing Business Description" unknown to appear in every engine report.
Both fields accept user-supplied local strings, require no external lookup, and
follow the existing pattern of optional CLI flags for local metadata. When
`--business-description` is supplied, `CompanyAnalysisEngine._unknowns()` no
longer appends the "Missing Business Description" unknown because
`business_description.strip()` is truthy. When `--company-name` is supplied,
`Company.name` is set to the user value; when omitted it falls back to the ticker
string. Both flags are entirely optional — omitting them preserves Sprint 55
behavior exactly.

## 2026-07-01: Add Company Analysis Merge Command (Sprint 60)

Decision: add `atlas company-analysis merge --inputs a.json --inputs b.json
--output combined.json` as a new subcommand under the existing
`company-analysis` subapp.

Rationale: Sprint 59's demo workflow used an inline `python3 -c` call to
concatenate two JSON lists. This was the only non-Atlas step in the pipeline.
The merge command removes that dependency, making the full multi-company demo
expressible in Atlas CLI commands only. The command operates at the raw JSON
dict level (load → validate via `parse_company_analysis_json` → concatenate
→ write) rather than deserialising into typed `CompanyAnalysisReport` objects,
because the inputs are already in the export format. `--inputs` accepts
repeated flags, so an arbitrary number of files can be merged. Input order is
preserved. The command validates each file before merging and fails cleanly on
missing files, invalid JSON, or non-object/non-list top-level values. No CLI
redesign to `atlas daily summary` was needed — `parse_company_analysis_json`
already accepts a JSON array of any length. 754 tests pass; 15 new tests in
`test_company_analysis_merge.py` cover command existence, two-file merge, order
preservation, single-file merge, Daily Brief compatibility, error handling,
no-network, and demo script correctness.

## 2026-07-01: Extend Demo to Two-Company Daily Brief (Sprint 59)

Decision: extend the Sprint 58 demo dataset from AMD-only to AMD + NVDA.
Updated `knowledge.json` (9 total facts), `research_input.json` (2 projects, 7
questions), and `watchlist_input.json` (2 items). Updated
`run_daily_brief_demo.sh` to generate separate company analysis exports for AMD
and NVDA, merge them via a Python one-liner into a single JSON array, and pass
the combined file to `atlas daily summary --company-analysis`. The Daily Brief
engine already accepts a JSON array of reports via `parse_company_analysis_json`,
so no CLI redesign was required. The merge step exposes a minor CLI limitation:
`--company-analysis` accepts one file, not multiple. This is documented as a
known limitation; Sprint 60 should address it. 739 tests pass; 34 tests in
`test_daily_brief_demo.py` (11 new vs Sprint 58) cover two-company data
validity, both company exports, merged array compatibility, two-company pipeline,
section presence, AMD/NVDA presence, two-report count, language safety,
determinism, and no-network constraints.

## 2026-07-01: Add Local Demo Dataset and End-to-End Daily Brief Demo (Sprint 58)

Decision: add a local example dataset under `examples/daily_brief_demo/` and a
demo script `scripts/run_daily_brief_demo.sh` that runs the complete Atlas Daily
Brief pipeline from structured local inputs.

Rationale: the pipeline (research export → watchlist intelligence → discovery
export → company analysis export → daily summary) was functional but had no
runnable example showing that all five stages connect end-to-end. A minimal demo
dataset (5 knowledge facts, 1 research project, 1 watchlist item — all AMD)
proves the pipeline works locally and gives developers and users a concrete
starting point. No new CLI commands, no new adapters, and no new domains were
needed — only fixture JSON files, a shell script, documentation, and tests. The
demo is explicitly marked as research context, not live market analysis. No
network calls are made at any step.

## 2026-07-01: Remove Daily Shim and Enforce Domain Boundaries (Sprint 75)

Decision: remove `atlas/daily/` (43-line re-export shim), fix the
`atlas/domains/daily_brief/` boundary violation, and extend the domain
boundary test with an explicit legacy-prefix prohibition list.

Changes:
- `atlas/daily/` deleted (2 files, 43 lines — pure re-export, zero logic)
- `atlas/cli/main.py` line 39: `from atlas.daily` → `from atlas.daily_brief`
- `tests/test_daily_brief.py`: import updated from `atlas.daily_brief` directly;
  `LegacyDailyBriefEngine` retained as a local alias for test readability
- `atlas/domains/daily_brief/__init__.py`: rewritten as a namespace stub with
  no imports from legacy modules or capability modules. `DailyBriefOutput`
  re-export (legacy artifact) removed.
- `tests/test_atlas_foundation.py`: stale `DailyBriefOutput` assertion replaced
  with `hasattr(daily_brief, "__all__")` check
- `tests/test_architecture_boundaries.py`: boundary test extended with legacy
  module prefixes; 2 new Sprint 75 tests added (`test_atlas_daily_shim_is_removed`,
  `test_domains_daily_brief_does_not_import_legacy`)
- `docs/LegacyConsolidationPlan.md` and `docs/ArchitectureConsolidation.md`
  updated to mark Sprint 75 as complete

Runtime behavior: unchanged. `atlas daily brief` still works (calls
`atlas.daily_brief` directly). `atlas daily summary` unchanged.
991 tests pass. Demo green. RC verification green.

## 2026-07-01: Legacy Engine Consolidation Plan (Sprint 74)

Decision: create `docs/LegacyConsolidationPlan.md` inventorying all legacy
Atlas modules, mapping their runtime CLI usage, documenting Blueprint-aligned
overlap, confirming provider safety, and selecting a Sprint 75 migration target.

No runtime code was changed. This is a planning-only sprint.

Key findings:
- `atlas/daily/` is a 43-line pure re-export shim. Only `atlas/cli/main.py`
  imports it. Selected as the Sprint 75 removal target (lowest-risk migration).
- `atlas/domains/daily_brief/__init__.py` imports from `atlas.daily_brief`
  (legacy) — a boundary violation. No external code uses this path; resolution
  is scheduled for Sprint 75 alongside shim removal.
- Provider safety confirmed: `atlas/providers/` is never imported by domains,
  capabilities, adapters, demo script, or release verification script.
- 4 legacy module groups identified: thin shims (A), provider-dependent (B),
  self-contained analytics (C), infrastructure/support (D).

Documentation updated:
- `docs/LegacyConsolidationPlan.md` created (new)
- `docs/ArchitectureConsolidation.md` — Sprint 74 section added, boundary
  violation documented
- `README.md` Documentation table — LegacyConsolidationPlan.md link added

## 2026-07-01: README Sprint Notes Archive (Sprint 73)

Decision: move historical sprint notes (Sprints 37–72) from `README.md` into
`docs/SprintHistory.md`. README.md is now a concise 125-line developer guide.

Rationale: `README.md` had grown to 1691 lines — over 93% of which were sprint
notes accumulated during development. The notes are valuable historical context
but not useful to a developer reading the README for the first time. Moving them
to a dedicated document preserves history while making the developer guide
immediately readable.

Changes:
- `README.md` trimmed from 1691 lines to 125 lines
- `docs/SprintHistory.md` created with header + all moved sprint notes
- README Documentation table updated: added `SprintHistory.md` row; fixed
  stale "RC1 release notes" label to "RC1 and RC2 release notes"
- `docs/DecisionLog.md` Sprint 73 entry added

No runtime behavior changed. No code changes. No new capabilities.

## 2026-07-01: Discovery Context Display Name Resolution (Sprint 72)

Decision: add `_resolve_node_display_name` in `atlas/capabilities/daily_brief/engine.py`
and use it in `_discovery_section` instead of `candidate.identifier`.

Rationale: the Discovery Context previously displayed raw knowledge node IDs
(`company-amd`, `company-nvda`) which are internal technical identifiers. The
discovery engine already computed human-readable `title` fields via
`_title_from_identifier` (`company-amd` → `AMD`), but the Daily Brief renderer
ignored them. This sprint wires the two together without changing any model or
export format.

Resolution order (deterministic, explicit, no fuzzy/AI):
1. `candidate.title` if non-empty
2. `candidate.ticker` if non-empty
3. `company-{x}` → `X.upper()` (single-segment suffix only)
4. original identifier as safe fallback

One pre-existing test (`test_discovery_candidate_identifier_used_as_item_title`)
asserted the old buggy behavior and was renamed and corrected. 17 new tests
added in `tests/test_discovery_display_names.py`.

Demo output change: Discovery Context now shows `AMD` and `NVDA` instead of
`company-amd` and `company-nvda`.

## 2026-07-01: RC2 Release Verification (Sprint 71)

Decision: declare Atlas Internal Release Candidate 2 (v0.1.0-rc2), extending
the RC1 documentation in `docs/ReleaseCandidate.md` with a new RC2 section.
No new product capability was added.

Verification results:
- 947 tests pass (0 failures)
- `scripts/verify_release_candidate.sh` — all 7 steps green
- `scripts/run_daily_brief_demo.sh` — all 7 steps complete
- All five Daily Brief input surfaces exercised in demo
- No false "No knowledge facts are linked" in output
- No forbidden language in output
- No network calls

Documentation updated:
- `docs/ReleaseCandidate.md` — RC2 section prepended; RC1 preserved below
- `README.md` — version updated to RC2; test count updated to 947; capabilities table updated
- `scripts/verify_release_candidate.sh` — final echo updated from "RC1" to "RC2"
- `docs/ArchitectureConsolidation.md` — noted RC2 review; no structural changes
- `docs/DecisionLog.md` — Sprint 71 entry added

## 2026-07-01: Evidence Link Resolution — Knowledge Facts via Company Node ID (Sprint 70)

Decision: add `--knowledge` flag to `atlas watchlist intelligence` and a
`assign_knowledge_facts` function in `atlas/adapters/watchlist.py` that
distributes knowledge facts to watchlist items by ticker or by the explicit
`company-{ticker.lower()}` node ID pattern (e.g. `company-amd` → `AMD`).
Update demo script Step 2 to pass `--knowledge examples/daily_brief_demo/knowledge.json`.

Rationale: knowledge facts in `knowledge.json` use `subject_node_id` values
like `"company-amd"` and `"company-nvda"`, while watchlist items identify
companies by ticker (`"AMD"`, `"NVDA"`). Without a mapping, `WatchlistItem.knowledge_facts`
was always empty, triggering `WatchlistUnknown("No Supporting Knowledge Facts",
"No knowledge facts are linked.", ticker)` which propagated as
`"AMD: No knowledge facts are linked."` into `suggested_next_research_steps` and
ultimately into the Daily Brief's "Suggested Next Research Steps" section.

Matching strategy: deterministic explicit mapping only. A fact matches a
watchlist item when `fact.subject_node_id == ticker` (exact) OR
`fact.subject_node_id == f"company-{ticker.lower()}"`. No fuzzy matching.
The `_node_id_matches_ticker` helper in `atlas/adapters/watchlist.py` is the
single, documented, tested implementation of this rule.

Demo output change: "Suggested Next Research Steps" no longer contains
`"AMD: No knowledge facts are linked."` / `"NVDA: No knowledge facts are linked."`.
Steps now reflect actual watchlist research priorities.

`examples/daily_brief_demo/README.md` Pipeline Steps updated to include
`--knowledge` in Step 2. Expected output updated to match new steps.

## 2026-07-01: Portfolio Demo Integration (Sprint 69)

Decision: add `examples/daily_brief_demo/portfolio.json` and pass `--portfolio`
to `atlas daily summary` in the demo script, completing all five Daily Brief
input surfaces in the demo.

Portfolio file: NVDA 55%, AMD 30%, Cash 15% — static example data, no live
prices, no investment advice. Concentration at 55% triggers `ConcentrationLevel.HIGH`
(threshold ≥ 35%), exercising the HIGH priority path in "What Deserves Attention".

Demo output changes from Sprint 68:
- Opening Summary: overall priority is now `high` (was `moderate`)
- Included Context: now includes `Portfolio: available`
- What Deserves Attention: `[!] Portfolio concentration: Concentration appears
  high. This deserves review.` added
- Portfolio Context section: now present (Holdings: 3, Concentration: High,
  55.0% largest, Cash: 15.0%)
- What Can Safely Wait: portfolio LOW items (holdings count, cash weight) added

`scripts/verify_release_candidate.sh` updated to also check "Portfolio Context"
section presence. All 7 verification steps still green.

12 new tests added to `tests/test_daily_brief_demo.py` (Sprint 69 section).
932 tests pass total (920 prior + 12 new).

## 2026-07-01: Post-RC Smoke Test and Release Verification (Sprint 68)

Decision: verify Atlas Internal RC1 (`atlas-v0.8-internal-rc1`) from a
clean-user perspective and add a release verification script.

Verification results:
- `git tag` confirms `atlas-v0.8-internal-rc1` exists on `main` at `178b27f`
- Compile check: clean
- Full test suite: 910 passed, 0 failed
- Demo: all 7 steps completed; all 7 output files present
- Output sections: Opening Summary, Included Context, What Deserves Attention,
  Company Analysis Context, What Can Safely Wait, Research Framing — all present
- Forbidden language: none found in `daily_brief.txt`
- Cleanup: `rm -rf tmp/atlas_demo` removes all generated files cleanly

Fix: `docs/ReleaseCandidate.md` stated 883 tests (written at Sprint 67 start
before 27 new release tests were counted). Corrected to 910.

Addition: `scripts/verify_release_candidate.sh` — 7-step local verification
script (compile, test, demo, file check, section check, language check,
cleanup). Runs end-to-end in ~20s. No network calls. Self-cleaning.

10 new tests added to `tests/test_release_candidate.py` verifying the
verification script exists and meets all constraints.

920 tests pass total (910 prior + 10 new).

## 2026-07-01: First Internal Release Candidate (Sprint 67)

Decision: declare Atlas v0.1.0-rc1 as the first internal release candidate
(RC1), completing the foundation sprint series (Sprints 36–67).

Deliverables:
- `docs/ReleaseCandidate.md` — RC1 release notes covering: what works, how to
  run tests and the demo, architecture state, release checklist, known
  limitations, technical debt, and next phase recommendation.
- `README.md` — replaced sprint-by-sprint top section with a clean developer
  guide (What Atlas Is, What Atlas Is Not, Current Capabilities table,
  Install, Run Tests, Quickstart, Architecture State, Documentation table,
  Constraints). Sprint notes preserved below a clear "Historical Sprint Notes"
  separator. Duplicate "Install locally" / "Quickstart" sections at the
  bottom cleaned up.
- `docs/ArchitectureConsolidation.md` — updated sprint reference to RC1.
- `tests/test_release_candidate.py` — 27 lightweight static tests verifying
  RC1 document existence, content, no-recommendation-language, and README
  developer-guide sections.

Rationale: after 67 sprints the repository had a clear working pipeline but
no single place that described the current state for a new developer. The
README top section read as a sprint log rather than a project guide. RC1 fixes
this by creating a stable documentation baseline before the next phase begins.

910 tests pass total (883 prior + 27 new).

## 2026-07-01: Local Demo UX Polish and First User Guide (Sprint 66)

Decision: improve the local Daily Brief demo experience and create a clear
user/developer guide for running Atlas locally.

Changes:
- `scripts/run_daily_brief_demo.sh` — added venv auto-detection (`ATLAS=`
  variable resolves `.venv/bin/atlas` or PATH-available `atlas`), added a
  clear error message when neither is found, added blank lines between steps
  for readability, saved Daily Brief output to `tmp/atlas_demo/daily_brief.txt`
  via `tee`, and added a generated-files summary at the end.
- `examples/daily_brief_demo/README.md` — rewritten to include: Purpose,
  What This Is Not, Prerequisites, Quickstart, Input Files table, Generated
  Files table with step mapping, Pipeline Steps (manual commands), Expected
  Output excerpt (accurate to actual demo output including "What Can Safely
  Wait" and "Discovery Context"), Clean Up, Known Limitations, and
  Architecture Notes sections.
- `README.md` — added "Quickstart: Run the Daily Brief Demo" section with
  one-line install, one-line run, cleanup command, and link to full guide.
- `tests/test_daily_brief_demo.py` — added 20 Sprint 66 asset verification
  tests covering: script existence, no network tools, no python one-liners,
  `set -euo pipefail`, output file, cleanup instructions, error handling,
  README content (disclaimers, sections, forbidden language), and root README
  Quickstart.

Rationale: the demo script failed with `atlas: command not found` for
developers who had not activated the virtualenv. The demo documentation
described an outdated expected output (missing "What Can Safely Wait" and
"Discovery Context" sections added in Sprints 64–65). The root README had
no clear path for a developer to run Atlas locally.

881 tests pass total (861 prior + 20 new).

## 2026-07-01: Daily Brief Priority Routing — HIGH/MODERATE Only in What Deserves Attention (Sprint 65)

Decision: remove LOW priority items from `_opening_section` ("What Deserves Attention")
and route them to the appropriate lower-signal destinations.

Two LOW items were removed from "What Deserves Attention":
1. **Knowledge context** — moved to "Included Context" via `_render_included_context`,
   which now reads `report.knowledge_node_count` (new field on `DailyBriefReport`).
2. **Company analysis with no unknowns** — excluded from `_opening_section` entirely;
   remains visible in "Company Analysis Context" and collected into "What Can Safely Wait"
   by the existing `_collect_safely_wait_items` mechanism from Sprint 64.

The fallback item in "What Deserves Attention" was updated to distinguish two states:
- **No inputs at all** → original "No meaningful developments were identified" message.
- **Inputs exist but all are LOW priority** → new calm message: "Context has been organised.
  No items require immediate attention." Determined by `_has_meaningful_input(data)`.

`DailyBriefReport` gained `knowledge_node_count: int = 0` (optional field with default,
no breaking change). The renderer reads it to populate "Included Context".

Rationale: "What Deserves Attention" was losing signal by promoting LOW items into the
same section as HIGH/MODERATE items. Readers had to scan all items to find what truly
needed attention. After this sprint, every item in "What Deserves Attention" is
actionable-research-worthy. LOW items remain visible in context-appropriate sections.

4 pre-existing tests updated to reflect the new routing. 16 new tests added in
`tests/test_daily_brief_priority_routing.py`. 861 tests pass total.

## 2026-07-01: Daily Brief What Can Safely Wait Section (Sprint 64)

Decision: add a "What Can Safely Wait" section to `render_daily_brief_report`
in `atlas/capabilities/daily_brief/engine.py`, populated by a new private
helper `_collect_safely_wait_items`.

The helper scans all sections except "What Deserves Attention" (the opening
summary) for LOW priority items and returns them in section order. The
renderer appends the section after "Suggested Next Research Steps" and before
"Research Framing" when the collected list is non-empty. No model changes
were required — LOW priority items already existed in the report structure.

Rationale: LOW priority items appeared throughout detail sections with no
visual distinction from MODERATE items (both rendered without a priority
marker). Readers had no consolidated view of what could be deferred. The new
section collects these items in one place so readers can quickly identify
what does not require immediate research attention. "LOW priority" means
"can be reviewed later," not "unimportant."

Sources collected: Portfolio Context (holdings, low concentration, cash weight),
Company Analysis Context (companies with no unknowns), Watchlist Context
(suggested research steps). "What Deserves Attention" is excluded to avoid
duplicating the aggregate summary items it contains.

The section is omitted when no inputs are supplied, when all company reports
have unknowns (MODERATE), or when no LOW items exist in any detail section.

22 new tests added in `tests/test_daily_brief_safely_wait.py`. All 823
pre-existing tests continue to pass (845 total).

## 2026-07-01: Daily Brief Opening Summary Alignment (Sprint 63)

Decision: add `_company_analysis_opening_item` helper and call it from
`_opening_section` so company analysis reports always generate an item in
the "What Deserves Attention" section.

Rationale: before Sprint 63, "What Deserves Attention" displayed the
"Status: No meaningful developments" fallback even when company analysis
reports were present — contradicting the Opening Summary which correctly
stated those reports were available. The fix is targeted: a new private
helper inspects `data.company_reports`, counts companies with unknowns,
and returns a `DailyBriefItem` with `moderate` priority if any company has
unknowns, or `low` if all are clean. No model changes. No new CLI flags.
No external calls. The fallback "no developments" item is now suppressed
whenever company reports exist.

Priority mapping:
- Any company with unknowns → `moderate` ("includes observations that deserve review")
- All companies clean → `low` ("context is available for review")

27 new tests added in `tests/test_daily_brief_opening_summary.py`. All
796 pre-existing tests continue to pass (823 total).

## 2026-07-01: Daily Brief Output Readability Improvements (Sprint 62)

Decision: rewrite `render_daily_brief_report` in
`atlas/capabilities/daily_brief/engine.py` for improved terminal readability,
and reorder `_build_sections` to surface Company Analysis before Research and
Watchlist.

Changes:
- Separator lines (`─ × 45`) between all major sections.
- "Included Context" block after Opening Summary: lists which companies,
  research projects, watchlist, discovery, and portfolio data are present.
  Omitted when no inputs are supplied.
- Company Analysis Context renders each company as a named group (ticker as
  sub-header, detail indented) rather than a flat list of items.
- Priority markers: `[!]` for high, `[·]` for moderate, no marker for low.
  Removes the noisy `[low]` / `[moderate]` / `[high]` bracket labels.
- Evidence Gaps section now appears before Unresolved Questions (was after).
- Unresolved Questions grouped by company ticker when context is set.
- Section order: Company Analysis Context now appears before Research Context
  and Watchlist Context (was last among detail sections).

Rationale: the previous output was structurally flat, printed debug-style
priority labels, and buried company analysis at the bottom. The new format
makes it immediately clear which companies are included, what deserves
attention, and how unknowns map to each company — without adding features,
AI, or network calls. All changes are in the renderer and section ordering;
the report model and CLI interface are unchanged.

25 new tests added in `tests/test_daily_brief_output_readability.py`. All
771 pre-existing tests continue to pass (796 total).

## 2026-07-01: Fix Evidence Gap Resolver — Gaps from Unknowns, Not Evidence Links (Sprint 61)

Decision: rewrite `_build_evidence_gaps` in `atlas/capabilities/daily_brief/engine.py`
to surface only company analysis `unknowns` whose title contains "evidence" (e.g.
"Missing Evidence"), not `evidence_links`.

Rationale: `evidence_links` on a `CompanyAnalysisReport` represent knowledge
facts the engine *confirmed* as supporting evidence — they are linked, not gaps.
The old implementation iterated `evidence_links` and displayed each as a gap,
which was semantically backwards: confirmed evidence was reported as missing
evidence. The fix scopes gaps per company (AMD gaps cannot appear as NVDA gaps)
and filters by unknown title so metadata unknowns ("Missing Sector", "Missing
Country") are excluded. When all metadata and knowledge facts are supplied, the
Evidence Gaps section no longer appears in the daily brief — which is the correct
outcome. A new `_is_evidence_gap_unknown(title)` helper makes the classification
rule explicit and testable. 17 new unit tests added in
`tests/test_evidence_gap_resolver.py`. Two pre-existing tests that asserted the
buggy behavior were renamed and rewritten to assert correct behavior.

## 2026-07-01: Add --sector and --country to Company Analysis Export (Sprint 57)

Decision: add two optional string flags — `--sector` and `--country` — to
`atlas company-analysis export`. Both populate `Company` fields used by
`CompanyAnalysisEngine` without requiring any network calls or new adapters.

Rationale: Sprint 56 left `Company.sector` and `Company.country` always empty,
causing "Missing Sector" and "Missing Country" unknowns to appear in every
engine-backed export. Both fields accept user-supplied local strings, require no
external lookup, and follow the pattern established in Sprint 56 for optional
metadata flags. When all four metadata flags (`--company-name`, `--sector`,
`--country`, `--business-description`) are supplied alongside `--ticker`, all
core "Missing X" unknowns are eliminated and engine confidence improves to
`moderate`. Only "Missing Evidence" remains when no knowledge facts are
provided. Both flags are entirely optional — omitting them preserves Sprint 56
behavior exactly. No new files were added; only `atlas/cli/main.py` was modified.

## 2026-07-01: Deprecate `atlas daily brief` Command (Sprint 76)

Decision: deprecate `atlas daily brief` in favor of `atlas daily summary`
(Blueprint-aligned). The command now prints a deprecation message and exits
without calling the legacy `DailyBriefEngine` or any provider.

Rationale: Sprint 75 removed the `atlas/daily/` shim. The next natural step is
to eliminate the remaining consumer of `atlas/daily_brief/` (the legacy
provider-coupled engine). Option A (deprecate the command) is smaller and
lower-risk than Option B (wire the command through the new capability). It
reduces provider coupling without changing the Blueprint-aligned path.
`atlas/daily_brief/` remains on disk to allow comparison and confirm no
external consumers exist before deletion in Sprint 77 or later.

## 2026-07-01: Remove Legacy `atlas/daily_brief/` Engine (Sprint 77)

Decision: delete `atlas/daily_brief/` (2 files, 353 lines) after confirming
no active imports remain. Six legacy engine unit tests were removed; one CLI
deprecation test was retained. Three architecture guardrail tests were added.

Rationale: Sprint 76 deprecated `atlas daily brief` and removed the CLI import.
The engine itself had no remaining consumers. Deletion reduces the legacy surface
area and eliminates the last provider-coupled code called by any Daily Brief path.
The guardrail tests ensure the module cannot be silently reintroduced.

## 2026-07-01: Deprecate `atlas watchlist analyze` Command (Sprint 78)

Decision: deprecate `atlas watchlist analyze` in favor of `atlas watchlist
intelligence` (Blueprint-aligned). The command now prints a deprecation message
and exits without calling `WatchlistEngine` or any provider.

Rationale: Follows the two-step pattern from Sprints 76–77. Unlike the daily
brief path (where DailyBriefEngine had only one CLI consumer), WatchlistEngine
is used by 5 other legacy engines. The CLI deprecation is safe and immediate;
full WatchlistEngine deletion requires retiring those 5 dependent engines first,
which is a larger multi-sprint effort outside Sprint 78's scope.

## 2026-07-01: Deprecate `atlas portfolio analyze` Command (Sprint 79)

Decision: deprecate `atlas portfolio analyze` in favor of `atlas portfolio
summary` (Blueprint-aligned, no providers). The command now prints a
deprecation message and exits without calling `PortfolioIntelligenceEngine`
or any provider.

Rationale: Follows the two-step pattern from Sprints 76–78. `atlas portfolio
summary` already exists as the Blueprint-aligned replacement. `atlas portfolio
review` is left unchanged in this sprint — it is a separate legacy path with
its own review engine and will be addressed in Sprint 80 or later.

## 2026-07-01: Deprecate `atlas portfolio review` Command (Sprint 80)

Decision: deprecate `atlas portfolio review` in favor of `atlas portfolio
summary` (Blueprint-aligned, no providers). The command now prints a
deprecation message and exits without calling `PortfolioReviewEngine` or
any provider.

Rationale: Follows the two-step pattern from Sprints 76–79. `atlas portfolio
summary` already exists as the Blueprint-aligned replacement. After Sprint 80,
both `atlas portfolio analyze` (Sprint 79) and `atlas portfolio review` (Sprint
80) are deprecated. `atlas portfolio summary` is the sole active portfolio
command. `PortfolioReviewEngine` remains on disk — it is still referenced by
`AtlasHomeEngine` (Group B) and cannot be deleted without broader consolidation.

## 2026-07-01: Deprecate `atlas evidence assess` Command (Sprint 81)

Decision: deprecate `atlas evidence assess`. No Blueprint-aligned evidence
capability exists yet, so the deprecation message directs users toward future
Blueprint-aligned decision and research capabilities rather than inventing a
specific replacement command.

Rationale: Group C self-contained module. `EvidenceQualityEngine` makes no
provider or network calls, making the CLI deprecation safe and immediate.
The engine itself cannot be deleted yet — it is used by `decision_journal`,
`comparison`, and `watchlist_review` legacy engines. CLI surface area is
reduced; full engine retirement requires broader consolidation.

## 2026-07-01: Deprecate `atlas reason analyze` Command (Sprint 82)

Decision: deprecate `atlas reason analyze`. No Blueprint-aligned reasoning
command exists yet, so the deprecation message directs users toward future
Blueprint-aligned decision and research capabilities rather than inventing
a specific replacement command.

Rationale: Group C self-contained module. `atlas.reasoning.ReasoningEngine`
makes no provider or network calls, making the CLI deprecation safe.
The `_build_reasoning_report` helper was removed as dead code after the
command body was replaced. The engine itself cannot be deleted yet — it is
still lazily imported by `atlas/principles/engine.py`.

Note: `atlas/domains/decision/engine.py` defines a separate `ReasoningEngine`
class (Blueprint-aligned protocol) — this is distinct from the legacy
`atlas.reasoning.ReasoningEngine` and is unaffected by this sprint.

---

## Sprint 83 — 2026-07-01: Deprecate `atlas risk size`

**Decision:** Deprecate `atlas risk size` CLI command (stub, exit 0) rather
than deleting it immediately.

**Rationale:** Same safe two-step pattern as Sprints 76–82. The `atlas/risk/`
engine is self-contained (Group C) and has no provider dependencies in the CLI
path. However, `RiskAnalysis` (a data type) is still imported by
`atlas/intelligence/`, `atlas/reasoning/`, and `atlas/conversation/` engines.
`RiskEngine` itself has no remaining non-CLI callers — but engine deletion
belongs to a future sprint after those consumers are confirmed removable.

**Alternatives considered:**
- Immediate deletion: too broad; `RiskAnalysis` type still in use elsewhere.
- Immediate migration: no Blueprint-aligned risk-sizing capability exists yet;
  inventing a replacement command would be premature.

**Outcome:** 16 new Sprint 83 deprecation tests; 1068 tests passing.

---

## Sprint 84 — 2026-07-01: Centralized Deprecation Registry

**Decision:** Create `atlas/cli/deprecations.py` as a CLI-local deprecated command
registry. Route all 7 deprecated command bodies through `deprecated_command_message()`.

**Rationale:** Sprints 76–83 each inlined a deprecation message string directly in
the CLI command body. This created 7 copies of near-identical boilerplate with no
single source of truth for message wording, replacement commands, or removal criteria.
The registry consolidates this without changing user-facing behavior.

**Design constraints applied:**
- Registry is CLI-local (no engine, provider, or domain imports)
- No framework dependency — pure Python dataclass + dict
- `DeprecatedCommand` is frozen and deterministic
- User-facing messages are preserved exactly

**Alternatives considered:**
- Leave inline (rejected: no single source of truth, hard to audit retirement readiness)
- Move to domains layer (rejected: deprecation is a CLI concern, not a domain concern)
- Add dynamic lookup at runtime (rejected: over-engineered for a static list of 7 items)

**Outcome:** 46 new registry tests; 1114 tests passing. Architecture boundaries clean.
Recommended Sprint 85: retire `atlas daily brief` command body (engine already deleted).

---

## Sprint 85 — 2026-07-01: Retire `atlas daily brief` Command Body

**Decision:** Remove the `atlas daily brief` command body and registration from
`atlas/cli/main.py`. Move its registry entry to `_RETIRED_REGISTRY`.

**Rationale:** The underlying `atlas.daily_brief` engine was deleted in Sprint 77.
Sprint 76 deprecated the CLI stub, and Sprint 84 centralized its message into the
registry. By Sprint 85 the stub was a pure no-op with no engine dependency, no
provider calls, and no active callers. Removing it is zero-risk and reduces CLI
surface area by one command.

**Alternatives considered:**
- Leave as deprecated stub indefinitely: rejected — the engine is gone, the stub
  serves no purpose, and it clutters the CLI help output.
- Add a compatibility alias: rejected — `atlas daily summary` provides complete
  replacement; a shim would only perpetuate legacy surface area.

**Outcome:** `atlas daily brief` is no longer callable. `atlas daily summary` is
the sole Daily Brief entry point. 1111 tests passing. `_RETIRED_REGISTRY` pattern
established for future retirements.

---

## Sprint 86 — 2026-07-01: Retire `atlas evidence assess` Command Body; Retain Engine

**Decision:** Remove `atlas evidence assess` command body. Retain `atlas/evidence/`
engine (`EvidenceQualityEngine`) on disk.

**Rationale:** The CLI stub was a pure no-op with no engine calls. Removing it is
zero-risk and reduces CLI surface area. However, the engine itself cannot be deleted:
three active non-deprecated legacy engines instantiate `EvidenceQualityEngine` —
`atlas/comparison/`, `atlas/decision_journal/`, and `atlas/watchlist_review/`. Deleting
the engine would break all three.

**Finding from sprint:** The Sprint 81 doc comment ("self-contained Group C module,
no known dependents") was incorrect — the engine has three callers that were not
identified at deprecation time. Tests now explicitly assert caller presence as an
invariant, so future sprints cannot accidentally delete the engine without updating them.

**Alternatives considered:**
- Delete engine despite active callers: rejected — would break comparison, decision
  journal, and watchlist review functionality.
- Defer command retirement until engine can be deleted: rejected — command and engine
  deletion are independent; retiring the stub costs nothing and reduces surface area.

**Outcome:** Command retired. Engine stays. 1107 tests passing. `_RETIRED_REGISTRY`
now has 2 entries (daily brief, evidence assess).

---

## Sprint 87 — 2026-07-01: Retire `atlas reason analyze` Command Body; Retain Engine

**Decision:** Remove `atlas reason analyze` command body. Retain `atlas/reasoning/`
engine on disk.

**Rationale:** The CLI stub was a pure no-op — safe to remove regardless of engine
state. The underlying `atlas.reasoning.ReasoningEngine` cannot be deleted yet because
`atlas/principles/engine.py` contains a lazy import of `render_reasoning_report`
inside `check_reasoning_report()`.

**Key finding from sprint:** `check_reasoning_report()` has no external callers —
it is exported by `atlas/principles/__init__.py` but nothing calls it. The lazy
import therefore never fires at runtime. This means the `atlas.reasoning` runtime
dependency is weaker than previously documented, but the import statement still
exists and engine deletion still requires removing it explicitly.

**TYPE_CHECKING import note:** `atlas/principles/engine.py` also imports `ReasoningReport`
under `if TYPE_CHECKING:` — this is not a runtime dependency and does not block deletion.

**Blueprint-aligned ReasoningEngine note:** `atlas/domains/decision/engine.py` defines
its own `ReasoningEngine` protocol class — completely separate from the legacy
`atlas.reasoning.ReasoningEngine`. Not affected by this sprint.

**Outcome:** Command retired. Engine stays. 1104 tests passing. `_RETIRED_REGISTRY`
now has 3 entries (daily brief, evidence assess, reason analyze).

---

## Sprint 88 — 2026-07-01: Retire `atlas risk size` Command Body; Retain Engine

**Decision:** Remove `atlas risk size` command body. Retain `atlas/risk/` module.

**Rationale:** The CLI stub was a pure no-op — safe to remove. The underlying
`RiskEngine` has no production instantiation points outside the deprecated command.
However, `RiskAnalysis` (a data type in the same file) is still actively imported
by `atlas/conversation/`, `atlas/intelligence/`, and `atlas/reasoning/`. Deleting
`atlas/risk/engine.py` would break those three imports. Separating `RiskEngine` from
`RiskAnalysis` in the same file is possible but constitutes surgical refactoring that
belongs in its own sprint rather than alongside a command retirement.

**Sprint spec rule applied:** "If RiskEngine and RiskAnalysis live in the same file
and separating them would create migration risk, do not delete the engine in this
sprint." — applied exactly as specified.

**Outcome:** Command retired. Engine stays. 1101 tests passing. `_RETIRED_REGISTRY`
now has 4 entries (daily brief, evidence assess, reason analyze, risk size).
Active deprecated `_REGISTRY` now has 3 entries (watchlist analyze, portfolio analyze,
portfolio review).

## Sprint 89 — 2026-07-02: Retire `atlas portfolio analyze` Command Body; Retain Engine

**Decision:** Remove `atlas portfolio analyze` command body. Retain `atlas/analysis/portfolio` module.

**Rationale:** The CLI stub was a pure no-op — safe to remove. The underlying
`PortfolioIntelligenceEngine` (and the shared types `Portfolio` and `PortfolioAnalysis`)
are still actively imported by 10+ modules across the codebase: `atlas/intelligence`,
`atlas/conversation`, `atlas/decision`, `atlas/dashboard`, `atlas/reasoning`, `atlas/home`,
`atlas/suitability`, `atlas/risk_drift`, `atlas/monitoring`, and `atlas/portfolio_review`.
Deleting the engine would break all those imports. Engine deletion deferred until all
callers are retired.

**Sprint 89 did not retire `atlas portfolio review`** — it remains an active deprecated
command (stub only). Retiring it was left for Sprint 90 to avoid scope creep and to allow
a focused import audit of `PortfolioReviewEngine`.

**Outcome:** Command retired. Engine stays. 1106 tests passing. `_RETIRED_REGISTRY`
now has 5 entries (daily brief, evidence assess, reason analyze, risk size, portfolio analyze).
Active deprecated `_REGISTRY` now has 2 entries (watchlist analyze, portfolio review).

## Sprint 90 — 2026-07-02: Retire `atlas portfolio review` Command Body; Retain Engine

**Decision:** Remove `atlas portfolio review` command body. Retain `atlas.portfolio_review` module.

**Rationale:** The CLI stub was a pure no-op — safe to remove. The import audit revealed
one active non-deprecated production caller: `atlas/home/engine.py` (`AtlasHomeEngine`)
imports `PortfolioReviewEngine` and `PortfolioReviewInput` from `atlas.portfolio_review`
and instantiates `PortfolioReviewEngine()` at runtime. Engine deletion was therefore
blocked — this is the same pattern used in Sprints 86–89.

**Important naming note:** `atlas.domains.portfolio.review` defines its own
`PortfolioReviewEngine` (Blueprint-aligned). This is a completely separate class from
the legacy `atlas.portfolio_review.PortfolioReviewEngine`. The Blueprint version is
unaffected by this sprint. The legacy version remains on disk for `AtlasHomeEngine`.

**Engine deletion path:** Retire or migrate `AtlasHomeEngine` to use the Blueprint-aligned
`atlas.domains.portfolio.review.PortfolioReviewEngine` instead of the legacy one.
Once that migration is complete, `atlas.portfolio_review` can be deleted.

**Outcome:** Command retired. Engine stays. 1111 tests passing. `_RETIRED_REGISTRY`
now has 6 entries (daily brief, evidence assess, reason analyze, risk size, portfolio analyze,
portfolio review). Active deprecated `_REGISTRY` now has 1 entry (watchlist analyze).

## Sprint 91 — 2026-07-02: Retire `atlas watchlist analyze` Command Body; Retain Engine

**Decision:** Remove `atlas watchlist analyze` command body. Retain `atlas.analysis.watchlist` module.

**Rationale:** The CLI stub was a pure no-op — safe to remove independently of engine deletion.
The import audit confirmed five active non-deprecated production callers of `WatchlistEngine`:
`atlas/intelligence`, `atlas/decision`, `atlas/monitoring`, `atlas/watchlist_review`, and
`atlas/conversation`. Engine deletion requires retiring all five callers — a multi-sprint
effort deferred to Sprint 92+.

**Sprint 91 completes the CLI deprecated command retirement plan.** All seven originally
deprecated CLI commands (daily brief, evidence assess, reason analyze, risk size, portfolio
analyze, portfolio review, watchlist analyze) have now had their command bodies retired.
The active `_REGISTRY` is empty. `atlas/cli/deprecations.py` is retained for retired-command
history and audit purposes.

**Outcome:** Command retired. Engine stays. 1116 tests passing (3 skipped — parametrized
tests with empty EXPECTED_COMMANDS, by design). `_RETIRED_REGISTRY` now has 7 entries.
Active `_REGISTRY` is empty.

## Sprint 92 — 2026-07-02: WatchlistEngine Caller Audit; Redundant Double-Run Eliminated

**Decision:** Audit `atlas/monitoring/` and `atlas/watchlist_review/` as WatchlistEngine caller
targets. Both are active CLI-backed modules — neither can be retired this sprint. Eliminate the
redundant double WatchlistEngine invocation found in `WatchlistReviewEngine.review()`. Add an
exclusivity guardrail test on the WatchlistEngine caller set.

**Rationale:** Both `atlas/monitoring/` and `atlas/watchlist_review/` power active CLI commands
(`atlas monitor watchlist` and `atlas watchlist review` respectively). Retirement is blocked.
However, the audit revealed `WatchlistReviewEngine.review()` was calling `WatchlistEngine.analyze()`
twice on the same inputs per review — once directly, once again inside
`MonitoringEngine.snapshot_watchlist()`. Extracting `snapshot_watchlist_from_analysis()` from
`MonitoringEngine` and updating `review()` to use it eliminates the redundant run without changing
behavior. Sharing the `WatchlistEngine` instance between `WatchlistReviewEngine` and its internal
`MonitoringEngine` reduces object count from 2 to 1.

Adding the caller exclusivity guardrail (`test_watchlist_engine_callers_are_exactly_the_known_set`)
prevents new WatchlistEngine callers from being added unnoticed during future sprints.

**Outcome:** WatchlistEngine caller count unchanged at 5. Redundant double-run eliminated.
One shared WatchlistEngine instance in WatchlistReviewEngine. Exclusivity guardrail added.
1118 tests passing (3 skipped). Demo passed. Release verification green.

## Sprint 93 — 2026-07-02: Remove WatchlistEngine from Monitoring Runtime Path

**Decision:** Replace `atlas monitor watchlist` CLI path with Blueprint-aligned `WatchlistIntelligenceEngine`,
removing `WatchlistEngine` from `atlas/monitoring/engine.py`. Retain `snapshot_watchlist_from_analysis()`
in `MonitoringEngine` for `watchlist_review`'s use.

**Rationale:** Sprint 92 isolated the watchlist monitoring path behind `snapshot_watchlist_from_analysis`.
Sprint 93's goal was to remove `WatchlistEngine` from monitoring entirely. The Blueprint-aligned
`WatchlistIntelligenceEngine` accepts `WatchlistIntelligenceInput` (name + minimal ticker items)
and produces research-coverage signals (items needing attention, evidence gaps, open questions)
rather than company scores. This is a valid replacement because:
- `atlas monitor watchlist` is about tracking research coverage gaps, not scoring companies
- The new signals are deterministic, local-only, provider-free
- No recommendation language; no buy/sell language
- The architecture boundary permits legacy modules to import capabilities (only domains are forbidden)

`snapshot_watchlist_from_analysis(analysis: WatchlistAnalysis)` is retained in `MonitoringEngine`
because `atlas/watchlist_review/engine.py` still calls it after computing its own `WatchlistAnalysis`
via its direct `WatchlistEngine`. That dependency is the Sprint 94 target.

**Output change:** `atlas monitor watchlist` signals changed from company-score-based (atlas_score,
valuation.score, quality.score) to research-coverage-based (items needing attention, evidence gaps,
open questions). Behavior intent preserved (monitoring research coverage health). Documented.

**Outcome:** WatchlistEngine caller count reduced 5 → **4** (intelligence, decision, watchlist_review,
conversation). `atlas/monitoring/engine.py` no longer imports `WatchlistEngine`. Provider parameter
made optional in `monitor_watchlist`/`snapshot_watchlist` — CLI call unchanged. 1121 tests passing
(3 skipped). Demo passed. Release verification green.

## Sprint 94 — 2026-07-02: Remove WatchlistEngine from Watchlist Review

**Decision:** Replace `atlas/watchlist_review/engine.py` direct `WatchlistEngine` usage with the
Blueprint-aligned `MonitoringEngine.snapshot_watchlist()` (introduced Sprint 93). Remove
`snapshot_watchlist_from_analysis()` from `MonitoringEngine` once it has no runtime callers.

**Rationale:** `WatchlistReviewEngine.review()` used `WatchlistEngine.analyze()` to produce a
`WatchlistAnalysis` for two purposes: (1) as input to `snapshot_watchlist_from_analysis()` for the
monitoring snapshot, and (2) to supply `atlas_score` and `confidence` per ticker to `_review_items`.
Sprint 93 made `MonitoringEngine.snapshot_watchlist(watchlist)` Blueprint-aligned — so purpose (1)
can be replaced with a direct call to that method (no legacy analysis needed as intermediate).
Purpose (2) (per-ticker `atlas_score`) cannot be replaced without WatchlistEngine or a provider call,
so `_review_items` now defaults to `base_score=45` for all companies. This is a documented, acceptable
behavior change: `relevance_score` values become less differentiated but remain deterministic and
local-only. With `snapshot_watchlist_from_analysis` now having no runtime callers, the bridge method
is deleted from `MonitoringEngine`, and `WatchlistAnalysis` is dropped from its imports.

**Outcome:** WatchlistEngine caller count reduced 4 → **3** (intelligence, decision, conversation).
`atlas/watchlist_review/engine.py` and `atlas/monitoring/engine.py` both no longer import
`WatchlistEngine`. `snapshot_watchlist_from_analysis` removed. 1121 tests passing (3 skipped).
Demo passed. Release verification green.

---

**Sprint 95 (2026-07-02): Remove WatchlistEngine from `atlas/decision/decision_engine.py`**

**Decision:** Replace `AtlasDecisionEngine` direct `WatchlistEngine` usage with `WatchlistIntelligenceEngine` (Blueprint capability), following the Sprint 93/94 pattern.

**Rationale:**
- `atlas/decision/` was the smallest remaining WatchlistEngine caller — clear migration path.
- `DecisionResult.watchlist_intelligence` now carries richer research signals (`WatchlistIntelligenceReport`) rather than legacy scoring output (`WatchlistAnalysis`).
- Consistent with Blueprint principle: decision layer should consume capability-level intelligence, not raw legacy engine scores.
- Confidence bonus (+4 for watchlist context) preserved unchanged — only the underlying source changes.

**Alternatives considered:**
- Keep `WatchlistAnalysis` in `DecisionResult` and only remove `WatchlistEngine` from the engine: rejected — would leave a dead import of `WatchlistAnalysis` in the result model.
- Migrate `atlas/conversation/` first: deferred — conversation has more surface area; decision was lower risk.

**Outcome:** WatchlistEngine caller count reduced 3 → **2** (intelligence, conversation).
`atlas/decision/decision_engine.py` no longer imports `WatchlistEngine`. `DecisionResult.watchlist_intelligence` holds `WatchlistIntelligenceReport | None`. 1122 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 96 (2026-07-02): Final WatchlistEngine caller audit and migration order decision**

**Decision:** Migrate `atlas/intelligence/` first (Sprint 97), then `atlas/conversation/` (Sprint 98). Do not migrate either in Sprint 96.

**Rationale:**
- Sprint 96 is an audit sprint only. Both remaining callers are more central than prior targets (monitoring, watchlist_review, decision).
- `atlas/intelligence/` is categorically lower risk: `WatchlistAnalysis` content is never rendered or surfaced in user-visible output. The only effect is a confidence bonus (+3 for non-None watchlist) and a passthrough field in `IntelligenceReport`.
- `atlas/conversation/` has a direct WATCHLIST_REVIEW response path that renders six specific `WatchlistAnalysis` fields (`strongest_opportunity`, `cheapest_valuation`, `highest_quality_company`). These have no 1:1 Blueprint equivalents. The semantic shift requires deliberate output design.
- `ConversationEngine.__init__` passes `watchlist_engine=self.watchlist_engine` into `IntelligenceEngine(...)`. Sprint 97 removing this parameter from `IntelligenceEngine.__init__` makes Sprint 97 a prerequisite for Sprint 98's cleanup.

**Alternatives considered:**
- Migrate conversation first: rejected — higher semantic risk, dependent on intelligence migration for clean kwarg removal.
- Migrate both in Sprint 96: rejected — this is a planning sprint; runtime changes require independent test coverage and careful output change documentation.
- Leave both for deletion with WatchlistEngine: rejected — doing the migration first decouples type cleanup from engine deletion.

**Outcome:** Migration plan document created at `docs/WatchlistEngineMigrationPlan.md`. Caller count remains 2. No runtime changes. 1122 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 97 (2026-07-02): Remove WatchlistEngine from `atlas/intelligence/engine.py`**

**Decision:** Replace `IntelligenceEngine` direct `WatchlistEngine` usage with `WatchlistIntelligenceEngine` (Blueprint capability), following the Sprint 95 pattern. Remove `watchlist_engine` from `IntelligenceEngine.__init__`.

**Rationale:**
- Sprint 96 identified this as the lower-risk migration: `WatchlistAnalysis` content was never rendered in any intelligence output string; the only effect was a confidence bonus (+3) and a stored passthrough field.
- `IntelligenceReport.watchlist_intelligence` now carries `WatchlistIntelligenceReport | None` — richer research signals replace legacy scoring output, consistent with Blueprint architecture.
- Removing `watchlist_engine` from `IntelligenceEngine.__init__` simplifies Sprint 98: `ConversationEngine.__init__` no longer needs to pass it through.
- Provider is no longer passed to the watchlist analysis path — `WatchlistIntelligenceEngine` needs no provider, reducing provider coupling.

**Alternatives considered:**
- Keep `WatchlistAnalysis` field in `IntelligenceReport` and only remove the engine param: rejected — would leave stale type annotation; field is a passthrough nobody reads.
- Migrate conversation first: deferred — conversation has deeper semantic coupling (`_answer_watchlist_review()` renders 6 specific WatchlistAnalysis fields with no 1:1 Blueprint equivalents).

**Outcome:** WatchlistEngine caller count reduced 2 → **1** (conversation only).
`atlas/intelligence/engine.py` no longer imports `WatchlistEngine`. `IntelligenceReport.watchlist_intelligence` holds `WatchlistIntelligenceReport | None`. 1124 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 98 (2026-07-02): Remove WatchlistEngine from `atlas/conversation/engine.py`; active caller count → 0**

**Decision:** Rewrite `_answer_watchlist_review()` to use `WatchlistIntelligenceEngine`; adopt research-attention output framing; set confidence to 70 (matching Blueprint monitoring pattern).

**Rationale:**
- This is the final active WatchlistEngine caller. After Sprint 98, the active caller count is zero.
- `_answer_watchlist_review()` previously rendered 6 legacy `WatchlistAnalysis` fields (`strongest_opportunity`, `cheapest_valuation`, `highest_quality_company`, `final_atlas_view`, `name`). None have 1:1 equivalents in `WatchlistIntelligenceReport`, requiring deliberate field mapping.
- Output framing shift from score-ranking to research-attention is intentional: Blueprint watchlist intelligence surfaces research gaps and coverage priorities, not ranked investment scores. Keeping score-ranking language ("Atlas ranks X first") would misrepresent the underlying data source.
- `confidence` changed from 80 to 70 for consistency with the Blueprint monitoring watchlist path (Sprint 93 established 70 as the Blueprint watchlist confidence baseline).
- Provider no longer passed to `_answer_watchlist_review()` — `WatchlistIntelligenceEngine` needs none. This is a provider boundary reduction, not expansion.

**Alternatives considered:**
- Keep `confidence=80`: rejected — 80 was a legacy hardcode unrelated to the Blueprint output; 70 matches the established Blueprint watchlist pattern.
- Map `cheapest_valuation`/`highest_quality_company` to dedicated Blueprint fields: no 1:1 equivalent exists; `evidence_gaps[0].detail` and `observations[0].detail` provide the closest research-coverage substitutes.

**Outcome:** WatchlistEngine active caller count: 1 → **0**. All active callers retired across Sprints 93–98. `WatchlistEngine` and `atlas/analysis/watchlist.py` retained for Sprint 99 deletion. 1124 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 99 (2026-07-02): Delete `WatchlistEngine`; slim `atlas/analysis/watchlist.py` to types only**

**Decision:** Delete `WatchlistEngine`, `WatchlistAnalysis`, `WatchlistSignal`, `WatchlistRecommendation`, and `render_watchlist_analysis` from `atlas/analysis/watchlist.py`. Retain file with `Watchlist` and `WatchlistItem` only. Delete `tests/test_watchlist.py`. Flip guardrail tests.

**Rationale:**
- Active WatchlistEngine caller count reached zero in Sprint 98. Deletion criteria met.
- `atlas/analysis/watchlist.py` cannot be fully deleted: 7 production modules import `Watchlist`/`WatchlistItem` as input types, and `atlas/shared/entities.py`'s `Watchlist` has a different structure (`tickers: tuple[str, ...]` vs `items: tuple[WatchlistItem, ...]`) — not a drop-in substitute.
- Slimming the file to types only achieves the deletion mission for `WatchlistEngine` while preserving the input contract that 7 callers depend on.
- `tests/test_watchlist.py` tested only `WatchlistEngine.analyze()` and `render_watchlist_analysis()` — both removed. No surviving test content; deletion is correct.

**Alternatives considered:**
- Migrate all type-only callers to `atlas/shared/entities.py` `Watchlist` in the same sprint: rejected — different field structure (`tickers` vs `items`) makes this a multi-file semantic migration; deferred to Sprint 100+.
- Full file deletion: rejected — would break 7 production module imports without a substitute type.

**Outcome:** `WatchlistEngine` deleted. `atlas/analysis/watchlist.py` slimmed to 33 lines. `tests/test_watchlist.py` deleted. Guardrails flipped to confirm non-importability. 1119 tests passing (3 skipped).

---

**Sprint 100 (2026-07-02): Post-WatchlistEngine architecture checkpoint; type migration plan created**

**Decision:** No runtime changes. Audit legacy watchlist state; add non-importability guardrails; create `docs/WatchlistTypeMigrationPlan.md`; recommend `WatchlistInput`/`WatchlistInputItem` in `atlas/capabilities/watchlist_intelligence/` as migration destination.

**Rationale:**
- WatchlistEngine deletion is confirmed complete. All deleted symbols (`WatchlistEngine`, `WatchlistAnalysis`, `WatchlistRecommendation`, `render_watchlist_analysis`) pass non-importability guardrails.
- `atlas/analysis/watchlist.py` contains only `Watchlist` and `WatchlistItem` — confirmed by source scan and new guardrail test.
- 7 production modules import `Watchlist`/`WatchlistItem` for CLI input parsing only. None use engine logic. All can be updated with mechanical import path changes in one sprint.
- Recommended destination is `atlas/capabilities/watchlist_intelligence/` (renamed to `WatchlistInput`/`WatchlistInputItem`) because: (a) the type is a capability input, not a domain entity; (b) `atlas/shared` already owns a structurally different `Watchlist`; (c) `atlas/domains/watchlist/` re-exports `atlas.shared.Watchlist` — adding a different `Watchlist` there creates a namespace conflict.

**Alternatives considered:**
- `atlas/shared/entities.py`: rejected — different structure; `from_json_file`/`from_mapping` are CLI input concerns, not canonical entity concerns.
- `atlas/domains/watchlist/`: rejected — namespace conflict with re-exported `atlas.shared.Watchlist`.
- Keep in `atlas/analysis/watchlist.py` permanently: rejected — perpetuates legacy analysis package as a type source.

**Outcome:** No runtime changes. 6 guardrails added. `docs/WatchlistTypeMigrationPlan.md` created. 1125 tests passing (3 skipped). Demo passed. Release verification green. Sprint 101 target: migrate `Watchlist`/`WatchlistItem` to `atlas/capabilities/watchlist_intelligence/` as `WatchlistInput`/`WatchlistInputItem`; delete `atlas/analysis/watchlist.py`.

---

**Sprint 101 (2026-07-02): Move `Watchlist`/`WatchlistItem` to capability layer; delete `atlas/analysis/watchlist.py`**

**Decision:** Add `WatchlistInput`/`WatchlistInputItem` to `atlas/capabilities/watchlist_intelligence/models.py`. Update all 7 production callers and 5 test files. Delete `atlas/analysis/watchlist.py`. No logic changes.

**Rationale:**
- As planned in Sprint 100, the legacy `Watchlist`/`WatchlistItem` were CLI input types that existed in the wrong layer. Moving them to the capability module that owns the watchlist analysis pipeline is Blueprint-aligned.
- Renaming to `WatchlistInput`/`WatchlistInputItem` distinguishes them from the canonical `atlas/shared/entities.py` `Watchlist` (domain entity) and the rich `atlas/capabilities/watchlist_intelligence/models.py` `WatchlistItem` (capability input).
- All 7 production callers used `Watchlist` only as a type annotation or via `from_json_file`/`from_mapping`. All changes were mechanical import path updates and type renames with no logic changes.
- `atlas/cli/deprecations.py` string reference (`legacy_module="atlas.analysis.watchlist"`) is historical metadata — correctly retained as a registry record; not an import.

**Alternatives considered:**
- Compatibility shim in `atlas/analysis/watchlist.py` re-exporting from capability: rejected — Sprint spec explicitly prohibits shims; full deletion achieves cleaner architecture.

**Outcome:** `atlas/analysis/watchlist.py` fully deleted. `atlas.analysis.watchlist` raises `ModuleNotFoundError`. `WatchlistInput`/`WatchlistInputItem` accessible from `atlas.capabilities.watchlist_intelligence`. 1124 tests passing (3 skipped). Demo passed. Release verification green. No behavior changes.

---

**Sprint 102 (2026-07-02): Analysis cleanup audit; `ComparisonEngine` selected as Sprint 103 target**

**Decision:** No runtime changes. Audit `atlas/analysis/` modules; recommend `ComparisonEngine` for Sprint 103 over `MemoryEngine`.

**Rationale:**
- `ComparisonEngine` has 2 production caller sites (both `atlas/decision/`), 0 active CLI commands, no Blueprint gap (legacy ranking; Blueprint `InvestmentComparisonEngine` exists), and a self-contained module with no cross-domain dependencies. Inline ranking option (Option A) can eliminate the engine without output changes.
- `MemoryEngine` has 4 caller sites, 3 active CLI commands (`atlas memory save/show/compare`), no Blueprint equivalent, and user-data coupling (local JSON files). Higher risk and complexity.
- Ordering: `ComparisonEngine` first because it is contained entirely within the decision engine's optional comparison path, with no CLI surface area. `MemoryEngine` deferred to Sprint 104+ pending further audit of `atlas memory` CLI command usage.

**Alternatives considered:**
- `MemoryEngine` first: rejected — 3 active CLI commands and user-data coupling make it higher risk than `ComparisonEngine`.
- Both in one sprint: rejected — two different migration patterns; keeping them separate maintains the sprint-per-engine cleanup discipline that has worked well.

**Outcome:** No runtime changes. `docs/AnalysisCleanupPlan.md` created. 1 guardrail test added. 1125 tests passing (3 skipped). Demo passed. Release verification green. Sprint 103 target: `ComparisonEngine`.

---

**Sprint 103 (2026-07-02): Retire `ComparisonEngine`; delete `atlas/analysis/comparison.py`**

**Decision:** Move `ComparisonResult`/`ComparisonRanking`/`ComparisonCandidate` types and ranking logic to `atlas/decision/comparison.py` as a free function; delete `atlas/analysis/comparison.py`.

**Rationale:**
- Option C (retire comparison path entirely) rejected: `_comparison_tickers()` in decision engine pulls from `context.watchlist.items` when a watchlist is set, making the comparison path active whenever watchlist context is provided.
- Option A (inline ranking) chosen: ranking logic is a simple sort across 5 score dimensions. Moving it to `atlas/decision/comparison.py` as `compare_tickers(tickers, provider, investment_engine)` eliminates the `ComparisonEngine` class, removes the constructor param from `AtlasDecisionEngine`, and preserves identical output.
- `ComparisonResult` retained as a type in `atlas/decision/comparison.py` because it is stored on `DecisionResult` and inspected by one test. Changing the output type would be a behavior change; the type move is location-only.

**Alternatives considered:**
- Option B (route through `InvestmentComparisonEngine`): rejected — heavier, different output format, would change `DecisionResult` shape.
- Keep `ComparisonEngine` class: rejected — no benefit to the class wrapper once callers are 0; free function is cleaner.

**Outcome:** `atlas/analysis/comparison.py` deleted. `atlas.analysis.comparison` raises `ModuleNotFoundError`. `ComparisonResult` et al. importable from `atlas.decision.comparison`. `AtlasDecisionEngine` constructor lost `comparison_engine` param. 4 guardrail tests added. 1125 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 104 (2026-07-02): Retire `MemoryEngine`; delete `atlas/analysis/memory.py`**

**Decision:** Move `MemoryEntry`, `MemoryComparison`, `MemoryStore` types and all logic to `atlas/decision/memory.py` as free functions; delete `atlas/analysis/memory.py`. Pattern identical to Sprint 103.

**Rationale:**
- Option A (delete outright) not viable: 3 active CLI commands (`atlas memory save/show/compare`) and `AtlasDecisionEngine._compare_memory()` are active callers.
- Option B (move to `atlas/decision/memory.py`) chosen: decision engine is primary runtime consumer; CLI importing from `atlas.decision.memory` is architecturally acceptable (CLI sits above all layers).
- `MemoryEngine` class eliminated: `load()` was pure delegation (`store.load()`); `save()` inlined; `save_ticker()` and `compare()` become `save_ticker()` and `compare_memory()` free functions.
- No Blueprint-aligned `MemoryStore[MemoryEntry]` was created — the existing concrete `MemoryStore` class moved as-is to avoid scope creep.

**Alternatives considered:**
- Retain with blockers (Option C): rejected — the logic was small and the migration pattern was proven by Sprint 103.
- Move to `atlas/history/`: rejected — `atlas/history/` uses Blueprint `atlas.memory.MemoryStore[Snapshot]`, a different generic abstraction. Merging would require adapting the type system beyond sprint scope.
- Invent new capability (`atlas/tracking/`): rejected — unnecessary scope; `atlas/decision/memory.py` co-locates the logic with its primary runtime consumer.

**Outcome:** `atlas/analysis/memory.py` deleted. `atlas.analysis.memory` raises `ModuleNotFoundError`. `MemoryEntry`/`MemoryStore`/`MemoryComparison` importable from `atlas.decision.memory`. `AtlasDecisionEngine` constructor lost `memory_engine` param. CLI updated to use free functions. 5 guardrail tests added. 1130 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 105 (2026-07-02): Eliminate `ExplanationEngine` class from `atlas/analysis/explanation.py`**

**Decision:** Inline `ExplanationEngine.explain()` logic directly into `explain_investment_report()` free function. File remains at `atlas/analysis/explanation.py`. `ExplanationEngine` class removed.

**Rationale:**
- `ExplanationEngine` was a one-method class (`explain()`) whose only caller was `explain_investment_report()` itself — no external code ever instantiated it directly.
- `explain_investment_report()` was already the public API; the class added no value beyond an unnecessary level of indirection.
- Moving the file out of `atlas/analysis/` is not viable: `atlas/analysis/report.py` imports `explain_investment_report` and `render_investment_explanation`. Moving to `atlas/decision/` or `atlas/capabilities/` would create a backwards dependency (`atlas/analysis/` → `atlas/decision/`), which is architecturally worse than the current state.
- Option B (in-place class elimination) is the correct action: the class is removed, the module becomes a pure free-function module, no behavior changes.

**Alternatives considered:**
- Move to `atlas/capabilities/explanation/`: rejected — `atlas/analysis/report.py` imports from this module; moving it out creates backwards dependency.
- Move to `atlas/decision/explanation.py`: rejected — same reason; `atlas/analysis/` should not depend on `atlas/decision/`.
- Retain as-is (Option C): rejected — the class provided no value; inline is safe and zero-risk.

**Outcome:** `ExplanationEngine` class deleted from `atlas/analysis/explanation.py`. `explain_investment_report()` is now a direct free function. `atlas/analysis/__init__.py` no longer re-exports `ExplanationEngine`. 3 guardrail tests added. 1133 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 106 (2026-07-02): Eliminate `RecommendationEngine` class from `atlas/analysis/scoring.py`**

**Decision:** Remove `RecommendationEngine` (thin one-method wrapper). Retain `ScoringEngine` (has real validation logic). Update tests to use `ThresholdRecommendationPolicy` directly.

**Rationale:**
- `RecommendationEngine` had one public method (`recommend()`) that delegated entirely to `ThresholdRecommendationPolicy.recommend()`. Constructor just forwarded threshold params. No production caller ever instantiated it — only `tests/test_scoring.py`.
- `ScoringEngine` is not a thin wrapper: it has a 4-check `_validate_weights()` static method, two public methods (`score()`, `confidence()`), and a `weights` constructor param. Elimination would lose the weight validation contract. Retained with documentation noting no production callers exist.
- `score_company()` free function retained — wraps `ScoringEngine` and provides the entry point for weight-injected scoring.

**Alternatives considered:**
- Eliminate `ScoringEngine` too: rejected — has real validation logic tested directly; elimination would lose the `_validate_weights()` contract.
- Move `scoring.py` to `atlas/capabilities/`: rejected — no production caller; not worth the migration overhead for a test-utility module.
- Retain `RecommendationEngine` (Option D): rejected — thin wrapper, zero production callers, identical pattern to `ExplanationEngine` eliminated in Sprint 105.

**Outcome:** `RecommendationEngine` class deleted from `atlas/analysis/scoring.py` and removed from `atlas/analysis/__init__.py`. `tests/test_scoring.py` updated to use `ThresholdRecommendationPolicy` directly. `ThresholdRecommendationPolicy` import removed from `scoring.py`. 3 guardrail tests added. 1136 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 107 (2026-07-02): Audit `atlas/analysis/report.py`; remove unused helper**

**Decision:** Retain `report.py` in place (Option C). Remove `render_company_analysis_report` (no callers). Keep `build_investment_report` and `render_investment_report`.

**Rationale:**
- `build_investment_report` has 3 active CLI call sites (lines 219, 265, 1408 of `atlas/cli/main.py`) and 1 Blueprint engine call site (`atlas/comparison/engine.py:214`). Cannot be deleted or moved without updating 4 call sites.
- `render_investment_report` has 2 active CLI call sites. Same retention reasoning.
- `render_company_analysis_report` was a thin one-liner combining the two functions above. Grep confirmed zero external callers — only its own definition. Removed as dead code.
- Moving the file to a Blueprint-aligned layer would create unnecessary churn — 4 callers would need import updates for no architectural gain. The file belongs where it is.

**Alternatives considered:**
- Delete file: rejected — `build_investment_report` and `render_investment_report` are actively used by CLI and Blueprint comparison engine.
- Move to `atlas/capabilities/`: rejected — would require updating 4 call sites and would create backwards-dependency pressure on `atlas/analysis/explanation.py` (which `report.py` imports).
- Simplify in-place: no simplification available beyond removing the dead helper.

**Outcome:** `render_company_analysis_report` removed from `atlas/analysis/report.py`. No `__init__.py` change needed (function was never exported). 2 guardrail tests added. 1138 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 108 (2026-07-02): Post-cleanup checkpoint for `atlas/analysis/`**

**Decision:** Checkpoint sprint — no runtime changes. `atlas/analysis/scoring.py` selected as Sprint 109 deletion target.

**Rationale:**
- Full inventory audit of `atlas/analysis/` confirmed 15 remaining modules (3 deleted in Sprints 101–107).
- `ScoringEngine` and `score_company` in `scoring.py` have zero production callers — confirmed by grep. Only `tests/test_scoring.py` uses them. This makes `scoring.py` the cleanest remaining deletion target.
- `portfolio.py` has 17 production import sites and 16 test files — too high coupling for near-term migration.
- `engine.py` has 10 production import sites and is the foundational scoring engine — leave for last.
- Blueprint `domains/` confirmed import-free from `atlas.analysis` via new AST-based guardrail test.
- All 3 previously deleted modules (`watchlist`, `comparison`, `memory`) confirmed still absent.

**Guardrails added:**
- `test_blueprint_domains_do_not_import_legacy_analysis` — AST scan confirms `atlas/domains/` never imports from `atlas.analysis`.

**Outcome:** 1 guardrail test added. 1138 tests passing (3 skipped). Demo passed. Release verification green. Sprint 109 target: delete `atlas/analysis/scoring.py`.

---

**Sprint 109 (2026-07-02): Delete `atlas/analysis/scoring.py`**

**Decision:** Delete `atlas/analysis/scoring.py`. Remove `ScoringEngine` and `score_company` from `atlas/analysis/__init__.py`.

**Rationale:**
- Sprint 108 grep confirmed zero production callers for `ScoringEngine` and `score_company` across the entire `atlas/` tree.
- `ScoringEngine` wrapped `AtlasInvestmentEngine` with a 4-check weight validation that was never exercised outside tests.
- No provider or network dependency. No runtime behavior changes.
- Removing the module tightens the public `atlas.analysis` surface and eliminates dead API.

**Alternatives considered:**
- Keep as documented test utility: rejected — public re-exports from `atlas.analysis.__init__` imply production availability; keeping dead API is misleading.
- Move weight validation into `AtlasInvestmentEngine`: out of scope — no production caller needs it.

**Outcome:** `atlas/analysis/scoring.py` deleted. 2 names removed from `atlas/analysis/__init__.py`. `tests/test_scoring.py` stripped of 3 dead tests (2 surviving tests kept). 2 guardrail tests updated. 1136 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 110 (2026-07-02): `atlas/analysis/portfolio.py` migration plan**

**Decision:** Multi-sprint migration required. Sprint 111 is a pre-migration guardrail sprint (Phase 1 of 6 already completed in Sprint 110). Phase 2 (type extraction) and Phase 3 (capability creation) are the next implementation targets.

**Rationale:**
- `PortfolioIntelligenceEngine` has no Blueprint equivalent. Cannot retire the module until `atlas/capabilities/portfolio_intelligence/` exists with equivalent 7-dimension portfolio-fit scoring.
- Schema gap: `PortfolioPosition.quality_score` and `risk_score` are not in `atlas.shared.Holding`. A `PortfolioFitProfile` type or `Holding` extension is needed before provider migration.
- `CompanyPortfolioProfile` is embedded in `CompanyDataProvider.get_portfolio_profile()`. 3 providers must be updated atomically.
- 17 production import sites make a bulk migration unsafe. One caller per sprint is the only safe approach.
- `render_portfolio_analysis` has zero active non-test production callers — can be removed as a low-risk first step in a future sprint.

**Documents created:** `docs/PortfolioAnalysisMigrationPlan.md`

**Guardrails added:** 3 pre-migration tests confirming domain is intact, adapter path is in use, and `render_portfolio_analysis` has no active production callers.

**Outcome:** 3 guardrail tests added. 1139 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 111 (2026-07-02): Delete `render_portfolio_analysis` from `atlas/analysis/portfolio.py`**

**Decision:** Delete `render_portfolio_analysis`. Also delete `_score_line` and `_signal_line` private helpers (only used by the deleted function). Remove re-export from `atlas/analysis/__init__.py`.

**Rationale:**
- Sprint 110 guardrail test confirmed zero active production callers. Only `atlas/analysis/__init__.py` re-exported it and `tests/test_portfolio.py` tested it.
- `render_portfolio_analysis` was the output renderer for the retired `atlas portfolio analyze` CLI command (retired Sprint 89). No active CLI command or engine calls it.
- The `_score_line` and `_signal_line` helpers were internal to `render_portfolio_analysis` and have no other callers.
- No provider or network dependency. Pure rendering logic.

**Outcome:** 3 symbols deleted from `portfolio.py`. 1 re-export removed from `__init__.py`. 1 test removed from `tests/test_portfolio.py`. 2 guardrail tests added. 1139 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 112 (2026-07-02): Create `atlas/capabilities/portfolio_intelligence/` stub**

**Decision:** Create new capability package with `PortfolioFitInput`, `PortfolioFitResult`, and `PortfolioFitDimension`. Omit `recommendation` enum from `PortfolioFitResult`. Rename `portfolio_score` → `fit_score`, `final_reasoning` → `summary`, `reasoning` → `note`.

**Rationale:**
- Blueprint layer must not carry advisory semantics (`PortfolioRecommendation.STRONG_ADD` / `ADD` / `REDUCE` etc.) — these belong to the legacy layer or to future user-facing rendering only.
- `fit_score` is more neutral than `portfolio_score` — it describes analytical output, not a grade.
- `summary` is more neutral than `final_reasoning` — the legacy field name implies a recommendation path.
- `note` vs `reasoning` — `PortfolioFitDimension.note` avoids the implication that a score requires a justification/argument rather than a factual observation.
- All legacy fields preserved where semantically equivalent — `ticker`, `company`, `sector`, `country`, `market_cap`, `quality_score`, `risk_score` are direct mappings.
- No provider or network dependency introduced. No existing callers changed.

**Outcome:** 3 new types. 12 tests. Boundary constraints verified by AST scan in tests. 1151 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 113 (2026-07-02): Implement `PortfolioIntelligenceCapability` engine**

**Decision:** Port 7-dimension scoring logic from `atlas/analysis/portfolio.py` into `atlas/capabilities/portfolio_intelligence/engine.py` as a new `PortfolioIntelligenceCapability` class. Accept `atlas.shared.Portfolio` (not legacy `Portfolio`). Document schema gap rather than working around it.

**Rationale:**
- Logic is ported, not wrapped — the new engine does not import `PortfolioIntelligenceEngine` or any legacy analysis symbol. This preserves the clean architecture boundary.
- `atlas.shared.Portfolio` is the correct input type for the Blueprint layer. Using the legacy `atlas.analysis.portfolio.Portfolio` would violate the architectural boundary.
- Schema gap (`atlas.shared.Holding` lacks `quality_score`, `risk_score`, `market_cap`) is real and affects 3 of 7 dimensions. Returning neutral scores with documented notes is correct: callers will know what's partial, and future `atlas.shared.Holding` extension will resolve these gaps without breaking callers.
- Weights in `_aggregate_fit_score` mirror the legacy exactly — this is intentional so aggregate behavior is comparable even while individual dimensions differ.
- No callers migrated — the legacy engine remains the active production path. This sprint adds capability alongside, not in replacement.

**Outcome:** `PortfolioIntelligenceCapability` engine created. 30 tests. 1181 tests passing (3 skipped). Demo passed. Release verification green.

---

**Sprint 114 (2026-07-02): Resolve schema gap; migrate conversation portfolio-fit to capability**

**Decision 1: Extend `atlas.shared.Holding` (Option A) rather than create `PortfolioFitHolding` (Option B)**

**Rationale:**
- `quality_score`, `risk_score`, `market_cap` make semantic sense on a holding entity — they are attributes of the underlying position, not capability-specific enrichment.
- Only 6 `Holding(...)` instantiation sites; all use keyword args; optional fields (default None) cause zero blast radius.
- Adapter already converts `PortfolioPosition` → `Holding`; natural place to carry enriched fields.
- Option B would have required an extra conversion layer and a capability-specific type with no shared value.

**Decision 2: Retain `portfolio_engine: PortfolioIntelligenceEngine` for `IntelligenceEngine` injection**

**Rationale:**
- Sprint spec: "do not migrate other callers." `IntelligenceEngine` is a separate caller.
- Adding `portfolio_fit_capability` as a second injectable allows conversation's own portfolio review path to use the new capability without touching `IntelligenceEngine`.
- This is the minimal-impact approach — exactly one path changes; all other paths unchanged.

**Decision 3: Keep `ConversationInput.portfolio: Portfolio | None` typed as legacy `Portfolio`**

**Rationale:**
- Changing the type would require updating `atlas/cli/main.py` (which builds `ConversationInput`), which is explicitly out of scope.
- The adapter conversion (`legacy_portfolio_to_domain_portfolio`) happens inside `_answer_portfolio_review` — the legacy Portfolio is converted to `atlas.shared.Portfolio` on the fly. No API surface change.

**Outcome:** 5 files changed. 13 new tests. 1194 tests passing (3 skipped). Demo passed. RC2 green.

---

**Sprint 115 (2026-07-02): Migrate dashboard portfolio-fit to capability**

**Decision:** Same pattern as Sprint 114. `portfolio_engine` retained in constructor for backward compatibility but is no longer called internally. `portfolio_fit_capability` added alongside it.

**Rationale:**
- The `if target_ticker and provider:` block is the only place `portfolio_engine` is used in the dashboard. Migrating just that block leaves the rest of the dashboard (suitability, risk drift, monitoring) untouched.
- Keeping `portfolio_engine` in the constructor is deliberate: it avoids breaking any caller that injects a mock for the old engine in tests, and preserves the public API surface until deletion is safe.
- Field mapping is direct: `portfolio_score` → `fit_score`, `final_reasoning` → `summary`.

**Outcome:** 2 files changed. 6 new tests. 1200 tests passing (3 skipped). Demo passed. RC2 green.

**Sprint 116 (2026-07-02): Migrate portfolio_review internal structural functions to shared Portfolio**

**Decision:** Unlike conversation/dashboard (one isolated block), `portfolio_review/engine.py` uses legacy `Portfolio.positions` throughout 8 private helpers. Migration approach: convert to `shared_portfolio = legacy_portfolio_to_domain_portfolio(review_input.portfolio)` at the top of `review()`, pass `shared_portfolio` to all structural functions, keep `review_input.portfolio` (legacy) for suitability/risk_drift/monitoring downstream. Input boundary type stays `LegacyPortfolio` — the CLI and downstream engines are unchanged.

**Rationale:**
- The entire engine is structural analysis (sectors, weights, quality averages, concentrations) — not portfolio-fit via `PortfolioIntelligenceCapability`. The "migration" here is removing `portfolio.positions` coupling from internal helpers by routing through the shared type.
- Keeping `LegacyPortfolio` at `PortfolioReviewInput.portfolio` avoids cascading changes to suitability, risk_drift, and monitoring engines (all still expect legacy `Portfolio`).
- `_average` updated to handle `quality_score: int | None` (Sprint 114 made it optional on `Holding`) via None-safe list comprehension.

**Outcome:** 2 files changed. 7 new tests. 1207 tests passing (3 skipped). Demo passed. RC2 green.

**Sprint 117 (2026-07-02): Adapter audit checkpoint — centralize PortfolioFitInput builder**

**Decision:** Option C — Centralize `PortfolioFitInput` builder. `legacy_portfolio_to_domain_portfolio` was already centralized. `PortfolioFitInput` construction (7-field 1-to-1 mapping from `CompanyPortfolioProfile`) was verbatim duplicate across conversation and dashboard. Extracted `portfolio_fit_input_from_profile` into `atlas/adapters/portfolio.py`. Portfolio review does not build `PortfolioFitInput` (structural-only path) and is unaffected.

**Rationale:**
- Duplication was genuine and mechanical: identical 7-line block in 2 callers.
- `atlas/adapters/portfolio.py` is the correct home: it already mediates between legacy and Blueprint types; adding `CompanyPortfolioProfile → PortfolioFitInput` conversion is consistent with its purpose.
- Capability engine remains clean: no legacy imports enter `atlas/capabilities/portfolio_intelligence/engine.py`.
- Keeping legacy `PortfolioFitInput` import in conversation/dashboard would have been dead weight after centralization.

**Outcome:** 4 files changed (adapter + 2 callers + new test file). 31 new tests. 1238 tests passing (3 skipped). Demo passed. RC2 green. Recommended Sprint 118: `atlas/reasoning/engine.py`.

**Sprint 118 (2026-07-02): Remove reasoning PortfolioAnalysis direct runtime import**

**Decision:** Option D — TYPE_CHECKING-only import. `PortfolioAnalysis` had runtime field accesses in `_collect_evidence` and `_bearish_factors`, but these are duck-typed attribute accesses that do not require the import at runtime. Added `from __future__ import annotations` (PEP 563) so the type annotation in `ReasoningInput.portfolio_analysis: PortfolioAnalysis | None` becomes a string at class-definition time, eliminating the need for the name to be defined at runtime.

**Rationale:**
- `from __future__ import annotations` is the correct tool: it defers annotation evaluation without changing any runtime behavior.
- `TYPE_CHECKING` guard keeps type checkers (mypy/pyright) fully aware of the type.
- No runtime field access requires an import — Python's duck typing handles attribute access on whatever object is passed.
- Transitive loading of `atlas.analysis.portfolio` via `atlas.analysis.__init__` is a pre-existing package coupling not introduced by reasoning/engine.py — fixing it is out of scope.

**Outcome:** 2 files changed (engine + test). 7 new tests. 1245 tests passing (3 skipped). Demo passed. RC2 green. Recommended Sprint 119: `atlas/risk_drift/engine.py`.

**Sprint 134 (2026-07-02): Planning sprint — audit `Portfolio`/`PortfolioPosition` remaining callers**

**Decision:** Sprint 135 target is "lift and shift" — move `Portfolio`, `PortfolioPosition`, and 2 private helpers from `atlas/analysis/portfolio.py` into `atlas/adapters/portfolio.py` and delete the source file in the same sprint.

**Rationale:**
- All 12 production import sites are now mapped (3 runtime + 1 re-export + 8 annotation-only).
- `atlas/adapters/portfolio.py` is the correct destination: already the legacy compatibility boundary, already imports `LegacyPortfolio`; making it self-contained eliminates the circular dependency direction.
- `atlas.shared.Portfolio` and `atlas.shared.Holding` are NOT drop-in replacements — different container field names (`.holdings` vs `.positions`) and no JSON loading methods. Migrating to them would require changing all 4 engines that access `.positions` directly, plus moving JSON loading out of the types entirely.
- Single-sprint completion avoids a "shim sprint" (move + keep stale re-export) that would need its own guardrail tests.
- `PortfolioPosition` has zero production runtime callers outside `portfolio.py` itself — it can only move alongside `Portfolio`.

**Outcome:** Caller map documented. Sprint 134 guardrail tests added. 1352 tests passing (3 skipped). Demo passed. RC2 green.

---

**Sprint 138 (2026-07-02): Analysis package checkpoint**

**Decision:** Audit-only sprint. No deletions, no migrations. Document the current `atlas/analysis/` state now that the portfolio migration is fully resolved.

**Findings:**
- 13 modules remain. Portfolio migration has reduced the package from 17 modules (Sprint 108) to 13.
- `engine.py` (foundational) — 11 production callers (`conversation`, `decision/*`, `intelligence`, `monitoring`, `reasoning`, `suitability`, `models`, `adapters`). Do not touch until a Blueprint replacement exists.
- `scores.py` (shared utility, 2 lines) — 10 production callers across 7 packages. Do not move without a broad refactor.
- `company_analysis.py`, `explanation.py`, `report.py` — active modules, no cleanup needed.
- 7 placeholder submodules (`growth`, `macro`, `moat`, `quality`, `sentiment`, `technicals`, `valuation`): each 18 lines, structurally identical, zero external production callers. Only imported by `company_analysis.py`. Sprint 139 consolidation target.
- `atlas/analysis/__init__.py`: 12 active exports, no stale symbols. `Portfolio` and `PortfolioPosition` confirmed absent.
- `atlas/capabilities/company_analysis/` exists but uses an entirely different model (`CompanyAnalysisReport`) — not a replacement for the legacy analysis layer.
- No Atlas Edge naming encountered.

**Sprint 139 target:** Consolidate the 7 identical-pattern placeholder submodules into `company_analysis.py` and delete the 7 files.

**Outcome:** Docs updated. No runtime changes. 1359 tests passing (3 skipped). Demo passed. RC2 green.

---

**Sprint 137 (2026-07-02): Delete `portfolio_fit_input_from_profile` identity adapter**

**Decision:** Remove the no-op identity function and update the 4 engine callers to call `provider.get_portfolio_profile()` directly.

**Rationale:**
- `portfolio_fit_input_from_profile(profile: PortfolioFitInput) -> PortfolioFitInput` was a pure identity (`return profile`) — adding it to the call chain had zero effect on runtime behavior.
- Sprint 133 retained it to avoid touching 4 engine callers; Sprint 135 and 136 confirmed the adapter boundary is stable enough to make the cleanup safe.
- Removing it makes the provider contract explicit in each engine: `fit_input = provider.get_portfolio_profile(ticker)`.

**Outcome:** `portfolio_fit_input_from_profile` deleted. 4 production files updated. 9 test functions updated. `atlas/adapters/portfolio.py` now contains only meaningful portfolio boundary utilities. 1359 tests passing (3 skipped). Demo passed. RC2 green. Portfolio migration fully resolved.

---

**Sprint 136 (2026-07-02): Post-portfolio migration checkpoint**

**Decision:** No code changes to runtime behavior. Verified architecture post-Sprint 135 deletion.

**Findings:**
- Zero active production imports of `atlas.analysis.portfolio` (AST-confirmed).
- `atlas.analysis.__init__` exports no Portfolio/PortfolioPosition symbols.
- `atlas/adapters/portfolio.py` is self-contained: no CLI, provider, or deleted-module imports.
- All 5 deleted portfolio symbols (PortfolioIntelligenceEngine, PortfolioAnalysis, PortfolioSignal, PortfolioRecommendation, CompanyPortfolioProfile) absent from adapter.
- `atlas/analysis/` inventory: 13 modules. No migration candidates identified for immediate deletion.
- `portfolio_fit_input_from_profile` is a no-op identity function still called by 4 engines (conversation, dashboard, intelligence, decision) — deferred from Sprint 133.

**Sprint 137 target:** Remove `portfolio_fit_input_from_profile` identity adapter from 4 engine callers and delete the function. It is a no-op added in Sprint 133 to avoid touching callers; those callers can now call provider methods directly.

**Outcome:** 4 guardrail tests added. Stale tracking text updated. 1365 tests passing (3 skipped). Demo passed. RC2 green.

---

**Sprint 135 (2026-07-02): Delete `atlas/analysis/portfolio.py`; move types to `atlas/adapters/portfolio.py`**

**Decision:** "Lift and shift" — `Portfolio`, `PortfolioPosition`, `_position_from_mapping`, `_normalize_weight` moved from `atlas/analysis/portfolio.py` into `atlas/adapters/portfolio.py`. `atlas/analysis/portfolio.py` deleted. All 12 production import sites updated atomically in the same sprint.

**Rationale:**
- `atlas/adapters/portfolio.py` is the correct destination: already the legacy compatibility boundary; making it self-contained removes the only remaining coupling back into `atlas/analysis/`.
- Doing the file deletion and all caller updates in one sprint avoids a partial-migration window where two modules each claim ownership.
- No runtime behavior changed: `Portfolio.from_mapping`, `from_json_file`, field access all identical.

**Outcome:** `atlas/analysis/portfolio.py` deleted. `atlas/analysis/` now contains only active modules: `engine.py`, `explanation.py`, `report.py`, `scores.py`, `providers.py`. Sprint 135 guardrail block added to `test_portfolio_analyze_deprecation.py`. Stale "is importable" assertions flipped in 5 test files. 1361 tests passing (3 skipped). Demo passed. RC2 green.

---

**Sprint 133 (2026-07-02): Delete `CompanyPortfolioProfile`; migrate providers to `PortfolioFitInput`**

**Decision:** Option A (thin identity adapter). Updated `CompanyDataProvider.get_portfolio_profile()` return type across all 3 provider files to `PortfolioFitInput`. Changed `portfolio_fit_input_from_profile` to identity function rather than removing it — avoids touching 4 engine callers (conversation, dashboard, intelligence, decision) and their tests.

**Rationale:**
- `CompanyPortfolioProfile` and `PortfolioFitInput` have identical fields (1-to-1 mapping), making the provider switch mechanical with no data loss.
- Option A (identity adapter) minimizes blast radius vs Option B (remove adapter and update engine callers): 4 engine files + their tests left untouched. Adapter cleanup deferred to a future sprint.
- Zero active production callers remained after providers were updated — deletion confirmed safe.

**Outcome:** `portfolio.py` reduced to 59 lines — only `Portfolio` and `PortfolioPosition` remain. All portfolio intelligence types now live in `atlas/capabilities/portfolio_intelligence/`. 1352 tests passing (3 skipped). Demo passed. RC2 green.

---

**Sprint 119 (2026-07-02): Migrate risk drift portfolio dependency**

**Decision:** Two-part migration. (1) `Portfolio`: TYPE_CHECKING guard only — duck-typed `.positions` access preserved because CLI and portfolio_review both pass legacy Portfolio; changing callers is out of scope. (2) `PortfolioAnalysis`: fully replaced by `PortfolioFitResult` from capabilities — this was dead code (no caller passes non-None), making it a safe forward migration.

**Rationale:**
- `_current_largest_weight` accesses `portfolio.positions` — this is duck-typed and continues to work for legacy Portfolio passed by callers. Moving `Portfolio` behind TYPE_CHECKING removes the runtime import without breaking anything.
- `current_portfolio_analysis: PortfolioAnalysis | None` was always None at runtime. Replacing with `PortfolioFitResult | None` is forward-aligned: future callers can pass `PortfolioFitResult` directly from the capability engine, enabling richer concentration context.
- `.overlap_with_existing_holdings.score` → `.overlap.score` because `PortfolioFitResult` uses `overlap` as the field name (per models.py mapping).

**Outcome:** 2 files changed (engine + test). 9 new tests. 1254 tests passing (3 skipped). Demo passed. RC2 green. Recommended Sprint 120: `atlas/suitability/engine.py`.
