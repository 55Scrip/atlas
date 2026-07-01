# Watchlist Intelligence Capability

Sprint 42 introduces the Atlas Watchlist Intelligence capability.

A watchlist is not a list of stocks. It is a portfolio of unanswered questions.
This capability helps investors understand which companies may deserve review
and why, without creating urgency or trade behavior.

It does not create recommendations, forecasts, price targets, AI-generated
analysis, or trade actions.

## Capability Responsibility

The capability is responsible for:

- representing watchlist items
- surfacing research status
- surfacing open questions
- preserving evidence links
- identifying missing evidence
- identifying unknowns
- producing calm structured observations
- suggesting next research steps

It is not responsible for owning Research, Knowledge, Company Analysis,
Decision, Portfolio, UI, AI, persistence, providers, or market data.

## Relationship To Research Domain

Watchlist Intelligence consumes `ResearchProject`, `ResearchQuestion`,
`ThesisFragment`, and `ResearchSummary` concepts.

Open research questions and thesis fragments without supporting evidence become
signals that research appears incomplete.

## Relationship To Knowledge Domain

The Knowledge domain stores attributed facts.

Watchlist Intelligence consumes `KnowledgeFact` objects as supporting context
and surfaces gaps when no knowledge facts are linked.

## Relationship To Company Analysis

Company Analysis helps describe a business with structured evidence and
confidence.

Watchlist Intelligence can consume a `CompanyAnalysisReport` and surface low
confidence as a reason for further study.

## Report Structure

Reports include:

- Overview
- Companies Needing Attention
- Open Questions
- Research Status
- Knowledge Context
- Company Analysis Context
- Evidence Gaps
- Unknowns
- Suggested Next Research Steps

## Prioritisation Logic

Prioritisation is deterministic and explainable. It considers:

- unresolved research questions
- missing evidence
- low company analysis confidence
- manual observations
- thesis fragments without support
- missing company context
- paused or archived status

Language should remain calm:

- `deserves review`
- `needs more evidence`
- `has unresolved questions`
- `research appears incomplete`
- `continue observing`

## Known Limitations

- No UI.
- No LLM calls.
- No external APIs.
- No market data providers.
- No persistence.
- No price targets.
- No trade actions.
- No automated discovery.

## Recommended Sprint 43

Sprint 43 should add deterministic adapters that assemble watchlist intelligence
inputs from existing Atlas data:

- watchlist membership
- company context
- linked research projects
- knowledge facts
- company analysis reports

Adapters should remain deterministic, provider-free, and non-advisory.


## JSON Export (Sprint 51)

`atlas watchlist intelligence` generates a Blueprint-aligned Watchlist
Intelligence report and optionally exports it as a local JSON file.

```bash
# Human-readable summary (stdout)
atlas watchlist intelligence

# Export to local JSON file
atlas watchlist intelligence --output watchlist.json

# Use the export as Daily Brief input
atlas daily summary --watchlist watchlist.json
```

The `--output` flag writes a JSON file compatible with
`atlas daily summary --watchlist`. The export includes:

| Field | Purpose |
|---|---|
| `name` | Watchlist name |
| `overview` | Plain-text overview |
| `open_questions` | Questions surfaced across watchlist items |
| `suggested_next_research_steps` | Deterministic research steps |
| `companies_needing_attention` | Items that deserve review or more evidence |
| `unknowns` | Missing evidence across watchlist items |
| `evidence_gaps` | Specific evidence gaps identified |

The export is local-only. No network calls are made. No recommendations
are produced. The format is stable across Sprint 51.
