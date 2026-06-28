# Atlas Architecture

## Architecture Intent

Atlas architecture should make reasoning modular, testable, explainable, and
durable.

This document describes conceptual information flow rather than Python class
details. Implementation choices may change, but the responsibilities and
separation of concerns should remain stable.

## Information Flow

Atlas should reason through a layered flow:

```text
Market Data
    ↓
Evidence
    ↓
Analysis Engines
    ↓
Reasoning
    ↓
Suitability
    ↓
Portfolio Context
    ↓
Risk and Drift
    ↓
Language Layer
    ↓
User Experience
    ↓
Memory, Monitoring, and Journal
```

Each layer should add context without hiding uncertainty.

## Market Data

Market data provides structured inputs.

Data providers should be replaceable. Core engines should depend on provider
interfaces rather than specific vendors. Unit tests should not require live API
calls. Missing data should be handled explicitly instead of silently invented.

## Evidence

Evidence is the bridge between raw information and reasoning.

Atlas should evaluate evidence quality before treating information as useful.
Extraordinary claims should require verifiable sources. Weak evidence should
lower confidence, increase monitoring needs, or move an idea into a research
state instead of a high-confidence assessment.

## Analysis Engines

Analysis engines evaluate specific domains:

- Company quality, growth, valuation, financial strength, and risk.
- Portfolio fit, concentration, diversification, and overlap.
- Watchlist quality, relevance, evidence, and noise.
- Themes, bottlenecks, beneficiaries, and second-order effects.
- Market regime, market health, and economic signals.
- Risk sizing, liquidity, capital deployment, and concentration.

Engines should be deterministic, typed, and independently testable. They should
avoid user interface formatting and should not duplicate logic from other
engines.

## Reasoning

Reasoning synthesizes outputs from multiple engines.

Reasoning should not invent facts. It should combine available evidence,
surface contradictions, explain uncertainty, and identify what Atlas trusts
most and least. It should be able to say that several scenarios appear
plausible.

## Suitability

Suitability connects an investment or portfolio to the investor profile.

The same asset can have different suitability depending on goals, time horizon,
risk tolerance, risk capacity, portfolio purpose, liquidity needs, and existing
holdings. Suitability is not a buy or sell decision. It evaluates compatibility
with the stated context.

## Portfolio Context

Portfolio context prevents isolated analysis.

Atlas should understand how an idea affects concentration, diversification,
theme exposure, geographic exposure, quality, risk, and existing holdings.
Portfolio context should be present whenever available.

## Risk and Drift

Risk engines evaluate capital safety, liquidity, position size, market regime
adjustments, and concentration. Risk drift evaluates whether the investor's
current situation, portfolio, or market environment has moved away from the
assumptions in the original profile.

Risk reasoning should appear before return-seeking language.

## Language Layer

The language layer standardizes communication.

It should provide consistent ratings, views, fit language, confidence
explanations, thesis structure, rationale, and guardrail checks. It should make
clear that Atlas Ratings are assessments, not buy or sell instructions.

Language should be calm, transparent, and precise.

## User Experience

User-facing experiences should synthesize existing engines rather than
reimplementing business logic.

Examples include:

- Home Dashboard.
- Daily Brief.
- Portfolio Review.
- Watchlist Review.
- Investment Comparison.
- Decision Journal.
- Conversation.

Each surface should answer a real investor workflow question and should expose
enough reasoning for the user to understand the conclusion.

## Memory, Monitoring, and Journal

Memory, monitoring, and decision journaling make Atlas useful over time.

- Memory stores prior analyses and compares changes.
- Monitoring tracks signals and explains what changed.
- Decision Journal preserves thesis, assumptions, risks, evidence, and review
  triggers.

These systems help Atlas support learning, not just reporting.

## Architectural Constraints

- Keep business logic separate from CLI.
- Keep providers replaceable.
- Keep engines deterministic by default.
- Keep tests independent from live APIs.
- Keep public outputs typed and structured.
- Keep user-facing language guarded against false certainty.
- Prefer small focused modules over large multipurpose files.

## Desired Direction

Atlas should become more coherent as more engines are added.

New systems should plug into the same flow of data, evidence, reasoning,
suitability, language, and user experience. The product should feel like one
intelligence system, not a pile of reports.
