# Atlas Daily Brief (Sprint 48)

## Responsibility

The Daily Brief organises existing Atlas domain and capability structures
into a calm, deterministic daily overview. It answers:

- What deserves attention?
- What remains unresolved?
- What can safely wait?
- What research should continue?

It does not generate recommendations, fetch news, call market data, or
invent events.

## Input Builder (Sprint 49)

`atlas.capabilities.daily_brief.input_builder.build_daily_brief_input` is the
canonical way to construct a `DailyBriefInput` from typed Atlas structures:

```python
from atlas.capabilities.daily_brief import DailyBriefCapability, build_daily_brief_input

brief_input = build_daily_brief_input(
    portfolio_summary=my_portfolio_summary,      # PortfolioSummary from atlas.domains.portfolio
    research_notes=my_notes,                    # tuple[ResearchNote, ...]
    research_projects=my_projects,              # tuple[ResearchProject, ...] — open questions extracted
    company_reports=my_company_reports,         # tuple[CompanyAnalysisReport, ...]
    watchlist_report=my_watchlist_report,       # WatchlistIntelligenceReport | None
    discovery_report=my_discovery_report,       # DiscoveryReport | None
    knowledge_node_count=len(my_facts),
    date_label="2026-07-01",
)
report = DailyBriefCapability().generate(brief_input)
```

The builder is deterministic, side-effect free, and makes no network calls.
It merges `open_research_questions` from both explicit arguments and from the
`OPEN`/`RESEARCHING` questions inside any supplied `ResearchProject` instances.

## Two Daily Brief Paths

### Legacy: `atlas daily brief` — RETIRED (Sprint 85)

The original command (`atlas daily brief`) was deprecated in Sprint 76 and fully
retired in Sprint 85. The command body has been removed — `atlas daily brief` is
no longer a valid CLI command.

The underlying `atlas.daily_brief.DailyBriefEngine` (provider-coupled, 353 lines)
was deleted in Sprint 77. Use `atlas daily summary` instead.

### Blueprint-aligned: `atlas daily summary` (Sprint 48, current)

The new command (`atlas daily summary`), powered by
`atlas.capabilities.daily_brief.DailyBriefCapability`, accepts optional
domain-native inputs and organises them into a structured daily brief using
only deterministic, in-memory calculations — no providers, no network,
no AI. This is the future direction.

## Report Structure

`DailyBriefReport` contains:

| Field | Type | Purpose |
|---|---|---|
| `title` | str | Always "Atlas Daily Brief" |
| `summary` | DailyBriefSummary | Bottom line, priority, development flag |
| `sections` | tuple[DailyBriefSection, ...] | Ordered structured sections |
| `unknowns` | tuple[DailyBriefUnknown, ...] | Unresolved questions |
| `evidence_gaps` | tuple[DailyBriefEvidenceLink, ...] | Missing evidence links |
| `next_research_steps` | tuple[str, ...] | Suggested next steps |
| `knowledge_node_count` | int | Count of knowledge facts; rendered in Included Context (Sprint 65) |

### Sections (in order)

1. **What Deserves Attention** — always present; shows "no developments" when nothing supplied
2. **Portfolio Context** — present only when portfolio summary provided
3. **Company Analysis Context** — present only when company reports provided
4. **Research Context** — present only when research notes provided
5. **Watchlist Context** — present only when watchlist report provided
6. **Discovery Context** — present only when discovery report with candidates provided

### What Deserves Attention — Priority Routing (Sprint 65)

"What Deserves Attention" contains only HIGH and MODERATE priority items.
LOW priority items are never promoted into this section.

| Item | Priority | Routing |
|---|---|---|
| Portfolio concentration HIGH/ELEVATED | `high` | What Deserves Attention |
| Open research questions | `moderate` | What Deserves Attention |
| Company reports with unknowns | `moderate` | What Deserves Attention |
| Company reports without unknowns | `low` | What Can Safely Wait |
| Knowledge context | `low` | Included Context only |

When all inputs are LOW priority, "What Deserves Attention" shows a calm
fallback: "Context has been organised. No items require immediate attention."
This is distinct from the empty-input fallback ("No meaningful developments were
identified"), which fires only when no inputs were supplied at all.

#### Company Analysis Routing (Sprint 63 + Sprint 65)

`_company_analysis_opening_item` evaluates all company reports to determine
a single priority item:

| Condition | Priority |
|---|---|
| Any company has unknowns | `moderate` — included in What Deserves Attention |
| All companies have no unknowns | `low` — excluded from What Deserves Attention |

Low-priority company analysis items remain visible in "Company Analysis Context"
and are collected into "What Can Safely Wait" by `_collect_safely_wait_items`.

## Priority Model

`DailyBriefPriority` has three levels: `low`, `moderate`, `high`.

Priority means "deserves attention" — not "requires action".

Priority is raised to `high` when portfolio concentration is `High` or
`Elevated` (≥25% in the largest position). Priority is `moderate` when
open research questions exist. Priority defaults to `low` when no signals
are present.

## No Meaningful Developments Behavior

When `DailyBriefInput()` is called with no arguments or an empty input,
the report returns:

- `has_meaningful_developments = False`
- `summary.overall_priority = low`
- `summary.bottom_line = "No meaningful developments were identified from the available inputs."`

This is valid, expected output. Atlas does not force fake insights.

## Relationship to Domains and Capabilities

Daily Brief may consume:

- `atlas.domains.portfolio` — via `PortfolioSummary` from the adapter
- `atlas.domains.research` — via `ResearchNote` tuples
- `atlas.domains.knowledge` — via `knowledge_node_count`
- `atlas.capabilities.company_analysis` — via `CompanyAnalysisReport` tuples
- `atlas.capabilities.watchlist_intelligence` — via `WatchlistIntelligenceReport`
- `atlas.capabilities.discovery` — via `DiscoveryReport`

Daily Brief does not own any of these concepts. It only composes them.

## No-News / No-API Constraint

`atlas.capabilities.daily_brief` makes no network calls, imports no
provider modules, and does not call `urllib`, `requests`, or `httpx`.
Verified by `tests/test_architecture_boundaries.py` and
`tests/test_daily_brief_capability.py::test_capability_makes_no_network_calls`.

## CLI Behavior

```bash
# Blueprint-aligned (Sprint 48–50)
atlas daily summary                              # no-input mode, always succeeds
atlas daily summary --portfolio portfolio.json   # with portfolio domain context
atlas daily summary --research research.json     # with research notes and open questions
atlas daily summary --watchlist watchlist.json   # with watchlist intelligence context
atlas daily summary --discovery discovery.json   # with discovery candidates
atlas daily summary --company-analysis company.json  # with company analysis context

# All flags are composable
atlas daily summary \
  --portfolio portfolio.json \
  --research research.json \
  --watchlist watchlist.json \
  --discovery discovery.json \
  --company-analysis company.json

# Legacy (unchanged)
atlas daily brief                                # original multi-engine brief
atlas daily brief --portfolio portfolio.json     # with legacy portfolio context
```

All flags are optional. With no flags the command always succeeds and reports
"No meaningful developments were identified from the available inputs."
No network calls are made regardless of which flags are supplied.

## JSON Input Formats

### Research JSON (`--research`)

```json
{
  "notes": [
    {
      "id": "n1",
      "title": "NVDA deep dive",
      "body": "Initial thesis forming around GPU demand.",
      "created_at": "2026-07-01",
      "related_tickers": ["NVDA"]
    }
  ],
  "open_questions": [
    "What is the TAM for data centre GPU?",
    "Who owns the supply chain?"
  ]
}
```

`notes` and `open_questions` are both optional. `open_questions` may be plain
strings or omitted. Questions appear in "Unresolved Questions" in the output.

### Watchlist JSON (`--watchlist`)

```json
{
  "name": "My Watchlist",
  "open_questions": [
    {"id": "wq1", "question": "What is NVDA's competitive moat?", "status": "open"}
  ],
  "suggested_next_research_steps": [
    "Research NVDA supply chain constraints."
  ]
}
```

`open_questions` items may also be plain strings. All fields are optional.

### Discovery JSON (`--discovery`)

```json
{
  "candidates": [
    {
      "identifier": "ASML",
      "title": "ASML Holding",
      "reasons": [
        {"title": "Knowledge Fact", "detail": "Critical semiconductor equipment supplier."}
      ],
      "priority": "moderate"
    }
  ]
}
```

`reasons` is optional; a fallback detail is used if omitted.
`priority` is informational only and does not imply action.

### Company Analysis JSON (`--company-analysis`)

```json
{
  "company": {
    "id": "nvda", "name": "NVIDIA Corporation",
    "ticker": "NVDA", "sector": "Semiconductors"
  },
  "unknowns": [
    {"title": "Competitive moat durability", "detail": "Evidence is limited."}
  ],
  "evidence_links": [
    {"id": "ev1", "source": "10-K 2025", "description": "Revenue breakdown."}
  ]
}
```

Accepts a single object or a JSON array of multiple company reports.
`unknowns` and `evidence_links` are optional.

## Integrated Input Sources (Sprint 49)

Daily Brief now correctly consumes all five input types using real typed
Atlas structures:

| Input source | Atlas type | What Daily Brief reads |
|---|---|---|
| Portfolio | `PortfolioSummary` | holdings count, concentration, cash weight, largest position |
| Research | `ResearchNote` | title, body (up to 200 chars) |
| Research Projects | `ResearchProject` | open and researching questions extracted automatically |
| Watchlist | `WatchlistIntelligenceReport` | open_questions, suggested_next_research_steps |
| Discovery | `DiscoveryReport` | candidates (identifier, reasons[0].detail) |
| Company Analysis | `CompanyAnalysisReport` | company.ticker, unknowns (title), evidence_links |

Sprint 49 also fixed attribute-name mismatches in the engine that would have
caused incorrect output (empty detail, wrong field names) when real typed
objects were passed without the builder:

- `ResearchNote`: now reads `title` / `body` (was `ticker` / `content`)
- `WatchlistIntelligenceReport`: now reads `suggested_next_research_steps` (was `suggested_next_steps`)
- `DiscoveryCandidate`: now reads `identifier` and `reasons[0].detail` (was `ticker` and `reason`)
- `CompanyAnalysisReport`: now reads `company.ticker` (was `ticker`) and `evidence_links` (was `evidence_gaps`)
- `CompanyAnalysisUnknown`: now reads `title` as the question text (was `question`)

## Local Demo Dataset (Sprints 58–59)

A working two-company demo dataset is available under `examples/daily_brief_demo/`:

| File | Purpose |
|---|---|
| `knowledge.json` | AMD (5 facts) + NVDA (4 facts) knowledge facts |
| `research_input.json` | AMD (4 questions) + NVDA (3 questions) research projects |
| `watchlist_input.json` | AMD + NVDA watchlist items |

Run the full pipeline with the included script:

```bash
bash scripts/run_daily_brief_demo.sh
```

The demo generates separate company analysis exports for AMD and NVDA, merges
them into a single JSON array, and passes the combined file to `daily summary`.
This produces a Daily Brief with 2 company analysis reports, 7 unresolved
questions, and 2 discovery candidates.

Or step by step — see `examples/daily_brief_demo/README.md`.

Clean up generated outputs:

```bash
rm -rf tmp/atlas_demo
```

The demo is local-only, deterministic, and makes no network calls.
It is not live market analysis. Data represents demo research context only.
AMD and NVDA are used as demo examples only — no comparison between them
as investment opportunities is made or implied.

## End-to-End Local Workflow (Sprints 51–53)

Sprints 51–53 complete the export pipeline. Every Daily Brief input type
except Company Analysis can now be generated from local JSON files with no
network calls, no AI, and no manual authoring of the output format:

```bash
# Step 1 — generate watchlist intelligence from real items
atlas watchlist intelligence \
  --input watchlist.json \
  --output watchlist_export.json

# Step 2 — export research projects as Daily Brief–compatible research JSON
atlas research export \
  --input research_projects.json \
  --output research_export.json

# Step 3 — generate discovery from knowledge, research, and watchlist context
atlas discovery export \
  --knowledge knowledge.json \
  --research research_projects.json \
  --watchlist watchlist.json \
  --output discovery_export.json

# Step 4 — consume all exports in Daily Brief
atlas daily summary \
  --watchlist watchlist_export.json \
  --research research_export.json \
  --discovery discovery_export.json \
  --company-analysis company.json
```

All steps are local-only, deterministic, and make no network calls.

## Research Export (Sprint 53)

`atlas research export` converts a research projects JSON file into the
format accepted by `atlas daily summary --research`.

```bash
# Export research projects as Daily Brief–compatible JSON
atlas research export --input research_projects.json --output research_export.json

# Use the export as Daily Brief input
atlas daily summary --research research_export.json

# Print summary to stdout (no --output)
atlas research export --input research_projects.json

# Run with no input (produces empty export structure)
atlas research export --output research_export.json
```

### Input JSON Format (`--input`)

```json
{
  "projects": [
    {
      "id": "proj-nvda",
      "title": "NVDA Research",
      "topic": "NVDA",
      "status": "researching",
      "questions": [
        "What is the long-term GPU TAM?",
        "Who are the key competitors?"
      ]
    }
  ]
}
```

This is the same format accepted by `atlas discovery export --research`.

### Output JSON Format (`--output`)

The exported JSON is compatible with `atlas daily summary --research`:

```json
{
  "notes": [
    {
      "id": "proj-nvda",
      "title": "NVDA Research",
      "body": "NVDA — researching",
      "created_at": "",
      "related_tickers": ["NVDA"]
    }
  ],
  "open_questions": [
    "What is the long-term GPU TAM?",
    "Who are the key competitors?"
  ]
}
```

Each project becomes one note. Open (`OPEN` / `RESEARCHING`) questions are
collected across all projects into `open_questions`. Topic strings that look
like tickers (all-uppercase, ≤5 chars) appear in `related_tickers`.

No network calls are made. No recommendations are produced.

## Company Analysis Export (Sprints 54–55)

`atlas company-analysis export` exports engine-derived company analysis context
to a Daily Brief–compatible JSON file.

```bash
# Engine-backed export (Sprints 55–57) — runs CompanyAnalysisEngine on local inputs
atlas company-analysis export \
  --ticker AMD \
  --company-name "AMD Corporation" \
  --sector "Semiconductors" \
  --country "USA" \
  --business-description "AMD designs high-performance CPUs and GPUs." \
  --knowledge knowledge.json \
  --research research.json \
  --output ca_export.json

# Manual input export (Sprint 54) — validates and re-exports a pre-authored file
atlas company-analysis export --input company.json --output ca_export.json

# Consume in Daily Brief
atlas daily summary --company-analysis ca_export.json
```

See [CompanyAnalysis.md](CompanyAnalysis.md) for all input formats.

## Known Limitations

- The legacy `atlas daily brief` command still calls legacy engines (Market
  Health, Risk Drift, Economics, etc.) with no domain-native equivalents.
- `knowledge_node_count` is accepted by `build_daily_brief_input` but not
  yet wired to a CLI flag.

## Company Analysis Merge (Sprint 60)

`atlas company-analysis merge` combines multiple company analysis JSON exports
into one Daily Brief–compatible file, eliminating the `python3 -c` step from
the demo workflow:

```bash
atlas company-analysis merge \
  --inputs tmp/atlas_demo/company_analysis_amd.json \
  --inputs tmp/atlas_demo/company_analysis_nvda.json \
  --output tmp/atlas_demo/company_analysis.json
```

The demo script (`scripts/run_daily_brief_demo.sh`) now uses this command
at step 6. The full two-company demo is expressible in Atlas CLI commands only.

## Output Format (Sprint 62)

`render_daily_brief_report` produces a structured, human-readable terminal
output. The format is stable and deterministic.

### Output Structure

```
Atlas Daily Brief
─────────────────────────────────────────────

Opening Summary
<bottom_line>
Overall priority: <low|moderate|high>

─────────────────────────────────────────────
Included Context

  Companies:  AMD, NVDA        ← tickers present in company analysis
  Research:   2 project(s)    ← research notes count
  Watchlist:  available        ← if watchlist present
  Discovery:  N candidate(s)  ← if discovery present
  Portfolio:  available        ← if portfolio present

─────────────────────────────────────────────
What Deserves Attention

  [!] <title>: <detail>       ← high priority items
  [·] <title>: <detail>       ← moderate priority items
  <title>: <detail>           ← low priority items (no marker)

─────────────────────────────────────────────
Company Analysis Context

  AMD
    <detail>
  NVDA
    <detail>

─────────────────────────────────────────────
Research Context
...

─────────────────────────────────────────────
Evidence Gaps              ← only if evidence unknowns exist

  AMD: <description>

─────────────────────────────────────────────
Unresolved Questions       ← only if unknowns exist

  AMD
    - <question>

─────────────────────────────────────────────
Suggested Next Research Steps
  - <step>

─────────────────────────────────────────────
What Can Safely Wait         ← only if LOW priority detail-section items exist

  - <title>: <detail>

─────────────────────────────────────────────
Research Framing
This is a deterministic daily brief for context and education. ...
```

### Priority Markers

| Priority | Marker | Meaning |
|---|---|---|
| `high` | `[!]` | Deserves immediate attention |
| `moderate` | `[·]` | Deserves review |
| `low` | *(none)* | Available for context; can safely wait |

### Multi-Company Formatting

Company Analysis Context renders each company as a named group (not a flat list).
Unresolved Questions from company analysis unknowns are grouped by company ticker.
Companies are never compared as investment opportunities; no ranking is implied.

### Included Context

When any inputs are present, an "Included Context" block appears immediately after
Opening Summary, listing which companies, research projects, watchlist, discovery,
and portfolio data are available. This block is omitted when no inputs are supplied.

### Evidence Gaps Section

The Evidence Gaps section appears only when at least one company analysis report
contains "Missing Evidence" unknowns (i.e. `--knowledge` was not supplied during
export). When full metadata and knowledge are provided, the section is omitted —
this is correct, not an error.

### What Can Safely Wait Section (Sprint 64)

Appears after "Suggested Next Research Steps" when any detail section contains
LOW priority items. Collects those items in one place so readers can quickly
identify what does not require immediate attention.

Sources scanned (in section order):
- **Portfolio Context** — holdings count, low concentration, cash weight
- **Company Analysis Context** — companies with no unknowns
- **Research Context** — research notes (all moderate; not typically surfaced here)
- **Watchlist Context** — suggested research steps (LOW)
- **Discovery Context** — currently all moderate; not typically surfaced here

"What Deserves Attention" is explicitly excluded to avoid duplicating the
opening summary items.

LOW priority means "can be reviewed later" — not "bad" or "unimportant." It
signals that no current structured input indicates urgent attention is needed.

The section is **omitted** when:
- No inputs are supplied (no-input mode)
- All company reports contain unknowns (MODERATE priority — nothing is LOW)
- No LOW priority items exist in any detail section

### Section Order

1. Opening Summary
2. Included Context
3. What Deserves Attention
4. Company Analysis Context
5. Research Context
6. Watchlist Context
7. Discovery Context
8. Evidence Gaps
9. Unresolved Questions
10. Suggested Next Research Steps
11. **What Can Safely Wait** ← Sprint 64
12. Research Framing

## Evidence Gap Resolver (Sprint 61)

`_build_evidence_gaps` in `atlas/capabilities/daily_brief/engine.py` surfaces
only evidence gaps that are genuine — where supporting evidence is absent. The
resolver follows two rules:

1. **`evidence_links` are NOT gaps.** A confirmed evidence link means the engine
   found a knowledge fact that supports a section. Displaying confirmed links as
   gaps was a bug (fixed in Sprint 61).

2. **Only `unknowns` with "evidence" in the title are gaps.** This matches
   "Missing Evidence" (emitted by `CompanyAnalysisEngine` when no knowledge
   facts are supplied) while excluding metadata unknowns such as "Missing Sector"
   or "Missing Country" which are not evidence-support issues.

Gaps are scoped per company: AMD gaps cannot appear under NVDA and vice versa.

When full metadata (`--sector`, `--country`, `--business-description`) and
knowledge facts (`--knowledge`) are supplied, the Evidence Gaps section does not
appear in the daily brief. This is correct — no evidence is missing. The section
appears only when a company analysis report contains "Missing Evidence" unknowns,
which happens when `--knowledge` is omitted from the export step.

## Discovery Context Display Names (Sprint 72)

The Discovery Context section uses `_resolve_node_display_name` in
`atlas/capabilities/daily_brief/engine.py` to convert raw knowledge node IDs
into human-readable labels. Resolution order (deterministic, no fuzzy/AI):

1. **Explicit `title` field** — if non-empty, use it directly (e.g. `"AMD"`)
2. **Explicit `ticker` field** — if non-empty and title is absent
3. **Company node pattern** — `company-{x}` → `X.upper()`, only when suffix
   contains no further hyphens (prevents ambiguous multi-word IDs)
4. **Original identifier** — safe fallback for unrecognised patterns

Examples: `company-amd` → `AMD`, `company-nvda` → `NVDA`.
`theme:semiconductors` → `theme:semiconductors` (no safe mapping).

No fuzzy matching, no semantic matching, no external lookup.

## Evidence Link Resolution — Watchlist Knowledge Facts (Sprint 70)

`atlas watchlist intelligence` accepts an optional `--knowledge` flag. When
supplied, `assign_knowledge_facts` in `atlas/adapters/watchlist.py` distributes
knowledge facts to watchlist items using two deterministic matching rules:

1. **Exact ticker match** — `fact.subject_node_id == ticker` (e.g. `"AMD"`)
2. **Company node ID pattern** — `fact.subject_node_id == f"company-{ticker.lower()}"` (e.g. `"company-amd"` → `"AMD"`)

No fuzzy matching. The `_node_id_matches_ticker` helper is the single
implementation of this rule and is covered by unit tests.

When a watchlist item has no matching knowledge facts, `WatchlistIntelligenceEngine`
generates a `WatchlistUnknown("No Supporting Knowledge Facts", ...)` which
propagates into `suggested_next_research_steps` as
`"{ticker}: No knowledge facts are linked."`. Passing `--knowledge` with facts
that match by the rules above suppresses this false-negative signal.

The demo pipeline passes `--knowledge examples/daily_brief_demo/knowledge.json`
in Step 2 so that AMD and NVDA knowledge facts (which use `company-amd` /
`company-nvda` node IDs) are correctly assigned to their watchlist items.
