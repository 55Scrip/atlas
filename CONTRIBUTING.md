# Contributing to Atlas

## 1. Project Philosophy

Atlas is an AI Investment Partner. Every feature must help investors make better capital allocation decisions.

## 2. Architecture Principles

- Keep business logic separate from CLI.
- Use modular services and engines.
- Do not hardcode investment logic inside commands.
- Every analysis module should expose a clean public interface.
- Prefer small focused modules over large files.

## 3. Code Standards

- Use type hints.
- Prefer dataclasses for structured outputs.
- Keep functions small and readable.
- Avoid hidden side effects.
- Avoid global mutable state.

## 4. Testing Requirements

- Every new feature must include tests.
- Every scoring model must have deterministic tests.
- CLI commands must have smoke tests.
- Do not merge code if tests fail.

## 5. Analysis Module Rules

Every analysis module should return:

- score
- summary
- strengths
- weaknesses
- confidence

## 6. Data Source Rules

- Data providers must be replaceable.
- No live API dependency should be required for unit tests.
- Mock providers should exist for testing.
- Every external data point should eventually support source tracking.

## 7. AI Rules

- AI should reason from structured data.
- AI must not invent missing facts.
- If data is insufficient, Atlas should say so.
- Every recommendation must include reasoning and confidence.

## 8. Git Workflow

- Main branch should stay stable.
- Each feature should be committed separately.
- Keep commits focused and descriptive.
- Run tests before committing.

## 9. Definition of Done

A feature is done only when:

- It works.
- It is tested.
- It is documented.
- It aligns with `ATLAS_MANIFEST.md`.
