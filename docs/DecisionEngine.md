# Decision Engine Foundation

Sprint 38 introduces the Atlas Decision domain.

This is not a recommendation engine. It does not produce trade actions,
forecasts, or portfolio instructions. It transforms structured evidence into
structured, explainable reasoning.

## Architecture

The Decision domain lives in `atlas.domains.decision`.

It contains:

- immutable decision models
- factual evidence models
- deterministic evidence collection
- deterministic reasoning pipeline
- confidence calculation
- structured `DecisionCard` output

The older `atlas.decision` package remains unchanged. That package is an
orchestration engine from earlier Atlas work. Sprint 38 adds the lower-level
domain foundation that future engines can reuse.

## Reasoning Pipeline

```text
Evidence
  ↓
Observations
  ↓
Reasoning Steps
  ↓
Unknowns
  ↓
Confidence
  ↓
Decision Result
  ↓
Decision Card
```

Each reasoning step references the evidence and observations that produced it.
Nothing is allowed to appear without traceable support.

## Evidence Model

Evidence contains facts only.

Supported categories:

- Portfolio
- Company
- Market
- Risk
- Valuation
- Technical
- Macro

Evidence has a source, strength, statement, category, and optional structured
data. Interpretation is added later by observations and reasoning steps.

## Explainability

Every `DecisionCard` includes:

- summary
- evidence
- key observations
- unknowns
- confidence
- risks
- explanation

The card does not use buy or sell language. It exists to help investors
understand the evidence base and uncertainty.

## Future AI Integration

Future AI services may assist with summarization or evidence extraction, but
they should consume and produce structured data through this domain boundary.

AI must not invent evidence. If facts are missing, the domain should surface
unknowns instead of hiding uncertainty.

## Known Limitations

- No LLM calls.
- No market data providers.
- No portfolio recommendations.
- No trade execution.
- Confidence scoring is deterministic and intentionally simple.
- Evidence collection currently normalizes supplied evidence rather than
  fetching facts from external systems.
