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

**Known boundary violation (as of Sprint 74):**

`atlas/domains/daily_brief/__init__.py` imports from `atlas.daily_brief` (legacy).
This violates the rule that domains must not import legacy modules. Resolution is
scheduled for Sprint 75 alongside `atlas/daily/` shim removal.
