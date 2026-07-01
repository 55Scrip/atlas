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

### Legacy: `atlas daily brief`

The original command (`atlas daily brief`), powered by
`atlas.daily_brief.DailyBriefEngine`, consumes the Atlas Home Engine,
Portfolio Review Engine, Watchlist Review Engine, Market Health Engine,
Risk Drift Engine, and other legacy engines to produce a CIO-style brief.
It is fully preserved and untouched by Sprint 48.

### Blueprint-aligned: `atlas daily summary` (Sprint 48)

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

### Sections (in order)

1. **What Deserves Attention** — always present; shows "no developments" when nothing supplied
2. **Portfolio Context** — present only when portfolio summary provided
3. **Research Context** — present only when research notes provided
4. **Watchlist Context** — present only when watchlist report provided
5. **Discovery Context** — present only when discovery report with candidates provided
6. **Company Analysis Context** — present only when company reports provided

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

## Company Analysis Export (Sprint 54)

`atlas company-analysis export` completes the Daily Brief export pipeline.

```bash
# Export company analysis from local input
atlas company-analysis export --input company.json --output ca_export.json

# Consume in Daily Brief
atlas daily summary --company-analysis ca_export.json
```

See [CompanyAnalysis.md](CompanyAnalysis.md) for the input JSON format.

## Known Limitations

- The legacy `atlas daily brief` command still calls legacy engines (Market
  Health, Risk Drift, Economics, etc.) with no domain-native equivalents.
- `knowledge_node_count` is accepted by `build_daily_brief_input` but not
  yet wired to a CLI flag.

## Recommendation for Sprint 55

Wire `CompanyAnalysisEngine` to the export command via `--knowledge` and
`--research` flags (mirroring the Discovery export pattern), so company
analysis reports can be generated from knowledge facts and research projects
rather than requiring manual JSON authoring of the report fields.
