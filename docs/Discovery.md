# Discovery Capability

Sprint 43 introduces the Atlas Discovery capability.

Discovery is the disciplined pursuit of understanding before conviction. It
turns structured inputs from Atlas into research candidates that may deserve
further study.

It does not create recommendations, forecasts, price targets, AI-generated
analysis, or trade actions.

## Capability Responsibility

The capability is responsible for:

- creating discovery candidates
- preserving evidence links
- explaining why candidates appeared
- surfacing unknowns and evidence gaps
- generating deterministic research questions
- assigning calm research priority

It is not responsible for owning Knowledge, Research, Watchlist Intelligence,
Company Analysis, Decision, Portfolio, UI, AI, persistence, providers, or market
data.

## Relationship To Knowledge Domain

Discovery consumes `KnowledgeFact` objects as attributed facts. Knowledge facts
can cause a company or concept to appear as a candidate, but Discovery does not
infer relationships that are not represented in the input.

## Relationship To Research Domain

Discovery consumes `ResearchProject` objects. Open research questions and thesis
evidence gaps become candidate unknowns and suggested research questions.

## Relationship To Company Analysis

Discovery consumes `CompanyAnalysisReport` objects. Company analysis confidence
and unknowns help determine what deserves further research.

## Relationship To Watchlist Intelligence

Discovery consumes `WatchlistIntelligenceReport` objects. Watchlist signals,
open questions, and evidence gaps help explain why a company may deserve
research attention.

## Candidate Model

A `DiscoveryCandidate` includes:

- identifier
- title
- discovery reasons
- supporting evidence links
- related knowledge facts
- related research questions
- related watchlist status
- unknowns
- suggested next research questions
- priority
- confidence
- context

## Priority Logic

Priority is deterministic and categorical:

- `low`
- `moderate`
- `high`

Priority means research attention, not investment attractiveness. It considers:

- supporting evidence links
- relationship to existing research
- relationship to watchlist items
- unresolved questions
- evidence gaps
- confidence

## Known Limitations

- No UI.
- No LLM calls.
- No external APIs.
- No market data providers.
- No persistence.
- No price targets.
- No trade actions.
- No semantic search.
- No inferred hidden conclusions.

## Recommended Sprint 44

Sprint 44 should add deterministic adapters that assemble `DiscoveryInput` from
existing Atlas data:

- knowledge collections
- research projects
- company analysis reports
- watchlist intelligence reports
- theme context

Adapters should remain provider-free, AI-free, deterministic, and non-advisory.


## JSON Export (Sprint 51)

`atlas discovery export` generates a Blueprint-aligned Discovery report and
optionally exports it as a local JSON file.

```bash
# Human-readable summary (stdout)
atlas discovery export

# Export to local JSON file
atlas discovery export --output discovery.json

# Use the export as Daily Brief input
atlas daily summary --discovery discovery.json
```

The `--output` flag writes a JSON file compatible with
`atlas daily summary --discovery`. The export includes:

| Field | Purpose |
|---|---|
| `summary` | Plain-text discovery summary |
| `candidates` | Discovery candidates with identifier, title, reasons, priority |
| `unknowns` | Missing evidence across candidates |

Each candidate includes:

| Field | Purpose |
|---|---|
| `identifier` | Unique identifier (ticker or concept) |
| `title` | Human-readable title |
| `reasons` | Explainable reasons the candidate appeared |
| `priority` | Research attention priority (`low`, `moderate`, `high`) |
| `confidence` | Confidence level |
| `unknowns` | Open questions for this candidate |
| `suggested_next_research_questions` | Suggested research questions |

The export is local-only. No network calls are made. No recommendations
are produced. Priority means "deserves research attention", not "investment
attractiveness". The format is stable across Sprint 51.
