# Architecture Consolidation (Sprint 44, updated Sprint 67, reviewed Sprint 71)

This document records the current state of Atlas architecture as of RC2 (Sprint 71),
clarifies which layers are current vs. legacy, and defines guardrails for
future sprints. It does not change runtime behavior.

Architecture is unchanged from RC1. RC2 verification (Sprint 71) confirmed no
new legacy patterns were introduced in Sprints 69–70. The Blueprint-aligned
adapter layer (`atlas/adapters/watchlist.py`) was extended to support knowledge
fact distribution — consistent with existing adapter patterns.

## Current Layers

Atlas currently has two parallel layers that have not yet been merged:

### 1. Blueprint-aligned layer (current architecture)

- `atlas/domains/` — owns canonical concepts and contracts: `portfolio`,
  `watchlist`, `research`, `decision`, `decision_journal`, `daily_brief`,
  `knowledge`, `ai`, `authentication`. Domains depend only on
  `atlas.shared` entities.
- `atlas/capabilities/` — composes domains into product-level, deterministic
  reasoning: `company_analysis`, `discovery`, `watchlist_intelligence`.
  Capabilities depend on domains, not on providers or legacy engines.
- `atlas/shared/` — canonical, immutable entities (`Portfolio`, `Holding`,
  `Company`, `Watchlist`, `ResearchNote`, `JournalEntry`, `User`,
  `MarketEvent`, `Decision`, `KnowledgeNode`).

This is the architecture all new product work should build on.

### 2. Legacy / engine layer (compatibility, not for expansion)

Modules such as `atlas/analysis/`, `atlas/portfolio_review/`,
`atlas/watchlist_review/`, `atlas/comparison/`, `atlas/conversation/`,
`atlas/dashboard/`, `atlas/daily/`, `atlas/decision_journal/` (top-level),
`atlas/economics/`, `atlas/evidence/`, `atlas/home/`, `atlas/intelligence/`,
`atlas/language/`, `atlas/market/`, `atlas/memory/`, `atlas/monitoring/`,
`atlas/principles/`, `atlas/profile/`, `atlas/reasoning/`, `atlas/risk/`,
`atlas/risk_drift/`, `atlas/suitability/`, `atlas/themes/`, `atlas/database/`,
`atlas/services/`, `atlas/models/` are the original working engines that
predate the domain/capability split. They remain functional and fully
tested, and the CLI currently calls them exclusively.

These modules are compatibility layers. They should not gain new
responsibilities; new product capabilities belong in
`atlas/domains`/`atlas/capabilities`.

### 3. Provider layer

`atlas/providers/` defines `CompanyDataProvider` (interface),
`MockCompanyAnalysisProvider` (default, no network access), and
`YahooFinanceProvider` (live HTTP calls via `urllib.request.urlopen`,
`atlas/providers/yahoo.py`).

### 4. CLI / runtime layer

`atlas/cli/main.py` is the Typer entry point (`atlas` console script). As of
Sprint 44, every CLI command imported exclusively from the legacy engine
layer and `atlas.services`, with nothing wired to `atlas.domains` or
`atlas.capabilities`.

**Sprint 45 update:** `atlas portfolio summary <portfolio.json>` is the
first CLI command that calls `atlas.domains.portfolio` (via the new
`atlas.adapters.portfolio` bridge described below). It is read-only,
additive, and does not call providers or external APIs. The two pre-existing
portfolio commands (`atlas portfolio analyze`, `atlas portfolio review`)
were left untouched — they answer different questions (ticker-fit analysis,
CIO-style review with profile/market dependencies) that do not map cleanly
onto the Portfolio Domain's allocation/concentration/validation scope, so
migrating them was judged unsafe for this sprint. All other CLI commands
still call the legacy engine layer exclusively.

**Sprint 46 update:** `atlas portfolio analyze <portfolio.json> TICKER` now
also calls `atlas.domains.portfolio` via the same adapter, appending a
"Portfolio Summary (Portfolio Domain)" section after its existing,
unchanged `PortfolioAnalysis` output. **Sprint 47 update:** the same
pattern was applied identically to `atlas portfolio review`, completing
domain coverage for all three `portfolio` subcommands. The command's proprietary fit-scoring
logic (diversification impact, sector/country/market-cap concentration
impact, overlap, expected quality/risk impact, the `Strong Add`/`Add`/
`Neutral`/`Reduce`/`Avoid` recommendation) was **not** migrated and remains
on `atlas.analysis.portfolio.PortfolioIntelligenceEngine` unchanged — it
answers "how well would this new ticker fit the portfolio", a question the
Portfolio Domain does not (and should not) attempt to answer, since the
domain is about understanding existing portfolio structure, not scoring
hypothetical additions. `atlas portfolio review` remains entirely legacy
and out of scope for this sprint.

### 5. Adapter layer

`atlas/adapters/` is the one layer permitted to import both the legacy
engine layer and `atlas.domains`/`atlas.shared`. Adapters translate legacy
runtime data shapes into domain entities. They must stay deterministic,
must not call external APIs, and must not mutate persisted data. Domains
must never import adapters back (enforced by
`tests/test_architecture_boundaries.py`), keeping the dependency direction
one-way: legacy/CLI -> adapters -> domains.

`atlas.adapters.portfolio.legacy_portfolio_to_domain_portfolio` translates
the legacy CLI portfolio JSON (positions with a relative `weight`, no
absolute market value) into `atlas.shared.Portfolio`/`Holding` entities,
using each position's `weight` as a stand-in `market_value`. This preserves
all relative domain calculations (allocation, concentration, top holdings)
exactly, but does not produce a meaningful absolute currency total — that
limitation is documented in the adapter module itself.

## Known Duplication

- Portfolio reasoning exists both as `atlas.analysis.portfolio` (legacy,
  CLI-wired) and `atlas.domains.portfolio` (Blueprint-aligned, not
  CLI-wired).
- Decision/decision-journal logic exists both as top-level
  `atlas/decision/`, `atlas/decision_journal/` (legacy, CLI-wired) and
  `atlas.domains.decision`, `atlas.domains.decision_journal`
  (Blueprint-aligned, not CLI-wired).
- Watchlist reasoning exists both as `atlas.analysis.watchlist` /
  `atlas.watchlist_review` (legacy, CLI-wired) and `atlas.domains.watchlist`
  / `atlas.capabilities.watchlist_intelligence` (Blueprint-aligned, not
  CLI-wired).

This duplication is expected during a deliberate migration and is not itself
a defect. It becomes a defect if the legacy layer keeps growing instead of
shrinking.

## Migration Path

1. Pick one duplicated concern at a time (e.g. portfolio).
2. Migrate the corresponding CLI command(s) to call the
   `atlas.domains`/`atlas.capabilities` structures instead of the legacy
   module. If the legacy and domain data shapes differ, add a small,
   deterministic adapter under `atlas/adapters/` rather than reshaping the
   domain to fit legacy assumptions.
3. Add tests proving behavioral parity with the legacy command before
   removing the legacy call site. If a legacy command has no equivalent
   domain computation (different question, different inputs), prefer adding
   a new, additive read-only command over forcing parity — see Sprint 45's
   `atlas portfolio summary`.
4. Only delete legacy code once nothing references it and parity is proven.
5. Repeat per concern. Do not attempt a single big-bang rewrite.

**Sprint 45 status:** portfolio summary/allocation/concentration reporting
now has a proven bridge (`atlas portfolio summary`) from legacy JSON input
to `atlas.domains.portfolio`. `atlas portfolio analyze` and
`atlas portfolio review` remain fully legacy and are the next candidates,
but require either extending the Portfolio Domain (ticker-fit analysis,
CIO review) or a larger adapter — out of scope for a narrow sprint.

**Sprint 46 status:** `atlas portfolio analyze` now surfaces Portfolio
Domain context (allocation, concentration, cash weight, top holdings)
alongside its unchanged legacy fit-score output, reusing the Sprint 45
adapter unmodified. `atlas portfolio review` remains the only fully-legacy
portfolio command and is the next candidate; it depends on investor profile
and optional market snapshot data that have no Portfolio Domain equivalent
yet, so migrating it will likely require either a profile/market domain or
a narrower additive approach similar to this sprint's.

**Sprint 47 status:** `atlas portfolio review` now appends the same
"Portfolio Summary (Portfolio Domain)" section introduced in Sprints 45 and
46. All three `portfolio` CLI commands (`summary`, `analyze`, `review`) now
surface Portfolio Domain calculations for allocation, concentration, cash
weight, and top holdings. The legacy review engine (investor profile,
suitability, risk drift, themes, market context, economics, monitoring,
principles) was not touched and remains fully intact. All portfolio CLI
commands now exercise `atlas.domains.portfolio` via the Sprint 45 adapter,
which required no changes in Sprints 46 or 47.

## Capabilities (Sprint 48–49 update)

`atlas/capabilities/daily_brief/` is the fourth Blueprint-aligned capability
alongside `company_analysis`, `watchlist_intelligence`, and `discovery`.

**Sprint 48** introduced the capability with a `DailyBriefCapability.generate()`
method and a new `atlas daily summary` CLI command. The `--portfolio` flag was
the only CLI-wired input.

**Sprint 49** added `atlas/capabilities/daily_brief/input_builder.py`, a typed
builder (`build_daily_brief_input`) that correctly transforms all five supported
input types into `DailyBriefInput`. The engine's attribute-name mismatches
against real Atlas types were also fixed. 392 tests pass; 39 new tests cover
the builder and each integration target end-to-end.

**Sprint 50** added `atlas/capabilities/daily_brief/json_loader.py` and extended
`atlas daily summary` with four new CLI flags: `--research`, `--watchlist`,
`--discovery`, and `--company-analysis`. Each flag accepts a local JSON file,
parses it into a lightweight structured type, feeds it through the Sprint 49
input builder, and generates a deterministic Daily Brief report. No network
calls are made. 433 tests pass; 41 new tests cover all new CLI flags, error
handling, multi-flag composition, language safety, and no-network constraints.

**Sprint 51** added `atlas/capabilities/watchlist_intelligence/exporter.py`,
`atlas/capabilities/discovery/exporter.py`, a new `atlas watchlist intelligence
[--output FILE]` command under the existing `watchlist` subapp, and a new
`atlas discovery export [--output FILE]` command under a new `discovery`
subapp. Both export commands produce JSON compatible with the Sprint 50 Daily
Brief input flags, closing the end-to-end local workflow: capability output →
JSON export → `atlas daily summary`. 474 tests pass; 41 new tests cover export
unit tests, CLI commands, round-trip export → Daily Brief, and existing behavior
preservation.

**Sprint 52** added three new adapter modules and wired real local JSON inputs
to both export commands, so they now produce meaningful structured output:

- `atlas/adapters/watchlist.py` — `watchlist_input_from_dict()` parses
  `{"name": ..., "items": [...]}` into `WatchlistIntelligenceInput`. Ticker is
  required; `open_questions` become `ResearchProject` entries with `OPEN`
  `ResearchQuestion` objects so the engine surfaces them as unresolved questions.
- `atlas/adapters/knowledge.py` — `knowledge_facts_from_dict()` parses
  `{"facts": [...]}` into `tuple[KnowledgeFact, ...]` with `KnowledgeSource`
  and `KnowledgeReference`.
- `atlas/adapters/research_input.py` — `research_projects_from_dict()` parses
  `{"projects": [...]}` into `tuple[ResearchProject, ...]` with `OPEN`
  `ResearchQuestion` entries.

CLI extensions:
- `atlas watchlist intelligence --input FILE` now loads real watchlist items
  from a local JSON file and passes them through `WatchlistIntelligenceEngine`.
- `atlas discovery export --knowledge FILE --research FILE --watchlist FILE`
  now loads all three input types and feeds them to `DiscoveryEngine`.

535 tests pass; 61 new tests cover adapters, extended CLI, error handling, round-trip
pipeline, language safety, determinism, and no-network constraints.

**Sprint 58** adds a local demo dataset and end-to-end Daily Brief demo workflow.
Three input fixture files were created under `examples/daily_brief_demo/`:
`knowledge.json` (5 AMD knowledge facts), `research_input.json` (1 AMD research
project with 4 open questions), and `watchlist_input.json` (1 AMD watchlist item).
A demo script `scripts/run_daily_brief_demo.sh` runs all five pipeline steps
(`research export`, `watchlist intelligence`, `discovery export`,
`company-analysis export`, `daily summary`) sequentially from local inputs with
no network calls. `examples/daily_brief_demo/README.md` documents purpose,
prerequisites, step-by-step commands, expected output, clean-up, and known
limitations. 728 tests pass; 23 new tests cover data validity, accepted input
shapes, individual export steps, the full end-to-end pipeline, section presence,
language safety, determinism, and no-network constraints. No architecture
boundaries were changed. The legacy `atlas daily brief` command is untouched.

**Sprint 57** added `--sector` and `--country` flags to `atlas company-analysis export`.
Both populate `Company.sector` and `Company.country` in the engine-backed path,
eliminating "Missing Sector" and "Missing Country" unknowns when supplied.
With all four metadata flags (`--company-name`, `--sector`, `--country`,
`--business-description`) provided alongside `--ticker`, all core "Missing X"
unknowns are eliminated and confidence improves to `moderate`. No new files were
created — only `atlas/cli/main.py` was modified. 705 tests pass; 16 new tests
cover the new flags.

**Sprint 56** added `--company-name` and `--business-description` flags to
`atlas company-analysis export`. `--company-name` populates `Company.name`;
`--business-description` populates `CompanyAnalysisInput.business_description`
and eliminates "Missing Business Description" unknown when supplied. 689 tests
pass; 16 new tests.

**Sprint 55** extended `atlas company-analysis export` with three new flags:
`--ticker`, `--knowledge`, and `--research`. When `--ticker` is provided, the
command builds a `Company` object and a `CompanyAnalysisInput` from the supplied
local files (using the existing `knowledge_facts_from_dict` and
`research_projects_from_dict` adapters from Sprint 52), runs
`CompanyAnalysisEngine().analyze()` deterministically, and exports the resulting
`CompanyAnalysisReport` via the Sprint 54 exporter. The first `ResearchProject`
whose `topic` matches the ticker is used as `research_project`; if none matches,
the first project is used. The Sprint 54 `--input` path and no-input path are
both fully preserved. No new files were created — only `atlas/cli/main.py` was
modified. 673 tests pass; 36 new tests cover ticker-only, knowledge, research,
combined, round-trip to Daily Brief, Sprint 54 path preservation, language
safety, determinism, and no-network constraints.

**Sprint 54** added `atlas/capabilities/company_analysis/exporter.py`
(`company_report_to_dict`, `company_reports_to_list`), `atlas/adapters/company_analysis.py`
(`company_reports_from_dict`), and an `atlas company-analysis export [--input FILE]
[--output FILE]` command under a new `company-analysis` subapp. The adapter accepts
a single report object or a list, parses `company`, `unknowns`, `evidence_links`,
`confidence` (string or object), and `what_could_change_the_view` into
`CompanyAnalysisReport` instances. The exporter serializes them to the list format
accepted by `parse_company_analysis_json` and `atlas daily summary --company-analysis`.
When `--input` is omitted the command exports `[]` — a valid empty structure that
produces no Company Analysis Context in the Daily Brief. This closes the last gap in
the Daily Brief local export pipeline: all five input types (portfolio, watchlist,
research, discovery, company analysis) can now be produced locally without manual
JSON authoring of capability output. 637 tests pass; 61 new tests cover adapter,
exporter, CLI, round-trip, language safety, determinism, and no-network constraints.

**Sprint 53** added `atlas/capabilities/daily_brief/research_exporter.py`
(`research_projects_to_dict`) and a new `atlas research export [--input FILE]
[--output FILE]` command under a new `research` subapp. The exporter converts
`tuple[ResearchProject, ...]` to the `{"notes": [...], "open_questions": [...]}`
dict accepted by `atlas daily summary --research`, closing the last remaining
export gap in the Daily Brief pipeline. Topics matching all-uppercase ≤5-char
ticker patterns are included in `related_tickers`. Open and Researching
questions are collected across all projects. 576 tests pass; 41 new tests cover
the exporter, CLI (no-input, `--input`, `--output`), error handling, round-trip
to daily summary, language safety, determinism, and no-network constraints.

The legacy `atlas.daily_brief` engine (powering `atlas daily brief`) is
untouched across all sprints.

## Rules for Future Sprints

- New product capabilities are built in `atlas/domains` and
  `atlas/capabilities`, not in the legacy engine layer.
- Domains must not import capabilities, providers, the CLI, or
  frontend/backend/database/services modules.
- Capabilities must not call external APIs or providers directly.
- Providers remain opt-in: importing Atlas, running its test suite, or
  invoking default CLI commands must never trigger network access. Live
  providers are only reachable through explicit flags (e.g.
  `atlas analyze TICKER --provider yahoo`).
- Legacy engine modules may be bug-fixed but should not gain new features.
- No naming that implies "Atlas Edge" (a separate, unrelated product) should
  appear in code, filenames, or docs. If found, it is technical debt to
  rename or remove.

## Sprint 74 — Legacy Consolidation Inventory

A full inventory of legacy modules and a migration plan was created in Sprint 74.
See [docs/LegacyConsolidationPlan.md](LegacyConsolidationPlan.md).

**Key findings from Sprint 74:**

- `atlas/daily/` is a 43-line pure re-export shim with no logic. Only `atlas/cli/main.py`
  imports it. Removal is the Sprint 75 target.
- `atlas/domains/daily_brief/__init__.py` imports from the legacy `atlas.daily_brief`
  module — a boundary violation (domain → legacy). No external code imports from
  `atlas.domains.daily_brief`, so the fix is safe. Targeted for Sprint 75.
- Provider safety confirmed: providers are never imported by domains, capabilities,
  adapters, or the demo/verification scripts.
- Blueprint-aligned Daily Brief pipeline (`atlas daily summary`) makes zero provider
  calls. Legacy pipeline (`atlas daily brief`) remains untouched.

**Sprint 75 — completed:**

- `atlas/daily/` (43-line re-export shim) deleted. `atlas/cli/main.py` and
  `tests/test_daily_brief.py` now import directly from `atlas.daily_brief`.
- `atlas/domains/daily_brief/__init__.py` boundary violation fixed: rewritten as
  a minimal namespace stub with no imports from legacy or capability modules.
- `test_domains_do_not_import_capabilities_or_providers_or_legacy` extended with
  explicit legacy forbidden-prefix list (`atlas.daily`, `atlas.daily_brief`,
  `atlas.analysis`, `atlas.portfolio_review`, etc.).
- Domain layer is now clean of legacy imports. The boundary test will catch any
  future re-introduction.

**Sprint 76 — completed:**

- `atlas daily brief` CLI command deprecated. The command now prints a
  deprecation notice and exits cleanly (exit 0) without calling `DailyBriefEngine`
  or any provider.
- `from atlas.daily_brief import ...` removed from `atlas/cli/main.py` module-level
  imports — the legacy engine is no longer imported by any current code path.
- `atlas/daily_brief/` (353 lines, provider-coupled legacy engine) remains on disk
  but is now fully isolated: no CLI command, no test, and no adapter imports it.
- `atlas daily summary` (Blueprint-aligned) is the current and only supported
  Daily Brief command.
- 10 new Sprint 76 deprecation tests. 1001 tests passing.
- Recommended Sprint 77 target: delete `atlas/daily_brief/` entirely.

**Sprint 77 — completed:**

- `atlas/daily_brief/` legacy engine (2 files, 353 lines) deleted.
- `tests/test_daily_brief.py` rewritten: 6 legacy engine tests removed, CLI
  deprecation test retained.
- 3 guardrail tests added to `test_architecture_boundaries.py` asserting the
  module directory is absent, the module is not importable, and no source file
  imports from it.
- `atlas.daily_brief` is now fully absent from the codebase. The legacy Daily
  Brief surface area (Group A shim + engine) is completely gone.
- `atlas daily summary` (Blueprint-aligned) remains the sole supported Daily
  Brief command. 998 tests passing.

**Sprint 78 — completed:**

- `atlas watchlist analyze` CLI command deprecated. Prints deprecation notice
  and exits cleanly (exit 0) without calling `WatchlistEngine` or any provider.
- `WatchlistEngine` and `render_watchlist_analysis` removed from `atlas/cli/main.py`
  module-level imports.
- `atlas watchlist intelligence` (Blueprint-aligned) remains the sole supported
  watchlist command.
- `atlas/analysis/watchlist.py` engine remains on disk — it is still used by
  5 legacy engines (monitoring, decision, intelligence, conversation,
  watchlist_review). Its removal requires a broader consolidation effort.
- 10 new Sprint 78 deprecation tests. 1008 tests passing.
- Recommended Sprint 79 target: remove `atlas watchlist analyze` command body
  entirely (or begin consolidating the 5 dependent legacy engines).

**Sprint 79 — completed:**

- `atlas portfolio analyze` CLI command deprecated. Prints deprecation notice
  and exits cleanly (exit 0) without calling `PortfolioIntelligenceEngine` or
  any provider.
- `PortfolioIntelligenceEngine` and `render_portfolio_analysis` removed from
  `atlas/cli/main.py` module-level imports.
- `atlas portfolio summary` (Blueprint-aligned) remains the sole supported
  portfolio domain command.
- `atlas portfolio review` is unchanged — separate legacy path, not in scope.
- `atlas/analysis/portfolio.py` remains on disk; `Portfolio` type is still
  used by summary and review commands.
- 10 new Sprint 79 deprecation tests. 1018 tests passing.
- Recommended Sprint 80 target: deprecate `atlas portfolio review` (the
  remaining legacy portfolio CLI command).

**Sprint 80 — completed:**

- `atlas portfolio review` CLI command deprecated. Prints deprecation notice
  and exits cleanly (exit 0) without calling `PortfolioReviewEngine` or any
  provider.
- `PortfolioReviewEngine`, `PortfolioReviewInput`, `render_portfolio_review`
  removed from `atlas/cli/main.py` module-level imports.
- `atlas portfolio analyze` (deprecated Sprint 79) remains unchanged.
- `atlas portfolio summary` (Blueprint-aligned) is now the sole active
  portfolio CLI command.
- `atlas/portfolio_review/` engine remains on disk — still referenced by
  `AtlasHomeEngine` (Group B legacy).
- 10 new Sprint 80 deprecation tests. 1028 tests passing.
- Recommended Sprint 81 target: continue Group B legacy engine consolidation
  or retire the deprecated CLI command bodies (`portfolio analyze`,
  `portfolio review`) entirely.

**Sprint 81 — completed:**

- `atlas evidence assess` CLI command deprecated. Prints deprecation notice
  and exits cleanly (exit 0) without calling `EvidenceQualityEngine` or
  any provider.
- `EvidenceQualityEngine` and `render_evidence_assessment` removed from
  `atlas/cli/main.py` module-level imports.
- No replacement command invented — message directs toward Blueprint-aligned
  decision and research capabilities (future work).
- `atlas/evidence/` engine remains on disk; still used by `decision_journal`,
  `comparison`, and `watchlist_review` legacy engines.
- All 4 prior deprecated commands (daily brief, watchlist analyze, portfolio
  analyze, portfolio review) confirmed still deprecated via regression tests.
- 12 new Sprint 81 deprecation tests. 1040 tests passing.
- Recommended Sprint 82 target: continue Group C deprecations — e.g.,
  `atlas reason analyze` (ReasoningEngine, self-contained, no providers).

**Sprint 82 — completed:**

- `atlas reason analyze` CLI command deprecated. Prints deprecation notice
  and exits cleanly (exit 0) without calling `ReasoningEngine` or any provider.
- `ReasoningEngine`, `ReasoningInput`, `ReasoningReport`, `render_reasoning_report`
  removed from `atlas/cli/main.py` module-level imports.
- `_build_reasoning_report` private helper (dead code) removed from CLI.
- No replacement command invented — message references Blueprint-aligned
  decision and research capabilities (future consolidation direction).
- `atlas/reasoning/` engine remains on disk; still referenced by
  `atlas/principles/engine.py` (lazy import).
- All 5 prior deprecated commands confirmed still deprecated via regression tests.
- 14 new Sprint 82 deprecation tests. 1054 tests passing.
- Recommended Sprint 83 target: continue Group C deprecations — e.g.,
  `atlas risk size` (RiskEngine, self-contained, no providers).

**Sprint 83 (2026-07-01):** `atlas risk size` deprecated.
- `RiskEngine`, `PositionSizingInput`, `render_risk_analysis` removed from
  `atlas/cli/main.py` module-level imports.
- No replacement command invented — message references Blueprint-aligned
  portfolio, decision and research capabilities (future consolidation direction).
- `atlas/risk/` engine remains on disk; `RiskAnalysis` type still imported by
  `atlas/intelligence/`, `atlas/reasoning/`, and `atlas/conversation/` engines.
  `RiskEngine` class itself has no remaining callers outside deprecated CLI.
- All 6 prior deprecated commands confirmed still deprecated via regression tests.
- 16 new Sprint 83 deprecation tests. 1068 tests passing.
- Recommended Sprint 84 target: continue Group C deprecations — e.g.,
  `atlas risk-drift analyze` (RiskDriftEngine, self-contained, no providers).

**Sprint 84 (2026-07-01):** Deprecated command registry created.
- `atlas/cli/deprecations.py` added — CLI-local registry for all 7 deprecated commands.
- Each deprecated CLI command body now calls `deprecated_command_message(command)` rather
  than inlining the message string. User-facing output is unchanged.
- Registry has no imports from legacy engines, providers, or domains.
- `docs/DeprecatedCommands.md` created with recommended retirement order.
- 46 new Sprint 84 registry tests. 1114 tests passing.
- Recommended Sprint 85 target: retire `atlas daily brief` command body (engine already
  deleted Sprint 77 — safest removal, no engine dependency).

**Sprint 85 (2026-07-01):** `atlas daily brief` command body retired.
- `daily_brief_command` function and `@daily_app.command("brief")` registration
  removed from `atlas/cli/main.py`. The command is no longer callable.
- Entry moved from `_REGISTRY` to `_RETIRED_REGISTRY` in `atlas/cli/deprecations.py`;
  `all_retired_commands()` public accessor added.
- `atlas daily summary` remains unchanged — the supported Daily Brief workflow.
- `atlas.daily_brief` engine remains absent (deleted Sprint 77 — invariant preserved).
- All regression tests updated to assert retirement (exit non-zero) rather than
  deprecation (exit 0 + message).
- 1111 tests passing. CLI surface area reduced by one command.
- Recommended Sprint 86 target: retire `atlas evidence assess` command body
  (EvidenceQualityEngine — self-contained Group C module, no known dependents).

**Sprint 86 (2026-07-01):** `atlas evidence assess` command body retired; `atlas.evidence` engine retained.
- `evidence_assess_command` function and `@evidence_app.command("assess")` registration
  removed from `atlas/cli/main.py`. Command is no longer callable.
- Entry moved from `_REGISTRY` to `_RETIRED_REGISTRY` in `atlas/cli/deprecations.py`.
- `atlas/evidence/` (EvidenceQualityEngine) intentionally kept on disk — confirmed active
  callers: `atlas/comparison/engine.py`, `atlas/decision_journal/engine.py`,
  `atlas/watchlist_review/engine.py`. Engine deletion requires retiring all three first.
- `test_evidence_assess_deprecation.py` rewritten as retirement test; includes assertions
  that the three caller files still exist and still reference EvidenceQualityEngine.
- 1107 tests passing. CLI surface area reduced by one more command.
- Recommended Sprint 87 target: retire `atlas reason analyze` command body
  (ReasoningEngine — requires removing lazy import in atlas/principles/engine.py first,
  then confirming no other callers).

**Sprint 87 (2026-07-01):** `atlas reason analyze` command body retired; `atlas.reasoning` engine retained.
- `reason_analyze_command` function and `@reason_app.command("analyze")` registration
  removed from `atlas/cli/main.py`. Command is no longer callable.
- Entry moved from `_REGISTRY` to `_RETIRED_REGISTRY` in `atlas/cli/deprecations.py`.
- `atlas/reasoning/` (ReasoningEngine) kept on disk — `atlas/principles/engine.py` contains:
  - TYPE_CHECKING import of `ReasoningReport` (not a runtime dependency)
  - Lazy import of `render_reasoning_report` inside `check_reasoning_report()` (no external callers)
- `atlas/domains/decision/engine.py` defines its own Blueprint-aligned `ReasoningEngine` class —
  completely separate from `atlas.reasoning.ReasoningEngine`; unaffected.
- `test_reason_analyze_deprecation.py` rewritten as retirement test; includes assertion that
  `atlas/principles/engine.py` still references `atlas.reasoning` (documents engine deletion blocker).
- 1104 tests passing. CLI surface area reduced by one more command.
- Recommended Sprint 88 target: retire `atlas risk size` command body (stub is a pure no-op;
  RiskEngine has no callers outside the deprecated command).

**Sprint 88 (2026-07-01):** `atlas risk size` command body retired; `atlas.risk` engine retained.
- `risk_size_command` function and `@risk_app.command("size")` registration removed from
  `atlas/cli/main.py`. Command is no longer callable.
- Entry moved from `_REGISTRY` to `_RETIRED_REGISTRY` in `atlas/cli/deprecations.py`.
- `atlas/risk/` kept on disk — `RiskAnalysis` (data type) still imported by
  `atlas/conversation/engine.py`, `atlas/intelligence/engine.py`, `atlas/reasoning/engine.py`.
- `RiskEngine` has no production instantiation points, but cohabitates with `RiskAnalysis`
  in `atlas/risk/engine.py`. Engine deletion deferred to avoid surgical file split.
- `test_risk_size_deprecation.py` rewritten as retirement test; includes assertions that
  `RiskAnalysis` callers still exist and `RiskAnalysis` remains importable.
- 1101 tests passing. CLI surface area reduced by one more command.
- Active `_REGISTRY` holds only the 3 remaining deprecated commands: watchlist analyze,
  portfolio analyze, portfolio review.
- Recommended Sprint 89 target: retire `atlas portfolio analyze` command body.

**Sprint 89 (2026-07-02):** `atlas portfolio analyze` command body retired; `atlas.analysis.portfolio` engine retained.
- `portfolio_analyze_command` function and `@portfolio_app.command("analyze")` registration removed
  from `atlas/cli/main.py`. Command is no longer callable.
- Entry moved from `_REGISTRY` to `_RETIRED_REGISTRY` in `atlas/cli/deprecations.py`.
- `atlas/analysis/portfolio` kept on disk — `Portfolio`, `PortfolioAnalysis`, and
  `PortfolioIntelligenceEngine` are still imported by `atlas/intelligence`, `atlas/conversation`,
  `atlas/decision`, `atlas/dashboard`, `atlas/reasoning`, `atlas/home`, `atlas/suitability`,
  `atlas/risk_drift`, `atlas/monitoring`, and `atlas/portfolio_review`. Engine deletion deferred
  until those callers are retired.
- `test_portfolio_analyze_deprecation.py` rewritten as retirement test; includes assertions that
  engine callers still exist and `PortfolioIntelligenceEngine` remains importable.
- `test_portfolio_analyze_migration.py` updated — all CLI tests now assert `exit_code != 0`;
  domain adapter tests retained to confirm `atlas portfolio summary` path still works.
- 1106 tests passing. CLI surface area reduced by one more command.
- Active `_REGISTRY` holds 2 remaining deprecated commands: watchlist analyze, portfolio review.
- Recommended Sprint 90 target: retire `atlas portfolio review` command body.

**Sprint 90 (2026-07-02):** `atlas portfolio review` command body retired; `atlas.portfolio_review` engine retained.
- `portfolio_review_command` function and `@portfolio_app.command("review")` registration removed
  from `atlas/cli/main.py`. Command is no longer callable.
- Entry moved from `_REGISTRY` to `_RETIRED_REGISTRY` in `atlas/cli/deprecations.py`.
- `atlas.portfolio_review` engine **intentionally retained** — `atlas/home/engine.py`
  (`AtlasHomeEngine`) still imports and instantiates `PortfolioReviewEngine` at runtime.
  Engine deletion deferred until `AtlasHomeEngine` is retired or migrated.
- Important distinction: `atlas.domains.portfolio.review.PortfolioReviewEngine` is a
  separate Blueprint-aligned class, unaffected by this change.
- `test_portfolio_review_deprecation.py` rewritten as retirement test; includes engine
  caller-presence assertion (`atlas/home/engine.py`) and Blueprint engine independence test.
- `test_portfolio_review_migration.py` updated — all CLI tests assert `exit_code != 0`;
  legacy engine and domain adapter tests retained.
- 1111 tests passing. CLI surface area reduced by one more command.
- Active `_REGISTRY` holds 1 remaining deprecated command: watchlist analyze.
- Recommended Sprint 91 target: retire `atlas watchlist analyze` command body.

**Sprint 91 (2026-07-02):** `atlas watchlist analyze` command body retired; `atlas.analysis.watchlist` engine retained.
- `watchlist_analyze_command` function and `@watchlist_app.command("analyze")` registration removed
  from `atlas/cli/main.py`. Command is no longer callable.
- Entry moved from `_REGISTRY` to `_RETIRED_REGISTRY` in `atlas/cli/deprecations.py`.
- Active `_REGISTRY` is now empty — all deprecated commands have been retired.
- `atlas.analysis.watchlist` engine **intentionally retained** — `WatchlistEngine` is still
  imported and instantiated by `atlas/intelligence`, `atlas/decision`, `atlas/monitoring`,
  `atlas/watchlist_review`, and `atlas/conversation`. Five active callers remain.
- `atlas watchlist intelligence` (Blueprint-aligned) is unaffected.
- `test_watchlist_analyze_deprecation.py` rewritten as retirement test; includes engine
  caller-presence assertions for all five callers; `test_active_deprecated_registry_is_now_empty`
  confirms the registry is empty.
- 1116 tests passing (3 skipped — parametrized tests with empty EXPECTED_COMMANDS).
- **Deprecated command retirement plan complete.** All seven originally deprecated CLI commands
  are now retired. Legacy engine cleanup remains as future technical debt (Sprints 92+).
- Recommended Sprint 92 target: begin legacy engine cleanup — retire `atlas/monitoring/` or
  `atlas/watchlist_review/` as the most isolated WatchlistEngine callers.

**Sprint 92 (2026-07-02):** WatchlistEngine caller audit complete; redundant double-run eliminated in watchlist_review; caller exclusivity guardrail added.
- Full import audit performed. WatchlistEngine callers: atlas/intelligence, atlas/decision,
  atlas/monitoring, atlas/watchlist_review, atlas/conversation — all 5 active (CLI commands).
  Neither `atlas/monitoring/` nor `atlas/watchlist_review/` can be retired this sprint.
- Key finding: `WatchlistReviewEngine.review()` was invoking `WatchlistEngine.analyze()` twice
  on the same inputs — once directly, once inside `MonitoringEngine.snapshot_watchlist()`.
- Cleanup performed:
  1. Added `MonitoringEngine.snapshot_watchlist_from_analysis(analysis)` — builds MonitoringSnapshot
     from pre-computed WatchlistAnalysis without re-running WatchlistEngine.
  2. Refactored `MonitoringEngine.snapshot_watchlist()` to delegate to the new method.
  3. `WatchlistReviewEngine.__init__` now shares one WatchlistEngine instance with its MonitoringEngine.
  4. `WatchlistReviewEngine.review()` uses `snapshot_watchlist_from_analysis` — redundant run eliminated.
  5. Added `test_watchlist_engine_callers_are_exactly_the_known_set` exclusivity guardrail.
- WatchlistEngine caller count: 5 before → 5 after (unchanged; both modules still require it for CLI).
- 1118 tests passing (3 skipped). Demo passed. Release verification green.
- Recommended Sprint 93 target: replace `atlas/monitoring/` watchlist snapshot methods with
  Blueprint-aligned data source, or migrate `atlas/watchlist_review/` direct WatchlistEngine usage
  to use the watchlist_intelligence capability layer.

**Sprint 93 (2026-07-02):** WatchlistEngine removed from `atlas/monitoring/engine.py`; caller count 5 → 4.
- `atlas monitor watchlist` CLI path now uses Blueprint-aligned `WatchlistIntelligenceEngine` instead of
  legacy `WatchlistEngine`. Legacy `Watchlist` (tickers) converted to minimal `WatchlistIntelligenceInput`
  items; `MonitoringSnapshot` built from research-driven signals (items needing attention, evidence gaps,
  open questions). Provider parameter is now optional — watchlist monitoring is provider-free.
- `snapshot_watchlist_from_analysis(analysis)` retained in `MonitoringEngine` — still called by
  `atlas/watchlist_review/engine.py` for its own direct WatchlistEngine analysis path.
- `atlas/watchlist_review/engine.py` updated: `MonitoringEngine()` no longer passed `watchlist_engine=`.
- Architecture boundary confirmed: legacy module (`atlas/monitoring/`) may import from
  `atlas.capabilities.watchlist_intelligence` — only domains are forbidden from importing capabilities.
- WatchlistEngine caller count: 5 before → **4** after (intelligence, decision, watchlist_review, conversation).
- 1121 tests passing (3 skipped). Demo passed. Release verification green.
- Recommended Sprint 94 target: migrate `atlas/watchlist_review/` direct WatchlistEngine dependency
  to Blueprint-aligned capability; also cleanup `snapshot_watchlist_from_analysis` in monitoring.

**Sprint 94 (2026-07-02):** WatchlistEngine removed from `atlas/watchlist_review/engine.py`; `snapshot_watchlist_from_analysis` removed from `MonitoringEngine`; caller count 4 → 3.
- `WatchlistReviewEngine.__init__` no longer accepts or instantiates `WatchlistEngine`.
  `review()` no longer computes `watchlist_analysis` via WatchlistEngine. Company items default
  to `base_score=45` instead of `atlas_score` — item rankings less differentiated, documented.
- `monitoring_engine.snapshot_watchlist_from_analysis(watchlist_analysis)` replaced with
  `monitoring_engine.snapshot_watchlist(supported_watchlist)` — Blueprint-aligned (Sprint 93).
  Both `Watchlist` and `WatchlistItem` from `atlas.analysis.watchlist` retained in import
  (still needed as legacy data types for the watchlist input contract).
- `snapshot_watchlist_from_analysis()` removed from `MonitoringEngine` — no runtime callers remain.
  `WatchlistAnalysis` import removed from `atlas/monitoring/engine.py`.
- Guardrail: `test_watchlist_review_engine_does_not_import_watchlist_engine` added.
- Exclusivity guardrail updated: caller set now 3 (intelligence, decision, conversation).
- WatchlistEngine caller count: 4 before → **3** after.
- 1121 tests passing (3 skipped). Demo passed. Release verification green.
- Recommended Sprint 95 target: migrate `atlas/decision/` or `atlas/conversation/` WatchlistEngine
  usage. `atlas/decision/` is smaller and may be lower-risk than `atlas/conversation/`.

**Sprint 95 (2026-07-02):** WatchlistEngine removed from `atlas/decision/decision_engine.py`; `DecisionResult.watchlist_intelligence` now carries `WatchlistIntelligenceReport | None`; caller count 3 → 2.
- `AtlasDecisionEngine.__init__` no longer accepts or instantiates `WatchlistEngine`.
  `_analyze_watchlist()` renamed to `_watchlist_intelligence()`, rewritten to use
  `WatchlistIntelligenceEngine().analyze()` (same conversion pattern as Sprint 93/94).
- `_confidence()` and `_reasoning()` updated to accept `WatchlistIntelligenceReport | None`.
  Reasoning now uses `report.overview` and `companies_needing_attention[0].ticker` (or
  `observations[0].ticker`) instead of legacy `final_atlas_view` / `strongest_opportunity.ticker`.
- `atlas/decision/decision_result.py`: `watchlist_analysis: WatchlistAnalysis | None` replaced
  with `watchlist_intelligence: WatchlistIntelligenceReport | None`. Import now points to capability.
- `atlas/intelligence/engine.py`: removed `watchlist_engine=self.watchlist_engine` from
  `AtlasDecisionEngine(...)` construction — parameter no longer accepted.
- Guardrail: `test_decision_engine_does_not_import_watchlist_engine` added.
- Exclusivity guardrail updated: caller set now 2 (intelligence, conversation).
- WatchlistEngine caller count: 3 before → **2** after.
- 1122 tests passing (3 skipped). Demo passed. Release verification green.
- Recommended Sprint 96 target: migrate `atlas/intelligence/` or `atlas/conversation/` WatchlistEngine
  dependency; `atlas/conversation/` carries the most WatchlistEngine surface area.
