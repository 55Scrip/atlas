"""Observed Decision Properties (Sprint 13) -- the smallest read-only
product-safe boundary around the existing, unmodified Pattern
Recognition subsystem (`atlas.core.application.pattern_recognition`).

Genesis: Sprint 10 discovered a real, deterministic, CLI-only Pattern
Recognition / Strategy Signature subsystem, fully disconnected from the
live product. Sprint 11 audited it for integration readiness. Sprint 12
defined the product-safe contract: raw `RecognizedPattern` and
`RecognizedStrategySignature` output is not safe to expose directly --
Strategy Signature in particular was found to collapse into one
unstable, ever-growing, multi-company component that would misrepresent
a structural artifact as a coherent "strategy" -- but individual
Patterns, wrapped in an evidence/scope/limitation contract, are safe.

This package is that wrapping. It:

- reuses `SameSubjectAndTypeStrategy`/`SameConfidenceStrategy` from
  `atlas.core.application.pattern_recognition.strategies` completely
  unmodified -- no grouping logic is duplicated here;
- never computes or serializes `RecognizedStrategySignature` at all;
- never reads `Outcome`, `Evaluation`, or `Learning` data -- every
  `ObservedDecisionProperty` is structurally `outcome_aware=False`;
- regenerates its own factual descriptions from structured fields
  (`matching_key`) rather than passing `RecognizedPattern.description`
  through verbatim, so the public wire contract never silently
  inherits legacy wording (Sprint 12 Phase 5);
- deliberately avoids `DecisionTimelineQuery` (which reads Outcome/
  Evaluation/Learning per Decision, an N+1 query pattern neither
  Pattern Recognition strategy ever needs -- see `service.py`'s own
  docstring) and instead builds the minimal `DecisionTimeline` the two
  strategies actually require directly from `DecisionRepository.list_all()`.

Following the one-way boundary `test_core_does_not_import_atlas_alpha`
already enforces: this package (`atlas.alpha`) is authorized to import
`atlas.core.application`/`atlas.core.domain`; nothing in Core ever
imports this package.
"""
from __future__ import annotations
