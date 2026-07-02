# Atlas Decision Log

This log records architectural decisions that shape future development.

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
