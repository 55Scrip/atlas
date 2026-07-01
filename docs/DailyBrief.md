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
# Blueprint-aligned (Sprint 48)
atlas daily summary                              # no-input mode, always succeeds
atlas daily summary --portfolio portfolio.json   # with portfolio domain context

# Legacy (unchanged)
atlas daily brief                                # original multi-engine brief
atlas daily brief --portfolio portfolio.json     # with legacy portfolio context
```

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

## Known Limitations

- `atlas daily summary` CLI currently only accepts `--portfolio`. Research notes,
  watchlist reports, discovery reports, and company analysis reports are
  supported at the capability level (via `build_daily_brief_input`) but are not
  yet wired to CLI flags — they require structured JSON inputs that are not yet
  part of the CLI.
- The legacy `atlas daily brief` command still calls legacy engines (Market
  Health, Risk Drift, Economics, etc.) with no domain-native equivalents.

## Recommendation for Sprint 50

Extend `atlas daily summary` CLI flags to accept structured JSON inputs for
watchlist and discovery (e.g. `--watchlist watchlist.json`, `--discovery
discovery.json`) so the capability can surface richer context at runtime.
Alternatively, begin migrating `atlas journal` commands to the
Blueprint-aligned decision domain, following the same additive pattern
established in Sprints 45–49.
