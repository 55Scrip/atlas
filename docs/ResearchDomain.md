# Research Domain

Sprint 40 introduces the Atlas Research domain.

Research is the disciplined process of turning curiosity into structured
understanding. The domain represents notes, questions, assumptions, evidence
references, thesis fragments, validation issues, and deterministic summaries.

It does not create recommendations, forecasts, discovery feeds, daily briefs,
company analysis, or AI-generated analysis.

## Domain Responsibility

The Research domain is responsible for:

- research projects
- research notes
- research questions
- assumptions
- thesis fragments
- evidence references
- research status
- research summaries
- validation

It is not responsible for UI, AI calls, persistence, external APIs, market data,
watchlists, or investment decisions.

## Core Models

The domain exports:

- `ResearchProject`
- `ResearchNote`
- `ResearchQuestion`
- `ResearchAssumption`
- `ThesisFragment`
- `ResearchEvidenceReference`
- `ResearchStatus`
- `ResearchSummary`

`ResearchNote` remains the canonical shared note entity from `atlas.shared`.
Sprint 40 adds the research-specific structures around it.

## Research Question Lifecycle

Research questions capture what remains unknown.

Supported question states:

- `open`
- `researching`
- `resolved`
- `archived`

Resolved questions should include resolution notes. Questions may link to
evidence references and can be revisited as research develops.

## Research Status

Research status describes the maturity of understanding:

- `not_started`
- `researching`
- `needs_more_evidence`
- `thesis_forming`
- `ready_for_review`
- `archived`

Status does not describe investment action.

## Thesis Fragments

A thesis fragment is an incomplete piece of investment reasoning.

It may include:

- a claim
- supporting evidence references
- assumptions
- confidence
- open questions
- status

A thesis fragment is not a final recommendation. It is structured reasoning
under development.

## Relationship To Knowledge Domain

Research may reference Knowledge facts through `ResearchEvidenceReference`.

The Knowledge domain stores attributed facts and explicit relationships.
Research organizes those facts into questions, assumptions, and thesis
development.

## Relationship To Decision Engine

The Decision domain reasons over structured evidence.

Research can eventually provide evidence references, open questions,
assumptions, and thesis fragments to the Decision domain. Sprint 40 does not add
that adapter yet.

## Validation

Validation returns structured issues and does not crash unnecessarily.

It checks:

- empty research projects
- missing titles
- duplicate question IDs
- thesis fragments without evidence references
- assumptions without explanation
- resolved questions without resolution notes
- resolved timestamps without resolved status

## Known Limitations

- No persistence.
- No UI.
- No AI-generated analysis.
- No company analysis.
- No discovery engine.
- No watchlist intelligence.
- No external APIs.
- No adapters to Knowledge or Decision yet.

## Recommended Sprint 41

Sprint 41 should add deterministic adapters between Research, Knowledge, and
Decision:

- convert Knowledge facts into research evidence references
- convert resolved research questions into Decision evidence
- surface unresolved research questions as Decision unknowns
- keep all adapters deterministic and provider-free

