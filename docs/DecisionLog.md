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
