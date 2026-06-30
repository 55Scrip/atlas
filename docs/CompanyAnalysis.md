# Company Analysis Capability

Sprint 41 introduces the Atlas Company Analysis capability.

Company Analysis is a deterministic capability built on top of existing Atlas
domains. It helps investors understand a business by organizing company
information, knowledge facts, research context, decision evidence, risks,
unknowns, and confidence.

It does not create recommendations, forecasts, price targets, AI-generated
analysis, or trade actions.

## Capability Responsibility

The capability is responsible for:

- organizing company facts
- surfacing important knowledge facts
- connecting research questions and thesis fragments
- preserving evidence links
- surfacing missing evidence and unknowns
- producing structured report sections
- explaining confidence categorically

It is not responsible for owning Knowledge, Research, Decision, Portfolio, UI,
AI, persistence, providers, or market data.

## Relationship To Knowledge Domain

The Knowledge domain stores attributed facts and source references.

Company Analysis consumes `KnowledgeFact` objects and preserves their source
attribution as `CompanyAnalysisEvidenceLink` entries.

## Relationship To Research Domain

The Research domain organizes notes, questions, assumptions, evidence
references, and thesis fragments.

Company Analysis consumes a `ResearchProject` when available. Open research
questions become unknowns. Thesis fragments appear as research context.

## Relationship To Decision Engine

The Decision domain represents structured evidence and reasoning.

Company Analysis may consume Decision evidence as context. It does not emit a
Decision action and does not convert company understanding into an investment
instruction.

## Report Structure

Reports include:

- Business Overview
- What Matters
- Supporting Evidence
- Key Risks
- Open Questions
- Research Context
- Knowledge Context
- Decision Context
- Confidence
- What Could Change the View

## Confidence Model

Confidence is categorical:

- `low`
- `moderate`
- `high`

The model considers:

- available company information
- evidence links
- unresolved research questions
- missing facts
- unsupported thesis fragments

Confidence is explainable and intentionally simple. It should not imply false
precision.

## Known Limitations

- No UI.
- No LLM calls.
- No external APIs.
- No market data providers.
- No persistence.
- No price targets.
- No investment actions.
- Risk detection is based only on supplied structured evidence language.

## Recommended Sprint 42

Sprint 42 should add deterministic adapters that make it easier to build
`CompanyAnalysisInput` from existing Atlas data:

- Knowledge facts for a company.
- Research projects for a company or topic.
- Decision evidence for company context.
- Portfolio exposure context where available.

Adapters should remain deterministic, provider-free, and non-advisory.

