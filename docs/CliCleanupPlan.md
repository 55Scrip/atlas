# Atlas CLI Deprecated Command Registry Cleanup Plan

**Created:** 2026-07-03 (Sprint 173)  
**Updated:** 2026-07-03 (Sprint 174)  
**Status:** CLOSED — Sprint 174 removed the 3 empty shell CLI app groups (`evidence`, `reason`, `risk`) from `atlas/cli/main.py`. No further `atlas/cli/` cleanup work is planned until new stale commands, broken active commands, or provider-boundary issues emerge.

---

## Background

Sprint 173 audits the CLI deprecated command registry and active command surface. This is the first formal audit of `atlas/cli/` after 14 cleanup track closures.

`atlas/cli/` contains 3 files:

| File | Lines | Category |
|---|---|---|
| `__init__.py` | 0 | Empty package marker |
| `deprecations.py` | 205 | Deprecated/retired command registry + public API |
| `main.py` | 1497 | All active command handlers + sub-app registrations + helpers |

---

## Deprecated Command Registry Inventory

### `_REGISTRY` (active deprecated commands)

**Empty.** As of Sprint 91, all deprecated commands were retired. `_REGISTRY = ()`.

`_BY_COMMAND`, `deprecated_command_message()`, `all_deprecated_commands()`, and `get_deprecated_command()` are all functional but return empty results — correct behavior.

### `_RETIRED_REGISTRY` (historical record, 7 entries)

| Command | Retired Sprint | Legacy Module | Replacement |
|---|---|---|---|
| `atlas daily brief` | Sprint 85 | `atlas.daily_brief` (deleted Sprint 77) | `atlas daily summary` |
| `atlas evidence assess` | Sprint 86 | `atlas.evidence` (still on disk) | None (consolidated) |
| `atlas reason analyze` | Sprint 87 | `atlas.reasoning` (deleted Sprint 153) | None (consolidated) |
| `atlas risk size` | Sprint 88 | `atlas.risk` (still on disk) | None (consolidated) |
| `atlas portfolio analyze` | Sprint 89 | `atlas.adapters.portfolio` (migrated Sprint 135) | `atlas portfolio summary` |
| `atlas portfolio review` | Sprint 90 | `atlas.portfolio_review` (still on disk) | `atlas portfolio summary` |
| `atlas watchlist analyze` | Sprint 91 | `atlas.analysis.watchlist` (deleted Sprint 101) | `atlas watchlist intelligence` |

### `DeprecatedCommand` dataclass

| Field | Purpose | Used at runtime? |
|---|---|---|
| `command` | CLI invocation string | `_BY_COMMAND` index key |
| `message` | Rich-formatted user message | `deprecated_command_message()` — only called if command is in `_REGISTRY` |
| `replacement_command` | Blueprint-aligned replacement | Documentation only |
| `consolidation_direction` | Where work is going | Documentation only |
| `legacy_module` | Module behind this command | Documentation only |
| `removal_criteria` | Conditions for deletion | Documentation only |

Since `_REGISTRY` is empty, `deprecated_command_message()` is never called at runtime. The entire `_RETIRED_REGISTRY` is documentation metadata only.

---

## Retirement Metadata Accuracy Review

Each `removal_criteria` tuple reviewed against repository reality after 14 cleanup closures:

### `atlas daily brief`
```
"atlas.daily_brief engine was deleted in Sprint 77."
"Command body retired in Sprint 85 — no remaining dependency."
```
**Accurate.** `atlas.daily_brief` confirmed deleted. ✓

### `atlas evidence assess`
```
"Command body retired in Sprint 86."
"atlas.evidence engine remains on disk — still used by atlas/comparison,
 atlas/decision_journal, and atlas/watchlist_review."
```
**Accurate.** Verified Sprint 173: `atlas/comparison/engine.py`, `atlas/decision_journal/engine.py`, and `atlas/watchlist_review/engine.py` all import from `atlas.evidence`. Engine deletion still correctly deferred. ✓

### `atlas reason analyze`
```
"Command body retired in Sprint 87."
"check_reasoning_report() removed from atlas/principles/engine.py in Sprint 152."
"atlas/reasoning/ package deleted in Sprint 153. No legacy module remains."
```
**Accurate.** `atlas/reasoning/` confirmed deleted Sprint 153. `check_reasoning_report` confirmed absent. ✓

### `atlas risk size`
```
"Command body retired in Sprint 88."
"atlas.risk engine remains on disk — RiskAnalysis type is still imported by
 atlas/conversation and atlas/intelligence engines (atlas/reasoning deleted Sprint 153)."
```
**Accurate.** Verified Sprint 173: `atlas/conversation/engine.py` and `atlas/intelligence/engine.py` both import `RiskAnalysis` from `atlas.risk`. Deferral rationale still holds. ✓

### `atlas portfolio analyze`
```
"Command body retired in Sprint 89."
"atlas.analysis.portfolio deleted Sprint 135. Portfolio and PortfolioPosition now
 live in atlas/adapters/portfolio.py. All 12 production import sites migrated."
```
**Accurate.** `atlas.analysis.portfolio` confirmed absent. ✓

### `atlas portfolio review`
```
"Command body retired in Sprint 90."
"atlas.portfolio_review engine remains on disk — PortfolioReviewEngine is still
 imported and instantiated by atlas/home/engine.py (AtlasHomeEngine)."
```
**Accurate.** Verified Sprint 173: `atlas/home/engine.py` imports and instantiates `PortfolioReviewEngine` from `atlas.portfolio_review`. Deferral rationale still holds. ✓

### `atlas watchlist analyze`
```
"Command body retired in Sprint 91."
"WatchlistEngine deleted Sprint 99. atlas/analysis/watchlist.py fully deleted Sprint 101."
```
**Accurate.** `atlas.analysis.watchlist` confirmed absent. ✓

**Finding: All 7 `removal_criteria` entries are accurate as of Sprint 173. No stale metadata found.**

---

## Retired Command Callability Review

`reason_app`, `risk_app`, and `evidence_app` sub-apps are registered with `app.add_typer()` (lines 145, 154, 157) but have **zero `@*_app.command()` decorators** — confirmed by grep returning no results. These app groups are empty shells: they appear in the app namespace but expose no callable commands.

| Retired Command | `_RETIRED_REGISTRY` entry | Active handler in `main.py`? | Callable? |
|---|---|---|---|
| `atlas daily brief` | ✓ | No | **No** ✓ |
| `atlas evidence assess` | ✓ | No | **No** ✓ |
| `atlas reason analyze` | ✓ | No | **No** ✓ |
| `atlas risk size` | ✓ | No | **No** ✓ |
| `atlas portfolio analyze` | ✓ | No | **No** ✓ |
| `atlas portfolio review` | ✓ | No | **No** ✓ |
| `atlas watchlist analyze` | ✓ | No | **No** ✓ |

**No retired command is accidentally callable.** ✓

**Notable:** `evidence_app`, `reason_app`, and `risk_app` are registered as typer sub-apps but contain zero commands. These empty shells are harmless — they result in an empty `atlas evidence`, `atlas reason`, and `atlas risk` command group with no subcommands. They are the residual scaffolding from retired commands and are candidates for removal in a future sprint.

---

## Active Command Surface Review

| Command | Handler | Key imports | Provider-coupled? | Closed-track dep? |
|---|---|---|---|---|
| `atlas init` | `init()` | `init_database` | No | No |
| `atlas add-company` | `add_company_command()` | `atlas.services.company_service` | No | No |
| `atlas list-companies` | `list_companies_command()` | `atlas.services.company_service` | No | No |
| `atlas report` | `report_command()` | `atlas.analysis.report` | Yes (mock default) | No — `atlas.analysis.report` is distinct active module, not closed-track |
| `atlas monitor` | `monitor_command()` | `atlas.monitoring`, `atlas.providers` | Yes (mock default) | No |
| `atlas import-financials` | `import_financials_command()` | `atlas.services.financial_import_service` | No | No |
| `atlas analyze` | `analyze_command()` | `atlas.capabilities.company_analysis` | Yes (mock default) | No |
| `atlas ask` | `ask_command()` | `atlas.conversation` | Yes (mock default) | No |
| `atlas home` | `home_command()` | `atlas.home` | Yes (mock default) | No |
| `atlas compare` | `compare_command()` | `atlas.comparison` | Yes (mock default) | No |
| `atlas dashboard show` | `dashboard_show_command()` | `atlas.dashboard` | Yes (mock default) | No |
| `atlas daily summary` | `daily_summary_command()` | `atlas.capabilities.daily_brief` | Yes (mock default) | No |
| `atlas economics analyze` | `economics_analyze_command()` | `atlas.economics` | No | No |
| `atlas intelligence analyze` | `intelligence_analyze_command()` | `atlas.intelligence` | Yes (mock default) | No |
| `atlas journal create/list/review` | 3 handlers | `atlas.decision_journal` | No | No |
| `atlas language explain` | `language_explain_command()` | `atlas.language` | No | No |
| `atlas memory save/show/compare` | 3 handlers | `atlas.decision.memory` | Partial (save uses mock) | No |
| `atlas market analyze/health` | 2 handlers | `atlas.market` | No | No |
| `atlas portfolio summary` | `portfolio_summary_command()` | `atlas.adapters.portfolio`, `atlas.domains.portfolio` | No | No |
| `atlas profile create/show/update` | 3 handlers | `atlas.profile` | No | No |
| `atlas principles check` | `principles_check_command()` | `atlas.principles` | No | No |
| `atlas risk-drift analyze` | `risk_drift_analyze_command()` | `atlas.risk_drift` | No | No |
| `atlas suitability analyze` | `suitability_analyze_command()` | `atlas.suitability` | Yes (mock default) | No |
| `atlas theme analyze` | `theme_analyze_command()` | `atlas.themes` | No | No |
| `atlas watchlist intelligence` | `watchlist_intelligence_command()` | `atlas.capabilities.watchlist_intelligence` | Yes (mock default) | No |
| `atlas watchlist review` | `watchlist_review_command()` | `atlas.watchlist_review` | Yes (mock default) | No |
| `atlas discovery export` | `discovery_export_command()` | `atlas.capabilities.discovery` | Yes (mock default) | No |
| `atlas research export` | `research_export_command()` | `atlas.capabilities.daily_brief` | No | No |
| `atlas company-analysis export/merge` | 2 handlers | `atlas.capabilities.company_analysis` | No | No |

**No active command depends on a deleted or closed-track module.**

`atlas.analysis.report` (imported by `atlas report`) is confirmed importable and is a distinct active module under `atlas/analysis/` — not one of the deleted analysis submodules.

---

## Provider Selection Review

`_provider_from_name()` at `main.py:1344`:
```python
def _provider_from_name(provider_name: str) -> CompanyDataProvider:
    normalized = provider_name.strip().lower()
    if normalized == "mock": return MockCompanyAnalysisProvider()
    if normalized == "yahoo": return YahooFinanceProvider()
```

| Detail | Value |
|---|---|
| Default provider flag | `--provider mock` (all provider-coupled commands) |
| Opt-in Yahoo path | `--provider yahoo` (explicit flag only) |
| Provider import location | `atlas/cli/main.py:100` only — correct, CLI-layer only |
| Commands with `--provider` | `report`, `monitor`, `analyze`, `ask`, `home`, `compare`, `dashboard show`, `intelligence analyze`, `suitability analyze`, `watchlist review`, `watchlist intelligence` |
| `memory save` | Uses `MockCompanyAnalysisProvider()` directly (line 576) — no flag, hardcoded mock |
| Network access | Yahoo path only, never default, never in demo or RC verification |

**Provider boundary unchanged and correct.** ✓

---

## Stale Reference Audit (CLI-focused)

All stale-symbol hits in `atlas/cli/` are in `deprecations.py` retirement metadata strings:

| Reference | Location | Classification |
|---|---|---|
| `atlas.reasoning` | `deprecations.py:91` `legacy_module` field | **Retired command metadata** — accurate (deleted Sprint 153) |
| `check_reasoning_report()` | `deprecations.py:94` `removal_criteria` | **Retired command metadata** — accurate (removed Sprint 152) |
| `atlas.analysis.portfolio` | `deprecations.py:129` `removal_criteria` | **Retired command metadata** — accurate (deleted Sprint 135) |
| `atlas.analysis.watchlist` | `deprecations.py:162` `legacy_module` field | **Retired command metadata** — accurate (deleted Sprint 101) |

**No stale active production references found in `atlas/cli/`.** ✓

---

## Command-to-Package Map

| CLI Group | Active Package | Direction | Provider-coupled | Recently closed track? |
|---|---|---|---|---|
| `atlas analyze` | `atlas.capabilities.company_analysis` | CLI → Capability | Yes (mock default) | No |
| `atlas ask` | `atlas.conversation` | CLI → Legacy engine | Yes (mock default) | CLOSED Sprint 167 — still active ✓ |
| `atlas home` | `atlas.home` | CLI → Legacy engine | Yes (mock default) | CLOSED Sprint 162 — still active ✓ |
| `atlas compare` | `atlas.comparison` | CLI → Legacy engine | Yes (mock default) | CLOSED Sprint 160 — still active ✓ |
| `atlas dashboard show` | `atlas.dashboard` | CLI → Legacy engine | Yes (type annotation only) | CLOSED Sprint 169 — still active ✓ |
| `atlas daily summary` | `atlas.capabilities.daily_brief` | CLI → Capability | Yes (mock default) | No |
| `atlas intelligence analyze` | `atlas.intelligence` | CLI → Legacy engine | Yes (mock default) | CLOSED Sprint 165 — still active ✓ |
| `atlas principles check` | `atlas.principles` | CLI → Legacy engine | No | CLOSED Sprint 158 — still active ✓ |
| `atlas portfolio summary` | `atlas.adapters.portfolio`, `atlas.domains.portfolio` | CLI → Adapter + Domain | No | Portfolio boundary CLOSED Sprint 148 — still active ✓ |
| `atlas risk-drift analyze` | `atlas.risk_drift` | CLI → Engine | No | No |
| `atlas suitability analyze` | `atlas.suitability` | CLI → Engine | Yes (mock default) | No |
| `atlas watchlist intelligence` | `atlas.capabilities.watchlist_intelligence` | CLI → Capability | Yes (mock default) | No |
| `atlas watchlist review` | `atlas.watchlist_review` | CLI → Engine | Yes (mock default) | No |
| `atlas report` | `atlas.analysis.report` | CLI → Legacy module | Yes (mock default) | No — distinct active module |
| `atlas memory *` | `atlas.decision.memory` | CLI → Engine module | Partial | No |
| `atlas journal *` | `atlas.decision_journal` | CLI → Engine | No | No |
| `atlas economics analyze` | `atlas.economics` | CLI → Engine | No | No |
| `atlas market *` | `atlas.market` | CLI → Types/Engine | No | No |
| `atlas theme analyze` | `atlas.themes` | CLI → Engine | No | No |
| `atlas discovery export` | `atlas.capabilities.discovery` | CLI → Capability | Yes (mock default) | No |

All closed-track packages that still have active CLI commands (home, compare, intelligence, conversation, dashboard, principles) are confirmed active and intentional. Their cleanup tracks closed because no cleanup was warranted — the engines remain the correct runtime implementation.

---

## Test Coverage Review

| Test File | Lines | Coverage Area |
|---|---|---|
| `test_deprecation_registry.py` | 291 | Registry completeness, message content rules, no engine imports, `_REGISTRY` empty |
| `test_reason_analyze_deprecation.py` | 144 | `atlas reason analyze` retired, `atlas.reasoning` deleted |
| `test_risk_size_deprecation.py` | 145 | `atlas risk size` retired, `RiskAnalysis` callers still accurate |
| `test_evidence_assess_deprecation.py` | 125 | `atlas evidence assess` retired, evidence engine still active |
| `test_daily_brief_deprecation.py` | 100 | `atlas daily brief` retired, `atlas daily summary` active |
| `test_portfolio_analyze_deprecation.py` | 550 | `atlas portfolio analyze` retired, Blueprint migration complete |
| `test_portfolio_review_deprecation.py` | 158 | `atlas portfolio review` retired, `portfolio_review` engine still on disk |
| `test_watchlist_analyze_deprecation.py` | 579 | `atlas watchlist analyze` retired, watchlist capability active |
| `test_provider_cli.py` | — | Provider selection behavior |
| `test_analyze_cli.py` | — | `atlas analyze` command |
| `test_rc_checkpoint_sprint163.py` | — | Sprint 163 RC guardrails (7 retired commands present) |

**Coverage is comprehensive.** All 7 retired commands have individual test files. The main registry completeness test (`test_deprecation_registry.py`) covers `_REGISTRY` empty state and `_RETIRED_REGISTRY` completeness.

**Gap identified (minor):** No dedicated Sprint 172/173 guardrail confirms the empty-shell app groups (`evidence_app`, `reason_app`, `risk_app`) have zero registered commands. This is low-risk — the typer framework enforces it — but could be documented.

---

## Cleanup Candidate Classification

| Candidate | Evidence | Risk | Sprint 174? |
|---|---|---|---|
| Empty shell app groups: `evidence_app`, `reason_app`, `risk_app` registered with `app.add_typer()` but zero commands | Three `app.add_typer()` registrations (lines 145, 154, 157) expose empty CLI groups. Running `atlas evidence --help`, `atlas reason --help`, `atlas risk --help` shows an empty command group with no subcommands. Confusing to users. | LOW — removing `add_typer()` calls and the app declarations (6 lines each) has zero runtime behavior change | **Yes — Sprint 174** |
| `_REGISTRY` public API (`deprecated_command_message`, `all_deprecated_commands`, `get_deprecated_command`) never called | `_REGISTRY` is empty; these functions are callable but never invoked in active production code | LOW — safe to leave; they are correct public API stubs | Leave unchanged (documented API) |
| Stale retirement metadata doc comments | All 7 entries verified accurate as of Sprint 173 | None | Leave unchanged |

**Primary cleanup candidate:** The three empty app-group registrations. Removing them is a 6-line change per group (app declaration + `app.add_typer()` call) with zero behavioral impact and real user-facing benefit (cleaner `atlas --help` output).

---

## Final Stable CLI State (Sprint 173)

| Area | Status |
|---|---|
| `_REGISTRY` | Empty — all deprecated commands retired Sprint 91 ✓ |
| `_RETIRED_REGISTRY` | 7 entries — all metadata accurate as of Sprint 173 ✓ |
| Retired command callability | Zero retired commands callable ✓ |
| Empty shell app groups | `evidence_app`, `reason_app`, `risk_app` registered but empty — Sprint 174 candidate |
| Active command count | ~30 commands across ~20 groups — all active and intentional ✓ |
| Provider boundary | `_provider_from_name()` in CLI only; default mock; Yahoo opt-in only ✓ |
| Stale closed-track imports | None in active production CLI code ✓ |
| No deleted-module imports | Confirmed ✓ |

---

## Recommended Sprint 174 Target

**Remove empty shell CLI app groups (`evidence_app`, `reason_app`, `risk_app`).**

Three sub-app groups are declared and registered in `atlas/cli/main.py` but contain zero commands:
- `evidence_app` (line 124) registered as `name="evidence"` (line 145)
- `reason_app` (line 133) registered as `name="reason"` (line 154)
- `risk_app` (line 136) registered as `name="risk"` (line 157)

These are residual scaffolding from the retired commands `atlas evidence assess`, `atlas reason analyze`, and `atlas risk size`. Running `atlas evidence --help` shows an empty group — confusing to users and inconsistent with the clean CLI surface.

Removing them is:
- 3 app declaration lines removed
- 3 `app.add_typer()` call lines removed
- Zero behavioral change (the commands were already not callable)
- User-facing improvement (cleaner `atlas --help` output)

After removing empty shells: close the CLI cleanup track. This closes a 15th cleanup track.

---

## Sprint 174 — Track Closure (COMPLETED)

**CLI cleanup track is CLOSED as of Sprint 174.**

Sprint 174 actions:
- Removed `evidence_app` declaration and `app.add_typer(evidence_app, name="evidence")` from `atlas/cli/main.py` ✓
- Removed `reason_app` declaration and `app.add_typer(reason_app, name="reason")` from `atlas/cli/main.py` ✓
- Removed `risk_app` declaration and `app.add_typer(risk_app, name="risk")` from `atlas/cli/main.py` ✓

Sprint 174 verified:
- `atlas --help` no longer shows `evidence`, `reason`, or `risk` groups ✓
- All active groups remain: intelligence, dashboard, principles, risk-drift, watchlist, daily, portfolio, and all others ✓
- All 7 retired commands remain not callable ✓
- `_RETIRED_REGISTRY` unchanged — 7 entries, all accurate ✓
- `_REGISTRY` remains empty ✓
- Provider boundary unchanged ✓
- 1536 tests passed, 3 skipped ✓

**Closure rationale:** The 3 empty groups were residual scaffolding from retired commands. They exposed no callable commands and only cluttered `atlas --help`. Removing them improves CLI clarity without changing any active or retired command behavior.

**Reopening condition:** If a new `atlas evidence`, `atlas reason`, or `atlas risk` command group is introduced, or if any other CLI command or group becomes stale.

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
| Conversation package | CLOSED Sprint 167 |
| Dashboard package | CLOSED Sprint 169 |
| Portfolio intelligence capability | CLOSED Sprint 171 |
| **CLI deprecated command registry** | **CLOSED Sprint 174** |

---

## Recommended Sprint 175 Target

**Release candidate checkpoint after 15 closed tracks.**

After closing the CLI cleanup track and modifying the root CLI help surface, Atlas should run an RC checkpoint before starting another broad package audit. Pattern matches Sprint 163 (after 10 tracks) and Sprint 172 (after 14 tracks).
