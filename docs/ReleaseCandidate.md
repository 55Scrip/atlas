# Atlas Internal Release Candidate 2

**Version:** v0.1.0-rc2  
**Date:** 2026-07-01  
**Sprint:** 71

---

## What This Is

Atlas Internal Release Candidate 2 (RC2) marks the completion of the Atlas
post-RC1 integration sprints (68–71). It extends RC1 with a complete five-surface
Daily Brief demo, portfolio concentration signalling, and evidence link resolution
for company knowledge facts.

This is an internal milestone — not a public release.

---

## What Changed Since RC1 (Sprints 69–70)

### Sprint 69 — Portfolio Demo Integration

- Added `examples/daily_brief_demo/portfolio.json` (NVDA 55%, AMD 30%, Cash 15%)
- Passed `--portfolio` to `atlas daily summary` in demo script
- Portfolio concentration at 55% exercises the HIGH priority path in "What Deserves Attention"
- Demo now exercises **all five** Daily Brief input surfaces: portfolio, research, watchlist, discovery, company analysis
- Overall brief priority in demo: `high` (was `moderate`)
- Added Portfolio Context section to demo output

### Sprint 70 — Evidence Link Resolution

- Added `--knowledge` flag to `atlas watchlist intelligence`
- Added `assign_knowledge_facts` in `atlas/adapters/watchlist.py`
- Knowledge facts are now distributed to watchlist items by two deterministic rules:
  1. Exact ticker match (`"AMD"`)
  2. Company node ID pattern (`"company-amd"` → `"AMD"`)
- Demo script Step 2 now passes `--knowledge examples/daily_brief_demo/knowledge.json`
- "Suggested Next Research Steps" no longer contains false `"AMD: No knowledge facts are linked."` / `"NVDA: No knowledge facts are linked."` lines

### Sprint 71 — RC2 Verification

- All 7 verification steps green
- 947 tests passing
- Documentation updated to reflect RC2 state

---

## What Works (RC2)

### Capabilities

| Capability | Module | What it provides |
|---|---|---|
| Portfolio | `atlas.domains.portfolio` | Deterministic portfolio understanding: weights, concentration, sector/country allocation |
| Research | `atlas.domains.research` | Research projects, open questions, notes, thesis fragments |
| Knowledge | `atlas.domains.knowledge` | Attributed facts, knowledge nodes, evidence references |
| Decision | `atlas.domains.decision` | Structured reasoning: evidence → observations → reasoning → unknowns |
| Company Analysis | `atlas.capabilities.company_analysis` | Deterministic company analysis from research + knowledge |
| Watchlist Intelligence | `atlas.capabilities.watchlist_intelligence` | Watchlist overview, open questions, suggested steps, knowledge fact linking |
| Discovery | `atlas.capabilities.discovery` | Discovery candidates from knowledge + research + watchlist |
| Daily Brief | `atlas.capabilities.daily_brief` | Deterministic daily overview with priority routing across five input surfaces |

### Full CLI Pipeline (RC2)

```
atlas research export         → research.json
atlas watchlist intelligence  → watchlist.json   (--knowledge now supported)
atlas discovery export        → discovery.json
atlas company-analysis export → company_analysis_<ticker>.json
atlas company-analysis merge  → company_analysis.json (combined)
atlas daily summary           → Daily Brief output
```

All commands are composable. All outputs are deterministic JSON. No network calls.

### Daily Brief Output (RC2)

Five input surfaces now exercised in the demo:

| Input | Surface | Key signal |
|---|---|---|
| `portfolio.json` | Portfolio Context | Concentration HIGH → `[!]` in What Deserves Attention |
| `research.json` | Research Context | 7 unresolved questions → MODERATE |
| `watchlist.json` | Watchlist Context | 4 open questions, 2 suggested steps |
| `discovery.json` | Discovery Context | 2 candidates → MODERATE |
| `company_analysis.json` | Company Analysis Context | AMD + NVDA available for review → LOW |

Priority routing (unchanged from RC1):

| Signal | Priority | Section |
|---|---|---|
| Portfolio concentration HIGH/ELEVATED | high | What Deserves Attention |
| Open research questions | moderate | What Deserves Attention |
| Discovery candidates | moderate | What Deserves Attention |
| Company reports without unknowns | low | What Can Safely Wait |

### Evidence Link Resolution (RC2)

`atlas watchlist intelligence --knowledge <file>` distributes knowledge facts
to watchlist items. Matching rules (deterministic, explicit, no fuzzy logic):

1. Exact ticker match: `fact.subject_node_id == "AMD"`
2. Company node ID: `fact.subject_node_id == "company-amd"` → ticker `AMD`

Implemented in `_node_id_matches_ticker` and `assign_knowledge_facts` in
`atlas/adapters/watchlist.py`. Covered by tests.

---

## How to Run Tests

```bash
.venv/bin/python -m compileall atlas tests
.venv/bin/python -m pytest
```

**Result:** 947 tests pass, 0 failures.

## Full Release Verification

```bash
bash scripts/verify_release_candidate.sh
```

Steps performed:
1. Compile check (`python -m compileall atlas tests`)
2. Full test suite (`pytest`)
3. Daily Brief demo (`scripts/run_daily_brief_demo.sh`)
4. Verify all 7 generated files exist in `tmp/atlas_demo/`
5. Verify expected sections in `daily_brief.txt` (including Portfolio Context)
6. Forbidden language check on `daily_brief.txt`
7. Cleanup (`rm -rf tmp/atlas_demo`)

**Result:** All 7 steps green on RC2 verification run.

---

## How to Run the Demo

```bash
bash scripts/run_daily_brief_demo.sh
```

**Result:** All 7 steps complete. `daily_brief.txt` saved. No network calls.

Cleanup:

```bash
rm -rf tmp/atlas_demo
```

---

## Release Checklist (RC2)

- [x] Compile check passes (`python -m compileall atlas tests`)
- [x] Full test suite passes (947 tests)
- [x] Demo script runs without virtualenv activation
- [x] All five Daily Brief input surfaces exercised in demo
- [x] Portfolio concentration signals HIGH in demo output
- [x] Evidence link resolution: `company-amd` → `AMD` matching works
- [x] No false "No knowledge facts are linked" in demo output
- [x] No external calls in demo pipeline
- [x] No recommendation language in CLI output
- [x] No recommendation language in demo documentation
- [x] Architecture boundary tests pass
- [x] No Atlas Edge naming in active code or docs
- [x] `docs/ReleaseCandidate.md` updated for RC2
- [x] `scripts/verify_release_candidate.sh` updated for RC2 wording
- [x] Working tree clean after commit

---

## Known Limitations (RC2)

1. **Legacy CLI commands** — `atlas daily brief`, `atlas home`, `atlas analyze`
   and others call legacy engines directly. They are functional but not part of
   the Blueprint-aligned pipeline. They will not receive new capabilities.

2. **No persistence** — Atlas has no database in the current demo pipeline.
   All state is passed via JSON files. A persistence layer is future scope.

3. **Provider layer is opt-in and untested in demo** — `atlas.providers` exists
   and works but is not called by the demo or Daily Brief pipeline. Tests verify
   that no provider calls are made.

4. **The `--company-analysis` flag accepts one file** — multiple company analysis
   reports require the merge step (`atlas company-analysis merge`) first. This is
   by design but adds a pipeline step.

*Resolved since RC1:*
- ~~Evidence link notes (`"AMD: No knowledge facts are linked."`) false negatives~~ — fixed in Sprint 70
- ~~Portfolio demo not exercised in demo script~~ — fixed in Sprint 69

---

## Technical Debt (RC2)

| Area | Description | Priority |
|---|---|---|
| README historical sections | Lines ~320+ are sprint notes, not developer docs. Future sprint could archive them. | Low |
| Legacy engine consolidation | 20+ legacy modules remain. Future sprints could migrate high-value engines to Blueprint-aligned layer. | Medium |
| `tmp/atlas_demo/` stale files | Demo script does not clean old files before writing. Files from earlier runs accumulate if cleanup is not run. | Low |
| ArchitectureConsolidation doc | References RC1 (Sprint 67) only. Could note RC2 review. | Low |

---

## Next Recommended Phase

**Sprint 72 recommendation: Knowledge Node Linking in Discovery Context**

The Discovery Context section currently shows knowledge facts by `subject_node_id`
(`company-amd`, `company-nvda`). A future sprint could resolve these node IDs to
human-readable company names in the Daily Brief output, making the section
more immediately readable without requiring knowledge of the node naming convention.

Alternative directions:
- Legacy engine migration (large, multi-sprint)
- Archive/clean README historical sprint notes (small, cosmetic)
- Persistence layer foundation (new capability, multi-sprint)

---

---

# Atlas Internal Release Candidate 1

**Version:** v0.1.0-rc1  
**Date:** 2026-07-01  
**Sprint:** 67

---

## What This Is

Atlas Internal Release Candidate 1 (RC1) marks the completion of the Atlas
foundation sprints (36–67). It establishes a stable, testable, fully local
investment research pipeline with no external dependencies.

This is an internal milestone — not a public release. It demonstrates that the
core Atlas architecture is sound, the Daily Brief pipeline is working, and the
codebase is clean enough to build on.

---

## What Works

### Domains (Blueprint-aligned)

| Domain | Module | What it provides |
|---|---|---|
| Portfolio | `atlas.domains.portfolio` | Deterministic portfolio understanding: weights, concentration, sector/country allocation |
| Research | `atlas.domains.research` | Research projects, open questions, notes, thesis fragments |
| Knowledge | `atlas.domains.knowledge` | Attributed facts, knowledge nodes, evidence references |
| Decision | `atlas.domains.decision` | Structured reasoning: evidence → observations → reasoning → unknowns |

### Capabilities (Blueprint-aligned)

| Capability | Module | What it provides |
|---|---|---|
| Company Analysis | `atlas.capabilities.company_analysis` | Deterministic company analysis from research + knowledge |
| Watchlist Intelligence | `atlas.capabilities.watchlist_intelligence` | Watchlist overview, open questions, suggested steps |
| Discovery | `atlas.capabilities.discovery` | Discovery candidates from knowledge + research + watchlist |
| Daily Brief | `atlas.capabilities.daily_brief` | Deterministic daily overview with priority routing |

### CLI Pipeline

Full JSON export pipeline for the Daily Brief:

```
atlas research export         → research.json
atlas watchlist intelligence  → watchlist.json
atlas discovery export        → discovery.json
atlas company-analysis export → company_analysis_<ticker>.json
atlas company-analysis merge  → company_analysis.json (combined)
atlas daily summary           → Daily Brief output
```

All commands are composable. All outputs are deterministic JSON. No network calls.

### Local Demo

A working end-to-end demo using AMD + NVDA example data:

```bash
bash scripts/run_daily_brief_demo.sh
```

Produces 7 output files in `tmp/atlas_demo/` including `daily_brief.txt`.
No virtualenv activation required — the script detects `.venv/bin/atlas`
automatically.

### Daily Brief Output (RC1 priority routing)

"What Deserves Attention" contains only HIGH and MODERATE items.

| Signal | Priority | Section |
|---|---|---|
| Portfolio concentration HIGH/ELEVATED | high | What Deserves Attention |
| Open research questions | moderate | What Deserves Attention |
| Company reports with unknowns | moderate | What Deserves Attention |
| Discovery candidates | moderate | What Deserves Attention |
| Company reports without unknowns | low | What Can Safely Wait |
| Knowledge context | low | Included Context |

---

## How to Run Tests

```bash
.venv/bin/python -m compileall atlas tests
.venv/bin/python -m pytest
```

**Result:** 910 tests pass, 0 failures.

## Full Release Verification (Sprint 68)

A single script runs compile check, full test suite, demo, file verification,
output section check, and forbidden-language check:

```bash
bash scripts/verify_release_candidate.sh
```

Steps performed:
1. Compile check (`python -m compileall atlas tests`)
2. Full test suite (`pytest`)
3. Daily Brief demo (`scripts/run_daily_brief_demo.sh`)
4. Verify all 7 generated files exist in `tmp/atlas_demo/`
5. Verify expected sections present in `daily_brief.txt`
6. Forbidden language check on `daily_brief.txt`
7. Cleanup (`rm -rf tmp/atlas_demo`)

**Result:** All 7 steps green on RC1 verification run.

---

## How to Run the Demo

```bash
bash scripts/run_daily_brief_demo.sh
```

**Result:** All 7 steps complete. `daily_brief.txt` saved. No network calls.

Cleanup:

```bash
rm -rf tmp/atlas_demo
```

---

## Release Checklist

- [x] Compile check passes (`python -m compileall atlas tests`)
- [x] Full test suite passes (910 tests)
- [x] Demo script runs without virtualenv activation
- [x] No external calls in demo pipeline
- [x] No recommendation language in CLI output
- [x] No recommendation language in demo documentation
- [x] Architecture boundary tests pass
- [x] No Atlas Edge naming in active code or docs
- [x] `docs/ReleaseCandidate.md` exists
- [x] `scripts/verify_release_candidate.sh` runs cleanly (Sprint 68)
- [x] Working tree clean after commit

---

## Current Architecture

### Active layers

```
atlas/domains/         ← canonical concepts, no provider imports
atlas/capabilities/    ← product capabilities, composes domains
atlas/shared/          ← immutable canonical entities
atlas/adapters/        ← bridges domain ↔ legacy types
atlas/providers/       ← opt-in market data (not called by demo)
atlas/cli/             ← CLI commands (typer)
```

### Legacy layers (preserved, not for expansion)

```
atlas/analysis/        ← original company analysis engine
atlas/daily/           ← original daily brief engine
atlas/daily_brief/     ← legacy daily brief module
atlas/dashboard/       ← legacy dashboard
atlas/home/            ← legacy home engine
atlas/intelligence/    ← legacy intelligence engine
atlas/portfolio_review/
atlas/watchlist_review/
atlas/comparison/
atlas/conversation/
atlas/decision_journal/
atlas/economics/
atlas/evidence/
atlas/language/
atlas/market/
atlas/memory/
atlas/monitoring/
atlas/principles/
atlas/profile/
atlas/reasoning/
atlas/risk/
atlas/risk_drift/
atlas/services/
atlas/suitability/
atlas/themes/
```

Legacy modules are functional and fully tested. All new capability work belongs
in `atlas/domains/` and `atlas/capabilities/`.

Guardrails: [docs/ArchitectureConsolidation.md](ArchitectureConsolidation.md)

---

## Known Limitations

1. **"Suggested Next Research Steps" evidence notes** — the Daily Brief shows
   per-company evidence-link notes ("AMD: No knowledge facts are linked.") even
   when knowledge is present at the project level. The evidence gap resolver
   matches knowledge by `subject_node_id`, not by company ticker. The notes are
   technically correct but may confuse users who see knowledge facts in
   "Included Context" but read "no knowledge facts linked" in research steps.

2. **Legacy CLI commands** — `atlas daily brief`, `atlas home`, `atlas analyze`
   and others call legacy engines directly. They are functional but not part of
   the Blueprint-aligned pipeline. They will not receive new capabilities.

3. **No persistence** — Atlas has no database in the current demo pipeline.
   All state is passed via JSON files. A persistence layer is future scope.

4. **No portfolio integration in demo** — the demo does not pass a portfolio
   file to `atlas daily summary`. Portfolio concentration signals (HIGH priority
   items) are exercised by tests but not shown in the demo output.

5. **Provider layer is opt-in and untested in demo** — `atlas.providers` exists
   and works but is not called by the demo or Daily Brief pipeline. Tests verify
   that no provider calls are made.

---

## Technical Debt

| Area | Description | Priority |
|---|---|---|
| README historical sections | Lines ~320–1680 are sprint notes, not developer docs. They are accurate history but add noise. A future sprint could archive them. | Low |
| Legacy engine consolidation | 20+ legacy modules remain. Future sprints could migrate high-value engines to the Blueprint-aligned layer. | Medium |
| Evidence link resolution | Knowledge facts attributed to `company-amd` node IDs are not auto-linked to the AMD company ticker in Research Steps output. | Low |
| `tmp/atlas_demo/` stale files | The demo script does not clean old files before writing. Files from earlier exploratory runs accumulate. | Low |
| Portfolio demo integration | The demo does not exercise portfolio concentration signals. Adding a demo portfolio JSON would complete the end-to-end story. | Medium |

---

## Next Recommended Phase

**Sprint 68 recommendation: Portfolio Demo Integration**

The one visible gap in the current demo is portfolio context. Adding a demo
`portfolio.json` to `examples/daily_brief_demo/` and passing `--portfolio` to
`atlas daily summary` in the demo script would complete the full Daily Brief
input surface. This would exercise HIGH priority concentration signals in the
demo output and make the "What Deserves Attention" section show all three
priority sources.

Alternative directions:
- Evidence link resolution fix (small, targeted)
- Legacy engine migration (large, multi-sprint)
- Archive/clean README historical sections (small, cosmetic)
