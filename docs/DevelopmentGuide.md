# Atlas Development Guide

Atlas development should follow the Constitution: evidence before opinion,
context before conclusion, calm before clever, and simplicity before
sophistication.

## Local Verification

Run the standard checks before committing:

```bash
.venv/bin/python -m compileall atlas tests
.venv/bin/python -m pytest
```

## Code Quality

Python formatting and linting are configured with Ruff in `pyproject.toml`.
Local hooks are defined in `.pre-commit-config.yaml`.

Frontend TypeScript is configured in `frontend/tsconfig.json` with strict mode.
No frontend runtime is required for Sprint 36.

## Architecture Rules

- Put canonical entities in `atlas.shared`.
- Keep domain boundaries in `atlas.domains` small and explicit.
- Keep business logic out of CLI commands.
- Depend on interfaces for future AI services.
- Avoid adding abstractions until they reduce real complexity.

## Testing Rules

- New behavior requires tests.
- Deterministic engines need deterministic tests.
- CLI additions need smoke tests.
- Do not merge if compile or tests fail.

## Documentation Rules

Architecture decisions that affect future development should be recorded in
`docs/DecisionLog.md`.

