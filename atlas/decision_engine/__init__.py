"""Atlas Decision Engine — reasoning pipeline foundation.

Governed by `docs/ATLAS_DECISION_ENGINE_DOCTRINE.md` and its companion
specifications (`docs/atlas_decision_engine/DE-001` through `DE-005`).
This package is the "Decision Engine Implementation Sprint 1" skeleton:
architectural backbone only. It is:

- NOT a Core Domain Object package. `OE-002` §4's Domain Object Set is
  closed (Observation, Knowledge Reference, Reasoning Trace, Judgment,
  Decision, Outcome); none of this package's pipeline-stage types is a
  member of that set, and none is intended to become one. This package
  lives outside `atlas/core/` entirely, sibling to it — the same
  placement `atlas/alpha/` already established for exactly this reason
  (see `atlas/alpha/portfolio/__init__.py`).
- NOT permitted to write to, or be imported by, `atlas/core/` — a
  one-way read relationship, enforced by
  `tests/test_architecture_boundaries.py::test_core_does_not_import_atlas_decision_engine`,
  mirroring `test_core_does_not_import_atlas_alpha`.
- NOT capable of producing a directional Atlas Recommendation this
  sprint. Every substantive evaluator (Business Evaluation, Valuation,
  Portfolio Intelligence, Reasoning) is a deterministic `not_evaluated`
  placeholder, so every pipeline run terminates in **Recommendation
  Withheld** (`DE-004` §4), by construction — not by a runtime check
  that happens to always pass.
- NOT an AI, scoring, heuristic, or valuation system. No network call,
  no storage access, no random or wall-clock-dependent behavior appears
  anywhere in this package; every timestamp is supplied explicitly by
  the caller.

Public entry point: `atlas.decision_engine.pipeline.run_pipeline`.
"""
from __future__ import annotations
